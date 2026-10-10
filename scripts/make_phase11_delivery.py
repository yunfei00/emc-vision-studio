import argparse
import json
import pathlib
import shutil
import subprocess
import sys
from datetime import datetime

def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)

def probe(ffprobe, path):
    result = run([ffprobe, "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height", "-of", "json", str(path)], capture_output=True, text=True)
    return json.loads(result.stdout)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="D:/AI-Video")
    args = p.parse_args()
    root = pathlib.Path(args.root)
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("FFmpeg and FFprobe must be on PATH")
    source = root / "private" / "lost-signal" / "phase10" / "lost_signal_phase10_voiced.mp4"
    if not source.is_file():
        raise FileNotFoundError("Missing Phase 10 voiced video: " + str(source))
    destination = root / "private" / "lost-signal" / "delivery"
    destination.mkdir(parents=True, exist_ok=True)
    full = destination / "lost_signal_full_103s.mp4"
    short = destination / "lost_signal_short_30s.mp4"
    report_path = destination / "quality_report.json"
    details = probe(ffprobe, source)
    duration = float(details["format"]["duration"])
    types = [stream.get("codec_type") for stream in details.get("streams", [])]
    if "video" not in types or "audio" not in types:
        raise RuntimeError("Full version requires both video and audio streams")
    if not 100 <= duration <= 106:
        raise RuntimeError("Full version duration out of expected 103s range: " + str(duration))
    shutil.copy2(source, full)
    # A 30s story digest made from 6 non-contiguous 5-second excerpts, including original burned-in subtitles and audio.
    # Since original subtitles are burned into the picture, selected shots may show text from the original timeline.
    segments = [(0, 5), (10, 5), (31, 5), (57, 5), (78, 5), (98, 5)]
    filters = []
    for i, (start, length) in enumerate(segments):
        filters.append("[0:v]trim=start=%s:duration=%s,setpts=PTS-STARTPTS[v%d]" % (start, length, i))
        filters.append("[0:a]atrim=start=%s:duration=%s,asetpts=PTS-STARTPTS[a%d]" % (start, length, i))
    joined = "".join("[v%d][a%d]" % (i, i) for i in range(len(segments)))
    filters.append(joined + "concat=n=%d:v=1:a=1[v][a]" % len(segments))
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
           "-filter_complex", ";".join(filters), "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(short)]
    run(cmd)
    short_details = probe(ffprobe, short)
    short_duration = float(short_details["format"]["duration"])
    if not 29 <= short_duration <= 31:
        raise RuntimeError("Short version duration unexpected: " + str(short_duration))
    report = {
        "project": "lost-signal",
        "status": "technical_delivery_generated",
        "created_at_local": datetime.now().isoformat(timespec="seconds"),
        "full": {"file": full.name, "duration_seconds": duration, "streams": details["streams"]},
        "short": {"file": short.name, "duration_seconds": short_duration, "streams": short_details["streams"]},
        "validation": {"full_duration_ok": True, "full_has_video_and_audio": True, "short_duration_ok": True},
        "limitations": [
            "SVD clips provide about 2.33 seconds of AI motion per shot; later portions are freeze-frame holds.",
            "Voice is Windows offline SAPI and may sound mechanical.",
            "Background audio is a simple synthesized drone, not a polished musical score.",
            "Short cut reuses burned-in full-length subtitles, which may not read like a new 30-second script.",
            "Automatic checks cannot assess character identity, visual realism, or audio aesthetics."
        ],
        "privacy": "All video and audio files stay on this local computer."
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    readme = destination / "README_交付说明.txt"
    readme.write_text("消失的信号｜本地交付\n\n完整版：lost_signal_full_103s.mp4\n精简版：lost_signal_short_30s.mp4\n质量报告：quality_report.json\n\n技术验证完成不代表视觉与声音质量已达到正式发布标准。\n所有素材仅保留本地，不要上传公共 GitHub。\n", encoding="utf-8")
    print("PHASE 11 DELIVERY COMPLETE:", destination, flush=True)
    print("FULL:", full, flush=True)
    print("SHORT:", short, flush=True)
    print("REPORT:", report_path, flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE 11 ERROR:", exc, file=sys.stderr, flush=True)
        sys.exit(1)
