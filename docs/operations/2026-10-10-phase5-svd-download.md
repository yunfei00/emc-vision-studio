# Phase 5｜下载 SVD 基础模型（14 帧）

## 当前结果

用户本地预检确认：S001 图片、ComfyUI API 和所有必要 SVD 节点均正常，唯独 `svd.safetensors` 尚未安装。因此先下载公开的 SVD 基础版模型，**不安装新 Python 依赖，不升级 PyTorch，不更改已验证的 CUDA 配置**。

## 模型来源

- 模型仓库：https://huggingface.co/stabilityai/stable-video-diffusion-img2vid
- 文件：https://huggingface.co/stabilityai/stable-video-diffusion-img2vid/resolve/main/svd.safetensors
- 文件名：`svd.safetensors`
- 模型约数 GB，需足够本地磁盘空间。具体大小以模型仓库为准。
- 使用前阅读模型页面许可和使用限制，按其要求获取访问权限。部分网络环境可能无法访问 Hugging Face；脚本不绕过访问控制。

## 操作

项目根目录 PowerShell：

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\download_phase5_svd.ps1 -Root "D:\AI-Video"
```

脚本使用 Python 标准库下载到 `D:\AI-Video\ComfyUI\models\checkpoints\svd.safetensors`。下载过程中使用 `.part` 临时文件，支持服务端允许时的断点续传。若已下载成功，会跳过重复下载。

**注意：** 当前脚本仅以文件体积做基本完整性检查，不等同于 SHA256 校验。建议以模型仓库提供的可信哈希进行额外核对；下载后 ComfyUI 加载成功也不意味着模型许可自动满足。

## 下载后

关闭 ComfyUI 并以已验证的兼容方式重新启动：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_windows_v100.ps1 -Root "D:\AI-Video" -SafeMode
```

再运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\phase5_svd_preflight.ps1 -Root "D:\AI-Video"
```

此时预期 `SVD MODEL` 出现 `svd.safetensors` 且 `READY FOR SVD: True`。这仅证明文件和节点准备好，**并不证明 V100S 已能完成 SVD 视频推理**。后续单独进行 14 帧推理验证。

## 保密

下载仅从公网获取公开模型；不上传任何用户图片、视频、设备资料或日志。模型、生成结果和运行记录均保留本地。
