from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_meeting_service
from app.models import DemoSampleResponse
from app.services.meeting_service import MeetingService

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.get("/sample-transcript", response_model=DemoSampleResponse)
def sample_transcript(
    service: Annotated[MeetingService, Depends(get_meeting_service)],
) -> DemoSampleResponse:
    return service.get_sample_transcript()


@router.post("/reset")
def reset_demo(service: Annotated[MeetingService, Depends(get_meeting_service)]) -> dict[str, str]:
    return service.reset_demo()

