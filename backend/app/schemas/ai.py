from datetime import datetime

from pydantic import BaseModel, Field


class CandidateCVAnalysisRequest(BaseModel):
    cv_id: int = Field(gt=0)
    job_id: int = Field(gt=0)
    consent_to_gemini: bool


class ApplicationCVAnalysisRequest(BaseModel):
    application_id: int = Field(gt=0)


class CVAnalysisResponse(BaseModel):
    analysis_id: int
    cv_id: int
    job_id: int
    score: int = Field(ge=0, le=100)
    summary: str
    matched_skills: list[str]
    missing_skills: list[str]
    recommendations: list[str]
    model: str
    created_at: datetime
