import requests
from ..config import settings
  
def score(features: dict) -> dict:
    try:
        r = requests.post(settings().SCORE_AGENT_URL, json=features, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}
    
    
# version 0.1
# def score(features: dict) -> dict:
#     """
#     Send only the raw CSV-aligned feature dict to the score agent.
#     The score agent expects a flat applicant dict at POST /score.
#     """
#     url = settings().SCORE_AGENT_URL
#     try:
#         resp = requests.post(url, json=features, timeout=10)
#         resp.raise_for_status()
#         return resp.json()
#     except Exception as e:
#         return {"error": str(e)}
