"""API ứng viên: CV riêng tư, nộp đơn, kiểm tra trùng và lịch sử."""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import require_candidate
from backend.app.models import CV, User
from backend.app.schemas.application import (
    ApplicationCheck, ApplicationCreate, ApplicationDetail, ApplicationList, CVResponse,
)
from backend.app.services import apply_service

router = APIRouter(prefix='/candidate', tags=['Ứng viên & Ứng tuyển'])
MAX_CV_BYTES = 5 * 1024 * 1024
CV_DIR = Path(os.getenv('CV_STORAGE_DIR', str(Path(__file__).resolve().parents[2] / 'private_uploads'))).resolve()


@router.post('/cvs', response_model=CVResponse, status_code=201)
async def upload_cv(file: UploadFile = File(...), user: User = Depends(require_candidate), db: Session = Depends(get_db)):
    filename = (file.filename or '').replace('\\', '/').split('/')[-1]
    if not filename.lower().endswith('.pdf') or len(filename) > 150:
        raise HTTPException(status_code=400, detail='Chỉ chấp nhận CV .pdf với tên tệp tối đa 150 ký tự')
    # Không tin MIME hay tên file do trình duyệt cung cấp: kiểm tra signature và giới hạn dung lượng.
    signature = await file.read(5)
    if signature != b'%PDF-':
        raise HTTPException(status_code=400, detail='Tệp CV không đúng định dạng PDF')
    CV_DIR.mkdir(parents=True, exist_ok=True)
    saved_name = f'{uuid.uuid4().hex}.pdf'
    path = CV_DIR / saved_name
    try:
        with path.open('xb') as output:
            output.write(signature)
            size = len(signature)
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_CV_BYTES:
                    raise HTTPException(status_code=413, detail='CV phải nhỏ hơn hoặc bằng 5 MB')
                output.write(chunk)
        cv = CV(candidate_id=user.user_id, title=filename, file_path=saved_name)
        db.add(cv)
        db.commit()
        db.refresh(cv)
        return cv
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()


@router.get('/cvs', response_model=list[CVResponse])
def list_cvs(user: User = Depends(require_candidate), db: Session = Depends(get_db)):
    return db.query(CV).filter(CV.candidate_id == user.user_id).order_by(CV.created_at.desc(), CV.cv_id.desc()).all()


@router.get('/cvs/{cv_id}/download')
def download_cv(cv_id: int, user: User = Depends(require_candidate), db: Session = Depends(get_db)):
    cv = db.query(CV).filter_by(cv_id=cv_id, candidate_id=user.user_id).first()
    if not cv:
        raise HTTPException(status_code=404, detail='Không tìm thấy CV')
    # Các CV mới luôn có tên UUID; bác bỏ đường dẫn bất thường trong dữ liệu cũ.
    if not cv.file_path.endswith('.pdf') or Path(cv.file_path).name != cv.file_path:
        raise HTTPException(status_code=404, detail='Không tìm thấy tệp')
    path = CV_DIR / cv.file_path
    if not path.is_file() or path.is_symlink():
        raise HTTPException(status_code=404, detail='Không tìm thấy tệp')
    return FileResponse(path, media_type='application/pdf', filename=cv.title)


@router.get('/applications/check/{job_id}', response_model=ApplicationCheck)
def has_applied(job_id: int, user: User = Depends(require_candidate), db: Session = Depends(get_db)):
    application = apply_service.check_duplicate(db, user.user_id, job_id)
    return ApplicationCheck(applied=application is not None,
                            application_id=application.application_id if application else None)


@router.post('/applications', response_model=ApplicationDetail, status_code=201)
def apply(data: ApplicationCreate, user: User = Depends(require_candidate), db: Session = Depends(get_db)):
    record = apply_service.create_application(db, user.user_id, data)
    db.refresh(record, attribute_names=['job', 'cv'])
    return apply_service.application_to_detail(record)


@router.get('/applications', response_model=ApplicationList)
def my_applications(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
                    user: User = Depends(require_candidate), db: Session = Depends(get_db)):
    return apply_service.list_applications(db, user.user_id, skip, limit)
