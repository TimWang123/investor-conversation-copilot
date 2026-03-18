import { api } from "/static/api.js";

const elements = {
  titleInput: document.querySelector("#title"),
  meetingTypeInput: document.querySelector("#meeting-type"),
  investorOrgInput: document.querySelector("#investor-org"),
  transcriptInput: document.querySelector("#transcript"),
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
};

elements.loadSampleButton.addEventListener("click", loadSample);
elements.analyzeButton.addEventListener("click", analyzeMeeting);
elements.resetButton.addEventListener("click", resetDemo);

bootstrap();

async function bootstrap() {
  await checkRuntime();
  await refreshDashboard({ preferLatest: true });
}

async function checkRuntime() {
  if (window.location.protocol === "file:") {
    elements.runtimeHint.innerHTML =
      '你现在很可能是直接打开了 HTML 文件，所以页面无法访问后端接口。请先运行 <code>.\\.venv\\Scripts\\python -m uvicorn app.main:app --reload</code>，再用 <code>http://127.0.0.1:8000</code> 打开。';
    return;
  }

  try {
    await api.health();
    elements.runtimeHint.classList.add("ok");
    elements.runtimeHint.innerHTML =
      '后端连接正常。你现在可以载入示例，也可以直接粘贴新的会议转写。';
  } catch (error) {
    showRuntimeError(error, "后端未连接");
  }
}

async function loadSample() {
  try {
    setStatus("正在载入示例对话…");
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
  if (!transcriptText) {
    setStatus("请先输入会议转写内容。");
    return;
  }

  setStatus("正在分析会议内容，这一步会抽取问答、生成复盘并刷新知识库…");
  elements.overview.textContent = "处理中，请稍候。";

  const payload = {
    title: elements.titleInput.value.trim() || "未命名会议",
    meeting_type: elements.meetingTypeInput.value,
    investor_org: elements.investorOrgInput.value.trim(),
    transcript_text: transcriptText,
  };

  try {
    const meeting = await api.createMeeting(payload);
    state.currentMeeting = meeting;
    state.selectedTopicId = meeting.qa_exchanges[0]?.topic_id || null;
    await refreshDashboard();
    renderMeeting(meeting);
    if (state.selectedTopicId) {
      await selectTopic(state.selectedTopicId);
    }
    setStatus(`分析完成，已识别 ${meeting.qa_exchanges.length} 组有效问答。`);
  } catch (error) {
    showRuntimeError(error, "分析失败");
  }
}

async function resetDemo() {
  try {
    await api.resetDemo();
    state.dashboard = null;
    state.currentMeeting = null;
    state.selectedTopicId = null;
    elements.transcriptInput.value = "";
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
    <strong>${meeting.title}</strong><br />
    总评分 <strong>${review?.overall_score ?? "-"}</strong> / 100。${review?.meeting_summary ?? ""}<br /><br />
    <strong>风格画像：</strong>${style?.style_summary ?? "待生成"}<br />
    <strong>亮点主题：</strong>${strongest}<br />
    <strong>优先补强：</strong>${weakest}<br />
    <strong>预算申请时可讲的价值：</strong>这套系统已经能把一场融资对话自动沉淀成“会议历史 + 主题库 + 标准话术 + 培训脚本”。
  `;

  if (!meeting.qa_exchanges.length) {
    elements.qaList.textContent = "还没有问答结果。";
    return;
  }

  elements.qaList.innerHTML = meeting.qa_exchanges
    .map((qa, index) => {
      const reviewItem = qa.review;
      return `
        <article class="qa-item">
          <h4>问答 ${index + 1} · ${qa.topic_name}</h4>
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
          <p><strong>优点：</strong>${escapeHtml(reviewItem.strengths.join("；") || "待补充")}</p>
          <p class="${reviewItem.weaknesses.length ? "risk" : ""}"><strong>不足：</strong>${escapeHtml(reviewItem.weaknesses.join("；") || "暂无明显问题")}</p>
          <p><strong>建议：</strong>${escapeHtml(reviewItem.improvement_suggestions.join("；") || "继续保持")}</p>
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
            <div>出现频次 ${topic.frequency} · 最近质量分 ${topic.latest_score}</div>
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
    `${topicDetail.topic.name}`,
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
  const message =
    error instanceof Error ? error.message : "未知错误，请检查后端是否已启动。";
  const hint =
    '请确认你是通过 <code>http://127.0.0.1:8000</code> 打开的页面，并且已经运行 <code>.\\.venv\\Scripts\\python -m uvicorn app.main:app --reload</code>。';
  setStatus(`${prefix}：${message}`);
  elements.overview.innerHTML = `<strong>${prefix}</strong><br />${escapeHtml(message)}<br /><br />${hint}`;
  elements.runtimeHint.innerHTML = hint;
}

function setStatus(message) {
  elements.statusText.textContent = message;
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

