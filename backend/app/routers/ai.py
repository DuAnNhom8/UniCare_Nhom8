import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..config import AI_PROVIDER, UPLOAD_DIR
from ..db import get_db
from ..deps import require_role
from ..models import Application, Candidate, JobPost, User
from ..schemas import AIAnalyzeIn, AIAnalyzeOut
from ..services.ai import analyze

router = APIRouter(prefix='/ai', tags=['AI candidate support'])
candidate_only = require_role('CANDIDATE')


def own_cv_text(candidate: Candidate) -> str:
    if not candidate.cv_url:
        raise HTTPException(422, 'Chưa có CV; hãy tải PDF lên hoặc nhập cv_text')
    path = UPLOAD_DIR / Path(candidate.cv_url).name
    if not path.is_file():
        raise HTTPException(404, 'File CV không tồn tại')
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            raise HTTPException(422, 'Không hỗ trợ PDF có mật khẩu')
        pages = [page.extract_text() or '' for page in reader.pages[:15]]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(422, 'Không thể trích xuất nội dung CV')
    cv_text = '\n'.join(pages).strip()[:12000]
    if not cv_text:
        raise HTTPException(422, 'PDF không có văn bản đọc được. Hãy nhập cv_text thủ công')
    return cv_text


@router.post('/analyze', response_model=AIAnalyzeOut)
def analyze_cv(data: AIAnalyzeIn, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    job = db.get(JobPost, data.job_id)
    if job is None or job.status != 'ACTIVE':
        raise HTTPException(404, 'Không tìm thấy tin tuyển dụng đang hoạt động')
    if AI_PROVIDER == 'openai' and not data.consent_to_external_processing:
        raise HTTPException(422, 'Vui lòng đồng ý gửi nội dung CV đến dịch vụ AI bên ngoài trước khi phân tích')
    candidate = db.get(Candidate, user.user_id)
    if candidate is None:
        raise HTTPException(404, 'Không tìm thấy hồ sơ Candidate')
    application = None
    if data.save_to_application:
        application = db.scalar(select(Application).where(
            Application.job_id == data.job_id, Application.candidate_id == user.user_id))
        if application is None:
            raise HTTPException(409, 'Bạn cần ứng tuyển vào tin này trước khi lưu kết quả AI vào đơn')
    cv_text = (data.cv_text or '').strip() or own_cv_text(candidate)
    if len(cv_text) < 30:
        raise HTTPException(422, 'Nội dung CV quá ngắn để đối chiếu')
    job_text = f'Vị trí: {job.title}\nMô tả: {job.description}\nYêu cầu: {job.requirements}'
    result, method = analyze(cv_text[:12000], job_text)
    if application is not None:
        application.ai_match_score = result.score
        application.ai_feedback = json.dumps({
            **result.model_dump(),
            'method': method,
            'analyzed_at': datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False)
        db.commit()
    return AIAnalyzeOut(**result.model_dump(), method=method, saved_to_application=application is not None)
