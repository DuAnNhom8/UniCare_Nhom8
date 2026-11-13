"""
Hệ thống Backend API - UniCareer (Nhóm 8)
Phân hệ Doanh nghiệp & Tuyển dụng (TV2)
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, SessionLocal
import backend.app.models  # Import all models for SQLAlchemy registry
from backend.app.models import User, Company, JobPost
from backend.app.routers import company, jobs
from datetime import date, timedelta

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Hệ thống API nền tảng hướng nghiệp & tuyển dụng UniCareer - Nhóm 8",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Cấu hình CORS để Frontend (HTML/JS) gọi API thuận tiện
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount thư mục frontend để chạy trực tiếp trên web server
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
if os.path.exists(frontend_path):
    app.mount("/frontend", StaticFiles(directory=frontend_path, html=True), name="frontend")

# Đăng ký các router phân hệ
app.include_router(company.router, prefix=settings.API_V1_STR)
app.include_router(jobs.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def on_startup():
    """Khởi tạo cấu trúc bảng CSDL và nạp dữ liệu khởi tạo mặc định nếu chưa có"""
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            # Tạo người dùng mẫu nếu chưa có
            employer_user = db.query(User).filter(User.user_id == 2).first()
            if not employer_user:
                employer_user = User(
                    user_id=2,
                    email="hr@technova.example",
                    password_hash="demo123",
                    role="EMPLOYER"
                )
                db.add(employer_user)
                db.commit()

            # Tạo công ty TechNova mẫu nếu chưa có
            company_obj = db.query(Company).filter(Company.company_id == 1).first()
            if not company_obj:
                company_obj = Company(
                    company_id=1,
                    employer_id=2,
                    company_name="TechNova",
                    industry="Công nghệ thông tin / Phần mềm",
                    website="https://technova.example",
                    location="TP. Hồ Chí Minh",
                    description="TechNova phát triển các giải pháp phần mềm và sản phẩm số cho doanh nghiệp."
                )
                db.add(company_obj)
                db.commit()

            # Tạo các tin tuyển dụng mẫu ban đầu nếu bảng đang rỗng
            jobs_count = db.query(JobPost).count()
            if jobs_count == 0:
                sample_jobs = [
                    JobPost(
                        job_id=1,
                        company_id=1,
                        title="Backend Developer Intern",
                        description="Tham gia phát triển backend và REST API với Python FastAPI và CSDL MySQL cho nền tảng UniCareer.",
                        requirements="Kiến thức Python cơ bản, hiểu biết về REST API, cơ sở dữ liệu quan hệ, tinh thần học hỏi cao.",
                        location="TP. Hồ Chí Minh",
                        salary_range="3–5 triệu/tháng",
                        job_type="INTERNSHIP",
                        experience_level="Không yêu cầu",
                        deadline=date.today() + timedelta(days=20),
                        status="ACTIVE",
                        approval_status="APPROVED"
                    ),
                    JobPost(
                        job_id=2,
                        company_id=1,
                        title="Frontend Developer Intern",
                        description="Xây dựng giao diện web responsive hiện đại với HTML5, CSS3, JavaScript và kết nối API hệ thống.",
                        requirements="Thành thạo HTML/CSS/JS, có thẩm mỹ giao diện tốt, biết sử dụng Git căn bản.",
                        location="Hybrid (TP.HCM)",
                        salary_range="3–5 triệu/tháng",
                        job_type="INTERNSHIP",
                        experience_level="Không yêu cầu",
                        deadline=date.today() + timedelta(days=25),
                        status="ACTIVE",
                        approval_status="APPROVED"
                    ),
                    JobPost(
                        job_id=3,
                        company_id=1,
                        title="Data Analyst Intern",
                        description="Thu thập, xử lý và phân tích dữ liệu tuyển dụng, hỗ trợ xây dựng dashboard báo cáo chuyên sâu.",
                        requirements="Kỹ năng SQL, Python pandas/numpy, tư duy phân tích số liệu tốt.",
                        location="Hà Nội",
                        salary_range="4–6 triệu/tháng",
                        job_type="INTERNSHIP",
                        experience_level="Không yêu cầu",
                        deadline=date.today() + timedelta(days=15),
                        status="ACTIVE",
                        approval_status="APPROVED"
                    ),
                    JobPost(
                        job_id=4,
                        company_id=1,
                        title="Business Analyst Intern",
                        description="Khảo sát quy trình nghiệp vụ tuyển dụng, viết tài liệu đặc tả yêu cầu SRS và hỗ trợ kiểm thử phần mềm.",
                        requirements="Kỹ năng giao tiếp tốt, tư duy logic, khả năng viết tài liệu URD/SRS.",
                        location="TP. Hồ Chí Minh",
                        salary_range="3–5 triệu/tháng",
                        job_type="INTERNSHIP",
                        experience_level="Không yêu cầu",
                        deadline=date.today() + timedelta(days=18),
                        status="ACTIVE",
                        approval_status="APPROVED"
                    )
                ]
                db.add_all(sample_jobs)
                db.commit()
        finally:
            db.close()
    except Exception as e:
        print(f"[Warning] Khởi tạo dữ liệu startup: {e}")

@app.get("/", tags=["Hệ thống"])
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
        "author": "UniCareer - Nhóm 8"
    }

@app.get("/health", tags=["Hệ thống"])
def health_check():
    return {"status": "ok"}
