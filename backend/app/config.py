import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://root:change-me@127.0.0.1:3306/unicareer?charset=utf8mb4')
JWT_SECRET = os.getenv('JWT_SECRET', '')
JWT_EXPIRES_MINUTES = int(os.getenv('JWT_EXPIRES_MINUTES', '30'))
AI_PROVIDER = os.getenv('AI_PROVIDER', 'rules').strip().lower()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-5.5')
UPLOAD_DIR = (ROOT / os.getenv('UPLOAD_DIR', 'uploads')).resolve()
MAX_CV_BYTES = int(os.getenv('MAX_CV_MB', '5')) * 1024 * 1024
