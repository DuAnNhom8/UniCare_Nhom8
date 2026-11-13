"""
API Router cho phân hệ Quản lý Tin tuyển dụng (Jobs Router)
Theo đặc tả SRS UniCareer mục 10.2.4 & Task T05FE9A
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.job import (
    JobCreate,
    JobUpdate,
    JobStatusUpdate,
    JobResponse
)
from backend.app.services import job_service

router = APIRouter(
    prefix="/jobs",
    tags=["Tin tuyển dụng (Job Posts)"]
)

@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng tin tuyển dụng mới (Tạo tin tuyển dụng)"
)
def create_job_post(
    job_in: JobCreate,
    db: Session = Depends(get_db)
):
    """
    Tạo mới một tin tuyển dụng cho doanh nghiệp:
    - **title**: Tên vị trí tuyển dụng (VD: Backend Developer Intern)
    - **description**: Mô tả chi tiết công việc
    - **requirements**: Yêu cầu ứng viên
    - **location**: Nơi làm việc (Hà Nội, TP.HCM, Remote, Hybrid...)
    - **salary_range**: Mức lương
    - **job_type**: INTERNSHIP / FULL_TIME / PART_TIME
    - **deadline**: Hạn chót nộp đơn
    - **status**: Trạng thái (mặc định: ACTIVE)
    """
    try:
        new_job = job_service.create_job(db, job_in)
        return new_job
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lỗi khi tạo tin tuyển dụng: {str(e)}"
        )

@router.get(
    "",
    response_model=List[JobResponse],
    summary="Xem danh sách tin tuyển dụng"
)
def list_job_posts(
    skip: int = Query(0, ge=0, description="Số bản ghi bỏ qua"),
    limit: int = Query(50, ge=1, le=100, description="Số lượng bản ghi tối đa"),
    company_id: Optional[int] = Query(None, description="Lọc theo mã doanh nghiệp"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái (ACTIVE, CLOSED, HIDDEN)"),
    keyword: Optional[str] = Query(None, description="Tìm kiếm từ khóa trong tiêu đề, địa điểm, mô tả"),
    job_type: Optional[str] = Query(None, description="Lọc theo loại hình công việc"),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách các tin tuyển dụng:
    Hỗ trợ tìm kiếm, phân trang và lọc theo trạng thái hiển thị (ACTIVE, CLOSED, HIDDEN).
    """
    return job_service.get_jobs(
        db,
        skip=skip,
        limit=limit,
        company_id=company_id,
        status=status,
        keyword=keyword,
        job_type=job_type
    )

@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Xem chi tiết một tin tuyển dụng"
)
def get_job_post_detail(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Lấy thông tin chi tiết của một tin tuyển dụng cụ thể theo mã job_id"""
    job = job_service.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy tin tuyển dụng có mã ID {job_id}"
        )
    return job

@router.put(
    "/{job_id}",
    response_model=JobResponse,
    summary="Cập nhật toàn diện tin tuyển dụng"
)
def update_job_post(
    job_id: int,
    job_in: JobUpdate,
    db: Session = Depends(get_db)
):
    """
    Cập nhật nội dung tin tuyển dụng:
    Cho phép sửa tiêu đề, mô tả, yêu cầu, hạn nộp hồ sơ, mức lương, trạng thái...
    """
    updated_job = job_service.update_job(db, job_id, job_in)
    if not updated_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy tin tuyển dụng có ID {job_id} để cập nhật"
        )
    return updated_job

@router.patch(
    "/{job_id}/status",
    response_model=JobResponse,
    summary="Đóng / Ẩn / Mở lại tin tuyển dụng (Cập nhật trạng thái)"
)
def update_job_post_status(
    job_id: int,
    status_in: JobStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Thực hiện chức năng Đóng hoặc Ẩn tin tuyển dụng:
    - **ACTIVE**: Mở lại tin tuyển dụng công khai
    - **CLOSED**: Đóng tin tuyển dụng (khi đã tuyển đủ người hoặc hết hạn)
    - **HIDDEN**: Tạm ẩn tin tuyển dụng (không hiển thị ngoài trang chủ/tìm kiếm)
    """
    try:
        updated_job = job_service.update_job_status(db, job_id, status_in.status)
        if not updated_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy tin tuyển dụng có ID {job_id}"
            )
        return updated_job
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa tin tuyển dụng"
)
def delete_job_post(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Xóa bỏ một tin tuyển dụng khỏi hệ thống"""
    success = job_service.delete_job(db, job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy tin tuyển dụng có ID {job_id} để xóa"
        )
    return {"message": f"Đã xóa thành công tin tuyển dụng ID {job_id}"}
