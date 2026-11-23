"""
BỘ KIỂM THỬ TỔNG THỂ TÍCH HỢP CÁC MODULE HỆ THỐNG
Dự án: UniCareer - Nhóm 8
Mã Task: T05FEB0
Người thực hiện: Đỗ Hoàng Sơn (TV2)
Mô tả: Kiểm tra tích hợp và liên kết dữ liệu end-to-end giữa 5 phân hệ:
1. Module Tài khoản & Phân quyền (Authentication & Users)
2. Module Hồ sơ Ứng viên (Candidate & Skills)
3. Module Doanh nghiệp (Employer & Company)
4. Module Việc làm & Tìm kiếm (Jobs & Search)
5. Module Ứng tuyển & Quản lý đơn (Applications)
6. Module Quản trị & Kiểm duyệt (Admin & Moderation)
"""

import os
import sys
import unittest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.database import Base, get_db
from backend.app.models.user import User
from backend.app.models.candidate import Candidate
from backend.app.models.company import Company
from backend.app.models.job import JobPost
from backend.app.models.application import Application
from backend.app.main import app

# Sử dụng SQLite In-Memory độc lập, cô lập môi trường test
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


class TestSystemIntegrationT05FEB0(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=test_engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=test_engine)

    def setUp(self):
        self.db = TestingSession()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    # ========================================================
    # 1. KIỂM THỬ MODULE TÀI KHOẢN & XÁC THỰC (AUTHENTICATION)
    # ========================================================
    def test_01_register_candidate_and_profile_creation(self):
        """Đăng ký tài khoản Sinh viên: tự động tạo hồ sơ ứng viên tương ứng"""
        res = client.post("/api/auth/register", json={
            "email": "candidate_test1@ptit.edu.vn",
            "password": "password123",
            "role": "CANDIDATE",
            "full_name": "Nguyễn Văn An"
        })
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["email"], "candidate_test1@ptit.edu.vn")
        self.assertEqual(data["role"], "CANDIDATE")
        self.assertTrue(data["is_active"])

        # Kiểm tra bản ghi candidate đã được tạo trong DB
        candidate = self.db.query(Candidate).filter(Candidate.candidate_id == data["user_id"]).first()
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.full_name, "Nguyễn Văn An")

    def test_02_register_employer_and_company_creation(self):
        """Đăng ký tài khoản Nhà tuyển dụng: tự động tạo hồ sơ công ty tương ứng"""
        res = client.post("/api/auth/register", json={
            "email": "hr_test1@innovate.vn",
            "password": "password123",
            "role": "EMPLOYER",
            "company_name": "Innovate Việt Nam"
        })
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["role"], "EMPLOYER")

        # Kiểm tra công ty tương ứng đã được tạo
        company = self.db.query(Company).filter(Company.employer_id == data["user_id"]).first()
        self.assertIsNotNone(company)
        self.assertEqual(company.company_name, "Innovate Việt Nam")

    def test_03_register_duplicate_email_rejected(self):
        """Từ chối đăng ký trùng email đã tồn tại trong hệ thống (HTTP 400)"""
        res = client.post("/api/auth/register", json={
            "email": "candidate_test1@ptit.edu.vn",
            "password": "password999",
            "role": "CANDIDATE"
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("đã được đăng ký", res.json()["detail"])

    def test_04_login_success_and_role_token(self):
        """Đăng nhập thành công trả về thông tin người dùng và phiên truy cập"""
        res = client.post("/api/auth/login", json={
            "email": "candidate_test1@ptit.edu.vn",
            "password": "password123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["role"], "CANDIDATE")

    def test_05_login_wrong_password_rejected(self):
        """Đăng nhập sai mật khẩu bị từ chối (HTTP 401)"""
        res = client.post("/api/auth/login", json={
            "email": "candidate_test1@ptit.edu.vn",
            "password": "wrongpassword"
        })
        self.assertEqual(res.status_code, 401)

    # ========================================================
    # 2. KIỂM THỬ MODULE HỒ SƠ ỨNG VIÊN (CANDIDATE PROFILE)
    # ========================================================
    def test_06_candidate_profile_view_and_update(self):
        """Ứng viên xem và cập nhật hồ sơ cá nhân, kỹ năng và trường học"""
        user = self.db.query(User).filter(User.email == "candidate_test1@ptit.edu.vn").first()
        self.assertIsNotNone(user)

        # Xem hồ sơ
        res_get = client.get(f"/api/candidates/profile?user_id={user.user_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["full_name"], "Nguyễn Văn An")

        # Cập nhật hồ sơ
        res_put = client.put(f"/api/candidates/profile?user_id={user.user_id}", json={
            "full_name": "Nguyễn Văn An (Updated)",
            "phone": "0987654321",
            "university": "PTIT TP.HCM",
            "major": "Kỹ thuật Phần mềm",
            "skills": "Python, FastAPI, RESTful API, Docker, MySQL",
            "bio": "Sinh viên đam mê phát triển hệ thống backend",
            "cv_url": "https://unicareer.vn/cv/nguyenvanan.pdf"
        })
        self.assertEqual(res_put.status_code, 200)
        updated_data = res_put.json()
        self.assertEqual(updated_data["full_name"], "Nguyễn Văn An (Updated)")
        self.assertEqual(updated_data["phone"], "0987654321")
        self.assertEqual(updated_data["skills"], "Python, FastAPI, RESTful API, Docker, MySQL")

    # ========================================================
    # 3. KIỂM THỬ MODULE DOANH NGHIỆP & VIỆC LÀM (COMPANY & JOBS)
    # ========================================================
    def test_07_employer_create_and_manage_jobs(self):
        """Nhà tuyển dụng tạo và quản lý tin tuyển dụng của công ty mình"""
        emp_user = self.db.query(User).filter(User.email == "hr_test1@innovate.vn").first()
        company = self.db.query(Company).filter(Company.employer_id == emp_user.user_id).first()

        # Tạo tin tuyển dụng 1: Backend Developer
        res_job1 = client.post("/api/jobs", json={
            "company_id": company.company_id,
            "title": "Backend Python Developer Intern",
            "description": "Lập trình backend với FastAPI và cơ sở dữ liệu quan hệ.",
            "requirements": "Thành thạo Python, nắm vững cấu trúc dữ liệu và giải thuật.",
            "location": "TP. Hồ Chí Minh",
            "salary_range": "4–6 triệu/tháng",
            "job_type": "INTERNSHIP",
            "deadline": str(date.today() + timedelta(days=20)),
            "status": "ACTIVE",
            "approval_status": "APPROVED"
        })
        self.assertEqual(res_job1.status_code, 201)
        job1_data = res_job1.json()
        self.assertEqual(job1_data["title"], "Backend Python Developer Intern")

        # Tạo tin tuyển dụng 2: Đang chờ duyệt (PENDING)
        res_job2 = client.post("/api/jobs", json={
            "company_id": company.company_id,
            "title": "AI Research Assistant Intern",
            "description": "Nghiên cứu ứng dụng mô hình ngôn ngữ lớn.",
            "requirements": "Kiến thức về Machine Learning, Python PyTorch.",
            "location": "Hà Nội",
            "salary_range": "5–8 triệu/tháng",
            "job_type": "INTERNSHIP",
            "deadline": str(date.today() + timedelta(days=30)),
            "status": "ACTIVE",
            "approval_status": "PENDING"
        })
        self.assertEqual(res_job2.status_code, 201)

    def test_08_job_search_and_filtering(self):
        """Tìm kiếm và lọc việc làm theo từ khóa và địa điểm"""
        # Tìm theo từ khóa "Python"
        res_search = client.get("/api/jobs?search=Python")
        self.assertEqual(res_search.status_code, 200)
        jobs = res_search.json()
        self.assertTrue(len(jobs) >= 1)
        self.assertTrue(any("Python" in j["title"] for j in jobs))

        # Lọc theo địa điểm
        res_loc = client.get("/api/jobs?location=TP. Hồ Chí Minh")
        self.assertEqual(res_loc.status_code, 200)
        self.assertTrue(len(res_loc.json()) >= 1)

    # ========================================================
    # 4. KIỂM THỬ LIÊN KẾT ỨNG TUYỂN (APPLICATION WORKFLOW)
    # ========================================================
    def test_09_candidate_apply_job_success(self):
        """Ứng viên nộp hồ sơ ứng tuyển vào tin tuyển dụng đang mở và được duyệt"""
        candidate_user = self.db.query(User).filter(User.email == "candidate_test1@ptit.edu.vn").first()
        job = self.db.query(JobPost).filter(JobPost.title == "Backend Python Developer Intern").first()

        res_apply = client.post(f"/api/candidates/apply?user_id={candidate_user.user_id}", json={
            "job_id": job.job_id,
            "candidate_id": candidate_user.user_id,
            "cover_letter": "Em mong muốn được đóng góp và học hỏi tại công ty."
        })
        self.assertEqual(res_apply.status_code, 201)
        app_data = res_apply.json()
        self.assertEqual(app_data["status"], "RECEIVED")
        self.assertIsNotNone(app_data["ai_match_score"])

    def test_10_candidate_duplicate_apply_rejected(self):
        """Ràng buộc nghiệp vụ: Ứng viên không được nộp trùng đơn cho cùng 1 tin (HTTP 400)"""
        candidate_user = self.db.query(User).filter(User.email == "candidate_test1@ptit.edu.vn").first()
        job = self.db.query(JobPost).filter(JobPost.title == "Backend Python Developer Intern").first()

        res_dup = client.post(f"/api/candidates/apply?user_id={candidate_user.user_id}", json={
            "job_id": job.job_id,
            "candidate_id": candidate_user.user_id
        })
        self.assertEqual(res_dup.status_code, 400)
        self.assertIn("đã nộp hồ sơ ứng tuyển", res_dup.json()["detail"])

    def test_11_candidate_view_my_applications(self):
        """Ứng viên theo dõi danh sách các đơn đã nộp và trạng thái xử lý"""
        candidate_user = self.db.query(User).filter(User.email == "candidate_test1@ptit.edu.vn").first()
        res = client.get(f"/api/candidates/applications?user_id={candidate_user.user_id}")
        self.assertEqual(res.status_code, 200)
        my_apps = res.json()
        self.assertEqual(len(my_apps), 1)
        self.assertEqual(my_apps[0]["job_title"], "Backend Python Developer Intern")
        self.assertEqual(my_apps[0]["company_name"], "Innovate Việt Nam")

    def test_12_employer_view_and_update_application_status(self):
        """Nhà tuyển dụng xem danh sách ứng viên nộp hồ sơ và cập nhật trạng thái đơn"""
        emp_user = self.db.query(User).filter(User.email == "hr_test1@innovate.vn").first()
        company = self.db.query(Company).filter(Company.employer_id == emp_user.user_id).first()

        # 1. Doanh nghiệp xem danh sách ứng viên
        res_apps = client.get(f"/api/companies/{company.company_id}/applications")
        self.assertEqual(res_apps.status_code, 200)
        apps = res_apps.json()
        self.assertEqual(len(apps), 1)
        target_app = apps[0]
        self.assertEqual(target_app["status"], "RECEIVED")
        self.assertEqual(target_app["candidate_name"], "Nguyễn Văn An (Updated)")

        # 2. Cập nhật trạng thái sang REVIEWING (Đang xem xét)
        res_st1 = client.put(
            f"/api/companies/{company.company_id}/applications/{target_app['application_id']}/status",
            json={"status": "REVIEWING"}
        )
        self.assertEqual(res_st1.status_code, 200)
        self.assertEqual(res_st1.json()["status"], "REVIEWING")

        # 3. Cập nhật trạng thái sang ACCEPTED (Đã chấp nhận)
        res_st2 = client.put(
            f"/api/companies/{company.company_id}/applications/{target_app['application_id']}/status",
            json={"status": "ACCEPTED"}
        )
        self.assertEqual(res_st2.status_code, 200)
        self.assertEqual(res_st2.json()["status"], "ACCEPTED")

    # ========================================================
    # 5. KIỂM THỬ MODULE QUẢN TRỊ & KIỂM DUYỆT (ADMIN MODULE)
    # ========================================================
    def test_13_admin_system_overview_stats(self):
        """Quản trị viên xem số liệu thống kê tổng hợp toàn hệ thống"""
        res = client.get("/api/admin/stats")
        self.assertEqual(res.status_code, 200)
        stats = res.json()
        self.assertTrue(stats["total_users"] >= 2)
        self.assertTrue(stats["candidate_count"] >= 1)
        self.assertTrue(stats["employer_count"] >= 1)
        self.assertTrue(stats["total_jobs"] >= 2)
        self.assertTrue(stats["total_applications"] >= 1)

    def test_14_admin_job_moderation_flow(self):
        """Quản trị viên kiểm duyệt tin: duyệt (APPROVED) tin PENDING"""
        pending_job = self.db.query(JobPost).filter(JobPost.approval_status == "PENDING").first()
        self.assertIsNotNone(pending_job)

        # Phê duyệt tin
        res_appr = client.put(f"/api/admin/jobs/{pending_job.job_id}/approval", json={
            "approval_status": "APPROVED"
        })
        self.assertEqual(res_appr.status_code, 200)
        self.assertEqual(res_appr.json()["approval_status"], "APPROVED")

    def test_15_admin_lock_and_unlock_user(self):
        """Quản trị viên khóa tài khoản vi phạm và ngăn đăng nhập"""
        candidate_user = self.db.query(User).filter(User.email == "candidate_test1@ptit.edu.vn").first()

        # 1. Khóa tài khoản
        res_lock = client.put(f"/api/admin/users/{candidate_user.user_id}/status", json={
            "is_active": False
        })
        self.assertEqual(res_lock.status_code, 200)
        self.assertFalse(res_lock.json()["is_active"])

        # 2. Người dùng bị khóa không thể đăng nhập (HTTP 403)
        res_login_blocked = client.post("/api/auth/login", json={
            "email": "candidate_test1@ptit.edu.vn",
            "password": "password123"
        })
        self.assertEqual(res_login_blocked.status_code, 403)
        self.assertIn("đã bị khóa", res_login_blocked.json()["detail"])

        # 3. Mở khóa tài khoản trở lại
        res_unlock = client.put(f"/api/admin/users/{candidate_user.user_id}/status", json={
            "is_active": True
        })
        self.assertEqual(res_unlock.status_code, 200)
        self.assertTrue(res_unlock.json()["is_active"])

        # 4. Người dùng đăng nhập bình thường sau khi mở khóa
        res_login_ok = client.post("/api/auth/login", json={
            "email": "candidate_test1@ptit.edu.vn",
            "password": "password123"
        })
        self.assertEqual(res_login_ok.status_code, 200)


if __name__ == "__main__":
    unittest.main()
