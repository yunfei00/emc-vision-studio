# Phase 6｜六镜头 SVD AI 视频批量生成

2026-10-10 用户确认 Phase 5 的 S001 SVD 14 帧 AI 视频已成功生成。Phase 6 复用相同的 SVD 模型、ComfyUI 节点、采样参数和 V100S SafeMode，不增加新模型依赖。

## 功能

- S001 至 S006 逐个生成 14 帧 AI 视频（1024×576、6 FPS、20 steps）
- 每个镜头输出独立 MP4（约 2.33 秒）
- 六镜头拼接为约 14 秒的 AI 视频预览
- 本地保存进度，重新运行时跳过已经成功输出的镜头
- 发生错误时停止并保留前面已完成的镜头

**这仍是 AI 视频技术预览，不是最初规划的 90–120 秒完整版。** 后续需要进一步设计时长、分镜节奏、配音、字幕与音效。

## 操作

确保 ComfyUI 正以此前验证成功的 `-SafeMode` 运行。在项目根目录 PowerShell：

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\generate_phase6_svd_all.ps1 -Root "D:\AI-Video"
```

该任务依次执行六次模型推理，耗时可能较长。不要同时运行其他 ComfyUI 大模型任务。

## 本地输出

- 每镜头：`D:\AI-Video\private\lost-signal\phase6\S001.mp4` 至 `S006.mp4`
- 合成视频：`D:\AI-Video\private\lost-signal\phase6\lost_signal_phase6_svd_preview.mp4`
- 帧文件：`D:\AI-Video\private\lost-signal\phase6\S001\frame_000.png` 等
- 进度：`D:\AI-Video\private\lost-signal\phase6\manifest.json`

如果中途失败，重新执行同一条命令，会跳过已有成功镜头。

## 保密

所有图像、视频、设备截图、真实数据和日志只留本地，不上传 GitHub 或聊天。只需反馈“Phase 6 完成”或“失败在 S00X，错误类型是什么”。
