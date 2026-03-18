# 给同事的快速体验说明

## 方式一：一键启动

1. 双击 `start-demo.bat`
2. 第一次运行会自动安装依赖
3. 启动后打开 `http://127.0.0.1:8000`

## 方式二：PowerShell 手动启动

```powershell
cd 当前项目目录
.\scripts\setup.ps1
.\scripts\run-demo.ps1
```

## 如果要启用 Kimi 增强模式

先在 PowerShell 里设置：

```powershell
.\scripts\env.example.ps1
```

然后把里面的 `replace-with-your-key` 换成自己的 key，或者手动设置环境变量后再运行：

```powershell
$env:MOONSHOT_API_KEY="你的 key"
.\scripts\run-demo.ps1
```

## 当前版本能做什么

- 粘贴会议转写直接分析
- 上传音频自动转写后分析
- 浏览器直接录音后分析
- 自动生成问答复盘、主题库、标准话术、培训脚本

