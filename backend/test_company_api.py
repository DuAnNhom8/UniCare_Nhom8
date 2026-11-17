"""
Kiểm thử tự động API Chức năng Doanh nghiệp (T85FE99)
Dự án UniCareer - Nhóm 8
Sử dụng SQLite in-memory để kiểm thử độc lập, không phụ thuộc CSDL bên ngoài.
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Thêm đường dẫn project vào sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import Base, get_db
from backend.app.models import User, Company, JobPost
from backend.app.main import app

from sqlalchemy.pool import StaticPool

# Sử dụng SQLite bộ nhớ tạm cho môi trường test (StaticPool để chia sẻ bộ nhớ trên cùng engine)
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

class TestCompanyAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Tạo bảng trong SQLite test DB
        Base.metadata.create_all(bind=engine)
        
        # Thêm User mẫu nhà tuyển dụng
        db = TestingSessionLocal()
        user1 = User(user_id=2, email="hr@technova.com", password_hash="secret", role="EMPLOYER")
        user2 = User(user_id=3, email="hr@fpt.com", password_hash="secret", role="EMPLOYER")
        db.add_all([user1, user2])
        db.commit()
        db.close()

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=engine)

    def test_01_root_and_health(self):
        """Kiểm tra server root và health endpoints"""
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("UniCareer", res.json()["project"])

        res_health = client.get("/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json()["status"], "ok")

    def test_02_create_company(self):
        """Kiểm tra chức năng Tạo mới thông tin doanh nghiệp (POST /api/companies)"""
        payload = {
            "employer_id": 2,
            "company_name": "TechNova Solutions",
            "description": "Chuyên cung cấp giải pháp công nghệ tiên tiến.",
            "website": "https://technova.vn",
            "industry": "Công nghệ thông tin",
            "location": "TP. Hồ Chí Minh"
        }
        response = client.post("/api/companies", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["company_name"], "TechNova Solutions")
        self.assertEqual(data["employer_id"], 2)
        self.assertEqual(data["location"], "TP. Hồ Chí Minh")
        self.assertIn("company_id", data)

    def test_03_create_duplicate_company_fails(self):
        """Kiểm tra ràng buộc: một nhà tuyển dụng không được tạo 2 công ty"""
        payload = {
            "employer_id": 2,
            "company_name": "TechNova Chi nhánh 2",
            "description": "Chi nhánh phụ",
            "website": "https://technova2.vn"
        }
        response = client.post("/api/companies", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("đã có hồ sơ doanh nghiệp", response.json()["detail"])

    def test_04_get_company_by_id(self):
        """Kiểm tra chức năng Xem chi tiết doanh nghiệp theo ID (GET /api/companies/{id})"""
        response = client.get("/api/companies/1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["company_id"], 1)
        self.assertEqual(data["company_name"], "TechNova Solutions")

    def test_05_get_company_by_employer(self):
        """Kiểm tra chức năng Xem thông tin doanh nghiệp theo Employer ID (GET /api/companies/by-employer/{id})"""
        response = client.get("/api/companies/by-employer/2")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["company_id"], 1)
        self.assertEqual(data["employer_id"], 2)

    def test_06_get_companies_list(self):
        """Kiểm tra chức năng Xem danh sách doanh nghiệp có phân trang & tìm kiếm (GET /api/companies)"""
        # Tạo thêm 1 công ty thứ 2
        payload2 = {
            "employer_id": 3,
            "company_name": "FPT Software",
            "industry": "Phần mềm & Viễn thông",
            "website": "https://fpt-software.com",
            "location": "Hà Nội"
        }
        client.post("/api/companies", json=payload2)

        # Lấy toàn bộ danh sách
        response = client.get("/api/companies")
        self.assertEqual(response.status_code, 200)
        companies = response.json()
        self.assertEqual(len(companies), 2)

        # Tìm kiếm theo từ khóa
        res_search = client.get("/api/companies?keyword=TechNova")
        self.assertEqual(res_search.status_code, 200)
        self.assertEqual(len(res_search.json()), 1)
        self.assertEqual(res_search.json()[0]["company_name"], "TechNova Solutions")

    def test_07_update_company(self):
        """Kiểm tra chức năng Cập nhật thông tin doanh nghiệp (PUT /api/companies/{id})"""
        update_payload = {
            "company_name": "TechNova Global Corporation",
            "location": "Khu Công nghệ cao, TP. Thủ Đức, TP.HCM",
            "description": "Tập đoàn công nghệ hàng đầu khu vực."
        }
        response = client.put("/api/companies/1", json=update_payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["company_name"], "TechNova Global Corporation")
        self.assertEqual(data["location"], "Khu Công nghệ cao, TP. Thủ Đức, TP.HCM")
        self.assertEqual(data["description"], "Tập đoàn công nghệ hàng đầu khu vực.")
        # Các trường không update phải được giữ nguyên
        self.assertEqual(data["website"], "https://technova.vn")

    def test_08_current_profile_endpoints(self):
        """Kiểm tra endpoints tiện ích cho giao diện web (/api/companies/profile/current)"""
        res_get = client.get("/api/companies/profile/current?employer_id=2")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["company_name"], "TechNova Global Corporation")

        res_put = client.put(
            "/api/companies/profile/current?employer_id=2",
            json={"website": "https://technova.global"}
        )
        self.assertEqual(res_put.status_code, 200)
        self.assertEqual(res_put.json()["website"], "https://technova.global")

    def test_09_delete_company(self):
        """Kiểm tra chức năng Xóa doanh nghiệp (DELETE /api/companies/{id})"""
        res = client.delete("/api/companies/2")
        self.assertEqual(res.status_code, 200)
        
        # Kiểm tra đã bị xóa
        res_get = client.get("/api/companies/2")
        self.assertEqual(res_get.status_code, 404)

if __name__ == "__main__":
    unittest.main()
