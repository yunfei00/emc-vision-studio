"""Assemble accepted v0.2 shots into a 103-second subtitled final with existing v0.1 audio."""
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path

REPAIR = {"S007","S009","S010","S011","S012","S013","S014","S015","S016","S017","S018"}
PLAN = Path(__file__).resolve().parents[1]/"plans/phase8_lost_signal_storyboard.json"

def run(cmd, cwd=None):
    p = subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,errors="replace")
    if p.returncode: raise RuntimeError("Command failed: "+" ".join(map(str,cmd[:8]))+"\n"+p.stderr[-2500:])
    return p.stdout

def probe(path):
    return json.loads(run(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height",
        "-of","json",str(path)]))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default="D:/AI-Video")
    p.add_argument("--no-subtitles",action="store_true",help="Only when burned subtitle filter is unavailable")
    args=p.parse_args()
    for tool in ("ffmpeg","ffprobe"):
        if not shutil.which(tool): raise RuntimeError(tool+" not found")
    root=Path(args.root)
    private=root/"private/lost-signal"
    base=private/"v0.2/p4"
    dest=private/"v0.2/delivery"
    dest.mkdir(parents=True,exist_ok=True)
    shots=[s for act in json.loads(PLAN.read_text(encoding="utf-8"))["acts"] for s in act["shots"]]
    if len(shots)!=19 or sum(s["seconds"] for s in shots)!=103: raise RuntimeError("Invalid 103s storyboard")
    # Existing v0.1 movie is an audio source only; v0.1 files remain untouched.
    audio_source=private/"phase10/lost_signal_phase10_voiced.mp4"
    subtitle=private/"phase10/lost_signal_zh.srt"
    if not audio_source.is_file(): raise FileNotFoundError("Missing original narration/music: "+str(audio_source))
    if not args.no_subtitles and not subtitle.is_file(): raise FileNotFoundError("Missing original SRT: "+str(subtitle))
    ainfo=probe(audio_source)
    if not any(x.get("codec_type")=="audio" for x in ainfo.get("streams",[])):
        raise RuntimeError("Existing v0.1 file has no audio stream")
    clips=[]
    for shot in shots:
        sid=shot["id"]
        source=base/("repair_dynamic" if sid in REPAIR else "full")/sid/(sid+".mp4")
        if not source.is_file(): raise FileNotFoundError("Required accepted clip missing: "+str(source))
        info=probe(source)
        if not any(x.get("codec_type")=="video" for x in info.get("streams",[])):
            raise RuntimeError("No video in "+str(source))
        actual=float(info["format"]["duration"])
        if abs(actual-shot["seconds"])>0.15:
            raise RuntimeError(f"{sid}: expected {shot['seconds']}s, got {actual:.3f}s")
        clips.append((sid,source,shot["seconds"]))
    print("Verified 19 inputs; preparing 103s final...",flush=True)
    # Use concat demuxer only after normalizing all sources to a consistent video format.
    stage=dest/"staging"
    stage.mkdir(exist_ok=True)
    normalized=[]
    for i,(sid,source,seconds) in enumerate(clips):
        target=stage/f"{i:02d}_{sid}.mp4"
        run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y","-i",str(source),
            "-vf","fps=24,scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,format=yuv420p",
            "-frames:v",str(seconds*24),"-an","-c:v","libx264","-preset","medium","-crf","19",
            "-video_track_timescale","12288",str(target)])
        frames=json.loads(run(["ffprobe","-v","error","-count_frames","-select_streams","v:0",
            "-show_entries","stream=nb_read_frames","-of","json",str(target)]))["streams"][0]
        if int(frames["nb_read_frames"])!=seconds*24:
            raise RuntimeError(f"{sid}: frame count mismatch")
        normalized.append(target)
        print(f"{i+1:02d}/19 {sid} OK",flush=True)
    listing=stage/"concat.txt"
    listing.write_text("".join("file '"+x.name+"'\n" for x in normalized),encoding="utf-8")
    picture=stage/"picture_103s.mp4"
    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0",
         "-i",str(listing),"-c","copy",str(picture)])
    if abs(float(probe(picture)["format"]["duration"])-103)>0.08:
        raise RuntimeError("Concatenated picture duration is not 103s")
    output=dest/"lost_signal_v0.2_final_103s.mp4"
    temp=dest/"final_pending_validation.mp4"
    cmd=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y","-i",str(picture),
         "-i",str(audio_source),"-map","0:v:0","-map","1:a:0",
         "-af","aresample=48000,apad,atrim=duration=103,asetpts=PTS-STARTPTS",
         "-c:a","aac","-b:a","192k"]
    if args.no_subtitles:
        cmd+=["-c:v","copy"]
    else:
        # Run in the SRT directory to avoid Windows drive colon escaping in libass.
        cmd+=["-vf","subtitles=lost_signal_zh.srt:charenc=UTF-8:force_style='FontName=Microsoft YaHei,FontSize=22,Outline=2,Shadow=1,Alignment=2,MarginV=34'",
              "-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p"]
    cmd+=["-t","103","-movflags","+faststart",str(temp)]
    run(cmd,cwd=subtitle.parent if not args.no_subtitles else None)
    result=probe(temp)
    types={x.get("codec_type") for x in result.get("streams",[])}
    if not {"video","audio"}<=types or abs(float(result["format"]["duration"])-103)>0.15:
        raise RuntimeError("Final verification failed; original files remain intact")
    temp.replace(output)
    report={"status":"assembled_pending_final_visual_review","duration":float(result["format"]["duration"]),
            "resolution":"1280x720","fps":24,"audio_source":str(audio_source),
            "subtitles":"burned" if not args.no_subtitles else "disabled",
            "shots":[{"shot":sid,"seconds":seconds,"source":str(path),
                "sha256":hashlib.sha256(path.read_bytes()).hexdigest()} for sid,path,seconds in clips],
            "output":str(output),"v0.1_untouched":True}
    (dest/"final_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("FINAL COMPLETE:",output,flush=True)
    print("REPORT:",dest/"final_report.json",flush=True)

if __name__=="__main__":
    main()
