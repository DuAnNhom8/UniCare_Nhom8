from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class JobCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=5)
    requirements: str = Field(min_length=5)
    location: Optional[str] = Field(default=None, max_length=150)
    salary_range: Optional[str] = Field(default=None, max_length=100)
    job_type: str = "INTERNSHIP"
    experience_level: Optional[str] = Field(default=None, max_length=100)
    deadline: date

    @field_validator("title", "description", "requirements", mode="before")
    @classmethod
    def strip_required_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("location", "salary_range", "experience_level", mode="before")
    @classmethod
    def strip_optional_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class JobUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=150)
    description: Optional[str] = Field(default=None, min_length=5)
    requirements: Optional[str] = Field(default=None, min_length=5)
    location: Optional[str] = Field(default=None, max_length=150)
    salary_range: Optional[str] = Field(default=None, max_length=100)
    job_type: Optional[str] = None
    experience_level: Optional[str] = Field(default=None, max_length=100)
    deadline: Optional[date] = None

    @field_validator(
        "title", "description", "requirements", "location", "salary_range", "experience_level",
        mode="before",
    )
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class JobStatusUpdate(BaseModel):
    status: str


class JobApprovalUpdate(BaseModel):
    approval_status: str


class JobResponse(BaseModel):
    job_id: int
    company_id: int
    title: str
    description: str
    requirements: str
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: str
    experience_level: Optional[str] = None
    deadline: date
    status: str
    approval_status: str
    created_at: datetime
    updated_at: datetime
    company_name: Optional[str] = None
    application_count: int = 0


class PublicJobResponse(JobResponse):
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    company_industry: Optional[str] = None


class PublicJobList(BaseModel):
    items: list[PublicJobResponse]
    total: int
    skip: int
    limit: int