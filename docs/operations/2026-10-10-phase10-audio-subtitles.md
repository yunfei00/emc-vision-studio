# Phase 10｜修复 Windows 10 自带播放器不显示中文字幕

用户反馈：Phase 10 的 MP4、SRT 和 TXT 均已生成，但 Windows 10 自带播放器不显示 MP4 内的可选字幕轨道。

## 修复

已修改 `scripts/make_phase10_audio_subtitles.py`：**默认将中文字幕直接烧录到画面**，不再依赖播放器对 mov_text 字幕轨道的支持。使用本地 FFmpeg 的 `subtitles/libass` 滤镜，字体优先使用 Windows 10 常见的 Microsoft YaHei。保留 `--soft-subtitles` 作为可选模式。

## 重新运行

不需要 ComfyUI，不需要重新生成 AI 视频。关闭正在播放旧 MP4 的播放器，在项目根目录 PowerShell 执行：

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\make_phase10_audio_subtitles.ps1 -Root "D:\AI-Video"
```

输出仍是：

`D:\AI-Video\private\lost-signal\phase10\lost_signal_phase10.mp4`

脚本会覆盖旧版 MP4；`lost_signal_zh.srt` 和 `narration_zh.txt` 继续保留。字幕直接成为画面一部分，不用在播放器中开启字幕。首次运行需要重新编码 103 秒视频，耗时会比旧版封装长。

如果报错 `FFmpeg build lacks subtitles/libass filter`，说明本机 FFmpeg 缺少字幕烧录功能；不要反复运行，反馈这个错误类型以便改用不依赖 libass 的方案。

**当前仍未加入真人配音或背景音乐**。如已有本地录音或音乐，可以使用脚本的 `-Voice` 和 `-Music` 参数混合；不调用云端服务。

所有图片、视频、录音和日志仅保留本地，不外传。
