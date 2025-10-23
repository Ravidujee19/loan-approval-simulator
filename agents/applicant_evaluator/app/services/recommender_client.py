import requests
from ..config import settings

def send_applicant_input(applicant_id: str, loan_id: str, applicant_input: dict) -> dict:
    url = getattr(settings(), "RECOMMENDER_URL", None)
    if not url:
        return {"error": "RECOMMENDER_URL not set"}
    payload = {
        "applicant_id": applicant_id,
        "loan_id": loan_id,
        "applicant_input": applicant_input,
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}
