"""
Dịch vụ xử lý Ứng tuyển (Application Service)
Theo đặc tả SRS UniCareer mục 10.2.5 & 11.2 (Application Module)
"""

from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.application import Application
from backend.app.models.job import JobPost
from backend.app.models.company import Company
from backend.app.models.candidate import Candidate
from backend.app.models.user import User
from backend.app.schemas.application import ApplicationCreate, ApplicationDetailResponse


def apply_job(db: Session, data: ApplicationCreate, user_id: int) -> Application:
    """
    Ứng viên nộp đơn ứng tuyển:
    - Kiểm tra tin tuyển dụng có tồn tại, còn hạn và đang mở nhận hồ sơ
    - Kiểm tra ràng buộc chống nộp đơn trùng lặp
    - Tạo đơn ứng tuyển với trạng thái mặc định 'RECEIVED'
    """
    # 1. Kiểm tra tin tuyển dụng
    job = db.query(JobPost).filter(JobPost.job_id == data.job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tin tuyển dụng #{data.job_id} không tồn tại."
        )

    if job.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tin tuyển dụng '{job.title}' hiện không mở nhận hồ sơ (trạng thái: {job.status})."
        )

    if job.approval_status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tin tuyển dụng này chưa được Quản trị viên duyệt công khai."
        )

    if job.deadline and job.deadline < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tin tuyển dụng đã hết hạn nộp hồ sơ vào ngày {job.deadline.strftime('%d/%m/%Y')}."
        )

    # 2. Kiểm tra nộp trùng
    existing = db.query(Application).filter(
        Application.job_id == data.job_id,
        Application.candidate_id == user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn đã nộp hồ sơ ứng tuyển vào vị trí này rồi. Vui lòng theo dõi kết quả ở mục Đơn ứng tuyển."
        )

    # 3. Tạo đơn ứng tuyển mới
    # Đánh giá điểm phù hợp AI sơ bộ (mock logic hoặc dựa trên kỹ năng nếu có)
    candidate_profile = db.query(Candidate).filter(Candidate.candidate_id == user_id).first()
    ai_score = 85
    ai_note = "Hồ sơ có định hướng phù hợp với vị trí thực tập."
    if candidate_profile and candidate_profile.skills:
        ai_score = 90
        ai_note = f"Kỹ năng '{candidate_profile.skills}' tương thích tốt với yêu cầu công việc."

    application = Application(
        job_id=data.job_id,
        candidate_id=user_id,
        status="RECEIVED",
        ai_match_score=ai_score,
        ai_feedback=ai_note
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def get_candidate_applications(db: Session, candidate_id: int) -> List[ApplicationDetailResponse]:
    """Lấy danh sách các đơn ứng tuyển của một ứng viên cụ thể"""
    applications = db.query(Application).filter(Application.candidate_id == candidate_id).order_by(Application.applied_at.desc()).all()
    results = []
    for app in applications:
        job = db.query(JobPost).filter(JobPost.job_id == app.job_id).first()
        company = db.query(Company).filter(Company.company_id == job.company_id).first() if job else None

        results.append(ApplicationDetailResponse(
            application_id=app.application_id,
            job_id=app.job_id,
            candidate_id=app.candidate_id,
            status=app.status,
            ai_match_score=app.ai_match_score,
            ai_feedback=app.ai_feedback,
            applied_at=app.applied_at,
            updated_at=app.updated_at,
            job_title=job.title if job else "Không xác định",
            company_name=company.company_name if company else "UniCareer Partner",
            company_location=job.location if job else "",
            salary_range=job.salary_range if job else ""
        ))
    return results


def get_company_applications(db: Session, company_id: int) -> List[ApplicationDetailResponse]:
    """Lấy danh sách hồ sơ ứng viên nộp vào các tin tuyển dụng của một doanh nghiệp"""
    # Lấy tất cả job_id của công ty
    company_jobs = db.query(JobPost).filter(JobPost.company_id == company_id).all()
    job_ids = [j.job_id for j in company_jobs]
    if not job_ids:
        return []

    applications = db.query(Application).filter(Application.job_id.in_(job_ids)).order_by(Application.applied_at.desc()).all()
    job_map = {j.job_id: j for j in company_jobs}
    results = []

    for app in applications:
        job = job_map.get(app.job_id)
        user = db.query(User).filter(User.user_id == app.candidate_id).first()
        cand = db.query(Candidate).filter(Candidate.candidate_id == app.candidate_id).first()

        results.append(ApplicationDetailResponse(
            application_id=app.application_id,
            job_id=app.job_id,
            candidate_id=app.candidate_id,
            status=app.status,
            ai_match_score=app.ai_match_score,
            ai_feedback=app.ai_feedback,
            applied_at=app.applied_at,
            updated_at=app.updated_at,
            job_title=job.title if job else "",
            candidate_name=cand.full_name if cand else (user.email if user else "Ứng viên"),
            candidate_email=user.email if user else "",
            candidate_phone=cand.phone if cand else "",
            candidate_university=cand.university if cand else "",
            candidate_major=cand.major if cand else "",
            candidate_cv_url=cand.cv_url if cand else "",
            candidate_skills=cand.skills if cand else ""
        ))
    return results


def update_application_status(db: Session, application_id: int, new_status: str) -> Application:
    """Nhà tuyển dụng cập nhật trạng thái đơn ứng tuyển (RECEIVED, REVIEWING, ACCEPTED, REJECTED)"""
    valid_statuses = ["RECEIVED", "REVIEWING", "ACCEPTED", "REJECTED"]
    clean_status = new_status.strip().upper()
    if clean_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trạng thái không hợp lệ: '{new_status}'. Các giá trị cho phép: {', '.join(valid_statuses)}"
        )

    app = db.query(Application).filter(Application.application_id == application_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Đơn ứng tuyển #{application_id} không tồn tại."
        )

    app.status = clean_status
    db.commit()
    db.refresh(app)
    return app
