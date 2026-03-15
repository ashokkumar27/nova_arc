from __future__ import annotations


def risk_status(score: int) -> str:
    if score >= 85:
        return "Critical"
    if score >= 70:
        return "High"
    if score >= 40:
        return "Moderate"
    return "Low"


def risk_delta(initial_score: int, residual_score: int) -> int:
    return initial_score - residual_score


def default_context(pack_id: str) -> str:
    if pack_id == "cold_chain":
        return "Pharma DC / Vaccine Vault / KL North"
    return "National Grid / Substation East"


def default_transcript(pack_id: str) -> str:
    if pack_id == "cold_chain":
        return "Zone B temperature is above threshold. Batch VX-204 may be affected. Shipment SHP-884 is loading now."
    return "Transformer T-17 is overheating. Feeder F-12 is under stress. Substation East may cascade."


def classify_error(error_message: str) -> dict:
    lowered = error_message.lower()
    if any(token in lowered for token in ("accessdenied", "unauthorized", "iam", "model")):
        return {
            "title": "IAM Or Model Access Failure",
            "detail": "Check Bedrock model access, region configuration, and AWS credentials.",
        }
    if "invalid json" in lowered or "planner returned no strategy" in lowered:
        return {
            "title": "Planner Parse Failure",
            "detail": "Nova did not return the required strict JSON plan payload.",
        }
    if any(token in lowered for token in ("connectionrefused", "urlopen", "backend")):
        return {
            "title": "Bridge Or Backend Unavailable",
            "detail": "Start the local backend or verify the configured BACKEND_URL.",
        }
    return {"title": "Mission Run Failed", "detail": error_message}
