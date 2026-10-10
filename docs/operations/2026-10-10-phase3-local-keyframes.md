# Phase 3｜本地批量生成《消失的信号》分镜关键帧

## 保密原则

用户明确表示资料不能外传。**禁止上传任何生成图像、视频、设备截图、运行日志或真实测试数据到 GitHub、聊天或第三方服务。** GitHub 仓库只保存通用代码、虚构场景提示词和不含敏感内容的操作说明。脚本使用本地 ComfyUI API（127.0.0.1），不传输图片到外网。

## 已知可用环境

Windows 10、uv Python 3.12、Tesla V100S 32GB、PyTorch 2.7.0+cu126、ComfyUI、SD1.5。**必须继续使用 `-SafeMode`，其已包含 `--disable-cuda-malloc`。**

## 本阶段内容

脚本依次生成 6 张独立的电影感分镜关键帧：实验室全景、手机特写、工程师观察频谱仪、RF 连接线特写、排查过程、收束镜头。分镜提示词不包含真实项目名称、真实测试数值或设备序列号。图像属于视觉草稿，不保证设备细节完全真实；不应作为工程证据。

## 操作

1. 在项目根目录 PowerShell 执行：

```powershell
git pull
```

2. 如果 ComfyUI 已在 `-SafeMode` 下运行，则保持运行，不要重复启动。否则关闭旧 ComfyUI，执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_windows_v100.ps1 -Root "D:\AI-Video" -SafeMode
```

3. 在另一个 PowerShell 窗口执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\generate_phase3_keyframes.ps1 -Root "D:\AI-Video"
```

脚本逐张生成，遇到失败会停止并打印异常；重新运行时自动跳过已完成的镜头。

## 本地结果

- 图片：`D:\AI-Video\ComfyUI\output\lost_signal_phase3_S001_*.png` 至 `S006`
- 本地任务记录：`D:\AI-Video\private\lost-signal\phase3\manifest.json`

**不要把上述文件上传 GitHub。** 本地只需检查：六张图是否存在、是否清晰、手机和测试仪表有无明显畸形、是否有错误文字和不合理的连线。

## 验收

完成后只需在聊天中回复“6 张已生成”或“失败在 S00X”，无需发送任何图片、日志或内部资料。下一阶段再规划本地关键帧动画化，优先研究 V100S 的显存和模型兼容性。
