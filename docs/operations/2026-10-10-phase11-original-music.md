# Phase 11｜本地生成原创背景音乐并重新混音

## 问题

用户反馈之前有声版几乎听不到背景音乐。原因是上一版仅合成了很轻的持续低频底音，并不是有旋律和节奏的配乐。

## 解决方案

新增 `scripts/generate_phase11_music.py`，只使用 Python 标准库在本地生成 103 秒电子纪录片风格音乐（和弦铺底、简短旋律、电子脉冲与淡入淡出）。分为四段：0–26 秒异常出现、26–53 秒调查、53–80 秒排查、80–103 秒收束。

将现有 `voice_103s.wav` 与新配乐混音。使用 FFmpeg `sidechaincompress`，配音出现时自动降低音乐音量，避免盖过中文解说。保持已经烧录中文字幕的视频画面不变。

这是**程序合成的原创简易配乐**，不是在线 AI 作曲，也不是商业级音乐制作。所有音频留本地，不上传。

## 操作

先关闭正在播放的旧 MP4，在项目根目录 PowerShell：

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\generate_phase11_music.ps1 -Root "D:\AI-Video"
```

该命令一次性完成生成音乐、混音、刷新 Phase 11 完整版与 30 秒版。无需 ComfyUI、无需下载音乐、无需重新生成视频。

## 本地输出

- `D:\AI-Video\private\lost-signal\phase10\audio\original_score_103s.wav`：独立背景配乐
- `D:\AI-Video\private\lost-signal\phase10\lost_signal_phase10_voiced.mp4`：更新后的有声视频
- `D:\AI-Video\private\lost-signal\delivery\lost_signal_full_103s.mp4`：刷新完整版
- `D:\AI-Video\private\lost-signal\delivery\lost_signal_short_30s.mp4`：刷新精简版

## 验收

先直接播放 `original_score_103s.wav`，应能听到轻电子节奏与旋律；再播放完整版，确认旁白可辨、背景音乐可听、字幕正常。若混音效果不理想，再调整音乐增益与避让阈值，不必重新生成画面。

所有生成音视频仅保留本机。
