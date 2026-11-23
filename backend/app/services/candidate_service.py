"""
Dịch vụ Quản lý Hồ sơ Ứng viên (Candidate Service)
Theo đặc tả SRS UniCareer mục 10.2.2 & 11.2 (Candidate Module)
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.candidate import Candidate
from backend.app.models.user import User
from backend.app.schemas.user import CandidateProfileUpdate, CandidateProfileResponse


def get_candidate_profile(db: Session, candidate_id: int) -> CandidateProfileResponse:
    """Lấy thông tin hồ sơ của ứng viên kèm email tài khoản"""
    candidate = db.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
    user = db.query(User).filter(User.user_id == candidate_id).first()

    if not candidate:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ứng viên #{candidate_id} không tồn tại."
            )
        # Tự động tạo hồ sơ trống nếu tài khoản đã tồn tại mà chưa có bản ghi candidate
        candidate = Candidate(
            candidate_id=user.user_id,
            full_name=user.email.split("@")[0].title(),
            university="Chưa cập nhật",
            major="Chưa cập nhật"
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

    return CandidateProfileResponse(
        candidate_id=candidate.candidate_id,
        full_name=candidate.full_name,
        phone=candidate.phone,
        university=candidate.university,
        major=candidate.major,
        skills=candidate.skills,
        bio=candidate.bio,
        cv_url=candidate.cv_url,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at,
        email=user.email if user else None
    )


def update_candidate_profile(db: Session, candidate_id: int, data: CandidateProfileUpdate) -> CandidateProfileResponse:
    """Cập nhật thông tin hồ sơ cá nhân của sinh viên"""
    candidate = db.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
    user = db.query(User).filter(User.user_id == candidate_id).first()

    if not candidate:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ứng viên #{candidate_id} không tồn tại."
            )
        candidate = Candidate(candidate_id=candidate_id, full_name="Sinh viên mới")
        db.add(candidate)

    # Cập nhật các trường được truyền lên
    if data.full_name is not None:
        candidate.full_name = data.full_name.strip()
    if data.phone is not None:
        candidate.phone = data.phone.strip()
    if data.university is not None:
        candidate.university = data.university.strip()
    if data.major is not None:
        candidate.major = data.major.strip()
    if data.skills is not None:
        candidate.skills = data.skills.strip()
    if data.bio is not None:
        candidate.bio = data.bio.strip()
    if data.cv_url is not None:
        candidate.cv_url = data.cv_url.strip()

    db.commit()
    db.refresh(candidate)

    return CandidateProfileResponse(
        candidate_id=candidate.candidate_id,
        full_name=candidate.full_name,
        phone=candidate.phone,
        university=candidate.university,
        major=candidate.major,
        skills=candidate.skills,
        bio=candidate.bio,
        cv_url=candidate.cv_url,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at,
        email=user.email if user else None
    )
