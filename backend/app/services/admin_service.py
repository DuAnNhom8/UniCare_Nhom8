from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.application import ApplicationModel
from app.models.company import CompanyModel
from app.models.job import JobModel
from app.models.user import UserModel
from app.services.job_service import set_approval_status


def system_stats(db: Session) -> dict:
    return {
        "total_users": db.query(UserModel).count(),
        "candidate_count": db.query(UserModel).filter(UserModel.role == "candidate").count(),
        "employer_count": db.query(UserModel).filter(UserModel.role == "employer").count(),
        "company_count": db.query(CompanyModel).count(),
        "total_jobs": db.query(JobModel).count(),
        "active_jobs": db.query(JobModel).filter(
            JobModel.status == "ACTIVE", JobModel.approval_status == "APPROVED"
        ).count(),
        "pending_jobs": db.query(JobModel).filter(JobModel.approval_status == "PENDING").count(),
        "total_applications": db.query(ApplicationModel).count(),
    }


def list_users(db: Session) -> list[dict]:
    users = (
        db.query(UserModel)
        .options(joinedload(UserModel.profile), joinedload(UserModel.company))
        .order_by(UserModel.id.desc())
        .all()
    )
    return [
        {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.lower(),
            "is_active": user.is_active,
            "created_at": user.created_at,
            "full_name": user.profile.full_name if user.profile else None,
            "company_name": user.company.company_name if user.company else None,
        }
        for user in users
    ]


def set_user_status(
    db: Session,
    user_id: int,
    is_active: bool,
    acting_admin_id: int,
) -> UserModel:
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
    if user.id == acting_admin_id and not is_active:
        raise HTTPException(
            status_code=409,
            detail="Không thể tự khóa tài khoản quản trị viên hiện tại",
        )
    if user.role.lower() == "admin" and not is_active:
        active_admins = db.query(UserModel).filter(
            UserModel.role == "admin", UserModel.is_active.is_(True)
        ).count()
        if active_admins <= 1:
            raise HTTPException(status_code=409, detail="Không thể khóa tài khoản quản trị viên duy nhất")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def list_admin_jobs(db: Session, approval_status: str | None = None) -> list[JobModel]:
    query = db.query(JobModel).options(joinedload(JobModel.company))
    if approval_status:
        normalized = approval_status.strip().upper()
        if normalized not in {"PENDING", "APPROVED", "REJECTED"}:
            raise HTTPException(status_code=422, detail="Trạng thái kiểm duyệt không hợp lệ")
        query = query.filter(JobModel.approval_status == normalized)
    return query.order_by(JobModel.created_at.desc(), JobModel.id.desc()).all()


def review_job(db: Session, job_id: int, approval_status: str) -> JobModel:
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Tin tuyển dụng không tồn tại")
    return set_approval_status(db, job, approval_status)
