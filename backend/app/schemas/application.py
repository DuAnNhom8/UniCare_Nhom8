"""Schemas nộp đơn, kiểm tra trùng, CV và lịch sử ứng tuyển."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ApplicationCreate(BaseModel):
    job_id: int = Field(..., gt=0)
    cv_id: int = Field(..., gt=0)
    cover_letter: Optional[str] = Field(None, max_length=5000)


class ApplicationResponse(BaseModel):
    application_id: int
    candidate_id: int
    job_id: int
    cv_id: Optional[int]
    cover_letter: Optional[str]
    status: str
    applied_at: datetime
    model_config = {'from_attributes': True}


class ApplicationDetail(ApplicationResponse):
    job_title: str
    company_name: str
    cv_title: Optional[str]


class ApplicationCheck(BaseModel):
    applied: bool
    application_id: Optional[int] = None


class ApplicationList(BaseModel):
    items: list[ApplicationDetail]
    total: int
    skip: int
    limit: int


class CVResponse(BaseModel):
    cv_id: int
    title: str
    created_at: datetime
    model_config = {'from_attributes': True}
