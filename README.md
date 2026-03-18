# Investor Conversation Copilot

这是一个面向融资场景的 AI 会议复盘 MVP。当前版本已经不是纯方案文档，而是一个可以直接跑起来的后端原型和工作台式演示页。

它的目标是把每一次和投资人的交流沉淀为：

- `高频问题库`
- `回答质量复盘`
- `个人回答风格画像`
- `新人统一培训话术`

## 这版已经做了什么

当前可运行能力：

1. 输入一段带说话人标记的会议转写。
2. 上传音频文件，或直接在浏览器里录一段演示音频。
3. 使用本地 `faster-whisper` 自动转写音频。
4. 自动识别投资人问题和你的回答。
5. 按主题归类问题，例如增长、壁垒、单位经济、融资规划、合规风险。
6. 对每组回答给出完整性、清晰度、一致性、证据充分度等评分。
7. 汇总本场会议总评和你的表达风格画像。
8. 基于历史会议自动生成高频问题库和新人培训话术。

为了先把价值跑通，这一版采用“本地转写 + Kimi 增强分析”的路线：

- 已支持：文本分析、音频上传、浏览器录音、本地 ASR、Kimi 增强复盘
- 暂未接入：移动端原生录音、对象存储、异步任务队列

这样做的原因很直接：先把“复盘和知识沉淀”这个最能拿预算的核心价值做出来，再逐步把输入端补齐。

## 技术栈

- 后端：`FastAPI`
- 存储：本地 `JSON state store`
- 前端：原生 `HTML / CSS / JavaScript` 工作台
- 测试：`pytest`

## 快速启动

1. 创建虚拟环境

```powershell
py -m venv .venv
```

2. 安装依赖

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

3. 启动服务

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

4. 打开演示页

在浏览器访问：`http://127.0.0.1:8000`

## 接入 Kimi / Moonshot

不要把 API Key 写进代码或提交到仓库。当前版本已经支持从环境变量读取 Moonshot 配置。

PowerShell 临时设置示例：

```powershell
$env:MOONSHOT_API_KEY="你的新 key"
$env:MOONSHOT_BASE_URL="https://api.moonshot.cn/v1"
$env:MOONSHOT_MODEL="kimi-latest"
```

如果你的控制台里给的是 Kimi 2.5 的专用模型名，就把 `MOONSHOT_MODEL` 换成你控制台实际显示的那个值。设置完后重新启动服务，页面顶部会提示当前是否已经进入模型增强模式。

## 本地 ASR 配置

默认会使用 `faster-whisper` 的 `small` 模型在 CPU 上转写。你也可以通过环境变量调整：

```powershell
$env:ASR_MODEL_SIZE="small"
$env:ASR_DEVICE="cpu"
$env:ASR_COMPUTE_TYPE="int8"
```

第一次做音频分析时，`faster-whisper` 可能会下载本地模型，这一步会比文本分析慢一些，属于正常现象。

## 演示方式

启动后你可以直接：

1. 点击“载入示例”
2. 或者上传一段音频 / 浏览器直接录音
3. 点击“生成复盘”
3. 现场展示系统自动产出的：
   - 会议历史
   - 问答复盘
   - 高频问题库
   - 标准话术
   - 新人培训话术

示例对话在：

- [fundraising_transcript.txt](C:\Users\a9322\Desktop\Codex\AI录音\samples\fundraising_transcript.txt)

## 发给同事体验

我已经补了适合同事快速体验的启动文件：

- [start-demo.bat](C:\Users\a9322\Desktop\Codex\AI录音\start-demo.bat)
- [scripts/setup.ps1](C:\Users\a9322\Desktop\Codex\AI录音\scripts\setup.ps1)
- [scripts/run-demo.ps1](C:\Users\a9322\Desktop\Codex\AI录音\scripts\run-demo.ps1)
- [COLLEAGUE_SETUP.md](C:\Users\a9322\Desktop\Codex\AI录音\COLLEAGUE_SETUP.md)

给同事时，建议直接发打包后的 zip，并提醒他：

1. 第一次运行会安装依赖
2. 如果不配 Kimi key，也能先体验本地规则版
3. 如果要和你一样启用 Kimi，需要他自己本地配置环境变量

## API

核心接口：

- `GET /api/health`
- `GET /api/dashboard`
- `POST /api/meetings`
- `POST /api/meetings/from-audio`
- `GET /api/meetings`
- `GET /api/meetings/{id}`
- `GET /api/meetings/{id}/qa-exchanges`
- `GET /api/meetings/{id}/review`
- `GET /api/topics`
- `GET /api/topics/{topic_id}`
- `GET /api/topics/{topic_id}/canonical-answers`
- `GET /api/training-scripts/latest`

接口文档启动后可在这里查看：

- `http://127.0.0.1:8000/docs`

## 代码结构

- [app/main.py](C:\Users\a9322\Desktop\Codex\AI录音\app\main.py)
- [app/api/routers/meetings.py](C:\Users\a9322\Desktop\Codex\AI录音\app\api\routers\meetings.py)
- [app/api/routers/dashboard.py](C:\Users\a9322\Desktop\Codex\AI录音\app\api\routers\dashboard.py)
- [app/services/analysis.py](C:\Users\a9322\Desktop\Codex\AI录音\app\services\analysis.py)
- [app/services/meeting_service.py](C:\Users\a9322\Desktop\Codex\AI录音\app\services\meeting_service.py)
- [app/services/transcription_service.py](C:\Users\a9322\Desktop\Codex\AI录音\app\services\transcription_service.py)
- [app/services/llm_gateway.py](C:\Users\a9322\Desktop\Codex\AI录音\app\services\llm_gateway.py)
- [app/services/transcript.py](C:\Users\a9322\Desktop\Codex\AI录音\app\services\transcript.py)
- [app/static/index.html](C:\Users\a9322\Desktop\Codex\AI录音\app\static\index.html)
- [app/static/main.js](C:\Users\a9322\Desktop\Codex\AI录音\app\static\main.js)
- [app/static/api.js](C:\Users\a9322\Desktop\Codex\AI录音\app\static\api.js)
- [tests/test_api.py](C:\Users\a9322\Desktop\Codex\AI录音\tests\test_api.py)

## 配套文档

- [产品与技术架构](C:\Users\a9322\Desktop\Codex\AI录音\docs\architecture.md)
- [数据模型与 AI 流程](C:\Users\a9322\Desktop\Codex\AI录音\docs\data-model-and-pipeline.md)

## 下一步最值得做的事

如果你要继续往“真实可用产品”推进，我建议下一步优先级是：

1. 接入真实录音和 ASR 转写
2. 接入你可提供的多模态 / 大模型 API
3. 把本地 JSON 存储升级为 PostgreSQL
4. 再开始做 Flutter 手机和桌面客户端
