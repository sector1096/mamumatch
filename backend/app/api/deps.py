from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.db.session import get_db


def auth_dep(_: None = Depends(require_api_key)) -> None:
    return None


def db_dep(db: Session = Depends(get_db)) -> Session:
    return db