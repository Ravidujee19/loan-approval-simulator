# /health/live, /health/ready

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health/live")
def live():
    return {"status": "ok"}


@router.get("/health/ready")
def ready():
    return {"status": "ready"}
