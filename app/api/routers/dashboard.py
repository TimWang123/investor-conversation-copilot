from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_meeting_service
from app.models import DashboardSummary
from app.services.meeting_service import MeetingService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardSummary)
def get_dashboard(service: Annotated[MeetingService, Depends(get_meeting_service)]) -> DashboardSummary:
    return service.get_dashboard_summary()

