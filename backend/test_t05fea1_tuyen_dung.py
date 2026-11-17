"""
KIỂM THỬ TOÀN DIỆN CHỨC NĂNG TUYỂN DỤNG (TASK T05FEA1)
Dự án: UniCareer - Nền tảng kết nối việc làm và định hướng nghề nghiệp cho sinh viên (Nhóm 8)
Người thực hiện: Đỗ Hoàng Sơn (PTIT-HCM-066)
Mô tả task: Kiểm tra tạo, cập nhật và đóng/ẩn tin tuyển dụng
Sprint: Sprint 3 (16/11 - 20/11)
Hạn hoàn thành: 17/11/2026
"""

import os
import sys
import unittest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Đảm bảo đường dẫn import đúng module của project
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.database import Base, get_db
from backend.app.models.user import User
from backend.app.models.company import Company
from backend.app.models.job import JobPost
from backend.app.main import app

# Sử dụng SQLite In-Memory độc lập, cô lập môi trường kiểm thử không ảnh hưởng DB thật
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

class TestRecruitmentFeatureT05FEA1(unittest.TestCase):
    """
    Bộ test case tự động chuẩn hóa cho Task T05FEA1:
    Hoàn thiện chức năng tuyển dụng - Kiểm tra tạo, cập nhật và đóng/ẩn tin tuyển dụng.
    """

    @classmethod
    def setUpClass(cls):
        """Khởi tạo schema và dữ liệu công ty mẫu ban đầu"""
        Base.metadata.create_all(bind=test_engine)
        db = TestingSession()
        try:
            # Tạo tài khoản nhà tuyển dụng
            user = User(
                user_id=1,
                email="employer@technova.example",
                password_hash="pbkdf2_hash_demo",
                role="EMPLOYER",
                is_active=True
            )
            db.add(user)
            db.commit()

            # Tạo hồ sơ công ty
            company = Company(
                company_id=1,
                employer_id=1,
                company_name="TechNova Solutions",
                industry="Công nghệ thông tin / Phần mềm",
                website="https://technova.example",
                location="TP. Hồ Chí Minh",
                description="Công ty phát triển giải pháp phần mềm và AI cho sinh viên."
            )
            db.add(company)
            db.commit()
        finally:
            db.close()

    @classmethod
    def tearDownClass(cls):
        """Dọn dẹp môi trường database sau khi kiểm thử kết thúc"""
        Base.metadata.drop_all(bind=test_engine)

    def test_01_create_job_success(self):
        """TC01: Kiểm tra TẠO MỚI tin tuyển dụng thành công với đầy đủ thông tin (POST /api/jobs)"""
        payload = {
            "company_id": 1,
            "title": "Backend AI Developer Intern",
            "description": "Tham gia phát triển API và tích hợp mô hình AI gợi ý việc làm cho sinh viên.",
            "requirements": "Thành thạo Python, hiểu biết về FastAPI/Flask, tư duy thuật toán tốt.",
            "location": "TP. Hồ Chí Minh",
            "salary_range": "5–8 triệu/tháng",
            "job_type": "INTERNSHIP",
            "experience_level": "Không yêu cầu",
            "deadline": str(date.today() + timedelta(days=30)),
            "status": "ACTIVE"
        }
        res = client.post("/api/jobs", json=payload)
        self.assertEqual(res.status_code, 201, f"Không tạo được tin tuyển dụng: {res.text}")
        data = res.json()
        self.assertIn("job_id", data)
        self.assertEqual(data["title"], "Backend AI Developer Intern")
        self.assertEqual(data["company_id"], 1)
        self.assertEqual(data["status"], "ACTIVE")
        self.assertEqual(data["job_type"], "INTERNSHIP")
        self.assertEqual(data["approval_status"], "APPROVED")
        self.assertIsNotNone(data["created_at"])
        # Lưu lại ID để các test case kế tiếp sử dụng
        self.__class__.created_job_id = data["job_id"]

    def test_02_create_job_validation_errors(self):
        """TC02: Kiểm tra validation khi thiếu các trường bắt buộc (title, description, requirements)"""
        # Thiếu title
        invalid_payload_1 = {
            "company_id": 1,
            "description": "Mô tả công việc đầy đủ",
            "requirements": "Yêu cầu ứng viên"
        }
        res1 = client.post("/api/jobs", json=invalid_payload_1)
        self.assertEqual(res1.status_code, 422)

        # Title quá ngắn (< 3 ký tự)
        invalid_payload_2 = {
            "company_id": 1,
            "title": "AB",
            "description": "Mô tả công việc chi tiết",
            "requirements": "Yêu cầu ứng viên"
        }
        res2 = client.post("/api/jobs", json=invalid_payload_2)
        self.assertEqual(res2.status_code, 422)

    def test_03_get_job_detail_and_not_found(self):
        """TC03: Kiểm tra XEM CHI TIẾT tin tuyển dụng theo ID (GET /api/jobs/{id})"""
        job_id = getattr(self.__class__, "created_job_id", 1)
        res = client.get(f"/api/jobs/{job_id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["job_id"], job_id)
        self.assertEqual(data["title"], "Backend AI Developer Intern")

        # Kiểm tra mã không tồn tại -> trả về 404
        res_404 = client.get("/api/jobs/999999")
        self.assertEqual(res_404.status_code, 404)

    def test_04_get_jobs_list_and_pagination(self):
        """TC04: Kiểm tra XEM DANH SÁCH tin tuyển dụng và phân trang (GET /api/jobs)"""
        res = client.get("/api/jobs?limit=10&skip=0")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

    def test_05_update_job_success(self):
        """TC05: Kiểm tra CẬP NHẬT tin tuyển dụng (PUT /api/jobs/{id})"""
        job_id = getattr(self.__class__, "created_job_id", 1)
        payload = {
            "title": "Senior Backend AI Developer Intern",
            "salary_range": "7–10 triệu/tháng",
            "location": "Hybrid (TP.HCM / Remote)",
            "description": "Mô tả đã được cập nhật mở rộng với nhiệm vụ tối ưu hóa truy vấn CSDL.",
            "requirements": "Kinh nghiệm Python nâng cao, SQLAlchemy, Docker cơ bản."
        }
        res = client.put(f"/api/jobs/{job_id}", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["title"], "Senior Backend AI Developer Intern")
        self.assertEqual(data["salary_range"], "7–10 triệu/tháng")
        self.assertEqual(data["location"], "Hybrid (TP.HCM / Remote)")
        # Kiểm tra các trường không thay đổi vẫn giữ nguyên vẹn
        self.assertEqual(data["status"], "ACTIVE")
        self.assertEqual(data["job_type"], "INTERNSHIP")

    def test_06_update_job_not_found(self):
        """TC06: Kiểm tra cập nhật tin tuyển dụng không tồn tại -> 404 Not Found"""
        res = client.put("/api/jobs/888888", json={"title": "Vị trí không tồn tại"})
        self.assertEqual(res.status_code, 404)

    def test_07_close_job_recruitment(self):
        """TC07: Kiểm tra chức năng ĐÓNG TIN TUYỂN DỤNG (PATCH /api/jobs/{id}/status -> CLOSED)"""
        job_id = getattr(self.__class__, "created_job_id", 1)
        res = client.patch(f"/api/jobs/{job_id}/status", json={"status": "CLOSED"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "CLOSED")

        # Kiểm tra bộ lọc lọc tin đã đóng (status=CLOSED)
        filter_res = client.get("/api/jobs?status=CLOSED")
        self.assertEqual(filter_res.status_code, 200)
        closed_jobs = filter_res.json()
        self.assertTrue(any(j["job_id"] == job_id for j in closed_jobs))

    def test_08_hide_job_recruitment(self):
        """TC08: Kiểm tra chức năng TẠM ẨN TIN TUYỂN DỤNG (PATCH /api/jobs/{id}/status -> HIDDEN)"""
        job_id = getattr(self.__class__, "created_job_id", 1)
        res = client.patch(f"/api/jobs/{job_id}/status", json={"status": "HIDDEN"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "HIDDEN")

        # Kiểm tra bộ lọc lọc tin tạm ẩn (status=HIDDEN)
        filter_res = client.get("/api/jobs?status=HIDDEN")
        self.assertEqual(filter_res.status_code, 200)
        hidden_jobs = filter_res.json()
        self.assertTrue(any(j["job_id"] == job_id for j in hidden_jobs))

    def test_09_reopen_job_recruitment(self):
        """TC09: Kiểm tra chức năng MỞ LẠI TIN TUYỂN DỤNG (PATCH /api/jobs/{id}/status -> ACTIVE)"""
        job_id = getattr(self.__class__, "created_job_id", 1)
        res = client.patch(f"/api/jobs/{job_id}/status", json={"status": "ACTIVE"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ACTIVE")

        # Kiểm tra bộ lọc lọc tin đang tuyển (status=ACTIVE)
        filter_res = client.get("/api/jobs?status=ACTIVE")
        self.assertEqual(filter_res.status_code, 200)
        active_jobs = filter_res.json()
        self.assertTrue(any(j["job_id"] == job_id for j in active_jobs))

    def test_10_invalid_status_rejected(self):
        """TC10: Kiểm tra từ chối đổi sang trạng thái không hợp lệ -> 400 Bad Request"""
        job_id = getattr(self.__class__, "created_job_id", 1)
        res = client.patch(f"/api/jobs/{job_id}/status", json={"status": "UNKNOWN_STATUS_XYZ"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("không hợp lệ", res.json()["detail"])

    def test_11_update_status_not_found(self):
        """TC11: Kiểm tra đổi trạng thái cho tin không tồn tại -> 404 Not Found"""
        res = client.patch("/api/jobs/777777/status", json={"status": "CLOSED"})
        self.assertEqual(res.status_code, 404)

    def test_12_search_jobs_by_keyword(self):
        """TC12: Kiểm tra chức năng TÌM KIẾM TIN theo từ khóa (GET /api/jobs?keyword=...)"""
        # Tìm từ khóa có trong tiêu đề
        res_found = client.get("/api/jobs?keyword=Senior")
        self.assertEqual(res_found.status_code, 200)
        self.assertGreaterEqual(len(res_found.json()), 1)

        # Tìm từ khóa không tồn tại
        res_empty = client.get("/api/jobs?keyword=TuKhoaKhongTonTai_999")
        self.assertEqual(res_empty.status_code, 200)
        self.assertEqual(len(res_empty.json()), 0)

    def test_13_filter_by_job_type(self):
        """TC13: Kiểm tra lọc theo loại hình công việc (job_type=INTERNSHIP)"""
        res = client.get("/api/jobs?job_type=INTERNSHIP")
        self.assertEqual(res.status_code, 200)
        jobs = res.json()
        self.assertTrue(all(j["job_type"] == "INTERNSHIP" for j in jobs))

    def test_14_delete_job_and_verify(self):
        """TC14: Kiểm tra chức năng XÓA TIN TUYỂN DỤNG (DELETE /api/jobs/{id})"""
        # Tạo một tin phụ để xóa
        temp_job_res = client.post("/api/jobs", json={
            "company_id": 1,
            "title": "Temp Job To Delete",
            "description": "Mô tả công việc tạm thời",
            "requirements": "Yêu cầu tạm thời"
        })
        self.assertEqual(temp_job_res.status_code, 201)
        temp_id = temp_job_res.json()["job_id"]

        # Thực hiện xóa
        del_res = client.delete(f"/api/jobs/{temp_id}")
        self.assertEqual(del_res.status_code, 200)

        # Xác nhận truy vấn lại trả về 404 Not Found
        get_res = client.get(f"/api/jobs/{temp_id}")
        self.assertEqual(get_res.status_code, 404)

        # Xóa lại lần 2 trả về 404
        del_again = client.delete(f"/api/jobs/{temp_id}")
        self.assertEqual(del_again.status_code, 404)

    def test_15_frontend_static_pages_accessible(self):
        """TC15: Kiểm tra các trang giao diện HTML nhà tuyển dụng được phục vụ chuẩn xác"""
        pages = [
            "/frontend/pages/company/manage-jobs.html",
            "/frontend/pages/company/post-job.html",
            "/frontend/pages/company/edit-job.html"
        ]
        for page_url in pages:
            res = client.get(page_url)
            self.assertEqual(res.status_code, 200, f"Trang {page_url} không tải được: {res.status_code}")
            self.assertIn("UniCareer", res.text)


def run_full_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRecruitmentFeatureT05FEA1)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

if __name__ == "__main__":
    result = run_full_suite()
    if not result.wasSuccessful():
        sys.exit(1)
