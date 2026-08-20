# Person A: Generate

Produces labeled JSONL transcripts for the defender and the demo.

## Outputs

- `data/flagship1_injections.jsonl` — 100 prompt-injection attacks
- `data/flagship2_poisonings.jsonl` — 100 multi-turn trust-poisoning attacks
- `data/flagship3_bias.jsonl` — 100 recommendation-bias attacks
- `data/legitimate_conversations.jsonl` — 100 legitimate baselines
- `data/GENERATION_REPORT.txt` — counts, sample IDs, limitations

## Fixtures

- `fixtures/merchant_pages.json` — 16 merchant injection pages
- `fixtures/personas.json` — 8 attacker personas
- `fixtures/legitimate_templates.json` — 10 legitimate payment templates
- `fixtures/biased_investments.json` — recommendation-bias pages

## Regenerate (offline, recommended)

```bash
python generate/harden_datasets.py
python generate/verify_fidelity.py
```

Live LLM generators (`generator_prompt_injection.py`, `generator_trust_poisoning.py`,
`generator_legitimate.py`) still work when `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or
`GEMINI_API_KEY` is set. They fall back to mocks otherwise.
