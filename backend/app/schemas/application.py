from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ApplicationCreate(BaseModel):
    job_id: int = Field(gt=0)
    cv_id: int = Field(gt=0)
    cover_letter: Optional[str] = Field(default=None, max_length=5000)


class ApplicationStatusUpdate(BaseModel):
    status: str


class ApplicationDetail(BaseModel):
    application_id: int
    candidate_id: int
    job_id: int
    cv_id: Optional[int] = None
    cover_letter: Optional[str] = None
    status: str
    applied_at: datetime
    job_title: str
    company_name: str
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_university: Optional[str] = None
    candidate_major: Optional[str] = None
    candidate_skills: Optional[str] = None
    cv_title: Optional[str] = None
    cv_type: Optional[str] = None
    cv_ai_allowed: bool = False


class ApplicationCheck(BaseModel):
    applied: bool
    application_id: Optional[int] = None


class ApplicationList(BaseModel):
    items: list[ApplicationDetail]
    total: int
    skip: int
    limit: int
