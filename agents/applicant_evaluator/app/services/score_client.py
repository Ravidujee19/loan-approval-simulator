import requests
from ..config import settings


def score(features: dict, vector: list[float], feature_order: list[str]) -> dict:
    
    url = settings().SCORE_AGENT_URL
    payload = {
        "features": features,        # dict (CSV-aligned)
        "vector": vector,            # numeric list aligned to feature_order
        "feature_order": feature_order
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}
