from fastapi import FastAPI

from app.api.router import router
from app.core.config import get_settings
from app.db.session import init_db


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(router, prefix="/api")

    @app.on_event("startup")
    def on_startup() -> None:
        init_db()

    return app


app = create_app()
