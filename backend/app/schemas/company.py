from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class CompanyUpdate(BaseModel):
    company_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, max_length=5000)
    website: Optional[str] = Field(default=None, max_length=255)
    industry: Optional[str] = Field(default=None, max_length=100)
    location: Optional[str] = Field(default=None, max_length=150)

    @field_validator("company_name", "description", "website", "industry", "location", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("website")
    @classmethod
    def validate_website(cls, value):
        if not value:
            return value
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Website phải bắt đầu bằng http:// hoặc https://")
        return value


class CompanyResponse(BaseModel):
    id: int
    company_id: int
    employer_id: int
    company_name: str
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    job_count: int = 0
    application_count: int = 0

    model_config = {"from_attributes": True}
