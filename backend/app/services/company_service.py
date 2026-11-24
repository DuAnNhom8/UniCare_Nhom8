from __future__ import annotations
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.application import ApplicationModel
from app.models.company import CompanyModel
from app.models.job import JobModel
from app.models.user import UserModel


def get_company_for_employer(db: Session, employer_id: int) -> CompanyModel | None:
    return db.query(CompanyModel).filter(CompanyModel.employer_id == employer_id).first()


def save_company_profile(db: Session, employer: UserModel, data: dict) -> CompanyModel | None:
    company = get_company_for_employer(db, employer.id)
    if company is None:
        company_name = data.get("company_name") or (employer.profile.full_name if employer.profile else "")
        if not company_name.strip():
            return None
        company = CompanyModel(employer_id=employer.id, company_name=company_name.strip())
        db.add(company)

    for field, value in data.items():
        if value is not None:
            setattr(company, field, value.strip() or None if isinstance(value, str) else value)
    db.commit()
    db.refresh(company)
    return company


def company_summary(db: Session, company: CompanyModel) -> dict:
    job_count = db.query(JobModel).filter(JobModel.company_id == company.id).count()
    application_count = (
        db.query(func.count(ApplicationModel.id))
        .join(JobModel, ApplicationModel.job_id == JobModel.id)
        .filter(JobModel.company_id == company.id)
        .scalar()
    )
    return {
        "id": company.id,
        "company_id": company.id,
        "employer_id": company.employer_id,
        "company_name": company.company_name,
        "description": company.description,
        "website": company.website,
        "industry": company.industry,
        "location": company.location,
        "created_at": company.created_at,
        "updated_at": company.updated_at,
        "job_count": job_count,
        "application_count": application_count or 0,
    }
