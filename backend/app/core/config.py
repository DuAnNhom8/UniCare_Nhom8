"""
Cấu hình ứng dụng UniCareer
"""

import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "UniCareer API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "unicareer_db")
    
    @property
    def DATABASE_URL(self) -> str:
        return os.getenv(
            "DATABASE_URL",
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

settings = Settings()
