"""Nạp tất cả ORM models để metadata.create_all thấy đầy đủ bảng."""
from backend.app.models.user import User
from backend.app.models.company import Company
from backend.app.models.job import JobPost
from backend.app.models.application import Application, CV

__all__ = ['User', 'Company', 'JobPost', 'Application', 'CV']
