# Phase 10｜中文字幕与本地音频混合

用户已确认 Phase 9 的 103 秒粗剪成功。此阶段首先提供**可运行的本地字幕和音频封装工具**，不下载新模型、不调用云端服务。

## 第一步：无外部音频，先验证字幕轨道

仓库根目录 PowerShell：

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\make_phase10_audio_subtitles.ps1 -Root "D:\AI-Video"
```

输出：

- `D:\AI-Video\private\lost-signal\phase10\lost_signal_phase10.mp4`
- `D:\AI-Video\private\lost-signal\phase10\lost_signal_zh.srt`
- `D:\AI-Video\private\lost-signal\phase10\narration_zh.txt`

**注意：** MP4 使用可选的中文软字幕轨道，需要播放器开启字幕显示；字幕不是烧录到画面。默认没有人声或背景音乐，原始静音轨道保持不变。不要把这版误认为完整配音成片。

## 第二步：如果已有本地配音/音乐

可选参数传入**本机音频文件**，支持 FFmpeg 可解码的常见格式：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\make_phase10_audio_subtitles.ps1 -Root "D:\AI-Video" -Voice "D:\AI-Video\private\lost-signal\audio\voice.wav" -Music "D:\AI-Video\private\lost-signal\audio\music.wav"
```

脚本按 103 秒截取音频、配音原音量、音乐 0.16 倍音量，混合成 AAC；只提供一个文件时也可以单独指定 `-Voice` 或 `-Music`。

配音内容来自 [中文解说词](../../plans/phase10_narration_zh.json)，当前没有自动生成 TTS：要使用人声，需要已有本地录音或之后增加经过验证的离线中文语音方案。

## 下一步

先确认无音频版 MP4 可以播放、播放器可启用中文字幕，再决定是否增加离线 TTS 或使用本地录音。之后补充环境音效与音量验收。

## 保密

所有生成素材、录音、视频和日志只留本地，不上传 GitHub、聊天或第三方平台。
