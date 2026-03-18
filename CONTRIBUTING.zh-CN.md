# 贡献指南

[English](./CONTRIBUTING.md) | [简体中文](./CONTRIBUTING.zh-CN.md)

感谢你参与 `Investor Conversation Copilot` 的开发。

## 本地开发

1. 创建虚拟环境
2. 安装 `requirements.txt` 里的依赖
3. 启动本地应用：

```powershell
.\scripts\run-demo.ps1
```

4. 提交前先跑测试：

```powershell
.\.venv\Scripts\python -m pytest -q
```

## 贡献约定

- 不要提交密钥、令牌或机器本地环境文件
- 只要行为发生了可自动验证的变化，就补测试
- 用户可见的功能变化要更新 `CHANGELOG.md`
- 核心演示链路必须保持可用：转写输入、音频上传、复盘输出
- 尽量用范围清晰、便于审阅的小型 PR

## Pull Request 提交检查

- 说明改了什么
- 说明为什么要改
- 列出如何测试
- 如果界面有变化，附上截图
- 如果还有后续工作，写清楚剩余事项

## 发布相关文件

- `VERSION` 记录当前公开演示版本
- `CHANGELOG.md` 记录版本变化
- `ROADMAP.md` 记录后续里程碑
