"""Offline video quality baseline. Only local aggregate reports are written."""
import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys

def execute(args):
    return subprocess.run(args, capture_output=True, text=True, errors="replace")

def probe(binary, path):
    p = execute([binary, "-v", "error", "-show_entries",
                 "format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate,nb_frames",
                 "-of", "json", str(path)])
    if p.returncode:
        raise RuntimeError("ffprobe failed for " + path.name)
    obj = json.loads(p.stdout)
    streams = obj.get("streams", [])
    return {"duration_seconds": round(float(obj.get("format", {}).get("duration", 0)), 3),
            "video": next((s for s in streams if s.get("codec_type") == "video"), None),
            "audio": next((s for s in streams if s.get("codec_type") == "audio"), None)}

def motion(binary, path):
    # metadata=print reports each retained frame without storing or exporting images.
    p = execute([binary, "-nostdin", "-hide_banner", "-loglevel", "info", "-i", str(path),
                 "-map", "0:v:0", "-vf", "mpdecimate,metadata=print", "-an", "-f", "null", "-"])
    if p.returncode:
        return {"status": "unavailable", "reason": "mpdecimate failed"}
    # Count retained frames using the final progress line.
    matches = re.findall(r"frame=\s*(\d+)", p.stderr)
    retained = int(matches[-1]) if matches else None
    return {"status": "ok" if retained is not None else "unavailable",
            "retained_frames": retained,
            "note": "Duplicate-frame proxy, not a semantic motion score"}

def audio_level(binary, path):
    p = execute([binary, "-nostdin", "-hide_banner", "-i", str(path),
                 "-vn", "-af", "volumedetect", "-f", "null", "-"])
    if p.returncode:
        return {"status": "unavailable"}
    values = {}
    for key in ("mean_volume", "max_volume"):
        match = re.search(key + r":\s*(-?[\d.]+) dB", p.stderr)
        values[key + "_db"] = float(match.group(1)) if match else None
    return {"status": "ok", **values}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/AI-Video")
    args = parser.parse_args()
    root = pathlib.Path(args.root)
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("ffmpeg and ffprobe must be on PATH")
    base = root / "private" / "lost-signal"
    full = base / "delivery" / "lost_signal_full_103s.mp4"
    if not full.is_file():
        raise RuntimeError("Expected local delivery missing; check delivery path")
    full_info = probe(ffprobe, full)
    full_info["motion"] = motion(ffmpeg, full)
    if full_info["audio"]:
        full_info["audio_level"] = audio_level(ffmpeg, full)
    clips = []
    for folder in ("phase6", "phase9"):
        directory = base / folder
        if directory.exists():
            clips.extend(p for p in directory.rglob("*.mp4") if p.is_file())
    clips = sorted(set(clips))
    report = {"version": "v0.2-P1-revised", "privacy": "local-only",
              "full": full_info, "clips": [], "thresholds": {
                  "target_duration_seconds": 103, "duration_tolerance_seconds": 1,
                  "target_width": 1920, "target_height": 1080},
              "warnings": []}
    for clip in clips:
        info = probe(ffprobe, clip)
        info["motion"] = motion(ffmpeg, clip)
        report["clips"].append({"scene": clip.stem, **info})
    if abs(full_info["duration_seconds"] - 103) > 1:
        report["warnings"].append("Full duration outside 103 +/- 1 seconds")
    video = full_info["video"] or {}
    if not video:
        report["warnings"].append("No video stream")
    if not full_info["audio"]:
        report["warnings"].append("No audio stream")
    if len(clips) < 19:
        report["warnings"].append("Fewer than 19 source clips discovered; verify source layout")
    report["limitations"] = [
        "mpdecimate is a duplicate-frame proxy, not an actual motion or aesthetic score",
        "No frame or media is saved or uploaded",
        "Scene-level freeze duration requires edit timeline metadata"]
    out = base / "v0.2" / "p1" / "quality_baseline.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("P1 COMPLETE")
    print("Duration:", full_info["duration_seconds"])
    print("Source clips:", len(clips))
    print("Warnings:", len(report["warnings"]))
    print("Report stored locally.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("P1 ERROR:", type(exc).__name__, str(exc), file=sys.stderr)
        sys.exit(1)
