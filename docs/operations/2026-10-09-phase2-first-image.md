# Phase 2：国内 ModelScope 下载优先方案

## 当前问题与处理

用户反馈 Hugging Face 镜像下载速度很慢、长期卡住。**停止继续等待旧下载任务**，改为使用魔搭 ModelScope 国内托管的 Stable Diffusion 1.5 checkpoint。该文件与先前 HF fp16 文件**不是同一个文件**，不能将原 `.part` 续传到新文件；旧 `.part` 可以保留，不影响新方案。

魔搭模型页面：https://www.modelscope.cn/models/AI-ModelScope/stable-diffusion-v1-5 。魔搭官方社区提供过 `v1-5-pruned-emaonly.ckpt` 的下载接口，约 4GB。下载速度受实际网络影响，**无法保证一定更快**。

## 第一步：停止原来的下载

在原下载窗口按 `Ctrl+C`。不要删除 `D:\AI-Video\ComfyUI\models\checkpoints\v1-5-pruned-emaonly-fp16.safetensors.part`，以后仍可恢复原任务。

## 第二步：更新 GitHub 脚本

在本地 `emc-vision-studio` 项目根目录打开 PowerShell：

```powershell
git pull
```

## 第三步：使用魔搭国内下载

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\download_modelscope_sd15.ps1 -Root "D:\AI-Video"
```

下载保存为：`D:\AI-Video\ComfyUI\models\checkpoints\v1-5-pruned-emaonly.ckpt`。

脚本支持 `curl.exe --continue-at -` 断点续传尝试，网络长期低于 10KB/s 时会主动中止，以便重试；服务端需支持 HTTP Range。文件不足预期大小时不会当作成功。**当前尚未在用户机器上验证下载速度或完整文件哈希。**

## 第四步：重启 ComfyUI

在原 ComfyUI 窗口按 `Ctrl+C` 停止，再在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_windows_v100.ps1 -Root "D:\AI-Video"
```

## 第五步：生成第一张图片

另开一个 PowerShell 窗口，在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\generate_first_image.ps1 -Root "D:\AI-Video" -Model modelscope
```

默认输出位置：`D:\AI-Video\ComfyUI\output`，文件名以 `lost_signal_lab_S001_` 开头。

**注意：** `QUEUE SUBMITTED` 只代表已提交任务，不代表生成成功。生成成功需要检查 ComfyUI 页面和输出图片。

## 备用方案

如果魔搭下载也慢，可以改用浏览器/下载管理器从魔搭模型页面下载该 checkpoint，再手动放入上面的 `checkpoints` 目录；必须保留准确文件名。先不要反复切换源、混用不同模型的 `.part` 文件。

## 验收状态

- [x] V100 CUDA 验证（用户反馈）
- [x] 国内魔搭下载脚本及生成脚本适配已提交
- [ ] 魔搭模型下载完成
- [ ] 图片实际生成成功
