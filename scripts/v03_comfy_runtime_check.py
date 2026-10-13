"""Inspect the exact ComfyUI Python environment and video-model support without modifying it."""
import json,pathlib,subprocess,sys,urllib.request
ROOT=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path("D:/AI-Video")
PY=ROOT/".venv/Scripts/python.exe"
COMFY=ROOT/"ComfyUI"
OUT=ROOT/"private/lost-signal/v0.3/reports"
OUT.mkdir(parents=True,exist_ok=True)
probe="""import json,sys
result={"python":sys.executable}
try:
 import torch
 result.update(torch=torch.__version__,cuda=torch.version.cuda,cuda_available=torch.cuda.is_available())
 if torch.cuda.is_available():
  result.update(device=torch.cuda.get_device_name(0),capability=list(torch.cuda.get_device_capability(0)),bf16_supported=torch.cuda.is_bf16_supported())
except Exception as e: result["error"]=repr(e)
print(json.dumps(result))
"""
if not PY.is_file():raise SystemExit("ComfyUI Python missing: "+str(PY))
p=subprocess.run([str(PY),"-c",probe],capture_output=True,text=True,errors="replace",timeout=90)
try: env=json.loads(p.stdout.strip().splitlines()[-1])
except Exception: env={"error":(p.stderr+" "+p.stdout)[-500:]}
report={"comfy_python":env,"comfy_root":str(COMFY),"api":{},"model_files":[]}
try:
 with urllib.request.urlopen("http://127.0.0.1:8188/object_info",timeout=15) as r:nodes=json.load(r)
 report["api"]={"ready":True,"wan_nodes":[n for n in nodes if "wan" in n.lower()],"video_nodes":[n for n in nodes if "video" in n.lower()][:30]}
except Exception as e:report["api"]={"ready":False,"error":str(e)}
for folder in ("diffusion_models","unet","checkpoints","vae","text_encoders","clip"):
 d=COMFY/"models"/folder
 if d.is_dir():
  for f in d.iterdir():
   if f.is_file() and any(s in f.name.lower() for s in ("wan","umt5","t5xxl")):
    report["model_files"].append(f.name)
path=OUT/"comfy_runtime_check.json"
path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("COMFY PYTHON:",env.get("python","unknown"))
print("TORCH:",env.get("torch",env.get("error","unknown")))
print("CUDA:",env.get("cuda","unknown"),"CAPABILITY:",env.get("capability","unknown"))
print("BF16:",env.get("bf16_supported","unknown"))
print("COMFY API:", "READY" if report["api"].get("ready") else "NOT READY")
print("WAN NODES:",len(report["api"].get("wan_nodes",[])))
print("WAN MODEL FILES:",len(report["model_files"]))
print("REPORT:",path)
