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


class TestCompanyAndJobManagementT05FEAD(unittest.TestCase):
    """
    Bộ kiểm thử chuẩn hóa cho Task T05FEAD:
    1. Kiểm tra tạo doanh nghiệp, cập nhật thông tin và xác thực ràng buộc.
    2. Kiểm tra quản lý tin tuyển dụng gắn với doanh nghiệp (tạo, cập nhật, đổi trạng thái, lọc).
    3. Kiểm tra kịch bản liên kết end-to-end giữa Doanh nghiệp và Tin tuyển dụng.
    """

    @classmethod
    def setUpClass(cls):
        """Khởi tạo schema và nạp dữ liệu mẫu ban đầu"""
        Base.metadata.create_all(bind=test_engine)
        db = TestingSession()
        try:
            # Tạo các tài khoản Employer phục vụ test
            employer1 = User(
                user_id=10,
                email="hr1@technova.vn",
                password_hash="hash_pw_10",
                role="EMPLOYER",
                is_active=True
            )
            employer2 = User(
                user_id=20,
                email="hr2@fptsoftware.vn",
                password_hash="hash_pw_20",
                role="EMPLOYER",
                is_active=True
            )
            employer3 = User(
                user_id=30,
                email="hr3@viettel.vn",
                password_hash="hash_pw_30",
                role="EMPLOYER",
                is_active=True
            )
            db.add_all([employer1, employer2, employer3])
            db.commit()
        finally:
            db.close()

    @classmethod
    def tearDownClass(cls):
        """Dọn dẹp môi trường database sau khi kiểm thử kết thúc"""
        Base.metadata.drop_all(bind=test_engine)

    # =========================================================================
    # PHẦN 1: KIỂM TRA CHỨC NĂNG DOANH NGHIỆP (TẠO, XEM, CẬP NHẬT, VALIDATION)
    # =========================================================================

    def test_01_create_company_success(self):
        """TC01: Kiểm tra tạo mới hồ sơ doanh nghiệp thành công (POST /api/companies)"""
        payload = {
            "employer_id": 10,
            "company_name": "Công ty Cổ phần Công nghệ TechNova",
            "industry": "Công nghệ thông tin",
            "website": "https://technova.vn",
            "location": "Tầng 5, Tòa nhà Innovation, TP. Hồ Chí Minh",
            "description": "Chuyên cung cấp giải pháp AI và phần mềm quản trị doanh nghiệp."
        }
        res = client.post("/api/companies", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("company_id", data)
        self.assertEqual(data["company_name"], payload["company_name"])
        self.assertEqual(data["employer_id"], 10)
        self.assertEqual(data["industry"], payload["industry"])

    def test_02_create_company_duplicate_employer_fails(self):
        """TC02: Kiểm tra ngăn chặn 1 tài khoản nhà tuyển dụng tạo nhiều hơn 1 doanh nghiệp"""
        payload = {
            "employer_id": 10,  # Đã tạo ở TC01
            "company_name": "TechNova Chi Nhánh 2",
            "industry": "IT"
        }
        res = client.post("/api/companies", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("detail", res.json())

    def test_03_create_second_company_success(self):
        """TC03: Kiểm tra tạo doanh nghiệp thứ 2 với employer_id khác thành công"""
        payload = {
            "employer_id": 20,
            "company_name": "FPT Software Toàn Cầu",
            "industry": "Phần mềm & Dịch vụ CNTT",
            "website": "https://fptsoftware.com",
            "location": "Khu Công nghệ cao, TP. Thủ Đức",
            "description": "Tập đoàn công nghệ hàng đầu Việt Nam."
        }
        res = client.post("/api/companies", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["employer_id"], 20)
        self.assertEqual(data["company_name"], payload["company_name"])

    def test_04_get_company_by_id(self):
        """TC04: Kiểm tra truy vấn chi tiết doanh nghiệp theo ID (GET /api/companies/{company_id})"""
        res = client.get("/api/companies/1")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["company_id"], 1)
        self.assertEqual(data["company_name"], "Công ty Cổ phần Công nghệ TechNova")

    def test_05_get_company_by_employer_id(self):
        """TC05: Kiểm tra truy vấn doanh nghiệp theo employer_id (GET /api/companies/by-employer/{employer_id})"""
        res = client.get("/api/companies/by-employer/20")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["employer_id"], 20)
        self.assertEqual(data["company_name"], "FPT Software Toàn Cầu")

    def test_06_get_company_not_found(self):
        """TC06: Kiểm tra truy vấn doanh nghiệp không tồn tại trả về mã lỗi 404"""
        res = client.get("/api/companies/9999")
        self.assertEqual(res.status_code, 404)

    def test_07_update_company_profile_success(self):
        """TC07: Kiểm tra cập nhật thông tin doanh nghiệp (PUT /api/companies/{company_id})"""
        update_payload = {
            "company_name": "TechNova Solutions & AI Global",
            "industry": "Trí tuệ nhân tạo & Điện toán đám mây",
            "website": "https://technova.ai",
            "location": "Tầng 12, Tòa nhà Bitexco, Q.1, TP.HCM",
            "description": "Mở rộng dịch vụ AI toàn cầu và đào tạo sinh viên tài năng."
        }
        res = client.put("/api/companies/1", json=update_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["company_name"], update_payload["company_name"])
        self.assertEqual(data["industry"], update_payload["industry"])
        self.assertEqual(data["website"], update_payload["website"])

    def test_08_list_companies_and_search(self):
        """TC08: Kiểm tra lấy danh sách doanh nghiệp và tìm kiếm theo từ khóa (GET /api/companies)"""
        # Tìm kiếm theo từ khóa 'FPT'
        res = client.get("/api/companies?keyword=FPT")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(len(data) >= 1)
        self.assertTrue(any("FPT" in c["company_name"] for c in data))

    # =========================================================================
    # PHẦN 2: KIỂM TRA QUẢN LÝ TIN TUYỂN DỤNG GẮN VỚI DOANH NGHIỆP
    # =========================================================================

    def test_09_create_job_for_company(self):
        """TC09: Kiểm tra tạo tin tuyển dụng gắn với doanh nghiệp thành công (POST /api/jobs)"""
        deadline_date = (date.today() + timedelta(days=30)).isoformat()
        payload = {
            "company_id": 1,
            "title": "Kỹ sư Trí tuệ Nhân tạo (AI Engineer)",
            "description": "Nghiên cứu và phát triển các mô hình học sâu (Deep Learning) và LLM.",
            "requirements": "Thành thạo Python, PyTorch/TensorFlow, tư duy toán tốt.",
            "location": "TP. Hồ Chí Minh",
            "salary_range": "15–25 triệu/tháng",
            "job_type": "FULL_TIME",
            "experience_level": "JUNIOR",
            "deadline": deadline_date,
            "status": "ACTIVE"
        }
        res = client.post("/api/jobs", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("job_id", data)
        self.assertEqual(data["company_id"], 1)
        self.assertEqual(data["title"], payload["title"])
        self.assertEqual(data["status"], "ACTIVE")

    def test_10_create_second_job_for_company(self):
        """TC10: Kiểm tra tạo thêm tin tuyển dụng dạng Thực tập sinh (POST /api/jobs)"""
        deadline_date = (date.today() + timedelta(days=45)).isoformat()
        payload = {
            "company_id": 1,
            "title": "Thực tập sinh Lập trình Web Fullstack",
            "description": "Tham gia hỗ trợ đội ngũ phát triển giao diện và API cho dự án UniCareer.",
            "requirements": "Biết HTML/CSS/JS, Python hoặc Node.js, chăm chỉ ham học hỏi.",
            "location": "Hybrid (Linh hoạt)",
            "salary_range": "4–7 triệu/tháng",
            "job_type": "INTERNSHIP",
            "experience_level": "INTERN",
            "deadline": deadline_date,
            "status": "ACTIVE"
        }
        res = client.post("/api/jobs", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["company_id"], 1)
        self.assertEqual(data["job_type"], "INTERNSHIP")

    def test_11_list_jobs_by_company(self):
        """TC11: Kiểm tra lấy danh sách tin tuyển dụng theo mã doanh nghiệp (GET /api/jobs?company_id=1)"""
        res = client.get("/api/jobs?company_id=1")
        self.assertEqual(res.status_code, 200)
        jobs = res.json()
        self.assertTrue(len(jobs) >= 2)
        for job in jobs:
            self.assertEqual(job["company_id"], 1)

    def test_12_update_job_details(self):
        """TC12: Kiểm tra cập nhật nội dung tin tuyển dụng (PUT /api/jobs/{job_id})"""
        update_data = {
            "title": "Kỹ sư Trí tuệ Nhân tạo Cao cấp (Senior AI Engineer)",
            "salary_range": "25–40 triệu/tháng",
            "description": "Dẫn dắt dự án phát triển mô hình gợi ý nghề nghiệp thông minh cho sinh viên."
        }
        res = client.put("/api/jobs/1", json=update_data)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["title"], update_data["title"])
        self.assertEqual(data["salary_range"], update_data["salary_range"])

    def test_13_close_job_status(self):
        """TC13: Kiểm tra đóng/ẩn tin tuyển dụng khi đã đủ ứng viên (PATCH /api/jobs/{job_id}/status)"""
        # Đóng tin tuyển dụng số 1
        res = client.patch("/api/jobs/1/status", json={"status": "CLOSED"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "CLOSED")

        # Xác thực trạng thái được lưu chính xác trong DB
        res_get = client.get("/api/jobs/1")
        self.assertEqual(res_get.json()["status"], "CLOSED")

    def test_14_filter_jobs_by_status(self):
        """TC14: Kiểm tra lọc danh sách tin tuyển dụng theo trạng thái (GET /api/jobs?status=CLOSED)"""
        res_closed = client.get("/api/jobs?status=CLOSED")
        self.assertEqual(res_closed.status_code, 200)
        closed_jobs = res_closed.json()
        self.assertTrue(all(j["status"] == "CLOSED" for j in closed_jobs))

        res_active = client.get("/api/jobs?status=ACTIVE")
        self.assertEqual(res_active.status_code, 200)
        active_jobs = res_active.json()
        self.assertTrue(all(j["status"] == "ACTIVE" for j in active_jobs))

    def test_15_reopen_job_status(self):
        """TC15: Kiểm tra kích hoạt mở lại tin tuyển dụng (PATCH /api/jobs/{job_id}/status -> ACTIVE)"""
        res = client.patch("/api/jobs/1/status", json={"status": "ACTIVE"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ACTIVE")

    # =========================================================================
    # PHẦN 3: KIỂM TRA LUỒNG TÍCH HỢP TOÀN TRÌNH (END-TO-END WORKFLOW)
    # =========================================================================

    def test_16_end_to_end_flow(self):
        """
        TC16: Kiểm thử luồng liên thông trọn vẹn:
        Tạo doanh nghiệp -> Đăng tin -> Chỉnh sửa tin -> Đóng tin -> Xóa tin.
        """
        # Bước 1: Tạo doanh nghiệp mới cho employer 30
        comp_res = client.post("/api/companies", json={
            "employer_id": 30,
            "company_name": "Tập đoàn Viettel Telecom",
            "industry": "Viễn thông & Dữ liệu lớn",
            "location": "Hà Nội"
        })
        self.assertEqual(comp_res.status_code, 201)
        comp_id = comp_res.json()["company_id"]

        # Bước 2: Đăng tin tuyển dụng cho Viettel
        job_res = client.post("/api/jobs", json={
            "company_id": comp_id,
            "title": "Chuyên viên Phân tích Dữ liệu Viễn thông",
            "description": "Phân tích hành vi thuê bao và lưu lượng mạng.",
            "requirements": "Thành thạo SQL, Python, hiểu biết về Big Data.",
            "location": "Hà Nội",
            "salary_range": "18–28 triệu/tháng",
            "status": "ACTIVE"
        })
        self.assertEqual(job_res.status_code, 201)
        job_id = job_res.json()["job_id"]

        # Bước 3: Cập nhật tin tuyển dụng
        update_res = client.put(f"/api/jobs/{job_id}", json={
            "salary_range": "20–30 triệu/tháng"
        })
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json()["salary_range"], "20–30 triệu/tháng")

        # Bước 4: Chuyển trạng thái sang HIDDEN
        hide_res = client.patch(f"/api/jobs/{job_id}/status", json={"status": "HIDDEN"})
        self.assertEqual(hide_res.status_code, 200)
        self.assertEqual(hide_res.json()["status"], "HIDDEN")

        # Bước 5: Xóa tin tuyển dụng và kiểm tra không còn tìm thấy
        del_res = client.delete(f"/api/jobs/{job_id}")
        self.assertEqual(del_res.status_code, 200)

        not_found_res = client.get(f"/api/jobs/{job_id}")
        self.assertEqual(not_found_res.status_code, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
