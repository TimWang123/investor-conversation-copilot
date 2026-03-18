from __future__ import annotations

from fastapi import HTTPException

from app.config import SAMPLES_DIR
from app.models import (
    CreateMeetingRequest,
    DashboardSummary,
    DemoSampleResponse,
    MeetingListItem,
    MeetingRecord,
    TopicDetail,
)
from app.services.analysis import (
    build_canonical_answers,
    build_topic_summaries,
    build_training_script,
    process_meeting,
)
from app.storage import JsonStateStore


class MeetingService:
    def __init__(self, store: JsonStateStore):
        self.store = store

    def get_sample_transcript(self) -> DemoSampleResponse:
        transcript_path = SAMPLES_DIR / "fundraising_transcript.txt"
        return DemoSampleResponse(
            title="Pre-A 一对一投资沟通",
            meeting_type="one_on_one",
            investor_org="启明增长基金",
            transcript_text=transcript_path.read_text(encoding="utf-8"),
        )

    def reset_demo(self) -> dict[str, str]:
        self.store.reset()
        return {"message": "demo data cleared"}

    def create_meeting(self, payload: CreateMeetingRequest) -> MeetingRecord:
        transcript_text = payload.transcript_text.strip()
        if not transcript_text:
            raise HTTPException(status_code=400, detail="transcript_text 不能为空。")

        history = self.store.list_meetings()
        meeting = MeetingRecord(
            title=payload.title,
            meeting_type=payload.meeting_type,
            investor_org=payload.investor_org,
            investor_names=payload.investor_names,
            founder_participants=payload.founder_participants,
            transcript_text=transcript_text,
        )
        try:
            processed = process_meeting(meeting, history)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        self.store.save_meeting(processed)
        return processed

    def list_meetings(self) -> list[MeetingListItem]:
        meetings = self.store.list_meetings()
        return [self._to_meeting_list_item(meeting) for meeting in sorted(meetings, key=lambda item: item.created_at, reverse=True)]

    def get_meeting(self, meeting_id: str) -> MeetingRecord:
        meeting = self.store.get_meeting(meeting_id)
        if meeting is None:
            raise HTTPException(status_code=404, detail="meeting not found")
        return meeting

    def reprocess_meeting(self, meeting_id: str) -> MeetingRecord:
        meeting = self.get_meeting(meeting_id)
        history = [item for item in self.store.list_meetings() if item.id != meeting_id]
        try:
            processed = process_meeting(meeting, history)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        self.store.save_meeting(processed)
        return processed

    def get_meeting_review_bundle(self, meeting_id: str) -> dict:
        meeting = self.get_meeting(meeting_id)
        return {"review": meeting.review, "style_profile": meeting.style_profile}

    def get_topics(self):
        return build_topic_summaries(self.store.list_meetings())

    def get_topic_detail(self, topic_id: str) -> TopicDetail:
        topics = self.get_topics()
        topic = next((item for item in topics if item.id == topic_id), None)
        if topic is None:
            raise HTTPException(status_code=404, detail="topic not found")
        return TopicDetail(
            topic=topic,
            canonical_answers=build_canonical_answers(self.store.list_meetings(), topic_id),
        )

    def get_canonical_answers(self, topic_id: str):
        return self.get_topic_detail(topic_id).canonical_answers

    def get_latest_training_script(self):
        script = build_training_script(self.store.list_meetings())
        if script is None:
            raise HTTPException(status_code=404, detail="training script not available yet")
        return script

    def get_dashboard_summary(self) -> DashboardSummary:
        meetings = self.store.list_meetings()
        topics = build_topic_summaries(meetings)
        total_qa_pairs = sum(len(meeting.qa_exchanges) for meeting in meetings)
        scores = [meeting.review.overall_score for meeting in meetings if meeting.review is not None]
        hottest_topic = topics[0].name if topics else None
        latest_meeting_id = meetings[-1].id if meetings else None
        recent_meetings = [self._to_meeting_list_item(meeting) for meeting in sorted(meetings, key=lambda item: item.created_at, reverse=True)]

        return DashboardSummary(
            total_meetings=len(meetings),
            total_qa_pairs=total_qa_pairs,
            average_overall_score=round(sum(scores) / len(scores)) if scores else None,
            hottest_topic=hottest_topic,
            latest_meeting_id=latest_meeting_id,
            recent_meetings=recent_meetings,
            topics=topics,
            training_script=build_training_script(meetings),
        )

    def _to_meeting_list_item(self, meeting: MeetingRecord) -> MeetingListItem:
        return MeetingListItem(
            id=meeting.id,
            title=meeting.title,
            meeting_type=meeting.meeting_type,
            investor_org=meeting.investor_org,
            status=meeting.status,
            created_at=meeting.created_at,
            processed_at=meeting.processed_at,
            overall_score=meeting.review.overall_score if meeting.review else None,
            qa_count=len(meeting.qa_exchanges),
        )

