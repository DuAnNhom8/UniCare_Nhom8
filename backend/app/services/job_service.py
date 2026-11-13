"""
Dịch vụ xử lý nghiệp vụ Tin tuyển dụng (Job Post Service)
Theo đặc tả SRS UniCareer mục 10.2.4 & Task T05FE9A
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.models.job import JobPost
from backend.app.models.company import Company
from backend.app.schemas.job import JobCreate, JobUpdate

VALID_JOB_STATUSES = {"ACTIVE", "CLOSED", "HIDDEN"}
VALID_APPROVAL_STATUSES = {"PENDING", "APPROVED", "REJECTED"}

def get_job_by_id(db: Session, job_id: int) -> Optional[JobPost]:
    """Lấy thông tin chi tiết một tin tuyển dụng theo ID"""
    return db.query(JobPost).filter(JobPost.job_id == job_id).first()

def get_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    company_id: Optional[int] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    job_type: Optional[str] = None
) -> List[JobPost]:
    """
    Lấy danh sách các tin tuyển dụng kèm lọc và tìm kiếm:
    - company_id: Lọc theo doanh nghiệp
    - status: Lọc theo trạng thái (ACTIVE, CLOSED, HIDDEN)
    - keyword: Tìm theo tiêu đề hoặc địa điểm
    - job_type: Lọc theo hình thức (FULL_TIME, PART_TIME, INTERNSHIP)
    """
    query = db.query(JobPost)

    if company_id is not None:
        query = query.filter(JobPost.company_id == company_id)

    if status:
        query = query.filter(JobPost.status == status.upper())

    if job_type:
        query = query.filter(JobPost.job_type == job_type.upper())

    if keyword:
        kw = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                JobPost.title.ilike(kw),
                JobPost.location.ilike(kw),
                JobPost.description.ilike(kw)
            )
        )

    return query.order_by(JobPost.job_id.desc()).offset(skip).limit(limit).all()

def ensure_default_company(db: Session) -> int:
    """Đảm bảo có ít nhất 1 công ty mặc định trong DB để gán cho tin đăng"""
    company = db.query(Company).first()
    if not company:
        company = Company(
            company_id=1,
            employer_id=2,
            company_name="TechNova",
            industry="Công nghệ thông tin / Phần mềm",
            website="https://technova.example",
            location="TP. Hồ Chí Minh",
            description="TechNova phát triển các giải pháp phần mềm và sản phẩm số cho doanh nghiệp."
        )
        db.add(company)
        db.commit()
        db.refresh(company)
    return company.company_id

def create_job(db: Session, job_in: JobCreate) -> JobPost:
    """
    Tạo mới một tin tuyển dụng:
    - Xác thực dữ liệu
    - Trạng thái mặc định: ACTIVE hoặc theo input
    - Trạng thái kiểm duyệt: APPROVED hoặc PENDING
    """
    target_company_id = job_in.company_id or 1
    # Kiểm tra công ty tồn tại
    comp = db.query(Company).filter(Company.company_id == target_company_id).first()
    if not comp:
        target_company_id = ensure_default_company(db)

    status_val = (job_in.status or "ACTIVE").upper()
    if status_val not in VALID_JOB_STATUSES:
        status_val = "ACTIVE"

    approval_val = (job_in.approval_status or "APPROVED").upper()
    if approval_val not in VALID_APPROVAL_STATUSES:
        approval_val = "APPROVED"

    deadline_val = job_in.deadline or date.today()

    db_job = JobPost(
        company_id=target_company_id,
        title=job_in.title.strip(),
        description=job_in.description.strip(),
        requirements=job_in.requirements.strip(),
        location=job_in.location or "TP. Hồ Chí Minh",
        salary_range=job_in.salary_range or "Thỏa thuận",
        job_type=job_in.job_type or "INTERNSHIP",
        experience_level=job_in.experience_level or "Không yêu cầu",
        deadline=deadline_val,
        status=status_val,
        approval_status=approval_val
    )

    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def update_job(db: Session, job_id: int, job_in: JobUpdate) -> Optional[JobPost]:
    """
    Cập nhật toàn diện nội dung tin tuyển dụng:
    Tiêu đề, mô tả, yêu cầu, lương, hạn nộp, trạng thái...
    """
    db_job = get_job_by_id(db, job_id)
    if not db_job:
        return None

    if hasattr(job_in, "model_dump"):
        update_data = job_in.model_dump(exclude_unset=True)
    else:
        update_data = job_in.dict(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None:
            if field == "status":
                val = value.upper()
                if val in VALID_JOB_STATUSES:
                    setattr(db_job, field, val)
            elif field == "approval_status":
                val = value.upper()
                if val in VALID_APPROVAL_STATUSES:
                    setattr(db_job, field, val)
            else:
                setattr(db_job, field, value)

    db.commit()
    db.refresh(db_job)
    return db_job

def update_job_status(db: Session, job_id: int, new_status: str) -> Optional[JobPost]:
    """
    Thực hiện chức năng ĐÓNG / ẨN / MỞ LẠI tin tuyển dụng:
    - ACTIVE: Đang tuyển dụng công khai
    - CLOSED: Đã đóng tuyển dụng (không nhận thêm hồ sơ)
    - HIDDEN: Tạm ẩn tin tuyển dụng (không hiển thị cho ứng viên)
    """
    db_job = get_job_by_id(db, job_id)
    if not db_job:
        return None

    status_normalized = new_status.strip().upper()
    if status_normalized not in VALID_JOB_STATUSES:
        raise ValueError(f"Trạng thái không hợp lệ: {new_status}. Hợp lệ gồm: {', '.join(VALID_JOB_STATUSES)}")

    db_job.status = status_normalized
    db.commit()
    db.refresh(db_job)
    return db_job

def delete_job(db: Session, job_id: int) -> bool:
    """Xóa hoàn toàn tin tuyển dụng"""
    db_job = get_job_by_id(db, job_id)
    if not db_job:
        return False
    db.delete(db_job)
    db.commit()
    return True
