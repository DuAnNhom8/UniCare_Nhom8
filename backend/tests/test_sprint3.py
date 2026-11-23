import os
from datetime import date, timedelta
from io import BytesIO

os.environ.setdefault('DATABASE_URL', 'sqlite://')
os.environ.setdefault('JWT_SECRET', 'abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJK')
os.environ.setdefault('AI_PROVIDER', 'rules')

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import Application, User
from app.routers import admin, ai, applications, auth, candidates
from app.schemas import AIResult


@pytest.fixture
def env(monkeypatch, tmp_path):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    @event.listens_for(engine, 'connect')
    def enable_fks(connection, record):
        connection.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    def session_dependency():
        with session_factory() as db:
            yield db
    app.dependency_overrides[get_db] = session_dependency
    monkeypatch.setattr(auth, 'hash_password', lambda password: 'test-only:'+password)
    monkeypatch.setattr(auth, 'verify_password', lambda password, saved: saved == 'test-only:'+password)
    monkeypatch.setattr(ai, 'AI_PROVIDER', 'rules')
    monkeypatch.setattr(ai, 'UPLOAD_DIR', tmp_path)
    monkeypatch.setattr(candidates, 'UPLOAD_DIR', tmp_path)
    monkeypatch.setattr(applications, 'UPLOAD_DIR', tmp_path)
    audit_events = []
    monkeypatch.setattr(admin, 'audit_action', lambda *values: audit_events.append(values))
    with TestClient(app) as client:
        def register(email, role, field, value):
            result = client.post('/auth/register', json={'email': email, 'password': 'safe-password-123', 'role': role, field: value})
            assert result.status_code == 201, result.text
            return result.json()['user_id']
        candidate_id = register('candidate@example.com', 'CANDIDATE', 'full_name', 'Ứng viên 1')
        other_candidate_id = register('othercandidate@example.com', 'CANDIDATE', 'full_name', 'Ứng viên 2')
        employer_id = register('employer@example.com', 'EMPLOYER', 'company_name', 'Công ty Alpha')
        other_employer_id = register('otheremployer@example.com', 'EMPLOYER', 'company_name', 'Công ty Beta')
        with session_factory() as db:
            admin_user = User(email='admin@example.com', password_hash='test-only:safe-password-123', role='ADMIN', is_active=True)
            db.add(admin_user)
            db.commit()
            admin_id = admin_user.user_id
        def headers(email):
            token = client.post('/auth/login', data={'username': email, 'password': 'safe-password-123'})
            assert token.status_code == 200, token.text
            return {'Authorization': 'Bearer '+token.json()['access_token']}
        h = {
            'candidate': headers('candidate@example.com'),
            'other_candidate': headers('othercandidate@example.com'),
            'employer': headers('employer@example.com'),
            'other_employer': headers('otheremployer@example.com'),
            'admin': headers('admin@example.com'),
        }
        job = client.post('/employer/jobs', headers=h['employer'], json={
            'title': 'Thực tập Python FastAPI',
            'description': 'Thiết kế và phát triển REST API bằng Python',
            'requirements': 'Python, FastAPI, MySQL, Git, Docker',
            'location': 'TP.HCM',
            'deadline': str(date.today() + timedelta(days=20)),
        })
        assert job.status_code == 201, job.text
        job_id = job.json()['job_id']
        application = client.post('/applications', headers=h['candidate'], json={'job_id': job_id})
        assert application.status_code == 201, application.text
        yield {
            'client':client, 'h':h, 'job_id':job_id,
            'app_id':application.json()['application_id'],
            'candidate_id':candidate_id, 'other_candidate_id':other_candidate_id,
            'employer_id':employer_id, 'other_employer_id':other_employer_id,
            'admin_id':admin_id, 'factory':session_factory,
            'audit_events':audit_events,
        }
    app.dependency_overrides.clear()
    engine.dispose()


def test_admin_manage_users_and_overview(env):
    c,h=env['client'],env['h']
    for role in ('candidate','employer','other_employer'):
        assert c.get('/admin/overview', headers=h[role]).status_code == 403
    summary=c.get('/admin/overview',headers=h['admin'])
    assert summary.status_code==200
    assert summary.json()['users_total']==5
    assert summary.json()['candidate_total']==2
    assert summary.json()['employer_total']==2
    assert summary.json()['applications_total']==1
    search=c.get('/admin/users',headers=h['admin'],params={'keyword':'otheremployer','role':'EMPLOYER'})
    assert search.status_code==200 and len(search.json())==1
    assert c.patch(f"/admin/users/{env['admin_id']}/status",headers=h['admin'],json={'is_active':False}).status_code==403
    banned=c.patch(f"/admin/users/{env['candidate_id']}/status",headers=h['admin'],json={'is_active':False})
    assert banned.status_code==200 and banned.json()['is_active'] is False
    assert c.get('/applications/me',headers=h['candidate']).status_code==403
    reopened=c.patch(f"/admin/users/{env['candidate_id']}/status",headers=h['admin'],json={'is_active':True})
    assert reopened.status_code==200
    assert c.get('/applications/me',headers=h['candidate']).status_code==200
    assert len(env['audit_events'])==2


def test_employer_candidate_profile_and_isolation(env):
    c,h,app_id=env['client'],env['h'],env['app_id']
    assert c.patch('/candidates/me',headers=h['candidate'],json={
        'phone':'0123456789','university':'PTIT','major':'Kỹ thuật phần mềm',
        'skills':['Python','FastAPI'],'bio':'Đã tham gia dự án quản lý thư viện',
    }).status_code==200
    ok=c.get(f'/employer/applications/{app_id}',headers=h['employer'])
    assert ok.status_code==200,ok.text
    obj=ok.json()
    assert obj['candidate_name']=='Ứng viên 1'
    assert obj['candidate_email']=='candidate@example.com'
    assert obj['major']=='Kỹ thuật phần mềm'
    assert obj['skills']==['Python','FastAPI']
    assert obj['job_title']=='Thực tập Python FastAPI'
    assert 'ai_match_score' not in obj
    assert c.get(f'/employer/applications/{app_id}',headers=h['other_employer']).status_code==404
    assert c.get(f'/employer/applications/{app_id}',headers=h['candidate']).status_code==403
    assert c.get(f'/employer/applications/{app_id}',headers=h['admin']).status_code==403
    assert c.get(f"/employer/jobs/{env['job_id']}/applications",headers=h['other_employer']).status_code==404


def test_cv_upload_and_protected_download(env):
    c,h,app_id=env['client'],env['h'],env['app_id']
    writer=PdfWriter();writer.add_blank_page(width=600,height=800)
    stream=BytesIO();writer.write(stream)
    uploaded=c.post('/candidates/me/cv',headers=h['candidate'],files={'file':('cv.pdf',stream.getvalue(),'application/pdf')})
    assert uploaded.status_code==200,uploaded.text
    profile=c.get(f'/employer/applications/{app_id}',headers=h['employer'])
    assert profile.json()['has_cv'] is True
    assert c.get(f'/employer/applications/{app_id}/cv',headers=h['employer']).status_code==200
    assert c.get(f'/employer/applications/{app_id}/cv',headers=h['other_employer']).status_code==404
    assert c.get(f'/employer/applications/{app_id}/cv',headers=h['candidate']).status_code==403
    assert c.post('/candidates/me/cv',headers=h['candidate'],files={'file':('fake.pdf',b'not pdf','application/pdf')}).status_code==422
    assert c.post('/ai/analyze',headers=h['candidate'],json={'job_id':env['job_id']}).status_code==422


def test_change_application_status_and_candidate_sees_update(env):
    c,h,app_id=env['client'],env['h'],env['app_id']
    assert c.patch(f'/employer/applications/{app_id}/status',headers=h['other_employer'],json={'status':'MATCHED'}).status_code==404
    assert c.patch(f'/employer/applications/{app_id}/status',headers=h['candidate'],json={'status':'MATCHED'}).status_code==403
    assert c.patch(f'/employer/applications/{app_id}/status',headers=h['employer'],json={'status':'UNKNOWN'}).status_code==422
    for status in ['REVIEWING','MATCHED','REJECTED']:
        update=c.patch(f'/employer/applications/{app_id}/status',headers=h['employer'],json={'status':status})
        assert update.status_code==200 and update.json()['status']==status
        current=c.get('/applications/me',headers=h['candidate']).json()[0]
        assert current['status']==status
        assert current['job_title']=='Thực tập Python FastAPI'


def test_ai_preview_save_retrieve_and_privacy(env):
    c,h,job_id=env['client'],env['h'],env['job_id']
    text='Tôi đã làm dự án REST API bằng Python FastAPI MySQL và sử dụng Git để quản lý mã nguồn.'
    request={'job_id':job_id,'cv_text':text}
    preview=c.post('/ai/analyze',headers=h['candidate'],json=request)
    assert preview.status_code==200,preview.text
    assert preview.json()['saved_to_application'] is False
    assert preview.json()['method']=='keyword_demo'
    assert 0<=preview.json()['score']<=100
    assert c.get('/applications/me',headers=h['candidate']).json()[0]['ai_result'] is None
    assert c.post('/ai/analyze',headers=h['other_candidate'],json={**request,'save_to_application':True}).status_code==409
    result=c.post('/ai/analyze',headers=h['candidate'],json={**request,'save_to_application':True})
    assert result.status_code==200,result.text
    assert result.json()['saved_to_application'] is True
    data=c.get('/applications/me',headers=h['candidate']).json()[0]
    assert data['ai_result']['score']==result.json()['score']
    assert data['ai_result']['method']=='keyword_demo'
    assert data['ai_result']['analyzed_at']
    assert data['status']=='RECEIVED'
    assert c.get('/applications/me',headers=h['other_candidate']).json()==[]
    assert 'ai_result' not in c.get(f'/employer/applications/{env["app_id"]}',headers=h['employer']).json()


def test_ai_real_provider_consent_and_mocked_inference(env,monkeypatch):
    c,h=env['client'],env['h']
    monkeypatch.setattr(ai,'AI_PROVIDER','openai')
    invoked=[]
    def fake_analysis(cv,job):
        invoked.append((cv,job))
        return AIResult(score=70,matched_skills=['python'],missing_skills=['docker'],suggestions=['Bổ sung minh chứng Docker']), 'openai'
    monkeypatch.setattr(ai,'analyze',fake_analysis)
    payload={'job_id':env['job_id'],'cv_text':'Tôi có kinh nghiệm Python và đã phát triển REST API.'}
    declined=c.post('/ai/analyze',headers=h['candidate'],json=payload)
    assert declined.status_code==422
    assert invoked==[]
    approved=c.post('/ai/analyze',headers=h['candidate'],json={**payload,'consent_to_external_processing':True,'save_to_application':True})
    assert approved.status_code==200,approved.text
    assert approved.json()['method']=='openai'
    assert len(invoked)==1
    assert c.get('/applications/me',headers=h['candidate']).json()[0]['ai_result']['method']=='openai'


def test_admin_moderation_and_employer_cannot_unhide(env):
    c,h,job_id=env['client'],env['h'],env['job_id']
    assert c.patch(f'/admin/jobs/{job_id}/moderate',headers=h['employer'],json={'status':'HIDDEN'}).status_code==403
    hidden=c.patch(f'/admin/jobs/{job_id}/moderate',headers=h['admin'],json={'status':'HIDDEN'})
    assert hidden.status_code==200
    assert c.get('/jobs').json()==[]
    assert c.patch(f'/employer/jobs/{job_id}',headers=h['employer'],json={'status':'ACTIVE'}).status_code==403
    assert c.post('/applications',headers=h['other_candidate'],json={'job_id':job_id}).status_code==422
    assert c.get('/admin/jobs',headers=h['admin'],params={'status':'HIDDEN','keyword':'Python'}).json()[0]['job_id']==job_id
    restored=c.patch(f'/admin/jobs/{job_id}/moderate',headers=h['admin'],json={'status':'ACTIVE'})
    assert restored.status_code==200
    assert c.get('/jobs').json()[0]['job_id']==job_id
    assert len(env['audit_events'])==2


def test_database_uniques_and_ai_score_constraint(env):
    with env['factory']() as db:
        existing=db.scalar(select(Application))
        db.add(Application(job_id=existing.job_id,candidate_id=existing.candidate_id,status='RECEIVED'))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        existing=db.scalar(select(Application))
        existing.ai_match_score=101
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        existing=db.scalar(select(Application))
        existing.ai_match_score=-1
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_employer_job_management(env):
    c,h,job_id=env['client'],env['h'],env['job_id']
    assert c.get('/companies/me',headers=h['employer']).json()['company_name']=='Công ty Alpha'
    assert c.patch('/companies/me',headers=h['employer'],json={'company_name':'Alpha Updated'}).status_code==200
    assert c.patch(f'/employer/jobs/{job_id}',headers=h['other_employer'],json={'title':'Khác'}).status_code==404
    assert c.patch(f'/employer/jobs/{job_id}',headers=h['employer'],json={'status':'CLOSED'}).status_code==200
    assert c.get('/jobs').json()==[]
    assert c.patch(f'/employer/jobs/{job_id}',headers=h['employer'],json={'status':'ACTIVE'}).status_code==200
    assert c.get('/jobs').json()[0]['status']=='ACTIVE'


def test_static_pages_and_unauthorized_api(env):
    c=env['client']
    for path in ['/static/index.html','/static/admin.html','/static/ai.html','/static/employer.html','/static/admin.js','/static/employer.js']:
        assert c.get(path).status_code==200
    assert c.get('/employer/jobs').status_code==401
    assert c.get('/admin/users').status_code==401
    assert c.get('/applications/me').status_code==401
