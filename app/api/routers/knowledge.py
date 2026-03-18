from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_meeting_service
from app.models import TopicDetail, TopicSummary
from app.services.meeting_service import MeetingService

router = APIRouter(tags=["knowledge"])


@router.get("/api/topics", response_model=list[TopicSummary])
def get_topics(service: Annotated[MeetingService, Depends(get_meeting_service)]) -> list[TopicSummary]:
    return service.get_topics()


@router.get("/api/topics/{topic_id}", response_model=TopicDetail)
def get_topic_detail(
    topic_id: str,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
) -> TopicDetail:
    return service.get_topic_detail(topic_id)


@router.get("/api/topics/{topic_id}/canonical-answers")
def get_canonical_answers(
    topic_id: str,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
):
    return service.get_canonical_answers(topic_id)


@router.get("/api/training-scripts/latest")
def get_latest_training_script(service: Annotated[MeetingService, Depends(get_meeting_service)]):
    return service.get_latest_training_script()

