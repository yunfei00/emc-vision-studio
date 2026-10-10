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
    paths = sorted({p.resolve() for folder in ("phase6", "phase9")
                    for p in (base / folder).rglob("*.mp4") if p.is_file()})
    # Recognize scene labels anywhere in filename, e.g. shot_S01_take2.mp4.
    # If no labels exist, use a deterministic preview-only fallback.
    by_scene = {}
    for path in paths:
        m = re.search(r"(?<![A-Za-z0-9])S(0[1-9]|1[0-9])(?![0-9])", path.stem, re.I)
        if m and probe(ffprobe, path) >= 0.5:
            key = "S" + m.group(1)
            by_scene.setdefault(key, []).append(path)
    selected = []
    for i in range(1, args.max_shots + 1):
        key = "S%02d" % i
        candidates = by_scene.get(key, [])
        if not candidates:
            continue
        # Prefer longer usable motion, then deterministic path ordering.
        source = sorted(candidates, key=lambda p: (-probe(ffprobe, p), str(p)))[0]
        selected.append((key, source))
    fallback = not bool(selected)
    if fallback:
        usable = [(p, probe(ffprobe, p)) for p in paths]
        usable = [(p, d) for p, d in usable if d >= 0.5]
        if not usable:
            raise RuntimeError("No playable local MP4 clips found")
        selected = [("P%02d" % i, p) for i, (p, _) in enumerate(usable[:args.max_shots], 1)]
    manifest = {"status": "rendering", "requested_shots": args.max_shots,
                "found_shots": len(selected), "missing_scenes":
                ["S%02d" % i for i in range(1, args.max_shots + 1)
                 if "S%02d" % i not in {key for key, _ in selected}],
                "shots": [], "mapping_mode": "unlabelled_preview" if fallback else "scene_labels",
                "note": "Unlabelled preview order is NOT verified story order"}
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
