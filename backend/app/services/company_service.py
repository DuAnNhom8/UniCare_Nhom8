"""
Dịch vụ xử lý nghiệp vụ Doanh nghiệp (Company Service)
Theo đặc tả SRS UniCareer mục 10.2.3 & Task T85FE99
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.company import Company
from backend.app.schemas.company import CompanyCreate, CompanyUpdate

def get_company_by_id(db: Session, company_id: int) -> Optional[Company]:
    """Lấy thông tin chi tiết công ty theo ID"""
    return db.query(Company).filter(Company.company_id == company_id).first()

def get_company_by_employer_id(db: Session, employer_id: int) -> Optional[Company]:
    """Lấy thông tin công ty theo ID của tài khoản nhà tuyển dụng"""
    return db.query(Company).filter(Company.employer_id == employer_id).first()

def get_companies(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    keyword: Optional[str] = None,
    industry: Optional[str] = None
) -> List[Company]:
    """Lấy danh sách các công ty kèm lọc tìm kiếm và phân trang"""
    query = db.query(Company)
    if keyword:
        query = query.filter(Company.company_name.ilike(f"%{keyword}%"))
    if industry:
        query = query.filter(Company.industry.ilike(f"%{industry}%"))
    return query.offset(skip).limit(limit).all()

def create_company(db: Session, company_in: CompanyCreate) -> Company:
    """
    Tạo mới thông tin doanh nghiệp.
    Mỗi nhà tuyển dụng (employer_id) chỉ được sở hữu 1 hồ sơ doanh nghiệp (1-1).
    """
    existing_company = get_company_by_employer_id(db, company_in.employer_id)
    if existing_company:
        raise ValueError(f"Nhà tuyển dụng ID {company_in.employer_id} đã có hồ sơ doanh nghiệp.")
    
    db_company = Company(
        employer_id=company_in.employer_id,
        company_name=company_in.company_name,
        description=company_in.description,
        website=company_in.website,
        industry=company_in.industry,
        location=company_in.location
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def update_company(db: Session, company_id: int, company_in: CompanyUpdate) -> Optional[Company]:
    """
    Cập nhật thông tin doanh nghiệp theo ID.
    Chỉ cập nhật các trường được gửi lên.
    """
    db_company = get_company_by_id(db, company_id)
    if not db_company:
        return None
    
    # Lấy dữ liệu update (tương thích Pydantic v1 & v2)
    if hasattr(company_in, "model_dump"):
        update_data = company_in.model_dump(exclude_unset=True)
    else:
        update_data = company_in.dict(exclude_unset=True)
        
    for field, value in update_data.items():
        if value is not None:
            setattr(db_company, field, value)
            
    db.commit()
    db.refresh(db_company)
    return db_company

def delete_company(db: Session, company_id: int) -> bool:
    """Xóa doanh nghiệp theo ID"""
    db_company = get_company_by_id(db, company_id)
    if not db_company:
        return False
    db.delete(db_company)
    db.commit()
    return True
