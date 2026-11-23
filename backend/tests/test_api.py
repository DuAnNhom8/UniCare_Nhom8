import os
from datetime import date, timedelta
from pathlib import Path

os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(__file__).parent.parent / 'tests' / 'test.db')
os.environ['JWT_SECRET'] = 'abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJK'
os.environ['AI_PROVIDER'] = 'rules'

from fastapi.testclient import TestClient
from sqlalchemy import select
from app import models
from app.db import Base, SessionLocal, engine
from app.main import app
from app.routers import auth

client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    Path('tests/test.db').unlink(missing_ok=True)


def test_full_candidate_employer_admin_flow():
    original_hash = auth.hash_password
    original_verify = auth.verify_password
    auth.hash_password = lambda pwd: 'dev-only-test-hash:' + pwd
    auth.verify_password = lambda pwd, hashed: hashed == 'dev-only-test-hash:' + pwd
    try:
        candidate = client.post('/auth/register', json={
            'email': 'student@example.com', 'password': 'password999',
            'role': 'CANDIDATE', 'full_name': 'Sinh viên Demo'
        })
        assert candidate.status_code == 201, candidate.text
        employer = client.post('/auth/register', json={
            'email': 'employer@example.com', 'password': 'password999',
            'role': 'EMPLOYER', 'company_name': 'Công ty Demo'
        })
        assert employer.status_code == 201, employer.text
        assert client.post('/auth/register', json={
            'email': 'administrator@example.com', 'password': 'password999',
            'role': 'ADMIN', 'full_name': 'Admin'}).status_code == 422
        assert client.post('/auth/register', json={
            'email': 'student@example.com', 'password': 'password999',
            'role': 'CANDIDATE', 'full_name': 'Other'}).status_code == 409
        with SessionLocal() as db:
            admin = models.User(email='admin@example.com', password_hash='dev-only-test-hash:password999', role='ADMIN', is_active=True)
            db.add(admin)
            db.commit()
            admin_id = admin.user_id
        def login(email):
            r = client.post('/auth/login', data={'username': email, 'password': 'password999'})
            assert r.status_code == 200, r.text
            return {'Authorization': 'Bearer ' + r.json()['access_token']}
        student_h = login('student@example.com')
        employer_h = login('employer@example.com')
        admin_h = login('admin@example.com')
        assert client.get('/admin/users', headers=student_h).status_code == 403
        assert client.post('/employer/jobs', json={}, headers=student_h).status_code == 403
        response = client.patch('/candidates/me', headers=student_h, json={'skills': ['Python', 'FastAPI']})
        assert response.status_code == 200, response.text
        assert response.json()['skills'] == ['Python', 'FastAPI']
        job = client.post('/employer/jobs', headers=employer_h, json={
            'title': 'Thực tập Python FastAPI',
            'description': 'Xây dựng backend ứng dụng web và REST API',
            'requirements': 'Biết Python, FastAPI, MySQL và Git',
            'location': 'TP.HCM',
            'deadline': str(date.today() + timedelta(days=20))
        })
        assert job.status_code == 201, job.text
        job_id = job.json()['job_id']
        assert client.get('/jobs').json()[0]['job_id'] == job_id
        wrong = client.post('/applications', headers=employer_h, json={'job_id': job_id})
        assert wrong.status_code == 403
        applied = client.post('/applications', headers=student_h, json={'job_id': job_id})
        assert applied.status_code == 201, applied.text
        app_id = applied.json()['application_id']
        assert client.post('/applications', headers=student_h, json={'job_id': job_id}).status_code == 409
        preview = client.post('/ai/analyze', headers=student_h, json={
            'job_id': job_id,
            'cv_text': 'Tôi xây dựng ứng dụng bằng Python và FastAPI, sử dụng Git để quản lý mã nguồn.'
        })
        assert preview.status_code == 200, preview.text
        assert preview.json()['method'] == 'keyword_demo'
        assert preview.json()['saved_to_application'] is False
        assert 0 <= preview.json()['score'] <= 100
        save = client.post('/ai/analyze', headers=student_h, json={
            'job_id': job_id,
            'cv_text': 'Tôi xây dựng ứng dụng bằng Python và FastAPI, sử dụng Git để quản lý mã nguồn.',
            'save_to_application': True
        })
        assert save.status_code == 200, save.text
        assert save.json()['saved_to_application'] is True
        with SessionLocal() as db:
            row = db.get(models.Application, app_id)
            assert row.ai_feedback is not None
            assert row.ai_match_score == save.json()['score']
        update = client.patch(f'/employer/applications/{app_id}/status', headers=employer_h, json={'status': 'REVIEWING'})
        assert update.status_code == 200, update.text
        assert client.get('/applications/me', headers=student_h).json()[0]['status'] == 'REVIEWING'
        assert client.get(f'/employer/jobs/{job_id}/applications', headers=employer_h).json()[0]['candidate_name'] == 'Sinh viên Demo'
        assert client.patch(f'/admin/users/{admin_id}/status', headers=admin_h, json={'is_active': False}).status_code == 403
        user_id = candidate.json()['user_id']
        assert client.patch(f'/admin/users/{user_id}/status', headers=admin_h, json={'is_active': False}).status_code == 200
        assert client.get('/auth/me', headers=student_h).status_code == 403
        moderation = client.patch(f'/admin/jobs/{job_id}/moderate', headers=admin_h, json={'status': 'HIDDEN'})
        assert moderation.status_code == 200, moderation.text
        assert client.get('/jobs').json() == []
        assert client.patch(f'/employer/jobs/{job_id}', headers=employer_h, json={'status': 'ACTIVE'}).status_code == 403
    finally:
        auth.hash_password = original_hash
        auth.verify_password = original_verify


def test_unique_application_and_score_constraint():
    from sqlalchemy.exc import IntegrityError
    with SessionLocal() as db:
        users = db.scalars(select(models.User)).all()
        candidate = next(x for x in users if x.role == 'CANDIDATE')
        job = db.scalars(select(models.JobPost)).first()
        duplicate = models.Application(job_id=job.job_id, candidate_id=candidate.user_id)
        db.add(duplicate)
        try:
            db.commit()
            assert False, 'UNIQUE(job_id,candidate_id) phải chặn trùng'
        except IntegrityError:
            db.rollback()
        current = db.scalars(select(models.Application)).first()
        current.ai_match_score = 101
        try:
            db.commit()
            assert False, 'CHECK phải chặn điểm AI >100'
        except IntegrityError:
            db.rollback()
