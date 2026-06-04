from fastapi import APIRouter, Depends

from app.api.places import router as places_router
from app.api.projects import router as projects_router
from app.core.security import require_basic_auth

router = APIRouter()
router.include_router(places_router, dependencies=[Depends(require_basic_auth)])
router.include_router(projects_router, dependencies=[Depends(require_basic_auth)])


@router.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
