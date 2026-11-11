"""
Bảng USERS - Quản lý tài khoản người dùng
Theo đặc tả SRS UniCareer mục 10.2.1
"""

from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True, comment="Mã người dùng")
    email = Column(String(100), unique=True, nullable=False, index=True, comment="Email đăng nhập")
    password_hash = Column(String(255), nullable=False, comment="Mật khẩu mã hóa BCrypt")
    role = Column(
        Enum("CANDIDATE", "EMPLOYER", "ADMIN", name="user_role_enum"),
        nullable=False,
        comment="Vai trò người dùng"
    )
    is_active = Column(Boolean, default=True, comment="Trạng thái tài khoản (True: Hoạt động, False: Khóa)")
    created_at = Column(DateTime, server_default=func.now(), comment="Thời gian tạo tài khoản")

    # Mối quan hệ 1-1 với Doanh nghiệp (nếu là EMPLOYER)
    company = relationship("Company", back_populates="employer", uselist=False, cascade="all, delete-orphan")
