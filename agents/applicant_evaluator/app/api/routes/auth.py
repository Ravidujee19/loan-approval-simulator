# POST /auth/register, /auth/login

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from agents.applicant_evaluator.app.api.deps import DB
from agents.applicant_evaluator.app.core.security import create_access_token
from agents.applicant_evaluator.app.db.models import User, UserRole
from agents.applicant_evaluator.app.schemas.user import UserCreate, UserLogin, UserOut
from agents.applicant_evaluator.app.utils.crypto import verify_password, get_password_hash
from agents.applicant_evaluator.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
    
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DB):
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(email=payload.email, password_hash=get_password_hash(payload.password), role=payload.role)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    db.refresh(user)
    return UserOut.model_validate(user, from_attributes=True)

@router.post("/login")
def login(payload: UserLogin, db: DB):
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(str(user.id), user.role.value)
    return {"access_token": token, "token_type": "bearer", "role": user.role.value}
