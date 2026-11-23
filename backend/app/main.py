"""
Hệ thống Backend API - UniCareer (Nhóm 8)
Phân hệ Doanh nghiệp & Tuyển dụng (TV2)
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, SessionLocal
import backend.app.models  # Import all models for SQLAlchemy registry
from backend.app.models import User, Company, JobPost
from backend.app.routers import company, jobs, auth, candidate
from datetime import date, timedelta

@asynccontextmanager
async def lifespan(_app: FastAPI):
    on_startup()
    yield


# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Hệ thống API nền tảng hướng nghiệp & tuyển dụng UniCareer - Nhóm 8",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Frontend mở trên FastAPI cùng origin; hỗ trợ thêm Live Server dùng khi phát triển.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500",
                   "http://127.0.0.1:5501", "http://localhost:5501",
                   "http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=False,
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
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(candidate.router, prefix=settings.API_V1_STR)

def on_startup():
    """Khởi tạo cấu trúc bảng CSDL và nạp dữ liệu khởi tạo mặc định nếu chưa có"""
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            # Chỉ nạp dữ liệu minh họa khi toàn bộ CSDL thực sự trống.
            # Tránh tạo tài khoản/doanh nghiệp demo khi nhóm đã nhập dữ liệu thật.
            if (db.query(User).first() or db.query(Company).first() or db.query(JobPost).first()):
                return
            # Tạo người dùng mẫu nếu chưa có
            employer_user = db.query(User).filter(User.email == "hr@technova.example").first()
            if not employer_user:
                employer_user = User(
                    email="hr@technova.example",
                    password_hash="!demo-account-login-disabled",
                    role="EMPLOYER"
                )
                db.add(employer_user)
                db.commit()
                db.refresh(employer_user)

            # Không ghi đè doanh nghiệp khác nếu CSDL đã có dữ liệu.
            company_obj = db.query(Company).filter(Company.employer_id == employer_user.user_id).first()
            if not company_obj:
                company_obj = Company(
                    employer_id=employer_user.user_id,
                    company_name="TechNova",
                    industry="Công nghệ thông tin / Phần mềm",
                    website="https://technova.example",
                    location="TP. Hồ Chí Minh",
                    description="TechNova phát triển các giải pháp phần mềm và sản phẩm số cho doanh nghiệp."
                )
                db.add(company_obj)
                db.commit()
                db.refresh(company_obj)

            # Tạo các tin tuyển dụng mẫu ban đầu nếu bảng đang rỗng
            jobs_count = db.query(JobPost).count()
            if jobs_count == 0:
                sample_jobs = [
                    JobPost(
                        company_id=company_obj.company_id,
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
                        company_id=company_obj.company_id,
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
                        company_id=company_obj.company_id,
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
                        company_id=company_obj.company_id,
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
        # Không tự chuyển sang SQLite: báo đúng lỗi để cấu hình MySQL.
        raise RuntimeError(f"Không thể khởi tạo CSDL. Kiểm tra backend/.env và MySQL: {e}") from e

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
