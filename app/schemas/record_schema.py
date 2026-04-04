from __future__ import annotations

from datetime import date as dt_date
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.financial_record import RecordType


class RecordCreateRequest(BaseModel):
    amount: float = Field(gt=0)
    type: RecordType
    category: str = Field(min_length=2, max_length=80)
    date: dt_date
    notes: str | None = Field(default=None, max_length=1000)


class RecordUpdateRequest(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    type: RecordType | None = None
    category: str | None = Field(default=None, min_length=2, max_length=80)
    date: dt_date | None = None
    notes: str | None = Field(default=None, max_length=1000)


class RecordResponse(BaseModel):
    id: int
    amount: float
    type: RecordType
    category: str
    date: dt_date
    notes: str | None
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RecordListQuery(BaseModel):
    type: RecordType | None = None
    category: str | None = None
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    notes: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
