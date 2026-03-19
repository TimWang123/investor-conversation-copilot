from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile
from app.config import SAMPLES_DIR, UPLOADS_DIR
from app.models import (
    CreateMeetingRequest,
    DashboardSummary,
    DemoSampleResponse,
    MeetingListItem,
    MeetingRecord,
    TopicDetail,
    new_id,
)
from app.services.analysis import (
    build_canonical_answers,
    build_topic_summaries,
    build_training_script,
    process_meeting,
)
from app.services.llm_gateway import LlmGateway
from app.services.transcription_service import FasterWhisperTranscriptionService
from app.storage import JsonStateStore


class MeetingService:
    def __init__(
        self,
        store: JsonStateStore,
        llm_gateway: LlmGateway | None = None,
        transcription_service: FasterWhisperTranscriptionService | None = None,
    ):
        self.store = store
        self.llm_gateway = llm_gateway
        self.transcription_service = transcription_service

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
        normalized_transcript = self._normalize_transcript_text(transcript_text)
        meeting = MeetingRecord(
            title=payload.title,
            meeting_type=payload.meeting_type,
            investor_org=payload.investor_org,
            investor_names=payload.investor_names,
            founder_participants=payload.founder_participants,
            transcript_text=normalized_transcript,
            raw_transcript_text=transcript_text,
            transcript_source="manual",
        )
        return self._process_and_save_meeting(meeting, history)

    async def create_meeting_from_audio(
        self,
        *,
        title: str,
        meeting_type: str,
        investor_org: str,
        audio_file: UploadFile,
        transcript_source: str,
    ) -> MeetingRecord:
        if self.transcription_service is None:
            raise HTTPException(status_code=503, detail="音频转写服务未启用。")
        suffix = Path(audio_file.filename or "recording.webm").suffix or ".webm"
        safe_name = f"{new_id('audio')}{suffix}"
        target_path = UPLOADS_DIR / safe_name
        payload = await audio_file.read()
        if not payload:
            raise HTTPException(status_code=400, detail="上传的音频文件为空。")
        target_path.write_bytes(payload)

        try:
            transcription = self.transcription_service.transcribe(target_path)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"音频转写失败：{exc}") from exc

        history = self.store.list_meetings()
        normalized_source = transcript_source if transcript_source in {"audio_upload", "audio_recording"} else "audio_upload"
        normalized_transcript = self._normalize_transcript_text(transcription.text)
        meeting = MeetingRecord(
            title=title.strip() or "未命名音频会议",
            meeting_type=meeting_type,
            investor_org=investor_org.strip(),
            transcript_text=normalized_transcript,
            raw_transcript_text=transcription.text,
            transcript_source=normalized_source,
            audio_filename=safe_name,
        )
        return self._process_and_save_meeting(meeting, history)

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
        if self.llm_gateway is not None:
            processed = self.llm_gateway.enrich_meeting(processed, history)
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

    def llm_status(self) -> dict:
        if self.llm_gateway is None:
            return {"provider": None, "enabled": False, "model": None}
        return self.llm_gateway.status()

    def transcription_status(self) -> dict:
        if self.transcription_service is None:
            return {"provider": None, "enabled": False, "model": None, "device": None}
        return self.transcription_service.status()

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

    def _process_and_save_meeting(self, meeting: MeetingRecord, history: list[MeetingRecord]) -> MeetingRecord:
        try:
            processed = process_meeting(meeting, history)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if self.llm_gateway is not None:
            processed = self.llm_gateway.enrich_meeting(processed, history)
        self.store.save_meeting(processed)
        return processed

    def _normalize_transcript_text(self, transcript_text: str) -> str:
        if self.llm_gateway is None:
            return transcript_text
        return self.llm_gateway.normalize_transcript(transcript_text)
