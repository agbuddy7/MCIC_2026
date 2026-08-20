#!/usr/bin/env python3
"""Convert conversation transcripts into ML-readable numeric features."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .schemas import (
        AUTHORITY_KEYWORDS,
        EXTERNAL_INSTRUCTION_KEYWORDS,
        FAMILY_KEYWORDS,
        FEATURE_SCHEMA,
        FINANCIAL_KEYWORDS,
        ROMANCE_KEYWORDS,
        STEERING_KEYWORDS,
        TRUST_BUILDING_PHRASES,
        URGENCY_KEYWORDS,
    )
except ImportError:
    from schemas import (
        AUTHORITY_KEYWORDS,
        EXTERNAL_INSTRUCTION_KEYWORDS,
        FAMILY_KEYWORDS,
        FEATURE_SCHEMA,
        FINANCIAL_KEYWORDS,
        ROMANCE_KEYWORDS,
        STEERING_KEYWORDS,
        TRUST_BUILDING_PHRASES,
        URGENCY_KEYWORDS,
    )


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = REPO_ROOT / "generate" / "data"

DATA_FILES = [
    "flagship1_injections.jsonl",
    "flagship2_poisonings.jsonl",
    "flagship3_bias.jsonl",
    "legitimate_conversations.jsonl",
]

FEATURE_COLUMNS = list(FEATURE_SCHEMA.keys())


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load a JSONL file into transcript dictionaries."""
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_default_datasets(data_dir: str | Path | None = None) -> list[dict[str, Any]]:
    """Load all standard defender training datasets that exist."""
    base = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    rows: list[dict[str, Any]] = []
    for filename in DATA_FILES:
        path = base / filename
        if path.exists():
            rows.extend(load_jsonl(path))
    if not rows:
        raise FileNotFoundError(f"No defender datasets found in {base}")
    return rows


def transcript_text(transcript: dict[str, Any]) -> str:
    return "\n".join(str(turn.get("content", "")) for turn in transcript.get("turns", []))


def count_terms(text: str, terms) -> int:
    lowered = text.lower()
    total = 0
    for term in terms:
        total += len(re.findall(rf"\b{re.escape(str(term).lower())}\b", lowered))
    return total


def extract_features(transcript: dict[str, Any]) -> dict[str, float | int]:
    """Convert one conversation transcript into numeric ML features."""
    details = transcript.get("transfer_details") or {}
    text = transcript_text(transcript)
    amount = float(details.get("amount") or 0)
    source = details.get("source_of_instruction") or ""
    introduced_by = transcript.get("payee_introduced_by") or ""
    known_payee = bool(transcript.get("known_payee", False))
    payee_first = transcript.get("payee_first_mentioned_turn")
    payment_turn = transcript.get("payment_requested_turn")
    payee_lag = 0
    if isinstance(payee_first, int) and isinstance(payment_turn, int):
        payee_lag = max(0, payment_turn - payee_first)
    elif details.get("payee_id"):
        payee_id = str(details["payee_id"])
        first = None
        turns = transcript.get("turns") or []
        for idx, turn in enumerate(turns):
            if payee_id in str(turn.get("content", "")):
                first = idx
                break
        if first is not None:
            payee_lag = max(0, len(turns) - 1 - first)

    urgency_word_count = count_terms(text, URGENCY_KEYWORDS)
    return {
        "turn_count": int(transcript.get("turn_count") or len(transcript.get("turns", []))),
        "amount": amount,
        "source_of_instruction_external": int(source == "external_content"),
        "source_of_instruction_user_explicit": int(source == "user_explicit"),
        "known_payee": int(known_payee),
        "payee_introduced_by_user": int(introduced_by == "user"),
        "payee_introduced_by_attacker": int(introduced_by == "attacker"),
        "payee_introduced_by_tool_result": int(introduced_by == "tool_result"),
        "payee_lag_turns": payee_lag,
        "urgency_word_count": urgency_word_count,
        "trust_word_count": count_terms(text, TRUST_BUILDING_PHRASES),
        "authority_word_count": count_terms(text, AUTHORITY_KEYWORDS),
        "romance_word_count": count_terms(text, ROMANCE_KEYWORDS),
        "external_instruction_count": count_terms(text, EXTERNAL_INSTRUCTION_KEYWORDS),
        "recommendation_steering_count": count_terms(text, STEERING_KEYWORDS),
        "has_new_payee": int(not known_payee),
        "has_urgent_payment": int(urgency_word_count > 0 and bool(transcript.get("final_transfer_attempted"))),
        "competing_options_suppressed": int(bool(transcript.get("competing_options_suppressed", False))),
        "contains_family_language": int(count_terms(text, FAMILY_KEYWORDS) > 0),
        "contains_financial_jargon": count_terms(text, FINANCIAL_KEYWORDS),
        "payee_reused_from_earlier": int(payee_lag > 2),
    }


extract_features_from_transcript = extract_features


def extract_features_from_jsonl(jsonl_file: str | Path) -> pd.DataFrame:
    """Load one JSONL file and extract a feature table."""
    transcripts = load_jsonl(jsonl_file)
    frame = pd.DataFrame.from_records([extract_features(row) for row in transcripts]).fillna(0)
    return frame.reindex(columns=FEATURE_COLUMNS, fill_value=0)


def build_feature_table(transcripts: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    """Build X/y tables and return the stable feature column ordering."""
    records = [extract_features(row) for row in transcripts]
    frame = pd.DataFrame.from_records(records).fillna(0)
    labels = pd.Series(
        [1 if row.get("ground_truth_label") == "fraud" else 0 for row in transcripts],
        name="label",
    )
    frame = frame.reindex(columns=FEATURE_COLUMNS, fill_value=0)
    return frame, labels, list(FEATURE_COLUMNS)


if __name__ == "__main__":
    data = load_default_datasets()
    x_table, y, feature_columns = build_feature_table(data)
    print(f"Loaded {len(data)} transcripts")
    print(f"Feature columns ({len(feature_columns)}):")
    for column in feature_columns:
        print(f"- {column}")
    print("Label counts:")
    print(y.value_counts().to_string())
