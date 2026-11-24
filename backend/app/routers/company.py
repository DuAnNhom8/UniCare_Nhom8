from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.company import CompanyModel
from app.models.user import UserModel
from app.schemas.application import ApplicationDetail, ApplicationStatusUpdate
from app.schemas.company import CompanyResponse, CompanyUpdate
from app.services import apply_service, company_service


router = APIRouter(prefix="/companies", tags=["Doanh nghiệp"])


@router.get("", response_model=list[CompanyResponse])
def list_companies(db: Session = Depends(get_db)):
    companies = db.query(CompanyModel).order_by(CompanyModel.company_name.asc()).all()
    return [company_service.company_summary(db, company) for company in companies]


@router.get("/profile/current", response_model=CompanyResponse)
def get_current_company(
    current_user: UserModel = Depends(require_roles("employer")),
    db: Session = Depends(get_db),
):
    company = company_service.get_company_for_employer(db, current_user.id)
    if company is None:
        raise HTTPException(status_code=404, detail="Chưa có hồ sơ doanh nghiệp")
    return company_service.company_summary(db, company)


@router.put("/profile/current", response_model=CompanyResponse)
def update_current_company(
    data: CompanyUpdate,
    current_user: UserModel = Depends(require_roles("employer")),
    db: Session = Depends(get_db),
):
    company = company_service.save_company_profile(db, current_user, data.model_dump(exclude_unset=True))
    if company is None:
        raise HTTPException(status_code=422, detail="Tên doanh nghiệp không được để trống")
    return company_service.company_summary(db, company)


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy doanh nghiệp")
    return company_service.company_summary(db, company)


@router.get("/{company_id}/applications", response_model=list[ApplicationDetail])
def list_company_applications(
    company_id: int,
    current_user: UserModel = Depends(require_roles("employer", "admin")),
    db: Session = Depends(get_db),
):
    company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
    if company is None or (current_user.role.lower() == "employer" and company.employer_id != current_user.id):
        raise HTTPException(status_code=404, detail="Không tìm thấy doanh nghiệp")
    return apply_service.list_company_applications(db, company.id)


@router.put("/{company_id}/applications/{application_id}/status", response_model=ApplicationDetail)
def update_application_status(
    company_id: int,
    application_id: int,
    data: ApplicationStatusUpdate,
    current_user: UserModel = Depends(require_roles("employer")),
    db: Session = Depends(get_db),
):
    company = company_service.get_company_for_employer(db, current_user.id)
    if company is None or company.id != company_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn ứng tuyển")
    return apply_service.update_company_application(db, company.id, application_id, data.status)
