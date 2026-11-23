"""
API Router cho phân hệ Doanh nghiệp (Company Router)
Theo đặc tả SRS UniCareer mục 10.2.3 & Task T85FE99
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse
)
from backend.app.services import company_service

router = APIRouter(
    prefix="/companies",
    tags=["Doanh nghiệp (Companies)"]
)

@router.post(
    "",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới hồ sơ doanh nghiệp"
)
def create_new_company(
    company_in: CompanyCreate,
    db: Session = Depends(get_db)
):
    """
    Tạo hồ sơ doanh nghiệp mới cho nhà tuyển dụng.
    - **company_name**: Tên công ty (bắt buộc, 2 - 150 ký tự)
    - **employer_id**: ID của tài khoản nhà tuyển dụng (mỗi tài khoản chỉ có 1 hồ sơ công ty)
    - **description**: Mô tả / giới thiệu
    - **website**: Đường dẫn trang web
    - **industry**: Lĩnh vực hoạt động
    - **location**: Địa chỉ trụ sở chính
    """
    try:
        new_company = company_service.create_company(db, company_in)
        return new_company
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "",
    response_model=List[CompanyResponse],
    summary="Xem danh sách doanh nghiệp"
)
def list_companies(
    skip: int = Query(0, ge=0, description="Số bản ghi bỏ qua (phân trang)"),
    limit: int = Query(20, ge=1, le=100, description="Số bản ghi tối đa trả về"),
    keyword: Optional[str] = Query(None, description="Tìm kiếm theo tên công ty"),
    industry: Optional[str] = Query(None, description="Lọc theo ngành nghề/lĩnh vực"),
    db: Session = Depends(get_db)
):
    """Lấy danh sách các doanh nghiệp trên hệ thống (dành cho ứng viên & khách xem)"""
    return company_service.get_companies(
        db,
        skip=skip,
        limit=limit,
        keyword=keyword,
        industry=industry
    )

@router.get(
    "/by-employer/{employer_id}",
    response_model=CompanyResponse,
    summary="Xem thông tin công ty theo Employer ID"
)
def get_company_by_employer(
    employer_id: int,
    db: Session = Depends(get_db)
):
    """Lấy thông tin doanh nghiệp theo ID tài khoản nhà tuyển dụng"""
    company = company_service.get_company_by_employer_id(db, employer_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy hồ sơ doanh nghiệp cho tài khoản ID {employer_id}"
        )
    return company

@router.get(
    "/profile/current",
    response_model=CompanyResponse,
    summary="Xem hồ sơ công ty của nhà tuyển dụng hiện tại"
)
def get_current_company_profile(
    employer_id: int = Query(2, description="ID nhà tuyển dụng hiện tại (mặc định demo là 2 - TechNova)"),
    db: Session = Depends(get_db)
):
    """API lấy thông tin công ty phục vụ trang thông tin doanh nghiệp trên giao diện Web"""
    company = company_service.get_company_by_employer_id(db, employer_id)
    if not company:
        # Nếu chưa có, thử tìm company_id=1
        company = company_service.get_company_by_id(db, 1)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chưa có thông tin doanh nghiệp. Vui lòng tạo mới!"
        )
    return company

@router.put(
    "/profile/current",
    response_model=CompanyResponse,
    summary="Cập nhật hồ sơ công ty của nhà tuyển dụng hiện tại"
)
def update_current_company_profile(
    company_in: CompanyUpdate,
    employer_id: int = Query(2, description="ID nhà tuyển dụng hiện tại"),
    db: Session = Depends(get_db)
):
    """API cập nhật nhanh hồ sơ công ty từ trang thông tin doanh nghiệp"""
    company = company_service.get_company_by_employer_id(db, employer_id)
    if not company:
        company = company_service.get_company_by_id(db, 1)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông tin doanh nghiệp để cập nhật."
        )
    updated = company_service.update_company(db, company.company_id, company_in)
    return updated

@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Xem chi tiết thông tin một doanh nghiệp theo ID"
)
def get_company_detail(
    company_id: int,
    db: Session = Depends(get_db)
):
    """Lấy thông tin chi tiết của một doanh nghiệp dựa trên company_id"""
    company = company_service.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy doanh nghiệp có ID {company_id}"
        )
    return company

@router.put(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Cập nhật thông tin doanh nghiệp theo ID"
)
def update_company_info(
    company_id: int,
    company_in: CompanyUpdate,
    db: Session = Depends(get_db)
):
    """
    Cập nhật các trường thông tin của doanh nghiệp:
    - **company_name**: Tên công ty mới
    - **description**: Giới thiệu công ty
    - **website**: Địa chỉ website
    - **industry**: Lĩnh vực hoạt động
    - **location**: Địa chỉ trụ sở
    """
    updated_company = company_service.update_company(db, company_id, company_in)
    if not updated_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy doanh nghiệp có ID {company_id} để cập nhật"
        )
    return updated_company

@router.delete(
    "/{company_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa thông tin doanh nghiệp"
)
def delete_company(
    company_id: int,
    db: Session = Depends(get_db)
):
    """Xóa doanh nghiệp khỏi hệ thống"""
    success = company_service.delete_company(db, company_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy doanh nghiệp có ID {company_id} để xóa"
        )
    return {"message": f"Đã xóa thành công doanh nghiệp ID {company_id}"}
