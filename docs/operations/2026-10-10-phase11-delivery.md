# Phase 11｜103 秒完整版、30 秒精简版、本地交付

## 前提

用户已确认 Phase 10 中文配音成功，且此前 Windows 10 自带播放器能够正常显示烧录的中文字幕。

## 操作

在仓库根目录 PowerShell 执行：

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\make_phase11_delivery.ps1 -Root "D:\AI-Video"
```

不需要启动 ComfyUI，不会重新生成 AI 图片或视频。脚本用 FFmpeg/FFprobe 验证完整版时长和音视频轨道，从现有有声成片中选取 6 段、每段 5 秒，合成 30 秒精简版。

## 本地交付目录

`D:\AI-Video\private\lost-signal\delivery\`

- `lost_signal_full_103s.mp4`：完整版，保留已有中文字幕和配音
- `lost_signal_short_30s.mp4`：六段精选镜头合成的 30 秒技术精简版
- `quality_report.json`：时长、音视频流、自动验证结果及已知限制
- `README_交付说明.txt`：本地交付说明

## 验收

用 Windows 10 自带播放器分别打开两个 MP4，检查画面、字幕和声音是否正常；确认完整版约 103 秒、精简版约 30 秒。脚本仅检查可机器验证的时长和流信息，不会自动评判人物一致性或声音审美。

## 当前质量限制

- 目前各 SVD 镜头真实 AI 运动约 2.33 秒，剩余为末帧停留
- Windows SAPI 配音可能比较机械
- 背景音为简单合成氛围底音，不是精细制作的配乐
- 30 秒版直接复用完整版烧录字幕，文字不一定符合独立短片节奏
- 这代表本地 AI 视频**技术工作流**交付，不等于影视级成片质量验收

## 保密

所有生成图片、视频、声音、运行记录仅保留在本机 `D:\AI-Video\private\` 下。公共 GitHub 只提交脚本和通用文档。
