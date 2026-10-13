"""v0.3 hardware and ComfyUI readiness report; no downloads or environment mutation."""
import argparse,json,os,pathlib,shutil,subprocess,sys,urllib.request,datetime
def cmd(argv,timeout=20):
    try:
        p=subprocess.run(argv,capture_output=True,text=True,timeout=timeout,errors="replace")
        return {"ok":p.returncode==0,"returncode":p.returncode,"stdout":p.stdout[-6000:],"stderr":p.stderr[-1500:]}
    except Exception as e:return {"ok":False,"error":str(e)}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default="D:/AI-Video")
    ap.add_argument("--comfy-url",default="http://127.0.0.1:8188")
    ap.add_argument("--comfy-root",default="")
    args=ap.parse_args()
    root=pathlib.Path(args.root)
    comfy=pathlib.Path(args.comfy_root) if args.comfy_root else root/"ComfyUI"
    out=root/"private/lost-signal/v0.3/reports"
    out.mkdir(parents=True,exist_ok=True)
    report={"created_at":datetime.datetime.now().isoformat(),"gpu":cmd(["nvidia-smi","--query-gpu=name,memory.total,memory.free,compute_cap,driver_version","--format=csv,noheader"]),
       "ffmpeg":cmd(["ffmpeg","-version"]),"ffprobe":cmd(["ffprobe","-version"]),
       "python":sys.version,"python_executable":sys.executable,"comfy_root":str(comfy),"comfy_available":False,
       "torch":None,"model_candidates":[],"recommendations":[]}
    try:
        import torch
        report["torch"]={"version":torch.__version__,"cuda_build":torch.version.cuda,
             "cuda_available":torch.cuda.is_available()}
        if torch.cuda.is_available():
            report["torch"]["device"]=torch.cuda.get_device_name(0)
            report["torch"]["capability"]=list(torch.cuda.get_device_capability(0))
    except Exception as e:report["torch"]={"error":str(e)}
    try:
        with urllib.request.urlopen(args.comfy_url.rstrip("/")+"/object_info",timeout=12) as resp:
            nodes=json.load(resp)
        report["comfy_available"]=True
        report["comfy_nodes"]=[x for x in nodes if any(y in x.lower() for y in ("wan","video","vae","sampler","checkpoint","unet","model"))][:100]
    except Exception as e:report["comfy_error"]=str(e)
    for directory in ("diffusion_models","unet","checkpoints","text_encoders","clip","vae"):
        folder=comfy/"models"/directory
        if folder.is_dir():
            for file in folder.iterdir():
                if file.is_file() and any(x in file.name.lower() for x in ("wan","umt5","t5","vae")):
                    report["model_candidates"].append({"folder":directory,"name":file.name,"size_gb":round(file.stat().st_size/1024**3,2)})
    report["recommendations"].append("V100S compute capability 7.0: confirm every Wan/attention kernel supports sm70; BF16 and newer fused kernels may be unsupported.")
    report["recommendations"].append("This report does not prove Wan inference compatibility. A real 5s generation test is required.")
    report["recommendations"].append("PyTorch in uv environment may differ from ComfyUI's Python interpreter.")
    path=out/"hardware_preflight.json"
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("V0.3 HARDWARE REPORT:",path)
    print("GPU:",report["gpu"].get("stdout","").strip())
    print("ComfyUI API:", "READY" if report["comfy_available"] else "NOT READY")
    print("Wan-related local model files:",len(report["model_candidates"]))
    torch_info=report["torch"] or {}\n    print("Torch in uv environment:", torch_info.get("version", "NOT INSTALLED (acceptable for preflight)"))\n    if torch_info.get("error"): print("Torch import note:", torch_info["error"][:180])\n    print("GPU driver check:", "PASS" if report["gpu"]["ok"] else "CHECK")\n    print("Next: send only the short console output above, not the full JSON.")
if __name__=="__main__":main()
