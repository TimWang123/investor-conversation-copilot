from __future__ import annotations

from pathlib import Path
import re
import subprocess

from fastapi import HTTPException, UploadFile
from app.config import (
    ASR_COMPUTE_TYPE,
    ASR_DEVICE,
    ASR_MODEL_SIZE,
    LLM_PROVIDER,
    MODELS_DIR,
    MOONSHOT_API_KEY,
    MOONSHOT_BASE_URL,
    MOONSHOT_MODEL,
    QWEN_API_KEY,
    QWEN_BASE_URL,
    QWEN_MODEL,
    SAMPLES_DIR,
    UPLOADS_DIR,
    save_local_settings,
)
from app.models import (
    AppSettingsResponse,
    CreateMeetingRequest,
    DashboardSummary,
    DemoSampleResponse,
    LlmSettingsPayload,
    MeetingListItem,
    MeetingRecord,
    SettingOption,
    TopicDetail,
    UpdateAsrSettingsRequest,
    UpdateLlmSettingsRequest,
    new_id,
)
from app.services.analysis import (
    build_canonical_answers,
    build_topic_summaries,
    build_training_script,
    process_meeting,
)
from app.services.llm_gateway import LlmGateway, build_llm_gateway
from app.services.transcription_service import FasterWhisperTranscriptionService
from app.storage import JsonStateStore


class MeetingService:
    LLM_PROVIDER_OPTIONS = [
        SettingOption(value="disabled", label="关闭 LLM", description="只使用本地规则分析，不调用外部大模型。"),
        SettingOption(value="moonshot", label="Moonshot / Kimi", description="使用 Moonshot / Kimi 做转写重建和复盘增强。"),
        SettingOption(value="qwen", label="Qwen / 千问", description="使用阿里云百炼的千问模型做转写重建和复盘增强。"),
    ]
    ASR_MODEL_OPTIONS = [
        SettingOption(value="base", label="base", description="更轻更快，适合流程演示和较老电脑。"),
        SettingOption(value="small", label="small", description="默认推荐，速度和中文会议准确率更平衡。"),
        SettingOption(value="medium", label="medium", description="更重但更稳，适合更在意识别质量的场景。"),
        SettingOption(value="large-v3", label="large-v3", description="准确率更强，但更慢，更适合高配机器。"),
        SettingOption(value="turbo", label="turbo", description="偏高配场景，追求更快的大模型转写体验。"),
    ]
    CPU_COMPUTE_OPTIONS = [
        SettingOption(value="int8", label="int8", description="默认推荐，CPU 上更省内存、更稳。"),
        SettingOption(value="float32", label="float32", description="更重更慢，适合少量高精度 CPU 测试。"),
    ]
    CUDA_COMPUTE_OPTIONS = [
        SettingOption(value="float16", label="float16", description="默认推荐，适合大多数 NVIDIA GPU。"),
        SettingOption(value="int8_float16", label="int8_float16", description="更省显存，适合显存更紧张的 GPU。"),
        SettingOption(value="int8", label="int8", description="进一步压缩显存占用，但速度和精度可能略有波动。"),
    ]

    def __init__(
        self,
        store: JsonStateStore,
        llm_gateway: LlmGateway | None = None,
        transcription_service: FasterWhisperTranscriptionService | None = None,
        settings_file: Path | None = None,
        llm_provider_name: str = LLM_PROVIDER,
        moonshot_model: str = MOONSHOT_MODEL,
        qwen_model: str = QWEN_MODEL,
        moonshot_api_key: str = MOONSHOT_API_KEY,
        moonshot_base_url: str = MOONSHOT_BASE_URL,
        qwen_api_key: str = QWEN_API_KEY,
        qwen_base_url: str = QWEN_BASE_URL,
    ):
        self.store = store
        self.llm_gateway = llm_gateway
        self.transcription_service = transcription_service
        self.settings_file = settings_file
        self._hardware_probe_cache: tuple[bool, str | None] | None = None
        self.llm_provider_name = (llm_provider_name or "disabled").strip().lower()
        self.moonshot_model = moonshot_model
        self.qwen_model = qwen_model
        self.moonshot_api_key = moonshot_api_key
        self.moonshot_base_url = moonshot_base_url
        self.qwen_api_key = qwen_api_key
        self.qwen_base_url = qwen_base_url

        if self.llm_gateway is not None:
            status = self.llm_gateway.status()
            self.llm_provider_name = status.get("provider") or self.llm_provider_name
            active_model = status.get("model") or ""
            if self.llm_provider_name == "moonshot" and active_model:
                self.moonshot_model = active_model
            if self.llm_provider_name == "qwen" and active_model:
                self.qwen_model = active_model

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
        investor_names: str = "",
        founder_participants: str = "",
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
            investor_names=self._split_participant_input(investor_names),
            founder_participants=self._split_participant_input(founder_participants),
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
            return {"provider": None, "enabled": False, "model": None, "device": None, "compute_type": None}
        return self.transcription_service.status()

    def get_app_settings(self) -> AppSettingsResponse:
        asr_status = self.transcription_status()
        llm_status = self.llm_status()
        model_size = asr_status.get("model") or ASR_MODEL_SIZE
        device = asr_status.get("device") or getattr(self.transcription_service, "device", ASR_DEVICE)
        compute_type = getattr(self.transcription_service, "compute_type", ASR_COMPUTE_TYPE)
        device_options = self._device_options(current_device=device)
        compute_type_options = self._compute_type_options(device=device)
        selected_provider = self._selected_llm_provider()
        return AppSettingsResponse(
            asr={
                "model_size": model_size,
                "device": device,
                "compute_type": compute_type,
                "model_options": self.ASR_MODEL_OPTIONS,
                "device_options": device_options,
                "compute_type_options": compute_type_options,
                "note": self._settings_note(device=device),
            },
            llm=LlmSettingsPayload(
                provider=selected_provider,
                model=self._selected_llm_model(selected_provider),
                provider_options=self.LLM_PROVIDER_OPTIONS,
                enabled=bool(llm_status.get("enabled")),
                current_provider=llm_status.get("provider") or "disabled",
                current_model=llm_status.get("model") or "",
                note=self._llm_settings_note(selected_provider, bool(llm_status.get("enabled"))),
            ),
        )

    def update_asr_settings(self, payload: UpdateAsrSettingsRequest) -> AppSettingsResponse:
        allowed_model_values = {option.value for option in self.ASR_MODEL_OPTIONS}
        if payload.model_size not in allowed_model_values:
            raise HTTPException(status_code=400, detail="不支持的 ASR_MODEL_SIZE。")
        if payload.device not in {"cpu", "cuda"}:
            raise HTTPException(status_code=400, detail="不支持的 ASR_DEVICE。")
        allowed_compute_values = {option.value for option in self._compute_type_options(device=payload.device)}
        if payload.compute_type not in allowed_compute_values:
            raise HTTPException(status_code=400, detail="当前设备不支持这个 ASR_COMPUTE_TYPE。")
        if payload.device == "cuda" and not self._cuda_available():
            raise HTTPException(
                status_code=400,
                detail="当前机器未检测到可用的 NVIDIA CUDA 环境。AMD 或未安装 CUDA 的机器请继续使用 CPU。",
            )

        self.transcription_service = FasterWhisperTranscriptionService(
            model_size=payload.model_size,
            device=payload.device,
            compute_type=payload.compute_type,
            download_root=MODELS_DIR,
        )
        save_local_settings(
            {
                "ASR_MODEL_SIZE": payload.model_size,
                "ASR_DEVICE": payload.device,
                "ASR_COMPUTE_TYPE": payload.compute_type,
            },
            target_path=self.settings_file,
        )
        return self.get_app_settings()

    def update_llm_settings(self, payload: UpdateLlmSettingsRequest) -> AppSettingsResponse:
        provider = (payload.provider or "").strip().lower()
        if provider not in {option.value for option in self.LLM_PROVIDER_OPTIONS}:
            raise HTTPException(status_code=400, detail="不支持的 LLM provider。")

        model = payload.model.strip()
        if provider != "disabled" and not model:
            raise HTTPException(status_code=400, detail="请填写模型名称。")

        self.llm_provider_name = provider
        if provider == "moonshot":
            self.moonshot_model = model
        elif provider == "qwen":
            self.qwen_model = model

        settings_payload: dict[str, str] = {"LLM_PROVIDER": provider}
        if provider == "moonshot":
            settings_payload["MOONSHOT_MODEL"] = model
        elif provider == "qwen":
            settings_payload["QWEN_MODEL"] = model

        save_local_settings(settings_payload, target_path=self.settings_file)
        self.llm_gateway = self._build_runtime_llm_gateway()
        return self.get_app_settings()

    def _cuda_available(self) -> bool:
        available, _ = self._probe_nvidia_hardware()
        return available

    def _probe_nvidia_hardware(self) -> tuple[bool, str | None]:
        if self._hardware_probe_cache is not None:
            return self._hardware_probe_cache

        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            self._hardware_probe_cache = (False, None)
            return self._hardware_probe_cache

        if result.returncode != 0:
            self._hardware_probe_cache = (False, None)
            return self._hardware_probe_cache

        gpu_name = next((line.strip() for line in result.stdout.splitlines() if line.strip()), None)
        self._hardware_probe_cache = (bool(gpu_name), gpu_name)
        return self._hardware_probe_cache

    def _device_options(self, current_device: str) -> list[SettingOption]:
        has_cuda, gpu_name = self._probe_nvidia_hardware()
        options = [
            SettingOption(value="cpu", label="CPU", description="通用模式，适合所有机器，也兼容 AMD 显卡环境。"),
        ]
        if has_cuda or current_device == "cuda":
            gpu_label = f"NVIDIA GPU ({gpu_name})" if gpu_name else "NVIDIA GPU"
            options.append(
                SettingOption(
                    value="cuda",
                    label="GPU / CUDA",
                    description=f"检测到 {gpu_label}。需要本机已安装 CUDA 12 与 cuDNN 9 运行库。",
                )
            )
        return options

    def _compute_type_options(self, device: str) -> list[SettingOption]:
        if device == "cuda":
            return self.CUDA_COMPUTE_OPTIONS
        return self.CPU_COMPUTE_OPTIONS

    def _selected_llm_provider(self) -> str:
        provider = (self.llm_provider_name or "disabled").strip().lower()
        if provider in {option.value for option in self.LLM_PROVIDER_OPTIONS}:
            return provider
        return "disabled"

    def _selected_llm_model(self, provider: str) -> str:
        if provider == "moonshot":
            return self.moonshot_model
        if provider == "qwen":
            return self.qwen_model
        return ""

    def _llm_settings_note(self, provider: str, enabled: bool) -> str:
        if provider == "disabled":
            return "当前已关闭模型增强，只使用本地规则做问答抽取和复盘。"
        if provider == "moonshot":
            if enabled:
                return f"当前正在使用 Moonshot / Kimi，模型为 {self.moonshot_model}。保存后会立即用于后续转写重建和复盘。"
            return "已选择 Moonshot / Kimi，但当前进程里还没有可用的 MOONSHOT_API_KEY，因此暂时不会启用模型增强。"
        if provider == "qwen":
            if enabled:
                return f"当前正在使用 Qwen，模型为 {self.qwen_model}。推荐日常用 qwen3.5-plus，重要复盘可切 qwen3-max。"
            return "已选择 Qwen，但当前进程里还没有可用的 QWEN_API_KEY，因此暂时不会启用模型增强。"
        return "当前 LLM 设置尚未初始化。"

    def _build_runtime_llm_gateway(self) -> LlmGateway | None:
        return build_llm_gateway(
            provider=self.llm_provider_name,
            moonshot_api_key=self.moonshot_api_key,
            moonshot_base_url=self.moonshot_base_url,
            moonshot_model=self.moonshot_model,
            qwen_api_key=self.qwen_api_key,
            qwen_base_url=self.qwen_base_url,
            qwen_model=self.qwen_model,
        )

    def _settings_note(self, device: str) -> str:
        has_cuda, gpu_name = self._probe_nvidia_hardware()
        common_note = "切换新档位后，第一次做音频转写时会下载对应模型；之后会复用本地缓存。"
        if device == "cuda":
            return (
                f"{common_note} 当前选择的是 GPU / CUDA 模式。若转写时报错，请检查本机是否安装了 CUDA 12 和 cuDNN 9。"
            )
        if has_cuda and gpu_name:
            return f"{common_note} 已检测到 {gpu_name}，如果你想提速，可以切换到 GPU / CUDA。"
        return f"{common_note} 当前机器未检测到受支持的 NVIDIA CUDA 环境；AMD 或其他显卡环境建议继续使用 CPU。"

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

    def _split_participant_input(self, raw_value: str) -> list[str]:
        parts = re.split(r"[\n,，；;]+", raw_value)
        return [part.strip() for part in parts if part.strip()]
