import argparse
import json
import pathlib
import shutil
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/AI-Video")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--fps", type=int, default=24)
    args = parser.parse_args()
    if args.fps <= 0:
        raise ValueError("fps must be positive")
    root, repo = pathlib.Path(args.root), pathlib.Path(args.repo)
    plan = json.loads((repo / "plans" / "phase8_lost_signal_storyboard.json").read_text(encoding="utf-8"))
    phase6 = root / "private" / "lost-signal" / "phase6"
    phase9 = root / "private" / "lost-signal" / "phase9"
    rough = phase9 / "rough_cut"
    rough.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg not found")
    shots = [shot for act in plan["acts"] for shot in act["shots"]]
    expected = sum(int(shot["seconds"]) for shot in shots)
    if expected != 103 or len(shots) != 19:
        raise RuntimeError("Unexpected storyboard duration or shot count")
    playlist = []
    for shot in shots:
        scene, seconds = shot["id"], int(shot["seconds"])
        source = (phase6 if int(scene[1:]) <= 6 else phase9) / (scene + ".mp4")
        if not source.is_file():
            raise FileNotFoundError("Missing AI video " + str(source))
        target = rough / (scene + "_rough.mp4")
        # Freeze last generated frame after the genuine SVD motion ends. This is a timing placeholder, not extra AI motion.
        vf = ("fps={fps},scale=1280:720:force_original_aspect_ratio=decrease,"
              "pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
              "tpad=stop_mode=clone:stop_duration={seconds},trim=duration={seconds},"
              "setpts=PTS-STARTPTS,format=yuv420p").format(fps=args.fps, seconds=seconds)
        cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
               "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
               "-vf", vf, "-t", str(seconds), "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "20", "-r", str(args.fps), "-c:a", "aac", "-b:a", "128k",
               "-shortest", str(target)]
        print("EDIT", scene, str(seconds) + "s", flush=True)
        subprocess.run(cmd, check=True)
        playlist.append(target)
    listfile = rough / "clips.txt"
    listfile.write_text("".join("file '{}_rough.mp4'\n".format(shot["id"]) for shot in shots), encoding="utf-8")
    final = rough / "lost_signal_103s_rough_cut.mp4"
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(listfile), "-c", "copy", "-movflags", "+faststart", str(final)],
                   cwd=str(rough), check=True)
    (rough / "rough_cut_manifest.json").write_text(json.dumps({
        "status": "complete", "planned_seconds": expected, "shots": shots,
        "motion_note": "Each shot begins with ~2.33s genuine SVD motion, then holds the last frame. Not 103s continuous AI motion.",
        "output": str(final)}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PHASE 9 ROUGH CUT COMPLETE:", final, flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE 9 ROUGH CUT ERROR:", exc, file=sys.stderr, flush=True)
        sys.exit(1)
