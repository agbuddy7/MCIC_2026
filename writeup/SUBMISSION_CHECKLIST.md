# Submission Checklist

## Required artifacts
- [x] Code repository
- [x] Solution walkthrough (`writeup/solution_walkthrough.md` and printable HTML)
- [x] Working web prototype (`webapp/`)

## Repository contents
- [x] `/identify` — taxonomy with 11 attacks and real-world grounding
- [x] `/generate` — generators, fixtures, JSONL datasets (flagship 1, 2, 3, legitimate)
- [x] `/defend` — gate, classifier, evaluation report, breakdown table
- [x] `/webapp` — React frontend + FastAPI backend
- [x] `/writeup` — walkthrough and this checklist

## Evaluation criteria mapped
- Diversity of attacks identified: 11 documented, 3 fully simulated
- Fidelity of attacks in simulation: schema-valid multi-turn JSONL
- Detection algorithm efficacy: precision / recall / F1 / AUC reported
- Novelty: closed-loop design and gate-vs-detector breakdown
- Real-world feasibility: Identify section plus gate/model limitations

## How to run the prototype
```bash
pip install -r requirements.txt
python webapp/backend/app.py
cd webapp/frontend && npm install && npm run dev
```
Open http://127.0.0.1:5173
