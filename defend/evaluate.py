#!/usr/bin/env python3
"""Evaluate the trained ML detector and write the Person B report."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import train_test_split

try:
    from .features import DEFAULT_DATA_DIR, FEATURE_COLUMNS, build_feature_table, load_default_datasets
except ImportError:
    from features import DEFAULT_DATA_DIR, FEATURE_COLUMNS, build_feature_table, load_default_datasets


DEFEND_DIR = Path(__file__).resolve().parent
MODEL_PATH = DEFEND_DIR / "classifier_model.pkl"
FEATURE_COLUMNS_PATH = DEFEND_DIR / "feature_columns.json"
METRICS_PATH = DEFEND_DIR / "evaluation_metrics.json"
REPORT_PATH = DEFEND_DIR / "evaluation_report.md"
BREAKDOWN_PATH = DEFEND_DIR / "breakdown_report.json"


def evaluate_model(data_dir: str | Path | None = None, threshold: float = 0.5, random_state: int = 42) -> dict:
    transcripts = load_default_datasets(data_dir or DEFAULT_DATA_DIR)
    x_table, y, _ = build_feature_table(transcripts)
    feature_columns = json.loads(FEATURE_COLUMNS_PATH.read_text(encoding="utf-8"))
    x_table = x_table.reindex(columns=feature_columns, fill_value=0)

    _, x_test, _, y_test = train_test_split(
        x_table,
        y,
        test_size=0.2,
        random_state=random_state,
        stratify=y,
    )

    model = joblib.load(MODEL_PATH)
    probabilities = model.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= threshold).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test,
        predictions,
        average="binary",
        zero_division=0,
    )
    tn, fp, fn, tp = confusion_matrix(y_test, predictions).ravel()

    metrics = {
        "model": "RandomForestClassifier",
        "threshold": threshold,
        "test_size": int(len(y_test)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "auc": float(roc_auc_score(y_test, probabilities)),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
        "feature_columns": feature_columns,
        "top_features": top_features(model, feature_columns),
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_evaluation_report(metrics)
    return metrics


def top_features(model, feature_columns: list[str], limit: int = 12) -> list[dict[str, float]]:
    importances = getattr(model, "feature_importances_", None)
    if importances is None:
        return []
    ranked = sorted(zip(feature_columns, importances), key=lambda item: item[1], reverse=True)
    return [{"feature": name, "importance": float(score)} for name, score in ranked[:limit]]


def load_breakdown_summary() -> dict | None:
    if not BREAKDOWN_PATH.exists():
        return None
    payload = json.loads(BREAKDOWN_PATH.read_text(encoding="utf-8"))
    return payload.get("summary")


def pct_cell(value: float) -> str:
    return f"{value:.1%}"


def write_evaluation_report(metrics: dict | None = None, breakdown_summary: dict | None = None) -> Path:
    if metrics is None and METRICS_PATH.exists():
        metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    if metrics is None:
        raise FileNotFoundError("evaluation metrics are missing; run evaluate.py first")

    summary = breakdown_summary or load_breakdown_summary()
    matrix = metrics["confusion_matrix"]
    top = "\n".join(
        f"- `{item['feature']}`: {item['importance']:.4f}" for item in metrics.get("top_features", [])
    ) or "- Feature importances unavailable."

    if summary:
        breakdown_table = f"""| Defense Result | Count | Percentage |
|---|---:|---:|
| Gate caught | {summary['gate_caught']} | {pct_cell(summary['gate_caught_rate'])} |
| Detector caught | {summary['detector_caught']} | {pct_cell(summary['detector_caught_rate'])} |
| Both caught | {summary['both_caught']} | {pct_cell(summary['both_caught_rate'])} |
| Missed | {summary['missed']} | {pct_cell(summary['missed_rate'])} |
| Combined defense | {summary['total_attacks'] - summary['missed']} | {pct_cell(summary['combined_defense_rate'])} |

Evaluated on {summary['total_attacks']} fraud conversations. Exclusive split: gate only {summary.get('gate_only', 0)}, detector only {summary.get('detector_only', 0)}."""
    else:
        breakdown_table = "_Run `python defend/breakdown.py` to fill this table._"

    feature_list = "\n".join(f"- `{name}`" for name in metrics.get("feature_columns", FEATURE_COLUMNS))

    report = f"""# Person B Defense Evaluation

The deterministic gate catches high-confidence provenance risks, while the ML detector
catches subtle behavioral fraud that rules alone miss. The combined system performs
better than either layer alone.

## 1. Features extracted

Each conversation JSONL record is converted by `extract_features()` into:

{feature_list}

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

- Model: `{metrics.get('model', 'RandomForestClassifier')}`
- Labels: `fraud → 1`, `legitimate → 0`
- Split: 80% train / 20% test, stratified by label
- Decision threshold: `{metrics['threshold']:.2f}`
- Test size: `{metrics['test_size']}`

## 4. Precision / Recall / F1 / AUC

| Metric | Value |
|---|---:|
| Precision | {metrics['precision']:.3f} |
| Recall | {metrics['recall']:.3f} |
| F1 | {metrics['f1']:.3f} |
| AUC | {metrics['auc']:.3f} |

### Confusion matrix

|  | Predicted Legitimate | Predicted Fraud |
|---|---:|---:|
| Actual Legitimate | {matrix['true_negative']} | {matrix['false_positive']} |
| Actual Fraud | {matrix['false_negative']} | {matrix['true_positive']} |

### Top model features

{top}

## 5. Gate vs detector breakdown

{breakdown_table}

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
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    return REPORT_PATH


def main() -> None:
    metrics = evaluate_model()
    print(json.dumps({k: v for k, v in metrics.items() if k != "feature_columns"}, indent=2))
    print(f"Saved metrics to {METRICS_PATH}")
    print(f"Saved report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
