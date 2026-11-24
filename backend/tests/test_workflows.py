import base64
import io
import json
import zipfile
from datetime import date
from unittest.mock import patch
from urllib.error import HTTPError

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.models.role import RoleModel
from app.models.user import UserModel
from app.routers import ai_services, candidate, users
from app.services import ai_matching


@pytest.fixture
def client(monkeypatch, tmp_path):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(main, "SessionLocal", testing_session)
    monkeypatch.setattr(candidate, "CV_DIR", tmp_path / "cvs")
    monkeypatch.setattr(users, "CV_UPLOAD_DIR", tmp_path / "cvs")
    monkeypatch.setattr(ai_services, "CV_STORAGE_DIR", tmp_path / "cvs")

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[get_db] = override_get_db
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()
    engine.dispose()


def register(client, email, role):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "Secure-test-password1",
            "role": role,
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_legacy_user_table_gets_active_column():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(255) NOT NULL, "
            "hashed_password VARCHAR(255) NOT NULL, role VARCHAR(50) NOT NULL, created_at DATETIME NOT NULL)"
        ))
        connection.execute(text(
            "INSERT INTO users (id, email, hashed_password, role, created_at) "
            "VALUES (1, 'legacy@example.com', 'hash', 'candidate', CURRENT_TIMESTAMP)"
        ))

    main.migrate_legacy_schema(engine)

    assert "is_active" in {column["name"] for column in inspect(engine).get_columns("users")}
    with engine.connect() as connection:
        assert connection.execute(text(
            "SELECT is_active FROM users WHERE id = 1"
        )).scalar_one() == 1
    engine.dispose()


def test_legacy_profile_and_cv_tables_get_new_columns():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE profiles (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, "
            "full_name VARCHAR(255) NOT NULL, phone VARCHAR(20), university VARCHAR(255), "
            "major VARCHAR(100), skills TEXT, bio TEXT)"
        ))
        connection.execute(text(
            "CREATE TABLE cvs (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, "
            "file_name VARCHAR(255) NOT NULL, file_url VARCHAR(500), description TEXT)"
        ))

    main.migrate_legacy_schema(engine)

    profile_columns = {column["name"] for column in inspect(engine).get_columns("profiles")}
    cv_columns = {column["name"] for column in inspect(engine).get_columns("cvs")}
    assert {"avatar_url", "github_url", "linkedin_url", "job_search_status"} <= profile_columns
    assert {"cv_type", "personal_info", "content"} <= cv_columns
    engine.dispose()


def create_approved_job(client):
    employer_headers = register(client, "employer@example.com", "employer")
    company = client.put(
        "/api/companies/profile/current",
        headers=employer_headers,
        json={
            "company_name": "Test Company",
            "description": "A test employer",
            "industry": "Technology",
        },
    )
    assert company.status_code == 200, company.text
    job = client.post(
        "/api/jobs",
        headers=employer_headers,
        json={
            "title": "Backend Developer Intern",
            "description": "Build backend services and APIs.",
            "requirements": "Python, SQL, and API development.",
            "job_type": "INTERNSHIP",
            "deadline": date.today().isoformat(),
        },
    )
    assert job.status_code == 201, job.text

    with main.SessionLocal() as db:
        admin = UserModel(
            email="admin@example.com",
            hashed_password=hash_password("Secure-admin-password1"),
            role="admin",
        )
        admin.roles.append(db.query(RoleModel).filter_by(name="admin").one())
        db.add(admin)
        db.commit()
        admin_id = admin.id
    admin_headers = {"Authorization": f"Bearer {create_access_token(admin_id)}"}
    approved = client.put(
        f"/api/admin/jobs/{job.json()['job_id']}/approval",
        headers=admin_headers,
        json={"approval_status": "APPROVED"},
    )
    assert approved.status_code == 200, approved.text
    return employer_headers, job.json()["job_id"], admin_headers


def create_builder_cv(
    client,
    headers,
    email,
    title="CV ứng viên",
    skills="Python, SQL",
):
    response = client.post(
        "/api/candidate/cvs/builder",
        headers=headers,
        json={
            "title": title,
            "personal_info": {
                "full_name": "Test User",
                "email": email,
                "phone": "+84901234567",
            },
            "content": {
                "objective": "Phát triển phần mềm",
                "education": "Đại học UniCare",
                "experience": "Thực tập phát triển ứng dụng",
                "projects": "Nền tảng tuyển dụng",
                "skills": skills,
                "certifications": "Python cơ bản",
            },
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_registration_profile_and_candidate_cv_analysis(client, monkeypatch):
    candidate_headers = register(client, "candidate@example.com", "candidate")
    profile = client.put(
        "/api/users/me/profile",
        headers=candidate_headers,
        json={
            "full_name": "Candidate One",
            "phone": "+84901234567",
            "github_url": "https://github.com/candidate",
            "job_search_status": "INTERNSHIP",
        },
    )
    assert profile.status_code == 200, profile.text
    assert profile.json()["phone"] == "+84901234567"
    assert profile.json()["job_search_status"] == "INTERNSHIP"
    assert "university" not in profile.json()

    cv = create_builder_cv(client, candidate_headers, "candidate@example.com")
    assert cv["allow_ai_analysis"] is False
    _, job_id, _ = create_approved_job(client)

    denied = client.post(
        "/api/ai/analyze/candidate",
        headers=candidate_headers,
        json={"cv_id": cv["cv_id"], "job_id": job_id, "consent_to_gemini": False},
    )
    assert denied.status_code == 400

    monkeypatch.setattr(
        ai_matching,
        "analyze_cv_text",
        lambda *args: {
            "score": 75,
            "summary": "Kỹ năng phù hợp với yêu cầu chính.",
            "matched_skills": ["Python"],
            "missing_skills": ["SQL nâng cao"],
            "recommendations": ["Bổ sung dự án thực tế."],
        },
    )
    analyzed = client.post(
        "/api/ai/analyze/candidate",
        headers=candidate_headers,
        json={"cv_id": cv["cv_id"], "job_id": job_id, "consent_to_gemini": True},
    )
    assert analyzed.status_code == 200, analyzed.text
    assert analyzed.json()["score"] == 75

    with main.SessionLocal() as db:
        saved = db.query(main.models.CVAnalysisModel).one()
        assert saved.job_id == job_id
        assert json.loads(saved.matched_skills) == ["Python"]

    login = client.post(
        "/api/auth/login",
        json={"email": "candidate@example.com", "password": "Secure-test-password1"},
    )
    assert login.status_code == 200
    login_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    logout = client.post("/api/auth/logout", headers=login_headers)
    assert logout.status_code == 200
    assert client.get("/api/auth/me", headers=login_headers).status_code == 401


def test_application_duplicate_prevention_and_employer_status(client):
    employer_headers, job_id, _ = create_approved_job(client)
    candidate_headers = register(client, "applicant@example.com", "candidate")
    profile = client.put(
        "/api/users/me/profile",
        headers=candidate_headers,
        json={
            "full_name": "Applicant",
            "phone": "+84987654321",
        },
    )
    assert profile.status_code == 200
    cv_response = client.post(
        "/api/candidate/cvs/builder",
        headers=candidate_headers,
        json={
            "title": "CV Backend",
            "personal_info": {
                "full_name": "Applicant CV",
                "email": "applicant.cv@example.com",
                "phone": "+84987654321",
            },
            "content": {
                "education": "UniCare University · Software Engineering",
                "skills": "Python, REST API",
            },
        },
    )
    assert cv_response.status_code == 201, cv_response.text
    cv = cv_response.json()

    application = client.post(
        "/api/candidate/applications",
        headers=candidate_headers,
        json={"job_id": job_id, "cv_id": cv["cv_id"], "cover_letter": "I am interested."},
    )
    assert application.status_code == 201, application.text
    duplicate = client.post(
        "/api/candidate/applications",
        headers=candidate_headers,
        json={"job_id": job_id, "cv_id": cv["cv_id"]},
    )
    assert duplicate.status_code == 409

    company = client.get("/api/companies/profile/current", headers=employer_headers)
    applications = client.get(
        f"/api/companies/{company.json()['company_id']}/applications",
        headers=employer_headers,
    )
    assert applications.status_code == 200, applications.text
    assert applications.json()[0]["candidate_name"] == "Applicant CV"
    assert applications.json()[0]["candidate_email"] == "applicant.cv@example.com"
    assert applications.json()[0]["candidate_university"] == "UniCare University · Software Engineering"
    assert applications.json()[0]["candidate_major"] is None
    assert applications.json()[0]["candidate_skills"] == "Python, REST API"
    assert applications.json()[0]["cv_type"] == "builder"
    downloaded_cv = client.get(
        f"/api/candidate/cvs/{cv['cv_id']}/download",
        headers=employer_headers,
    )
    assert downloaded_cv.status_code == 200
    assert "<h1>Applicant CV</h1>" in downloaded_cv.text

    updated = client.put(
        f"/api/companies/{company.json()['company_id']}/applications/{application.json()['application_id']}/status",
        headers=employer_headers,
        json={"status": "REVIEWING"},
    )
    assert updated.status_code == 200, updated.text
    invalid_transition = client.put(
        f"/api/companies/{company.json()['company_id']}/applications/{application.json()['application_id']}/status",
        headers=employer_headers,
        json={"status": "PENDING"},
    )
    assert invalid_transition.status_code == 422


def test_public_job_search_and_admin_account_lock(client):
    _, job_id, admin_headers = create_approved_job(client)
    admin_id = client.get("/api/auth/me", headers=admin_headers).json()["id"]
    with main.SessionLocal() as db:
        second_admin = UserModel(
            email="second-admin@example.com",
            hashed_password=hash_password("Secure-admin-password2"),
            role="admin",
        )
        second_admin.roles.append(db.query(RoleModel).filter_by(name="admin").one())
        db.add(second_admin)
        db.commit()
        second_admin_id = second_admin.id

    self_lock = client.put(
        f"/api/admin/users/{admin_id}/status",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert self_lock.status_code == 409
    assert client.get("/api/auth/me", headers=admin_headers).status_code == 200

    second_admin_lock = client.put(
        f"/api/admin/users/{second_admin_id}/status",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert second_admin_lock.status_code == 200
    last_admin_lock = client.put(
        f"/api/admin/users/{second_admin_id}/status",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert last_admin_lock.status_code == 409

    found = client.get("/api/jobs/public", params={"keyword": "Backend"})
    assert found.status_code == 200
    assert found.json()["total"] == 1
    assert found.json()["items"][0]["job_id"] == job_id
    missing = client.get("/api/jobs/public", params={"keyword": "no-such-role"})
    assert missing.json()["total"] == 0

    candidate_headers = register(client, "lockable@example.com", "candidate")
    current_user = client.get("/api/auth/me", headers=candidate_headers)
    locked = client.put(
        f"/api/admin/users/{current_user.json()['id']}/status",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert locked.status_code == 200
    assert client.get("/api/auth/me", headers=candidate_headers).status_code == 401


def test_public_registration_cannot_create_admin_and_admin_routes_are_protected(client):
    registration = client.post(
        "/api/auth/register",
        json={
            "email": "self-appointed-admin@example.com",
            "password": "Secure-test-password1",
            "role": "admin",
        },
    )
    assert registration.status_code == 400

    candidate_headers = register(client, "candidate-admin-access@example.com", "candidate")
    assert client.get("/api/admin/stats").status_code == 401
    assert client.get("/api/admin/stats", headers=candidate_headers).status_code == 403
    oversized_password = client.post(
        "/api/auth/login",
        json={"email": "candidate-admin-access@example.com", "password": "x" * 129},
    )
    assert oversized_password.status_code == 422


def test_company_website_requires_http_or_https(client):
    employer_headers = register(client, "company-website@example.com", "employer")
    invalid = client.put(
        "/api/companies/profile/current",
        headers=employer_headers,
        json={"company_name": "Test Company", "website": "javascript:alert(1)"},
    )
    assert invalid.status_code == 422

    valid = client.put(
        "/api/companies/profile/current",
        headers=employer_headers,
        json={"company_name": "Test Company", "website": "https://example.com"},
    )
    assert valid.status_code == 200
    assert valid.json()["website"] == "https://example.com"


def test_cv_file_is_preserved_when_delete_transaction_fails(client, monkeypatch, tmp_path):
    headers = register(client, "cv-delete@example.com", "candidate")
    uploaded = client.post(
        "/api/candidate/cvs/upload",
        headers=headers,
        files={"file": ("resume.pdf", b"%PDF-1.7 test document", "application/pdf")},
    )
    assert uploaded.status_code == 201, uploaded.text
    cv_id = uploaded.json()["cv_id"]
    stored_path = next((tmp_path / "cvs").iterdir())
    assert stored_path.is_file()

    def fail_commit(_self):
        raise SQLAlchemyError("simulated database failure")

    monkeypatch.setattr("sqlalchemy.orm.Session.commit", fail_commit)
    deleted = client.delete(f"/api/candidate/cvs/{cv_id}", headers=headers)
    assert deleted.status_code == 500
    assert stored_path.is_file()
    listed = client.get("/api/candidate/cvs", headers=headers)
    assert listed.status_code == 200
    assert any(cv["cv_id"] == cv_id for cv in listed.json())


def test_employer_ai_requires_candidate_consent_and_persists_result(client, monkeypatch):
    employer_headers, job_id, _ = create_approved_job(client)
    candidate_headers = register(client, "consenting@example.com", "candidate")
    cv = create_builder_cv(
        client,
        candidate_headers,
        "consenting@example.com",
        title="CV ứng viên đồng ý AI",
    )
    application = client.post(
        "/api/candidate/applications",
        headers=candidate_headers,
        json={"job_id": job_id, "cv_id": cv["cv_id"]},
    )
    assert application.status_code == 201
    company_id = client.get(
        "/api/companies/profile/current",
        headers=employer_headers,
    ).json()["company_id"]
    listed_applications = client.get(
        f"/api/companies/{company_id}/applications",
        headers=employer_headers,
    )
    assert listed_applications.status_code == 200
    assert listed_applications.json()[0]["cv_ai_allowed"] is False

    denied = client.post(
        "/api/ai/analyze/application",
        headers=employer_headers,
        json={"application_id": application.json()["application_id"]},
    )
    assert denied.status_code == 403

    consent = client.put(
        f"/api/candidate/cvs/{cv['cv_id']}/ai-consent",
        headers=candidate_headers,
        json={"allow_ai_analysis": True},
    )
    assert consent.status_code == 200
    listed_applications = client.get(
        f"/api/companies/{company_id}/applications",
        headers=employer_headers,
    )
    assert listed_applications.json()[0]["cv_ai_allowed"] is True
    monkeypatch.setattr(
        ai_matching,
        "analyze_cv_text",
        lambda *args: {
            "score": 60,
            "summary": "Có một số kỹ năng cần bổ sung.",
            "matched_skills": ["Python"],
            "missing_skills": ["SQL"],
            "recommendations": ["Thực hành truy vấn dữ liệu."],
        },
    )
    analyzed = client.post(
        "/api/ai/analyze/application",
        headers=employer_headers,
        json={"application_id": application.json()["application_id"]},
    )
    assert analyzed.status_code == 200, analyzed.text
    assert analyzed.json()["score"] == 60

    revoked = client.put(
        f"/api/candidate/cvs/{cv['cv_id']}/ai-consent",
        headers=candidate_headers,
        json={"allow_ai_analysis": False},
    )
    assert revoked.status_code == 200
    denied_again = client.post(
        "/api/ai/analyze/application",
        headers=employer_headers,
        json={"application_id": application.json()["application_id"]},
    )
    assert denied_again.status_code == 403

    deleted = client.delete(
        f"/api/users/me/cvs/{cv['cv_id']}",
        headers=candidate_headers,
    )
    assert deleted.status_code == 204
    with main.SessionLocal() as db:
        assert db.query(main.models.CVAnalysisModel).count() == 0


def test_profile_and_multiple_cv_versions_remain_independent(client):
    headers = register(client, "profile-cv@example.com", "candidate")
    saved_profile = client.put(
        "/api/users/me/profile",
        headers=headers,
        json={
            "full_name": "Nguyễn Minh Anh",
            "email": "profile-cv@example.com",
            "phone": "+84901234567",
            "avatar_url": "https://example.com/avatar.png",
            "github_url": "https://github.com/minhanh",
            "linkedin_url": "https://linkedin.com/in/minhanh",
            "job_search_status": "OPEN",
        },
    )
    assert saved_profile.status_code == 200, saved_profile.text
    assert "skills" not in saved_profile.json()

    def create_builder(title, name, skills):
        response = client.post(
            "/api/candidate/cvs/builder",
            headers=headers,
            json={
                "title": title,
                "personal_info": {
                    "full_name": name,
                    "email": "profile-cv@example.com",
                    "phone": "+84901234567",
                    "github_url": "https://github.com/minhanh",
                    "linkedin_url": None,
                },
                "content": {
                    "objective": "Phát triển phần mềm",
                    "education": "Đại học UniCare",
                    "experience": "Thực tập backend",
                    "projects": "Nền tảng tuyển dụng",
                    "skills": skills,
                    "certifications": "Python cơ bản",
                },
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    first_cv = create_builder("CV Backend", "Minh Anh - Backend", "Python, FastAPI")
    second_cv = create_builder("CV Data", "Minh Anh - Data", "SQL, Pandas")
    updated_cv = client.put(
        f"/api/candidate/cvs/{first_cv['cv_id']}",
        headers=headers,
        json={
            "title": "CV Backend Intern",
            "personal_info": {
                "full_name": "Minh Anh - Backend",
                "email": "profile-cv@example.com",
                "phone": "+84901234567",
                "github_url": "https://github.com/minhanh",
                "linkedin_url": None,
            },
            "content": {
                "objective": "Ứng tuyển vị trí backend",
                "education": "Đại học UniCare",
                "experience": "Thực tập backend",
                "projects": "Nền tảng tuyển dụng",
                "skills": "Python, FastAPI, MySQL",
                "certifications": "Python cơ bản",
            },
        },
    )
    assert updated_cv.status_code == 200, updated_cv.text

    listed_cvs = client.get("/api/candidate/cvs", headers=headers)
    assert listed_cvs.status_code == 200
    assert {cv["cv_id"] for cv in listed_cvs.json()} == {
        first_cv["cv_id"],
        second_cv["cv_id"],
    }
    assert next(cv for cv in listed_cvs.json() if cv["cv_id"] == first_cv["cv_id"])["title"] == "CV Backend Intern"
    unchanged_profile = client.get("/api/users/me/profile", headers=headers)
    assert unchanged_profile.status_code == 200
    assert unchanged_profile.json()["full_name"] == "Nguyễn Minh Anh"
    assert unchanged_profile.json()["phone"] == "+84901234567"

    password_change = client.put(
        "/api/users/me/password",
        headers=headers,
        json={
            "current_password": "Secure-test-password1",
            "new_password": "Secure-new-password1",
        },
    )
    assert password_change.status_code == 200, password_change.text
    login = client.post(
        "/api/auth/login",
        json={"email": "profile-cv@example.com", "password": "Secure-new-password1"},
    )
    assert login.status_code == 200, login.text


def test_candidate_can_upload_cv_and_create_builder_cv(client):
    headers = register(client, "text-only@example.com", "candidate")
    uploaded = client.post(
        "/api/candidate/cvs/upload",
        headers=headers,
        files={"file": ("candidate.pdf", b"%PDF-1.7", "application/pdf")},
    )
    assert uploaded.status_code == 201, uploaded.text
    assert uploaded.json()["cv_type"] == "upload"
    assert uploaded.json()["title"] == "candidate.pdf"
    downloaded = client.get(uploaded.json()["file_url"], headers=headers)
    assert downloaded.status_code == 200
    assert downloaded.content == b"%PDF-1.7"
    assert client.post(
        "/api/users/me/cvs",
        headers=headers,
        files={"file": ("candidate.pdf", b"%PDF-1.7", "application/pdf")},
    ).status_code == 405

    cv = create_builder_cv(client, headers, "text-only@example.com")
    assert cv["cv_type"] == "builder"
    assert cv["file_url"] is not None
    assert cv["content"]["skills"] == "Python, SQL"


@pytest.mark.parametrize(
    ("filename", "content", "status_code"),
    [
        pytest.param("candidate.txt", b"not a CV", 422, id="unsupported-extension"),
        pytest.param("candidate.pdf", b"not a PDF", 422, id="invalid-pdf"),
        pytest.param("candidate.docx", b"not a DOCX archive", 422, id="invalid-docx"),
        pytest.param(
            "large.pdf",
            b"%PDF-" + b"x" * (10 * 1024 * 1024),
            413,
            id="oversized-pdf",
        ),
    ],
)
def test_cv_upload_rejects_invalid_files(client, filename, content, status_code):
    headers = register(client, f"invalid-{filename.replace('.', '-')}@example.com", "candidate")
    response = client.post(
        "/api/candidate/cvs/upload",
        headers=headers,
        files={"file": (filename, content, "application/octet-stream")},
    )
    assert response.status_code == status_code, response.text
    assert client.get("/api/candidate/cvs", headers=headers).json() == []
    assert not candidate.CV_DIR.exists() or list(candidate.CV_DIR.iterdir()) == []


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("candidate.pdf", b"%PDF-1.7 private CV content"),
        ("candidate.docx", None),
    ],
)
def test_uploaded_cvs_can_be_analyzed(client, monkeypatch, filename, content):
    if filename.endswith(".docx"):
        document = io.BytesIO()
        with zipfile.ZipFile(document, "w") as archive:
            archive.writestr("word/document.xml", "<document>CV content</document>")
        content = document.getvalue()

    headers = register(client, f"upload-ai-{filename.replace('.', '-')}@example.com", "candidate")
    uploaded = client.post(
        "/api/candidate/cvs/upload",
        headers=headers,
        files={"file": (filename, content, "application/octet-stream")},
    )
    assert uploaded.status_code == 201, uploaded.text
    _, job_id, _ = create_approved_job(client)
    captured = {}

    def fake_analyze_cv_file(path, original_name, job_title, job_description, job_requirements):
        captured["path"] = path
        captured["original_name"] = original_name
        captured["job"] = (job_title, job_description, job_requirements)
        return {
            "score": 80,
            "summary": "Phù hợp.",
            "matched_skills": ["Python"],
            "missing_skills": [],
            "recommendations": ["Tiếp tục học."],
        }

    monkeypatch.setattr(ai_matching, "analyze_cv_file", fake_analyze_cv_file)
    analyzed = client.post(
        "/api/ai/analyze/candidate",
        headers=headers,
        json={
            "cv_id": uploaded.json()["cv_id"],
            "job_id": job_id,
            "consent_to_gemini": True,
        },
    )

    assert analyzed.status_code == 200, analyzed.text
    assert analyzed.json()["score"] == 80
    assert captured["path"].read_bytes() == content
    assert captured["original_name"] == filename
    assert captured["job"] == (
        "Backend Developer Intern",
        "Build backend services and APIs.",
        "Python, SQL, and API development.",
    )


def test_gemini_request_uses_inline_pdf_input(tmp_path, monkeypatch):
    cv_path = tmp_path / "cv.pdf"
    cv_data = b"%PDF-1.7 private CV content"
    cv_path.write_bytes(cv_data)
    result = {
        "score": 80,
        "summary": "Phù hợp.",
        "matched_skills": ["Python"],
        "missing_skills": [],
        "recommendations": ["Tiếp tục học."],
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({
                "candidates": [{
                    "content": {
                        "parts": [{
                            "text": json.dumps(result, ensure_ascii=False),
                        }],
                    },
                }],
            }).encode("utf-8")

    monkeypatch.setattr(ai_matching, "GEMINI_API_KEY", "test-api-key")
    monkeypatch.setattr(ai_matching, "GEMINI_MODEL", "test-model")
    with patch("app.services.ai_matching.urlopen", return_value=FakeResponse()) as gemini_request:
        response = ai_matching.analyze_cv_file(
            cv_path,
            "cv.pdf",
            "Backend Developer",
            "Build APIs.",
            "Python and SQL.",
        )

    request = gemini_request.call_args.args[0]
    sent = json.loads(request.data)
    file_input = sent["contents"][0]["parts"][1]["inlineData"]
    assert request.full_url.endswith("/models/test-model:generateContent")
    assert request.get_header("X-goog-api-key") == "test-api-key"
    assert file_input["mimeType"] == "application/pdf"
    assert file_input["data"] == base64.b64encode(cv_data).decode("ascii")
    assert sent["generationConfig"]["responseMimeType"] == "application/json"
    assert response == result


def test_legacy_docx_cv_is_extracted_and_analyzed_as_text(tmp_path, monkeypatch):
    cv_path = tmp_path / "cv.docx"
    document_xml = b"""\
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Backend Engineer</w:t></w:r></w:p>
    <w:p><w:r><w:t>Python</w:t><w:tab/><w:t>SQL</w:t></w:r></w:p>
  </w:body>
</w:document>
"""
    with zipfile.ZipFile(cv_path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)

    captured = {}
    result = {"score": 80}

    def fake_analyze_cv_text(cv_text, job_title, job_description, job_requirements):
        captured["args"] = (
            cv_text,
            job_title,
            job_description,
            job_requirements,
        )
        return result

    monkeypatch.setattr(ai_matching, "analyze_cv_text", fake_analyze_cv_text)
    response = ai_matching.analyze_cv_file(
        cv_path,
        "cv.docx",
        "Backend Developer",
        "Build APIs.",
        "Python and SQL.",
    )

    assert response == result
    assert captured["args"] == (
        "Backend Engineer\nPython\tSQL",
        "Backend Developer",
        "Build APIs.",
        "Python and SQL.",
    )


def test_invalid_legacy_docx_cv_returns_clear_error(tmp_path):
    cv_path = tmp_path / "cv.docx"
    cv_path.write_bytes(b"not a DOCX archive")

    with pytest.raises(HTTPException) as error:
        ai_matching.analyze_cv_file(
            cv_path,
            "cv.docx",
            "Backend Developer",
            "Build APIs.",
            "Python and SQL.",
        )

    assert error.value.status_code == 422
    assert "DOCX" in error.value.detail


def test_gemini_request_uses_entered_cv_text_without_personal_contact(monkeypatch):
    result = {
        "score": 80,
        "summary": "Kỹ năng phù hợp.",
        "matched_skills": ["Python"],
        "missing_skills": ["SQL"],
        "recommendations": ["Bổ sung dự án dữ liệu."],
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({
                "candidates": [{
                    "content": {
                        "parts": [{
                            "text": json.dumps(result, ensure_ascii=False),
                        }],
                    },
                }],
            }).encode("utf-8")

    monkeypatch.setattr(ai_matching, "GEMINI_API_KEY", "test-api-key")
    monkeypatch.setattr(ai_matching, "GEMINI_MODEL", "test-model")
    with patch("app.services.ai_matching.urlopen", return_value=FakeResponse()) as gemini_request:
        response = ai_matching.analyze_cv_text(
            "Kỹ năng:\nPython, FastAPI\nDự án:\nNền tảng tuyển dụng",
            "Backend Developer",
            "Phát triển REST API.",
            "Python, SQL.",
        )

    request = gemini_request.call_args.args[0]
    sent = json.loads(request.data)
    user_text = sent["contents"][0]["parts"][0]["text"]
    assert request.full_url.endswith("/models/test-model:generateContent")
    assert sent["generationConfig"]["responseJsonSchema"]["required"]
    assert "Nền tảng tuyển dụng" in user_text
    assert "candidate@example.com" not in user_text
    assert response == result


def test_gemini_analysis_requires_api_key(monkeypatch):
    monkeypatch.setattr(ai_matching, "GEMINI_API_KEY", "")
    with pytest.raises(HTTPException) as error:
        ai_matching.analyze_cv_text(
            "Kỹ năng: Python",
            "Backend Developer",
            "Phát triển REST API.",
            "Python, SQL.",
        )
    assert error.value.status_code == 503


def test_gemini_analysis_retries_transient_service_unavailable(monkeypatch):
    result = {
        "score": 80,
        "summary": "Phù hợp.",
        "matched_skills": ["Python"],
        "missing_skills": [],
        "recommendations": ["Tiếp tục học."],
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({
                "candidates": [{
                    "content": {
                        "parts": [{
                            "text": json.dumps(result, ensure_ascii=False),
                        }],
                    },
                }],
            }).encode("utf-8")

    monkeypatch.setattr(ai_matching, "GEMINI_API_KEY", "test-api-key")
    with (
        patch(
            "app.services.ai_matching.urlopen",
            side_effect=[
                HTTPError(
                    "https://example.test/generateContent",
                    503,
                    "Service Unavailable",
                    {},
                    io.BytesIO(),
                ),
                FakeResponse(),
            ],
        ) as gemini_request,
        patch("app.services.ai_matching.time.sleep") as sleep,
    ):
        response = ai_matching._request_analysis([{"text": "synthetic input"}])

    assert response == result
    assert gemini_request.call_count == 2
    sleep.assert_called_once()
