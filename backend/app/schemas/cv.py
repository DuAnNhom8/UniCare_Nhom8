from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, EmailStr, Field, field_validator


class CVPersonalInfo(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    github_url: Optional[str] = Field(default=None, max_length=500)
    linkedin_url: Optional[str] = Field(default=None, max_length=500)

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Họ và tên trong CV không được để trống")
        return normalized

    @field_validator("github_url", "linkedin_url")
    @classmethod
    def validate_social_url(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Đường dẫn mạng xã hội phải bắt đầu bằng http:// hoặc https://")
        return value


class CVContent(BaseModel):
    objective: str = Field(default="", max_length=5000)
    education: str = Field(default="", max_length=10000)
    experience: str = Field(default="", max_length=15000)
    projects: str = Field(default="", max_length=15000)
    skills: str = Field(default="", max_length=5000)
    certifications: str = Field(default="", max_length=10000)


class CVBuilderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    personal_info: CVPersonalInfo
    content: CVContent

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Tên CV không được để trống")
        return normalized


class CVBuilderUpdate(CVBuilderCreate):
    pass


class CVResponse(BaseModel):
    cv_id: int
    id: int
    user_id: int
    title: str
    file_name: str
    file_url: Optional[str] = None
    description: Optional[str] = None
    cv_type: str = "upload"
    personal_info: Optional[CVPersonalInfo] = None
    content: Optional[CVContent] = None
    allow_ai_analysis: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
