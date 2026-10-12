"""Run three approved image-to-video workflow jobs against local ComfyUI.

Requires an API-format ComfyUI workflow with a LoadImage node and SaveImage
output. Does not alter model nodes or silently substitute an incompatible model.
"""
import argparse,copy,datetime,hashlib,json,pathlib,shutil,subprocess,time,urllib.request
SHOTS={"S007":6,"S010":6,"S016":5}
def api(base,path,payload=None,timeout=45):
    data=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(base+path,data=data,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.load(r)
def run(args):
    p=subprocess.run(args,capture_output=True,text=True,errors="replace")
    if p.returncode:raise RuntimeError(p.stderr[-2000:])
    return p.stdout
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default="D:/AI-Video")
    p.add_argument("--comfy-root",default="")
    p.add_argument("--server",default="http://127.0.0.1:8188")
    p.add_argument("--workflow",required=True,help="ComfyUI API-format workflow JSON")
    p.add_argument("--image-node",required=True,help="LoadImage node ID")
    p.add_argument("--save-node",required=True,help="SaveImage node ID")
    p.add_argument("--timeout",type=int,default=3600)
    a=p.parse_args()
    root=pathlib.Path(a.root); comfy=pathlib.Path(a.comfy_root) if a.comfy_root else root/"ComfyUI"
    base=root/"private/lost-signal/v0.2"
    out=root/"private/lost-signal/v0.3/pilot"
    out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((base/"manifest.json").read_text(encoding="utf-8-sig"))
    records={x["shot"]:x["filename"] for x in manifest["shots"]}
    wf=json.loads(pathlib.Path(a.workflow).read_text(encoding="utf-8-sig"))
    if "prompt" in wf and isinstance(wf["prompt"],dict):wf=wf["prompt"]
    if not isinstance(wf,dict) or a.image_node not in wf or a.save_node not in wf:
        raise ValueError("Workflow must be API-format keyed node IDs and contain specified nodes")
    if wf[a.image_node].get("class_type")!="LoadImage" or wf[a.save_node].get("class_type")!="SaveImage":
        raise ValueError("Selected nodes must be LoadImage and SaveImage")
    nodes=api(a.server.rstrip("/"),"/object_info")
    for node in wf.values():
        if not isinstance(node,dict) or node.get("class_type") not in nodes:
            raise ValueError("Unknown ComfyUI node: "+str(node.get("class_type") if isinstance(node,dict) else node))
    for tool in ("ffmpeg","ffprobe"):
        if not shutil.which(tool):raise RuntimeError(tool+" missing")
    report={"status":"running","workflow":str(a.workflow),"shots":[],"warnings":[],
            "visual_acceptance":"pending_manual_review"}
    report_path=out/"benchmark_report.json"
    for sid,seconds in SHOTS.items():
        source=(base/"keyframes"/records[sid]).resolve()
        if source.parent!=(base/"keyframes").resolve() or not source.is_file():
            raise FileNotFoundError(str(source))
        name="v03_"+sid+"_"+hashlib.sha256(source.read_bytes()).hexdigest()[:10]+source.suffix
        input_dir=comfy/"input";input_dir.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,input_dir/name)
        graph=copy.deepcopy(wf)
        graph[a.image_node]["inputs"]["image"]=name
        prefix="v03_"+sid+"_"+str(int(time.time()))
        graph[a.save_node]["inputs"]["filename_prefix"]=prefix
        start=time.monotonic()
        response=api(a.server.rstrip("/"),"/prompt",{"prompt":graph,"client_id":"emc-v03"})
        pid=response.get("prompt_id")
        if not pid:raise RuntimeError("Workflow rejected: "+str(response))
        deadline=time.monotonic()+a.timeout
        history=None
        while time.monotonic()<deadline:
            history=api(a.server.rstrip("/"),"/history/"+pid).get(pid)
            if history:
                status=history.get("status",{})
                if status.get("status_str")=="error":raise RuntimeError(sid+": "+str(status.get("messages"))[-2500:])
                if status.get("completed"):break
            time.sleep(4)
        else:raise TimeoutError(sid+" timed out, prompt_id="+pid)
        images=history.get("outputs",{}).get(a.save_node,{}).get("images",[])
        if len(images)<2:raise RuntimeError(sid+": SaveImage produced fewer than two frames")
        folder=out/sid;folder.mkdir(exist_ok=True)
        frames=folder/"frames";frames.mkdir(exist_ok=True)
        output_base=(comfy/"output").resolve()
        for i,item in enumerate(images):
            src=(output_base/item.get("subfolder","")/item["filename"]).resolve()
            if not src.is_relative_to(output_base):raise ValueError("Unsafe frame path")
            shutil.copy2(src,frames/f"frame_{i:05d}.png")
        # Benchmark encodes native frame sequence at 24fps, WITHOUT fake extension or freeze frames.
        video=folder/(sid+"_native.mp4")
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-framerate","24",
             "-i",str(frames/"frame_%05d.png"),"-an","-c:v","libx264","-pix_fmt","yuv420p",
             "-crf","18",str(video)])
        info=json.loads(run(["ffprobe","-v","error","-show_entries",
            "format=duration:stream=width,height,r_frame_rate","-of","json",str(video)]))
        record={"shot":sid,"target_seconds":seconds,"native_frames":len(images),
                "native_duration_seconds":float(info["format"]["duration"]),
                "resolution":f'{info["streams"][0]["width"]}x{info["streams"][0]["height"]}',
                "wall_seconds":round(time.monotonic()-start,1),"video":str(video),
                "prompt_id":pid,"human_quality":"pending"}
        report["shots"].append(record)
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        print(sid,record,flush=True)
    report["status"]="generated_pending_visual_review"
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("BENCHMARK COMPLETE:",report_path)
if __name__=="__main__":main()
