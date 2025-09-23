# agents/applicant_evaluator/app/api/routes/applicants.py
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from uuid import UUID
import logging

from agents.applicant_evaluator.app.api.deps import DB, get_current_user, require_role
from agents.applicant_evaluator.app.db.models import Applicant, UserRole
from agents.applicant_evaluator.app.schemas.applicant import (
    ApplicantCreate,
    ApplicantOut,
    ApplicantUpdate,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/applicants", tags=["applicants"])


@router.post("", response_model=ApplicantOut, status_code=status.HTTP_201_CREATED)
def create_applicant(payload: ApplicantCreate, db: DB, user=Depends(get_current_user)):
    """Create an applicant tied to the authenticated user."""
    data = payload.model_dump(exclude_none=True)

    # Derive incomes if only one provided
    if "monthly_income" in data and "annual_income" not in data:
        try:
            data["annual_income"] = round(float(data["monthly_income"]) * 12, 2)
        except Exception:
            raise HTTPException(status_code=400, detail="monthly_income must be numeric")
    if "annual_income" in data and "monthly_income" not in data:
        try:
            data["monthly_income"] = round(float(data["annual_income"]) / 12.0, 2)
        except Exception:
            raise HTTPException(status_code=400, detail="annual_income must be numeric")

    # Keep only real DB columns to avoid unexpected kwargs
    model_cols = {c.name for c in Applicant.__table__.columns}
    filtered = {k: v for k, v in data.items() if k in model_cols}

    # Coerce user_id if your column is UUID
    uid = user["sub"]
    try:
        uid = UUID(str(uid))
    except Exception:
        pass
    filtered["user_id"] = uid

    try:
        applicant = Applicant(**filtered)
        db.add(applicant)
        db.commit()
        db.refresh(applicant)
        # 🔒 Force ORM-mode validation even if schema config wasn't picked up
        return ApplicantOut.model_validate(applicant, from_attributes=True)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Applicant already exists or violates a constraint",
        )
    except TypeError as e:
        db.rollback()
        log.exception("Applicant create TypeError: %s", e)
        raise HTTPException(status_code=400, detail=f"Invalid field(s) for Applicant: {str(e)}")
    except Exception as e:
        db.rollback()
        log.exception("Applicant create failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error while creating applicant: {e.__class__.__name__}: {e}",
        )


@router.get("", response_model=list[ApplicantOut])
def list_applicants(
    limit: int = 50,
    offset: int = 0,
    db: DB = None,
    user=Depends(get_current_user),
):
    if user["role"] == UserRole.admin.value:
        stmt = select(Applicant).offset(offset).limit(limit)
    else:
        stmt = (
            select(Applicant)
            .where(Applicant.user_id == user["sub"])
            .offset(offset)
            .limit(limit)
        )
    rows = db.execute(stmt).scalars().all()
    return [ApplicantOut.model_validate(a, from_attributes=True) for a in rows]


@router.get("/{applicant_id}", response_model=ApplicantOut)
def get_applicant(applicant_id: str, db: DB, user=Depends(get_current_user)):
    app_obj = db.get(Applicant, applicant_id)
    if not app_obj:
        raise HTTPException(status_code=404, detail="Applicant not found")
    if user["role"] != UserRole.admin.value and str(app_obj.user_id) != str(user["sub"]):
        raise HTTPException(status_code=403, detail="Forbidden")
    return ApplicantOut.model_validate(app_obj, from_attributes=True)


@router.put("/{applicant_id}", response_model=ApplicantOut)
def update_applicant(
    applicant_id: str,
    payload: ApplicantUpdate,
    db: DB,
    user=Depends(get_current_user),
):
    app_obj = db.get(Applicant, applicant_id)
    if not app_obj:
        raise HTTPException(status_code=404, detail="Applicant not found")
    if user["role"] != UserRole.admin.value and str(app_obj.user_id) != str(user["sub"]):
        raise HTTPException(status_code=403, detail="Forbidden")

    data = payload.model_dump(exclude_unset=True, exclude_none=True)

    # Keep only model columns
    model_cols = {c.name for c in Applicant.__table__.columns}
    data = {k: v for k, v in data.items() if k in model_cols}

    # Derive incomes if needed
    if "monthly_income" in data and "annual_income" not in data:
        data["annual_income"] = round(float(data["monthly_income"]) * 12, 2)
    if "annual_income" in data and "monthly_income" not in data:
        data["monthly_income"] = round(float(data["annual_income"]) / 12.0, 2)

    for k, v in data.items():
        setattr(app_obj, k, v)

    try:
        db.add(app_obj)
        db.commit()
        db.refresh(app_obj)
        return ApplicantOut.model_validate(app_obj, from_attributes=True)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Update violates a unique/foreign key constraint",
        )
    except Exception as e:
        db.rollback()
        log.exception("Applicant update failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal error while updating applicant")


@router.delete("/{applicant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_applicant(applicant_id: str, db: DB, _=Depends(require_role(UserRole.admin))):  # type: ignore
    app_obj = db.get(Applicant, applicant_id)
    if not app_obj:
        raise HTTPException(status_code=404, detail="Applicant not found")
    db.delete(app_obj)
    db.commit()
    return None