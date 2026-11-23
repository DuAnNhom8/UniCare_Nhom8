"""
Export all Pydantic Schemas for UniCareer System
"""

from backend.app.schemas.auth import UserRegister, UserLogin, UserResponse, LoginResponse
from backend.app.schemas.user import CandidateProfileUpdate, CandidateProfileResponse, UserStatusUpdate, UserAdminResponse
from backend.app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyDetailResponse
from backend.app.schemas.job import JobCreate, JobUpdate, JobStatusUpdate, JobResponse
from backend.app.schemas.application import ApplicationCreate, ApplicationStatusUpdate, ApplicationResponse, ApplicationDetailResponse

__all__ = [
    "UserRegister", "UserLogin", "UserResponse", "LoginResponse",
    "CandidateProfileUpdate", "CandidateProfileResponse", "UserStatusUpdate", "UserAdminResponse",
    "CompanyCreate", "CompanyUpdate", "CompanyResponse", "CompanyDetailResponse",
    "JobCreate", "JobUpdate", "JobStatusUpdate", "JobResponse",
    "ApplicationCreate", "ApplicationStatusUpdate", "ApplicationResponse", "ApplicationDetailResponse"
]
