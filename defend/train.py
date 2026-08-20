#!/usr/bin/env python3
"""Train the behavioral ML fraud detector."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import train_test_split

try:
    from .features import DEFAULT_DATA_DIR, build_feature_table, load_default_datasets
except ImportError:
    from features import DEFAULT_DATA_DIR, build_feature_table, load_default_datasets


DEFEND_DIR = Path(__file__).resolve().parent
MODEL_PATH = DEFEND_DIR / "classifier_model.pkl"
FEATURE_COLUMNS_PATH = DEFEND_DIR / "feature_columns.json"
TRAINING_METRICS_PATH = DEFEND_DIR / "training_metrics.json"


def build_classifier(random_state: int = 42):
    try:
        from xgboost import XGBClassifier

        return XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=random_state,
        ), "XGBClassifier"
    except ImportError:
        from sklearn.ensemble import GradientBoostingClassifier

        return GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=5,
            random_state=random_state,
        ), "GradientBoostingClassifier"


def train_model(data_dir: str | Path | None = None, random_state: int = 42) -> dict:
    transcripts = load_default_datasets(data_dir or DEFAULT_DATA_DIR)
    x_table, y, feature_columns = build_feature_table(transcripts)

    x_train, x_test, y_train, y_test = train_test_split(
        x_table,
        y,
        test_size=0.2,
        random_state=random_state,
        stratify=y,
    )

    model, model_name = build_classifier(random_state)
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(x_test)[:, 1]
    else:
        probabilities = predictions.astype(float)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test,
        predictions,
        average="binary",
        zero_division=0,
    )

    metrics = {
        "model": model_name,
        "total_transcripts": len(transcripts),
        "train_size": int(len(x_train)),
        "test_size": int(len(x_test)),
        "fraud_count": int(y.sum()),
        "legitimate_count": int((y == 0).sum()),
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "auc": float(roc_auc_score(y_test, probabilities)),
    }

    DEFEND_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    FEATURE_COLUMNS_PATH.write_text(json.dumps(feature_columns, indent=2), encoding="utf-8")
    TRAINING_METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def main() -> None:
    metrics = train_model()
    print(json.dumps(metrics, indent=2))
    print(f"Saved model to {MODEL_PATH}")
    print(f"Saved feature columns to {FEATURE_COLUMNS_PATH}")


if __name__ == "__main__":
    main()
