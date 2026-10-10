# Phase 5｜SVD 14 帧本地图生视频推理

用户已确认 `READY FOR SVD: True`。此时可开始真正的 SVD 模型推理，目标是将 Phase 3 的 S001 图片转换成 **14 帧 AI 生成画面**，并在本地合成为 MP4。

## 操作

1. 保持 ComfyUI 以 V100S `-SafeMode` 模式运行，不能恢复到旧的 CUDA 内存分配模式。
2. 在 `emc-vision-studio` 项目根目录执行：

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\generate_phase5_svd.ps1 -Root "D:\AI-Video"
```

## 处理流程

- 从本地 ComfyUI output 选择最新的 `lost_signal_phase3_S001_*.png`
- 复制到本地 ComfyUI input
- 使用 `svd.safetensors`、ComfyUI 原生 `SVD_img2vid_Conditioning`、14 帧、1024×576、20 采样步
- 等待 KSampler、VAE 完成，保存 14 张 PNG
- 使用本地 FFmpeg 将 14 帧以 6 FPS 合成为约 2.33 秒的 MP4

输出文件：

`D:\AI-Video\private\lost-signal\phase5\S001_svd_14frames.mp4`

对应 PNG：`D:\AI-Video\private\lost-signal\phase5\frame_000.png` 至 `frame_013.png`。

## 注意

V100S 32GB 上的 SVD 推理尚未实际验证；首次运行可能较慢，也可能遇到显存不足或 CUDA 算子兼容问题。**不要因报错而盲目重装 CUDA、升级 PyTorch 或重新下载模型。** 当前脚本将自动打印失败节点和异常；用户只需反馈简短错误类型或节点名，无需传输图片、日志或内部数据。

## 保密

脚本只调用 `http://127.0.0.1:8188` 的 ComfyUI，视频、PNG、生成记录全部保存在本机，不上传外部服务。仓库仅保存通用代码与说明。
