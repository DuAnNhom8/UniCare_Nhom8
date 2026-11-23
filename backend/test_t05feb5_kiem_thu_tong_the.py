"""
BỘ KIỂM THỬ TỔNG THỂ TOÀN BỘ CÁC LUỒNG HỆ THỐNG UNICAREER
Dự án: UniCareer - Nhóm 8
Mã Task: T05FEB5
Mô tả Task: Chạy thử các luồng chính từ đăng nhập đến ứng tuyển và quản trị
Người thực hiện: Đỗ Hoàng Sơn (TV2 - PTIT-HCM-066)

Nội dung kiểm thử bao quát toàn bộ 6 kịch bản chính:
1. Luồng Xác thực & Phân quyền người dùng (CANDIDATE, EMPLOYER, ADMIN)
2. Luồng Hồ sơ sinh viên & Quản lý kỹ năng / CV
3. Luồng Quản lý tin tuyển dụng của Doanh nghiệp (Tạo, sửa, đóng/ẩn)
4. Luồng Tìm kiếm, lọc và xem chi tiết việc làm của Sinh viên
5. Luồng Ứng tuyển & Xử lý đơn ứng tuyển 2 chiều (Sinh viên - Nhà tuyển dụng)
6. Luồng Quản trị hệ thống, Kiểm duyệt tin và Quản lý người dùng của Admin
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

# Sử dụng SQLite In-Memory độc lập với StaticPool để đảm bảo môi trường kiểm thử cách ly hoàn toàn
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


class TestOverallSystemFlowsT05FEB5(unittest.TestCase):
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

    # =========================================================================
    # KỊCH BẢN 1: LUỒNG XÁC THỰC, ĐĂNG KÝ VÀ PHÂN QUYỀN TRUY CẬP
    # =========================================================================
    def test_01_flow_register_candidate_and_profile_init(self):
        """TC01: Đăng ký tài khoản Sinh viên mới -> Hệ thống tự động khởi tạo hồ sơ Candidate"""
        res = client.post("/api/auth/register", json={
            "email": "student_t05feb5@ptit.edu.vn",
            "password": "Password@123",
            "role": "CANDIDATE",
            "full_name": "Đỗ Hoàng Sơn"
        })
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["email"], "student_t05feb5@ptit.edu.vn")
        self.assertEqual(data["role"], "CANDIDATE")
        self.assertTrue(data["is_active"])

        # Xác thực bản ghi tương ứng trong CSDL
        cand = self.db.query(Candidate).filter(Candidate.candidate_id == data["user_id"]).first()
        self.assertIsNotNone(cand)
        self.assertEqual(cand.full_name, "Đỗ Hoàng Sơn")

    def test_02_flow_register_employer_and_company_init(self):
        """TC02: Đăng ký tài khoản Nhà tuyển dụng -> Hệ thống tự động tạo hồ sơ Company"""
        res = client.post("/api/auth/register", json={
            "email": "hr_t05feb5@technova.vn",
            "password": "Password@123",
            "role": "EMPLOYER",
            "company_name": "TechNova Corp"
        })
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["role"], "EMPLOYER")

        # Xác thực bản ghi doanh nghiệp trong CSDL
        comp = self.db.query(Company).filter(Company.employer_id == data["user_id"]).first()
        self.assertIsNotNone(comp)
        self.assertEqual(comp.company_name, "TechNova Corp")

    def test_03_flow_login_and_token_generation(self):
        """TC03: Đăng nhập hệ thống thành công -> Cấp Bearer Token và trả về đúng vai trò"""
        res = client.post("/api/auth/login", json={
            "email": "student_t05feb5@ptit.edu.vn",
            "password": "Password@123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["user"]["role"], "CANDIDATE")

    def test_04_flow_login_validation_and_security(self):
        """TC04: Kiểm tra bảo mật đăng nhập: từ chối sai mật khẩu và từ chối email trùng lặp"""
        # Sai mật khẩu
        res_fail = client.post("/api/auth/login", json={
            "email": "student_t05feb5@ptit.edu.vn",
            "password": "WrongPassword"
        })
        self.assertEqual(res_fail.status_code, 401)

        # Trùng email đăng ký
        res_dup = client.post("/api/auth/register", json={
            "email": "student_t05feb5@ptit.edu.vn",
            "password": "Password@123",
            "role": "CANDIDATE"
        })
        self.assertEqual(res_dup.status_code, 400)
        self.assertIn("đã được đăng ký", res_dup.json()["detail"])

    # =========================================================================
    # KỊCH BẢN 2: LUỒNG HỒ SƠ SINH VIÊN, KỸ NĂNG VÀ CV
    # =========================================================================
    def test_05_flow_candidate_profile_view_and_update(self):
        """TC05: Sinh viên xem và cập nhật hồ sơ cá nhân, trường học, chuyên ngành và kỹ năng"""
        user = self.db.query(User).filter(User.email == "student_t05feb5@ptit.edu.vn").first()
        self.assertIsNotNone(user)

        # Xem hồ sơ
        res_get = client.get(f"/api/candidates/profile?user_id={user.user_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["full_name"], "Đỗ Hoàng Sơn")

        # Cập nhật hồ sơ đầy đủ
        res_put = client.put(f"/api/candidates/profile?user_id={user.user_id}", json={
            "full_name": "Đỗ Hoàng Sơn (Fullstack Intern)",
            "phone": "0912345678",
            "university": "Học viện Công nghệ Bưu chính Viễn thông (PTIT)",
            "major": "Công nghệ Thông tin",
            "skills": "Python, FastAPI, MySQL, HTML5/CSS3, JavaScript, Git",
            "bio": "Sinh viên năm cuối nhiệt huyết, đam mê phát triển hệ thống web tối ưu.",
            "cv_url": "https://unicareer.vn/cv/dohoangson.pdf"
        })
        self.assertEqual(res_put.status_code, 200)
        p = res_put.json()
        self.assertEqual(p["full_name"], "Đỗ Hoàng Sơn (Fullstack Intern)")
        self.assertEqual(p["phone"], "0912345678")
        self.assertEqual(p["university"], "Học viện Công nghệ Bưu chính Viễn thông (PTIT)")
        self.assertIn("Python, FastAPI", p["skills"])

    # =========================================================================
    # KỊCH BẢN 3: LUỒNG DOANH NGHIỆP ĐĂNG TIN VÀ QUẢN TRỊ TIN TUYỂN DỤNG
    # =========================================================================
    def test_06_flow_employer_post_and_manage_job(self):
        """TC06: Doanh nghiệp đăng tin tuyển dụng mới và quản lý vòng đời tin"""
        hr_user = self.db.query(User).filter(User.email == "hr_t05feb5@technova.vn").first()
        comp = self.db.query(Company).filter(Company.employer_id == hr_user.user_id).first()

        # Đăng tin tuyển dụng 1 (Đã duyệt)
        res_job1 = client.post("/api/jobs", json={
            "company_id": comp.company_id,
            "title": "Backend Python Developer Intern",
            "description": "Tham gia phát triển API và dịch vụ backend cho nền tảng UniCareer.",
            "requirements": "Kiến thức tốt về Python, FastAPI, SQL và tư duy giải thuật.",
            "location": "TP. Hồ Chí Minh",
            "salary_range": "4–6 triệu/tháng",
            "job_type": "INTERNSHIP",
            "deadline": str(date.today() + timedelta(days=25)),
            "status": "ACTIVE",
            "approval_status": "APPROVED"
        })
        self.assertEqual(res_job1.status_code, 201)
        job1 = res_job1.json()
        self.assertEqual(job1["title"], "Backend Python Developer Intern")
        self.assertEqual(job1["status"], "ACTIVE")

        # Đăng tin tuyển dụng 2 (Hàng đợi kiểm duyệt PENDING)
        res_job2 = client.post("/api/jobs", json={
            "company_id": comp.company_id,
            "title": "Data Analyst Intern",
            "description": "Thu thập và phân tích dữ liệu ứng tuyển.",
            "requirements": "SQL, Python pandas, PowerBI.",
            "location": "Hà Nội",
            "salary_range": "3–5 triệu/tháng",
            "job_type": "INTERNSHIP",
            "deadline": str(date.today() + timedelta(days=20)),
            "status": "ACTIVE",
            "approval_status": "PENDING"
        })
        self.assertEqual(res_job2.status_code, 201)

        # Cập nhật thông tin tin tuyển dụng 1
        res_update = client.put(f"/api/jobs/{job1['job_id']}", json={
            "salary_range": "5–7 triệu/tháng"
        })
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.json()["salary_range"], "5–7 triệu/tháng")

    # =========================================================================
    # KỊCH BẢN 4: LUỒNG TÌM KIẾM, LỌC VÀ XEM CHI TIẾT VIỆC LÀM
    # =========================================================================
    def test_07_flow_job_search_and_detail(self):
        """TC07: Sinh viên tìm kiếm việc làm theo từ khóa, địa điểm và xem chi tiết công việc"""
        # Tìm kiếm theo từ khóa "Backend"
        res_search = client.get("/api/jobs?search=Backend")
        self.assertEqual(res_search.status_code, 200)
        jobs = res_search.json()
        self.assertTrue(len(jobs) >= 1)
        self.assertIn("Backend", jobs[0]["title"])

        # Lọc theo địa điểm "TP. Hồ Chí Minh"
        res_loc = client.get("/api/jobs?location=TP. Hồ Chí Minh")
        self.assertEqual(res_loc.status_code, 200)
        self.assertTrue(len(res_loc.json()) >= 1)

        # Xem chi tiết tin tuyển dụng
        job_id = jobs[0]["job_id"]
        res_detail = client.get(f"/api/jobs/{job_id}")
        self.assertEqual(res_detail.status_code, 200)
        self.assertEqual(res_detail.json()["job_id"], job_id)
        self.assertIn("Python", res_detail.json()["requirements"])

    # =========================================================================
    # KỊCH BẢN 5: LUỒNG ỨNG TUYỂN VÀ QUẢN LÝ ĐƠN ỨNG TUYỂN END-TO-END
    # =========================================================================
    def test_08_flow_application_submission_and_rules(self):
        """TC08: Sinh viên nộp đơn ứng tuyển, kiểm tra điểm AI và ràng buộc chống nộp trùng"""
        cand_user = self.db.query(User).filter(User.email == "student_t05feb5@ptit.edu.vn").first()
        job = self.db.query(JobPost).filter(JobPost.title == "Backend Python Developer Intern").first()

        # 1. Nộp đơn lần đầu thành công
        res_apply = client.post(f"/api/candidates/apply?user_id={cand_user.user_id}", json={
            "job_id": job.job_id,
            "candidate_id": cand_user.user_id,
            "cover_letter": "Em rất yêu thích môi trường làm việc tại TechNova và có định hướng phát triển backend lâu dài."
        })
        self.assertEqual(res_apply.status_code, 201)
        app_data = res_apply.json()
        self.assertEqual(app_data["status"], "RECEIVED")
        self.assertTrue(app_data["ai_match_score"] >= 80)

        # 2. Ràng buộc: Thử nộp trùng lần 2 cho cùng 1 tin -> Bị từ chối HTTP 400
        res_dup = client.post(f"/api/candidates/apply?user_id={cand_user.user_id}", json={
            "job_id": job.job_id,
            "candidate_id": cand_user.user_id
        })
        self.assertEqual(res_dup.status_code, 400)
        self.assertIn("đã nộp hồ sơ ứng tuyển", res_dup.json()["detail"])

    def test_09_flow_candidate_tracks_application_history(self):
        """TC09: Sinh viên theo dõi lịch sử và trạng thái các đơn ứng tuyển cá nhân"""
        cand_user = self.db.query(User).filter(User.email == "student_t05feb5@ptit.edu.vn").first()
        res_apps = client.get(f"/api/candidates/applications?user_id={cand_user.user_id}")
        self.assertEqual(res_apps.status_code, 200)
        apps = res_apps.json()
        self.assertEqual(len(apps), 1)
        self.assertEqual(apps[0]["job_title"], "Backend Python Developer Intern")
        self.assertEqual(apps[0]["company_name"], "TechNova Corp")
        self.assertEqual(apps[0]["status"], "RECEIVED")

    def test_10_flow_employer_reviews_and_updates_application(self):
        """TC10: Nhà tuyển dụng xem danh sách ứng viên nộp hồ sơ và duyệt trạng thái đơn"""
        hr_user = self.db.query(User).filter(User.email == "hr_t05feb5@technova.vn").first()
        comp = self.db.query(Company).filter(Company.employer_id == hr_user.user_id).first()

        # Doanh nghiệp lấy danh sách hồ sơ nhận được
        res_comp_apps = client.get(f"/api/companies/{comp.company_id}/applications")
        self.assertEqual(res_comp_apps.status_code, 200)
        comp_apps = res_comp_apps.json()
        self.assertEqual(len(comp_apps), 1)
        app_item = comp_apps[0]
        self.assertEqual(app_item["candidate_name"], "Đỗ Hoàng Sơn (Fullstack Intern)")

        # Cập nhật trạng thái đơn sang REVIEWING (Đang xem xét)
        res_rev = client.put(
            f"/api/companies/{comp.company_id}/applications/{app_item['application_id']}/status",
            json={"status": "REVIEWING"}
        )
        self.assertEqual(res_rev.status_code, 200)
        self.assertEqual(res_rev.json()["status"], "REVIEWING")

        # Cập nhật trạng thái đơn sang ACCEPTED (Đã chấp nhận)
        res_acc = client.put(
            f"/api/companies/{comp.company_id}/applications/{app_item['application_id']}/status",
            json={"status": "ACCEPTED"}
        )
        self.assertEqual(res_acc.status_code, 200)
        self.assertEqual(res_acc.json()["status"], "ACCEPTED")

        # Xác thực phía ứng viên thấy trạng thái cập nhật tức thời
        cand_user = self.db.query(User).filter(User.email == "student_t05feb5@ptit.edu.vn").first()
        cand_apps = client.get(f"/api/candidates/applications?user_id={cand_user.user_id}").json()
        self.assertEqual(cand_apps[0]["status"], "ACCEPTED")

    # =========================================================================
    # KỊCH BẢN 6: LUỒNG QUẢN TRỊ HỆ THỐNG, KIỂM DUYỆT VÀ QUẢN LÝ NGƯỜI DÙNG
    # =========================================================================
    def test_11_flow_admin_system_dashboard_metrics(self):
        """TC11: Quản trị viên truy xuất số liệu thống kê tổng thể toàn hệ thống"""
        res_stats = client.get("/api/admin/stats")
        self.assertEqual(res_stats.status_code, 200)
        stats = res_stats.json()
        self.assertTrue(stats["total_users"] >= 2)
        self.assertTrue(stats["candidate_count"] >= 1)
        self.assertTrue(stats["employer_count"] >= 1)
        self.assertTrue(stats["company_count"] >= 1)
        self.assertTrue(stats["total_jobs"] >= 2)
        self.assertTrue(stats["total_applications"] >= 1)

    def test_12_flow_admin_job_moderation(self):
        """TC12: Quản trị viên kiểm duyệt tin tuyển dụng trong hàng đợi (PENDING -> APPROVED)"""
        pending_job = self.db.query(JobPost).filter(JobPost.approval_status == "PENDING").first()
        self.assertIsNotNone(pending_job)

        # Admin duyệt tin
        res_appr = client.put(f"/api/admin/jobs/{pending_job.job_id}/approval", json={
            "approval_status": "APPROVED"
        })
        self.assertEqual(res_appr.status_code, 200)
        self.assertEqual(res_appr.json()["approval_status"], "APPROVED")

        # Xác thực tin đã được công khai trong danh sách việc làm
        self.db.expire_all()
        db_job = self.db.query(JobPost).filter(JobPost.job_id == pending_job.job_id).first()
        self.assertEqual(db_job.approval_status, "APPROVED")

    def test_13_flow_admin_user_lock_and_unlock(self):
        """TC13: Quản trị viên khóa tài khoản vi phạm và khôi phục quyền truy cập"""
        cand_user = self.db.query(User).filter(User.email == "student_t05feb5@ptit.edu.vn").first()

        # 1. Khóa tài khoản
        res_lock = client.put(f"/api/admin/users/{cand_user.user_id}/status", json={"is_active": False})
        self.assertEqual(res_lock.status_code, 200)
        self.assertFalse(res_lock.json()["is_active"])

        # 2. Thử đăng nhập bằng tài khoản bị khóa -> Bị chặn với HTTP 403
        res_login_blocked = client.post("/api/auth/login", json={
            "email": "student_t05feb5@ptit.edu.vn",
            "password": "Password@123"
        })
        self.assertEqual(res_login_blocked.status_code, 403)
        self.assertIn("đã bị khóa", res_login_blocked.json()["detail"])

        # 3. Mở khóa lại tài khoản
        res_unlock = client.put(f"/api/admin/users/{cand_user.user_id}/status", json={"is_active": True})
        self.assertEqual(res_unlock.status_code, 200)
        self.assertTrue(res_unlock.json()["is_active"])

        # 4. Đăng nhập lại bình thường sau khi mở khóa
        res_login_ok = client.post("/api/auth/login", json={
            "email": "student_t05feb5@ptit.edu.vn",
            "password": "Password@123"
        })
        self.assertEqual(res_login_ok.status_code, 200)

    def test_14_flow_admin_protect_sole_admin(self):
        """TC14: Ràng buộc an toàn: Không cho phép khóa tài khoản Quản trị viên duy nhất"""
        # Tạo admin test
        admin_user = User(email="superadmin@unicareer.vn", password_hash="secret", role="ADMIN", is_active=True)
        self.db.add(admin_user)
        self.db.commit()

        # Khóa admin khi chỉ có 1 admin hoạt động -> Bị từ chối HTTP 400
        res_lock_admin = client.put(f"/api/admin/users/{admin_user.user_id}/status", json={"is_active": False})
        self.assertEqual(res_lock_admin.status_code, 400)
        self.assertIn("Không thể khóa tài khoản Quản trị viên duy nhất", res_lock_admin.json()["detail"])


if __name__ == "__main__":
    unittest.main()
