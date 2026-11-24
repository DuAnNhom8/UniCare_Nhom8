import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.core.config import CV_STORAGE_DIR
from app.core.database import get_db
from app.core.security import require_roles
from app.models.ai import CVAnalysisModel
from app.models.application import ApplicationModel
from app.models.cv import CVModel
from app.models.job import JobModel
from app.models.user import UserModel
from app.schemas.ai import (
    ApplicationCVAnalysisRequest,
    CandidateCVAnalysisRequest,
    CVAnalysisResponse,
)
from app.services import ai_matching, company_service, job_service


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["Phân tích CV"])


def _stored_cv_path(cv: CVModel) -> Path:
    stored_name = Path(cv.file_url or "").name
    if not stored_name or stored_name != cv.file_url:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp CV")
    path = CV_STORAGE_DIR / stored_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp CV")
    return path


def _analyze_and_save(
    db: Session,
    *,
    cv: CVModel,
    job: JobModel,
    requested_by: UserModel,
) -> dict:
    if cv.cv_type == "builder":
        sections = cv.content or {}
        labels = {
            "objective": "Mục tiêu nghề nghiệp",
            "education": "Học vấn",
            "experience": "Kinh nghiệm làm việc",
            "projects": "Dự án",
            "skills": "Kỹ năng",
            "certifications": "Chứng chỉ",
        }
        cv_text = "\n\n".join(
            f"{label}:\n{sections[key]}"
            for key, label in labels.items()
            if sections.get(key)
        )
        result = ai_matching.analyze_cv_text(
            cv_text,
            job.title,
            job.description,
            job.requirements,
        )
    elif cv.cv_type == "upload":
        result = ai_matching.analyze_cv_file(
            _stored_cv_path(cv),
            cv.file_name,
            job.title,
            job.description,
            job.requirements,
        )
    else:
        raise HTTPException(
            status_code=422,
            detail="Loại CV này không hỗ trợ phân tích AI",
        )
    analysis = CVAnalysisModel(
        cv_id=cv.id,
        job_id=job.id,
        candidate_id=cv.user_id,
        requested_by_id=requested_by.id,
        score=result["score"],
        summary=result["summary"],
        matched_skills=json.dumps(result["matched_skills"], ensure_ascii=False),
        missing_skills=json.dumps(result["missing_skills"], ensure_ascii=False),
        recommendations=json.dumps(result["recommendations"], ensure_ascii=False),
        model=ai_matching.GEMINI_MODEL,
    )
    db.add(analysis)
    try:
        db.commit()
        db.refresh(analysis)
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Could not save CV analysis")
        raise HTTPException(
            status_code=500,
            detail="Không thể lưu kết quả phân tích CV",
        ) from error
    return {
        "analysis_id": analysis.id,
        "cv_id": cv.id,
        "job_id": job.id,
        "score": analysis.score,
        "summary": analysis.summary,
        "matched_skills": json.loads(analysis.matched_skills),
        "missing_skills": json.loads(analysis.missing_skills),
        "recommendations": json.loads(analysis.recommendations),
        "model": analysis.model,
        "created_at": analysis.created_at,
    }


@router.post("/analyze/candidate", response_model=CVAnalysisResponse)
def analyze_candidate_cv(
    request: CandidateCVAnalysisRequest,
    current_user: UserModel = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    if not request.consent_to_gemini:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cần đồng ý gửi CV đến Gemini trước khi phân tích",
        )
    cv = (
        db.query(CVModel)
        .filter(CVModel.id == request.cv_id, CVModel.user_id == current_user.id)
        .first()
    )
    if cv is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy CV")
    job = job_service.get_public_job(db, request.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Tin tuyển dụng không còn được công khai")
    return _analyze_and_save(db, cv=cv, job=job, requested_by=current_user)


@router.post("/analyze/application", response_model=CVAnalysisResponse)
def analyze_application_cv(
    request: ApplicationCVAnalysisRequest,
    current_user: UserModel = Depends(require_roles("employer")),
    db: Session = Depends(get_db),
):
    company = company_service.get_company_for_employer(db, current_user.id)
    if company is None:
        raise HTTPException(status_code=409, detail="Chưa có hồ sơ doanh nghiệp")
    application = (
        db.query(ApplicationModel)
        .join(JobModel, ApplicationModel.job_id == JobModel.id)
        .options(
            joinedload(ApplicationModel.cv).joinedload(CVModel.ai_consent),
            joinedload(ApplicationModel.job).joinedload(JobModel.company),
        )
        .filter(
            ApplicationModel.id == request.application_id,
            JobModel.company_id == company.id,
        )
        .first()
    )
    if application is None or application.cv is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ ứng tuyển hoặc CV")
    if not application.cv.ai_consent or not application.cv.ai_consent.consented:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ứng viên chưa cho phép phân tích CV qua Gemini",
        )
    return _analyze_and_save(
        db,
        cv=application.cv,
        job=application.job,
        requested_by=current_user,
    )