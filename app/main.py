from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers.dashboard import router as dashboard_router
from app.api.routers.demo import router as demo_router
from app.api.routers.knowledge import router as knowledge_router
from app.api.routers.meetings import router as meetings_router
from app.config import STATE_FILE, STATIC_DIR
from app.services.meeting_service import MeetingService
from app.storage import JsonStateStore


def create_app(store: JsonStateStore | None = None) -> FastAPI:
    app = FastAPI(
        title="Investor Conversation Copilot",
        version="0.1.0",
        description="A demoable MVP for investor meeting analysis and training script generation.",
    )
    storage = store or JsonStateStore(STATE_FILE)
    app.state.meeting_service = MeetingService(storage)

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(demo_router)
    app.include_router(meetings_router)
    app.include_router(knowledge_router)
    app.include_router(dashboard_router)

    @app.get("/", include_in_schema=False)
    def root() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
