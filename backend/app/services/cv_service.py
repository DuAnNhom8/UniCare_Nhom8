from __future__ import annotations
import logging
from html import escape
from pathlib import Path
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.cv import CVModel


logger = logging.getLogger(__name__)
MAX_CV_SIZE = 10 * 1024 * 1024
ALLOWED_CV_EXTENSIONS = frozenset({".pdf", ".docx"})


def cv_payload(cv: CVModel) -> dict:
    return {
        "cv_id": cv.id,
        "id": cv.id,
        "user_id": cv.user_id,
        "title": cv.file_name,
        "file_name": cv.file_name,
        "file_url": f"/api/candidate/cvs/{cv.id}/download",
        "description": cv.description,
        "cv_type": cv.cv_type or "upload",
        "personal_info": cv.personal_info,
        "content": cv.content,
        "allow_ai_analysis": bool(cv.ai_consent and cv.ai_consent.consented),
        "created_at": cv.created_at,
        "updated_at": cv.updated_at,
    }


def delete_cv_record(db: Session, cv: CVModel, storage_dir: Path) -> None:
    cv_id = cv.id
    stored_path = None
    if cv.file_url:
        stored_name = Path(cv.file_url).name
        if stored_name == cv.file_url:
            stored_path = storage_dir / stored_name

    db.delete(cv)
    try:
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail="Không thể xóa CV") from error

    if stored_path is not None:
        try:
            stored_path.unlink(missing_ok=True)
        except OSError as error:
            logger.exception(
                "CV %s was removed from the database, but its file could not be deleted",
                cv_id,
            )
            raise HTTPException(
                status_code=500,
                detail="CV đã bị xóa khỏi tài khoản nhưng tệp lưu trữ chưa thể xóa",
            ) from error


def render_cv_html(cv: CVModel) -> str:
    personal = cv.personal_info or {}
    content = cv.content or {}

    def safe_text(value: str | None) -> str:
        return escape(value or "").replace("\n", "<br>")

    contact = [
        personal.get("email"),
        personal.get("phone"),
    ]
    for label, key in (("GitHub", "github_url"), ("LinkedIn", "linkedin_url")):
        value = personal.get(key)
        if value:
            parsed = urlparse(value)
            if parsed.scheme in {"http", "https"} and parsed.netloc:
                contact.append(
                    f'<a href="{escape(value, quote=True)}">{label}</a>'
                )
            else:
                contact.append(value)

    sections = (
        ("Mục tiêu nghề nghiệp", "objective"),
        ("Học vấn", "education"),
        ("Kinh nghiệm làm việc", "experience"),
        ("Dự án", "projects"),
        ("Kỹ năng", "skills"),
        ("Chứng chỉ", "certifications"),
    )
    section_markup = "".join(
        f"<section><h2>{heading}</h2><p>{safe_text(content.get(key))}</p></section>"
        for heading, key in sections
        if content.get(key)
    )
    return (
        "<!doctype html><html lang=\"vi\"><head><meta charset=\"utf-8\">"
        f"<title>{safe_text(cv.file_name)}</title><style>"
        "body{font:15px/1.65 Arial,sans-serif;color:#203047;max-width:820px;"
        "margin:40px auto;padding:0 28px}h1{color:#14345d;margin-bottom:4px}"
        "h2{font-size:17px;color:#2457a6;border-bottom:1px solid #dce5f2;"
        "padding-bottom:6px;margin-top:24px}p{white-space:normal}"
        "a{color:#2457a6;margin-right:12px}@media print{body{margin:0 auto}}"
        "</style></head><body>"
        f"<h1>{safe_text(personal.get('full_name') or cv.file_name)}</h1>"
        f"<p>{' · '.join(safe_text(item) for item in contact if item)}</p>"
        f"{section_markup}</body></html>"
    )
