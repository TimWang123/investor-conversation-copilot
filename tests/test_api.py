from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.storage import JsonStateStore


def build_client(tmp_path: Path) -> TestClient:
    store = JsonStateStore(tmp_path / "state.json")
    app = create_app(store)
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
