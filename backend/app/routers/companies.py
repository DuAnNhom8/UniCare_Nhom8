from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..deps import require_role
from ..models import Company, User
from ..schemas import CompanyOut, CompanyUpdate

router = APIRouter(prefix='/companies', tags=['Companies'])
employer_only = require_role('EMPLOYER')

def own_company(db: Session, employer_id: int) -> Company:
    from sqlalchemy import select
    company = db.scalar(select(Company).where(Company.employer_id == employer_id))
    if company is None:
        raise HTTPException(404, 'Không tìm thấy công ty')
    return company

@router.get('/me', response_model=CompanyOut)
def get_company(user: User = Depends(employer_only), db: Session = Depends(get_db)):
    return own_company(db, user.user_id)

@router.patch('/me', response_model=CompanyOut)
def update_company(data: CompanyUpdate, user: User = Depends(employer_only), db: Session = Depends(get_db)):
    company = own_company(db, user.user_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == 'company_name' and value is None:
            raise HTTPException(422, 'company_name không được rỗng')
        setattr(company, field, str(value) if field == 'website' and value is not None else value)
    db.commit()
    return company
