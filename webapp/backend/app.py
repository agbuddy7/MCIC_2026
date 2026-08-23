#!/usr/bin/env python3
"""Person C API: run Person A's transcripts through Person B's gate and detector."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFEND_DIR = REPO_ROOT / "defend"
DATA_DIR = REPO_ROOT / "generate" / "data"
sys.path.insert(0, str(DEFEND_DIR))

from features import extract_features, load_default_datasets  # noqa: E402
from gate import DeterministicGate, combine_layers  # noqa: E402

app = FastAPI(title="MCIC Defense Lab", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FEATURE_COLUMNS = json.loads((DEFEND_DIR / "feature_columns.json").read_text(encoding="utf-8"))
MODEL = joblib.load(DEFEND_DIR / "classifier_model.pkl")
GATE = DeterministicGate()
TRANSCRIPTS = {row["conversation_id"]: row for row in load_default_datasets(DATA_DIR)}
METRICS = json.loads((DEFEND_DIR / "evaluation_metrics.json").read_text(encoding="utf-8"))
BREAKDOWN = json.loads((DEFEND_DIR / "breakdown_report.json").read_text(encoding="utf-8"))
TAXONOMY_PATH = REPO_ROOT / "identify" / "attack_taxonomy.md"


class SimulateRequest(BaseModel):
    conversationId: str


def score_transcript(transcript: dict) -> dict:
    gate_result = GATE.evaluate(transcript)
    features = extract_features(transcript)
    frame = pd.DataFrame([[features.get(col, 0) for col in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)
    probability = float(MODEL.predict_proba(frame)[0, 1])
    combined = combine_layers(gate_result, probability)
    return {
        "conversationId": transcript.get("conversation_id"),
        "attackType": transcript.get("attack_type"),
        "groundTruth": transcript.get("ground_truth_label"),
        "gateVerdict": combined["gate_verdict"],
        "gateReasons": combined["gate_reasons"],
        "detectorScore": combined["ml_fraud_probability"],
        "mlFlag": combined["ml_flag"],
        "finalVerdict": combined["verdict"],
        "transferDetails": transcript.get("transfer_details") or {},
        "transcript": transcript,
    }


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "transcripts": len(TRANSCRIPTS)}


@app.get("/api/catalog")
def catalog() -> dict:
    groups = {
        "prompt_injection_merchant_content": [],
        "multiturn_trust_poisoning": [],
        "recommendation_bias": [],
        "legitimate": [],
    }
    for transcript in TRANSCRIPTS.values():
        attack_type = transcript.get("attack_type")
        if attack_type in groups and len(groups[attack_type]) < 8:
            groups[attack_type].append(
                {
                    "conversationId": transcript["conversation_id"],
                    "attackType": attack_type,
                    "groundTruth": transcript.get("ground_truth_label"),
                    "amount": (transcript.get("transfer_details") or {}).get("amount"),
                    "payeeId": (transcript.get("transfer_details") or {}).get("payee_id"),
                }
            )
    featured = [
        groups["prompt_injection_merchant_content"][0]["conversationId"] if groups["prompt_injection_merchant_content"] else None,
        groups["multiturn_trust_poisoning"][0]["conversationId"] if groups["multiturn_trust_poisoning"] else None,
        groups["recommendation_bias"][0]["conversationId"] if groups["recommendation_bias"] else None,
        groups["legitimate"][0]["conversationId"] if groups["legitimate"] else None,
    ]
    return {"groups": groups, "featured": [item for item in featured if item]}


@app.post("/api/simulate")
def simulate(payload: SimulateRequest) -> dict:
    transcript = TRANSCRIPTS.get(payload.conversationId)
    if transcript is None:
        raise HTTPException(status_code=404, detail=f"Unknown conversationId: {payload.conversationId}")
    return score_transcript(transcript)


@app.get("/api/evaluation")
def evaluation() -> dict:
    return BREAKDOWN


@app.get("/api/metrics")
def metrics() -> dict:
    return METRICS


@app.get("/api/taxonomy")
def taxonomy() -> dict:
    return {"markdown": TAXONOMY_PATH.read_text(encoding="utf-8")}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5000)
