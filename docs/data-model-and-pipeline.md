# 数据模型与 AI 流程

## 一、核心实体

### 1. Meeting

代表一次融资沟通。

建议字段：

- `id`
- `title`
- `meeting_type`
- `started_at`
- `ended_at`
- `investor_org`
- `investor_names`
- `founder_participants`
- `audio_url`
- `transcript_status`
- `analysis_status`
- `language`
- `created_by`

### 2. TranscriptSegment

代表一段带时间轴和说话人的转写结果。

建议字段：

- `id`
- `meeting_id`
- `speaker_label`
- `speaker_role`
- `start_ms`
- `end_ms`
- `text`
- `confidence`
- `raw_text`

### 3. QAExchange

代表一次问题与回答的配对结果。

建议字段：

- `id`
- `meeting_id`
- `question_segment_ids`
- `answer_segment_ids`
- `question_text`
- `answer_text`
- `topic_id`
- `question_intent`
- `confidence`

### 4. QuestionTopic

代表问题库中的一个主题。

建议字段：

- `id`
- `name`
- `description`
- `embedding`
- `sample_questions`
- `frequency`
- `last_seen_at`

### 5. AnswerReview

代表对一次回答的 AI 评估结果。

建议字段：

- `id`
- `qa_exchange_id`
- `completeness_score`
- `clarity_score`
- `consistency_score`
- `evidence_score`
- `brevity_score`
- `risk_score`
- `strengths`
- `weaknesses`
- `improvement_suggestions`
- `missing_points`

### 6. StyleProfile

代表阶段性的个人回答风格画像。

建议字段：

- `id`
- `subject_id`
- `time_window`
- `style_summary`
- `tone_tags`
- `strength_tags`
- `risk_tags`
- `common_patterns`
- `generated_at`

### 7. CanonicalAnswer

代表某个主题下的标准回答版本。

建议字段：

- `id`
- `topic_id`
- `version`
- `summary_answer`
- `structured_talking_points`
- `supporting_facts`
- `dos`
- `donts`
- `source_meeting_ids`
- `status`
- `approved_by`

### 8. TrainingScript

代表给新人的培训材料。

建议字段：

- `id`
- `version`
- `audience`
- `script_title`
- `content`
- `topic_ids`
- `source_canonical_answer_ids`
- `generated_at`

## 二、建议数据库关系

```text
Meeting 1 --- N TranscriptSegment
Meeting 1 --- N QAExchange
QAExchange 1 --- 1 AnswerReview
QAExchange N --- 1 QuestionTopic
QuestionTopic 1 --- N CanonicalAnswer
CanonicalAnswer N --- N TrainingScript
```

## 三、处理流水线

### Step 1. 音频接收

输入：

- 本地录音文件

处理：

- 校验格式
- 上传对象存储
- 记录会议元数据

输出：

- `Meeting`

### Step 2. 转写与说话人识别

输入：

- 音频 URL

处理：

- ASR 转写
- 时间轴切分
- speaker diarization
- 标记“投资人 / 我方 / 其他”

输出：

- `TranscriptSegment[]`

### Step 3. 问答抽取

输入：

- 会议全文转写

处理：

- 识别问题起止位置
- 识别对应回答范围
- 提取问题意图
- 抽取核心主题

输出：

- `QAExchange[]`

### Step 4. 问题归类与聚类

输入：

- 当前批次问答对
- 历史问题库

处理：

- 向量召回相似问题
- 判断归入已有主题还是创建新主题
- 更新主题频率和示例问题

输出：

- 更新后的 `QuestionTopic`

### Step 5. 回答评估

输入：

- 问答对
- 当前主题的历史标准答案
- 公司知识上下文

处理：

- 判断回答是否覆盖核心点
- 判断与历史口径是否冲突
- 给出缺失点与改写建议

输出：

- `AnswerReview`

### Step 6. 风格画像更新

输入：

- 多场会议中的回答集合

处理：

- 识别长期表达习惯
- 识别强项主题和薄弱主题
- 统计常见冗长或模糊表达模式

输出：

- `StyleProfile`

### Step 7. 标准话术生成

输入：

- 历史高质量回答
- 评估结论
- 最新战略口径

处理：

- 生成某主题下的推荐回答框架
- 输出关键词、证据点、禁忌表达
- 生成版本号

输出：

- `CanonicalAnswer`

### Step 8. 培训脚本生成

输入：

- 标准话术集合
- 高频问题排名

处理：

- 按场景组织内容
- 生成新人培训用回答模板
- 生成模拟问答练习题

输出：

- `TrainingScript`

## 四、建议的 AI Prompt 任务拆分

为了减少一次大模型调用做太多事情导致结果不稳定，建议拆成多个小任务：

### Prompt A：说话人角色校正

目标：

- 把 `speaker_1 / speaker_2` 校正为 `investor / founder / teammate`

### Prompt B：问题识别

目标：

- 找出投资人真正关心的问题
- 合并连续追问

### Prompt C：回答配对

目标：

- 给每个问题找出主回答区间
- 排除插话、寒暄和打断

### Prompt D：回答评分

目标：

- 从多维度打分
- 输出缺失信息与具体建议

### Prompt E：风格总结

目标：

- 总结你最近 N 场会议的表达风格
- 标出稳定优势和常见短板

### Prompt F：标准话术生成

目标：

- 把高质量回答转为可培训的统一表达框架

## 五、建议评分维度

为了让复盘更稳定，建议每次回答统一打分：

- `是否回答到了问题本身`
- `是否覆盖投资人真正关心的核心点`
- `是否给了数据、案例或证据`
- `是否和历史口径一致`
- `是否容易让外部人理解`
- `是否过度承诺`
- `是否过长`

每一维都应输出：

- 分数
- 评分理由
- 可操作改进建议

## 六、标准话术应该长什么样

建议生成结构化结果，而不是纯自然语言大段文本：

```json
{
  "topic": "为什么你们有壁垒",
  "core_answer": "一句话标准回答",
  "three_key_points": [
    "点一",
    "点二",
    "点三"
  ],
  "supporting_evidence": [
    "关键数据",
    "客户案例"
  ],
  "follow_up_answers": [
    {
      "question": "如果投资人继续追问技术壁垒？",
      "answer": "推荐二层回答"
    }
  ],
  "dos": [
    "先讲结论再讲证明"
  ],
  "donts": [
    "不要只说愿景不说证据"
  ]
}
```

## 七、MVP API 草案

### 1. 创建会议

- `POST /api/meetings`

### 2. 获取上传地址

- `POST /api/meetings/{id}/upload-url`

### 3. 提交处理任务

- `POST /api/meetings/{id}/process`

### 4. 查询会议详情

- `GET /api/meetings/{id}`

### 5. 查询问答列表

- `GET /api/meetings/{id}/qa-exchanges`

### 6. 查询复盘结论

- `GET /api/meetings/{id}/review`

### 7. 查询问题库

- `GET /api/topics`

### 8. 查询某主题标准答案

- `GET /api/topics/{id}/canonical-answers`

### 9. 查询培训脚本

- `GET /api/training-scripts/latest`

## 八、建议的演进策略

### 第一阶段：验证价值

目标：

- 让单次会议复盘真正有用

衡量指标：

- 问答抽取准确率
- 复盘建议可用率
- 用户是否愿意复用生成的话术

### 第二阶段：沉淀组织资产

目标：

- 建成高频问题库和统一回答口径

衡量指标：

- 高频主题覆盖率
- 标准话术被采用的比例

### 第三阶段：做成培训系统

目标：

- 新人能够用系统完成学习与演练

衡量指标：

- 培训完成率
- 演练回答与标准口径一致率

## 九、如果接下来直接开发

我建议的顺序是：

1. 后端先搭：会议、转写、问答抽取、复盘接口
2. 再做 Flutter 客户端：录音、上传、结果查看
3. 最后补知识库和培训模块

这样能最快看到真实样例，避免一开始就把时间花在复杂 UI 或高级权限系统上。
