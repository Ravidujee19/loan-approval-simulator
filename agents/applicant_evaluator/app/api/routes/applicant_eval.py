from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from ...schemas.applicant_profile import (
    ApplicantProfile,
    Features,
    Quality,
    Consistency,
    Provenance,
)
from ...services import (
    storage,
    nlp,
    rules,
    feature_builder,
    feature_vector,
    score_client,        # manith
    recommender_client,  # thenura
)

router = APIRouter(prefix="/api/v1/applicants", tags=["applicant-evaluator"])


# JSON body for form fields
class FormPayload(BaseModel):
    loan_id: str
    no_of_dependents: int | None = None
    education: str | None = None  # "Graduate" | "Not Graduate"
    self_employed: str | bool | None = None  # "Yes"/"No" or true/false
    income_annum: float | None = None
    loan_amount: float | None = None
    loan_term: int | None = None  # YEARS
    cibil_score: int | None = None
    residential_assets_value: float | None = None
    commercial_assets_value: float | None = None
    luxury_assets_value: float | None = None
    bank_asset_value: float | None = None


# helper
def _normalize_for_models(feat: dict) -> dict:
    out = dict(feat)

    # education
    edu = str(out.get("education", "")).strip()
    el = edu.lower()
    if el in {"grad", "graduate", "g"}:
        out["education"] = "Graduate"
    elif el in {"not graduate", "not_graduate", "non graduate", "non-graduate", "nongraduate", "ng"}:
        out["education"] = "Not Graduate"
    elif edu:
        out["education"] = "Unknown"
    else:
        out["education"] = "Unknown"

    # self_employed -> Yes/No
    se = out.get("self_employed")
    if isinstance(se, bool):
        out["self_employed"] = "Yes" if se else "No"
    else:
        s = str(se).strip().lower()
        out["self_employed"] = "Yes" if s in {"yes", "y", "true", "1"} else "No"

    # numeric coercions
    num_keys = [
        "no_of_dependents", "income_annum", "loan_amount", "loan_term", "cibil_score",
        "residential_assets_value", "commercial_assets_value", "luxury_assets_value", "bank_asset_value",
    ]
    for k in num_keys:
        v = out.get(k, None)
        if v is None or v == "":
            continue
        try:
            out[k] = float(v) if k != "loan_term" else int(float(v))  # loan_term is YEARS (int)
        except Exception:
            pass

    return out


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
            saved.append(
                {
                    "doc_id": doc_id,
                    "filename": f.filename,
                    "content_type": f.content_type,
                }
            )
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

    # 5) quality score
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

    # 6) construct vector in the exact CSV order
    order = feature_vector.FEATURE_ORDER
    vec = feature_vector.to_vector(feats, order)

    # 7) SCORE AGENT (SEND NORMALIZED DICT)
    feature_dict = feature_vector.feats_to_dict(feats)
    score_features = _normalize_for_models(feature_dict)  
    scored = score_client.score(score_features) or {}    

    # 8) RECOMMENDATION AGENT (also normalized)
    rec_features = _normalize_for_models(feature_dict)
    prediction = scored.get("prediction", "Rejected")
    approved = str(prediction).lower() == "approved"
    rec_input = {**rec_features, "approved": approved}

    recommendation = recommender_client.send_applicant_input(
        applicant_id=applicant_id,
        loan_id=payload.loan_id,
        applicant_input=rec_input,
    ) or {}

    # 9) persist + respond
    data = profile.model_dump()
    data["inference"] = scored
    data["recommendation"] = recommendation
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
