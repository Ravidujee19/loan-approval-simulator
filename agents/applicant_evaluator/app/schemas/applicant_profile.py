from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional

# CSV columns:
# loan_id,no_of_dependents,education,self_employed,income_annum,loan_amount,loan_term,
# cibil_score,residential_assets_value,commercial_assets_value,luxury_assets_value,
# bank_asset_value,

Education = Literal["Graduate","Not Graduate"]

class Features(BaseModel):
    no_of_dependents: int = Field(ge=0)
    education: Education                   
    self_employed: bool                    
    income_annum: float = Field(ge=0)
    loan_amount: float = Field(ge=0)
    loan_term: int = Field(ge=1)           
    cibil_score: int = Field(ge=300, le=900)
    residential_assets_value: float = 0
    commercial_assets_value: float = 0
    luxury_assets_value: float = 0
    bank_asset_value: float = 0

class Provenance(BaseModel):
    field: str
    source_doc: str
    page: int | None = None
    method: str | None = None
    snippet: str | None = None

class Consistency(BaseModel):
    warnings: List[str] = []
    hard_stops: List[str] = []

class Quality(BaseModel):
    overall_confidence: float = Field(ge=0, le=1)
    field_confidence: Dict[str, float]

class ApplicantProfile(BaseModel):
    applicant_id: str
    loan_id: str
    features: Features
    quality: Quality
    consistency: Consistency
    provenance: List[Provenance] = []
    # optional extras for transparency / debugging
    extra_extracted: Dict[str, str | float | int | bool] = {}
    timestamp: str
