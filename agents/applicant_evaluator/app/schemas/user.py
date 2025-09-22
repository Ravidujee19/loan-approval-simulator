from pydantic import BaseModel, EmailStr, Field

from agents.applicant_evaluator.app.db.models import UserRole
from uuid import UUID


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole  # "admin" | "applicant"
    # role: UserRole = UserRole.user


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    role: UserRole
