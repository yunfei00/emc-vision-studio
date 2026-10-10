"""P2: local-only SVD clip inventory and reversible motion preview."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

def probe(ffprobe, path):
    result = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                            capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("Cannot inspect local clip")
    return float(result.stdout.strip())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/AI-Video")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--seconds", type=float, default=6.0)
    args = parser.parse_args()
    if not 2 <= args.seconds <= 15:
        raise ValueError("Preview seconds must be between 2 and 15")
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("FFmpeg and ffprobe must be on PATH")
    base = Path(args.root) / "private" / "lost-signal"
    clips = sorted({p.resolve() for folder in ("phase6", "phase9")
                    for p in (base / folder).rglob("*.mp4") if p.is_file()})
    if not clips:
        raise RuntimeError("No local phase6/phase9 MP4 clips found")
    inventory = []
    for clip in clips:
        try:
            duration = probe(ffprobe, clip)
            inventory.append({"file": clip.name, "duration_seconds": round(duration, 3),
                              "source": str(clip.parent.relative_to(base))})
        except (RuntimeError, ValueError):
            inventory.append({"file": clip.name, "status": "probe_failed"})
    out = base / "v0.2" / "p2"
    out.mkdir(parents=True, exist_ok=True)
    report = {"phase": "v0.2-P2", "clip_count": len(clips), "clips": inventory,
              "preview": "not_requested"}
    if args.preview:
        selected = next((p for p in clips if probe(ffprobe, p) >= 1), None)
        if selected is None:
            raise RuntimeError("No usable preview clip")
        dest = out / "motion_preview.mp4"
        temp = out / "motion_preview.tmp.mp4"
        # Trim or gently slow source to target length, preserving moving frames.
        duration = probe(ffprobe, selected)
        factor = min(2.0, max(1.0, args.seconds / duration))
        filtergraph = ("setpts=%s*(PTS-STARTPTS),fps=24,"
                       "scale=1280:720:force_original_aspect_ratio=decrease,"
                       "pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p" % factor)
        command = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                   "-i", str(selected), "-vf", filtergraph, "-t", str(args.seconds),
                   "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", str(temp)]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError("Preview FFmpeg render failed")
        temp.replace(dest)
        report["preview"] = {"status": "created", "source_file": selected.name,
                             "duration_seconds": round(probe(ffprobe, dest), 3),
                             "method": "trim or max 2x slow-motion, no freeze padding"}
    (out / "inventory.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                        encoding="utf-8")
    print("P2 COMPLETE")
    print("Clips:", len(clips))
    print("Preview:", report["preview"]["status"] if isinstance(report["preview"], dict) else "not requested")
    print("All outputs remain local.")

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("P2 ERROR:", type(error).__name__, str(error), file=sys.stderr)
        sys.exit(1)
