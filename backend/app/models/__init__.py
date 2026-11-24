from app.models.user import UserModel
from app.models.profile import ProfileModel
from app.models.cv import CVModel
from app.models.role import PermissionModel, RoleModel
from app.models.company import CompanyModel
from app.models.job import JobModel
from app.models.application import ApplicationModel
from app.models.ai import CVAIConsentModel, CVAnalysisModel, RevokedTokenModel

__all__ = [
    "UserModel",
    "ProfileModel",
    "CVModel",
    "RoleModel",
    "PermissionModel",
    "CompanyModel",
    "JobModel",
    "ApplicationModel",
    "CVAIConsentModel",
    "CVAnalysisModel",
    "RevokedTokenModel",
]
