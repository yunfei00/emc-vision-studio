import argparse
import json
import pathlib
import shutil
import subprocess
import sys

SCENES = [
    ("S001", "信号消失", "实验室里，一次异常悄然出现。"),
    ("S002", "定位异常", "手机定位开始漂移，问题并不简单。"),
    ("S003", "追踪线索", "工程师从频谱中寻找干扰来源。"),
    ("S004", "排查链路", "每一根线缆、每一个接口，都可能是关键。"),
    ("S005", "锁定原因", "通过逐项排查，逐渐逼近答案。"),
    ("S006", "恢复信号", "找到问题，才能让信号重新清晰。"),
]

def run(cmd, cwd=None):
    subprocess.run(cmd, check=True, cwd=cwd)

def probe(ffprobe, path):
    cmd = [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return float(result.stdout.strip())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/AI-Video")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--hold", type=float, default=0.6)
    args = parser.parse_args()
    root = pathlib.Path(args.root)
    source = root / "private" / "lost-signal" / "phase6"
    output = root / "private" / "lost-signal" / "phase7"
    output.mkdir(parents=True, exist_ok=True)
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("ffmpeg and ffprobe must be available in PATH")
    if args.fps <= 0 or args.hold < 0:
        raise ValueError("Invalid fps or hold")
    clips = []
    for scene, title, narration in SCENES:
        path = source / (scene + ".mp4")
        if not path.is_file():
            raise FileNotFoundError(str(path))
        duration = probe(ffprobe, path)
        if duration <= 0:
            raise RuntimeError("Invalid clip: " + str(path))
        clips.append((scene, title, narration, path, duration))
    # No auto-TTS or third-party service; silent stereo audio makes later local audio editing straightforward.
    normalized = []
    for scene, title, narration, path, duration in clips:
        target = output / (scene + "_edit.mp4")
        vf = "fps={fps},scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p".format(fps=args.fps)
        run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(path),
             "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
             "-filter:v", vf, "-t", str(duration + args.hold), "-shortest",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-r", str(args.fps),
             "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(target)])
        normalized.append(target)
    playlist = output / "clips.txt"
    playlist.write_text("".join("file '{}_edit.mp4'\n".format(scene) for scene, *_ in clips), encoding="utf-8")
    final = output / "lost_signal_phase7_story_cut.mp4"
    run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
         "-i", str(playlist), "-c", "copy", "-movflags", "+faststart", str(final)], cwd=str(output))
    # Export a local editorial script, not burned-in subtitles (avoids unreliable Windows fonts and timing assumptions).
    plan = [{"scene": scene, "title": title, "narration_draft": narration,
             "source": str(path), "source_seconds": round(duration, 3)}
            for scene, title, narration, path, duration in clips]
    (output / "edit_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    script = "# 《消失的信号》六镜头解说词草稿\n\n" + "\n\n".join(
        "## {} · {}\n{}".format(scene, title, narration) for scene, title, narration, *_ in clips
    ) + "\n"
    (output / "narration_draft.md").write_text(script, encoding="utf-8")
    print("PHASE 7 STORY CUT COMPLETE:", final)
    print("NARRATION DRAFT:", output / "narration_draft.md")
    print("NOTE: This is a short silent story cut; subtitles, voice-over and music are not yet embedded.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE 7 ERROR:", exc, file=sys.stderr)
        sys.exit(1)
