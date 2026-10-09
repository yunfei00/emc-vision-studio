# Phase 2：首张实验室画面——国内镜像与断点续传版

## 当前状态

V100 CUDA 运算已经通过（用户反馈）。已将原来基于 `Invoke-WebRequest` 的下载方式改为 **Hugging Face 国内镜像 + curl.exe 断点续传**。本地下载尚未验证成功。

## 文件位置

- 本文档：`emc-vision-studio\docs\operations\2026-10-09-phase2-first-image.md`
- 下载脚本：`emc-vision-studio\scripts\download_first_image_model.ps1`
- 默认模型目录：`D:\AI-Video\ComfyUI\models\checkpoints`

## 第一步：更新项目

在本地 `emc-vision-studio` 根目录打开 PowerShell：

```powershell
git pull
```

## 第二步：使用国内镜像下载（推荐）

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\download_first_image_model.ps1 -Root "D:\AI-Video" -Source mirror
```

镜像站：`https://hf-mirror.com`。如果此前下载中断，**再次执行同一条命令**。临时文件会保存在模型目录中，以 `.safetensors.part` 结尾。脚本使用 `curl.exe --continue-at -` 尝试 HTTP Range 续传。是否真正续传取决于服务器是否支持 Range；若不支持，curl 会报错而不是将部分文件当成成功结果。

> 如果安装根目录不是 D 盘，修改 `-Root` 为你的实际安装目录。

### 备用：官方源

镜像不可用时：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\download_first_image_model.ps1 -Root "D:\AI-Video" -Source official
```

**注意：** 不同来源可能重定向到不同存储端点；如果已有 `.part` 文件，切换来源后应先确认两边文件确实一致，否则不要盲目混用部分文件。

## 第三步：启动 ComfyUI

下载成功后，重启 ComfyUI：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_windows_v100.ps1 -Root "D:\AI-Video"
```

浏览器：`http://127.0.0.1:8188`。

## 第四步：生成第一张图片

在另一个 PowerShell 窗口、项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\generate_first_image.ps1 -Root "D:\AI-Video"
```

看到 `QUEUE SUBMITTED` 只代表已入队。真正生成成功后，图片在：

```text
D:\AI-Video\ComfyUI\output
```

文件名以 `lost_signal_lab_S001_` 开头。

## 备用国内平台

魔搭社区：https://modelscope.cn/ 。其官方 CLI 支持 `modelscope download --model <仓库ID> --local_dir <目录>`。但**尚未核实本项目指定 checkpoint 的魔搭仓库 ID**，因此没有编造下载命令。先使用镜像方式，后续如有准确的魔搭模型仓库再增加对应脚本。

## 验收状态

- [x] CUDA 运算通过（用户反馈）
- [x] 镜像与断点续传脚本已提交
- [ ] 模型完整下载并校验
- [ ] 图片生成成功
- [ ] 结果提交 GitHub

参考：https://hf-mirror.com/ 、https://github.com/modelscope/modelscope/blob/master/docs/source/command.md
