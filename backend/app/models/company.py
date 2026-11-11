"""
Bảng COMPANIES - Quản lý hồ sơ doanh nghiệp (TV2)
Theo tài liệu đặc tả SRS UniCareer mục 10.2.3
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Company(Base):
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True, autoincrement=True, comment="Mã doanh nghiệp")
    employer_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Tài khoản nhà tuyển dụng (1-1 với USERS)"
    )
    company_name = Column(String(150), nullable=False, index=True, comment="Tên doanh nghiệp")
    description = Column(Text, nullable=True, comment="Mô tả / giới thiệu doanh nghiệp")
    website = Column(String(255), nullable=True, comment="Website công ty")
    industry = Column(String(100), nullable=True, comment="Ngành nghề hoạt động")
    location = Column(String(150), nullable=True, comment="Địa chỉ trụ sở chính")
    created_at = Column(DateTime, server_default=func.now(), comment="Ngày tạo thông tin")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Ngày cập nhật gần nhất")

    # Mối quan hệ
    employer = relationship("User", back_populates="company")
    jobs = relationship("JobPost", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company(id={self.company_id}, name='{self.company_name}')>"
