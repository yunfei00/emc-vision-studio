# Phase 5：AI 图生视频（SVD 14 帧）预检

2026-10-10 用户确认 Phase 4 的 MP4 已生成成功。本阶段开始评估真正的 AI 图生视频，首选 ComfyUI 原生 Stable Video Diffusion（SVD）14 帧工作流，**暂不批量安装或下载大模型**。

## 为什么选 SVD

SVD 基础模型可从一张静态图生成 14 帧，SVD-XT 则是 25 帧。先用 S001 验证最小流程；Tesla V100S 32GB 的实际运行速度、显存和算子兼容性尚未验证，不能保证成功。SVD 与已安装的 SD1.5 是**不同模型**，不能直接复用 SD1.5 checkpoint。

参考：
- https://comfyui-wiki.com/en/workflows/video
- https://huggingface.co/stabilityai/stable-video-diffusion-img2vid
- https://github.com/huggingface/diffusers/blob/main/docs/source/en/api/pipelines/stable_diffusion/svd.md

模型下载前须确认许可、来源和下载条件；不得向在线推理 API 上传任何素材。只允许从公开来源下载模型文件到本地。

## 第一步：预检（不会上传、下载或修改模型）

在项目根目录 PowerShell：

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\phase5_svd_preflight.ps1 -Root "D:\AI-Video"
```

预检会确认 S001 图片、ComfyUI 本地 API、原生 SVD 节点和是否已有 SVD 模型。若 ComfyUI 没启动，先用已验证的 V100S 兼容模式启动：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_windows_v100.ps1 -Root "D:\AI-Video" -SafeMode
```

预检结果只写本地 `D:\AI-Video\private\lost-signal\phase5\preflight.json`。

如果提示 `SVD MODEL: NOT INSTALLED`，这是预期结果，不是失败；**不要随意下载十几个 GB 的模型**。本阶段先确定节点与素材齐备，再准备经过验证的下载及推理脚本。

## 保密

不得上传图片、视频、设备截图、真实数据、日志到 GitHub 或聊天。用户只需反馈 `COMFY API`、`SVD NODES` 是否齐备，以及是否已有模型（无需发送路径、图片或日志）。
