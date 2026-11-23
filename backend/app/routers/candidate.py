"""
API Router cho phân hệ Sinh viên / Ứng viên (Candidate Router)
Theo đặc tả SRS UniCareer mục 10.2.2, 10.2.5 & 11.2 (Candidate & Application Module)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.user import CandidateProfileUpdate, CandidateProfileResponse
from backend.app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationDetailResponse
from backend.app.services import candidate_service, apply_service

router = APIRouter(
    prefix="/candidates",
    tags=["Ứng viên & Hồ sơ (Candidates)"]
)


@router.get(
    "/profile",
    response_model=CandidateProfileResponse,
    summary="Xem thông tin hồ sơ ứng viên"
)
def get_profile(
    user_id: int = Query(..., description="Mã ứng viên (users.user_id)"),
    db: Session = Depends(get_db)
):
    """Lấy thông tin chi tiết hồ sơ cá nhân và kỹ năng của ứng viên"""
    return candidate_service.get_candidate_profile(db, user_id)


@router.put(
    "/profile",
    response_model=CandidateProfileResponse,
    summary="Cập nhật hồ sơ cá nhân của sinh viên"
)
def update_profile(
    data: CandidateProfileUpdate,
    user_id: int = Query(..., description="Mã ứng viên (users.user_id)"),
    db: Session = Depends(get_db)
):
    """Chỉnh sửa họ tên, số điện thoại, trường học, kỹ năng và CV của sinh viên"""
    return candidate_service.update_candidate_profile(db, user_id, data)


@router.post(
    "/apply",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Nộp đơn ứng tuyển vào vị trí việc làm"
)
def apply_to_job(
    data: ApplicationCreate,
    user_id: int = Query(None, description="Mã ứng viên (nếu truyền qua query string)"),
    db: Session = Depends(get_db)
):
    """
    Ứng viên nộp hồ sơ ứng tuyển:
    - Ràng buộc: Tin tuyển dụng phải ACTIVE, APPROVED và chưa hết hạn
    - Ràng buộc duy nhất: Một ứng viên không nộp trùng đơn cho cùng 1 tin
    """
    candidate_id = data.candidate_id or user_id
    if not candidate_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thiếu thông tin mã ứng viên (candidate_id)."
        )
    return apply_service.apply_job(db, data, candidate_id)


@router.get(
    "/applications",
    response_model=List[ApplicationDetailResponse],
    summary="Xem danh sách các đơn đã ứng tuyển"
)
def get_my_applications(
    user_id: int = Query(..., description="Mã ứng viên (users.user_id)"),
    db: Session = Depends(get_db)
):
    """Lấy danh sách các công việc đã nộp kèm trạng thái (RECEIVED, REVIEWING, ACCEPTED, REJECTED)"""
    return apply_service.get_candidate_applications(db, user_id)
