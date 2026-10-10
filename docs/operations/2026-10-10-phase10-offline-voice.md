# Phase 10｜Windows 10 离线中文配音与背景音

用户确认烧录中文字幕后，已可用 Windows 10 自带播放器正常显示。下一步不动 AI 视频与字幕，直接为现有 103 秒视频生成声音。

## 运行

在仓库根目录 PowerShell 执行：

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\generate_phase10_offline_voice.ps1 -Root "D:\AI-Video"
```

脚本通过 Windows 内置 System.Speech（SAPI）枚举本机**已安装且启用的中文离线语音**，逐镜头朗读虚构中文解说词，合成 103 秒人声时间轴；同时用 Python 本地合成低音量氛围音并混合。全部在本地执行，不访问在线语音 API。

**如果报错 `Chinese offline voice missing`：** 表示本机没有可用的中文 SAPI 语音，脚本会列出本机语音名称并停止。不要误以为已完成配音，也不要上传任何内部资料；后续可选择安装 Windows 离线中文语音组件或使用自己的本地录音。

## 结果

- 配音和本地音频：`D:\AI-Video\private\lost-signal\phase10\audio\`
- 带中文字幕、中文配音和低音量合成氛围音的视频：`D:\AI-Video\private\lost-signal\phase10\lost_signal_phase10_voiced.mp4`
- 之前字幕正常的 `lost_signal_phase10.mp4` 不会覆盖。

当前背景音是**程序生成的简易氛围底音**，不是正式创作的完整配乐。某些 SAPI 中文语音可能读得机械，脚本会提示旁白超过镜头时长的情况；后续仍需人工听感验收，必要时调整解说长度或换离线语音。

## 保密

所有图片、视频、语音、音频和运行数据只留本地。GitHub 只保存通用代码、虚构解说词和文档。
