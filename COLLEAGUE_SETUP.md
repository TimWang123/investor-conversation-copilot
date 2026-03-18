# 给同事的快速体验说明

[English](./COLLEAGUE_SETUP.en.md) | [简体中文](./COLLEAGUE_SETUP.md)

## 最简单的方式

1. 双击 [`start-demo.bat`](./start-demo.bat)
2. 第一次运行会自动创建虚拟环境并安装依赖
3. 服务就绪后会自动打开浏览器
4. 默认地址是 `http://127.0.0.1:8000`

停止服务时：

1. 双击 [`stop-demo.bat`](./stop-demo.bat)

## 如果要启用 Kimi

推荐方式：

1. 复制 [`scripts/env.example.ps1`](./scripts/env.example.ps1) 为 `scripts/env.local.ps1`
2. 把里面的占位值改成你自己的配置
3. 再次双击 [`start-demo.bat`](./start-demo.bat)

也可以手动运行：

```powershell
.\scripts\launch-demo.ps1 -MoonshotApiKey "your-key"
```

## 如果要以前台方式查看日志

```powershell
.\scripts\run-demo.ps1
```

## 当前能体验什么

- 粘贴转写文本直接分析
- 上传音频后自动转写并复盘
- 在浏览器中录音后直接生成复盘
- 自动生成问答复盘、主题库、标准话术和培训脚本

## 常见问题

- 第一次做音频分析时，本地会下载 `faster-whisper` 模型，速度会慢一点
- 如果没有配置 Kimi，也可以先体验本地规则版
- 如果浏览器没有自动打开，可以手动访问 `http://127.0.0.1:8000`
