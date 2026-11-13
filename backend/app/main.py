"""
Hệ thống Backend API - UniCareer (Nhóm 8)
Phân hệ Doanh nghiệp & Tuyển dụng (TV2)
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.database import engine, Base
import backend.app.models  # Import all models for SQLAlchemy registry
from backend.app.routers import company

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

@app.on_event("startup")
def on_startup():
    """Khởi tạo cấu trúc bảng CSDL nếu chưa có (khi DB đang kết nối)"""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[Warning] Không thể tự động tạo bảng MySQL khi khởi động (chưa bật MySQL hoặc sai thông tin .env): {e}")

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
