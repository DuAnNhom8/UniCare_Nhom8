import secrets
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import CV_STORAGE_DIR
from app.core.database import get_db
from app.core.security import require_roles
from app.models.ai import CVAIConsentModel
from app.models.application import ApplicationModel
from app.models.company import CompanyModel
from app.models.cv import CVModel
from app.models.job import JobModel
from app.models.user import UserModel
from app.schemas.application import ApplicationCheck, ApplicationCreate, ApplicationDetail, ApplicationList
from app.schemas.cv import CVBuilderCreate, CVBuilderUpdate, CVResponse
from app.schemas.user import CVAIConsentUpdate
from app.services import apply_service, company_service
from app.services.cv_service import (
    ALLOWED_CV_EXTENSIONS,
    MAX_CV_SIZE,
    cv_payload,
    delete_cv_record,
    render_cv_html,
)


router = APIRouter(prefix="/candidate", tags=["Ứng viên & Ứng tuyển"])
CV_DIR = CV_STORAGE_DIR


@router.get("/cvs", response_model=list[CVResponse])
def list_cvs(
    current_user: UserModel = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    cvs = (
        db.query(CVModel)
        .filter(CVModel.user_id == current_user.id)
        .order_by(CVModel.updated_at.desc(), CVModel.id.desc())
        .all()
    )
    return [cv_payload(cv) for cv in cvs]


@router.post("/cvs/upload", response_model=CVResponse, status_code=201)
async def upload_cv(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    original_name = Path((file.filename or "").replace("\\", "/")).name
    suffix = Path(original_name).suffix.lower()
    if not original_name or len(original_name) > 255 or suffix not in ALLOWED_CV_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail="Chỉ hỗ trợ CV PDF hoặc DOCX, tên tệp tối đa 255 ký tự",
        )

    CV_DIR.mkdir(parents=True, exist_ok=True)
    stored_path = CV_DIR / f"{secrets.token_hex(16)}{suffix}"
    persisted = False
    try:
        size = 0
        signature = bytearray()
        with stored_path.open("xb") as destination:
            while chunk := await file.read(64 * 1024):
                size += len(chunk)
                if size > MAX_CV_SIZE:
                    raise HTTPException(status_code=413, detail="CV vượt quá giới hạn 10 MB")
                if len(signature) < 8:
                    signature.extend(chunk[: 8 - len(signature)])
                destination.write(chunk)

        if size == 0:
            raise HTTPException(status_code=422, detail="Tệp CV không được để trống")
        if suffix == ".pdf" and not signature.startswith(b"%PDF-"):
            raise HTTPException(status_code=422, detail="Tệp không có định dạng PDF hợp lệ")
        if suffix == ".docx":
            try:
                with zipfile.ZipFile(stored_path) as archive:
                    archive.getinfo("word/document.xml")
            except (zipfile.BadZipFile, KeyError, OSError) as error:
                raise HTTPException(
                    status_code=422,
                    detail="Tệp không có định dạng DOCX hợp lệ",
                ) from error

        cv = CVModel(
            user_id=current_user.id,
            file_name=original_name,
            file_url=stored_path.name,
            cv_type="upload",
        )
        db.add(cv)
        try:
            db.commit()
            db.refresh(cv)
        except SQLAlchemyError as error:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Không thể lưu CV đã tải lên",
            ) from error
        persisted = True
        return cv_payload(cv)
    finally:
        try:
            await file.close()
        finally:
            if not persisted:
                stored_path.unlink(missing_ok=True)


@router.put("/cvs/{cv_id}/ai-consent", response_model=CVResponse)
def update_cv_ai_consent(
    cv_id: int,
    request: CVAIConsentUpdate,
    current_user: UserModel = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    cv = (
        db.query(CVModel)
        .filter(CVModel.id == cv_id, CVModel.user_id == current_user.id)
        .first()
    )
    if cv is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy CV")

    consent = cv.ai_consent
    if consent is None:
        consent = CVAIConsentModel(candidate_id=current_user.id)
        cv.ai_consent = consent
    consent.consented = request.allow_ai_analysis
    db.commit()
    db.refresh(cv)
    return cv_payload(cv)


@router.post("/cvs/builder", response_model=CVResponse, status_code=201)
def create_cv_from_template(
    request: CVBuilderCreate,
    current_user: UserModel = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    cv = CVModel(
        user_id=current_user.id,
        file_name=request.title.strip(),
        cv_type="builder",
        personal_info=request.personal_info.model_dump(mode="json"),
        content=request.content.model_dump(mode="json"),
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)
    return cv_payload(cv)


@router.put("/cvs/{cv_id}", response_model=CVResponse)
def update_cv_from_template(
    cv_id: int,
    request: CVBuilderUpdate,
    current_user: UserModel = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    cv = (
        db.query(CVModel)
        .filter(CVModel.id == cv_id, CVModel.user_id == current_user.id)
        .first()
    )
    if cv is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy CV")
    if cv.cv_type != "builder":
        raise HTTPException(status_code=409, detail="Chỉ có thể chỉnh sửa CV tạo từ mẫu")
    cv.file_name = request.title.strip()
    cv.personal_info = request.personal_info.model_dump(mode="json")
    cv.content = request.content.model_dump(mode="json")
    db.commit()
    db.refresh(cv)
    return cv_payload(cv)


@router.get("/cvs/{cv_id}/download")
def download_cv(
    cv_id: int,
    current_user: UserModel = Depends(require_roles("candidate", "employer", "admin")),
    db: Session = Depends(get_db),
):
    cv = db.query(CVModel).filter(CVModel.id == cv_id).first()
    if cv is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy CV")
    authorized = current_user.role.lower() == "admin" or cv.user_id == current_user.id
    if current_user.role.lower() == "employer":
        company = company_service.get_company_for_employer(db, current_user.id)
        authorized = bool(
            company
            and db.query(ApplicationModel.id)
            .join(JobModel, ApplicationModel.job_id == JobModel.id)
            .filter(
                ApplicationModel.cv_id == cv.id,
                JobModel.company_id == company.id,
            )
            .first()
        )
    if not authorized:
        raise HTTPException(status_code=404, detail="Không tìm thấy CV")
    if cv.cv_type == "builder":
        return Response(
            content=render_cv_html(cv),
            media_type="text/html; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="cv-{cv.id}.html"'},
        )
    stored_name = Path(cv.file_url or "").name
    if not stored_name or stored_name != cv.file_url or not (CV_DIR / stored_name).is_file():
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp CV")
    return FileResponse(CV_DIR / stored_name, filename=cv.file_name)


@router.delete("/cvs/{cv_id}", status_code=204)
def delete_cv(
    cv_id: int,
    current_user: UserModel = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    cv = (
        db.query(CVModel)
        .filter(CVModel.id == cv_id, CVModel.user_id == current_user.id)
        .first()
    )
    if cv is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy CV")
    delete_cv_record(db, cv, CV_DIR)
    return None


@router.get("/applications/check/{job_id}", response_model=ApplicationCheck)
def check_application(
    job_id: int,
    current_user: UserModel = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    application = apply_service.find_application(db, current_user.id, job_id)
    return {
        "applied": application is not None,
        "application_id": application.id if application else None,
    }


@router.post("/applications", response_model=ApplicationDetail, status_code=201)
def apply(
    data: ApplicationCreate,
    current_user: UserModel = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    application = apply_service.create_application(db, current_user.id, data)
    application = (
        db.query(ApplicationModel)
        .filter(ApplicationModel.id == application.id)
        .first()
    )
    return apply_service.application_payload(application)


@router.get("/applications", response_model=ApplicationList)
def list_my_applications(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: UserModel = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    return apply_service.list_candidate_applications(db, current_user.id, skip, limit)