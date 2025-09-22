# agents/applicant_evaluator/app/api/routes/loans.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import joinedload
from agents.applicant_evaluator.app.api.deps import DB, get_current_user, require_role
from agents.applicant_evaluator.app.db.models import Applicant, LoanApplication, UserRole
from agents.applicant_evaluator.app.schemas.loan import LoanCreate, LoanOut
from agents.applicant_evaluator.app.services.evaluator import evaluate_loan
from agents.applicant_evaluator.app.services.idempotency import IdempotencyStore
from agents.applicant_evaluator.app.services.score_store import save_bundle

router = APIRouter(prefix="/loans", tags=["loans"])

@router.post("", response_model=LoanOut)
def create_loan(
    payload: LoanCreate,
    request: Request,
    db: DB,
    user=Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    # ---- JSON-safe key for idempotency (UUID, Decimal etc. become strings)
    key_payload = payload.model_dump(mode="json")

    if idempotency_key:
        stored = IdempotencyStore.get(idempotency_key, key_payload)
        if stored:
            return LoanOut.model_validate(stored)

    # Ownership / existence checks
    applicant = db.get(Applicant, UUID(str(payload.applicant_id)))
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    if user["role"] != UserRole.admin.value and str(applicant.user_id) != user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Create loan
    loan = LoanApplication(
        applicant_id=payload.applicant_id,
        amount_requested=payload.amount_requested,
        term_months=payload.term_months,
        loan_type=payload.loan_type,
        purpose=payload.purpose,
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)

    # Evaluate and attach result
    evaluation = evaluate_loan(db, loan)
    loan.evaluation_id = evaluation.id
    db.add(loan)
    db.commit()
    db.refresh(loan)

    # Reload with relations (for clean serialization)
    full = (
        db.query(LoanApplication)
        .options(
            joinedload(LoanApplication.applicant),
            joinedload(LoanApplication.evaluation),
        )
        .filter(LoanApplication.id == loan.id)
        .first()
    )

    # Save JSON bundle (do not let filesystem errors crash the request)
    corr_id = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
    try:
        save_bundle(full, correlation_id=corr_id, idempotency_key=idempotency_key)
    except Exception:
        pass

    # Store idempotent response (JSON-safe dump)
    if idempotency_key:
        IdempotencyStore.set(
            idempotency_key,
            key_payload,
            LoanOut.model_validate(full, from_attributes=True).model_dump(mode="json"),
        )

    return LoanOut.model_validate(full, from_attributes=True)
