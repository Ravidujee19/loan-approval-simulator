from datetime import date
from pydantic import BaseModel, Field


class DBModel(BaseModel):
    class Config:
        from_attributes = True


class Pagination(BaseModel):
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)
