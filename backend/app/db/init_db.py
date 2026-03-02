from pathlib import Path

from sqlalchemy import text

from app.db.session import engine


def ensure_pipeline_jobs_table() -> None:
    sql_path = Path(__file__).resolve().parents[2] / "migrations" / "001_create_pipeline_jobs.sql"
    sql = sql_path.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.execute(text(sql))