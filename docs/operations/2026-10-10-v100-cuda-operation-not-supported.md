# V100 首图推理失败：CUDA Error Operation Not Supported

## 已确认的事实

- 模型已经手动下载完成（用户反馈）。
- ComfyUI 开始生成时，GPU 报 `RuntimeError: CUDA error: operation not supported`（用户反馈）。
- 之前的 CUDA 矩阵测试通过，**不代表卷积、注意力算子和模型推理均可用**。
- 当前尚无完整 Python traceback、GPU 驱动版本和故障节点，**不能断言一定是驱动太旧**。V100（sm_70）对部分较新的加速算子存在兼容限制。

## 第一步：停止正在运行的 ComfyUI

在 ComfyUI 的 PowerShell 窗口按 `Ctrl+C`，确保旧进程已退出。不要同时启动两个占用 8188 端口的实例。

## 第二步：拉取修复脚本

在 `emc-vision-studio` 仓库根目录打开 PowerShell：

```powershell
git pull
```

## 第三步：先进行分项 GPU 算子测试

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\diagnose_v100_inference.ps1 -Root "D:\AI-Video"
```

此测试会输出 Python/PyTorch/CUDA/GPU 架构，并分别测试 `fp32 matmul`、`fp32 convolution` 和 `math SDPA`。如果某项显示 FAIL，请保留完整报错。

## 第四步：启动 V100 兼容模式

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_windows_v100.ps1 -Root "D:\AI-Video" -SafeMode
```

此模式尝试关闭 xFormers、自定义节点，使用 split cross attention，并强制 FP32 模型与 VAE，便于避开可能不兼容的半精度或高性能注意力实现。**FP32 会增加显存占用、速度可能降低。** 不保证解决所有驱动/算子问题。

若启动阶段提示 `unrecognized arguments`，说明当前 ComfyUI 版本可能不支持其中某项参数，请记录错误，不要自行乱改驱动。

## 第五步：重新提交图片生成任务

另开一个 PowerShell 窗口，仍在仓库根目录：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\generate_first_image.ps1 -Root "D:\AI-Video" -Model modelscope
```

查看 ComfyUI 控制台是否生成成功。默认输出目录 `D:\AI-Video\ComfyUI\output`。

## 如果仍失败

请提供：

1. 第三步的 `PASS/FAIL` 结果和失败 traceback；
2. ComfyUI 控制台中 `RuntimeError` 前后约 20 行；
3. `nvidia-smi` 显示的 Driver Version。

**暂时不要**升级显卡驱动、重新安装 PyTorch、删除模型或关闭 TLS 证书验证。先定位出错算子，再选择最小修复。
