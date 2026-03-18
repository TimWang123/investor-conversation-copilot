from __future__ import annotations

from dataclasses import dataclass


INVESTOR_PREFIXES = (
    "投资人",
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


@dataclass(slots=True)
class TranscriptTurn:
    speaker: str
    role: str
    text: str
    order: int


def parse_transcript(transcript_text: str) -> list[TranscriptTurn]:
    turns: list[TranscriptTurn] = []
    current: TranscriptTurn | None = None
    order = 0

    for raw_line in transcript_text.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        parsed = _parse_prefixed_line(line, order)
        if parsed:
            if current is not None:
                turns.append(current)
            current = parsed
            order += 1
            continue

        if current is None:
            inferred_role = "investor" if _looks_like_question(line) else "founder"
            current = TranscriptTurn(
                speaker="未标记",
                role=inferred_role,
                text=line,
                order=order,
            )
            order += 1
        else:
            # Labeled blocks can continue across multiple lines, but unlabeled
            # ASR output is usually already segmented per utterance and should
            # not be merged into one giant turn.
            if current.speaker != "未标记":
                current.text = f"{current.text} {line}".strip()
            else:
                turns.append(current)
                inferred_role = "investor" if _looks_like_question(line) else "founder"
                current = TranscriptTurn(
                    speaker="未标记",
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


def _looks_like_question(text: str) -> bool:
    markers = ("?", "？", "为什么", "怎么", "多少", "是否", "能否", "有没有")
    return any(marker in text for marker in markers)


def _normalize_unknown_roles(turns: list[TranscriptTurn]) -> list[TranscriptTurn]:
    if not turns:
        return turns

    normalized: list[TranscriptTurn] = []
    previous_role = "investor"
    for turn in turns:
        role = turn.role
        if role not in {"investor", "founder"}:
            role = "investor" if _looks_like_question(turn.text) else _flip_role(previous_role)
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
