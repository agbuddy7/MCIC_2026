#!/usr/bin/env python3
"""Compare deterministic gate coverage with ML detector coverage."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

try:
    from .evaluate import write_evaluation_report
    from .features import DEFAULT_DATA_DIR, extract_features, load_default_datasets
    from .gate import GATE_HIT, DeterministicGate
except ImportError:
    from evaluate import write_evaluation_report
    from features import DEFAULT_DATA_DIR, extract_features, load_default_datasets
    from gate import GATE_HIT, DeterministicGate


DEFEND_DIR = Path(__file__).resolve().parent
MODEL_PATH = DEFEND_DIR / "classifier_model.pkl"
FEATURE_COLUMNS_PATH = DEFEND_DIR / "feature_columns.json"
BREAKDOWN_PATH = DEFEND_DIR / "breakdown_report.json"
BREAKDOWN_MD_PATH = DEFEND_DIR / "breakdown_report.md"


def analyze(data_dir: str | Path | None = None, threshold: float = 0.5) -> dict:
    transcripts = load_default_datasets(data_dir or DEFAULT_DATA_DIR)
    fraud_transcripts = [row for row in transcripts if row.get("ground_truth_label") == "fraud"]
    feature_columns = json.loads(FEATURE_COLUMNS_PATH.read_text(encoding="utf-8"))
    x_table = pd.DataFrame([extract_features(row) for row in fraud_transcripts]).reindex(
        columns=feature_columns, fill_value=0
    )

    model = joblib.load(MODEL_PATH)
    gate = DeterministicGate()
    probabilities = model.predict_proba(x_table)[:, 1]

    exclusive = {"gate_caught": 0, "detector_caught": 0, "both_caught": 0, "missed": 0}
    details = []

    for transcript, probability in zip(fraud_transcripts, probabilities):
        gate_result = gate.evaluate(transcript)
        gate_hit = gate_result["verdict"] in GATE_HIT
        detector_hit = float(probability) >= threshold

        if gate_hit and detector_hit:
            exclusive["both_caught"] += 1
            category = "both_caught"
        elif gate_hit:
            exclusive["gate_caught"] += 1
            category = "gate_caught"
        elif detector_hit:
            exclusive["detector_caught"] += 1
            category = "detector_caught"
        else:
            exclusive["missed"] += 1
            category = "missed"

        details.append(
            {
                "conversation_id": transcript.get("conversation_id"),
                "attack_type": transcript.get("attack_type"),
                "category": category,
                "gate_verdict": gate_result["verdict"],
                "gate_reasons": gate_result["reasons"],
                "detector_fraud_probability": float(probability),
            }
        )

    total = len(fraud_transcripts)
    gate_caught_total = exclusive["gate_caught"] + exclusive["both_caught"]
    detector_caught_total = exclusive["detector_caught"] + exclusive["both_caught"]
    combined_caught = total - exclusive["missed"]
    summary = {
        "total_attacks": total,
        "gate_only": exclusive["gate_caught"],
        "detector_only": exclusive["detector_caught"],
        "both_caught": exclusive["both_caught"],
        "missed": exclusive["missed"],
        "gate_caught": gate_caught_total,
        "detector_caught": detector_caught_total,
        "gate_caught_rate": pct(gate_caught_total, total),
        "detector_caught_rate": pct(detector_caught_total, total),
        "gate_only_rate": pct(exclusive["gate_caught"], total),
        "detector_only_rate": pct(exclusive["detector_caught"], total),
        "both_caught_rate": pct(exclusive["both_caught"], total),
        "missed_rate": pct(exclusive["missed"], total),
        "combined_defense_rate": pct(combined_caught, total),
        "gate_catch_rate": pct(gate_caught_total, total),
        "detector_catch_rate": pct(detector_caught_total, total),
        "combined_catch_rate": pct(combined_caught, total),
        "false_negative_rate": pct(exclusive["missed"], total),
        "total_transcripts": total,
        "threshold": threshold,
        "exclusive_outcomes": exclusive,
    }

    report = {"summary": summary, "details": details}
    BREAKDOWN_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    BREAKDOWN_MD_PATH.write_text(render_markdown(summary), encoding="utf-8")
    write_evaluation_report(breakdown_summary=summary)
    return report


def pct(count: int, total: int) -> float:
    return float(count / total) if total else 0.0


def render_markdown(summary: dict) -> str:
    return f"""# Gate vs ML Detector Breakdown

Evaluated on {summary['total_attacks']} simulated fraud attacks.

| Defense Result | Count | Percentage |
|---|---:|---:|
| Gate caught | {summary['gate_caught']} | {summary['gate_caught_rate']:.1%} |
| Detector caught | {summary['detector_caught']} | {summary['detector_caught_rate']:.1%} |
| Both caught | {summary['both_caught']} | {summary['both_caught_rate']:.1%} |
| Missed | {summary['missed']} | {summary['missed_rate']:.1%} |
| Combined defense | {summary['total_attacks'] - summary['missed']} | {summary['combined_defense_rate']:.1%} |

The deterministic gate catches high-confidence provenance risks. The ML detector catches
subtle behavioral fraud that rules alone miss. Combined defense is stronger than either
layer alone.
"""


def main() -> None:
    report = analyze()
    print(json.dumps(report["summary"], indent=2))
    print(f"Saved breakdown to {BREAKDOWN_PATH}")


if __name__ == "__main__":
    main()
