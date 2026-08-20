# MCIC 2026 Agentic Payment Fraud Defense

This repository contains a red-team/blue-team simulation for GenAI-enabled payment fraud.

## Project Structure

- `generate/` - synthetic conversation generators and final JSONL datasets
- `generate/data/` - labeled transcript datasets used by the defender
- `generate/fixtures/` - source fixtures for merchant pages, personas, and biased recommendations
- `identify/` - attack taxonomy and research notes
- `schemas.json` - shared transcript schema
- `attack_handover_specification.md` - attacker-to-defender handoff notes

## Final Datasets

Each JSONL file contains one conversation transcript per line.

- `generate/data/flagship1_injections.jsonl` - prompt injection via merchant content, 100 rows
- `generate/data/flagship2_poisonings.jsonl` - multi-turn trust poisoning, 100 rows
- `generate/data/flagship3_bias.jsonl` - recommendation bias/context poisoning, 100 rows
- `generate/data/legitimate_conversations.jsonl` - legitimate but suspicious-looking baseline, 100 rows

## Regenerate Hardened Datasets

```bash
python generate/harden_datasets.py
python generate/verify_fidelity.py
python defend/run_all.py
```

The hardening script creates deterministic, schema-compatible data with realistic payee IDs,
more varied templates, matched transfer amounts, and extra metadata useful for defender features.

## Validate Data

```bash
python generate/verify_fidelity.py
```

Expected result: all four JSONL files validate successfully against the shared schema.

## Defender Handoff

Person B should train on:

- fraud class: `flagship1_injections.jsonl`, `flagship2_poisonings.jsonl`, `flagship3_bias.jsonl`
- legitimate class: `legitimate_conversations.jsonl`

The deterministic gate should prioritize hard provenance signals such as
`source_of_instruction == "external_content"`, while the ML detector should learn behavioral
signals such as urgency, planted payees, rapport-building, authority language, and recommendation
steering.
