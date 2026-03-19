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
            "compute_type": "int8",
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
    service = MeetingService(
        store,
        transcription_service=FakeTranscriptionService(),
        settings_file=tmp_path / "settings.json",
    )
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
        settings_file=tmp_path / "settings.json",
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


def test_settings_endpoint_updates_asr_model_size(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    settings_response = client.get("/api/settings")
    assert settings_response.status_code == 200
    settings = settings_response.json()
    assert settings["asr"]["model_size"] == "fake-small"
    assert settings["asr"]["model_options"]
    assert settings["asr"]["device_options"]
    assert settings["asr"]["compute_type_options"]
    assert settings["llm"]["provider"] == "disabled"
    assert settings["llm"]["provider_options"]

    update_response = client.post(
        "/api/settings/asr",
        json={"model_size": "medium", "device": "cpu", "compute_type": "int8"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["asr"]["model_size"] == "medium"
    assert updated["asr"]["device"] == "cpu"
    assert updated["asr"]["compute_type"] == "int8"

    saved_settings = (tmp_path / "settings.json").read_text(encoding="utf-8")
    assert '"ASR_MODEL_SIZE": "medium"' in saved_settings
    assert '"ASR_DEVICE": "cpu"' in saved_settings
    assert '"ASR_COMPUTE_TYPE": "int8"' in saved_settings


def test_settings_endpoint_updates_llm_provider_and_model(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    update_response = client.post(
        "/api/settings/llm",
        json={"provider": "qwen", "model": "qwen3.5-plus"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["llm"]["provider"] == "qwen"
    assert updated["llm"]["model"] == "qwen3.5-plus"
    assert updated["llm"]["current_provider"] == "qwen"
    assert updated["llm"]["current_model"] == ""
    assert updated["llm"]["enabled"] is False

    saved_settings = (tmp_path / "settings.json").read_text(encoding="utf-8")
    assert '"LLM_PROVIDER": "qwen"' in saved_settings
    assert '"QWEN_MODEL": "qwen3.5-plus"' in saved_settings


def test_settings_endpoint_rejects_cuda_without_supported_runtime(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    client.app.state.meeting_service._hardware_probe_cache = (False, None)

    response = client.post(
        "/api/settings/asr",
        json={"model_size": "small", "device": "cuda", "compute_type": "float16"},
    )
    assert response.status_code == 400
    assert "CUDA" in response.json()["detail"]


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
    assert health["app_name"] == "天枢智元·融谈Copilot"
    assert health["app_version"] == "0.2.5"
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


def test_create_meeting_with_multiline_follow_up_questions(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    payload = {
        "title": "多轮追问转写",
        "meeting_type": "one_on_one",
        "investor_org": "测试基金",
        "transcript_text": (
            "这款软件独特的竞争优势是什么\n"
            "OK 我们过去12个月 ARR 从320万增长到了1280万\n"
            "四季度的环比增长是18% 21% 23%和26%\n"
            "目标新增客户主要来自于老客户转介绍和行业渠道合作\n"
            "听起来增长数据不错\n"
            "那软件的盈利模式是怎样的呢\n"
            "我们现在的壁垒不是单一点 而是三层叠加\n"
            "第一层是场景数据\n"
            "我们已经累积了47家付费客户的真实流程数据\n"
            "积累了不少数据呢\n"
            "那第二层壁垒是什么呢\n"
            "这些数据又如何帮助软件持续发展呢\n"
            "我们从去年下半年开始严格看这组数据\n"
            "平均目前是 CAC 大概在2.8万左右\n"
            "首年合同额在9.6万左右\n"
            "那客户的留存率怎么样呢\n"
            "另外市场推广方面有什么计划\n"
        ),
    }

    response = client.post("/api/meetings", json=payload)
    assert response.status_code == 201
    meeting = response.json()
    assert len(meeting["qa_exchanges"]) >= 3


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
