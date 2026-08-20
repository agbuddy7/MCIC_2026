#!/usr/bin/env python3
"""Feature names, keyword lists, and gate policy constants."""

from __future__ import annotations


FEATURE_SCHEMA = {
    "turn_count": int,
    "amount": float,
    "source_of_instruction_external": int,
    "source_of_instruction_user_explicit": int,
    "known_payee": int,
    "payee_introduced_by_user": int,
    "payee_introduced_by_attacker": int,
    "payee_introduced_by_tool_result": int,
    "payee_lag_turns": int,
    "urgency_word_count": int,
    "trust_word_count": int,
    "authority_word_count": int,
    "romance_word_count": int,
    "external_instruction_count": int,
    "recommendation_steering_count": int,
    "has_new_payee": int,
    "has_urgent_payment": int,
    "competing_options_suppressed": int,
    "contains_family_language": int,
    "contains_financial_jargon": int,
    "payee_reused_from_earlier": int,
}

URGENCY_KEYWORDS = [
    "tonight",
    "urgent",
    "urgently",
    "asap",
    "immediately",
    "due",
    "deadline",
    "emergency",
    "critical",
    "rush",
    "hurry",
    "now",
    "today",
    "before",
    "expires",
    "expiring",
    "midnight",
    "pending",
    "window",
    "closes",
    "late",
]

TRUST_BUILDING_PHRASES = [
    "thank you",
    "appreciate",
    "trust",
    "believe",
    "understand",
    "feel like",
    "connection",
    "honest",
    "genuine",
    "safe",
    "safest",
    "verified",
    "verification",
    "confirm",
    "confirmed",
    "support",
    "help",
    "cooperating",
    "remember",
]

FAMILY_KEYWORDS = [
    "sister",
    "brother",
    "mom",
    "dad",
    "parent",
    "wife",
    "husband",
    "son",
    "daughter",
    "friend",
    "family",
    "relative",
    "loved one",
]

FINANCIAL_KEYWORDS = [
    "account",
    "transfer",
    "balance",
    "payment",
    "refund",
    "bank",
    "wire",
    "invoice",
    "deposit",
    "ledger",
]

AUTHORITY_KEYWORDS = [
    "compliance",
    "support",
    "bank",
    "security",
    "audit",
    "verification",
    "management",
    "property",
    "office",
    "case",
    "policy",
    "settlement",
    "cardholder",
    "operations",
    "lease",
]

ROMANCE_KEYWORDS = [
    "matched",
    "profile",
    "smile",
    "connection",
    "embarrassed",
    "hotel",
    "clinic",
    "travel",
    "friday",
    "photos",
    "dear",
    "love",
]

EXTERNAL_INSTRUCTION_KEYWORDS = [
    "route",
    "routing",
    "override",
    "settlement",
    "clearing",
    "ledger",
    "processor",
    "reference",
    "supersedes",
    "memo",
    "sponsored",
    "editorial",
]

STEERING_KEYWORDS = [
    "recommend",
    "recommending",
    "recommendation",
    "default",
    "preferred",
    "single best",
    "aaa",
    "sponsored",
    "steer",
    "steers",
    "allocation",
    "strongest",
]

GATE_POLICY = {
    "payee_allowlist_required_above": 50.00,
    "hard_cap_per_transaction": 500.00,
    "hard_cap_daily": 1000.00,
    "require_step_up_confirmation_if": [
        "payee_id not in known_payees",
        "source_of_instruction == 'external_content'",
        "amount > payee_allowlist_required_above",
        "payee introduced by tool_result",
        "payee introduced by attacker",
        "competing options suppressed",
    ],
    "block_unconditionally_if": [
        "amount > hard_cap_per_transaction",
        "payee_id is null",
        "amount > 500 and payee is new",
        "daily spending would exceed hard_cap_daily",
    ],
}

DEFAULT_KNOWN_PAYEES = {
    "techmart-checkout",
    "ispcorp-billing",
    "paypal-newuser",
    "flightbooker-main",
    "amazon-checkout",
}
