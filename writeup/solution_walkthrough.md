# Solution walkthrough

**Agentic Fraud: Closed-loop detection and defense**  
Mastercard Innovation Challenge 2026

## 1. Title
Closed-loop red team / blue team for GenAI-enabled payment fraud.

## 2. Challenge overview
Payment assistants that can call `transfer_funds` will read untrusted merchant pages, chat history, and recommendation sources. The project generates those attacks, defends them with a two-layer stack, and demos the loop in a web prototype.

## 3. Identify pillar
See `identify/attack_taxonomy.md`: 11 attack types with channel, technique, target, and feasibility. Three flagships are fully simulated; the rest provide breadth.

## 4. Flagship 1 — Prompt injection
User asks the agent to pay a merchant. `get_payee_details` returns policy text that redirects settlement to an attacker payee. The tool call is labeled `source_of_instruction: external_content`. Dataset: `generate/data/flagship1_injections.jsonl`.

## 5. Flagship 2 — Trust poisoning
An attacker builds rapport, plants a payee, then asks for an urgent transfer. The final call can still be `user_explicit`. Dataset: `generate/data/flagship2_poisonings.jsonl`.

## 6. Deterministic gate
Rules in `defend/gate.py`: null payee block, $500 hard cap, $1000 daily cap, unknown payee step-up, external content, amount > $50, tool-result payee, attacker-introduced payee, recommendation suppression.

## 7. ML detector
XGBoost on transcript features (urgency, trust, family language, payee lag, provenance flags). Holdout metrics are in `defend/evaluation_metrics.json`.

## 8. Closing the loop
Misses and gate-only cases feed feature work and generator variants. Person C's UI runs the same JSONL through the live gate and model.

## 9. Gate vs detector
Use `defend/breakdown_report.json`. Combined defense is the novelty table: neither layer is the whole product.

## 10. Real-world feasibility
The gate is inspectable policy. The detector is a ranking layer for social-engineering trajectories. Latency is a single-tree ensemble plus rule evaluation. False positives on first-time high-value payees are an explicit limitation.

## 11. Novelty argument
Deterministic provenance catches tool-tainted payments. Stochastic behavioral scoring catches conversations that look like a normal user request. Combined coverage is the argument.

## 12. Future work
KYC forgery fidelity, voice-clone fingerprinting, production taint tracking without labeled `attacker` roles, and a live closed-loop retrain job.
