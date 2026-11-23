"""Chạy bằng `python -m pytest -q` từ thư mục gốc dự án.
Dùng SQLite tạm cho kiểm thử; ứng dụng bình thường luôn kết nối MySQL.
"""
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

# Phải thiết lập trước khi import backend.app.main.
_test_directory = tempfile.TemporaryDirectory(prefix='unicareer-tests-')
os.environ['DATABASE_URL'] = f"sqlite:///{Path(_test_directory.name) / 'test.sqlite3'}"

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models import JobPost, Application, CV, User


@pytest.fixture(scope='module')
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_returns_only_open_approved_unexpired_jobs(client):
    initial = client.get('/api/jobs/public')
    assert initial.status_code == 200, initial.text
    data = initial.json()
    assert data['total'] == 4
    assert all(j['status'] == 'ACTIVE' and j['approval_status'] == 'APPROVED' for j in data['items'])
    assert all(j['company_name'] == 'TechNova' for j in data['items'])
    assert all(j['job_id'] > 0 for j in data['items'])

    db = SessionLocal()
    try:
        for title, approval, status, deadline in [
            ('Hidden job', 'APPROVED', 'HIDDEN', date.today() + timedelta(days=5)),
            ('Closed job', 'APPROVED', 'CLOSED', date.today() + timedelta(days=5)),
            ('Unapproved job', 'PENDING', 'ACTIVE', date.today() + timedelta(days=5)),
            ('Expired job', 'APPROVED', 'ACTIVE', date.today() - timedelta(days=1)),
        ]:
            db.add(JobPost(company_id=data['items'][0]['company_id'], title=title,
                           description='Mô tả thử nghiệm', requirements='Yêu cầu thử nghiệm',
                           job_type='INTERNSHIP', deadline=deadline,
                           status=status, approval_status=approval))
        db.commit()
        assert client.get('/api/jobs/public').json()['total'] == 4
        assert client.get('/api/jobs/public?keyword=Hidden').json()['total'] == 0
        for job in db.query(JobPost).filter(JobPost.title.in_([
            'Hidden job', 'Closed job', 'Unapproved job', 'Expired job'
        ])).all():
            assert client.get(f'/api/jobs/public/{job.job_id}').status_code == 404
    finally:
        db.query(JobPost).filter(JobPost.title.in_([
            'Hidden job', 'Closed job', 'Unapproved job', 'Expired job'
        ])).delete(synchronize_session=False)
        db.commit()
        db.close()


def test_keyword_location_type_and_salary_filters(client):
    backend = client.get('/api/jobs/public?keyword=backend').json()
    assert backend['total'] == 1
    assert backend['items'][0]['title'] == 'Backend Developer Intern'
    assert client.get('/api/jobs/public?keyword=technova').json()['total'] == 4
    assert client.get('/api/jobs/public?location=H%C3%A0%20N%E1%BB%99i').json()['total'] == 1
    assert client.get('/api/jobs/public?job_type=PART_TIME').json()['total'] == 0
    assert client.get('/api/jobs/public?job_type=INTERNSHIP').json()['total'] == 4
    assert client.get('/api/jobs/public?salary=paid').json()['total'] == 4
    assert client.get('/api/jobs/public?salary=negotiable').json()['total'] == 0


def test_detail_sort_pagination_and_invalid_inputs(client):
    result = client.get('/api/jobs/public?sort=deadline&limit=2&skip=0').json()
    result_next = client.get('/api/jobs/public?sort=deadline&limit=2&skip=2').json()
    assert result['total'] == 4 and result_next['total'] == 4
    assert len(result['items']) == 2 and len(result_next['items']) == 2
    assert result['items'][0]['deadline'] <= result['items'][1]['deadline']
    assert {job['job_id'] for job in result['items']}.isdisjoint(
        {job['job_id'] for job in result_next['items']})
    job_id = result['items'][0]['job_id']
    detail = client.get(f'/api/jobs/public/{job_id}')
    assert detail.status_code == 200
    assert detail.json()['job_id'] == job_id
    assert detail.json()['company_description']
    assert client.get('/api/jobs/public/999999').status_code == 404
    assert client.get('/api/jobs/public?job_type=INVALID').status_code == 422
    assert client.get('/api/jobs/public?limit=1000').status_code == 422
    assert client.get('/api/jobs/public?sort=INVALID').status_code == 422
    assert client.get("/api/jobs/public?keyword=%27%20OR%201%3D1%20--").json()['total'] == 0


def test_application_and_cv_models_have_relationships(client):
    """Bảo đảm 2 bảng mới được tạo và ràng buộc duy nhất hoạt động."""
    from sqlalchemy import inspect
    from backend.app.core.database import engine
    schema = inspect(engine)
    assert 'applications' in schema.get_table_names()
    assert 'cvs' in schema.get_table_names()
    assert {'candidate_id', 'job_id', 'cv_id'}.issubset(
        {column['name'] for column in schema.get_columns('applications')})
    unique_constraints = schema.get_unique_constraints('applications')
    assert any(set(row['column_names']) == {'candidate_id', 'job_id'} for row in unique_constraints)


def test_existing_company_api_does_not_break(client):
    response = client.get('/api/companies')
    assert response.status_code == 200
    assert response.json()[0]['company_name'] == 'TechNova'
    response = client.get('/api/jobs')
    assert response.status_code == 200
    assert len(response.json()) == 4


def test_cv_application_link_and_prevent_duplicate(client):
    from sqlalchemy.exc import IntegrityError

    db = SessionLocal()
    try:
        candidate = User(email='candidate_for_tests@example.test', password_hash='!not-for-login', role='CANDIDATE')
        db.add(candidate)
        db.flush()
        cv = CV(candidate_id=candidate.user_id, title='CV thực tập', file_path='private/cv-demo.pdf')
        db.add(cv)
        db.flush()
        job = db.query(JobPost).filter(JobPost.status == 'ACTIVE').first()
        db.add(Application(candidate_id=candidate.user_id, job_id=job.job_id,
                           cv_id=cv.cv_id, cover_letter='Thư ứng tuyển mẫu', status='PENDING'))
        db.commit()
        saved = db.query(Application).filter(Application.candidate_id == candidate.user_id).one()
        assert saved.job_id == job.job_id
        assert saved.cv.title == 'CV thực tập'

        db.add(Application(candidate_id=candidate.user_id, job_id=job.job_id,
                           cover_letter='Nộp trùng'))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        db.delete(db.query(User).filter(User.email == 'candidate_for_tests@example.test').one())
        db.commit()
    finally:
        db.close()


def test_static_pages_and_scripts_are_served(client):
    page = client.get('/frontend/pages/candidate/index.html')
    assert page.status_code == 200
    assert 'id="public-job-list"' in page.text
    assert 'assets/js/candidate.js' in page.text
    assert client.get('/frontend/assets/js/candidate.js').status_code == 200
    detail_page = client.get('/frontend/pages/candidate/job-detail.html?id=1')
    assert detail_page.status_code == 200
    assert 'id="public-job-detail"' in detail_page.text
