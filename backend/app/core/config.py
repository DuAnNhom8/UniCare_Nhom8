import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
if len(SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY must be configured with at least 32 characters")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be configured")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip() or "gemini-3.5-flash-lite"

cv_storage_dir = Path(os.getenv("CV_STORAGE_DIR", "private_uploads/cvs"))
if not cv_storage_dir.is_absolute():
    if cv_storage_dir.parts and cv_storage_dir.parts[0].lower() == BACKEND_DIR.name.lower():
        cv_storage_dir = Path(*cv_storage_dir.parts[1:])
    cv_storage_dir = BACKEND_DIR / cv_storage_dir
CV_STORAGE_DIR = cv_storage_dir.resolve()