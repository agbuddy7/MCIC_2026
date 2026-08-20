#!/usr/bin/env python3
"""Deterministic first-layer safety gate for transfer attempts."""

from __future__ import annotations

from typing import Any

try:
    from .schemas import DEFAULT_KNOWN_PAYEES, GATE_POLICY
except ImportError:
    from schemas import DEFAULT_KNOWN_PAYEES, GATE_POLICY


ALLOW = "allow"
PASSED = "passed"
STEP_UP = "step_up_required"
BLOCK = "block"
BLOCKED = "blocked"

GATE_HIT = {STEP_UP, BLOCK, BLOCKED}


class DeterministicGate:
    """Rule-based safety barrier that runs before the ML detector."""

    def __init__(self, policy: dict | None = None, known_payees: set[str] | None = None):
        self.policy = policy or GATE_POLICY
        self.known_payees = set(known_payees or DEFAULT_KNOWN_PAYEES)
        self.daily_spending: dict[str, float] = {}

    def evaluate_transfer(
        self,
        payee_id: str | None,
        amount: float | None,
        currency: str | None = "USD",
        source_of_instruction: str | None = None,
        user_id: str = "default",
        known_payee: bool | None = None,
        introduced_by: str | None = None,
        competing_options_suppressed: bool = False,
    ) -> dict[str, Any]:
        del currency
        amount = float(amount or 0)
        reasons: list[str] = []
        verdict = ALLOW

        if payee_id is None:
            return _result(BLOCK, ["payee_id is null"])

        is_known = bool(known_payee) or payee_id in self.known_payees
        daily_total = self.daily_spending.get(user_id, 0.0)

        if amount > self.policy["hard_cap_per_transaction"]:
            return _result(
                BLOCK,
                [f"amount {amount} exceeds hard cap {self.policy['hard_cap_per_transaction']}"],
            )

        if daily_total + amount > self.policy["hard_cap_daily"]:
            return _result(
                BLOCK,
                [
                    f"daily spending {daily_total} + {amount} exceeds cap {self.policy['hard_cap_daily']}"
                ],
            )

        if not is_known:
            verdict = STEP_UP
            reasons.append("payee_id not in known_payees")

        if source_of_instruction == "external_content":
            verdict = max_verdict(verdict, STEP_UP)
            reasons.append("source_of_instruction == 'external_content'")

        if amount > self.policy["payee_allowlist_required_above"]:
            verdict = max_verdict(verdict, STEP_UP)
            reasons.append(
                f"amount {amount} > threshold {self.policy['payee_allowlist_required_above']}"
            )

        if introduced_by == "tool_result":
            verdict = max_verdict(verdict, STEP_UP)
            reasons.append("final payee was first introduced by a tool result")

        if introduced_by == "attacker":
            verdict = max_verdict(verdict, STEP_UP)
            reasons.append("final payee was first introduced by an attacker")

        if competing_options_suppressed:
            verdict = max_verdict(verdict, STEP_UP)
            reasons.append("recommendation appears to suppress competing options")

        if amount > self.policy["hard_cap_per_transaction"] and not is_known:
            verdict = BLOCK
            reasons.append("amount exceeds $500 for a new payee")

        if source_of_instruction == "user_explicit" and is_known and verdict == ALLOW:
            return _result(ALLOW, ["user explicitly requested a transfer to a known payee"])

        if not reasons:
            reasons.append("all checks passed")

        return _result(verdict, reasons)

    def evaluate(self, transcript: dict[str, Any]) -> dict[str, Any]:
        details = transcript.get("transfer_details") or {}
        if not transcript.get("final_transfer_attempted", False):
            return _result(ALLOW, ["no transfer attempted"])
        return self.evaluate_transfer(
            payee_id=details.get("payee_id"),
            amount=details.get("amount"),
            currency=details.get("currency"),
            source_of_instruction=details.get("source_of_instruction"),
            user_id=str(transcript.get("conversation_id") or "default"),
            known_payee=bool(transcript.get("known_payee", False)),
            introduced_by=transcript.get("payee_introduced_by"),
            competing_options_suppressed=bool(transcript.get("competing_options_suppressed", False)),
        )


def _result(verdict: str, reasons: list[str]) -> dict[str, Any]:
    return {
        "verdict": verdict,
        "legacy_verdict": {ALLOW: PASSED, BLOCK: BLOCKED}.get(verdict, verdict),
        "reasons": reasons,
        "score": verdict_score(verdict),
    }


def verdict_score(verdict: str) -> int:
    return {ALLOW: 0, PASSED: 0, STEP_UP: 1, BLOCK: 2, BLOCKED: 2}.get(verdict, 0)


def max_verdict(current: str, candidate: str) -> str:
    return current if verdict_score(current) >= verdict_score(candidate) else candidate


def evaluate(transcript: dict[str, Any]) -> dict[str, Any]:
    """Convenience function for callers that do not need custom thresholds."""
    return DeterministicGate().evaluate(transcript)


def combine_layers(gate_result: dict[str, Any], fraud_probability: float, threshold: float = 0.5) -> dict[str, Any]:
    """Merge gate verdict and ML score into a single Person C-facing decision."""
    ml_flag = float(fraud_probability) >= threshold
    gate_verdict = gate_result.get("verdict", ALLOW)
    gate_hit = gate_verdict in GATE_HIT

    if gate_verdict in {BLOCK, BLOCKED}:
        final = BLOCK
    elif ml_flag and gate_hit:
        final = BLOCK
    elif gate_hit or ml_flag:
        final = STEP_UP
    else:
        final = ALLOW

    return {
        "verdict": final,
        "gate_verdict": gate_verdict,
        "gate_reasons": list(gate_result.get("reasons") or []),
        "ml_fraud_probability": float(fraud_probability),
        "ml_flag": ml_flag,
        "threshold": threshold,
    }


if __name__ == "__main__":
    gate = DeterministicGate()
    tests = [
        (None, 50, "USD", "user_explicit", "should block: null payee"),
        ("new-payee-123", 100, "USD", "external_content", "should require step-up"),
        ("techmart-checkout", 30, "USD", "user_explicit", "should allow"),
        ("new-payee-123", 750, "USD", "user_explicit", "should block: hard cap"),
    ]
    for payee_id, amount, currency, source, description in tests:
        result = gate.evaluate_transfer(payee_id, amount, currency, source)
        print(f"{description}: {result['verdict']} ({', '.join(result['reasons'])})")
