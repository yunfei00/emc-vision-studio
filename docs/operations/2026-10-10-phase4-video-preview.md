# Phase 4｜本地视频预览（不上传素材）

## 目标

六张已生成的关键帧合成一段约 24 秒、24 fps、1280×720 的 MP4 预览片。此阶段是**静态图片镜头运动**，不是 AI 生成真实人物动作。先确认本地视频工具链可用，再规划 V100S 图生视频模型。

## 保密规则

所有图片、视频、日志、清单都保存在本机 `D:\AI-Video`。不要发送聊天、上传 GitHub 或云盘。仓库只保留通用脚本与文档。

## 前置

- 已生成 `lost_signal_phase3_S001_*.png` 到 `S006` 六张图片。
- 已有 `D:\AI-Video\.venv\Scripts\python.exe`。
- 本机可调用 `ffmpeg`，可在 PowerShell 中运行 `ffmpeg -version` 验证。**不要通过未经核验的下载脚本安装 FFmpeg。** 若未安装，请从 FFmpeg 官方下载页 https://ffmpeg.org/download.html 选择 Windows 构建并将 ffmpeg.exe 所在目录添加 PATH。

## 操作

在 `emc-vision-studio` 根目录 PowerShell：

```powershell
git pull
ffmpeg -version
powershell -ExecutionPolicy Bypass -File .\scripts\make_phase4_preview.ps1 -Root "D:\AI-Video"
```

该脚本仅调用本地 FFmpeg，不要求 ComfyUI 正在运行，不需要 GPU。

## 结果

输出：`D:\AI-Video\private\lost-signal\phase4\lost_signal_phase4_preview.mp4`

另有 `S001.mp4` 到 `S006.mp4`、`clips.txt`、`manifest.json`，均留在本机。

成功标志：终端显示 `COMPLETE:` 加本地文件路径，并且视频可在本地播放器播放。

如果失败，只需要告诉我简短的错误类型（例如“FFmpeg 未安装”“S003 找不到”），不需要发任何内部日志或图片。

## 局限与后续

当前采用图片裁剪和平移形成轻微运镜，没有真实运动生成、转场、配音或字幕。下一步研究适配 Tesla V100S 32GB 的本地 AI 图生视频，并保留这一可用的传统视频管线作为兜底。
