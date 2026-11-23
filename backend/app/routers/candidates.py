import json
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pypdf import PdfReader
from sqlalchemy.orm import Session
from ..config import MAX_CV_BYTES, UPLOAD_DIR
from ..db import get_db
from ..deps import require_role
from ..models import Candidate, User
from ..schemas import CandidateOut, CandidateUpdate

router = APIRouter(prefix='/candidates', tags=['Candidates'])
candidate_only = require_role('CANDIDATE')

def candidate_profile(db: Session, user_id: int) -> Candidate:
    obj = db.get(Candidate, user_id)
    if obj is None:
        raise HTTPException(404, 'Không tìm thấy hồ sơ sinh viên')
    return obj

def candidate_json(candidate: Candidate) -> CandidateOut:
    try:
        skills = json.loads(candidate.skills) if candidate.skills else None
    except (ValueError, TypeError):
        skills = []
    return CandidateOut(candidate_id=candidate.candidate_id, full_name=candidate.full_name,
        phone=candidate.phone, university=candidate.university, major=candidate.major,
        skills=skills, bio=candidate.bio, has_cv=bool(candidate.cv_url))

@router.get('/me', response_model=CandidateOut)
def get_profile(user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    return candidate_json(candidate_profile(db, user.user_id))

@router.patch('/me', response_model=CandidateOut)
def update_profile(payload: CandidateUpdate, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    obj = candidate_profile(db, user.user_id)
    for name, value in payload.model_dump(exclude_unset=True).items():
        if name == 'full_name' and value is None:
            raise HTTPException(422, 'full_name không được rỗng')
        if name == 'skills':
            value = json.dumps([s.strip() for s in value if s.strip()], ensure_ascii=False) if value is not None else None
        setattr(obj, name, value)
    db.commit()
    return candidate_json(obj)

@router.post('/me/cv')
async def upload_cv(file: UploadFile = File(...), user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(422, 'Chỉ hỗ trợ file PDF')
    if file.content_type not in ('application/pdf', 'application/octet-stream'):
        raise HTTPException(422, 'MIME type không phải PDF')
    raw = await file.read(MAX_CV_BYTES + 1)
    await file.close()
    if len(raw) > MAX_CV_BYTES:
        raise HTTPException(413, 'Dung lượng CV vượt quá giới hạn')
    if not raw.startswith(b'%PDF-'):
        raise HTTPException(422, 'Nội dung không phải PDF hợp lệ')
    try:
        reader = PdfReader(BytesIO(raw))
        if reader.is_encrypted:
            raise HTTPException(422, 'Không hỗ trợ PDF có mật khẩu')
        if len(reader.pages) > 30:
            raise HTTPException(422, 'CV vượt quá 30 trang')
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(422, 'Không thể đọc file PDF')
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f'{uuid4().hex}.pdf'
    filepath = UPLOAD_DIR / filename
    filepath.write_bytes(raw)
    candidate = candidate_profile(db, user.user_id)
    previous = candidate.cv_url
    candidate.cv_url = filename
    db.commit()
    if previous and previous != filename:
        (UPLOAD_DIR / Path(previous).name).unlink(missing_ok=True)
    return {'message': 'Tải CV thành công', 'has_cv': True}

@router.get('/me/cv')
def download_cv(user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    candidate = candidate_profile(db, user.user_id)
    if not candidate.cv_url:
        raise HTTPException(404, 'Chưa có CV')
    filepath = UPLOAD_DIR / Path(candidate.cv_url).name
    if not filepath.is_file():
        raise HTTPException(404, 'Không tìm thấy file CV')
    return FileResponse(filepath, media_type='application/pdf', filename='my_cv.pdf')
