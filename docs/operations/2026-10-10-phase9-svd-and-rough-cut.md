# Phase 9｜新增 13 镜头 AI 视频与 103 秒结构粗剪

## 已有基础

用户确认 Phase 8 的 S007–S019 共 13 张图片生成成功。此前 S001–S006 的 SVD 视频也已通过实际验证。

## 步骤一：新增 13 段 SVD 视频

保持 ComfyUI 使用 V100S `-SafeMode` 运行，仓库根目录 PowerShell：

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\generate_phase9_svd.ps1 -Root "D:\AI-Video"
```

依次生成 S007–S019，每段 14 帧、6 FPS、1024×576。脚本支持跳过已完成镜头，失败后可重复运行。

结果：`D:\AI-Video\private\lost-signal\phase9\S007.mp4` 至 `S019.mp4`。

## 步骤二：19 镜头 103 秒结构粗剪

确认第一步成功后执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\make_phase9_rough_cut.ps1 -Root "D:\AI-Video"
```

输出：`D:\AI-Video\private\lost-signal\phase9\rough_cut\lost_signal_103s_rough_cut.mp4`。

按照 [Phase 8 分镜计划](../../plans/phase8_lost_signal_storyboard.json) 的顺序、镜头秒数进行剪辑，统一为 1280×720、24 FPS、H.264 和静音 AAC 音轨。

**重要：** SVD 每镜头只有约 2.33 秒真实生成运动，剩余时长用末帧停留补足。这是 103 秒**结构粗剪**，不是 103 秒连续 AI 动画，也没有实际配音、字幕和音乐。后续需按观看效果追加运动镜头或修改时长。

## 保密

所有视频、图片、设备资料、日志均只保留本地，不上传 GitHub、聊天或云端。只需回复“Phase 9 成功”或“失败在 S0XX / 粗剪”。
