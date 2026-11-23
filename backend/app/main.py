"""
Hệ thống Backend API - UniCareer (Nhóm 8)
Tích hợp toàn diện các module hệ thống (Task T05FEB0):
- Tài khoản & Xác thực (Auth)
- Hồ sơ ứng viên & Kỹ năng (Candidate)
- Doanh nghiệp (Company)
- Việc làm & Tin tuyển dụng (Jobs)
- Ứng tuyển & Quản lý đơn (Applications)
- Quản trị hệ thống & Kiểm duyệt (Admin)
"""

import os
from datetime import date, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, SessionLocal
import backend.app.models  # Import all models for SQLAlchemy registry
from backend.app.models import User, Candidate, Company, JobPost, Application
from backend.app.routers import auth, candidate, company, jobs, admin

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Hệ thống API nền tảng hướng nghiệp & tuyển dụng UniCareer - Tích hợp đầy đủ các module hệ thống",
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

# Đăng ký các router phân hệ vào hệ thống
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(candidate.router, prefix=settings.API_V1_STR)
app.include_router(company.router, prefix=settings.API_V1_STR)
app.include_router(jobs.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)


@app.on_event("startup")
def on_startup():
    """Khởi tạo cấu trúc bảng CSDL và nạp dữ liệu khởi tạo mặc định nếu chưa có"""
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            # 1. Tạo tài khoản Admin mặc định
            admin_user = db.query(User).filter(User.role == "ADMIN").first()
            if not admin_user:
                admin_user = User(
                    email="admin@unicareer.vn",
                    password_hash="admin123",
                    role="ADMIN",
                    is_active=True
                )
                db.add(admin_user)
                db.commit()

            # 2. Tạo tài khoản Nhà tuyển dụng mẫu nếu chưa có
            employer_user = db.query(User).filter(User.email == "hr@technova.example").first()
            if not employer_user:
                employer_user = User(
                    email="hr@technova.example",
                    password_hash="demo123",
                    role="EMPLOYER",
                    is_active=True
                )
                db.add(employer_user)
                db.commit()

            # 3. Tạo tài khoản Sinh viên mẫu nếu chưa có
            candidate_user = db.query(User).filter(User.email == "sinhvien@ptit.edu.vn").first()
            if not candidate_user:
                candidate_user = User(
                    email="sinhvien@ptit.edu.vn",
                    password_hash="demo123",
                    role="CANDIDATE",
                    is_active=True
                )
                db.add(candidate_user)
                db.commit()

                # Tạo hồ sơ sinh viên
                cand_profile = Candidate(
                    candidate_id=candidate_user.user_id,
                    full_name="Đỗ Hoàng Sơn",
                    phone="0912345678",
                    university="Học viện Công nghệ Bưu chính Viễn thông (PTIT)",
                    major="Công nghệ Thông tin",
                    skills="Python, FastAPI, MySQL, HTML5/CSS3, JavaScript, Git",
                    bio="Sinh viên năm cuối nhiệt huyết, đam mê phát triển hệ thống backend và giải pháp web tối ưu.",
                    cv_url="https://example.com/cv/do_hoang_son_cv.pdf"
                )
                db.add(cand_profile)
                db.commit()

            # 4. Tạo công ty TechNova mẫu nếu chưa có
            company_obj = db.query(Company).filter(Company.employer_id == employer_user.user_id).first()
            if not company_obj:
                company_obj = Company(
                    employer_id=employer_user.user_id,
                    company_name="TechNova Solutions",
                    industry="Công nghệ thông tin / Phần mềm",
                    website="https://technova.example",
                    location="TP. Hồ Chí Minh",
                    description="TechNova phát triển các giải pháp phần mềm và sản phẩm số cho doanh nghiệp."
                )
                db.add(company_obj)
                db.commit()

            # 5. Tạo các tin tuyển dụng mẫu ban đầu nếu bảng đang rỗng
            jobs_count = db.query(JobPost).count()
            if jobs_count == 0:
                sample_jobs = [
                    JobPost(
                        job_id=1,
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
                        job_id=2,
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
                        job_id=3,
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
                        job_id=4,
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
                    ),
                    JobPost(
                        job_id=5,
                        company_id=company_obj.company_id,
                        title="DevOps Engineer Intern",
                        description="Vận hành CI/CD pipelines, container hóa dịch vụ với Docker và triển khai hạ tầng cloud.",
                        requirements="Hiểu biết về Linux, Git, Docker, tư duy tự động hóa tốt.",
                        location="TP. Hồ Chí Minh",
                        salary_range="4–7 triệu/tháng",
                        job_type="INTERNSHIP",
                        experience_level="Không yêu cầu",
                        deadline=date.today() + timedelta(days=30),
                        status="ACTIVE",
                        approval_status="PENDING"
                    )
                ]
                db.add_all(sample_jobs)
                db.commit()

            # 6. Khởi tạo một đơn ứng tuyển mẫu cho sinh viên vào tin #1 nếu chưa có đơn nào
            app_count = db.query(Application).count()
            if app_count == 0 and candidate_user:
                first_job = db.query(JobPost).filter(JobPost.status == "ACTIVE", JobPost.approval_status == "APPROVED").first()
                if first_job:
                    sample_app = Application(
                        job_id=first_job.job_id,
                        candidate_id=candidate_user.user_id,
                        status="RECEIVED",
                        ai_match_score=92,
                        ai_feedback="Ứng viên đáp ứng xuất sắc các kỹ năng Python & REST API cho vị trí này."
                    )
                    db.add(sample_app)
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
        "description": "Hệ thống tích hợp đầy đủ module tài khoản, doanh nghiệp, việc làm, ứng tuyển, quản trị",
        "docs": "/docs",
        "modules": [
            "Authentication (/api/auth)",
            "Candidate Profile & Applications (/api/candidates)",
            "Company Management (/api/companies)",
            "Job Posts Management (/api/jobs)",
            "Admin Management (/api/admin)"
        ],
        "author": "UniCareer - Nhóm 8 (Đỗ Hoàng Sơn - TV2)"
    }


@app.get("/health", tags=["Hệ thống"])
def health_check():
    return {"status": "ok", "system": "integrated"}
