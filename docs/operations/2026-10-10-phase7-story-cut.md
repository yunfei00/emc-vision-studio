# Phase 7：本地六镜头叙事样片

Phase 6 已由用户确认完成。Phase 7 将六段 SVD 视频统一为 1280×720、24 FPS，附加静音音频轨道，输出叙事样片与本地解说词草稿。当前不含实际配音、字幕或音乐，也不是 90–120 秒完整版。

项目根目录 PowerShell：

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\make_phase7_story_cut.ps1 -Root "D:\AI-Video"
```

输出目录：`D:\AI-Video\private\lost-signal\phase7`

包含 `lost_signal_phase7_story_cut.mp4`、`narration_draft.md` 和 `edit_plan.json`。

无需启动 ComfyUI；只调用本地 FFmpeg。所有图片、视频、日志和内部资料留在本机，不上传 GitHub 或聊天。
