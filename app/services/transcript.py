from __future__ import annotations

import re
from dataclasses import dataclass


UNKNOWN_SPEAKER = "未标注"

INVESTOR_PREFIXES = (
    "投资人",
    "投资方",
    "Investor",
    "VC",
    "Q",
    "问题",
)

FOUNDER_PREFIXES = (
    "我",
    "创始人",
    "Founder",
    "CEO",
    "回答",
    "A",
)

QUESTION_PATTERNS = (
    r"[?？]$",
    r"(是什么|为什么|为何|如何|怎么样|怎样|怎么|多少|哪个|哪些|哪一层|哪一类|是否|能否|可否|会不会|有没有|有何|有什么)",
    r"^(那|那么|另外|再|还有|然后).*(是什么|什么|如何|怎样|怎么样|计划|安排|多少|有没有|呢|吗|么)$",
)

INVESTOR_COMMENT_PATTERNS = (
    r"^(听起来|看起来|明白了|理解了|有意思|所以|也就是说)",
    r".*(不错|有吸引力|清楚了|明白了|理解了)$",
)


@dataclass(slots=True)
class TranscriptTurn:
    speaker: str
    role: str
    text: str
    order: int


def looks_like_question_text(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized or len(normalized) <= 4:
        return False
    return any(re.search(pattern, normalized, re.IGNORECASE) for pattern in QUESTION_PATTERNS)


def parse_transcript(transcript_text: str) -> list[TranscriptTurn]:
    turns: list[TranscriptTurn] = []
    current: TranscriptTurn | None = None
    order = 0

    for raw_line in transcript_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        parsed = _parse_prefixed_line(line, order)
        if parsed is not None:
            if current is not None:
                turns.append(current)
            current = parsed
            order += 1
            continue

        inferred_role = _infer_unlabeled_role(line, current.role if current else None)
        if current is None:
            current = TranscriptTurn(
                speaker=UNKNOWN_SPEAKER,
                role=inferred_role,
                text=line,
                order=order,
            )
            order += 1
            continue

        if current.speaker != UNKNOWN_SPEAKER:
            current.text = f"{current.text} {line}".strip()
            continue

        if inferred_role == current.role:
            current.text = f"{current.text} {line}".strip()
            continue

        turns.append(current)
        current = TranscriptTurn(
            speaker=UNKNOWN_SPEAKER,
            role=inferred_role,
            text=line,
            order=order,
        )
        order += 1

    if current is not None:
        turns.append(current)

    return _normalize_unknown_roles(turns)


def _parse_prefixed_line(line: str, order: int) -> TranscriptTurn | None:
    for prefix in INVESTOR_PREFIXES:
        value = _consume_prefix(line, prefix)
        if value is not None:
            return TranscriptTurn(speaker=prefix, role="investor", text=value, order=order)

    for prefix in FOUNDER_PREFIXES:
        value = _consume_prefix(line, prefix)
        if value is not None:
            return TranscriptTurn(speaker=prefix, role="founder", text=value, order=order)

    return None


def _consume_prefix(line: str, prefix: str) -> str | None:
    lower_line = line.lower()
    lower_prefix = prefix.lower()
    separators = (":", "：", "-", " ")
    for separator in separators:
        token = f"{lower_prefix}{separator}"
        if lower_line.startswith(token):
            return line[len(prefix) + len(separator) :].strip()
    if lower_line == lower_prefix:
        return ""
    return None


def _infer_unlabeled_role(text: str, previous_role: str | None) -> str:
    if looks_like_question_text(text):
        return "investor"
    if _looks_like_investor_comment(text):
        return "investor"
    if previous_role == "investor":
        return "founder"
    return previous_role or "founder"


def _looks_like_investor_comment(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return False
    return any(re.search(pattern, normalized, re.IGNORECASE) for pattern in INVESTOR_COMMENT_PATTERNS)


def _normalize_unknown_roles(turns: list[TranscriptTurn]) -> list[TranscriptTurn]:
    if not turns:
        return turns

    normalized: list[TranscriptTurn] = []
    previous_role = "investor"
    for turn in turns:
        role = turn.role
        if role not in {"investor", "founder"}:
            role = "investor" if looks_like_question_text(turn.text) else _flip_role(previous_role)
        previous_role = role
        normalized.append(
            TranscriptTurn(
                speaker=turn.speaker,
                role=role,
                text=turn.text.strip(),
                order=turn.order,
            )
        )
    return normalized


def _flip_role(role: str) -> str:
    return "founder" if role == "investor" else "investor"
