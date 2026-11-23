"""
API Router cho phân hệ Quản trị hệ thống (Admin Router)
Theo đặc tả SRS UniCareer mục 11.2 (Admin Module)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.user import UserAdminResponse, UserStatusUpdate
from backend.app.schemas.job import JobResponse
from backend.app.services import admin_service

router = APIRouter(
    prefix="/admin",
    tags=["Quản trị hệ thống (Admin)"]
)


@router.get(
    "/stats",
    summary="Thống kê tổng quan số liệu hệ thống"
)
def get_stats(
    db: Session = Depends(get_db)
):
    """Lấy số lượng người dùng, doanh nghiệp, tin tuyển dụng và hồ sơ ứng tuyển"""
    return admin_service.get_system_stats(db)


@router.get(
    "/users",
    response_model=List[UserAdminResponse],
    summary="Lấy danh sách toàn bộ người dùng trong hệ thống"
)
def list_users(
    db: Session = Depends(get_db)
):
    """Hiển thị tất cả tài khoản người dùng, vai trò và trạng thái hoạt động"""
    return admin_service.get_all_users(db)


@router.put(
    "/users/{user_id}/status",
    summary="Khóa hoặc mở khóa tài khoản người dùng"
)
def toggle_user_status(
    user_id: int,
    data: UserStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Quản trị viên thay đổi trạng thái hoạt động của tài khoản:
    - **is_active: true** -> Mở khóa
    - **is_active: false** -> Khóa tài khoản
    """
    user = admin_service.update_user_status(db, user_id, data.is_active)
    return {
        "user_id": user.user_id,
        "email": user.email,
        "is_active": user.is_active,
        "message": f"Tài khoản đã được {'mở khóa' if user.is_active else 'khóa'} thành công."
    }


@router.get(
    "/jobs",
    response_model=List[JobResponse],
    summary="Danh sách tin tuyển dụng cho Admin kiểm duyệt"
)
def list_admin_jobs(
    approval_status: Optional[str] = Query(None, description="Lọc theo trạng thái duyệt (PENDING, APPROVED, REJECTED)"),
    db: Session = Depends(get_db)
):
    """Hiển thị các tin tuyển dụng cần kiểm duyệt hoặc đã duyệt"""
    return admin_service.get_jobs_for_admin(db, approval_status)


@router.put(
    "/jobs/{job_id}/approval",
    summary="Phê duyệt hoặc từ chối tin tuyển dụng"
)
def review_job_post(
    job_id: int,
    approval_in: dict,
    db: Session = Depends(get_db)
):
    """
    Admin duyệt tin:
    - **approval_status**: APPROVED (Duyệt công khai) hoặc REJECTED (Từ chối)
    """
    status_val = approval_in.get("approval_status")
    if not status_val:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thiếu trường 'approval_status'."
        )
    job = admin_service.set_job_approval(db, job_id, status_val)
    return {
        "job_id": job.job_id,
        "title": job.title,
        "approval_status": job.approval_status,
        "message": f"Tin tuyển dụng đã chuyển sang trạng thái: {job.approval_status}"
    }
