"""Nghiệp vụ ứng tuyển: kiểm tra trùng cả trước khi lưu và tại ràng buộc DB."""
from datetime import date

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from backend.app.models import Application, CV, JobPost
from backend.app.schemas.application import ApplicationCreate, ApplicationDetail, ApplicationResponse


def application_to_detail(application: Application) -> ApplicationDetail:
    return ApplicationDetail(
        **ApplicationResponse.model_validate(application).model_dump(),
        job_title=application.job.title,
        company_name=application.job.company.company_name,
        cv_title=application.cv.title if application.cv else None,
    )


def check_duplicate(db: Session, candidate_id: int, job_id: int) -> Application | None:
    return db.query(Application).filter_by(candidate_id=candidate_id, job_id=job_id).first()


def create_application(db: Session, candidate_id: int, data: ApplicationCreate) -> Application:
    job = db.get(JobPost, data.job_id)
    if not job or job.status != 'ACTIVE' or job.approval_status != 'APPROVED' or job.deadline < date.today():
        raise HTTPException(status_code=404, detail='Công việc không tồn tại hoặc đã hết hạn nhận hồ sơ')
    cv = db.get(CV, data.cv_id)
    if not cv or cv.candidate_id != candidate_id:
        raise HTTPException(status_code=404, detail='CV không tồn tại hoặc không thuộc tài khoản này')
    if check_duplicate(db, candidate_id, data.job_id):
        raise HTTPException(status_code=409, detail='Bạn đã ứng tuyển công việc này. Không thể nộp trùng.')
    application = Application(candidate_id=candidate_id, job_id=data.job_id,
                              cv_id=data.cv_id, cover_letter=data.cover_letter or None,
                              status='PENDING')
    db.add(application)
    try:
        db.commit()
        db.refresh(application)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='Bạn đã ứng tuyển công việc này. Không thể nộp trùng.')
    return application


def list_applications(db: Session, candidate_id: int, skip: int, limit: int):
    query = db.query(Application).filter(Application.candidate_id == candidate_id)
    total = query.count()
    rows = (query.options(joinedload(Application.job).joinedload(JobPost.company), joinedload(Application.cv))
            .order_by(Application.applied_at.desc(), Application.application_id.desc())
            .offset(skip).limit(limit).all())
    return {'items': [application_to_detail(row) for row in rows], 'total': total,
            'skip': skip, 'limit': limit}
