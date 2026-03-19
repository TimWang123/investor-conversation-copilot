from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_meeting_service
from app.models import AppSettingsResponse, UpdateAsrSettingsRequest, UpdateLlmSettingsRequest
from app.services.meeting_service import MeetingService

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=AppSettingsResponse)
def get_settings(
    service: Annotated[MeetingService, Depends(get_meeting_service)],
) -> AppSettingsResponse:
    return service.get_app_settings()


@router.post("/asr", response_model=AppSettingsResponse)
def update_asr_settings(
    payload: UpdateAsrSettingsRequest,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
) -> AppSettingsResponse:
    return service.update_asr_settings(payload)


@router.post("/llm", response_model=AppSettingsResponse)
def update_llm_settings(
    payload: UpdateLlmSettingsRequest,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
) -> AppSettingsResponse:
    return service.update_llm_settings(payload)
