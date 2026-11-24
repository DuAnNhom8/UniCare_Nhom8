from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import CV_STORAGE_DIR
from app.core.database import get_db
from app.core.security import get_current_user, hash_password, require_roles, verify_password
from app.models.profile import ProfileModel
from app.models.user import UserModel
from app.models.cv import CVModel
from app.schemas.cv import CVResponse
from app.schemas.user import (
    CVUpdate,
    PasswordChange,
    ProfileResponse,
    ProfileUpdate,
)
from app.services.cv_service import cv_payload, delete_cv_record, render_cv_html
from fastapi.responses import Response


router = APIRouter(prefix="/users", tags=["User Profile"])

CV_UPLOAD_DIR = CV_STORAGE_DIR


def profile_payload(user: UserModel, profile: ProfileModel | None) -> dict:
    if profile is None:
        return {
            "id": None,
            "user_id": user.id,
            "email": user.email,
            "full_name": "",
            "phone": None,
            "avatar_url": None,
            "github_url": None,
            "linkedin_url": None,
            "job_search_status": "OPEN",
        }
    return {
        "id": profile.id,
        "user_id": user.id,
        "email": user.email,
        "full_name": profile.full_name,
        "phone": profile.phone,
        "avatar_url": profile.avatar_url,
        "github_url": profile.github_url,
        "linkedin_url": profile.linkedin_url,
        "job_search_status": profile.job_search_status or "OPEN",
    }


@router.get("/me/profile", response_model=ProfileResponse)
def get_my_profile(
    current_user: UserModel = Depends(require_roles("candidate", "admin")),
    db: Session = Depends(get_db),
):
    profile = db.query(ProfileModel).filter(ProfileModel.user_id == current_user.id).first()
    return profile_payload(current_user, profile)


@router.put("/me/profile", response_model=ProfileResponse)
def update_my_profile(
    request: ProfileUpdate,
    current_user: UserModel = Depends(require_roles("candidate", "admin")),
    db: Session = Depends(get_db),
):
    profile = db.query(ProfileModel).filter(ProfileModel.user_id == current_user.id).first()

    if request.email is not None:
        new_email = str(request.email).lower()
        if new_email != current_user.email:
            existing = db.query(UserModel).filter(
                UserModel.email == new_email,
                UserModel.id != current_user.id,
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email đã được sử dụng",
                )
            current_user.email = new_email

    if profile is None:
        profile = ProfileModel(
            user_id=current_user.id,
            full_name=(request.full_name or "").strip(),
        )
        profile.phone = request.phone
        profile.avatar_url = request.avatar_url
        profile.github_url = request.github_url
        profile.linkedin_url = request.linkedin_url
        profile.job_search_status = request.job_search_status or "OPEN"
        db.add(profile)
    else:
        if request.full_name is not None:
            profile.full_name = request.full_name.strip()
        if "phone" in request.model_fields_set:
            profile.phone = request.phone
        if "avatar_url" in request.model_fields_set:
            profile.avatar_url = request.avatar_url
        if "github_url" in request.model_fields_set:
            profile.github_url = request.github_url
        if "linkedin_url" in request.model_fields_set:
            profile.linkedin_url = request.linkedin_url
        if request.job_search_status is not None:
            profile.job_search_status = request.job_search_status

    if not profile.full_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Họ và tên không được để trống",
        )

    db.commit()
    db.refresh(profile)
    db.refresh(current_user)
    return profile_payload(current_user, profile)


@router.put("/me/password")
def change_my_password(
    request: PasswordChange,
    current_user: UserModel = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu hiện tại không chính xác",
        )
    if request.current_password == request.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu mới phải khác mật khẩu hiện tại",
        )
    current_user.hashed_password = hash_password(request.new_password)
    db.commit()
    return {"message": "Đã cập nhật mật khẩu"}


@router.get("/me/cvs", response_model=list[CVResponse])
def list_my_cvs(
    current_user: UserModel = Depends(require_roles("candidate", "admin")),
    db: Session = Depends(get_db),
):
    cvs = (
        db.query(CVModel)
        .filter(CVModel.user_id == current_user.id)
        .order_by(CVModel.updated_at.desc())
        .all()
    )
    return [cv_payload(cv) for cv in cvs]


@router.get("/me/cvs/{cv_id}/download")
def download_my_cv(
    cv_id: int,
    current_user: UserModel = Depends(require_roles("candidate", "admin")),
    db: Session = Depends(get_db),
):
    cv = db.query(CVModel).filter(CVModel.id == cv_id, CVModel.user_id == current_user.id).first()
    if cv is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy CV")
    if cv.cv_type == "builder":
        return Response(
            content=render_cv_html(cv),
            media_type="text/html; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="cv-{cv.id}.html"'},
        )
    stored_name = Path(cv.file_url or "").name
    if not stored_name or stored_name != cv.file_url or not (CV_UPLOAD_DIR / stored_name).is_file():
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp CV")
    return FileResponse(CV_UPLOAD_DIR / stored_name, filename=cv.file_name)


@router.put("/me/cvs/{cv_id}", response_model=CVResponse)
def update_my_cv(
    cv_id: int,
    request: CVUpdate,
    current_user: UserModel = Depends(require_roles("candidate", "admin")),
    db: Session = Depends(get_db),
):
    cv = (
        db.query(CVModel)
        .filter(CVModel.id == cv_id, CVModel.user_id == current_user.id)
        .first()
    )
    if cv is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy CV")

    if request.description is not None:
        cv.description = request.description.strip() or None
    if cv.cv_type == "builder":
        if request.title is not None:
            title = request.title.strip()
            if not title:
                raise HTTPException(status_code=422, detail="Tên CV không được để trống")
            cv.file_name = title
        if request.personal_info is not None:
            cv.personal_info = request.personal_info.model_dump(mode="json")
        if request.content is not None:
            cv.content = request.content.model_dump(mode="json")
    db.commit()
    db.refresh(cv)
    return cv_payload(cv)


@router.delete("/me/cvs/{cv_id}", status_code=204)
def delete_my_cv(
    cv_id: int,
    current_user: UserModel = Depends(require_roles("candidate", "admin")),
    db: Session = Depends(get_db),
):
    cv = (
        db.query(CVModel)
        .filter(CVModel.id == cv_id, CVModel.user_id == current_user.id)
        .first()
    )
    if cv is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy CV")

    delete_cv_record(db, cv, CV_UPLOAD_DIR)
    return None
