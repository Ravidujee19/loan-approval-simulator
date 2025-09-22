# agents/applicant_evaluator/app/schemas/applicant.py
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
    id: UUID  # <-- was str; make it UUID
    user_id: UUID 
    # If you also return this, match its type too:
    # user_id: Optional[UUID] = None
    # created_at: Optional[datetime] = None
    # updated_at: Optional[datetime] = None


# from datetime import date
# from pydantic import BaseModel, EmailStr, Field, field_validator
# from pydantic import ConfigDict


# class ApplicantCreate(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
    
#     first_name: str
#     last_name: str
#     email: EmailStr
#     phone: str
#     dob: date
#     employment_status: str
#     employer_name: str | None = None
#     monthly_income: float = Field(ge=0)
#     other_income: float = 0
#     existing_monthly_debt: float = 0


# class ApplicantUpdate(ApplicantCreate):
#     pass


# class ApplicantOut(BaseModel):
#     applicant_id: str
#     first_name: str
#     last_name: str
#     email: EmailStr
#     phone: str
#     dob: date
#     employment_status: str
#     employer_name: str | None
#     monthly_income: float
#     other_income: float
#     existing_monthly_debt: float
