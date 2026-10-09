# Phase 1：Windows 10 + Tesla V100（uv 环境管理）操作手册

## 当前进度（2026-10-09）

用户已在 Windows 10 / Tesla V100 32GB 上完成安装，并确认 **ComfyUI 网页正常打开**。后台出现 `no opengl-accelerate module loaded`。该消息通常只说明可选 OpenGL 加速模块未加载，**单凭此消息不能判定 CUDA 故障**。不需要仅为该提示重装 ComfyUI。

**已验证：** 本地 Web 界面可访问（用户反馈）。**待验证：** CUDA 实算、模型加载和视频生成。

## 一、Python 环境管理

全程使用 **uv** 管理 Python 3.12、虚拟环境和依赖；不使用 Conda。

## 二、当前需要执行的操作：CUDA 验证

打开 PowerShell，进入已经克隆的 `emc-vision-studio` 仓库目录，先更新脚本：

```powershell
git pull
```

然后运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_windows_v100.ps1 -Root "D:\AI-Video"
```

若之前将 ComfyUI 安装到 C 盘或其他路径，修改 `-Root` 为安装时使用的路径。

**通过标准：** 看到 `GPU 架构: (7, 0)` 和 `CUDA 矩阵运算：通过`。若失败，保留错误信息，不要盲目升级驱动或重装全部依赖。

## 三、后续启动

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_windows_v100.ps1 -Root "D:\AI-Video"
```

浏览器访问 http://127.0.0.1:8188 。

## 四、OpenGL 提示如何处理

- `no opengl-accelerate module loaded` **不是 CUDA 推理失败的直接证据**。
- 若网页正常、CUDA 验证通过，暂时忽略。
- 如果后续具体节点出现 OpenGL 错误，再定位该节点所属插件及其依赖；不预先安装未知来源的模块。
- 这条提示的准确来源尚未定位，不把它标记为已经彻底修复。

## 五、阶段验收

- [x] ComfyUI 网页可打开（用户反馈）
- [ ] Tesla V100 CUDA 矩阵运算通过
- [ ] 加载合适的模型并成功生成图像
- [ ] 生成首个 5 秒视频 Demo

**注意：** 目前没有实际生成的媒体文件，不能声称视频制作已完成。
