# GET /evaluations/{id}

from fastapi import APIRouter, Depends, HTTPException

from agents.applicant_evaluator.app.api.deps import DB, get_current_user
from agents.applicant_evaluator.app.db.models import Evaluation

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/{evaluation_id}")
def get_eval(evaluation_id: str, db: DB, _=Depends(get_current_user)):
    ev = db.get(Evaluation, evaluation_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "evaluation_id": str(ev.id),
        "loan_id": str(ev.loan_id),
        "eligibility": ev.eligibility,
        "score": ev.score,
        "reasons": ev.reasons,
        "created_at": ev.created_at,
    }
