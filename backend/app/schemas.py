from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

class RegisterIn(BaseModel):
    email: EmailStr = Field(max_length=100)
    password: str = Field(min_length=8, max_length=128)
    role: Literal['CANDIDATE', 'EMPLOYER']
    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    company_name: str | None = Field(default=None, min_length=1, max_length=150)

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

class TokenOut(BaseModel):
    access_token: str
    token_type: str = 'bearer'

class CandidateUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    university: str | None = Field(default=None, max_length=150)
    major: str | None = Field(default=None, max_length=100)
    skills: list[str] | None = Field(default=None, max_length=60)
    bio: str | None = Field(default=None, max_length=5000)

class CandidateOut(BaseModel):
    candidate_id: int
    full_name: str
    phone: str | None
    university: str | None
    major: str | None
    skills: list[str] | None
    bio: str | None
    has_cv: bool

class CompanyUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=8000)
    website: HttpUrl | None = None

class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    company_id: int
    employer_id: int
    company_name: str
    description: str | None
    website: str | None

class JobWrite(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=10, max_length=20000)
    requirements: str = Field(min_length=5, max_length=15000)
    location: str | None = Field(default=None, max_length=100)
    salary_range: str | None = Field(default=None, max_length=100)
    deadline: date

class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, min_length=10, max_length=20000)
    requirements: str | None = Field(default=None, min_length=5, max_length=15000)
    location: str | None = Field(default=None, max_length=100)
    salary_range: str | None = Field(default=None, max_length=100)
    deadline: date | None = None
    status: Literal['ACTIVE', 'CLOSED', 'HIDDEN'] | None = None

class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    job_id: int
    company_id: int
    title: str
    description: str
    requirements: str
    location: str | None
    salary_range: str | None
    deadline: date
    status: str
    created_at: datetime

class ApplyIn(BaseModel):
    job_id: int = Field(gt=0)

class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    application_id: int
    job_id: int
    candidate_id: int
    status: str
    applied_at: datetime

class StoredAIResult(BaseModel):
    score: int = Field(ge=0, le=100)
    matched_skills: list[str]
    missing_skills: list[str]
    suggestions: list[str]
    method: str
    analyzed_at: str | None = None

class CandidateApplicationOut(ApplicationOut):
    job_title: str
    ai_result: StoredAIResult | None = None

class EmployerApplicationOut(ApplicationOut):
    candidate_name: str
    has_cv: bool

class EmployerApplicationDetailOut(EmployerApplicationOut):
    candidate_email: EmailStr
    phone: str | None = None
    university: str | None = None
    major: str | None = None
    skills: list[str]
    bio: str | None = None
    job_title: str

class UpdateApplicationStatus(BaseModel):
    status: Literal['RECEIVED', 'REVIEWING', 'MATCHED', 'REJECTED']

class UserStatusIn(BaseModel):
    is_active: bool

class ModerateJobIn(BaseModel):
    status: Literal['ACTIVE', 'HIDDEN']

class AIAnalyzeIn(BaseModel):
    job_id: int = Field(gt=0)
    cv_text: str | None = Field(default=None, max_length=16000)
    save_to_application: bool = False
    consent_to_external_processing: bool = False

class AIResult(BaseModel):
    score: int = Field(ge=0, le=100)
    matched_skills: list[str]
    missing_skills: list[str]
    suggestions: list[str]

class AIAnalyzeOut(AIResult):
    method: Literal['openai', 'keyword_demo']
    saved_to_application: bool
    disclaimer: str = 'Đánh giá tham khảo để cải thiện CV, không dùng tự động tuyển chọn hoặc loại ứng viên.'
