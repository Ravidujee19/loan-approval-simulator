from datetime import date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class ApplicantBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    dob: date
    employment_status: str
    employer_name: Optional[str] = None
    monthly_income: float = Field(ge=0)
    other_income: float = 0
    existing_monthly_debt: float = 0

class ApplicantCreate(ApplicantBase):
    pass

class ApplicantUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    dob: Optional[date] = None
    employment_status: Optional[str] = None
    employer_name: Optional[str] = None
    monthly_income: Optional[float] = Field(default=None, ge=0)
    other_income: Optional[float] = None
    existing_monthly_debt: Optional[float] = None

class ApplicantOut(ApplicantBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID  
    user_id: UUID 