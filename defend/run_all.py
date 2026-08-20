#!/usr/bin/env python3
"""Run the full Person B defender pipeline."""

from breakdown import analyze
from evaluate import evaluate_model, write_evaluation_report
from train import train_model


def main() -> None:
    print("Training ML detector...")
    train_metrics = train_model()
    print(f"Training complete: F1={train_metrics['f1']:.3f}, AUC={train_metrics['auc']:.3f}")

    print("Evaluating ML detector...")
    eval_metrics = evaluate_model()
    print(f"Evaluation complete: F1={eval_metrics['f1']:.3f}, AUC={eval_metrics['auc']:.3f}")

    print("Generating gate-vs-detector breakdown...")
    breakdown = analyze()
    summary = breakdown["summary"]
    write_evaluation_report(eval_metrics, summary)
    print(
        "Combined defense complete: "
        f"gate={summary['gate_caught_rate']:.1%}, "
        f"detector={summary['detector_caught_rate']:.1%}, "
        f"combined={summary['combined_defense_rate']:.1%}"
    )


if __name__ == "__main__":
    main()
