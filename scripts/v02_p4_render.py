"""P4 image-to-video pilot and full batch, preserving all private source assets."""
import argparse, hashlib, json, shutil, subprocess, time, urllib.request
from pathlib import Path

PLAN = Path(__file__).resolve().parents[1] / "plans/phase8_lost_signal_storyboard.json"
PILOT = {"S007", "S010", "S016"}
# Hands and instruments should not be hallucinated by SVD.
SAFE = {"S007", "S009", "S010", "S011", "S012", "S013", "S014", "S015", "S016", "S017", "S018"}

def api(url, path, data=None):
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(url + path, data=body, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=45) as resp: return json.load(resp)

def command(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode: raise RuntimeError(result.stderr[-1000:])

def duration(path):
    result = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of",
        "default=noprint_wrappers=1:nokey=1",str(path)],capture_output=True,text=True,check=True)
    return float(result.stdout.strip())

def safe_render(image, output, seconds):
    frames = seconds * 24
    vf = ("scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
          "zoompan=z='min(zoom+0.00015,1.015)':x='iw/2-(iw/zoom/2)':"
          f"y='ih/2-(ih/zoom/2)':d={frames}:s=1280x720:fps=24,format=yuv420p")
    tmp = output.with_name("tmp_" + output.name)
    command(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y","-loop","1",
             "-i",str(image),"-vf",vf,"-frames:v",str(frames),"-an","-c:v","libx264",
             "-preset","medium","-crf","19",str(tmp)])
    tmp.replace(output)

def svd_render(image, output, scene, root, server, timeout):
    inp = root / "ComfyUI/input"
    inp.mkdir(parents=True,exist_ok=True)
    filename = f"p4_{scene}_{hashlib.sha256(image.read_bytes()).hexdigest()[:10]}.png"
    shutil.copy2(image,inp/filename)
    nodes = api(server,"/object_info")
    graph = {
      "1":{"class_type":"ImageOnlyCheckpointLoader","inputs":{"ckpt_name":"svd.safetensors"}},
      "2":{"class_type":"LoadImage","inputs":{"image":filename}},
      "3":{"class_type":"SVD_img2vid_Conditioning","inputs":{"width":1024,"height":576,
          "video_frames":14,"motion_bucket_id":28,"fps":6,"augmentation_level":0,
          "clip_vision":["1",1],"init_image":["2",0],"vae":["1",2]}},
      "4":{"class_type":"VideoLinearCFGGuidance","inputs":{"model":["1",0],"min_cfg":1}},
      "5":{"class_type":"KSampler","inputs":{"seed":2026101200+int(scene[1:]),"steps":24,
          "cfg":2.0,"sampler_name":"euler","scheduler":"karras","denoise":1,
          "model":["4",0],"positive":["3",0],"negative":["3",1],"latent_image":["3",2]}},
      "6":{"class_type":"VAEDecode","inputs":{"samples":["5",0],"vae":["1",2]}},
      "7":{"class_type":"SaveImage","inputs":{"filename_prefix":"p4_"+scene,"images":["6",0]}}
    }
    for item in graph.values():
        kind = item["class_type"]
        if kind not in nodes: raise RuntimeError("Missing node: "+kind)
        fields = set(nodes[kind].get("input",{}).get("required",{})) | set(nodes[kind].get("input",{}).get("optional",{}))
        if set(item["inputs"]) - fields: raise RuntimeError("Unsupported node inputs: "+kind)
    result = api(server,"/prompt",{"prompt":graph,"client_id":"emc-p4"})
    pid = result.get("prompt_id")
    if not pid: raise RuntimeError("Prompt rejected: "+str(result))
    deadline = time.monotonic()+timeout
    while time.monotonic()<deadline:
        record = api(server,"/history/"+pid).get(pid)
        if record:
            status = record.get("status",{})
            if status.get("status_str")=="error": raise RuntimeError(str(status.get("messages",[]))[-800:])
            if status.get("completed"):
                images = [x for node in record.get("outputs",{}).values() for x in node.get("images",[])]
                if len(images)!=14: raise RuntimeError("Expected 14 frames, got "+str(len(images)))
                folder = output.parent / "svd_frames"
                folder.mkdir(parents=True,exist_ok=True)
                base = (root/"ComfyUI/output").resolve()
                for i,item in enumerate(images):
                    src = (base/item.get("subfolder","")/item["filename"]).resolve()
                    if not src.is_relative_to(base): raise RuntimeError("Unsafe output path")
                    shutil.copy2(src,folder/f"frame_{i:03d}.png")
                tmp = output.with_name("tmp_"+output.name)
                command(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                    "-framerate","6","-i",str(folder/"frame_%03d.png"),"-an",
                    "-c:v","libx264","-pix_fmt","yuv420p","-crf","19",str(tmp)])
                tmp.replace(output)
                return pid
        time.sleep(3)
    raise TimeoutError("ComfyUI timed out: "+pid)

def main():
    p = argparse.ArgumentParser(description="P4: pilot or approved full batch")
    p.add_argument("--root",default="D:/AI-Video")
    p.add_argument("--server",default="http://127.0.0.1:8188")
    p.add_argument("--mode",choices=["pilot","all"],default="pilot")
    p.add_argument("--accept-pilot",action="store_true")
    p.add_argument("--engine",choices=["safe","hybrid","svd-test"],default="hybrid")
    p.add_argument("--timeout",type=int,default=2400)
    args = p.parse_args()
    if args.mode=="all" and not args.accept_pilot:
        p.error("Review pilot videos first, then pass --accept-pilot")
    root = Path(args.root)
    base = root/"private/lost-signal/v0.2"
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    shots = [s for act in plan["acts"] for s in act["shots"]]
    if len(shots)!=19 or sum(s["seconds"] for s in shots)!=103: raise RuntimeError("Storyboard invalid")
    manifest = json.loads((base/"manifest.json").read_text(encoding="utf-8-sig"))
    records = {r["shot"]:r for r in manifest["shots"]}
    selected = [s for s in shots if args.mode=="all" or s["id"] in PILOT]
    sources = {}
    for shot in selected:
        sid = shot["id"]
        src = (base/"keyframes"/records[sid]["filename"]).resolve()
        if src.parent!=(base/"keyframes").resolve() or not src.is_file():
            raise FileNotFoundError(f"{sid}: invalid image path {src}")
        sources[sid] = src
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"): raise RuntimeError("FFmpeg missing")
    out = base/"p4"/("pilot" if args.mode=="pilot" else "full")
    out.mkdir(parents=True,exist_ok=True)
    report = {"mode":args.mode,"engine":args.engine,"status":"running","shots":[],
              "warnings":[],"visual_accepted":False}
    for shot in selected:
        sid,seconds = shot["id"],shot["seconds"]
        scene_dir = out/sid
        scene_dir.mkdir(parents=True,exist_ok=True)
        target = scene_dir/(sid+".mp4")
        method,pid = "safe",None
        # Default pilot uses safe motion on all 3 sensitive test shots.
        if args.engine=="svd-test" or (args.engine=="hybrid" and sid not in SAFE):
            try:
                raw = scene_dir/(sid+"_svd_raw.mp4")
                pid = svd_render(sources[sid],raw,sid,root,args.server.rstrip("/"),args.timeout)
                raw_duration = duration(raw)
                factor = min(2.0,seconds/raw_duration)
                moving = min(seconds,raw_duration*factor)
                temp = scene_dir/"moving.mp4"
                command(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                    "-i",str(raw),"-vf",f"setpts={factor}*(PTS-STARTPTS),fps=24,scale=1280:720,format=yuv420p",
                    "-t",str(moving),"-an","-c:v","libx264","-crf","19",str(temp)])
                command(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                    "-i",str(temp),"-vf",f"tpad=stop_mode=clone:stop_duration={max(0,seconds-moving)+0.1},fps=24",
                    "-t",str(seconds),"-an","-c:v","libx264","-crf","19",str(target)])
                method = "svd"
            except Exception as exc:
                report["warnings"].append(f"{sid}: SVD failed, safe fallback: {exc}")
                safe_render(sources[sid],target,seconds)
                method = "safe_fallback"
        else:
            safe_render(sources[sid],target,seconds)
        actual = duration(target)
        if abs(actual-seconds)>0.12: raise RuntimeError(f"{sid}: wrong duration {actual}")
        report["shots"].append({"shot":sid,"target_seconds":seconds,"actual_seconds":round(actual,3),
            "method":method,"input_sha256":hashlib.sha256(sources[sid].read_bytes()).hexdigest(),
            "output":str(target),"prompt_id":pid,"visual_accepted":False})
        (out/"render_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        print(f"{sid}: {method} {actual:.2f}s",flush=True)
    report["status"]="rendered_pending_visual_review"
    (out/"render_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("P4 RENDER COMPLETE:",len(selected),"clips; visual review required")
    print("Report:",out/"render_report.json")

if __name__=="__main__":
    main()
