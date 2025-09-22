from fastapi import APIRouter, Depends
from sqlalchemy import func

from agents.applicant_evaluator.app.api.deps import DB, get_current_user
from agents.applicant_evaluator.app.db.models import (
    Applicant,
    LoanApplication,
    LoanStatus,
    UserRole,
)

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
def get_stats(db: DB, user=Depends(get_current_user)):
    """
    Returns simple, dashboard-friendly JSON:
    {
      "total_loans": int,
      "by_status": {"approved": n, "rejected": n, ...},
      "outcomes": {"approved": n, "rejected": n, "pending": n},
      "user_type": "admin" | "applicant"
    }
    """
    # Base query: admin sees all loans; applicants see only their own (via Applicant.user_id)
    q = db.query(LoanApplication)
    if user["role"] != UserRole.admin.value:
        q = (
            q.join(Applicant, Applicant.id == LoanApplication.applicant_id)
             .filter(Applicant.user_id == user["sub"])
        )

    total_loans = q.count()

    rows = (
        q.with_entities(LoanApplication.status, func.count())
         .group_by(LoanApplication.status)
         .all()
    )
    by_status: dict[str, int] = {}
    for status_value, count in rows:
        # status_value might be an enum instance or a string depending on dialect
        key = status_value.value if hasattr(status_value, "value") else str(status_value)
        by_status[key] = int(count)

    outcomes = {
        "approved": by_status.get(LoanStatus.approved.value, 0),
        "rejected": by_status.get(LoanStatus.rejected.value, 0),
        "pending": (
            by_status.get(LoanStatus.submitted.value, 0)
            + by_status.get(LoanStatus.review.value, 0)
            + by_status.get(LoanStatus.evaluated.value, 0)
        ),
    }

    return {
        "total_loans": total_loans,
        "by_status": by_status,
        "outcomes": outcomes,
        "user_type": user["role"],
    }
