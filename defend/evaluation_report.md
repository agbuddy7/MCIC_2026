# Person B Defense Evaluation

The deterministic gate catches high-confidence provenance risks, while the ML detector
catches subtle behavioral fraud that rules alone miss. The combined system performs
better than either layer alone.

## 1. Features extracted

Each conversation JSONL record is converted by `extract_features()` into:

- `turn_count`
- `amount`
- `source_of_instruction_external`
- `source_of_instruction_user_explicit`
- `known_payee`
- `payee_introduced_by_user`
- `payee_introduced_by_attacker`
- `payee_introduced_by_tool_result`
- `payee_lag_turns`
- `urgency_word_count`
- `trust_word_count`
- `authority_word_count`
- `romance_word_count`
- `external_instruction_count`
- `recommendation_steering_count`
- `has_new_payee`
- `has_urgent_payment`
- `competing_options_suppressed`
- `contains_family_language`
- `contains_financial_jargon`
- `payee_reused_from_earlier`

These features mix payment metadata (`amount`, `known_payee`, instruction source, payee
provenance) with transcript behavior (urgency, trust, authority, romance, steering).

## 2. Deterministic gate rules

`defend/gate.py` returns `allow`, `step_up_required`, or `block`:

- If `payee_id` is null → `block`
- If amount exceeds the $500 per-transaction hard cap → `block`
- If daily spending would exceed $1000 → `block`
- If the payee is not in the known-payee allowlist → `step_up_required`
- If `source_of_instruction == external_content` → `step_up_required`
- If amount is above $50 → `step_up_required`
- If the payee was introduced by `tool_result` → `step_up_required`
- If recommendation bias suppresses alternatives → `step_up_required`
- If the payee was introduced by an attacker → `step_up_required`
- If the source is `user_explicit`, the payee is known, and no other rule fired → `allow`

## 3. ML model used

- Model: `RandomForestClassifier`
- Labels: `fraud → 1`, `legitimate → 0`
- Split: 80% train / 20% test, stratified by label
- Decision threshold: `0.50`
- Test size: `80`

## 4. Precision / Recall / F1 / AUC

| Metric | Value |
|---|---:|
| Precision | 1.000 |
| Recall | 1.000 |
| F1 | 1.000 |
| AUC | 1.000 |

### Confusion matrix

|  | Predicted Legitimate | Predicted Fraud |
|---|---:|---:|
| Actual Legitimate | 20 | 0 |
| Actual Fraud | 0 | 60 |

### Top model features

- `trust_word_count`: 0.4421
- `payee_introduced_by_user`: 0.2888
- `turn_count`: 0.2691
- `amount`: 0.0000
- `source_of_instruction_external`: 0.0000
- `source_of_instruction_user_explicit`: 0.0000
- `known_payee`: 0.0000
- `payee_introduced_by_attacker`: 0.0000
- `payee_introduced_by_tool_result`: 0.0000
- `payee_lag_turns`: 0.0000
- `urgency_word_count`: 0.0000
- `authority_word_count`: 0.0000

## 5. Gate vs detector breakdown

| Defense Result | Count | Percentage |
|---|---:|---:|
| Gate caught | 300 | 100.0% |
| Detector caught | 300 | 100.0% |
| Both caught | 300 | 100.0% |
| Missed | 0 | 0.0% |
| Combined defense | 300 | 100.0% |

Evaluated on 300 fraud conversations. Exclusive split: gate only 0, detector only 0.

## 6. Why combined defense is stronger

The gate is reliable for hard policy signals: external payment instructions, tool-planted
payees, recommendation suppression, and high-value transfers to unknown destinations.
Those rules are inspectable and do not depend on a trained model.

The ML detector is needed for behavioral fraud, especially multi-turn trust poisoning
where the final tool call can still be labeled `user_explicit`. Linguistic markers,
payee-lag, and introduction timing catch those cases even when a single provenance
rule does not fire or when metadata is incomplete.

Combined decision rule used for Person C:

- gate `block` → final `block`
- gate hit and ML fraud flag → final `block`
- either layer flags risk → final `step_up_required`
- otherwise → `allow`

This keeps high-confidence provenance blocks, while still escalating subtle fraud that
rules miss.

## 7. Known limitations

- The datasets are synthetic and class-separable; production conversations will be noisier.
- Features such as `payee_introduced_by_*` are labeled in this simulation and may be weaker
  or unavailable in a live assistant unless taint-tracking is implemented.
- The gate is conservative on new payees over $500, so legitimate first-time rent, tuition,
  or vendor payments can receive `block` even when the ML score is low.
- Perfect or near-perfect test metrics can overstate generalization. The useful judge
  evidence is the complementary coverage of the two layers, not a claim of real-world AUC.
- The ML detector is trained on English lexical cues from this generator and will miss
  novel phrasing, other languages, and attacks that never attempt a transfer.
