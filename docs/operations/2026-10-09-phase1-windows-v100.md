# Phase 1 — Windows 10 + Tesla V100 32GB 安装手册

**状态：脚本已提交，尚未在用户电脑执行；ComfyUI 和视频模型均未验收。**

## 已知硬件

Windows 10、Tesla V100 32GB 显存、128GB 内存、2TB 硬盘。无需再次提供这些信息。

## 为什么选 CUDA 12.6

V100 是 Volta sm_70。PyTorch 的 CUDA 12.8/13.0 新构建不应直接用于 V100；选择官方仍提供的 PyTorch 2.7.0 + cu126 作为第一轮兼容性候选，运行时必须做 CUDA 矩阵计算测试。不要安装 ComfyUI 默认的 CUDA 13 Portable 版。

来源：
- https://github.com/Comfy-Org/ComfyUI
- https://pytorch.org/get-started/previous-versions/
- https://github.com/pytorch/pytorch/issues/172352

## 第一步：前置软件（仅首次）

安装 Windows Git：https://git-scm.com/download/win
安装 Python 3.12 64-bit：https://www.python.org/downloads/windows/
确保 PowerShell 可使用 `git` 和 `py -3.12`。

## 第二步：获取项目

打开 PowerShell，在准备放项目的目录运行：

```powershell
git clone https://github.com/yunfei00/emc-vision-studio.git
cd emc-vision-studio
```

已有项目则执行 `git pull`。

## 第三步：自动安装

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_windows_v100.ps1 -Root "D:\AI-Video"
```

脚本会建立独立 Python 3.12 环境、拉取 ComfyUI、安装 PyTorch 2.7.0/cu126、执行 GPU 实算验证，再安装 ComfyUI 依赖。默认安装目录 D:\AI-Video，可按磁盘调整。**不会安装模型权重，也不会自动生成视频。** 如 GPU 测试失败，脚本停止，避免继续安装错误依赖。

## 第四步：启动

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_windows_v100.ps1 -Root "D:\AI-Video"
```

浏览器打开 http://127.0.0.1:8188 。保持 PowerShell 窗口运行。

## 验收与故障

1. 安装过程应显示 Tesla V100 和 CUDA 矩阵运算通过。
2. 启动后本机可访问 8188 页面。
3. 如提示驱动过旧，记录报错再选驱动升级方案；不盲目更新。
4. 如提示 `no kernel image` 或 `sm_70`，停止并检查 torch 架构列表，不要强行运行。
5. 如 ComfyUI 依赖升级或替换 torch，需重新运行 GPU 测试。
6. 下一步再确定 V100 可运行、授权明确的视频模型及首个 5 秒 Demo。

### 提交证据

记录实际运行的 ComfyUI commit、torch/CUDA 版本、GPU 计算结果、启动日志和模型许可证；**目前全部未实机验证**。
