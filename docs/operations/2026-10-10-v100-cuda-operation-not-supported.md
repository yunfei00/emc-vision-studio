# V100 推理失败：获取真正报错节点和 traceback

## 已知结果

用户已完成以下验证：Tesla V100S PCIe 32GB、sm_70、PyTorch 2.7.0+cu126，CUDA 可用；**FP32 矩阵乘法、FP32 卷积和 SDPA 三项均 PASS**。但是 Stable Diffusion 实际执行时报 `CUDA error: operation not supported`。

这说明基本 CUDA 算子可用，**不能据此认定是显卡驱动过旧，也不能认为所有 ComfyUI 算子都可用**。CUDA 错误可能异步报告，报错位置不一定是实际失败算子。需要获得失败节点和完整 Python traceback。

## 已做的代码改动

`scripts/generate_first_image.ps1` 现在提交任务后会持续查询 ComfyUI 的 `/history/{prompt_id}`，自动打印：

- `FAILED NODE`：出错节点 ID 和类型
- `EXCEPTION`：异常名称和内容
- `TRACEBACK`：ComfyUI 返回的 Python traceback
- 成功时显示 `GENERATION COMPLETE` 和输出文件信息

不再只打印 `QUEUE SUBMITTED` 就结束。

## 操作步骤

1. 关闭旧 ComfyUI 窗口（按 Ctrl+C），不要同时运行两个 ComfyUI 实例。
2. 在项目根目录执行：

```powershell
git pull
```

3. 以兼容模式启动 ComfyUI：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_windows_v100.ps1 -Root "D:\AI-Video" -SafeMode
```

4. 在**另一个 PowerShell 窗口**，项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\generate_first_image.ps1 -Root "D:\AI-Video" -Model modelscope
```

5. 如果失败，发送第二个窗口中 `FAILED NODE`、`EXCEPTION`、`TRACEBACK` 的输出。如果 history 没有 traceback，请发送 ComfyUI 服务窗口里 `Exception during processing` 附近的完整日志。

## 下一步处理原则

根据实际失败节点再判断是模型加载、采样器、VAE、注意力实现还是驱动 / PyTorch 组合问题。**暂时不重装环境、不重新下载模型**。

注意：这里的 CUDA 错误提示 `Compile with TORCH_USE_CUDA_DSA to enable device-side assertions` 只是 PyTorch 的通用建议，并不代表必须编译 PyTorch 才能排查。
