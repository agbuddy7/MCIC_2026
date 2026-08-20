#!/usr/bin/env python3
"""Shared transcript schema loader for Person A generators."""

from __future__ import annotations

import json
from pathlib import Path


SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas.json"


def load_transcript_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


ATTACK_TYPES = [
    "prompt_injection_merchant_content",
    "multiturn_trust_poisoning",
    "recommendation_bias",
    "legitimate",
]

SOURCE_OF_INSTRUCTION = ["user_explicit", "agent_inferred", "external_content"]
GROUND_TRUTH_LABELS = ["fraud", "legitimate"]
