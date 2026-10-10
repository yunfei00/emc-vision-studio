import argparse
import json
import math
import pathlib
import shutil
import struct
import subprocess
import sys
import wave

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="D:/AI-Video")
    p.add_argument("--repo", required=True)
    p.add_argument("--mode", choices=["prepare", "mix"], required=True)
    args = p.parse_args()
    root, repo = pathlib.Path(args.root), pathlib.Path(args.repo)
    out = root / "private" / "lost-signal" / "phase10" / "audio"
    out.mkdir(parents=True, exist_ok=True)
    plan = json.loads((repo / "plans" / "phase8_lost_signal_storyboard.json").read_text(encoding="utf-8"))
    words = json.loads((repo / "plans" / "phase10_narration_zh.json").read_text(encoding="utf-8"))["narration"]
    cursor = 0
    items = []
    for act in plan["acts"]:
        for shot in act["shots"]:
            scene, duration = shot["id"], int(shot["seconds"])
            items.append({"id": scene, "start": cursor, "duration": duration, "text": words[scene]})
            cursor += duration
    if cursor != 103:
        raise RuntimeError("Unexpected timeline")
    (out / "timeline.json").write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8-sig")
    if args.mode == "prepare":
        print("Prepared local narration timeline with", len(items), "shots")
        return
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("ffmpeg and ffprobe must be on PATH")
    parts = []
    for item in items:
        source = out / (item["id"] + ".wav")
        if not source.is_file():
            raise FileNotFoundError("Missing voice: " + str(source))
        result = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(source)], capture_output=True, text=True, check=True)
        length = float(result.stdout.strip())
        if length > item["duration"] - 0.25:
            print("WARNING: narration may overrun its shot:", item["id"], "length:", round(length, 2), flush=True)
        # Each cue is bounded to its shot. Avoid narration spilling into the next shot.
        target = out / (item["id"] + "_timed.wav")
        subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
                        "-af", "apad,atrim=duration=%s,asetpts=PTS-STARTPTS" % item["duration"],
                        "-ar", "48000", "-ac", "2", str(target)], check=True)
        parts.append(target)
    playlist = out / "voice_clips.txt"
    playlist.write_text("".join("file '%s'\n" % part.name for part in parts), encoding="utf-8")
    voice = out / "voice_103s.wav"
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(playlist), "-ar", "48000", "-ac", "2", str(voice)], cwd=str(out), check=True)
    # Deterministic, low-level ambient drone made entirely locally, not licensed third-party music.
    music = out / "ambient_103s.wav"
    sr = 16000
    with wave.open(str(music), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        for sec in range(103):
            data = bytearray()
            for n in range(sr):
                t = sec + n / sr
                fade = min(1.0, t / 3, (103 - t) / 4)
                envelope = max(0.0, fade)
                # Ambient tonal bed, not a commercial track.
                sample = envelope * (0.38 * math.sin(2 * math.pi * 110 * t) + 0.26 * math.sin(2 * math.pi * 164.81 * t) + 0.13 * math.sin(2 * math.pi * 220 * t))
                data.extend(struct.pack("<h", int(max(-1, min(1, sample)) * 4000)))
            w.writeframes(data)
    export = root / "private" / "lost-signal" / "phase10" / "lost_signal_phase10.mp4"
    source_video = root / "private" / "lost-signal" / "phase9" / "rough_cut" / "lost_signal_103s_rough_cut.mp4"
    subtitle = root / "private" / "lost-signal" / "phase10" / "lost_signal_zh.srt"
    if not source_video.is_file() or not subtitle.is_file():
        raise FileNotFoundError("Phase 9 video or Phase 10 subtitles missing")
    final = root / "private" / "lost-signal" / "phase10" / "lost_signal_phase10_voiced.mp4"
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(export), "-i", str(voice), "-i", str(music),
           "-filter_complex", "[1:a]volume=1.0,atrim=duration=103[v];[2:a]volume=0.14,atrim=duration=103[m];[v][m]amix=inputs=2:duration=longest:normalize=0[a]",
           "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", "103", "-movflags", "+faststart", str(final)]
    subprocess.run(cmd, check=True)
    print("OFFLINE VOICED VIDEO:", final, flush=True)
    print("Original subtitle video remains unchanged:", export, flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE 10 AUDIO ERROR:", exc, file=sys.stderr, flush=True)
        sys.exit(1)
