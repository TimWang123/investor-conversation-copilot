from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers.dashboard import router as dashboard_router
from app.api.routers.demo import router as demo_router
from app.api.routers.knowledge import router as knowledge_router
from app.api.routers.meetings import router as meetings_router
from app.config import (
    APP_DISPLAY_NAME,
    APP_VERSION,
    ASR_COMPUTE_TYPE,
    ASR_DEVICE,
    ASR_MODEL_SIZE,
    LLM_PROVIDER,
    MODELS_DIR,
    MOONSHOT_API_KEY,
    MOONSHOT_BASE_URL,
    MOONSHOT_MODEL,
    QWEN_API_KEY,
    QWEN_BASE_URL,
    QWEN_MODEL,
    STATE_FILE,
    STATIC_DIR,
)
from app.services.llm_gateway import build_llm_gateway
from app.services.meeting_service import MeetingService
from app.services.transcription_service import FasterWhisperTranscriptionService
from app.storage import JsonStateStore


def create_app(
    store: JsonStateStore | None = None,
    meeting_service: MeetingService | None = None,
) -> FastAPI:
    app = FastAPI(
        title=APP_DISPLAY_NAME,
        version=APP_VERSION,
        description="A demoable MVP for investor meeting analysis and training script generation.",
    )
    storage = store or JsonStateStore(STATE_FILE)
    if meeting_service is None:
        llm_gateway = build_llm_gateway(
            provider=LLM_PROVIDER,
            moonshot_api_key=MOONSHOT_API_KEY,
            moonshot_base_url=MOONSHOT_BASE_URL,
            moonshot_model=MOONSHOT_MODEL,
            qwen_api_key=QWEN_API_KEY,
            qwen_base_url=QWEN_BASE_URL,
            qwen_model=QWEN_MODEL,
        )
        transcription_service = FasterWhisperTranscriptionService(
            model_size=ASR_MODEL_SIZE,
            device=ASR_DEVICE,
            compute_type=ASR_COMPUTE_TYPE,
            download_root=MODELS_DIR,
        )
        meeting_service = MeetingService(
            storage,
            llm_gateway=llm_gateway,
            transcription_service=transcription_service,
        )
    app.state.meeting_service = meeting_service

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
        llm = app.state.meeting_service.llm_status()
        asr = app.state.meeting_service.transcription_status()
        return {
            "status": "ok",
            "app_name": APP_DISPLAY_NAME,
            "app_version": APP_VERSION,
            "llm_provider": llm["provider"] or "disabled",
            "llm_enabled": str(llm["enabled"]).lower(),
            "llm_model": llm["model"] or "",
            "asr_provider": asr["provider"] or "disabled",
            "asr_enabled": str(asr["enabled"]).lower(),
            "asr_model": asr["model"] or "",
            "asr_device": asr.get("device") or "",
        }

    return app


app = create_app()
