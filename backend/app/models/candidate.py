"""
Bảng CANDIDATES - Quản lý hồ sơ ứng viên / sinh viên
Theo tài liệu đặc tả SRS UniCareer mục 10.2.2
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    candidate_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
        comment="Mã sinh viên, liên kết 1-1 với USERS"
    )
    full_name = Column(String(100), nullable=False, comment="Họ và tên sinh viên")
    phone = Column(String(20), nullable=True, comment="Số điện thoại liên lạc")
    university = Column(String(150), nullable=True, comment="Trường đại học")
    major = Column(String(100), nullable=True, comment="Chuyên ngành đào tạo")
    skills = Column(Text, nullable=True, comment="Danh sách kỹ năng (JSON hoặc chuỗi phân tách dấu phẩy)")
    bio = Column(Text, nullable=True, comment="Giới thiệu bản thân và mục tiêu nghề nghiệp")
    cv_url = Column(String(255), nullable=True, comment="Đường dẫn lưu trữ CV")
    created_at = Column(DateTime, server_default=func.now(), comment="Thời gian tạo hồ sơ")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Thời gian cập nhật")

    # Mối quan hệ 1-1 với bảng User
    user = relationship("User", back_populates="candidate")

    def __repr__(self):
        return f"<Candidate(id={self.candidate_id}, name='{self.full_name}')>"
