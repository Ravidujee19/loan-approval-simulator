# agents/applicant_evaluator/app/api/deps.py
# auth deps, db session, rate limit, idempotency


from typing import Annotated, TypeAlias

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from agents.applicant_evaluator.app.core.security import decode_token
from agents.applicant_evaluator.app.db.session import get_db
from agents.applicant_evaluator.app.db.models import UserRole

security = HTTPBearer()


def get_current_user(creds: Annotated[HTTPAuthorizationCredentials, Security(security)]) -> dict:
    try:
        payload = decode_token(creds.credentials)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


def require_role(role: UserRole):
    def _role_dep(user: dict = Depends(get_current_user)):
        if user.get("role") != role.value:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return _role_dep


# DB = Annotated[Session, Depends(get_db)]
DB: TypeAlias = Annotated[Session, Depends(get_db)]