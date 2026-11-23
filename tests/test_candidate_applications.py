"""E2E API Sprint 3: auth, CV, check trùng, nộp đơn và lịch sử riêng tư.
Chạy với SQLite tạm; không thay đổi MySQL thực tế.
"""
import io
import os
import tempfile
from pathlib import Path

_test_dir = tempfile.TemporaryDirectory(prefix='unicareer-apps-')
os.environ['DATABASE_URL'] = f"sqlite:///{Path(_test_dir.name) / 'tests.sqlite3'}"
os.environ['CV_STORAGE_DIR'] = str(Path(_test_dir.name) / 'private-cvs')
os.environ['JWT_SECRET_KEY'] = 'unit-test-secret-key-not-valid-for-production-1111111111'

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models import Application, User, JobPost


@pytest.fixture(scope='module')
def client():
    with TestClient(app) as c:
        yield c


def headers(token):
    return {'Authorization': f'Bearer {token}'}


def register_and_login(client, email, role='CANDIDATE'):
    r = client.post('/api/auth/register', json={'email': email, 'password': 'GreatPassword123!', 'role': role})
    assert r.status_code == 201, r.text
    login = client.post('/api/auth/login', json={'email': email, 'password': 'GreatPassword123!'})
    assert login.status_code == 200, login.text
    return login.json()['access_token']


def upload(client, token):
    return client.post('/api/candidate/cvs', headers=headers(token),
                       files={'file': ('cv-test.pdf', b'%PDF-1.4\n%%EOF', 'application/pdf')})


def test_application_end_to_end_with_isolation_and_duplicate(client):
    candidate1 = register_and_login(client, 'sprint3_candidate_01@example.test')
    candidate2 = register_and_login(client, 'sprint3_candidate_02@example.test')
    employer = register_and_login(client, 'sprint3_employer_01@example.test', role='EMPLOYER')
    try:
        public = client.get('/api/jobs/public').json()
        assert public['total'] >= 1
        job_id = public['items'][0]['job_id']

        assert client.get('/api/candidate/applications').status_code == 401
        assert client.get('/api/candidate/applications', headers=headers('invalid')).status_code == 401
        assert client.get('/api/candidate/applications', headers=headers(employer)).status_code == 403
        assert client.get('/api/auth/me', headers=headers(candidate1)).json()['role'] == 'CANDIDATE'

        cv_result = upload(client, candidate1)
        assert cv_result.status_code == 201, cv_result.text
        cv_id = cv_result.json()['cv_id']
        assert cv_result.json()['title'] == 'cv-test.pdf'
        assert 'file_path' not in cv_result.json()
        assert len(client.get('/api/candidate/cvs', headers=headers(candidate1)).json()) == 1
        assert client.get('/api/candidate/cvs', headers=headers(candidate2)).json() == []
        assert client.get(f'/api/candidate/cvs/{cv_id}/download', headers=headers(candidate1)).content.startswith(b'%PDF-')
        assert client.get(f'/api/candidate/cvs/{cv_id}/download', headers=headers(candidate2)).status_code == 404

        pre = client.get(f'/api/candidate/applications/check/{job_id}', headers=headers(candidate1))
        assert pre.status_code == 200 and not pre.json()['applied']
        payload = {'job_id': job_id, 'cv_id': cv_id, 'cover_letter': 'Tôi yêu thích vị trí này.'}
        apply = client.post('/api/candidate/applications', json=payload, headers=headers(candidate1))
        assert apply.status_code == 201, apply.text
        assert apply.json()['candidate_id'] > 0
        assert apply.json()['job_title'] == public['items'][0]['title']
        assert apply.json()['cv_title'] == 'cv-test.pdf'

        assert client.get(f'/api/candidate/applications/check/{job_id}', headers=headers(candidate1)).json()['applied']
        duplicate = client.post('/api/candidate/applications', json=payload, headers=headers(candidate1))
        assert duplicate.status_code == 409
        assert 'đã ứng tuyển' in duplicate.json()['detail']
        own_list = client.get('/api/candidate/applications', headers=headers(candidate1)).json()
        assert own_list['total'] == 1 and own_list['items'][0]['job_id'] == job_id
        assert client.get('/api/candidate/applications?skip=10', headers=headers(candidate1)).json()['items'] == []
        assert client.get('/api/candidate/applications', headers=headers(candidate2)).json()['total'] == 0
        assert client.post('/api/candidate/applications', json=payload, headers=headers(candidate2)).status_code == 404
        assert client.post('/api/candidate/applications', json=payload, headers=headers(employer)).status_code == 403
    finally:
        db = SessionLocal()
        try:
            for email in ['sprint3_candidate_01@example.test', 'sprint3_candidate_02@example.test', 'sprint3_employer_01@example.test']:
                user = db.query(User).filter(User.email == email).first()
                if user: db.delete(user)
            db.commit()
        finally: db.close()


def test_upload_validation_bad_file_and_expired_jobs(client):
    token = register_and_login(client, 'sprint3_candidate_03@example.test')
    try:
        bad = client.post('/api/candidate/cvs', headers=headers(token),
                          files={'file': ('cv.pdf', b'not a pdf', 'application/pdf')})
        assert bad.status_code == 400
        bad = client.post('/api/candidate/cvs', headers=headers(token),
                          files={'file': ('cv.exe', b'%PDF-1.4', 'application/pdf')})
        assert bad.status_code == 400
        large = client.post('/api/candidate/cvs', headers=headers(token),
                            files={'file': ('cv.pdf', b'%PDF-' + b'Z' * (5 * 1024 * 1024), 'application/pdf')})
        assert large.status_code == 413
        assert client.get('/api/candidate/cvs', headers=headers(token)).json() == []
        assert client.post('/api/candidate/applications', json={'job_id': 123456789, 'cv_id': 1}, headers=headers(token)).status_code == 404
    finally:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == 'sprint3_candidate_03@example.test').first()
            if user: db.delete(user)
            db.commit()
        finally: db.close()


def test_auth_rejects_duplicate_email_and_unauthorized_admin_registration(client):
    registration = {'email': 'sprint3_temporary@example.test', 'password': 'AnotherGoodPassword123', 'role': 'CANDIDATE'}
    first = client.post('/api/auth/register', json=registration)
    assert first.status_code == 201, first.text
    try:
        assert client.post('/api/auth/register', json=registration).status_code == 409
        assert client.post('/api/auth/login', json={'email': registration['email'], 'password': 'bad password'}).status_code == 401
        assert client.post('/api/auth/register', json={**registration, 'email': 'sprint3_admin@example.test', 'role': 'ADMIN'}).status_code == 422
        assert client.post('/api/auth/register', json={**registration, 'email': 'sprint3_bad@example.test', 'password': '123'}).status_code == 422
    finally:
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(email=registration['email']).first()
            if user: db.delete(user)
            db.commit()
        finally: db.close()


def test_frontend_application_pages_connected(client):
    for page, marker in [('apply-job.html', 'application-form'), ('my-applications.html', 'application-history'), ('cv-manage.html', 'cv-upload-form')]:
        response = client.get(f'/frontend/pages/candidate/{page}')
        assert response.status_code == 200
        assert f'id="{marker}"' in response.text
        assert 'assets/js/candidate.js' in response.text
