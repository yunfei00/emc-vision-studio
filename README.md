# EMC Vision Studio｜AI 视频创作工作室

本项目记录企业技术宣传视频的本地 AI 制作学习过程，首部作品为《消失的信号》（90–120 秒正片及 30 秒短版）。

## 硬件环境
Windows 10、NVIDIA Tesla V100（32GB 显存）、128GB 系统内存、2TB 硬盘。以上配置已确认，无需重复检测。

## 从哪里开始
**操作入口：[`docs/操作指南.md`](docs/操作指南.md)**。此文件用中文说明每一步该打开哪个文档、哪个脚本、在哪个目录运行，以及当前完成状态。

- [`docs/operations/2026-10-09-phase1-windows-v100.md`](docs/operations/2026-10-09-phase1-windows-v100.md)：Phase 1 安装操作手册（中文）。
- [`docs/progress.md`](docs/progress.md)：项目进度。
- [`docs/acceptance/phase-1.md`](docs/acceptance/phase-1.md)：安装验收记录。
- [`productions/001-lost-signal/`](productions/001-lost-signal/)：首部作品素材与制作文档。

## 仓库规则
中文作为所有面向使用者的文档默认语言。GitHub Public 仓库允许提交学习素材、视频、图片和音频；大文件使用 Git LFS，模型权重和缓存不入库，密码及密钥不得提交。尚未实机运行的脚本不得标记为验收通过。
