import requests
from ..config import settings
  
def score(features: dict) -> dict:
    try:
        r = requests.post(settings().SCORE_AGENT_URL, json=features, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

