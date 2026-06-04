from fastapi import APIRouter

from app.api.projects import router as projects_router

router = APIRouter()
router.include_router(projects_router)


@router.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
