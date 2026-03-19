import { api } from "/static/api.js";

const elements = {
  titleInput: document.querySelector("#title"),
  meetingTypeInput: document.querySelector("#meeting-type"),
  investorOrgInput: document.querySelector("#investor-org"),
  transcriptInput: document.querySelector("#transcript"),
  audioFileInput: document.querySelector("#audio-file"),
  audioMeta: document.querySelector("#audio-meta"),
  recordStartButton: document.querySelector("#record-start"),
  recordStopButton: document.querySelector("#record-stop"),
  recordClearButton: document.querySelector("#record-clear"),
  settingsAsrModelSize: document.querySelector("#setting-asr-model-size"),
  settingsAsrDevice: document.querySelector("#setting-asr-device"),
  settingsAsrComputeType: document.querySelector("#setting-asr-compute-type"),
  settingsCurrentDevice: document.querySelector("#setting-asr-current-device"),
  settingsCurrentComputeType: document.querySelector("#setting-asr-current-compute-type"),
  settingsSaveButton: document.querySelector("#save-settings"),
  settingsStatus: document.querySelector("#settings-status"),
  settingsLlmProvider: document.querySelector("#setting-llm-provider"),
  settingsLlmModel: document.querySelector("#setting-llm-model"),
  settingsLlmCurrentProvider: document.querySelector("#setting-llm-current-provider"),
  settingsLlmCurrentModel: document.querySelector("#setting-llm-current-model"),
  settingsLlmSaveButton: document.querySelector("#save-llm-settings"),
  settingsLlmStatus: document.querySelector("#llm-settings-status"),
  runtimeHint: document.querySelector("#runtime-hint"),
  statusText: document.querySelector("#status-text"),
  overview: document.querySelector("#overview"),
  qaList: document.querySelector("#qa-list"),
  historyList: document.querySelector("#history-list"),
  topicsList: document.querySelector("#topics-list"),
  canonicalAnswer: document.querySelector("#canonical-answer"),
  trainingScript: document.querySelector("#training-script"),
  totalMeetings: document.querySelector("#metric-total-meetings"),
  totalQa: document.querySelector("#metric-total-qa"),
  averageScore: document.querySelector("#metric-average-score"),
  hottestTopic: document.querySelector("#metric-hottest-topic"),
  loadSampleButton: document.querySelector("#load-sample"),
  analyzeButton: document.querySelector("#analyze"),
  resetButton: document.querySelector("#reset-demo"),
};

const state = {
  dashboard: null,
  currentMeeting: null,
  selectedTopicId: null,
  settings: null,
  audioBlob: null,
  audioFilename: null,
  audioSource: "audio_upload",
  mediaRecorder: null,
  mediaStream: null,
};

elements.loadSampleButton.addEventListener("click", loadSample);
elements.analyzeButton.addEventListener("click", analyzeMeeting);
elements.resetButton.addEventListener("click", resetDemo);
elements.audioFileInput.addEventListener("change", handleAudioFileChange);
elements.recordStartButton.addEventListener("click", startRecording);
elements.recordStopButton.addEventListener("click", stopRecording);
elements.recordClearButton.addEventListener("click", clearAudioSelection);
elements.settingsAsrDevice.addEventListener("change", handleSettingsDeviceChange);
elements.settingsSaveButton.addEventListener("click", saveSettings);
elements.settingsLlmProvider.addEventListener("change", handleLlmProviderChange);
elements.settingsLlmSaveButton.addEventListener("click", saveLlmSettings);

bootstrap();

async function bootstrap() {
  await checkRuntime();
  await loadSettings();
  await refreshDashboard({ preferLatest: true });
}

async function checkRuntime() {
  if (window.location.protocol === "file:") {
    elements.runtimeHint.innerHTML =
      '你现在很可能是直接打开了 HTML 文件，所以页面无法访问后端接口。请先运行 <code>.\\.venv\\Scripts\\python -m uvicorn app.main:app --reload</code>，再用 <code>http://127.0.0.1:8000</code> 打开。';
    return;
  }

  try {
    const health = await api.health();
    elements.runtimeHint.classList.add("ok");
    const llmHint =
      health.llm_enabled === "true"
        ? `模型增强已启用，当前使用 ${escapeHtml(health.llm_model || health.llm_provider)}。`
        : "当前处于本地规则分析模式。";
    const asrHint =
      health.asr_enabled === "true"
        ? `音频转写已启用，当前模型是 ${escapeHtml(health.asr_model || health.asr_provider)}，设备为 ${escapeHtml(health.asr_device || "cpu")}，计算类型为 ${escapeHtml(health.asr_compute_type || "int8")}。`
        : "音频转写未启用。";
    elements.runtimeHint.innerHTML = `后端连接正常。${llmHint} ${asrHint}`;
  } catch (error) {
    showRuntimeError(error, "后端未连接");
  }
}

async function loadSettings() {
  try {
    const settings = await api.settings();
    state.settings = settings;
    renderSettings(settings);
  } catch (error) {
    elements.settingsStatus.textContent = "设置加载失败，请检查后端是否已启动。";
  }
}

function renderSettings(settings) {
  const asr = settings.asr;
  const llm = settings.llm;
  renderSelectOptions(elements.settingsAsrModelSize, asr.model_options, asr.model_size);
  renderSelectOptions(elements.settingsAsrDevice, asr.device_options, asr.device);
  renderComputeTypeOptions(asr.compute_type_options, asr.compute_type);
  elements.settingsCurrentDevice.textContent = asr.device || "cpu";
  elements.settingsCurrentComputeType.textContent = asr.compute_type || "int8";
  elements.settingsStatus.textContent = asr.note || "可以在这里调整本地转写模型配置。";
  renderSelectOptions(elements.settingsLlmProvider, llm.provider_options, llm.provider);
  elements.settingsLlmModel.value = llm.model || "";
  elements.settingsLlmCurrentProvider.textContent = llm.current_provider || "disabled";
  elements.settingsLlmCurrentModel.textContent = llm.current_model || "-";
  elements.settingsLlmStatus.textContent = llm.note || "这里可以切换模型提供方和模型名。";
  updateLlmModelPlaceholder(llm.provider);
}

function renderSelectOptions(selectElement, options, selectedValue) {
  selectElement.innerHTML = options
    .map((option) => {
      const selected = option.value === selectedValue ? " selected" : "";
      return `<option value="${escapeHtml(option.value)}"${selected}>${escapeHtml(option.label)} - ${escapeHtml(option.description)}</option>`;
    })
    .join("");
}

function renderComputeTypeOptions(options, selectedValue) {
  elements.settingsAsrComputeType.innerHTML = options
    .map((option) => {
      const selected = option.value === selectedValue ? " selected" : "";
      return `<option value="${escapeHtml(option.value)}"${selected}>${escapeHtml(option.label)} - ${escapeHtml(option.description)}</option>`;
    })
    .join("");
}

function handleLlmProviderChange() {
  updateLlmModelPlaceholder(elements.settingsLlmProvider.value);
}

function updateLlmModelPlaceholder(provider) {
  if (provider === "qwen") {
    elements.settingsLlmModel.placeholder = "例如 qwen3.5-plus 或 qwen3-max";
    if (!elements.settingsLlmModel.value.trim()) {
      elements.settingsLlmModel.value = "qwen3.5-plus";
    }
    return;
  }

  if (provider === "moonshot") {
    elements.settingsLlmModel.placeholder = "例如 kimi-latest";
    if (!elements.settingsLlmModel.value.trim()) {
      elements.settingsLlmModel.value = "kimi-latest";
    }
    return;
  }

  elements.settingsLlmModel.placeholder = "当前已关闭模型增强";
  if (provider === "disabled") {
    elements.settingsLlmModel.value = "";
  }
}

function handleSettingsDeviceChange() {
  if (!state.settings) {
    return;
  }
  const asr = state.settings.asr;
  const nextDevice = elements.settingsAsrDevice.value;
  const cpuOptions = asr.compute_type_options;
  const allDeviceOptions = asr.device_options;
  const selectedDevice = allDeviceOptions.find((option) => option.value === nextDevice)?.value || nextDevice;
  const computeOptions =
    selectedDevice === asr.device
      ? asr.compute_type_options
      : selectedDevice === "cuda"
        ? [
            { value: "float16", label: "float16", description: "默认推荐，适合大多数 NVIDIA GPU。" },
            { value: "int8_float16", label: "int8_float16", description: "更省显存，适合显存更紧张的 GPU。" },
            { value: "int8", label: "int8", description: "进一步压缩显存占用，但速度和精度可能略有波动。" },
          ]
        : [
            { value: "int8", label: "int8", description: "默认推荐，CPU 上更省内存、更稳。" },
            { value: "float32", label: "float32", description: "更重更慢，适合少量高精度 CPU 测试。" },
          ];

  renderComputeTypeOptions(computeOptions, computeOptions[0]?.value || cpuOptions[0]?.value || "int8");
}

async function loadSample() {
  try {
    setStatus("正在载入示例对话...");
    clearAudioSelection({ silent: true });
    const sample = await api.sampleTranscript();
    elements.titleInput.value = sample.title;
    elements.meetingTypeInput.value = sample.meeting_type;
    elements.investorOrgInput.value = sample.investor_org;
    elements.transcriptInput.value = sample.transcript_text;
    setStatus("示例已载入，可以直接生成复盘。");
  } catch (error) {
    showRuntimeError(error, "载入示例失败");
  }
}

async function analyzeMeeting() {
  const transcriptText = elements.transcriptInput.value.trim();
  const hasAudio = Boolean(state.audioBlob);
  if (!hasAudio && !transcriptText) {
    setStatus("请先输入会议转写内容，或者上传一段音频。");
    return;
  }

  setStatus(
    hasAudio
      ? "正在转写音频并生成复盘。首次使用新 ASR 模型时可能会下载本地模型，请稍等。"
      : "正在分析会议内容，这一步会抽取问答、生成复盘并刷新主题库。"
  );
  elements.overview.textContent = "处理中，请稍候。";

  try {
    const meeting = hasAudio ? await submitAudioMeeting() : await submitTranscriptMeeting(transcriptText);
    state.currentMeeting = meeting;
    state.selectedTopicId = meeting.qa_exchanges[0]?.topic_id || null;
    elements.transcriptInput.value = meeting.transcript_text || transcriptText;
    await refreshDashboard();
    renderMeeting(meeting);
    if (state.selectedTopicId) {
      await selectTopic(state.selectedTopicId, { silent: true });
    }
    setStatus(`分析完成，已识别 ${meeting.qa_exchanges.length} 组有效问答。`);
  } catch (error) {
    showRuntimeError(error, "分析失败");
  }
}

async function saveSettings() {
  const modelSize = elements.settingsAsrModelSize.value;
  const device = elements.settingsAsrDevice.value;
  const computeType = elements.settingsAsrComputeType.value;

  if (!modelSize || !device || !computeType) {
    elements.settingsStatus.textContent = "请先完整选择模型档位、设备和计算类型。";
    return;
  }

  elements.settingsSaveButton.disabled = true;
  elements.settingsStatus.textContent = "正在保存设置并更新本地转写服务...";
  try {
    const settings = await api.updateAsrSettings({
      model_size: modelSize,
      device,
      compute_type: computeType,
    });
    state.settings = settings;
    renderSettings(settings);
    await checkRuntime();
    elements.settingsStatus.textContent = `已保存。当前使用 ${device} / ${computeType} / ${modelSize}，下一次音频分析会按新设置运行。`;
  } catch (error) {
    const message = error instanceof Error ? error.message : "未知错误";
    elements.settingsStatus.textContent = `保存失败：${message}`;
  } finally {
    elements.settingsSaveButton.disabled = false;
  }
}

async function saveLlmSettings() {
  const provider = elements.settingsLlmProvider.value;
  const model = elements.settingsLlmModel.value.trim();

  if (provider !== "disabled" && !model) {
    elements.settingsLlmStatus.textContent = "请先填写模型名称。";
    return;
  }

  elements.settingsLlmSaveButton.disabled = true;
  elements.settingsLlmStatus.textContent = "正在保存模型设置并刷新当前分析模式...";
  try {
    const settings = await api.updateLlmSettings({ provider, model });
    state.settings = settings;
    renderSettings(settings);
    await checkRuntime();
    const activeProvider = settings.llm.current_provider || "disabled";
    const activeModel = settings.llm.current_model || model || "-";
    elements.settingsLlmStatus.textContent = `已保存。当前生效为 ${activeProvider} / ${activeModel}。`;
  } catch (error) {
    const message = error instanceof Error ? error.message : "未知错误";
    elements.settingsLlmStatus.textContent = `保存失败：${message}`;
  } finally {
    elements.settingsLlmSaveButton.disabled = false;
  }
}

async function resetDemo() {
  try {
    await api.resetDemo();
    state.dashboard = null;
    state.currentMeeting = null;
    state.selectedTopicId = null;
    elements.transcriptInput.value = "";
    clearAudioSelection({ silent: true });
    renderEmptyDashboard();
    setStatus("演示数据已清空。");
  } catch (error) {
    showRuntimeError(error, "清空失败");
  }
}

async function refreshDashboard({ preferLatest = false } = {}) {
  try {
    const dashboard = await api.dashboard();
    state.dashboard = dashboard;
    renderMetrics(dashboard);
    renderHistory(dashboard.recent_meetings);
    renderTopics(dashboard.topics);
    renderTrainingScript(dashboard.training_script?.content);

    if (!dashboard.recent_meetings.length) {
      renderEmptyDashboard();
      return;
    }

    if (preferLatest && dashboard.latest_meeting_id) {
      await selectMeeting(dashboard.latest_meeting_id, { silent: true });
      return;
    }

    if (state.currentMeeting) {
      renderMeeting(state.currentMeeting);
    }

    if (!state.selectedTopicId && dashboard.topics[0]) {
      state.selectedTopicId = dashboard.topics[0].id;
      await selectTopic(state.selectedTopicId, { silent: true });
    }
  } catch (error) {
    showRuntimeError(error, "仪表盘加载失败");
  }
}

async function selectMeeting(meetingId, { silent = false } = {}) {
  try {
    const meeting = await api.getMeeting(meetingId);
    state.currentMeeting = meeting;
    renderMeeting(meeting);
    renderHistory(state.dashboard?.recent_meetings || []);
    if (!silent) {
      setStatus(`已切换到会议：${meeting.title}`);
    }
  } catch (error) {
    showRuntimeError(error, "会议详情加载失败");
  }
}

async function selectTopic(topicId, { silent = false } = {}) {
  try {
    const topicDetail = await api.getTopicDetail(topicId);
    state.selectedTopicId = topicId;
    renderTopics(state.dashboard?.topics || []);
    renderCanonicalAnswer(topicDetail);
    if (!silent) {
      setStatus(`已切换到主题：${topicDetail.topic.name}`);
    }
  } catch (error) {
    showRuntimeError(error, "主题详情加载失败");
  }
}

function renderMetrics(dashboard) {
  elements.totalMeetings.textContent = String(dashboard.total_meetings);
  elements.totalQa.textContent = String(dashboard.total_qa_pairs);
  elements.averageScore.textContent = dashboard.average_overall_score ?? "-";
  elements.hottestTopic.textContent = dashboard.hottest_topic ?? "-";
}

function renderMeeting(meeting) {
  const review = meeting.review;
  const style = meeting.style_profile;
  const strongest = review?.strongest_topics?.join("、") || "待识别";
  const weakest = review?.weakest_topics?.join("、") || "待识别";

  elements.overview.innerHTML = `
    <strong>${escapeHtml(meeting.title)}</strong><br />
    总评分 <strong>${review?.overall_score ?? "-"}</strong> / 100。${escapeHtml(review?.meeting_summary ?? "")}<br /><br />
    <strong>风格画像：</strong>${escapeHtml(style?.style_summary ?? "待生成")}<br />
    <strong>亮点主题：</strong>${escapeHtml(strongest)}<br />
    <strong>优先补强：</strong>${escapeHtml(weakest)}<br />
    <strong>预算汇报可讲价值：</strong>这套系统已经能把一场融资对话自动沉淀成“会议历史 + 主题库 + 标准话术 + 培训脚本”。
  `;

  if (!meeting.qa_exchanges.length) {
    elements.qaList.textContent = "还没有问答结果。";
    return;
  }

  elements.qaList.innerHTML = meeting.qa_exchanges
    .map((qa, index) => {
      const reviewItem = qa.review;
      const strengths = reviewItem?.strengths?.join("；") || "待补充";
      const weaknesses = reviewItem?.weaknesses?.join("；") || "暂无明显问题";
      const suggestions = reviewItem?.improvement_suggestions?.join("；") || "继续保持";
      return `
        <article class="qa-item">
          <h4>问答 ${index + 1} · ${escapeHtml(qa.topic_name)}</h4>
          <div class="pill-row">
            <span class="pill">完整性 ${reviewItem.completeness_score}</span>
            <span class="pill">清晰度 ${reviewItem.clarity_score}</span>
            <span class="pill">一致性 ${reviewItem.consistency_score}</span>
            <span class="pill">证据 ${reviewItem.evidence_score}</span>
          </div>
          <p><strong>投资人：</strong>${escapeHtml(qa.question_text)}</p>
          <p><strong>你的回答：</strong>${escapeHtml(qa.answer_text)}</p>
          <div class="score-grid">
            <div class="score-chip">简洁度<strong>${reviewItem.brevity_score}</strong></div>
            <div class="score-chip">风险表达<strong>${reviewItem.risk_score}</strong></div>
            <div class="score-chip">识别置信度<strong>${Math.round(qa.confidence * 100)}</strong></div>
          </div>
          <p><strong>优点：</strong>${escapeHtml(strengths)}</p>
          <p class="${reviewItem.weaknesses.length ? "risk" : ""}"><strong>不足：</strong>${escapeHtml(weaknesses)}</p>
          <p><strong>建议：</strong>${escapeHtml(suggestions)}</p>
        </article>
      `;
    })
    .join("");
}

function renderHistory(meetings) {
  if (!meetings.length) {
    elements.historyList.textContent = "还没有历史会议。";
    return;
  }

  elements.historyList.innerHTML = meetings
    .map(
      (meeting) => `
        <article class="list-item ${meeting.id === state.currentMeeting?.id ? "active" : ""}" data-meeting-id="${meeting.id}">
          <h4>${escapeHtml(meeting.title)}</h4>
          <div class="list-meta">
            <div>${escapeHtml(meeting.investor_org || "未填写机构")} · ${escapeHtml(labelMeetingType(meeting.meeting_type))}</div>
            <div>问答 ${meeting.qa_count} 组 · 评分 ${meeting.overall_score ?? "-"}</div>
          </div>
        </article>
      `
    )
    .join("");

  elements.historyList.querySelectorAll("[data-meeting-id]").forEach((node) => {
    node.addEventListener("click", () => selectMeeting(node.dataset.meetingId));
  });
}

function renderTopics(topics) {
  if (!topics.length) {
    elements.topicsList.textContent = "还没有主题。";
    return;
  }

  elements.topicsList.innerHTML = topics
    .map(
      (topic) => `
        <article class="list-item ${topic.id === state.selectedTopicId ? "active" : ""}" data-topic-id="${topic.id}">
          <h4>${escapeHtml(topic.name)}</h4>
          <div class="list-meta">
            <div>出现频次 ${topic.frequency} · 最近评分 ${topic.latest_score}</div>
            <div>${escapeHtml(topic.sample_questions[0] || topic.description)}</div>
          </div>
        </article>
      `
    )
    .join("");

  elements.topicsList.querySelectorAll("[data-topic-id]").forEach((node) => {
    node.addEventListener("click", () => selectTopic(node.dataset.topicId));
  });
}

function renderCanonicalAnswer(topicDetail) {
  const canonical = topicDetail.canonical_answers[0];
  if (!canonical) {
    elements.canonicalAnswer.textContent = "这个主题还没有生成标准话术。";
    return;
  }

  const lines = [
    topicDetail.topic.name,
    "",
    `一句话回答：${canonical.summary_answer}`,
    "",
    "推荐展开顺序：",
    ...canonical.structured_talking_points.map((item) => `- ${item}`),
  ];

  if (canonical.supporting_facts.length) {
    lines.push("", "优先引用的证据：");
    lines.push(...canonical.supporting_facts.slice(0, 4).map((item) => `- ${item}`));
  }

  lines.push("", "注意事项：");
  lines.push(...canonical.dos.slice(0, 2).map((item) => `- 要做：${item}`));
  lines.push(...canonical.donts.slice(0, 2).map((item) => `- 避免：${item}`));

  elements.canonicalAnswer.innerHTML = `<div class="canonical-box">${escapeHtml(lines.join("\n"))}</div>`;
}

function renderTrainingScript(content) {
  elements.trainingScript.textContent = content || "还没有生成培训脚本。";
}

function renderEmptyDashboard() {
  elements.totalMeetings.textContent = "0";
  elements.totalQa.textContent = "0";
  elements.averageScore.textContent = "-";
  elements.hottestTopic.textContent = "-";
  elements.overview.textContent = "还没有分析结果。先载入示例，或者粘贴一段会议转写再生成复盘。";
  elements.qaList.textContent = "还没有问答结果。";
  elements.historyList.textContent = "还没有历史会议。";
  elements.topicsList.textContent = "还没有主题。";
  elements.canonicalAnswer.textContent = "选择一个主题后，这里会显示该主题的统一回答框架和注意事项。";
  elements.trainingScript.textContent = "还没有生成培训脚本。";
}

function showRuntimeError(error, prefix) {
  const message = error instanceof Error ? error.message : "未知错误，请检查后端是否已启动。";
  const hint =
    '请确认你是通过 <code>http://127.0.0.1:8000</code> 打开的页面，并且已经运行 <code>.\\.venv\\Scripts\\python -m uvicorn app.main:app --reload</code>。';
  setStatus(`${prefix}：${message}`);
  elements.overview.innerHTML = `<strong>${escapeHtml(prefix)}</strong><br />${escapeHtml(message)}<br /><br />${hint}`;
  elements.runtimeHint.innerHTML = hint;
}

function setStatus(message) {
  elements.statusText.textContent = message;
}

async function submitTranscriptMeeting(transcriptText) {
  return api.createMeeting({
    title: elements.titleInput.value.trim() || "未命名会议",
    meeting_type: elements.meetingTypeInput.value,
    investor_org: elements.investorOrgInput.value.trim(),
    transcript_text: transcriptText,
  });
}

async function submitAudioMeeting() {
  const formData = new FormData();
  formData.append("title", elements.titleInput.value.trim() || "未命名音频会议");
  formData.append("meeting_type", elements.meetingTypeInput.value);
  formData.append("investor_org", elements.investorOrgInput.value.trim());
  formData.append("transcript_source", state.audioSource);
  formData.append("audio", state.audioBlob, state.audioFilename || "meeting.webm");
  return api.createMeetingFromAudio(formData);
}

function handleAudioFileChange(event) {
  const file = event.target.files?.[0];
  if (!file) {
    clearAudioSelection({ silent: true });
    return;
  }
  state.audioBlob = file;
  state.audioFilename = file.name;
  state.audioSource = "audio_upload";
  renderAudioMeta(`已选择音频文件：${file.name}，大小 ${(file.size / 1024 / 1024).toFixed(2)} MB。点击“生成复盘”后会先自动转写。`);
}

async function startRecording() {
  if (!navigator.mediaDevices?.getUserMedia) {
    setStatus("当前浏览器不支持录音，请改用音频文件上传。");
    return;
  }

  try {
    clearAudioSelection({ silent: true });
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const chunks = [];
    const recorder = new MediaRecorder(stream);

    recorder.addEventListener("dataavailable", (event) => {
      if (event.data.size > 0) {
        chunks.push(event.data);
      }
    });

    recorder.addEventListener("stop", () => {
      const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
      state.audioBlob = blob;
      state.audioFilename = `recording-${Date.now()}.webm`;
      state.audioSource = "audio_recording";
      renderAudioMeta(`已录制浏览器音频：${state.audioFilename}。点击“生成复盘”后会先自动转写。`);
      stream.getTracks().forEach((track) => track.stop());
      state.mediaRecorder = null;
      state.mediaStream = null;
      elements.recordStartButton.disabled = false;
      elements.recordStopButton.disabled = true;
    });

    recorder.start();
    state.mediaRecorder = recorder;
    state.mediaStream = stream;
    elements.recordStartButton.disabled = true;
    elements.recordStopButton.disabled = false;
    setStatus("正在录音，结束后点击“停止录音”。");
    renderAudioMeta("录音中。停止后会把这段音频用于自动转写。");
  } catch (error) {
    showRuntimeError(error, "录音启动失败");
  }
}

function stopRecording() {
  if (!state.mediaRecorder) {
    return;
  }
  state.mediaRecorder.stop();
  setStatus("录音已停止，正在准备音频。");
}

function clearAudioSelection(options = {}) {
  if (state.mediaStream) {
    state.mediaStream.getTracks().forEach((track) => track.stop());
  }
  state.mediaRecorder = null;
  state.mediaStream = null;
  state.audioBlob = null;
  state.audioFilename = null;
  state.audioSource = "audio_upload";
  elements.audioFileInput.value = "";
  elements.recordStartButton.disabled = false;
  elements.recordStopButton.disabled = true;
  renderAudioMeta("当前未选择音频，将按文本模式分析。");
  if (!options.silent) {
    setStatus("已清除音频选择。");
  }
}

function renderAudioMeta(message) {
  elements.audioMeta.textContent = message;
}

function labelMeetingType(value) {
  const mapping = {
    one_on_one: "一对一",
    roadshow: "路演",
    due_diligence: "尽调",
    follow_up: "跟进",
  };
  return mapping[value] || value;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
