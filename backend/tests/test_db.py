from sqlalchemy import text

from app.db.session import engine


def test_db_connects():
    with engine.connect() as conn:
        value = conn.execute(text("SELECT 1")).scalar_one()
    assert value == 1