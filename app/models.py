from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


class StyleProfile(BaseModel):
    id: str = Field(default_factory=lambda: new_id("style"))
    style_summary: str
    tone_tags: list[str] = Field(default_factory=list)
    strength_tags: list[str] = Field(default_factory=list)
    risk_tags: list[str] = Field(default_factory=list)
    common_patterns: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=utc_now_iso)


class QAReview(BaseModel):
    completeness_score: int
    clarity_score: int
    consistency_score: int
    evidence_score: int
    brevity_score: int
    risk_score: int
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    improvement_suggestions: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)


class QAExchange(BaseModel):
    id: str = Field(default_factory=lambda: new_id("qa"))
    question_text: str
    answer_text: str
    topic_id: str
    topic_name: str
    question_intent: str
    confidence: float = 0.78
    review: QAReview


class MeetingReview(BaseModel):
    meeting_summary: str
    overall_score: int
    strongest_topics: list[str] = Field(default_factory=list)
    weakest_topics: list[str] = Field(default_factory=list)
    top_improvements: list[str] = Field(default_factory=list)
    style_snapshot: str
    consistency_assessment: str


class MeetingRecord(BaseModel):
    id: str = Field(default_factory=lambda: new_id("meeting"))
    title: str
    meeting_type: str = "one_on_one"
    investor_org: str = ""
    investor_names: list[str] = Field(default_factory=list)
    founder_participants: list[str] = Field(default_factory=list)
    transcript_text: str
    raw_transcript_text: str | None = None
    transcript_source: Literal["manual", "audio_upload", "audio_recording"] = "manual"
    audio_filename: str | None = None
    status: Literal["draft", "processed"] = "draft"
    created_at: str = Field(default_factory=utc_now_iso)
    processed_at: str | None = None
    qa_exchanges: list[QAExchange] = Field(default_factory=list)
    review: MeetingReview | None = None
    style_profile: StyleProfile | None = None


class TopicSummary(BaseModel):
    id: str
    name: str
    description: str
    frequency: int
    sample_questions: list[str] = Field(default_factory=list)
    latest_score: int


class CanonicalAnswer(BaseModel):
    id: str = Field(default_factory=lambda: new_id("canon"))
    topic_id: str
    version: int
    summary_answer: str
    structured_talking_points: list[str] = Field(default_factory=list)
    supporting_facts: list[str] = Field(default_factory=list)
    dos: list[str] = Field(default_factory=list)
    donts: list[str] = Field(default_factory=list)
    source_meeting_ids: list[str] = Field(default_factory=list)
    status: Literal["draft", "approved"] = "draft"


class TrainingScript(BaseModel):
    id: str = Field(default_factory=lambda: new_id("script"))
    version: int
    audience: str = "新人"
    script_title: str
    content: str
    topic_ids: list[str] = Field(default_factory=list)
    source_canonical_answer_ids: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=utc_now_iso)


class CreateMeetingRequest(BaseModel):
    title: str
    meeting_type: str = "one_on_one"
    investor_org: str = ""
    investor_names: list[str] = Field(default_factory=list)
    founder_participants: list[str] = Field(default_factory=list)
    transcript_text: str


class DemoSampleResponse(BaseModel):
    title: str
    meeting_type: str
    investor_org: str
    transcript_text: str


class MeetingListItem(BaseModel):
    id: str
    title: str
    meeting_type: str
    investor_org: str
    status: Literal["draft", "processed"]
    created_at: str
    processed_at: str | None = None
    overall_score: int | None = None
    qa_count: int = 0


class TopicDetail(BaseModel):
    topic: TopicSummary
    canonical_answers: list[CanonicalAnswer] = Field(default_factory=list)


class DashboardSummary(BaseModel):
    total_meetings: int
    total_qa_pairs: int
    average_overall_score: int | None = None
    hottest_topic: str | None = None
    latest_meeting_id: str | None = None
    recent_meetings: list[MeetingListItem] = Field(default_factory=list)
    topics: list[TopicSummary] = Field(default_factory=list)
    training_script: TrainingScript | None = None


class TranscriptionResult(BaseModel):
    text: str
    language: str | None = None
    duration_seconds: float | None = None
    segments: list[dict] = Field(default_factory=list)


class SettingOption(BaseModel):
    value: str
    label: str
    description: str


class AsrSettingsPayload(BaseModel):
    model_size: str
    device: str
    compute_type: str
    model_options: list[SettingOption] = Field(default_factory=list)
    device_options: list[SettingOption] = Field(default_factory=list)
    compute_type_options: list[SettingOption] = Field(default_factory=list)
    note: str = ""


class AppSettingsResponse(BaseModel):
    asr: AsrSettingsPayload


class UpdateAsrSettingsRequest(BaseModel):
    model_size: str
    device: str
    compute_type: str
