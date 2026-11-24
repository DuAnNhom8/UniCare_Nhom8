from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class CVModel(Base):
    __tablename__ = "cvs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    cv_type = Column(String(20), nullable=False, default="upload")
    personal_info = Column(JSON, nullable=True)
    content = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserModel", back_populates="cvs")
    applications = relationship("ApplicationModel", back_populates="cv")
    ai_consent = relationship(
        "CVAIConsentModel",
        back_populates="cv",
        cascade="all, delete-orphan",
        uselist=False,
    )
    analyses = relationship(
        "CVAnalysisModel",
        back_populates="cv",
        cascade="all, delete-orphan",
    )