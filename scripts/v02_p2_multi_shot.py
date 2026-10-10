"""Local-only multi-clip motion assembly; never modifies original clips."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

def probe(binary, path):
    p = subprocess.run([binary, "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                       capture_output=True, text=True)
    if p.returncode:
        return 0.0
    try:
        return float(p.stdout.strip())
    except ValueError:
        return 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="D:/AI-Video")
    ap.add_argument("--max-shots", type=int, default=19)
    ap.add_argument("--shot-seconds", type=float, default=4.0)
    args = ap.parse_args()
    if not 1 <= args.max_shots <= 19 or not 1 <= args.shot_seconds <= 8:
        raise ValueError("Invalid shot count or duration")
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("FFmpeg tools missing")
    base = Path(args.root) / "private" / "lost-signal"
    output = base / "v0.2" / "p2" / "assembly"
    output.mkdir(parents=True, exist_ok=True)
    # The original production uses S001-S019, not S01-S19.
    # Use only original scene clips, never rough cuts or concatenated previews.
    selected = []
    missing = []
    for i in range(1, args.max_shots + 1):
        scene = "S%03d" % i
        folder = base / ("phase6" if i <= 6 else "phase9")
        source = folder / (scene + ".mp4")
        if source.is_file() and probe(ffprobe, source) >= 0.5:
            selected.append((scene, source))
        else:
            missing.append(scene)
    if not selected:
        raise RuntimeError("No original S001-S019 clips found in phase6/phase9")
    fallback = False
    manifest = {"status": "rendering", "requested_shots": args.max_shots,
                "found_shots": len(selected), "missing_scenes":
                missing,
                "shots": [], "mapping_mode": "storyboard",
                "note": "Ordered by phase8 storyboard, only original S001-S019 clips"}
    plan = Path(__file__).resolve().parents[1] / "plans" / "phase8_lost_signal_storyboard.json"
    storyboard = json.loads(plan.read_text(encoding="utf-8"))
    order = [shot["id"] for act in storyboard["acts"] for shot in act["shots"]]
    selected.sort(key=lambda pair: order.index(pair[0]))
    segments = []
    for scene, source in selected:
        duration = probe(ffprobe, source)
        factor = min(2.0, max(1.0, args.shot_seconds / duration))
        limit = min(args.shot_seconds, duration * factor)
        target = output / (scene + ".mp4")
        tmp = output / (scene + ".tmp.mp4")
        vf = ("setpts=%.6f*(PTS-STARTPTS),fps=24,"
              "scale=1280:720:force_original_aspect_ratio=decrease,"
              "pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p" % factor)
        cmd = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
               "-i", str(source), "-vf", vf, "-t", str(limit),
               "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", str(tmp)]
        if subprocess.run(cmd, capture_output=True).returncode:
            raise RuntimeError("Render failed at " + scene)
        tmp.replace(target)
        segments.append(target)
        manifest["shots"].append({"scene": scene, "source_name": source.name,
                                  "source_seconds": round(duration, 3),
                                  "output_seconds": round(probe(ffprobe, target), 3)})
    # Concat demuxer with local ASCII-safe segment paths relative to list file.
    listing = output / "segments.txt"
    listing.write_text("".join("file '%s'\n" % p.name for p in segments), encoding="ascii")
    combined = output / "multi_shot_preview.mp4"
    temp = output / "multi_shot_preview.tmp.mp4"
    cmd = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "concat", "-safe", "0", "-i", str(listing),
           "-c", "copy", str(temp)]
    if subprocess.run(cmd, capture_output=True).returncode:
        raise RuntimeError("Concatenation failed")
    temp.replace(combined)
    manifest["status"] = "complete"
    manifest["total_seconds"] = round(probe(ffprobe, combined), 3)
    (output / "assembly_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("P2 ASSEMBLY COMPLETE")
    print("Shots:", len(selected), "/", args.max_shots)
    print("Missing scenes:", len(manifest["missing_scenes"]))
    print("Mapping mode:", manifest["mapping_mode"])
    print("Preview seconds:", manifest["total_seconds"])
    print("Outputs remain local.")

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("P2 ASSEMBLY ERROR:", type(error).__name__, str(error), file=sys.stderr)
        sys.exit(1)
