"""Extract the last frame of the highest-priority shot for local continuation tests."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="D:/AI-Video")
    args = p.parse_args()
    base = Path(args.root) / "private" / "lost-signal"
    plan_path = base / "v0.2" / "p2" / "motion_extension_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    candidates = [item for item in plan["priority_order"] if item["gap_seconds"] >= 1]
    if not candidates:
        raise RuntimeError("No extension candidate")
    item = candidates[0]
    scene = item["scene"]
    source = base / ("phase6" if int(scene[1:]) <= 6 else "phase9") / (scene + ".mp4")
    if not source.is_file():
        raise FileNotFoundError(str(source))
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg not on PATH")
    folder = base / "v0.2" / "p2" / "continuation" / scene
    folder.mkdir(parents=True, exist_ok=True)
    frame = folder / "source_last_frame.png"
    cmd = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
           "-sseof", "-0.1", "-i", str(source), "-frames:v", "1", str(frame)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode or not frame.is_file():
        raise RuntimeError("Last frame extraction failed: " + result.stderr[-400:])
    metadata = {
        "scene": scene, "gap_seconds": item["gap_seconds"],
        "source_name": source.name, "last_frame_name": frame.name,
        "status": "awaiting_local_visual_review",
        "note": "No additional AI motion generated. Frame is an input candidate only.",
    }
    (folder / "continuation_candidate.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print("P2 CONTINUATION CANDIDATE READY")
    print("Scene:", scene)
    print("Gap seconds:", item["gap_seconds"])
    print("Frame:", frame)
    print("No GPU inference performed. All files remain local.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("P2 CONTINUATION ERROR:", type(error).__name__, str(error), file=sys.stderr)
        sys.exit(1)
