"""Thiết lập chung của UniCareer."""
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv(Path(__file__).resolve().parents[2] / '.env')


class Settings(BaseModel):
    PROJECT_NAME: str = 'UniCareer API'
    VERSION: str = '1.1.0'
    API_V1_STR: str = '/api'
    DB_USER: str = os.getenv('DB_USER', 'root')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    DB_HOST: str = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT: int = int(os.getenv('DB_PORT', '3306'))
    DB_NAME: str = os.getenv('DB_NAME', 'unicareer_db')


settings = Settings()
