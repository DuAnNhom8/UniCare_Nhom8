"""Bảng CV và đơn ứng tuyển, liên kết ứng viên với tin tuyển dụng."""
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class CV(Base):
    __tablename__ = 'cvs'

    cv_id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    candidate = relationship('User', back_populates='cvs')
    applications = relationship('Application', back_populates='cv')


class Application(Base):
    __tablename__ = 'applications'
    __table_args__ = (UniqueConstraint('candidate_id', 'job_id', name='uq_candidate_job'),)

    application_id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey('job_posts.job_id', ondelete='CASCADE'), nullable=False, index=True)
    cv_id = Column(Integer, ForeignKey('cvs.cv_id', ondelete='SET NULL'), nullable=True)
    cover_letter = Column(Text, nullable=True)
    status = Column(Enum('PENDING', 'REVIEWING', 'ACCEPTED', 'REJECTED', name='application_status_enum'), nullable=False, default='PENDING')
    applied_at = Column(DateTime, server_default=func.now(), nullable=False)

    candidate = relationship('User', back_populates='applications')
    job = relationship('JobPost', back_populates='applications')
    cv = relationship('CV', back_populates='applications')
