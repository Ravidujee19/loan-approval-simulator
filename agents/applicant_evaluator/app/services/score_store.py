from __future__ import annotations
import json
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import joinedload
from agents.applicant_evaluator.app.core.config import settings
from agents.applicant_evaluator.app.db.models import LoanApplication

def _coerce(v: Any) -> Any:
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (UUID, )):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, list):
        return [_coerce(x) for x in v]
    if isinstance(v, dict):
        return {k: _coerce(x) for k, x in v.items()}
    return v

def build_bundle(loan: LoanApplication,
                 *,
                 correlation_id: Optional[str] = None,
                 idempotency_key: Optional[str] = None) -> Dict[str, Any]:
    a = loan.applicant
    e = loan.evaluation
    bundle: Dict[str, Any] = {
        "meta": {
            "correlation_id": correlation_id,
            "idempotency_key": idempotency_key,
        },
        "loan": {
            "loan_id": str(loan.id),
            "applicant_id": str(loan.applicant_id),
            "amount_requested": _coerce(loan.amount_requested),
            "term_months": loan.term_months,
            "loan_type": loan.loan_type,
            "purpose": loan.purpose,
            "status": getattr(loan.status, "value", str(loan.status)),
            "application_date": loan.application_date.isoformat() if loan.application_date else None,
        },
        "applicant": None,
        "evaluation": None,
    }
    if a:
        bundle["applicant"] = {
            "applicant_id": str(a.id),
            "first_name": a.first_name,
            "last_name": a.last_name,
            "email": a.email,
            "phone": a.phone,
            "dob": a.dob.isoformat() if a.dob else None,
            "employment_status": a.employment_status,
            "employer_name": a.employer_name,
            "monthly_income": _coerce(a.monthly_income),
            "other_income": _coerce(a.other_income),
            "existing_monthly_debt": _coerce(a.existing_monthly_debt),
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
    if e:
        bundle["evaluation"] = {
            "evaluation_id": str(e.id),
            "loan_id": str(e.loan_id),
            "eligibility": e.eligibility,
            "score": e.score,
            "reasons": list(e.reasons or []),
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
    return bundle

def save_bundle(loan: LoanApplication,
                *,
                correlation_id: Optional[str] = None,
                idempotency_key: Optional[str] = None) -> str:
    """Writes data/score_store/<loan_id>.json; returns file path."""
    folder = Path(settings().SCORE_STORE_DIR)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{loan.id}.json"
    payload = build_bundle(loan, correlation_id=correlation_id, idempotency_key=idempotency_key)
    # ensure JSON-serializable
    payload = _coerce(payload)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), indent=2), encoding="utf-8")
    return str(path)

def load_bundle_path(loan_id: UUID | str) -> str:
    return str(Path(settings().SCORE_STORE_DIR) / f"{loan_id}.json")
