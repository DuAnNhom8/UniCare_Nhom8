from datetime import date, datetime
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class User(Base):
    __tablename__ = 'users'
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(Enum('CANDIDATE', 'EMPLOYER', 'ADMIN'), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default='1')
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp(), nullable=False)
    candidate: Mapped['Candidate | None'] = relationship(back_populates='user', uselist=False)
    company: Mapped['Company | None'] = relationship(back_populates='employer', uselist=False)
    __table_args__ = (Index('idx_users_role_active', 'role', 'is_active'),)

class Candidate(Base):
    __tablename__ = 'candidates'
    candidate_id: Mapped[int] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    university: Mapped[str | None] = mapped_column(String(150))
    major: Mapped[str | None] = mapped_column(String(100))
    skills: Mapped[str | None] = mapped_column(Text)
    bio: Mapped[str | None] = mapped_column(Text)
    cv_url: Mapped[str | None] = mapped_column(String(255))
    user: Mapped[User] = relationship(back_populates='candidate')

class Company(Base):
    __tablename__ = 'companies'
    company_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), unique=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(255))
    employer: Mapped[User] = relationship(back_populates='company')
    jobs: Mapped[list['JobPost']] = relationship(back_populates='company')

class JobPost(Base):
    __tablename__ = 'job_posts'
    job_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.company_id', ondelete='RESTRICT'), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(String(100))
    salary_range: Mapped[str | None] = mapped_column(String(100))
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(Enum('ACTIVE', 'CLOSED', 'HIDDEN'), server_default='ACTIVE', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp(), nullable=False)
    company: Mapped[Company] = relationship(back_populates='jobs')
    __table_args__ = (Index('idx_job_status_deadline', 'status', 'deadline'), Index('idx_job_company', 'company_id'))

class Application(Base):
    __tablename__ = 'applications'
    application_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey('job_posts.job_id', ondelete='RESTRICT'), nullable=False)
    candidate_id: Mapped[int] = mapped_column(ForeignKey('candidates.candidate_id', ondelete='RESTRICT'), nullable=False)
    status: Mapped[str] = mapped_column(Enum('RECEIVED', 'REVIEWING', 'MATCHED', 'REJECTED'), server_default='RECEIVED', nullable=False)
    ai_match_score: Mapped[int | None] = mapped_column(Integer)
    ai_feedback: Mapped[str | None] = mapped_column(Text)
    applied_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp(), nullable=False)
    __table_args__ = (
        UniqueConstraint('job_id', 'candidate_id', name='uq_application_candidate_job'),
        CheckConstraint('ai_match_score IS NULL OR ai_match_score BETWEEN 0 AND 100', name='chk_ai_score'),
        Index('idx_app_candidate', 'candidate_id', 'applied_at'),
        Index('idx_app_job_status', 'job_id', 'status'),
    )
