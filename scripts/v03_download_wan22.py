"""Download official Wan 2.2 TI2V-5B ComfyUI weights with TLS verification and resume.

Usage: D:\\AI-Video\\.venv\\Scripts\\python.exe scripts/v03_download_wan22.py
"""
import argparse,hashlib,json,pathlib,sys,time,urllib.error,urllib.request
BASE="https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files"
FILES=[
("diffusion_models","wan2.2_ti2v_5B_fp16.safetensors"),
("text_encoders","umt5_xxl_fp8_e4m3fn_scaled.safetensors"),
("vae","wan2.2_vae.safetensors"),
]
def fetch(folder,name,dest):
    url=f"{BASE}/{folder}/{name}"
    partial=dest.with_name(dest.name+".part")
    if dest.is_file() and dest.stat().st_size>1024*1024:
        print("EXISTS:",dest,"(verify hash separately if previously downloaded)",flush=True);return
    for attempt in range(5):
        pos=partial.stat().st_size if partial.exists() else 0
        req=urllib.request.Request(url,headers={"User-Agent":"emc-vision-studio-v0.3/1.0","Range":f"bytes={pos}-"} if pos else {"User-Agent":"emc-vision-studio-v0.3/1.0"})
        try:
            with urllib.request.urlopen(req,timeout=120) as resp:
                status=resp.status
                if pos and status!=206:
                    partial.unlink(missing_ok=True);pos=0
                total_header=resp.headers.get("Content-Length")
                total=int(total_header)+pos if total_header and status==206 else int(total_header) if total_header else None
                mode="ab" if pos and status==206 else "wb"
                downloaded=pos if mode=="ab" else 0
                with partial.open(mode) as f:
                    while True:
                        chunk=resp.read(1024*1024)
                        if not chunk:break
                        f.write(chunk);downloaded+=len(chunk)
                        if downloaded%(256*1024*1024)<len(chunk):
                            print(f"  {name}: {downloaded/1024**3:.2f} GB"+(f" / {total/1024**3:.2f} GB" if total else ""),flush=True)
                if total is not None and downloaded!=total:raise IOError(f"Incomplete: {downloaded} != {total}")
                if partial.stat().st_size<1024*1024:raise IOError("Downloaded file unexpectedly small")
                with partial.open("rb") as f:
                    head=f.read(512).lstrip()
                if head.startswith((b"<",b"{")):
                    raise IOError("Response resembles HTML/JSON, not a model file")
                partial.replace(dest)
                print("DOWNLOADED:",dest,round(dest.stat().st_size/1024**3,2),"GB",flush=True)
                return
        except (OSError,urllib.error.URLError) as e:
            print(f"Attempt {attempt+1}/5 failed for {name}: {e}",flush=True)
            if attempt==4:raise
            time.sleep(min(30,2**attempt))
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default="D:/AI-Video")
    args=ap.parse_args()
    modelroot=pathlib.Path(args.root)/"ComfyUI/models"
    for folder,name in FILES:
        target=modelroot/folder/name
        target.parent.mkdir(parents=True,exist_ok=True)
        fetch(folder,name,target)
    print("All required files present. Restart ComfyUI to refresh model lists.")
    print("IMPORTANT: Model load/inference on V100S sm70 and FP8 text encoder remain unverified.")
if __name__=="__main__":main()
