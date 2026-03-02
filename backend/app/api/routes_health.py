from fastapi import APIRouter, Depends

from app.api.deps import auth_dep

router = APIRouter(tags=["health"])


@router.get("/health", dependencies=[Depends(auth_dep)])
def health():
    return {"status": "ok"}