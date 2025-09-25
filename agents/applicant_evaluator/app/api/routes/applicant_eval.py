from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
# import requests
# from ..config import settings

from ...schemas.applicant_profile import ApplicantProfile, Features, Quality, Consistency, Provenance
from ...services import storage, nlp, rules, feature_builder, feature_vector, score_client


router = APIRouter(prefix="/api/v1/applicants", tags=["applicant-evaluator"])

# JSON body for form fields (frontend-friendly)
class FormPayload(BaseModel):
    loan_id: str
    no_of_dependents: int | None = None
    education: str | None = None        # "Graduate" | "Not Graduate"
    self_employed: str | bool | None = None  # "Yes"/"No" or true/false
    income_annum: float | None = None
    loan_amount: float | None = None
    loan_term: int | None = None        # YEARS
    cibil_score: int | None = None
    residential_assets_value: float | None = None
    commercial_assets_value: float | None = None
    luxury_assets_value: float | None = None
    bank_asset_value: float | None = None

@router.post("/", response_model=dict)
def create_applicant():
    applicant_id = str(uuid.uuid4())
    storage.ensure_bucket(applicant_id)
    return {"applicant_id": applicant_id}

@router.post("/{applicant_id}/documents")
async def upload_documents(applicant_id: str, files: List[UploadFile] = File(...)):
    try:
        saved = []
        for f in files:
            doc_id, _ = storage.save_upload(applicant_id, f.filename, f.file)
            saved.append({"doc_id": doc_id, "filename": f.filename, "content_type": f.content_type})
        return {"applicant_id": applicant_id, "saved": saved}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"upload failed: {e}")

@router.post("/{applicant_id}/evaluate-with-form", response_model=dict)
async def evaluate_with_form(applicant_id: str, payload: FormPayload, request: Request):
    # 1) pull docs and run lightweight NLP
    docs = storage.list_docs(applicant_id)
    raw_texts = [storage.read_text(d["path"]) for d in docs]
    doc_fields, provenance, confidences, extras = nlp.extract_from_texts(docs, raw_texts)

    # 2) merge form → doc (form wins when provided)
    provided = {k: v for k, v in payload.model_dump().items() if v is not None}
    merged = {**doc_fields, **provided}

    # 3) rules checks
    warnings, hard_stops = rules.check(merged)

    # 4) build CSV-aligned features (exclude label loan_status)
    feats: Features = feature_builder.to_features(merged)

    # 5) quality score (simple avg of field confidences we extracted from docs)
    overall_conf = (sum(confidences.values()) / max(len(confidences), 1)) if confidences else 0.0
    quality = Quality(overall_confidence=overall_conf, field_confidence=confidences)

    profile = ApplicantProfile(
        applicant_id=applicant_id,
        loan_id=payload.loan_id,
        features=feats,
        quality=quality,
        consistency=Consistency(warnings=warnings, hard_stops=hard_stops),
        provenance=[Provenance(**p) for p in provenance],
        extra_extracted=extras,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )

    # 6) construct vector in the exact CSV order (minus label)
    order = feature_vector.FEATURE_ORDER
    vec = feature_vector.to_vector(feats, order)

    # 7) hand-off to your friend's score_agent
    scored = score_client.score(
        features={
            # send raw feature dict (already aligned to CSV keys)
            "no_of_dependents": feats.no_of_dependents,
            "education": feats.education,
            "self_employed": feats.self_employed,
            "income_annum": feats.income_annum,
            "loan_amount": feats.loan_amount,
            "loan_term": feats.loan_term,
            "cibil_score": feats.cibil_score,
            "residential_assets_value": feats.residential_assets_value,
            "commercial_assets_value": feats.commercial_assets_value,
            "luxury_assets_value": feats.luxury_assets_value,
            "bank_asset_value": feats.bank_asset_value,
        },
        vector=vec,
        feature_order=order
    )

    # 8) persist + respond
    data = profile.model_dump()
    data["inference"] = scored
    data["vector"] = vec
    data["vector_order"] = order

    storage.save_profile(applicant_id, payload.loan_id, data)
    return data

@router.get("/{applicant_id}/profile", response_model=dict)
def get_profile(applicant_id: str, loan_id: str):
    data = storage.load_profile(applicant_id, loan_id)
    if not data:
        raise HTTPException(status_code=404, detail="profile not found")
    return data


# def send_applicant_input(applicant_id: str, loan_id: str, applicant_input: dict) -> dict:
#     url = settings().RECOMMENDER_URL
#     payload = {
#         "applicant_id": applicant_id,
#         "loan_id": loan_id,
#         "applicant_input": applicant_input,
#     }
#     try:
#         r = requests.post(url, json=payload, timeout=15)
#         r.raise_for_status()
#         return r.json()
#     except Exception as e:
#         return {"error": str(e)}