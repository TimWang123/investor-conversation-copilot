from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.models import TranscriptionResult
from app.services.meeting_service import MeetingService
from app.storage import JsonStateStore


class FakeTranscriptionService:
    def status(self) -> dict:
        return {
            "provider": "fake-asr",
            "enabled": True,
            "model": "fake-small",
            "device": "cpu",
        }

    def transcribe(self, audio_path: Path, language: str | None = "zh") -> TranscriptionResult:
        assert audio_path.exists()
        return TranscriptionResult(
            text=(
                "你们最近增长怎么样？"
                "我们过去 12 个月 ARR 从 100 万增长到 400 万，复购率也超过了 60%。"
                "你们有什么壁垒？"
                "我们的壁垒主要来自真实业务数据、交付效率和渠道合作。"
            ),
            language=language,
            duration_seconds=12.0,
            segments=[],
        )


def build_client(tmp_path: Path) -> TestClient:
    store = JsonStateStore(tmp_path / "state.json")
    service = MeetingService(store, transcription_service=FakeTranscriptionService())
    app = create_app(store=store, meeting_service=service)
    return TestClient(app)


class FakeLlmGateway:
    @property
    def enabled(self) -> bool:
        return True

    def status(self) -> dict:
        return {"provider": "moonshot", "enabled": True, "model": "fake-kimi"}

    def normalize_transcript(self, transcript_text: str) -> str:
        return (
            "投资人：你们最近增长怎么样？\n"
            "我：我们过去 12 个月 ARR 从 100 万增长到 400 万，复购率超过 60%。\n"
            "投资人：那壁垒是什么？\n"
            "我：我们的壁垒主要来自真实业务数据、交付效率和渠道合作。"
        )

    def enrich_meeting(self, meeting, history):
        return meeting


def build_client_with_llm(tmp_path: Path) -> TestClient:
    store = JsonStateStore(tmp_path / "state.json")
    service = MeetingService(
        store,
        llm_gateway=FakeLlmGateway(),
        transcription_service=FakeTranscriptionService(),
    )
    app = create_app(store=store, meeting_service=service)
    return TestClient(app)


def test_create_meeting_generates_review_and_topics(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    payload = {
        "title": "测试融资会议",
        "meeting_type": "one_on_one",
        "investor_org": "测试基金",
        "transcript_text": (
            "投资人：你们最近增长怎么样？\n"
            "我：我们过去 12 个月 ARR 从 100 万增长到 400 万，复购率也超过了 60%。\n"
            "投资人：你们有什么壁垒？\n"
            "我：我们的壁垒主要来自真实业务数据、交付效率和渠道合作。"
        ),
    }
    response = client.post("/api/meetings", json=payload)
    assert response.status_code == 201
    meeting = response.json()
    assert meeting["status"] == "processed"
    assert len(meeting["qa_exchanges"]) == 2
    assert meeting["review"]["overall_score"] > 0
    assert meeting["style_profile"]["style_summary"]

    topics_response = client.get("/api/topics")
    assert topics_response.status_code == 200
    topics = topics_response.json()
    assert len(topics) >= 1

    meetings_response = client.get("/api/meetings")
    assert meetings_response.status_code == 200
    meetings = meetings_response.json()
    assert meetings[0]["qa_count"] == 2

    dashboard_response = client.get("/api/dashboard")
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["total_meetings"] == 1
    assert dashboard["total_qa_pairs"] == 2
    assert dashboard["recent_meetings"][0]["title"] == "测试融资会议"

    script_response = client.get("/api/training-scripts/latest")
    assert script_response.status_code == 200
    script = script_response.json()
    assert "新人融资沟通统一话术" in script["content"]

    topic_detail_response = client.get(f"/api/topics/{topics[0]['id']}")
    assert topic_detail_response.status_code == 200
    topic_detail = topic_detail_response.json()
    assert topic_detail["canonical_answers"]


def test_create_meeting_from_audio(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.post(
        "/api/meetings/from-audio",
        data={
            "title": "音频会议",
            "meeting_type": "one_on_one",
            "investor_org": "测试基金",
            "transcript_source": "audio_upload",
        },
        files={"audio": ("meeting.webm", b"fake-audio-bytes", "audio/webm")},
    )
    assert response.status_code == 201
    meeting = response.json()
    assert meeting["transcript_source"] == "audio_upload"
    assert meeting["audio_filename"]
    assert meeting["qa_exchanges"]

    health_response = client.get("/api/health")
    assert health_response.status_code == 200
    health = health_response.json()
    assert health["asr_enabled"] == "true"


def test_create_meeting_with_freeform_transcript_without_speaker_labels(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    payload = {
        "title": "无标签转写",
        "meeting_type": "one_on_one",
        "investor_org": "测试基金",
        "transcript_text": (
            "你们最近增长怎么样？"
            "我们过去 12 个月 ARR 从 100 万增长到 400 万，复购率超过 60%。"
            "那壁垒是什么？"
            "我们的壁垒主要来自真实业务数据、交付效率和渠道合作。"
        ),
    }
    response = client.post("/api/meetings", json=payload)
    assert response.status_code == 201
    meeting = response.json()
    assert len(meeting["qa_exchanges"]) >= 2


def test_llm_normalizes_transcript_roles_before_analysis(tmp_path: Path) -> None:
    client = build_client_with_llm(tmp_path)

    payload = {
        "title": "角色重建",
        "meeting_type": "one_on_one",
        "investor_org": "测试基金",
        "transcript_text": (
            "你们最近增长怎么样？"
            "我们过去 12 个月 ARR 从 100 万增长到 400 万，复购率超过 60%。"
            "那壁垒是什么？"
            "我们的壁垒主要来自真实业务数据、交付效率和渠道合作。"
        ),
    }
    response = client.post("/api/meetings", json=payload)
    assert response.status_code == 201
    meeting = response.json()
    assert meeting["raw_transcript_text"]
    assert meeting["transcript_text"].startswith("投资人：")
    assert len(meeting["qa_exchanges"]) == 2
