"""
Bảng APPLICATIONS - Quản lý đơn ứng tuyển
Theo tài liệu đặc tả SRS UniCareer mục 10.2.5
"""

from sqlalchemy import Column, Integer, Text, DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Application(Base):
    __tablename__ = "applications"

    application_id = Column(Integer, primary_key=True, autoincrement=True, comment="Mã đơn ứng tuyển")
    job_id = Column(
        Integer,
        ForeignKey("job_posts.job_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Mã tin tuyển dụng"
    )
    candidate_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Mã ứng viên (tham chiếu users.user_id)"
    )
    status = Column(
        Enum("RECEIVED", "REVIEWING", "ACCEPTED", "REJECTED", name="application_status_enum"),
        default="RECEIVED",
        nullable=False,
        comment="Trạng thái xử lý đơn (RECEIVED, REVIEWING, ACCEPTED, REJECTED)"
    )
    ai_match_score = Column(Integer, nullable=True, comment="Điểm phù hợp AI đánh giá (0-100)")
    ai_feedback = Column(Text, nullable=True, comment="Nhận xét phản hồi hoặc góp ý từ AI")
    applied_at = Column(DateTime, server_default=func.now(), comment="Thời gian nộp đơn ứng tuyển")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Thời gian cập nhật")

    # Ràng buộc chống ứng tuyển trùng: 1 ứng viên chỉ nộp tối đa 1 đơn cho 1 tin
    __table_args__ = (
        UniqueConstraint("job_id", "candidate_id", name="uq_job_candidate"),
    )

    # Quan hệ
    job = relationship("JobPost", back_populates="applications")
    candidate = relationship("User", back_populates="applications")

    def __repr__(self):
        return f"<Application(id={self.application_id}, job_id={self.job_id}, candidate_id={self.candidate_id}, status='{self.status}')>"
