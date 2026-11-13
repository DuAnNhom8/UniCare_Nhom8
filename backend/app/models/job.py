"""
Bảng JOB_POSTS - Quản lý tin tuyển dụng (TV2)
Theo tài liệu đặc tả SRS UniCareer mục 10.2.4
"""

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class JobPost(Base):
    __tablename__ = "job_posts"

    job_id = Column(Integer, primary_key=True, autoincrement=True, comment="Mã tin tuyển dụng")
    company_id = Column(
        Integer,
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Mã doanh nghiệp đăng tin"
    )
    title = Column(String(150), nullable=False, index=True, comment="Tên vị trí tuyển dụng")
    description = Column(Text, nullable=False, comment="Mô tả công việc")
    requirements = Column(Text, nullable=False, comment="Yêu cầu đối với ứng viên")
    location = Column(String(100), nullable=True, comment="Địa điểm làm việc (Hà Nội, TP.HCM, Hybrid...)")
    salary_range = Column(String(100), nullable=True, comment="Khoảng lương (VD: 3-5 triệu/tháng, Thỏa thuận)")
    job_type = Column(
        Enum("FULL_TIME", "PART_TIME", "INTERNSHIP", name="job_type_enum"),
        nullable=True,
        default="INTERNSHIP",
        comment="Loại hình công việc"
    )
    experience_level = Column(String(50), nullable=True, comment="Yêu cầu kinh nghiệm (VD: Không yêu cầu)")
    deadline = Column(Date, nullable=False, comment="Hạn cuối nộp hồ sơ ứng tuyển")
    status = Column(
        Enum("ACTIVE", "CLOSED", "HIDDEN", name="job_status_enum"),
        default="ACTIVE",
        nullable=False,
        comment="Trạng thái hiển thị (ACTIVE: Đang tuyển, CLOSED: Đã đóng, HIDDEN: Tạm ẩn)"
    )
    approval_status = Column(
        Enum("PENDING", "APPROVED", "REJECTED", name="job_approval_enum"),
        default="PENDING",
        nullable=False,
        comment="Trạng thái kiểm duyệt của Admin (PENDING: Chờ duyệt, APPROVED: Đã duyệt, REJECTED: Từ chối)"
    )
    created_at = Column(DateTime, server_default=func.now(), comment="Thời gian đăng tin")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Thời gian cập nhật")

    # Mối quan hệ
    company = relationship("Company", back_populates="jobs")

    def __repr__(self):
        return f"<JobPost(id={self.job_id}, title='{self.title}', status='{self.status}')>"
