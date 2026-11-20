"""
Kiểm thử tự động API Chức năng Tin tuyển dụng (Task T05FE9A)
Dự án UniCareer - Nhóm 8
Sử dụng SQLite in-memory để kiểm thử độc lập, không phụ thuộc CSDL bên ngoài.
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Thêm đường dẫn project vào sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import Base, get_db
from backend.app.models import User, Company, JobPost
from backend.app.main import app

# Sử dụng SQLite bộ nhớ tạm cho môi trường test
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

class TestJobsAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        db = TestingSessionLocal()
        # Tạo user & company
        user = User(user_id=2, email="hr@technova.example", password_hash="secret", role="EMPLOYER")
        db.add(user)
        db.commit()

        company = Company(
            company_id=1,
            employer_id=2,
            company_name="TechNova",
            industry="Công nghệ thông tin",
            website="https://technova.example",
            location="TP. Hồ Chí Minh",
            description="TechNova test description"
        )
        db.add(company)
        db.commit()
        db.close()

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=engine)

    def test_01_create_job(self):
        """Kiểm tra chức năng Tạo mới tin tuyển dụng (POST /api/jobs)"""
        payload = {
            "company_id": 1,
            "title": "AI Engineer Intern",
            "description": "Nghiên cứu và phát triển mô hình gợi ý CV cho nền tảng UniCareer.",
            "requirements": "Kiến thức Python, PyTorch/TensorFlow, tư duy thuật toán tốt.",
            "location": "TP. Hồ Chí Minh",
            "salary_range": "5–8 triệu/tháng",
            "job_type": "INTERNSHIP",
            "experience_level": "Không yêu cầu",
            "deadline": "2026-12-15",
            "status": "ACTIVE"
        }
        res = client.post("/api/jobs", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["title"], "AI Engineer Intern")
        self.assertEqual(data["status"], "ACTIVE")
        self.assertEqual(data["job_type"], "INTERNSHIP")
        self.assertIn("job_id", data)

    def test_02_get_jobs_list(self):
        """Kiểm tra chức năng Xem danh sách tin tuyển dụng (GET /api/jobs)"""
        res = client.get("/api/jobs")
        self.assertEqual(res.status_code, 200)
        jobs = res.json()
        self.assertGreaterEqual(len(jobs), 1)

    def test_03_get_job_detail(self):
        """Kiểm tra chức năng Xem chi tiết một tin tuyển dụng (GET /api/jobs/{id})"""
        res = client.get("/api/jobs/1")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["job_id"], 1)
        self.assertEqual(data["title"], "AI Engineer Intern")

    def test_04_update_job(self):
        """Kiểm tra chức năng Cập nhật tin tuyển dụng (PUT /api/jobs/{id})"""
        payload = {
            "title": "Senior AI Engineer Intern",
            "salary_range": "6–10 triệu/tháng",
            "location": "Hybrid (TP.HCM)"
        }
        res = client.put("/api/jobs/1", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["title"], "Senior AI Engineer Intern")
        self.assertEqual(data["salary_range"], "6–10 triệu/tháng")
        self.assertEqual(data["location"], "Hybrid (TP.HCM)")
        # Các trường khác phải được giữ nguyên
        self.assertEqual(data["status"], "ACTIVE")

    def test_05_close_job_status(self):
        """Kiểm tra chức năng Đóng tin tuyển dụng (PATCH /api/jobs/{id}/status -> CLOSED)"""
        res = client.patch("/api/jobs/1/status", json={"status": "CLOSED"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "CLOSED")

        # Kiểm tra lọc theo status=CLOSED
        res_filter = client.get("/api/jobs?status=CLOSED")
        self.assertEqual(res_filter.status_code, 200)
        self.assertEqual(len(res_filter.json()), 1)

    def test_06_hide_and_reopen_job(self):
        """Kiểm tra chức năng Ẩn tin (HIDDEN) và Mở lại tin (ACTIVE)"""
        # Ẩn tin
        res_hide = client.patch("/api/jobs/1/status", json={"status": "HIDDEN"})
        self.assertEqual(res_hide.status_code, 200)
        self.assertEqual(res_hide.json()["status"], "HIDDEN")

        # Mở lại tin
        res_active = client.patch("/api/jobs/1/status", json={"status": "ACTIVE"})
        self.assertEqual(res_active.status_code, 200)
        self.assertEqual(res_active.json()["status"], "ACTIVE")

    def test_07_invalid_status_fails(self):
        """Kiểm tra từ chối trạng thái không hợp lệ"""
        res = client.patch("/api/jobs/1/status", json={"status": "INVALID_STATUS"})
        self.assertEqual(res.status_code, 400)

    def test_08_search_job_by_keyword(self):
        """Kiểm tra tìm kiếm tin theo từ khóa (GET /api/jobs?keyword=...)"""
        res = client.get("/api/jobs?keyword=Senior")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)

        res_empty = client.get("/api/jobs?keyword=NonExistentKeywordXYZ")
        self.assertEqual(res_empty.status_code, 200)
        self.assertEqual(len(res_empty.json()), 0)

    def test_09_delete_job(self):
        """Kiểm tra chức năng Xóa tin tuyển dụng (DELETE /api/jobs/{id})"""
        res = client.delete("/api/jobs/1")
        self.assertEqual(res.status_code, 200)

        # Kiểm tra đã bị xóa
        res_check = client.get("/api/jobs/1")
        self.assertEqual(res_check.status_code, 404)

if __name__ == "__main__":
    unittest.main()
