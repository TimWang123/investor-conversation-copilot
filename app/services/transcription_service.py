from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Any

from app.models import TranscriptionResult


class FasterWhisperTranscriptionService:
    def __init__(
        self,
        model_size: str,
        device: str,
        compute_type: str,
        download_root: Path,
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.download_root = download_root
        self.download_root.mkdir(parents=True, exist_ok=True)
        self._model = None
        self._lock = Lock()

    @property
    def enabled(self) -> bool:
        return True

    def status(self) -> dict[str, Any]:
        return {
            "provider": "faster-whisper",
            "enabled": self.enabled,
            "model": self.model_size,
            "device": self.device,
        }

    def transcribe(self, audio_path: Path, language: str | None = "zh") -> TranscriptionResult:
        model = self._get_model()
        segments_iter, info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
        )

        segments_payload: list[dict] = []
        texts: list[str] = []
        for segment in segments_iter:
            text = segment.text.strip()
            if not text:
                continue
            texts.append(text)
            segments_payload.append(
                {
                    "start": round(float(segment.start), 2),
                    "end": round(float(segment.end), 2),
                    "text": text,
                }
            )

        transcript_text = "\n".join(texts).strip()
        if not transcript_text:
            raise ValueError("音频已上传，但没有识别出可用文本。")

        duration = None
        if segments_payload:
            duration = float(segments_payload[-1]["end"])

        return TranscriptionResult(
            text=transcript_text,
            language=getattr(info, "language", language),
            duration_seconds=duration,
            segments=segments_payload,
        )

    def _get_model(self):
        if self._model is not None:
            return self._model

        with self._lock:
            if self._model is not None:
                return self._model
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=str(self.download_root),
            )
        return self._model

