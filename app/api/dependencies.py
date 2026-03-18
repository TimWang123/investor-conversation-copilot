from __future__ import annotations

from fastapi import Request

from app.services.meeting_service import MeetingService


def get_meeting_service(request: Request) -> MeetingService:
    return request.app.state.meeting_service

