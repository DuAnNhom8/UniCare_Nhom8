from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class JobModel(Base):
    __tablename__ = "job_posts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=False)
    location = Column(String(150), nullable=True)
    salary_range = Column(String(100), nullable=True)
    job_type = Column(String(30), nullable=False, default="INTERNSHIP")
    experience_level = Column(String(100), nullable=True)
    deadline = Column(Date, nullable=False, default=date.today)
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)
    approval_status = Column(String(20), nullable=False, default="PENDING", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("CompanyModel", back_populates="jobs")
    applications = relationship("ApplicationModel", back_populates="job", cascade="all, delete-orphan")

    @property
    def job_id(self):
        return self.id

    @property
    def company_name(self):
        return self.company.company_name if self.company else None

    @property
    def company_description(self):
        return self.company.description if self.company else None

    @property
    def company_website(self):
        return self.company.website if self.company else None

    @property
    def company_industry(self):
        return self.company.industry if self.company else None