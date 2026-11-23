"""Kết nối SQLAlchemy; chỉ dùng SQLite nếu DATABASE_URL được cấu hình rõ ràng (ví dụ khi test)."""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv(Path(__file__).resolve().parents[2] / '.env')

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    DATABASE_URL = URL.create(
        'mysql+pymysql',
        username=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', '3306')),
        database=os.getenv('DB_NAME', 'unicareer_db'),
        query={'charset': 'utf8mb4'},
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    **({'connect_args': {'check_same_thread': False}} if str(DATABASE_URL).startswith('sqlite') else {'pool_recycle': 3600}),
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
