"""
Cấu hình kết nối Cơ sở dữ liệu MySQL sử dụng SQLAlchemy ORM
Dự án UniCareer - Nhóm 8
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Tải biến môi trường an toàn (nếu có python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Cấu hình chuỗi kết nối MySQL (Mặc định hoặc từ biến môi trường .env)
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "unicareer_db")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

# Khởi tạo engine và session
# Lưu ý: Khi chưa có MySQL đang chạy, engine tạo kết nối lazy nên không bị crash app
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho toàn bộ models ORM
Base = declarative_base()

def get_db():
    """Dependency cung cấp db session cho các API routers"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
