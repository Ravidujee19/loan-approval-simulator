# JWT, password policy, headers, CORS

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt

from agents.applicant_evaluator.app.core.config import settings

ALGORITHM = "HS256"


def create_access_token(subject: str, role: str, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings().ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(to_encode, settings().SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings().SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        raise ValueError("invalid_token") from e
