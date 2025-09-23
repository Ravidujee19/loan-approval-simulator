from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class EvaluationOut(BaseModel):
    # Read from ORM attrs and keep JSON key names stable
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    # ORM attr is `id`; expose as `evaluation_id`
    evaluation_id: UUID = Field(validation_alias="id", serialization_alias="evaluation_id")

    # ORM attr is UUID; serialize as string in JSON
    loan_id: UUID | None = None

    eligibility: str
    score: int
    reasons: list[str]
    created_at: datetime | None = None