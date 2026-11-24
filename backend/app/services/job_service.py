from datetime import date

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.company import CompanyModel
from app.models.job import JobModel
from app.schemas.job import JobCreate, JobUpdate

JOB_TYPES = {"FULL_TIME", "PART_TIME", "INTERNSHIP"}
JOB_STATUSES = {"ACTIVE", "CLOSED", "HIDDEN"}
APPROVAL_STATUSES = {"PENDING", "APPROVED", "REJECTED"}


def job_payload(job: JobModel) -> dict:
    return {
        "job_id": job.id,
        "company_id": job.company_id,
        "title": job.title,
        "description": job.description,
        "requirements": job.requirements,
        "location": job.location,
        "salary_range": job.salary_range,
        "job_type": job.job_type,
        "experience_level": job.experience_level,
        "deadline": job.deadline,
        "status": job.status,
        "approval_status": job.approval_status,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "company_name": job.company.company_name if job.company else None,
        "company_description": job.company.description if job.company else None,
        "company_website": job.company.website if job.company else None,
        "company_industry": job.company.industry if job.company else None,
        "application_count": len(job.applications),
    }


def validate_job_type(value: str) -> str:
    normalized = value.strip().upper()
    if normalized not in JOB_TYPES:
        raise HTTPException(status_code=422, detail="Loại công việc không hợp lệ")
    return normalized


def create_job(db: Session, company_id: int, data: JobCreate) -> JobModel:
    if data.deadline < date.today():
        raise HTTPException(status_code=422, detail="Hạn ứng tuyển phải từ hôm nay trở đi")
    job = JobModel(
        company_id=company_id,
        title=data.title.strip(),
        description=data.description.strip(),
        requirements=data.requirements.strip(),
        location=data.location.strip() if data.location else None,
        salary_range=data.salary_range.strip() if data.salary_range else None,
        job_type=validate_job_type(data.job_type),
        experience_level=data.experience_level.strip() if data.experience_level else None,
        deadline=data.deadline,
        status="ACTIVE",
        approval_status="PENDING",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def list_jobs(
    db: Session,
    *,
    company_id: int | None = None,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[JobModel]:
    query = db.query(JobModel).options(joinedload(JobModel.company), joinedload(JobModel.applications))
    if company_id is not None:
        query = query.filter(JobModel.company_id == company_id)
    if status_filter:
        normalized = status_filter.strip().upper()
        if normalized not in JOB_STATUSES:
            raise HTTPException(status_code=422, detail="Trạng thái tin tuyển dụng không hợp lệ")
        query = query.filter(JobModel.status == normalized)
    return query.order_by(JobModel.created_at.desc(), JobModel.id.desc()).offset(skip).limit(limit).all()


def get_job(db: Session, job_id: int) -> JobModel | None:
    return (
        db.query(JobModel)
        .options(joinedload(JobModel.company), joinedload(JobModel.applications))
        .filter(JobModel.id == job_id)
        .first()
    )


def update_job(db: Session, job: JobModel, data: JobUpdate) -> JobModel:
    updates = data.model_dump(exclude_unset=True)
    if "deadline" in updates and updates["deadline"] and updates["deadline"] < date.today():
        raise HTTPException(status_code=422, detail="Hạn ứng tuyển phải từ hôm nay trở đi")
    if updates.get("job_type") is not None:
        updates["job_type"] = validate_job_type(updates["job_type"])
    for field, value in updates.items():
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip() or None
        setattr(job, field, value)
    db.commit()
    return get_job(db, job.id)


def set_job_status(db: Session, job: JobModel, new_status: str) -> JobModel:
    normalized = new_status.strip().upper()
    if normalized not in JOB_STATUSES:
        raise HTTPException(status_code=422, detail="Trạng thái tin tuyển dụng không hợp lệ")
    job.status = normalized
    db.commit()
    return get_job(db, job.id)


def list_public_jobs(
    db: Session,
    *,
    keyword: str | None = None,
    location: str | None = None,
    job_type: str | None = None,
    salary: str | None = None,
    sort: str = "latest",
    skip: int = 0,
    limit: int = 12,
) -> dict:
    query = (
        db.query(JobModel)
        .options(joinedload(JobModel.company), joinedload(JobModel.applications))
        .join(CompanyModel, CompanyModel.id == JobModel.company_id)
        .filter(
            JobModel.status == "ACTIVE",
            JobModel.approval_status == "APPROVED",
            JobModel.deadline >= date.today(),
        )
    )
    if keyword and keyword.strip():
        escaped = keyword.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        search = f"%{escaped}%"
        query = query.filter(or_(
            JobModel.title.ilike(search, escape="\\"),
            JobModel.description.ilike(search, escape="\\"),
            JobModel.requirements.ilike(search, escape="\\"),
            CompanyModel.company_name.ilike(search, escape="\\"),
        ))
    if location and location.strip():
        query = query.filter(JobModel.location.ilike(f"%{location.strip()}%"))
    if job_type:
        query = query.filter(JobModel.job_type == validate_job_type(job_type))
    if salary == "negotiable":
        query = query.filter(JobModel.salary_range.ilike("%thỏa thuận%"))
    elif salary == "paid":
        query = query.filter(JobModel.salary_range.isnot(None), ~JobModel.salary_range.ilike("%thỏa thuận%"))
    elif salary is not None:
        raise HTTPException(status_code=422, detail="Bộ lọc lương không hợp lệ")
    total = query.count()
    if sort == "deadline":
        query = query.order_by(JobModel.deadline.asc(), JobModel.id.desc())
    elif sort == "latest":
        query = query.order_by(JobModel.created_at.desc(), JobModel.id.desc())
    else:
        raise HTTPException(status_code=422, detail="Cách sắp xếp không hợp lệ")
    jobs = query.offset(skip).limit(limit).all()
    return {"items": [job_payload(job) for job in jobs], "total": total, "skip": skip, "limit": limit}


def get_public_job(db: Session, job_id: int) -> JobModel | None:
    return (
        db.query(JobModel)
        .options(joinedload(JobModel.company), joinedload(JobModel.applications))
        .filter(
            JobModel.id == job_id,
            JobModel.status == "ACTIVE",
            JobModel.approval_status == "APPROVED",
            JobModel.deadline >= date.today(),
        )
        .first()
    )


def set_approval_status(db: Session, job: JobModel, approval_status: str) -> JobModel:
    normalized = approval_status.strip().upper()
    if normalized not in APPROVAL_STATUSES:
        raise HTTPException(status_code=422, detail="Trạng thái kiểm duyệt không hợp lệ")
    job.approval_status = normalized
    db.commit()
    return get_job(db, job.id)