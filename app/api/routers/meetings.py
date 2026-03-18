from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies import get_meeting_service
from app.models import CreateMeetingRequest, MeetingListItem, MeetingRecord
from app.services.meeting_service import MeetingService

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


@router.get("", response_model=list[MeetingListItem])
def list_meetings(service: Annotated[MeetingService, Depends(get_meeting_service)]) -> list[MeetingListItem]:
    return service.list_meetings()


@router.post("", response_model=MeetingRecord, status_code=201)
def create_meeting(
    payload: CreateMeetingRequest,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
) -> MeetingRecord:
    return service.create_meeting(payload)


@router.post("/from-audio", response_model=MeetingRecord, status_code=201)
async def create_meeting_from_audio(
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    title: Annotated[str, Form(...)],
    meeting_type: Annotated[str, Form()] = "one_on_one",
    investor_org: Annotated[str, Form()] = "",
    transcript_source: Annotated[str, Form()] = "audio_upload",
    audio: UploadFile = File(...),
) -> MeetingRecord:
    return await service.create_meeting_from_audio(
        title=title,
        meeting_type=meeting_type,
        investor_org=investor_org,
        audio_file=audio,
        transcript_source=transcript_source,
    )


@router.post("/{meeting_id}/process", response_model=MeetingRecord)
def reprocess_meeting(
    meeting_id: str,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
) -> MeetingRecord:
    return service.reprocess_meeting(meeting_id)


@router.get("/{meeting_id}", response_model=MeetingRecord)
def get_meeting(
    meeting_id: str,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
) -> MeetingRecord:
    return service.get_meeting(meeting_id)


@router.get("/{meeting_id}/qa-exchanges")
def get_meeting_qas(
    meeting_id: str,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
):
    return service.get_meeting(meeting_id).qa_exchanges


@router.get("/{meeting_id}/review")
def get_meeting_review(
    meeting_id: str,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
):
    return service.get_meeting_review_bundle(meeting_id)
