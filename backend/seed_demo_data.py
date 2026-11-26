#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script nạp dữ liệu mẫu ban đầu cho hệ thống UniCareer (Nhóm 8)
Tạo sẵn tài khoản Sinh viên, Nhà tuyển dụng, Quản trị viên và các tin tuyển dụng mẫu
"""

import sys
import os
from datetime import date, timedelta

# Đảm bảo import được app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app.models.role import RoleModel
from app.models.user import UserModel
from app.models.profile import ProfileModel
from app.models.company import CompanyModel
from app.models.job import JobModel
from app.models.cv import CVModel
from app.services.auth_service import seed_roles

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_roles(db)
        cand_role = db.query(RoleModel).filter(RoleModel.name == "candidate").first()
        emp_role = db.query(RoleModel).filter(RoleModel.name == "employer").first()
        admin_role = db.query(RoleModel).filter(RoleModel.name == "admin").first()

        # 1. Sinh viên (Candidate)
        student = db.query(UserModel).filter(UserModel.email == "sinhvien@ptit.edu.vn").first()
        if not student:
            student = UserModel(
                email="sinhvien@ptit.edu.vn",
                hashed_password=hash_password("password123"),
                role="candidate",
                is_active=True
            )
            student.roles.append(cand_role)
            student.profile = ProfileModel(
                full_name="Đỗ Hoàng Sơn",
                phone="0912345678",
                university="Học viện Công nghệ Bưu chính Viễn thông (PTIT)",
                major="Công nghệ Thông tin",
                bio="Sinh viên năm cuối đam mê phát triển hệ thống backend và giải pháp web tối ưu.",
                skills="Python, FastAPI, MySQL, HTML5/CSS3, JavaScript, Git"
            )
            db.add(student)
            db.commit()
            print("✅ Đã tạo tài khoản Sinh viên: sinhvien@ptit.edu.vn / password123")

        # 2. Nhà tuyển dụng (Employer)
        employer = db.query(UserModel).filter(UserModel.email == "hr@technova.example").first()
        if not employer:
            employer = UserModel(
                email="hr@technova.example",
                hashed_password=hash_password("password123"),
                role="employer",
                is_active=True
            )
            employer.roles.append(emp_role)
            employer.profile = ProfileModel(full_name="HR Manager (TechNova)")
            db.add(employer)
            db.commit()

            # Tạo công ty TechNova
            company = CompanyModel(
                employer_id=employer.id,
                company_name="TechNova Solutions",
                industry="Công nghệ thông tin / Phần mềm",
                website="https://technova.example",
                location="TP. Hồ Chí Minh",
                description="TechNova phát triển các giải pháp phần mềm và sản phẩm số cho doanh nghiệp."
            )
            db.add(company)
            db.commit()

            # Tạo tin tuyển dụng mẫu
            sample_jobs = [
                JobModel(
                    company_id=company.id,
                    title="Backend Developer Intern",
                    description="Tham gia phát triển backend và REST API với Python FastAPI và CSDL cho nền tảng UniCareer.",
                    requirements="Kiến thức Python cơ bản, hiểu biết về REST API, cơ sở dữ liệu quan hệ, tinh thần học hỏi cao.",
                    location="TP. Hồ Chí Minh",
                    salary_range="3–5 triệu/tháng",
                    job_type="INTERNSHIP",
                    experience_level="Không yêu cầu",
                    deadline=date.today() + timedelta(days=25),
                    status="ACTIVE",
                    approval_status="APPROVED"
                ),
                JobModel(
                    company_id=company.id,
                    title="Frontend Developer Intern",
                    description="Xây dựng giao diện web responsive hiện đại với HTML5, CSS3, JavaScript và kết nối API hệ thống.",
                    requirements="Thành thạo HTML/CSS/JS, có thẩm mỹ giao diện tốt, biết sử dụng Git căn bản.",
                    location="Hybrid (TP.HCM)",
                    salary_range="3–5 triệu/tháng",
                    job_type="INTERNSHIP",
                    experience_level="Không yêu cầu",
                    deadline=date.today() + timedelta(days=30),
                    status="ACTIVE",
                    approval_status="APPROVED"
                ),
                JobModel(
                    company_id=company.id,
                    title="Data Analyst Intern",
                    description="Thu thập, xử lý và phân tích dữ liệu tuyển dụng, hỗ trợ xây dựng dashboard báo cáo chuyên sâu.",
                    requirements="Kỹ năng SQL, Python pandas/numpy, tư duy phân tích số liệu tốt.",
                    location="Hà Nội",
                    salary_range="4–6 triệu/tháng",
                    job_type="INTERNSHIP",
                    experience_level="Không yêu cầu",
                    deadline=date.today() + timedelta(days=20),
                    status="ACTIVE",
                    approval_status="APPROVED"
                )
            ]
            db.add_all(sample_jobs)
            db.commit()
            print("✅ Đã tạo tài khoản Nhà tuyển dụng: hr@technova.example / password123")

        # 3. Quản trị viên (Admin)
        admin = db.query(UserModel).filter(UserModel.email == "admin@unicareer.vn").first()
        if not admin:
            admin = UserModel(
                email="admin@unicareer.vn",
                hashed_password=hash_password("admin123456"),
                role="admin",
                is_active=True
            )
            admin.roles.append(admin_role)
            admin.profile = ProfileModel(full_name="Quản trị viên Hệ thống")
            db.add(admin)
            db.commit()
            print("✅ Đã tạo tài khoản Quản trị viên: admin@unicareer.vn / admin123456")

        print("🎉 Khởi tạo dữ liệu mẫu hoàn tất!")
    finally:
        db.close()

if __name__ == "__main__":
    main()
