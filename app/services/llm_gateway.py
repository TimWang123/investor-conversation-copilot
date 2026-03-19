from __future__ import annotations

import json
from typing import Any, Protocol

import httpx

from app.models import MeetingRecord, MeetingReview, QAReview, StyleProfile


class LlmGateway(Protocol):
    @property
    def enabled(self) -> bool: ...

    def status(self) -> dict[str, Any]: ...

    def normalize_transcript(self, transcript_text: str) -> str: ...

    def enrich_meeting(self, meeting: MeetingRecord, history: list[MeetingRecord]) -> MeetingRecord: ...


class OpenAICompatibleGateway:
    def __init__(self, *, provider: str, api_key: str, base_url: str, model: str):
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.model)

    def status(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "enabled": self.enabled,
            "model": self.model if self.enabled else None,
        }

    def normalize_transcript(self, transcript_text: str) -> str:
        if not self.enabled:
            return transcript_text
        if _has_explicit_roles(transcript_text):
            return transcript_text

        payload = self._run_transcript_reconstruction_prompt(transcript_text)
        if payload is None:
            return transcript_text

        normalized = str(payload.get("normalized_transcript") or "").strip()
        if not normalized or not _has_explicit_roles(normalized):
            return transcript_text
        return normalized

    def enrich_meeting(self, meeting: MeetingRecord, history: list[MeetingRecord]) -> MeetingRecord:
        if not self.enabled or not meeting.qa_exchanges:
            return meeting

        payload = self._run_analysis_prompt(meeting, history)
        if payload is None:
            return meeting

        qa_lookup = {qa.id: qa for qa in meeting.qa_exchanges}
        for item in payload.get("qa_reviews", []):
            qa_id = item.get("qa_id")
            if qa_id not in qa_lookup:
                continue
            qa_lookup[qa_id].review = QAReview(
                completeness_score=_normalize_score(item.get("completeness_score"), qa_lookup[qa_id].review.completeness_score),
                clarity_score=_normalize_score(item.get("clarity_score"), qa_lookup[qa_id].review.clarity_score),
                consistency_score=_normalize_score(item.get("consistency_score"), qa_lookup[qa_id].review.consistency_score),
                evidence_score=_normalize_score(item.get("evidence_score"), qa_lookup[qa_id].review.evidence_score),
                brevity_score=_normalize_score(item.get("brevity_score"), qa_lookup[qa_id].review.brevity_score),
                risk_score=_normalize_score(item.get("risk_score"), qa_lookup[qa_id].review.risk_score),
                strengths=_normalize_list(item.get("strengths")) or qa_lookup[qa_id].review.strengths,
                weaknesses=_normalize_list(item.get("weaknesses")) or qa_lookup[qa_id].review.weaknesses,
                improvement_suggestions=_normalize_list(item.get("improvement_suggestions"))
                or qa_lookup[qa_id].review.improvement_suggestions,
                missing_points=_normalize_list(item.get("missing_points")) or qa_lookup[qa_id].review.missing_points,
            )

        meeting_review_payload = payload.get("meeting_review")
        if isinstance(meeting_review_payload, dict):
            meeting.review = MeetingReview(
                meeting_summary=str(meeting_review_payload.get("meeting_summary") or meeting.review.meeting_summary),
                overall_score=_normalize_score(meeting_review_payload.get("overall_score"), meeting.review.overall_score),
                strongest_topics=_normalize_list(meeting_review_payload.get("strongest_topics")) or meeting.review.strongest_topics,
                weakest_topics=_normalize_list(meeting_review_payload.get("weakest_topics")) or meeting.review.weakest_topics,
                top_improvements=_normalize_list(meeting_review_payload.get("top_improvements")) or meeting.review.top_improvements,
                style_snapshot=str(meeting_review_payload.get("style_snapshot") or meeting.review.style_snapshot),
                consistency_assessment=str(
                    meeting_review_payload.get("consistency_assessment") or meeting.review.consistency_assessment
                ),
            )

        style_payload = payload.get("style_profile")
        if isinstance(style_payload, dict):
            meeting.style_profile = StyleProfile(
                style_summary=str(style_payload.get("style_summary") or meeting.style_profile.style_summary),
                tone_tags=_normalize_list(style_payload.get("tone_tags")) or meeting.style_profile.tone_tags,
                strength_tags=_normalize_list(style_payload.get("strength_tags")) or meeting.style_profile.strength_tags,
                risk_tags=_normalize_list(style_payload.get("risk_tags")) or meeting.style_profile.risk_tags,
                common_patterns=_normalize_list(style_payload.get("common_patterns")) or meeting.style_profile.common_patterns,
            )

        return meeting

    def _run_analysis_prompt(self, meeting: MeetingRecord, history: list[MeetingRecord]) -> dict[str, Any] | None:
        history_context = _history_context(history)
        qa_payload = [
            {
                "qa_id": qa.id,
                "topic_id": qa.topic_id,
                "topic_name": qa.topic_name,
                "question": qa.question_text,
                "answer": qa.answer_text,
                "current_review": qa.review.model_dump(mode="json"),
            }
            for qa in meeting.qa_exchanges
        ]
        prompt = {
            "task": "review_investor_meeting",
            "goal": "对融资沟通中的每组问答做更专业的投资人视角复盘，同时总结本场会议总评和表达风格。",
            "requirements": [
                "保留中文输出。",
                "务必只返回 JSON 对象，不要输出额外解释。",
                "评分必须是 0 到 100 的整数。",
                "每组问答的建议要具体可执行，避免空泛。",
            ],
            "history_context": history_context,
            "meeting": {
                "title": meeting.title,
                "meeting_type": meeting.meeting_type,
                "investor_org": meeting.investor_org,
                "qa_pairs": qa_payload,
            },
            "json_schema": {
                "qa_reviews": [
                    {
                        "qa_id": "string",
                        "completeness_score": 80,
                        "clarity_score": 80,
                        "consistency_score": 80,
                        "evidence_score": 80,
                        "brevity_score": 80,
                        "risk_score": 80,
                        "strengths": ["string"],
                        "weaknesses": ["string"],
                        "improvement_suggestions": ["string"],
                        "missing_points": ["string"],
                    }
                ],
                "meeting_review": {
                    "meeting_summary": "string",
                    "overall_score": 80,
                    "strongest_topics": ["string"],
                    "weakest_topics": ["string"],
                    "top_improvements": ["string"],
                    "style_snapshot": "string",
                    "consistency_assessment": "string",
                },
                "style_profile": {
                    "style_summary": "string",
                    "tone_tags": ["string"],
                    "strength_tags": ["string"],
                    "risk_tags": ["string"],
                    "common_patterns": ["string"],
                },
            },
        }

        messages = [
            {
                "role": "system",
                "content": "你是一名严谨的融资沟通教练，擅长发现创始人回答中的缺口、表达漂移和证据不足问题。",
            },
            {
                "role": "user",
                "content": json.dumps(prompt, ensure_ascii=False, indent=2),
            },
        ]
        return self._post_chat_completion(messages=messages, temperature=0.2, timeout_seconds=60.0)

    def _run_transcript_reconstruction_prompt(self, transcript_text: str) -> dict[str, Any] | None:
        prompt = {
            "task": "reconstruct_dialogue_roles",
            "goal": "把融资沟通转写还原成按说话人切分的对话，尽量区分投资人和创始人。",
            "requirements": [
                "只能使用两个角色标签：投资人： 和 我：",
                "保持原意，不要发明新的事实。",
                "如果一句话明显是在发问，优先归给投资人。",
                "如果一句话明显是在解释业务、数据、计划、风险应对，优先归给我。",
                "返回 JSON，不要输出额外解释。",
            ],
            "raw_transcript": transcript_text,
            "json_schema": {
                "normalized_transcript": "投资人：...\n我：...\n投资人：...\n我：..."
            },
        }
        messages = [
            {
                "role": "system",
                "content": "你是一名擅长融资会议整理的助理，能够根据自然转写还原对话中的说话人角色。",
            },
            {
                "role": "user",
                "content": json.dumps(prompt, ensure_ascii=False, indent=2),
            },
        ]
        return self._post_chat_completion(messages=messages, temperature=0.1, timeout_seconds=45.0)

    def _post_chat_completion(
        self,
        *,
        messages: list[dict[str, Any]],
        temperature: float,
        timeout_seconds: float,
    ) -> dict[str, Any] | None:
        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError:
            return None

        try:
            content = response.json()["choices"][0]["message"]["content"]
            return _extract_json(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            return None


class MoonshotGateway(OpenAICompatibleGateway):
    def __init__(self, api_key: str, base_url: str, model: str):
        super().__init__(provider="moonshot", api_key=api_key, base_url=base_url, model=model)


class QwenGateway(OpenAICompatibleGateway):
    def __init__(self, api_key: str, base_url: str, model: str):
        super().__init__(provider="qwen", api_key=api_key, base_url=base_url, model=model)


def build_llm_gateway(
    *,
    provider: str,
    moonshot_api_key: str,
    moonshot_base_url: str,
    moonshot_model: str,
    qwen_api_key: str,
    qwen_base_url: str,
    qwen_model: str,
) -> OpenAICompatibleGateway | None:
    normalized_provider = (provider or "auto").strip().lower()

    if normalized_provider == "disabled":
        return None
    if normalized_provider in {"moonshot", "kimi"}:
        return MoonshotGateway(api_key=moonshot_api_key, base_url=moonshot_base_url, model=moonshot_model)
    if normalized_provider in {"qwen", "dashscope", "tongyi"}:
        return QwenGateway(api_key=qwen_api_key, base_url=qwen_base_url, model=qwen_model)

    if moonshot_api_key:
        return MoonshotGateway(api_key=moonshot_api_key, base_url=moonshot_base_url, model=moonshot_model)
    if qwen_api_key:
        return QwenGateway(api_key=qwen_api_key, base_url=qwen_base_url, model=qwen_model)
    return None


def _history_context(history: list[MeetingRecord]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for meeting in history[-5:]:
        for qa in meeting.qa_exchanges[:4]:
            rows.append(
                {
                    "topic_id": qa.topic_id,
                    "topic_name": qa.topic_name,
                    "question": qa.question_text[:180],
                    "answer_excerpt": qa.answer_text[:220],
                    "overall_hint": {
                        "completeness_score": qa.review.completeness_score,
                        "evidence_score": qa.review.evidence_score,
                        "consistency_score": qa.review.consistency_score,
                    },
                }
            )
    return rows


def _extract_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            text = text.split("\n", 1)[1]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise json.JSONDecodeError("json object not found", text, 0)
    return json.loads(text[start : end + 1])


def _normalize_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result = []
    seen = set()
    for item in value:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _normalize_score(value: Any, fallback: int) -> int:
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return fallback


def _has_explicit_roles(transcript_text: str) -> bool:
    return "投资人：" in transcript_text or "我：" in transcript_text
