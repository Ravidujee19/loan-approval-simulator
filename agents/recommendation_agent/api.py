# agents/recommendation_agent/api.py
from fastapi import FastAPI
from pydantic import BaseModel
from .predict import recommend

app = FastAPI(title="Recommendation Agent")

class RecommendPayload(BaseModel):
    applicant_id: str
    loan_id: str
    applicant_input: dict

@app.post("/api/v1/recommend")
def recommend_endpoint(p: RecommendPayload):
    approved = bool(p.applicant_input.get("approved", False))
    features = {k: v for k, v in p.applicant_input.items() if k != "approved"}
    return recommend(features, approved=approved)
