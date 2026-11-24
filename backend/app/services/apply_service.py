from __future__ import annotations
from datetime import date

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.application import ApplicationModel
from app.models.cv import CVModel
from app.models.job import JobModel
from app.models.user import UserModel
from app.schemas.application import ApplicationCreate


def application_payload(application: ApplicationModel) -> dict:
    profile = application.candidate.profile
    cv = application.cv
    is_builder_cv = bool(cv and cv.cv_type == "builder")
    cv_personal = cv.personal_info or {} if is_builder_cv else {}
    cv_content = cv.content or {} if is_builder_cv else {}
    return {
        "application_id": application.id,
        "candidate_id": application.candidate_id,
        "job_id": application.job_id,
        "cv_id": application.cv_id,
        "cover_letter": application.cover_letter,
        "status": application.status,
        "applied_at": application.applied_at,
        "job_title": application.job.title,
        "company_name": application.job.company.company_name,
        "candidate_name": cv_personal.get("full_name") or (
            profile.full_name if profile else None
        ),
        "candidate_email": cv_personal.get("email") or application.candidate.email,
        "candidate_university": (
            cv_content.get("education") or None
            if is_builder_cv
            else profile.university if profile else None
        ),
        "candidate_major": None if is_builder_cv else profile.major if profile else None,
        "candidate_skills": (
            cv_content.get("skills") or None
            if is_builder_cv
            else profile.skills if profile else None
        ),
        "cv_title": cv.file_name if cv else None,
        "cv_type": cv.cv_type if cv else None,
        "cv_ai_allowed": bool(
            cv
            and cv.ai_consent
            and cv.ai_consent.consented
        ),
    }


def find_application(db: Session, candidate_id: int, job_id: int) -> ApplicationModel | None:
    return (
        db.query(ApplicationModel)
        .filter(ApplicationModel.candidate_id == candidate_id, ApplicationModel.job_id == job_id)
        .first()
    )


def create_application(db: Session, candidate_id: int, data: ApplicationCreate) -> ApplicationModel:
    job = db.query(JobModel).filter(
        JobModel.id == data.job_id,
        JobModel.status == "ACTIVE",
        JobModel.approval_status == "APPROVED",
        JobModel.deadline >= date.today(),
    ).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Công việc không tồn tại hoặc đã hết hạn nhận hồ sơ")
    cv = db.query(CVModel).filter(CVModel.id == data.cv_id, CVModel.user_id == candidate_id).first()
    if cv is None:
        raise HTTPException(status_code=404, detail="CV không tồn tại hoặc không thuộc tài khoản này")
    if find_application(db, candidate_id, data.job_id):
        raise HTTPException(status_code=409, detail="Bạn đã ứng tuyển công việc này. Không thể nộp trùng.")

    application = ApplicationModel(
        candidate_id=candidate_id,
        job_id=data.job_id,
        cv_id=data.cv_id,
        cover_letter=data.cover_letter.strip() if data.cover_letter else None,
        status="PENDING",
    )
    db.add(application)
    try:
        db.commit()
        db.refresh(application)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Bạn đã ứng tuyển công việc này. Không thể nộp trùng.")
    return application


def _application_query(db: Session):
    return (
        db.query(ApplicationModel)
        .options(
            joinedload(ApplicationModel.candidate).joinedload(UserModel.profile),
            joinedload(ApplicationModel.job).joinedload(JobModel.company),
            joinedload(ApplicationModel.cv).joinedload(CVModel.ai_consent),
        )
    )


def list_candidate_applications(db: Session, candidate_id: int, skip: int, limit: int) -> dict:
    query = db.query(ApplicationModel).filter(ApplicationModel.candidate_id == candidate_id)
    total = query.count()
    rows = (
        _application_query(db)
        .filter(ApplicationModel.candidate_id == candidate_id)
        .order_by(ApplicationModel.applied_at.desc(), ApplicationModel.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {"items": [application_payload(row) for row in rows], "total": total, "skip": skip, "limit": limit}


def list_company_applications(db: Session, company_id: int) -> list[dict]:
    rows = (
        db.query(ApplicationModel)
        .join(JobModel, ApplicationModel.job_id == JobModel.id)
        .filter(JobModel.company_id == company_id)
        .options(
            joinedload(ApplicationModel.candidate).joinedload(UserModel.profile),
            joinedload(ApplicationModel.job).joinedload(JobModel.company),
            joinedload(ApplicationModel.cv).joinedload(CVModel.ai_consent),
        )
        .order_by(ApplicationModel.applied_at.desc(), ApplicationModel.id.desc())
        .all()
    )
    return [application_payload(row) for row in rows]


def update_company_application(
    db: Session,
    company_id: int,
    application_id: int,
    new_status: str,
) -> dict:
    normalized = new_status.strip().upper()
    if normalized not in {"REVIEWING", "ACCEPTED", "REJECTED"}:
        raise HTTPException(status_code=422, detail="Trạng thái đơn ứng tuyển không hợp lệ")
    application = (
        db.query(ApplicationModel)
        .join(JobModel, ApplicationModel.job_id == JobModel.id)
        .filter(ApplicationModel.id == application_id, JobModel.company_id == company_id)
        .first()
    )
    if application is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn ứng tuyển")
    if application.status in {"ACCEPTED", "REJECTED"} and application.status != normalized:
        raise HTTPException(status_code=409, detail="Đơn đã có kết quả cuối cùng")
    application.status = normalized
    db.commit()
    updated = (
        db.query(ApplicationModel)
        .options(
            joinedload(ApplicationModel.candidate).joinedload(UserModel.profile),
            joinedload(ApplicationModel.job).joinedload(JobModel.company),
            joinedload(ApplicationModel.cv).joinedload(CVModel.ai_consent),
        )
        .filter(ApplicationModel.id == application_id)
        .one()
    )
    return application_payload(updated)