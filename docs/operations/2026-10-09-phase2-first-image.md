# Phase 2：生成《消失的信号》第一张实验室画面

**状态：V100 CUDA 验证已通过（用户反馈）。模型下载和图片生成尚未执行。**

## 使用位置

所有命令都在本地 `emc-vision-studio` 仓库根目录的 PowerShell 执行。默认 ComfyUI 根目录为 `D:\AI-Video`，如安装在其他盘，修改 `-Root`。

## 第一步：更新项目

```powershell
git pull
```

## 第二步：下载第一张图所需的模型

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\download_first_image_model.ps1 -Root "D:\AI-Video"
```

使用 SD 1.5 的 fp16 checkpoint，文件约 2GB，存入 `D:\AI-Video\ComfyUI\models\checkpoints\`。脚本检查文件大小；如果网络无法访问 Hugging Face，则停止并保留 .part 文件，不伪称成功。该模型用于**技术可行性演示**，后续正式视频使用的模型和商用许可需单独审查。

## 第三步：重启 ComfyUI

如果 ComfyUI 正在运行，关闭原来的启动窗口，再从项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_windows_v100.ps1 -Root "D:\AI-Video"
```

浏览器打开 http://127.0.0.1:8188 。

## 第四步：自动提交生成任务

在另一个 PowerShell 窗口、项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\generate_first_image.ps1 -Root "D:\AI-Video"
```

任务通过 ComfyUI 本地 API 提交；脚本显示 `QUEUE SUBMITTED` 仅表示已入队，不表示图片已经成功生成。请到 ComfyUI 的任务列表检查结果。

## 第五步：查看图片

默认输出目录：

```text
D:\AI-Video\ComfyUI\output
```

文件名以 `lost_signal_lab_S001_` 开头。图像尺寸 768×512，固定种子 20261009，24 步 Euler 采样。完整工作流：`workflows/text-to-image/first-lab-sd15-api.json`。

## 验收

- [x] CUDA 矩阵计算通过（用户反馈）
- [ ] 下载模型成功
- [ ] ComfyUI 模型加载成功
- [ ] 生成并查看第一张图片
- [ ] 将结果和运行记录提交 GitHub

**注意：** 该图片为概念画面，不代表真实 EMC 测量数据。生成后再做专业技术画面审核。
