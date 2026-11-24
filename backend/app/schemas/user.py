from typing import Optional
from datetime import datetime
from urllib.parse import urlparse

import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.cv import CVContent, CVPersonalInfo


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    github_url: Optional[str] = Field(default=None, max_length=500)
    linkedin_url: Optional[str] = Field(default=None, max_length=500)
    job_search_status: Optional[str] = Field(default=None, max_length=32)

    @field_validator("full_name", "phone", "avatar_url", "github_url", "linkedin_url")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("avatar_url", "github_url", "linkedin_url")
    @classmethod
    def validate_http_url(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Đường dẫn phải bắt đầu bằng http:// hoặc https://")
        return value

    @field_validator("job_search_status")
    @classmethod
    def validate_job_search_status(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in {"OPEN", "INTERNSHIP", "NOT_LOOKING"}:
            raise ValueError("Trạng thái tìm việc không hợp lệ")
        return normalized

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not re.fullmatch(r"\+?[0-9][0-9\s().-]{7,19}", value):
            raise ValueError("Số điện thoại không hợp lệ")
        return value


class ProfileResponse(BaseModel):
    id: Optional[int] = None
    user_id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    job_search_status: str = "OPEN"

    model_config = {"from_attributes": True}


class CVUpdate(BaseModel):
    description: Optional[str] = Field(default=None, max_length=5000)
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    personal_info: Optional[CVPersonalInfo] = None
    content: Optional[CVContent] = None


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class CVAIConsentUpdate(BaseModel):
    allow_ai_analysis: bool


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserAdminResponse(BaseModel):
    user_id: int
    email: str
    role: str
    is_active: bool
    created_at: datetime
    full_name: Optional[str] = None
    company_name: Optional[str] = None