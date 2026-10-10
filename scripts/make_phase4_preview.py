import argparse
import json
import pathlib
import shutil
import subprocess
import sys

SCENES = ["S001", "S002", "S003", "S004", "S005", "S006"]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="D:/AI-Video")
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--seconds", type=float, default=4.0)
    args = p.parse_args()
    if args.fps < 1 or args.seconds <= 0:
        raise ValueError("fps and seconds must be positive")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found in PATH. Install FFmpeg locally and rerun; do not upload private media.")
    root = pathlib.Path(args.root)
    source = root / "ComfyUI" / "output"
    private = root / "private" / "lost-signal" / "phase4"
    private.mkdir(parents=True, exist_ok=True)
    images = []
    for scene in SCENES:
        matches = sorted(source.glob("lost_signal_phase3_" + scene + "_*.png"))
        if not matches:
            raise FileNotFoundError("Missing local keyframe for " + scene + " in " + str(source))
        images.append(matches[-1])
    clips = []
    frames = round(args.fps * args.seconds)
    for index, (scene, image) in enumerate(zip(SCENES, images)):
        clip = private / (scene + ".mp4")
        # Crop a gently moving 16:9 window from the source image. No external assets.
        vf = (
            "scale=1920:1080:force_original_aspect_ratio=increase,"
            "crop=1280:720:"
            "x='(in_w-out_w)/2+40*sin(n/60)':"
            "y='(in_h-out_h)/2+20*cos(n/60)',"
            "setsar=1,format=yuv420p"
        )
        cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
               "-loop", "1", "-framerate", str(args.fps), "-i", str(image),
               "-vf", vf, "-frames:v", str(frames),
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
               "-pix_fmt", "yuv420p", "-r", str(args.fps), str(clip)]
        print("Rendering:", scene, flush=True)
        subprocess.run(cmd, check=True)
        clips.append(clip)
    concat = private / "clips.txt"
    concat.write_text("".join("file '" + clip.name + "'\n" for clip in clips), encoding="utf-8")
    output = private / "lost_signal_phase4_preview.mp4"
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "concat", "-safe", "0", "-i", str(concat),
                    "-c", "copy", str(output)], cwd=str(private), check=True)
    manifest = {"status": "complete", "frames_per_scene": frames, "fps": args.fps,
                "seconds_per_scene": args.seconds, "output": str(output),
                "sources": [str(i) for i in images]}
    (private / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("COMPLETE:", output, flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR:", exc, file=sys.stderr)
        raise
