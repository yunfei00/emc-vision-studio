# 环境安装原则

目标：Windows 10、Tesla V100 32GB 显存、128GB 内存、2TB 硬盘。

**所有 Python 版本、虚拟环境、依赖安装统一使用 uv。** 不使用 Conda、python -m venv 或 pip 命令。详细复制命令统一在 [Phase 1 中文操作手册](../operations/2026-10-09-phase1-windows-v100.md)。

脚本：`scripts/install_windows_v100.ps1`；启动：`scripts/start_windows_v100.ps1`。

安装与渲染尚未实机验收。
