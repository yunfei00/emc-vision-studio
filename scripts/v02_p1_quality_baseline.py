"""Offline, privacy-preserving v0.2 P1 video quality baseline."""
import argparse
import json
import pathlib
import shutil
import statistics
import subprocess
import sys

def run_json(command):
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)

def inspect(ffprobe, path):
    data = run_json([ffprobe, "-v", "error", "-show_entries",
                     "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate",
                     "-of", "json", str(path)])
    streams = data.get("streams", [])
    return {"duration_seconds": round(float(data.get("format", {}).get("duration", 0)), 3),
            "video": next((s for s in streams if s.get("codec_type") == "video"), None),
            "audio": next((s for s in streams if s.get("codec_type") == "audio"), None)}

def motion_metrics(ffmpeg, path):
    # No image frames are saved or uploaded. Blackdetect is avoided: content is confidential.
    # mpdecimate identifies repeated frames without requiring numpy or OpenCV.
    result = subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "info", "-i", str(path),
                             "-vf", "mpdecimate", "-an", "-f", "null", "-"],
                            capture_output=True, text=True, errors="replace")
    if result.returncode:
        return {"status": "unavailable", "reason": "ffmpeg mpdecimate failed"}
    # Use metadata frame counts via ffprobe for exact decoded input and output counts.
    count = subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "info", "-i", str(path),
                            "-vf", "mpdecimate", "-an", "-f", "null", "-"],
                           capture_output=True, text=True, errors="replace")
    import re
    matches = re.findall(r"frame=\s*(\d+)", count.stderr)
    kept = int(matches[-1]) if matches else None
    return {"status": "ok" if kept is not None else "unavailable",
            "frames_kept_after_mpdecimate": kept,
            "note": "Approximate duplicate-frame metric; not a semantic motion score"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/AI-Video")
    args = parser.parse_args()
    root = pathlib.Path(args.root)
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("ffmpeg and ffprobe must be in PATH")
    base = root / "private" / "lost-signal"
    output = base / "v0.2" / "p1"
    output.mkdir(parents=True, exist_ok=True)
    full = base / "delivery" / "lost_signal_full_103s.mp4"
    if not full.is_file():
        raise FileNotFoundError("Missing v0.1 delivery: " + str(full))
    report = {"version": "v0.2-P1", "privacy": "Local-only; no media is uploaded",
              "full": {"path": str(full), **inspect(ffprobe, full)},
              "svd_clips": [], "known_limits": []}
    paths = list((base / "phase6").glob("S00*.mp4"))
    paths += list((base / "phase9").rglob("S0*.mp4"))
    unique = {str(p.resolve()): p for p in paths}
    for path in sorted(unique.values(), key=lambda p: str(p)):
        report["svd_clips"].append({"scene": path.stem, "path": str(path),
                                    **inspect(ffprobe, path)})
    durations = [item["duration_seconds"] for item in report["svd_clips"]]
    if durations:
        report["svd_clip_duration_summary"] = {
            "count": len(durations), "min_seconds": min(durations),
            "median_seconds": statistics.median(durations), "max_seconds": max(durations)}
    report["known_limits"] = [
        "Short source SVD clips may be held as freeze frames to fill 103 seconds.",
        "Clip length alone does not measure visible movement.",
        "Character consistency and cinematic quality need human review.",
        "The automated report does not save frames or transmit any media."
    ]
    path = output / "quality_baseline.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("V0.2 P1 BASELINE COMPLETE:", path)
    print("Full video seconds:", report["full"]["duration_seconds"])
    print("Detected source clips:", len(report["svd_clips"]))
    if durations:
        print("Median source clip seconds:", statistics.median(durations))
    print("No media uploaded.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("V0.2 P1 ERROR:", exc, file=sys.stderr)
        sys.exit(1)
