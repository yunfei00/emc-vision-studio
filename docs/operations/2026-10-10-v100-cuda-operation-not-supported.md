# V100 KSampler Operation Not Supported：优先关闭 CUDA 异步内存分配

## 已有诊断结论

用户反馈 Tesla V100S PCIe 32GB、PyTorch 2.7.0+cu126，FP32 matmul、FP32 convolution、SDPA 三项均 PASS。ComfyUI 的 KSampler 节点报 `CUDA error: operation not supported`。现有 traceback 仅看到 `execution.py line 538`，还不能确定失败的底层 CUDA API。

ComfyUI 社区有类似 KSampler 错误案例，日志中提示部分显卡不支持 `cudaMallocAsync`，建议添加 `--disable-cuda-malloc`。**这只是有依据的优先尝试，不代表已证实 V100S 的根因。**

参考：https://github.com/Comfy-Org/ComfyUI/issues/6843

## 已提交的修复

`scripts/start_windows_v100.ps1` 的 `-SafeMode` 现已添加 `--disable-cuda-malloc`，同时保留 `--disable-xformers --disable-all-custom-nodes --use-split-cross-attention --force-fp32 --fp32-vae` 和 `CUDA_LAUNCH_BLOCKING=1`。

## 请按以下步骤执行

1. 关闭 ComfyUI 启动窗口（Ctrl+C），确认旧实例退出。
2. 在 `emc-vision-studio` 根目录执行：

```powershell
git pull
```

3. 重新启动兼容模式：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_windows_v100.ps1 -Root "D:\AI-Video" -SafeMode
```

4. 在另一个 PowerShell 窗口执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\generate_first_image.ps1 -Root "D:\AI-Video" -Model modelscope
```

5. 如果仍然失败，**不必再重复运行 CUDA 三项基础测试**。请复制 ComfyUI 服务窗口的完整 traceback，尤其是 `execution.py line 538` **之后**，直到最后一个报错行的所有 `File ... line ...`；同时贴出启动日志中的 `Device:` 和内存分配方式（是否出现 `cudaMallocAsync`）。

成功时脚本输出 `GENERATION COMPLETE`，图片在 `D:\AI-Video\ComfyUI\output`。

## 暂不执行

不要重新下载模型、重装 CUDA/PyTorch、编译 `TORCH_USE_CUDA_DSA` 或盲目更新驱动。先确认关闭异步 CUDA 分配器是否解决问题。
