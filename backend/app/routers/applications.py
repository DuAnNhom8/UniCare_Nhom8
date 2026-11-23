import json
from datetime import date
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..config import UPLOAD_DIR
from ..db import get_db
from ..deps import require_role
from ..models import Application, Candidate, JobPost, User
from ..schemas import ApplicationOut, ApplyIn, CandidateApplicationOut, EmployerApplicationDetailOut, EmployerApplicationOut, UpdateApplicationStatus
from .companies import own_company

candidate_router = APIRouter(prefix='/applications', tags=['Applications'])
employer_router = APIRouter(prefix='/employer', tags=['Employer applications'])
candidate_only = require_role('CANDIDATE')
employer_only = require_role('EMPLOYER')


def stored_ai(application: Application):
    if application.ai_match_score is None or not application.ai_feedback:
        return None
    try:
        value = json.loads(application.ai_feedback)
        if isinstance(value, dict) and {'matched_skills', 'missing_skills', 'suggestions'} <= value.keys():
            return {
                'score': application.ai_match_score,
                'matched_skills': value['matched_skills'],
                'missing_skills': value['missing_skills'],
                'suggestions': value['suggestions'],
                'method': value.get('method', 'legacy'),
                'analyzed_at': value.get('analyzed_at'),
            }
    except (ValueError, TypeError):
        pass
    return {
        'score': application.ai_match_score,
        'matched_skills': [],
        'missing_skills': [],
        'suggestions': [application.ai_feedback],
        'method': 'legacy',
        'analyzed_at': None,
    }


def candidate_application_json(application: Application, job_title: str) -> CandidateApplicationOut:
    return CandidateApplicationOut(
        application_id=application.application_id, job_id=application.job_id,
        candidate_id=application.candidate_id, status=application.status,
        applied_at=application.applied_at, job_title=job_title, ai_result=stored_ai(application),
    )


@candidate_router.post('', response_model=ApplicationOut, status_code=201)
def apply(data: ApplyIn, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    job = db.get(JobPost, data.job_id)
    if not job or job.status != 'ACTIVE' or job.deadline < date.today():
        raise HTTPException(422, 'Chỉ có thể ứng tuyển vào tin đang hoạt động và còn hạn')
    if db.scalar(select(Application).where(Application.job_id == data.job_id, Application.candidate_id == user.user_id)):
        raise HTTPException(409, 'Bạn đã ứng tuyển vào tin này')
    application = Application(job_id=data.job_id, candidate_id=user.user_id, status='RECEIVED')
    db.add(application)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Bạn đã ứng tuyển vào tin này')
    db.refresh(application)
    return application


@candidate_router.get('/me', response_model=list[CandidateApplicationOut])
def my_applications(user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Application, JobPost.title)
        .join(JobPost, Application.job_id == JobPost.job_id)
        .where(Application.candidate_id == user.user_id)
        .order_by(Application.applied_at.desc())
    ).all()
    return [candidate_application_json(application, title) for application, title in rows]


def get_owned_application(db: Session, employer_id: int, application_id: int):
    company = own_company(db, employer_id)
    stmt = select(Application).join(JobPost, Application.job_id == JobPost.job_id).where(
        Application.application_id == application_id, JobPost.company_id == company.company_id)
    application = db.scalar(stmt)
    if not application:
        raise HTTPException(404, 'Không tìm thấy đơn ứng tuyển thuộc công ty')
    return application


@employer_router.get('/jobs/{job_id}/applications', response_model=list[EmployerApplicationOut])
def job_applications(job_id: int, user: User = Depends(employer_only), db: Session = Depends(get_db)):
    company = own_company(db, user.user_id)
    job = db.get(JobPost, job_id)
    if not job or job.company_id != company.company_id:
        raise HTTPException(404, 'Không tìm thấy tin thuộc công ty')
    stmt = select(Application, Candidate).join(Candidate, Candidate.candidate_id == Application.candidate_id).where(
        Application.job_id == job_id).order_by(Application.applied_at.desc())
    return [EmployerApplicationOut(
        application_id=app.application_id, job_id=app.job_id,
        candidate_id=app.candidate_id, status=app.status, applied_at=app.applied_at,
        candidate_name=candidate.full_name, has_cv=bool(candidate.cv_url),
    ) for app, candidate in db.execute(stmt)]


@employer_router.get('/applications/{application_id}', response_model=EmployerApplicationDetailOut)
def application_detail(application_id: int, user: User = Depends(employer_only), db: Session = Depends(get_db)):
    application = get_owned_application(db, user.user_id, application_id)
    candidate = db.get(Candidate, application.candidate_id)
    account = db.get(User, application.candidate_id)
    job = db.get(JobPost, application.job_id)
    try:
        skills = json.loads(candidate.skills) if candidate.skills else []
        if not isinstance(skills, list):
            skills = []
    except (ValueError, TypeError):
        skills = []
    return EmployerApplicationDetailOut(
        application_id=application.application_id, job_id=application.job_id,
        candidate_id=application.candidate_id, status=application.status,
        applied_at=application.applied_at, candidate_name=candidate.full_name,
        candidate_email=account.email, phone=candidate.phone, university=candidate.university,
        major=candidate.major, skills=skills, bio=candidate.bio, has_cv=bool(candidate.cv_url),
        job_title=job.title,
    )


@employer_router.patch('/applications/{application_id}/status', response_model=ApplicationOut)
def update_application_status(application_id: int, data: UpdateApplicationStatus,
                              user: User = Depends(employer_only), db: Session = Depends(get_db)):
    application = get_owned_application(db, user.user_id, application_id)
    application.status = data.status
    db.commit()
    db.refresh(application)
    return application


@employer_router.get('/applications/{application_id}/cv')
def view_candidate_cv(application_id: int, user: User = Depends(employer_only), db: Session = Depends(get_db)):
    application = get_owned_application(db, user.user_id, application_id)
    candidate = db.get(Candidate, application.candidate_id)
    if not candidate or not candidate.cv_url:
        raise HTTPException(404, 'Ứng viên chưa có CV')
    path = UPLOAD_DIR / Path(candidate.cv_url).name
    if not path.is_file():
        raise HTTPException(404, 'Không tìm thấy file CV')
    return FileResponse(path, filename=f'candidate_{candidate.candidate_id}_cv.pdf', media_type='application/pdf')
