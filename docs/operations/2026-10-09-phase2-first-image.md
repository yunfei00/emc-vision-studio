# Phase 2：GPU 最终确认与首张图片准备

## 当前情况

用户已安装 ComfyUI 且网页能打开，验证脚本曾打印版本号，但尚未明确确认 CUDA 运算通过。因此本阶段先执行 **CUDA 实算 + 模型目录检查**，不重新安装 ComfyUI。

## 操作位置

本地 GitHub 项目根目录：`emc-vision-studio`。

ComfyUI 默认安装根目录：`D:\AI-Video`（如果当时修改过安装位置，以下命令同步修改 `-Root`）。

## 第一步：更新脚本

在项目根目录的 PowerShell 执行：

```powershell
git pull
```

## 第二步：执行一次验证和模型目录准备

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_and_prepare_phase2.ps1 -Root "D:\AI-Video"
```

这个脚本会自动执行 V100 CUDA 矩阵运算，并打印已有模型文件名。**不会下载模型、不会重装环境、不会修改已有模型。**

## 如何判断通过

应看到：

```text
CUDA 矩阵运算：通过
模型目录：D:\AI-Video\ComfyUI\models\checkpoints
验证完成。尚未下载或安装任何图像/视频模型。
```

如果只打印 PyTorch 版本号，但没有“CUDA 矩阵运算：通过”，就不能判定 GPU 验证通过。

## 下一步：首张图片

GPU 验证通过后，再选择一个许可证清晰、适合 V100 32GB 的图像模型，提供模型下载、校验、ComfyUI 工作流及首张实验室场景图的生成步骤。当前尚未选择并安装模型，也尚未生成图片。

## 关于后台 OpenGL 提示

`no opengl-accelerate module loaded` 不是 CUDA 推理失败的直接证据；若 CUDA 实算通过且 ComfyUI 正常使用，可以暂时忽略。
