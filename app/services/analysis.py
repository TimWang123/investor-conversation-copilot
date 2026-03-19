from __future__ import annotations

import re
from collections import defaultdict
from statistics import mean

from app.models import (
    CanonicalAnswer,
    MeetingRecord,
    MeetingReview,
    QAExchange,
    QAReview,
    SpeakerReview,
    StyleProfile,
    TopicSummary,
    TrainingScript,
    new_id,
    utc_now_iso,
)
from app.services.transcript import TranscriptTurn, parse_transcript


TOPIC_LIBRARY = {
    "growth": {
        "name": "增长与业绩",
        "keywords": ("增长", "营收", "收入", "ARR", "GMV", "订单", "留存", "复购", "客户数"),
        "expected_points": ("最近 12 个月增长趋势", "核心经营指标", "复购或留存表现"),
        "dos": ("先讲结论，再给数据。", "用同比或环比强化说服力。"),
        "donts": ("不要只说增长快，不给具体口径。",),
    },
    "business_model": {
        "name": "商业模式",
        "keywords": ("商业模式", "收费", "毛利", "利润", "收入结构", "单价"),
        "expected_points": ("收入来源", "毛利结构", "客户付费逻辑"),
        "dos": ("把收入来源拆开说。", "说明为什么结构可持续。"),
        "donts": ("不要只讲愿景，不讲钱怎么来。",),
    },
    "unit_economics": {
        "name": "单位经济模型",
        "keywords": ("CAC", "LTV", "回本", "ROI", "获客成本", "客单价", "毛利"),
        "expected_points": ("获客成本", "回本周期", "单客终身价值"),
        "dos": ("给出明确的口径和时间范围。", "说明关键变量如何改善。"),
        "donts": ("不要把收入和利润混在一起。",),
    },
    "barrier": {
        "name": "壁垒与竞争",
        "keywords": ("壁垒", "护城河", "竞争", "对手", "替代", "优势", "差异化"),
        "expected_points": ("为什么别人难复制", "竞争优势来源", "已有验证结果"),
        "dos": ("把技术、数据、渠道、组织壁垒拆开说。",),
        "donts": ("不要只说我们更懂用户。",),
    },
    "team": {
        "name": "团队与执行力",
        "keywords": ("团队", "创始人", "背景", "招聘", "组织", "执行"),
        "expected_points": ("核心成员背景", "岗位互补", "过去执行成绩"),
        "dos": ("突出关键成员与阶段匹配度。",),
        "donts": ("不要只列头衔。",),
    },
    "fundraising": {
        "name": "融资规划",
        "keywords": ("融资", "估值", "资金", "用途", "轮次", "募资"),
        "expected_points": ("计划融资额", "资金用途", "阶段目标"),
        "dos": ("把资金用途和关键里程碑绑定。",),
        "donts": ("不要只说多融一点更安全。",),
    },
    "risk": {
        "name": "风险与合规",
        "keywords": ("风险", "合规", "监管", "政策", "法律", "牌照"),
        "expected_points": ("关键风险点", "缓释动作", "当前进展"),
        "dos": ("承认风险，再讲应对。",),
        "donts": ("不要说完全没有风险。",),
    },
    "market": {
        "name": "市场空间",
        "keywords": ("市场", "TAM", "空间", "赛道", "规模", "增速"),
        "expected_points": ("市场规模", "增长速度", "细分切入口"),
        "dos": ("给市场定义边界。",),
        "donts": ("不要把所有相关市场都算进来。",),
    },
}

DEFAULT_TOPIC = {
    "name": "综合问题",
    "keywords": (),
    "expected_points": ("先给结论", "补充证据", "说明下一步"),
    "dos": ("回答结构尽量清楚。",),
    "donts": ("不要绕开问题本身。",),
}

EVIDENCE_MARKERS = (
    "%",
    "万",
    "亿",
    "ARR",
    "GMV",
    "留存",
    "复购",
    "客户",
    "合同",
    "毛利",
    "净收入",
)

CAUTION_WORDS = ("目前", "阶段性", "正在", "预计", "计划", "谨慎", "验证", "观察")
AGGRESSIVE_WORDS = ("一定", "绝对", "百分之百", "完全没有风险", "稳赢", "必然")
QUESTION_HINTS = (
    "?",
    "？",
    "吗",
    "么",
    "为什么",
    "怎么",
    "多少",
    "是否",
    "能否",
    "能不能",
    "有没有",
    "请问",
    "想问",
    "想了解",
    "方便讲讲",
    "怎么看",
    "是什么",
    "会不会",
)


def process_meeting(meeting: MeetingRecord, history: list[MeetingRecord]) -> MeetingRecord:
    turns = parse_transcript(
        meeting.transcript_text,
        investor_names=meeting.investor_names,
        founder_participants=meeting.founder_participants,
    )
    qa_exchanges = extract_qa_pairs(turns, history)
    if not qa_exchanges:
        qa_exchanges = extract_qa_pairs_from_freeform_text(meeting.transcript_text, history)
    if not qa_exchanges:
        raise ValueError("没有从文本中识别出有效问答。建议使用更清晰的录音，或在转写后补充基本标点和断句。")

    style_profile = summarize_style(qa_exchanges)
    meeting_review = build_meeting_review(meeting, qa_exchanges, style_profile)

    meeting.qa_exchanges = qa_exchanges
    meeting.style_profile = style_profile
    meeting.review = meeting_review
    meeting.status = "processed"
    meeting.processed_at = utc_now_iso()
    return meeting


def extract_qa_pairs(turns: list[TranscriptTurn], history: list[MeetingRecord]) -> list[QAExchange]:
    qa_exchanges: list[QAExchange] = []
    index = 0

    while index < len(turns):
        turn = turns[index]
        if not _is_question_turn(turn):
            index += 1
            continue

        question_parts = [turn.text]
        question_speakers = [turn.speaker]
        index += 1
        while index < len(turns) and turns[index].role == "investor":
            question_parts.append(turns[index].text)
            question_speakers.append(turns[index].speaker)
            index += 1

        answer_parts: list[str] = []
        answer_speakers: list[str] = []
        while index < len(turns) and turns[index].role != "investor":
            answer_parts.append(turns[index].text)
            answer_speakers.append(turns[index].speaker)
            index += 1

        question_text = " ".join(part.strip() for part in question_parts if part.strip()).strip()
        answer_text = " ".join(part.strip() for part in answer_parts if part.strip()).strip()
        if not question_text or not answer_text:
            continue

        qa_exchanges.append(
            _build_qa_exchange(
                question_text,
                answer_text,
                history,
                question_speakers=_clean_speaker_names(question_speakers, fallback_role="investor"),
                answer_speakers=_clean_speaker_names(answer_speakers, fallback_role="founder"),
            )
        )

    return qa_exchanges


def extract_qa_pairs_from_freeform_text(
    transcript_text: str,
    history: list[MeetingRecord],
) -> list[QAExchange]:
    chunks = _segment_freeform_transcript(transcript_text)
    if len(chunks) < 2:
        return []

    qa_exchanges: list[QAExchange] = []
    index = 0
    while index < len(chunks):
        if not _looks_like_question_text(chunks[index]):
            index += 1
            continue

        question_parts = [chunks[index]]
        index += 1
        while index < len(chunks) and _looks_like_question_text(chunks[index]):
            question_parts.append(chunks[index])
            index += 1

        answer_parts: list[str] = []
        while index < len(chunks) and not _looks_like_question_text(chunks[index]):
            answer_parts.append(chunks[index])
            index += 1

        question_text = " ".join(part.strip() for part in question_parts if part.strip()).strip()
        answer_text = " ".join(part.strip() for part in answer_parts if part.strip()).strip()
        if not question_text or not answer_text:
            continue

        qa_exchanges.append(
            _build_qa_exchange(
                question_text,
                answer_text,
                history,
                question_speakers=["投资人"],
                answer_speakers=["我方"],
            )
        )

    return qa_exchanges


def classify_topic(question_text: str, answer_text: str) -> tuple[str, str]:
    combined = f"{question_text} {answer_text}".lower()
    best_topic_id = "general"
    best_score = 0

    for topic_id, definition in TOPIC_LIBRARY.items():
        score = sum(1 for keyword in definition["keywords"] if keyword.lower() in combined)
        if score > best_score:
            best_topic_id = topic_id
            best_score = score

    if best_topic_id == "general":
        return "general", DEFAULT_TOPIC["name"]
    return best_topic_id, TOPIC_LIBRARY[best_topic_id]["name"]


def _build_qa_exchange(
    question_text: str,
    answer_text: str,
    history: list[MeetingRecord],
    *,
    question_speakers: list[str] | None = None,
    answer_speakers: list[str] | None = None,
) -> QAExchange:
    topic_id, topic_name = classify_topic(question_text, answer_text)
    historical_answers = [
        qa.answer_text
        for item in history
        for qa in item.qa_exchanges
        if qa.topic_id == topic_id
    ]
    review = review_answer(question_text, answer_text, topic_id, historical_answers)
    return QAExchange(
        question_text=question_text,
        answer_text=answer_text,
        question_speakers=question_speakers or [],
        answer_speakers=answer_speakers or [],
        topic_id=topic_id,
        topic_name=topic_name,
        question_intent=f"围绕{topic_name}的投资人关注点",
        confidence=_confidence(question_text, answer_text),
        review=review,
    )


def review_answer(
    question_text: str,
    answer_text: str,
    topic_id: str,
    historical_answers: list[str],
) -> QAReview:
    topic_definition = TOPIC_LIBRARY.get(topic_id, DEFAULT_TOPIC)
    expected_points = topic_definition["expected_points"]
    answer_length = len(answer_text)
    sentence_count = max(1, len(re.findall(r"[。！？!?]", answer_text)))
    has_number = bool(re.search(r"\d", answer_text))
    evidence_hits = sum(1 for marker in EVIDENCE_MARKERS if marker.lower() in answer_text.lower())
    matched_points = sum(1 for point in expected_points if _soft_keyword_hit(point, answer_text))

    completeness_score = _clamp(52 + matched_points * 12 + min(answer_length // 40, 18))
    clarity_score = _clamp(78 - max((answer_length - 260) // 18, 0) - max(sentence_count - 6, 0) * 4)
    evidence_score = _clamp(50 + (12 if has_number else 0) + evidence_hits * 6)
    brevity_score = _score_brevity(answer_length)
    risk_score = _score_risk_expression(answer_text)
    consistency_score = _score_consistency(answer_text, historical_answers)

    strengths: list[str] = []
    weaknesses: list[str] = []
    suggestions: list[str] = []
    missing_points: list[str] = []

    if has_number or evidence_hits >= 2:
        strengths.append("回答里带了具体数据或经营事实，可信度更高。")
    else:
        weaknesses.append("数据支撑偏弱，投资人会继续追问真实性和稳定性。")
        suggestions.append("补充 1 到 2 个关键数字，例如 ARR、增长率、留存或毛利。")

    if matched_points >= 2:
        strengths.append("核心问题基本有回应，没有明显绕开主题。")
    else:
        weaknesses.append("关键点覆盖不够完整，容易让人觉得只答到表面。")
        missing_points.extend(point for point in expected_points if not _soft_keyword_hit(point, answer_text))
        suggestions.append("按“结论 -> 证明 -> 下一步”三段式回答，减少跳跃。")

    if clarity_score >= 75:
        strengths.append("表达结构相对清楚，适合路演场景快速理解。")
    else:
        weaknesses.append("回答偏长或层次不够清楚，重点容易被淹没。")
        suggestions.append("先用一句话给结论，再分 2 到 3 点展开。")

    if consistency_score < 70 and historical_answers:
        weaknesses.append("和历史口径的重合度偏低，建议检查是否存在表达漂移。")
        suggestions.append("和历史最佳回答对齐关键表述，避免不同场合讲法差异太大。")

    if risk_score < 70:
        weaknesses.append("表达略显激进，容易触发投资人对可兑现性的担心。")
        suggestions.append("把绝对化表述改成阶段性判断，并说明验证依据。")
    else:
        strengths.append("语气总体审慎，适合融资沟通中的风险管理。")

    if topic_id == "fundraising" and "用途" not in answer_text:
        missing_points.append("资金用途拆分")
        suggestions.append("把本轮资金拆成产品、销售、组织三部分，便于投资人判断效率。")

    if topic_id == "barrier" and not re.search(r"数据|技术|渠道|组织|供应链|品牌", answer_text):
        missing_points.append("壁垒来源拆分")
        suggestions.append("把壁垒拆成技术、数据、渠道或组织中的至少两项。")

    if topic_id == "unit_economics" and not re.search(r"CAC|LTV|回本|获客|毛利", answer_text, re.IGNORECASE):
        missing_points.append("单位经济核心指标")
        suggestions.append("明确说明 CAC、毛利和回本周期，否则很难支撑可复制性判断。")

    return QAReview(
        completeness_score=completeness_score,
        clarity_score=clarity_score,
        consistency_score=consistency_score,
        evidence_score=evidence_score,
        brevity_score=brevity_score,
        risk_score=risk_score,
        strengths=_dedupe_keep_order(strengths),
        weaknesses=_dedupe_keep_order(weaknesses),
        improvement_suggestions=_dedupe_keep_order(suggestions),
        missing_points=_dedupe_keep_order(missing_points),
    )


def summarize_style(qa_exchanges: list[QAExchange]) -> StyleProfile:
    answers = [qa.answer_text for qa in qa_exchanges]
    average_length = mean(len(answer) for answer in answers)
    data_ratio = mean(1 if re.search(r"\d", answer) else 0 for answer in answers)
    caution_ratio = mean(
        1 if any(word in answer for word in CAUTION_WORDS) else 0 for answer in answers
    )

    narrative_tag = "偏数据驱动" if data_ratio >= 0.45 else "偏故事驱动"
    structure_tag = "偏简洁" if average_length < 150 else "偏展开"
    risk_tag = "偏审慎" if caution_ratio >= 0.35 else "偏强势"

    strength_tags: list[str] = []
    risk_tags: list[str] = []
    common_patterns: list[str] = []

    if data_ratio >= 0.45:
        strength_tags.append("常用数据支撑结论")
    else:
        risk_tags.append("容易在关键回答里缺少指标")

    if average_length < 150:
        strength_tags.append("结论表达相对干净")
    else:
        risk_tags.append("容易展开过多，重点可能不够聚焦")

    if caution_ratio >= 0.35:
        strength_tags.append("风险表达相对克制")
    else:
        risk_tags.append("偶尔会显得承诺过满")

    common_patterns.append("习惯先给业务判断，再补充背景。")
    if data_ratio < 0.45:
        common_patterns.append("适合增加固定的数据锚点，提升复用性。")
    if average_length >= 150:
        common_patterns.append("建议把回答压缩为一句结论加三点展开。")

    return StyleProfile(
        style_summary=f"{narrative_tag}、{structure_tag}、{risk_tag}。",
        tone_tags=[narrative_tag, structure_tag, risk_tag],
        strength_tags=_dedupe_keep_order(strength_tags),
        risk_tags=_dedupe_keep_order(risk_tags),
        common_patterns=_dedupe_keep_order(common_patterns),
    )


def build_meeting_review(
    meeting: MeetingRecord,
    qa_exchanges: list[QAExchange],
    style_profile: StyleProfile,
) -> MeetingReview:
    overall_score = round(
        mean(
            (
                qa.review.completeness_score
                + qa.review.clarity_score
                + qa.review.consistency_score
                + qa.review.evidence_score
                + qa.review.brevity_score
                + qa.review.risk_score
            )
            / 6
            for qa in qa_exchanges
        )
    )

    ranked_topics = sorted(
        qa_exchanges,
        key=lambda item: (
            item.review.completeness_score
            + item.review.evidence_score
            + item.review.consistency_score
        ),
        reverse=True,
    )
    strongest_topics = _dedupe_keep_order([item.topic_name for item in ranked_topics[:3]])
    weakest_topics = _dedupe_keep_order([item.topic_name for item in ranked_topics[-2:]])

    suggestions = []
    for qa in qa_exchanges:
        suggestions.extend(qa.review.improvement_suggestions)
    top_improvements = _dedupe_keep_order(suggestions)[:4]
    speaker_reviews = _build_speaker_reviews(meeting, qa_exchanges)
    consistency_risks = _build_consistency_risks(meeting, qa_exchanges)
    follow_up_questions = _find_follow_up_questions(meeting)
    founder_speakers = [item.speaker_name for item in speaker_reviews if item.answer_count > 0]

    summary = (
        f"本场会议共识别出 {len(qa_exchanges)} 组有效问答。"
        f" 你的回答在 {', '.join(strongest_topics[:2]) or '核心主题'} 上较稳定，"
        f"但在 {', '.join(weakest_topics[:2]) or '部分主题'} 上仍有进一步标准化空间。"
    )
    if meeting.meeting_type != "one_on_one" or len(founder_speakers) >= 2:
        summary += (
            f" 本场多人会议中，系统识别到 {len(founder_speakers) or 1} 位我方发言人参与回答，"
            "已经开始按人拆分回答贡献和口径一致性。"
        )
    consistency_assessment = (
        "当前回答风格已经具备可复用雏形，适合进一步沉淀为统一对外口径。"
        if overall_score >= 76
        else "当前回答具备亮点，但标准化程度还不够，建议优先把高频问题收敛成固定框架。"
    )
    if consistency_risks:
        consistency_assessment += " 本场会议存在需要重点对齐的多人口径风险。"

    return MeetingReview(
        meeting_summary=summary,
        overall_score=overall_score,
        strongest_topics=strongest_topics,
        weakest_topics=weakest_topics,
        top_improvements=top_improvements,
        style_snapshot=style_profile.style_summary,
        consistency_assessment=consistency_assessment,
        speaker_reviews=speaker_reviews,
        consistency_risks=consistency_risks,
        follow_up_questions=follow_up_questions,
    )


def _build_speaker_reviews(meeting: MeetingRecord, qa_exchanges: list[QAExchange]) -> list[SpeakerReview]:
    grouped: dict[str, list[QAExchange]] = defaultdict(list)
    for qa in qa_exchanges:
        for speaker in qa.answer_speakers:
            grouped[speaker].append(qa)

    ordered_names = _dedupe_keep_order(meeting.founder_participants + list(grouped.keys()))
    reviews: list[SpeakerReview] = []
    for speaker_name in ordered_names:
        exchanges = grouped.get(speaker_name, [])
        if not exchanges:
            reviews.append(
                SpeakerReview(
                    speaker_name=speaker_name,
                    role="founder",
                    answer_count=0,
                    average_score=None,
                    strengths=[],
                    risks=["本场会议未识别到该成员的有效回答。"],
                )
            )
            continue

        average_score = round(
            mean(
                (
                    qa.review.completeness_score
                    + qa.review.clarity_score
                    + qa.review.consistency_score
                    + qa.review.evidence_score
                    + qa.review.brevity_score
                    + qa.review.risk_score
                )
                / 6
                for qa in exchanges
            )
        )
        clarity_avg = mean(qa.review.clarity_score for qa in exchanges)
        evidence_avg = mean(qa.review.evidence_score for qa in exchanges)
        consistency_avg = mean(qa.review.consistency_score for qa in exchanges)
        brevity_avg = mean(qa.review.brevity_score for qa in exchanges)

        strengths: list[str] = []
        risks: list[str] = []
        if evidence_avg >= 78:
            strengths.append("数据支撑较稳，适合承担指标类问题。")
        if clarity_avg >= 78:
            strengths.append("表达结构较清晰，适合正面承接投资人追问。")
        if consistency_avg < 72:
            risks.append("和历史口径或其他发言人的表述有一定漂移。")
        if brevity_avg < 70:
            risks.append("展开偏多，建议进一步收敛成固定答题框架。")
        if evidence_avg < 70:
            risks.append("证据密度偏弱，建议补足数字和经营事实。")

        reviews.append(
            SpeakerReview(
                speaker_name=speaker_name,
                role="founder",
                answer_count=len(exchanges),
                average_score=average_score,
                strengths=_dedupe_keep_order(strengths),
                risks=_dedupe_keep_order(risks),
            )
        )
    return reviews


def _build_consistency_risks(meeting: MeetingRecord, qa_exchanges: list[QAExchange]) -> list[str]:
    risks: list[str] = []
    active_founders = _dedupe_keep_order(
        [speaker for qa in qa_exchanges for speaker in qa.answer_speakers if speaker not in {"我方", "未标注"}]
    )
    if (meeting.meeting_type != "one_on_one" or len(meeting.founder_participants) > 1) and len(active_founders) < 2:
        risks.append("本场会议标记为多人场景，但当前只识别到一位我方主要回答人，建议补充发言人标签。")

    topic_grouped: dict[str, list[QAExchange]] = defaultdict(list)
    for qa in qa_exchanges:
        topic_grouped[qa.topic_id].append(qa)

    for exchanges in topic_grouped.values():
        topic_name = exchanges[0].topic_name
        speakers = _dedupe_keep_order(
            [speaker for qa in exchanges for speaker in qa.answer_speakers if speaker not in {"我方", "未标注"}]
        )
        if len(speakers) < 2:
            continue
        overlap = _topic_answer_overlap(exchanges)
        if overlap < 0.18:
            risks.append(f"{topic_name} 由多人分别回答，但表述差异较大，建议统一成同一套外部口径。")

    return _dedupe_keep_order(risks)[:4]


def _find_follow_up_questions(meeting: MeetingRecord) -> list[str]:
    turns = parse_transcript(
        meeting.transcript_text,
        investor_names=meeting.investor_names,
        founder_participants=meeting.founder_participants,
    )
    pending: list[str] = []
    index = 0
    while index < len(turns):
        if turns[index].role != "investor":
            index += 1
            continue

        question_parts = [turns[index].text]
        index += 1
        while index < len(turns) and turns[index].role == "investor":
            question_parts.append(turns[index].text)
            index += 1

        answered = False
        while index < len(turns) and turns[index].role != "investor":
            if turns[index].text.strip():
                answered = True
            index += 1

        if not answered:
            pending.append(" ".join(part.strip() for part in question_parts if part.strip()).strip())

    return _dedupe_keep_order([item for item in pending if item])[:4]


def build_topic_summaries(meetings: list[MeetingRecord]) -> list[TopicSummary]:
    grouped: dict[str, list[QAExchange]] = defaultdict(list)
    for meeting in meetings:
        for qa in meeting.qa_exchanges:
            grouped[qa.topic_id].append(qa)

    topics: list[TopicSummary] = []
    for topic_id, exchanges in grouped.items():
        latest_score = round(
            mean((qa.review.completeness_score + qa.review.evidence_score) / 2 for qa in exchanges)
        )
        topics.append(
            TopicSummary(
                id=topic_id,
                name=exchanges[0].topic_name,
                description=f"围绕{exchanges[0].topic_name}的投资人高频问题",
                frequency=len(exchanges),
                sample_questions=_dedupe_keep_order([qa.question_text for qa in exchanges])[:3],
                latest_score=latest_score,
            )
        )

    return sorted(topics, key=lambda item: (-item.frequency, item.name))


def build_canonical_answers(meetings: list[MeetingRecord], topic_id: str) -> list[CanonicalAnswer]:
    exchanges = [
        qa
        for meeting in meetings
        for qa in meeting.qa_exchanges
        if qa.topic_id == topic_id
    ]
    if not exchanges:
        return []

    exchanges.sort(
        key=lambda item: (
            item.review.completeness_score
            + item.review.evidence_score
            + item.review.clarity_score
        ),
        reverse=True,
    )
    topic_definition = TOPIC_LIBRARY.get(topic_id, DEFAULT_TOPIC)
    source_meeting_ids = _dedupe_keep_order(
        [meeting.id for meeting in meetings if any(qa.topic_id == topic_id for qa in meeting.qa_exchanges)]
    )

    canonical = CanonicalAnswer(
        topic_id=topic_id,
        version=len(source_meeting_ids),
        summary_answer=_compose_canonical_summary(exchanges[0].answer_text, topic_definition["name"]),
        structured_talking_points=list(topic_definition["expected_points"]),
        supporting_facts=_extract_supporting_facts([qa.answer_text for qa in exchanges])[:5],
        dos=list(topic_definition["dos"]),
        donts=list(topic_definition["donts"]),
        source_meeting_ids=source_meeting_ids,
        status="draft",
    )
    return [canonical]


def build_training_script(meetings: list[MeetingRecord]) -> TrainingScript | None:
    topics = build_topic_summaries(meetings)
    if not topics:
        return None

    sections: list[str] = [
        "# 新人融资沟通统一话术",
        "",
        "这份脚本由历史会议自动归纳生成，建议先背会结构，再根据实际数据替换其中的证据点。",
        "",
    ]
    topic_ids: list[str] = []
    canonical_ids: list[str] = []

    for index, topic in enumerate(topics, start=1):
        canonical_answers = build_canonical_answers(meetings, topic.id)
        if not canonical_answers:
            continue
        canonical = canonical_answers[0]
        topic_ids.append(topic.id)
        canonical_ids.append(canonical.id)
        sections.extend(
            [
                f"## {index}. {topic.name}",
                f"一句话回答：{canonical.summary_answer}",
                "",
                "推荐展开顺序：",
            ]
        )
        sections.extend([f"- {point}" for point in canonical.structured_talking_points])
        if canonical.supporting_facts:
            sections.append("")
            sections.append("优先引用的证据：")
            sections.extend([f"- {fact}" for fact in canonical.supporting_facts[:3]])
        sections.append("")
        sections.append("注意事项：")
        sections.extend([f"- 要做：{item}" for item in canonical.dos[:2]])
        sections.extend([f"- 避免：{item}" for item in canonical.donts[:2]])
        sections.append("")

    return TrainingScript(
        id=new_id("script"),
        version=len(meetings),
        script_title="新人融资沟通统一话术",
        content="\n".join(sections).strip(),
        topic_ids=topic_ids,
        source_canonical_answer_ids=canonical_ids,
    )


def _is_question_turn(turn: TranscriptTurn) -> bool:
    return turn.role == "investor" or any(token in turn.text for token in ("?", "？"))


def _clean_speaker_names(speakers: list[str], *, fallback_role: str) -> list[str]:
    fallback = "投资人" if fallback_role == "investor" else "我方"
    cleaned = [
        speaker.strip()
        for speaker in speakers
        if speaker and speaker.strip() and speaker.strip() not in {"未标注", "UNKNOWN"}
    ]
    return _dedupe_keep_order(cleaned) or [fallback]


def _topic_answer_overlap(exchanges: list[QAExchange]) -> float:
    if len(exchanges) < 2:
        return 1.0

    overlaps: list[float] = []
    for index, exchange in enumerate(exchanges):
        current_tokens = _meaningful_tokens(exchange.answer_text)
        if not current_tokens:
            continue
        for other in exchanges[index + 1 :]:
            other_tokens = _meaningful_tokens(other.answer_text)
            if not other_tokens:
                continue
            overlaps.append(len(current_tokens & other_tokens) / max(len(current_tokens | other_tokens), 1))
    if not overlaps:
        return 0.0
    return max(overlaps)


def _segment_freeform_transcript(transcript_text: str) -> list[str]:
    normalized = transcript_text.replace("\r\n", "\n").replace("\r", "\n")
    raw_parts = re.split(r"[\n]+|(?<=[。！？!?])", normalized)
    chunks = []
    for part in raw_parts:
        text = re.sub(r"\s+", " ", part).strip()
        if not text:
            continue
        chunks.append(text)
    return _merge_short_chunks(chunks)


def _merge_short_chunks(chunks: list[str]) -> list[str]:
    merged: list[str] = []
    for chunk in chunks:
        if not merged:
            merged.append(chunk)
            continue

        previous = merged[-1]
        if len(chunk) <= 6 and not _looks_like_question_text(chunk):
            merged[-1] = f"{previous}{chunk}"
            continue

        if len(previous) <= 6 and not _looks_like_question_text(previous) and not _looks_like_question_text(chunk):
            merged[-1] = f"{previous}{chunk}"
            continue

        merged.append(chunk)
    return merged


def _looks_like_question_text(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return False
    if normalized.endswith(("?", "？", "吗", "么")):
        return True
    return any(hint in normalized for hint in QUESTION_HINTS)


def _score_brevity(answer_length: int) -> int:
    if answer_length < 45:
        return 58
    if answer_length <= 180:
        return 88
    if answer_length <= 280:
        return 74
    return 62


def _score_risk_expression(answer_text: str) -> int:
    score = 72
    score += sum(6 for word in CAUTION_WORDS if word in answer_text)
    score -= sum(10 for word in AGGRESSIVE_WORDS if word in answer_text)
    return _clamp(score)


def _score_consistency(answer_text: str, historical_answers: list[str]) -> int:
    if not historical_answers:
        return 78
    current_tokens = _meaningful_tokens(answer_text)
    if not current_tokens:
        return 70

    overlaps = []
    for historical in historical_answers:
        tokens = _meaningful_tokens(historical)
        if not tokens:
            continue
        overlaps.append(len(current_tokens & tokens) / max(len(current_tokens), 1))
    if not overlaps:
        return 72
    return _clamp(round(60 + max(overlaps) * 35))


def _meaningful_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[A-Za-z]{2,}|\d+|[\u4e00-\u9fff]{2,}", text)
        if token not in {"我们", "目前", "这个", "因为", "所以", "然后", "就是"}
    }


def _soft_keyword_hit(point: str, answer_text: str) -> bool:
    keywords = re.findall(r"[A-Za-z]{2,}|[\u4e00-\u9fff]{2,}", point)
    return any(keyword.lower() in answer_text.lower() for keyword in keywords)


def _extract_supporting_facts(answer_texts: list[str]) -> list[str]:
    facts: list[str] = []
    patterns = (
        r"\d+(?:\.\d+)?\s*%",
        r"\d+(?:\.\d+)?\s*(?:万|亿|个月|周|天|家|人)",
        r"(?:ARR|GMV|CAC|LTV)\s*[^\s，。；;]*",
    )
    for text in answer_texts:
        for pattern in patterns:
            facts.extend(re.findall(pattern, text, re.IGNORECASE))
    return _dedupe_keep_order([fact.strip() for fact in facts if fact.strip()])


def _compose_canonical_summary(answer_text: str, topic_name: str) -> str:
    chunks = [chunk.strip() for chunk in re.split(r"[。！？!?]", answer_text) if chunk.strip()]
    if not chunks:
        return f"{topic_name}的回答需要先给结论，再补充证据。"
    summary = "；".join(chunks[:2])
    if len(summary) < 24:
        summary = f"{summary}，并补充关键数据与验证结果。"
    return summary


def _confidence(question_text: str, answer_text: str) -> float:
    base = 0.72
    if any(token in question_text for token in ("?", "？")):
        base += 0.08
    if len(answer_text) > 60:
        base += 0.06
    return round(min(base, 0.96), 2)


def _clamp(score: int) -> int:
    return max(0, min(100, score))


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result
