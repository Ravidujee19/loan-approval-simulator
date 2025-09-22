# agents/applicant_evaluator/app/schemas/loan.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from agents.applicant_evaluator.app.schemas.evaluation import EvaluationOut

class LoanCreate(BaseModel):
    # Accept string UUIDs from the client; Pydantic will coerce to UUID
    applicant_id: UUID
    amount_requested: float = Field(gt=0)
    term_months: int = Field(ge=6, le=120)
    loan_type: str
    purpose: str

class LoanOut(BaseModel):
    # Read from ORM attributes and keep JSON key names stable
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    # ORM attr is `id`; expose as `loan_id`
    loan_id: UUID = Field(validation_alias="id", serialization_alias="loan_id")

    # ORM attr is UUID; serialize as string in JSON
    applicant_id: UUID

    amount_requested: float
    term_months: int
    loan_type: str
    purpose: str
    application_date: datetime | None = None
    status: str

    evaluation: EvaluationOut | None = None


# from datetime import datetime
# from uuid import UUID
# from pydantic import BaseModel, Field, ConfigDict

# from agents.applicant_evaluator.app.schemas.evaluation import EvaluationOut


# class LoanCreate(BaseModel):
#     # Accept UUID from client (string UUID is fine; Pydantic will coerce)
#     applicant_id: UUID
#     amount_requested: float = Field(gt=0)
#     term_months: int = Field(ge=6, le=120)
#     loan_type: str
#     purpose: str


# class LoanOut(BaseModel):
#     # Read from ORM attributes and keep aliasing stable
#     model_config = ConfigDict(from_attributes=True, populate_by_name=True)

#     # ORM attr is `id`; we expose as `loan_id`
#     loan_id: UUID = Field(validation_alias="id", serialization_alias="loan_id")

#     # ORM attr is UUID already; accept UUID and serialize as string
#     applicant_id: UUID

#     amount_requested: float
#     term_months: int
#     loan_type: str
#     purpose: str
#     application_date: datetime | None = None
#     status: str

#     # nested object; we'll align its schema next
#     evaluation: EvaluationOut | None = None
