from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from app.models import MeetingRecord


class JsonStateStore:
    def __init__(self, path: Path):
        self.path = path
        self.lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"meetings": []})

    def list_meetings(self) -> list[MeetingRecord]:
        payload = self._read()
        return [MeetingRecord.model_validate(item) for item in payload.get("meetings", [])]

    def get_meeting(self, meeting_id: str) -> MeetingRecord | None:
        meetings = self.list_meetings()
        return next((meeting for meeting in meetings if meeting.id == meeting_id), None)

    def save_meeting(self, meeting: MeetingRecord) -> MeetingRecord:
        with self.lock:
            payload = self._read()
            meetings = payload.get("meetings", [])
            updated = False
            for index, item in enumerate(meetings):
                if item["id"] == meeting.id:
                    meetings[index] = meeting.model_dump(mode="json")
                    updated = True
                    break
            if not updated:
                meetings.append(meeting.model_dump(mode="json"))
            payload["meetings"] = meetings
            self._write(payload)
        return meeting

    def reset(self) -> None:
        with self.lock:
            self._write({"meetings": []})

    def _read(self) -> dict:
        if not self.path.exists():
            return {"meetings": []}
        raw = self.path.read_text(encoding="utf-8").strip()
        if not raw:
            return {"meetings": []}
        return json.loads(raw)

    def _write(self, payload: dict) -> None:
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

