from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class ProfileModel(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False) # Liên kết 1-1 với bảng users
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    job_search_status = Column(String(32), nullable=False, default="OPEN")

    # Kept for legacy application data; new profile payloads do not expose these fields.
    university = Column(String(255), nullable=True)
    major = Column(String(100), nullable=True)
    skills = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Quan hệ ngược lại với bảng User nếu cần
    user = relationship("UserModel", back_populates="profile")