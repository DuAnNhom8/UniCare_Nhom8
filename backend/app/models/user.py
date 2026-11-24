from sqlalchemy import Boolean, Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="candidate")  # Candidate, employer, admin
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    roles = relationship("RoleModel", secondary=user_roles, back_populates="users")
    profile = relationship("ProfileModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    cvs = relationship("CVModel", back_populates="user", cascade="all, delete-orphan")
    company = relationship("CompanyModel", back_populates="employer", uselist=False, cascade="all, delete-orphan")
    applications = relationship("ApplicationModel", back_populates="candidate", cascade="all, delete-orphan")