# Person B: Defender Pipeline

Two-layer defense: deterministic safety gate, then an ML fraud detector.

## Files for Person C

- `features.py` / `schemas.py` - `extract_features(transcript)`
- `gate.py` - `evaluate(transcript)`, `evaluate_transfer(...)`, `combine_layers(...)`
- `classifier.py` / `train.py` - trains XGBoost (falls back to GradientBoosting)
- `classifier_model.pkl` - trained model
- `feature_columns.json` - inference column order
- `evaluation_metrics.json` - precision, recall, F1, AUC, confusion matrix
- `breakdown_report.json` - gate vs ML coverage
- `evaluation_report.md` - judge-facing writeup

## Run

From the repository root:

```bash
python defend/run_all.py
```
