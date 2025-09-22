# agents/applicant_evaluator/app/api/routes/metrics.py
from enum import Enum
from fastapi import APIRouter, Depends
from sqlalchemy import func

from agents.applicant_evaluator.app.api.deps import DB, require_role
from agents.applicant_evaluator.app.db.models import Evaluation, LoanApplication, UserRole

router = APIRouter(prefix="/metrics", tags=["metrics"])

def _json_key(v):
    # Normalize keys for JSON (Enums -> value, bool stays bool)
    if isinstance(v, Enum):
        return v.value
    return v

@router.get("")
def metrics(
    db: DB,
    user=Depends(require_role(UserRole.admin))
):
    total_loans = db.query(func.count(LoanApplication.id)).scalar() or 0

    by_status_rows = (
        db.query(LoanApplication.status, func.count(LoanApplication.id))
        .group_by(LoanApplication.status)
        .all()
    )
    by_status = { _json_key(k): v for k, v in by_status_rows }

    outcome_rows = (
        db.query(Evaluation.eligibility, func.count(Evaluation.id))
        .group_by(Evaluation.eligibility)
        .all()
    )
    outcomes = { _json_key(k): v for k, v in outcome_rows }

    return {
        "total_loans": total_loans,
        "by_status": by_status,
        "outcomes": outcomes,
        # "user_type": user.role.value,   
    }


# @router.get("")
# def metrics(db: DB, user=Depends(require_role(UserRole.admin))):  # capture logged-in admin
#     total_loans = db.query(func.count(LoanApplication.id)).scalar() or 0

#     by_status_rows = (
#         db.query(LoanApplication.status, func.count(LoanApplication.id))
#         .group_by(LoanApplication.status)
#         .all()
#     )
#     by_status = { _json_key(k): v for k, v in by_status_rows }

#     outcome_rows = (
#         db.query(Evaluation.eligibility, func.count(Evaluation.id))
#         .group_by(Evaluation.eligibility)
#         .all()
#     )
#     outcomes = { _json_key(k): v for k, v in outcome_rows }

#     return {
#         "total_loans": total_loans,
#         "by_status": by_status,
#         "outcomes": outcomes,
#         "user_type": user.role.value,
#     }


# # GET /metrics (admin)

# from fastapi import APIRouter, Depends
# from sqlalchemy import func

# from agents.applicant_evaluator.app.api.deps import DB, require_role
# from agents.applicant_evaluator.app.db.models import Evaluation, LoanApplication, UserRole

# router = APIRouter(prefix="/metrics", tags=["metrics"])


# @router.get("")
# def metrics(db: DB, _=Depends(require_role(UserRole.admin))):
#     total_loans = db.query(func.count(LoanApplication.id)).scalar()
#     by_status = dict(
#         db.query(LoanApplication.status, func.count(LoanApplication.id)).group_by(LoanApplication.status)
#     )
#     outcomes = dict(
#         db.query(Evaluation.eligibility, func.count(Evaluation.id)).group_by(Evaluation.eligibility)
#     )
#     return {"total_loans": total_loans or 0, "by_status": by_status, "outcomes": outcomes}
