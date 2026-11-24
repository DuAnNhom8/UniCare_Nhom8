from __future__ import annotations
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app import models
from app.core.database import Base, engine, SessionLocal
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.jobs import router as jobs_router
from app.routers.candidate import router as candidate_router
from app.routers.company import router as company_router
from app.routers.admin import router as admin_router
from app.routers.ai_services import router as ai_router
from app.services.auth_service import seed_roles


def migrate_legacy_schema(database_engine: Engine) -> None:
    inspector = inspect(database_engine)
    tables = set(inspector.get_table_names())
    migrations = {
        "users": {
            "is_active": "BOOLEAN NOT NULL DEFAULT 1",
        },
        "profiles": {
            "avatar_url": "VARCHAR(500) NULL",
            "github_url": "VARCHAR(500) NULL",
            "linkedin_url": "VARCHAR(500) NULL",
            "job_search_status": "VARCHAR(32) NOT NULL DEFAULT 'OPEN'",
        },
        "cvs": {
            "cv_type": "VARCHAR(20) NOT NULL DEFAULT 'upload'",
            "personal_info": "JSON NULL",
            "content": "JSON NULL",
        },
    }
    with database_engine.begin() as connection:
        for table, columns_to_add in migrations.items():
            if table not in tables:
                continue
            existing_columns = {
                column["name"] for column in inspect(connection).get_columns(table)
            }
            for column, definition in columns_to_add.items():
                if column not in existing_columns:
                    connection.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    migrate_legacy_schema(engine)
    db = SessionLocal()
    try:
        seed_roles(db)
    finally:
        db.close()
    yield


app = FastAPI(title="UniCare API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
api_prefix = "/api"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(users_router, prefix=api_prefix)
app.include_router(jobs_router, prefix=api_prefix)
app.include_router(candidate_router, prefix=api_prefix)
app.include_router(company_router, prefix=api_prefix)
app.include_router(admin_router, prefix=api_prefix)
app.include_router(ai_router, prefix=api_prefix)

frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/frontend", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


@app.get("/")
def root():
    return {"message": "UniCare API"}