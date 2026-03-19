# 桌面版打包说明

这个项目现在可以打成一个 Windows 桌面应用，产品名为 `天枢智元·融谈Copilot`。

## 它打出来的是什么

桌面版是一个原生 Windows 可执行程序，它会：

- 在后台启动本地 FastAPI 服务
- 用 `pywebview` 打开桌面窗口，而不是浏览器标签页
- 在打包模式下把用户数据写到本地可写目录

## 打包步骤

1. 准备好项目虚拟环境
2. 安装桌面打包依赖：

```powershell
.\.venv\Scripts\python -m pip install -r requirements-desktop.txt
```

3. 运行打包脚本：

```powershell
.\scripts\build-desktop.ps1 -Clean
```

4. 打包结果在：

```text
dist\天枢智元-融谈Copilot
```

## 发给同事时要发什么

要发整个输出目录，不要只发一个 exe。

重点文件包括：

- `天枢智元-融谈Copilot.exe`
- `settings.example.json`
- PyInstaller 自动生成的其余依赖文件

## 打包版如何配置模型

给桌面版配置 Qwen 或 Kimi 最简单的方式是：

1. 把 `settings.example.json` 复制为 `settings.json`
2. 填入 Qwen 或 Moonshot / Kimi 的配置
3. 把 `settings.json` 和 exe 放在同一个目录

示例：

```json
{
  "LLM_PROVIDER": "qwen",
  "QWEN_API_KEY": "replace-with-your-key",
  "QWEN_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "QWEN_MODEL": "qwen-plus",
  "ASR_MODEL_SIZE": "small",
  "ASR_DEVICE": "cpu",
  "ASR_COMPUTE_TYPE": "int8"
}
```

## 说明

- 第一次做音频转写时，可能会下载本地 whisper 模型
- 打包版不会把数据写进程序目录，而是写到本地可写目录
- 如果 `8000` 端口被占用，桌面版会自动尝试其他本地端口
