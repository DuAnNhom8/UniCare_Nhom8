from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import UserModel
from app.schemas.job import JobApprovalUpdate, JobResponse
from app.schemas.user import UserAdminResponse, UserStatusUpdate
from app.services import admin_service, job_service


router = APIRouter(prefix="/admin", tags=["Quản trị hệ thống"])


@router.get("/stats")
def get_stats(
    _admin: UserModel = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    return admin_service.system_stats(db)


@router.get("/users", response_model=list[UserAdminResponse])
def list_users(
    _admin: UserModel = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    return admin_service.list_users(db)


@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    data: UserStatusUpdate,
    current_admin: UserModel = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    user = admin_service.set_user_status(db, user_id, data.is_active, current_admin.id)
    return {
        "user_id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "message": "Đã cập nhật trạng thái tài khoản",
    }


@router.get("/jobs", response_model=list[JobResponse])
def list_admin_jobs(
    approval_status: str | None = Query(default=None),
    _admin: UserModel = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    return [job_service.job_payload(job) for job in admin_service.list_admin_jobs(db, approval_status)]


@router.put("/jobs/{job_id}/approval", response_model=JobResponse)
def review_job(
    job_id: int,
    data: JobApprovalUpdate,
    _admin: UserModel = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    return job_service.job_payload(admin_service.review_job(db, job_id, data.approval_status))