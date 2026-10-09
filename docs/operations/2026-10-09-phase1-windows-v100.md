# Phase 1：Windows 10 + Tesla V100（uv 环境管理）操作手册

**状态：已编写并提交脚本，尚未在目标电脑实际运行验证。**

## 已确认配置

Windows 10、Tesla V100 32GB 显存、128GB 系统内存、2TB 硬盘。Python 安装、虚拟环境创建和依赖管理全部由 **uv** 负责，不使用 Conda，也不要求单独安装 Python。

## 第一步：准备 uv 和 Git

- uv 官方 Windows 安装说明：https://docs.astral.sh/uv/getting-started/installation/
- Git for Windows：https://git-scm.com/download/win

在 PowerShell 安装 uv：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

安装 Git for Windows 后，重新打开 PowerShell。若已经安装 uv/Git，跳过本步骤。

## 第二步：获取项目

```powershell
git clone https://github.com/yunfei00/emc-vision-studio.git
cd emc-vision-studio
```

已经克隆则进入项目目录执行 `git pull`。

## 第三步：运行 uv 自动安装

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_windows_v100.ps1 -Root "D:\AI-Video"
```

脚本自动执行：`uv python install 3.12`、`uv venv`、`uv pip install`；安装 PyTorch 2.7.0/cu126 候选版本；运行两次 V100 CUDA 矩阵测试；拉取并安装 ComfyUI 依赖。**如果 V100 的 sm_70 不受当前 PyTorch wheel 支持，脚本会停止，不能视为安装成功。**

> 2TB 硬盘容量不等于 D 盘一定存在。如果没有 D 盘，请将 `-Root` 改成实际有足够空间的目录，如 `"C:\AI-Video"`。

## 第四步：启动 ComfyUI

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_windows_v100.ps1 -Root "D:\AI-Video"
```

浏览器打开：http://127.0.0.1:8188

## 第五步：验收

- [ ] uv 可运行，Python 3.12 由 uv 安装
- [ ] V100 GPU CUDA 实算通过
- [ ] ComfyUI 能启动且本机网页可访问
- [ ] 后续安装兼容视频模型并生成可播放的 5 秒 Demo

### 注意

- 目前只交付环境安装脚本，尚未远程执行或生成 Demo。
- Tesla V100 是 Volta sm_70，不使用要求 BF16/FlashAttention-2 的方案。
- ComfyUI 上游依赖会变化，安装后必须再次检查 CUDA 实算。
- Python 包管理仅使用 uv，**不使用 pip 命令、Conda 或系统 Python 虚拟环境管理**。
