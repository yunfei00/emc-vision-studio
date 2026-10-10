import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import wave

def stamp(seconds):
    milliseconds = int(round(seconds * 1000))
    hours, rest = divmod(milliseconds, 3600000)
    minutes, rest = divmod(rest, 60000)
    sec, ms = divmod(rest, 1000)
    return "%02d:%02d:%02d,%03d" % (hours, minutes, sec, ms)

def ffmpeg_run(args):
    subprocess.run(args, check=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/AI-Video")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--voice", default="")
    parser.add_argument("--music", default="")
    parser.add_argument("--burn-subtitles", action="store_true")
    args = parser.parse_args()
    root, repo = pathlib.Path(args.root), pathlib.Path(args.repo)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not in PATH")
    plan = json.loads((repo / "plans" / "phase8_lost_signal_storyboard.json").read_text(encoding="utf-8"))
    script = json.loads((repo / "plans" / "phase10_narration_zh.json").read_text(encoding="utf-8"))["narration"]
    source = root / "private" / "lost-signal" / "phase9" / "rough_cut" / "lost_signal_103s_rough_cut.mp4"
    if not source.is_file():
        raise FileNotFoundError(str(source))
    output = root / "private" / "lost-signal" / "phase10"
    output.mkdir(parents=True, exist_ok=True)
    subtitle = output / "lost_signal_zh.srt"
    cues = []
    cursor = 0
    for act in plan["acts"]:
        for shot in act["shots"]:
            scene = shot["id"]
            seconds = int(shot["seconds"])
            if scene not in script:
                raise KeyError("Missing narration for " + scene)
            cues.append((cursor, cursor + seconds, script[scene]))
            cursor += seconds
    if cursor != 103:
        raise RuntimeError("Unexpected timeline duration: " + str(cursor))
    subtitle.write_text("".join("%d\n%s --> %s\n%s\n\n" % (i, stamp(start), stamp(end), line)
                                for i, (start, end, line) in enumerate(cues, 1)), encoding="utf-8-sig")
    (output / "narration_zh.txt").write_text("\n".join("%s %s" % (stamp(start), line) for start, _, line in cues) + "\n", encoding="utf-8")
    # User-provided local audio is optional; no network TTS or upload.
    voice = pathlib.Path(args.voice) if args.voice else None
    music = pathlib.Path(args.music) if args.music else None
    for item in (voice, music):
        if item and not item.is_file():
            raise FileNotFoundError(str(item))
    if not voice and not music:
        print("No local audio provided: retain the original silent audio track.", flush=True)
    target = output / "lost_signal_phase10.mp4"
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source)]
    if voice:
        cmd += ["-i", str(voice)]
    if music:
        cmd += ["-i", str(music)]
    if voice and music:
        cmd += ["-filter_complex", "[1:a]volume=1.0,apad,atrim=duration=103[v];[2:a]volume=0.16,apad,atrim=duration=103[m];[v][m]amix=inputs=2:duration=longest:normalize=0[a]",
                "-map", "0:v:0", "-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    elif voice or music:
        input_idx = 1
        volume = "1.0" if voice else "0.16"
        cmd += ["-filter_complex", "[%d:a]volume=%s,apad,atrim=duration=103[a]" % (input_idx, volume),
                "-map", "0:v:0", "-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-map", "0:v:0", "-map", "0:a:0?", "-c:a", "copy"]
    # Prefer a soft subtitle stream to avoid Windows drawtext/font dependencies.
    if args.burn_subtitles:
        print("Burn-in requested, but not supported in this baseline; using selectable SRT track instead.", flush=True)
    cmd += ["-i", str(subtitle), "-map", str(2 if voice and music else 1 if voice or music else 1) + ":s:0",
            "-c:s", "mov_text", "-c:v", "copy", "-t", "103", "-movflags", "+faststart", str(target)]
    ffmpeg_run(cmd)
    (output / "manifest.json").write_text(json.dumps({
        "status": "complete", "duration_seconds": 103, "subtitles": str(subtitle),
        "video": str(target), "voice_included": bool(voice), "music_included": bool(music),
        "subtitle_mode": "selectable_mov_text_not_burned_in"}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PHASE 10 EXPORT COMPLETE:", target, flush=True)
    print("SUBTITLE FILE:", subtitle, flush=True)
    print("VOICE INCLUDED:", bool(voice), "MUSIC INCLUDED:", bool(music), flush=True)
    print("SUBTITLES: selectable track, enable in player", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE 10 ERROR:", exc, file=sys.stderr, flush=True)
        sys.exit(1)
