from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class ApplicationModel(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("job_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    cv_id = Column(Integer, ForeignKey("cvs.id", ondelete="SET NULL"), nullable=True, index=True)
    cover_letter = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    applied_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidate = relationship("UserModel", back_populates="applications")
    job = relationship("JobModel", back_populates="applications")
    cv = relationship("CVModel", back_populates="applications")

    @property
    def application_id(self):
        return self.id