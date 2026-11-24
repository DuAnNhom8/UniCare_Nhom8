from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.company import CompanyModel
from app.models.job import JobModel
from app.models.user import UserModel
from app.schemas.job import JobCreate, JobResponse, JobStatusUpdate, JobUpdate, PublicJobList, PublicJobResponse
from app.services import company_service, job_service


router = APIRouter(prefix="/jobs", tags=["Tin tuyển dụng"])


@router.get("/public", response_model=PublicJobList)
def public_jobs(
    keyword: str | None = Query(default=None, max_length=100),
    location: str | None = Query(default=None, max_length=100),
    job_type: str | None = Query(default=None),
    salary: str | None = Query(default=None),
    sort: str = Query(default="latest"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return job_service.list_public_jobs(
        db, keyword=keyword, location=location, job_type=job_type,
        salary=salary, sort=sort, skip=skip, limit=limit,
    )


@router.get("/public/{job_id}", response_model=PublicJobResponse)
def public_job_detail(job_id: int, db: Session = Depends(get_db)):
    job = job_service.get_public_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Tin không tồn tại hoặc không còn được công khai")
    return job_service.job_payload(job)


@router.get("", response_model=list[JobResponse])
def list_jobs(
    company_id: int | None = Query(default=None, gt=0),
    status_filter: str | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: UserModel = Depends(require_roles("employer", "admin")),
    db: Session = Depends(get_db),
):
    if current_user.role.lower() == "employer":
        company = company_service.get_company_for_employer(db, current_user.id)
        if company is None:
            return []
        company_id = company.id
    jobs = job_service.list_jobs(db, company_id=company_id, status_filter=status_filter, skip=skip, limit=limit)
    return [job_service.job_payload(job) for job in jobs]


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    data: JobCreate,
    current_user: UserModel = Depends(require_roles("employer")),
    db: Session = Depends(get_db),
):
    company = company_service.get_company_for_employer(db, current_user.id)
    if company is None:
        raise HTTPException(status_code=409, detail="Hãy hoàn thiện hồ sơ doanh nghiệp trước khi đăng tin")
    job = job_service.create_job(db, company.id, data)
    return job_service.job_payload(job_service.get_job(db, job.id))


def _owned_job(db: Session, job_id: int, current_user: UserModel) -> JobModel:
    job = job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tin tuyển dụng")
    if current_user.role.lower() == "employer":
        company = company_service.get_company_for_employer(db, current_user.id)
        if company is None or job.company_id != company.id:
            raise HTTPException(status_code=404, detail="Không tìm thấy tin tuyển dụng")
    return job


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    current_user: UserModel = Depends(require_roles("employer", "admin")),
    db: Session = Depends(get_db),
):
    return job_service.job_payload(_owned_job(db, job_id, current_user))


@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    data: JobUpdate,
    current_user: UserModel = Depends(require_roles("employer", "admin")),
    db: Session = Depends(get_db),
):
    job = _owned_job(db, job_id, current_user)
    updated = job_service.update_job(db, job, data)
    return job_service.job_payload(updated)


@router.patch("/{job_id}/status", response_model=JobResponse)
def update_job_status(
    job_id: int,
    data: JobStatusUpdate,
    current_user: UserModel = Depends(require_roles("employer", "admin")),
    db: Session = Depends(get_db),
):
    job = _owned_job(db, job_id, current_user)
    updated = job_service.set_job_status(db, job, data.status)
    return job_service.job_payload(updated)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    current_user: UserModel = Depends(require_roles("employer", "admin")),
    db: Session = Depends(get_db),
):
    job = _owned_job(db, job_id, current_user)
    db.delete(job)
    db.commit()