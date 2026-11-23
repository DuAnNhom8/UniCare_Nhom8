"""
Dịch vụ Quản trị hệ thống (Admin Service)
Theo đặc tả SRS UniCareer mục 11.2 (Admin Module)
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.user import User
from backend.app.models.candidate import Candidate
from backend.app.models.company import Company
from backend.app.models.job import JobPost
from backend.app.models.application import Application
from backend.app.schemas.user import UserAdminResponse


def get_system_stats(db: Session) -> Dict[str, Any]:
    """Thống kê tổng quan số liệu toàn hệ thống cho Dashboard Quản trị"""
    total_users = db.query(User).count()
    candidate_count = db.query(User).filter(User.role == "CANDIDATE").count()
    employer_count = db.query(User).filter(User.role == "EMPLOYER").count()
    company_count = db.query(Company).count()
    total_jobs = db.query(JobPost).count()
    active_jobs = db.query(JobPost).filter(JobPost.status == "ACTIVE", JobPost.approval_status == "APPROVED").count()
    pending_jobs = db.query(JobPost).filter(JobPost.approval_status == "PENDING").count()
    total_applications = db.query(Application).count()

    return {
        "total_users": total_users,
        "candidate_count": candidate_count,
        "employer_count": employer_count,
        "company_count": company_count,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "pending_jobs": pending_jobs,
        "total_applications": total_applications
    }


def get_all_users(db: Session) -> List[UserAdminResponse]:
    """Lấy danh sách tất cả người dùng kèm thông tin bổ sung"""
    users = db.query(User).order_by(User.user_id.desc()).all()
    results = []
    for u in users:
        cand_name = None
        comp_name = None
        if u.role == "CANDIDATE":
            cand = db.query(Candidate).filter(Candidate.candidate_id == u.user_id).first()
            if cand:
                cand_name = cand.full_name
        elif u.role == "EMPLOYER":
            comp = db.query(Company).filter(Company.employer_id == u.user_id).first()
            if comp:
                comp_name = comp.company_name

        results.append(UserAdminResponse(
            user_id=u.user_id,
            email=u.email,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at,
            full_name=cand_name,
            company_name=comp_name
        ))
    return results


def update_user_status(db: Session, user_id: int, is_active: bool) -> User:
    """Quản trị viên khóa hoặc mở khóa tài khoản người dùng"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Người dùng #{user_id} không tồn tại."
        )

    # Không cho phép tự khóa tài khoản Admin mặc định
    if user.role == "ADMIN" and not is_active:
        admin_count = db.query(User).filter(User.role == "ADMIN", User.is_active == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể khóa tài khoản Quản trị viên duy nhất của hệ thống."
            )

    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def get_jobs_for_admin(db: Session, approval_status: str = None) -> List[JobPost]:
    """Lấy danh sách tin tuyển dụng cho Admin kiểm duyệt"""
    query = db.query(JobPost)
    if approval_status:
        query = query.filter(JobPost.approval_status == approval_status.upper())
    return query.order_by(JobPost.created_at.desc()).all()


def set_job_approval(db: Session, job_id: int, approval_status: str) -> JobPost:
    """Quản trị viên phê duyệt hoặc từ chối tin tuyển dụng"""
    clean_status = approval_status.strip().upper()
    if clean_status not in ["APPROVED", "REJECTED", "PENDING"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trạng thái kiểm duyệt '{approval_status}' không hợp lệ. Cho phép: APPROVED, REJECTED, PENDING."
        )

    job = db.query(JobPost).filter(JobPost.job_id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tin tuyển dụng #{job_id} không tồn tại."
        )

    job.approval_status = clean_status
    db.commit()
    db.refresh(job)
    return job
