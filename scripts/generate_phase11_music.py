"""Create an original, deterministic offline score and mix with existing Chinese narration."""
import argparse
import json
import math
import pathlib
import shutil
import struct
import subprocess
import sys
import wave

DURATION = 103
SAMPLE_RATE = 16000
BPM = 92
BEAT = 60.0 / BPM
NOTES = {"C": 261.63, "D": 293.66, "Eb": 311.13, "F": 349.23, "G": 392.0, "Ab": 415.30, "Bb": 466.16}
CHORDS = [
    (0, 26, [130.81, 155.56, 196.00], ["C", "Eb", "G", "Eb"], 0.46),
    (26, 53, [116.54, 146.83, 174.61], ["D", "F", "Ab", "F"], 0.68),
    (53, 80, [103.83, 155.56, 174.61], ["Eb", "G", "Bb", "G"], 0.95),
    (80, 103, [130.81, 164.81, 196.00], ["G", "Eb", "C", "G"], 0.54),
]

def score(t):
    for start, end, chord, melody, energy in CHORDS:
        if start <= t < end:
            break
    local = t - start
    beat_pos = local / BEAT
    step = int(beat_pos)
    phase = beat_pos - step
    # Slow harmonic pads with a breathing envelope.
    pad = sum(math.sin(2 * math.pi * hz * t + math.sin(t * 0.37) * 0.11) for hz in chord) / 3
    pad *= 0.29 * (0.78 + 0.22 * math.sin(t * 0.42))
    # A sparse bell-like melodic line, with audible decay and rests.
    note = NOTES[melody[(step // 2) % len(melody)]]
    envelope = math.exp(-5.0 * ((beat_pos / 2) % 1.0)) if step % 2 == 0 or phase > 0 else 0
    bell = (math.sin(2 * math.pi * note * t) + 0.28 * math.sin(2 * math.pi * note * 2.01 * t)) * 0.20 * envelope
    # Rounded electronic kick and quiet ticking pulse, growing during investigation.
    pulse_env = math.exp(-17 * phase)
    kick = math.sin(2 * math.pi * (62 + 38 * math.exp(-18 * phase)) * t) * pulse_env * (0.13 if start >= 26 else 0.04)
    tick = math.sin(2 * math.pi * 980 * t) * math.exp(-46 * phase) * (0.022 if start >= 26 else 0.006)
    fade = min(1.0, max(0.0, t / 3.0), max(0.0, (DURATION - t) / 5.0))
    # Smooth section transitions to avoid abrupt clicks.
    edge = min(local, end - t)
    boundary = 0.78 + 0.22 * min(1.0, max(0.0, edge / 0.7))
    return (pad + bell + kick + tick) * energy * fade * boundary

def create_music(path):
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        for second in range(DURATION):
            chunk = bytearray()
            for i in range(SAMPLE_RATE):
                t = second + i / SAMPLE_RATE
                value = max(-0.95, min(0.95, score(t)))
                chunk.extend(struct.pack("<h", int(value * 18000)))
            output.writeframes(chunk)

def probe(ffprobe, path):
    result = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], capture_output=True, text=True, check=True)
    return float(result.stdout.strip())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/AI-Video")
    args = parser.parse_args()
    root = pathlib.Path(args.root)
    base = root / "private" / "lost-signal" / "phase10"
    audio = base / "audio"
    audio.mkdir(parents=True, exist_ok=True)
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("ffmpeg/ffprobe not found")
    source = base / "lost_signal_phase10.mp4"
    voice = audio / "voice_103s.wav"
    if not source.is_file() or not voice.is_file():
        raise FileNotFoundError("Existing burned-subtitle video or voice_103s.wav missing. Complete Phase 10 first.")
    video_duration = probe(ffprobe, source)
    voice_duration = probe(ffprobe, voice)
    if video_duration < 1 or voice_duration < 1:
        raise RuntimeError("Video or voice is empty")
    print("Input durations: video=%.3fs, voice=%.3fs; normalizing audio to 103s" % (video_duration, voice_duration), flush=True)
    if video_duration < DURATION - 1:
        print("WARNING: video is shorter than 103s; extending final frame locally", flush=True)
    music = audio / "original_score_103s.wav"
    print("Generating original 103-second score locally...", flush=True)
    create_music(music)
    target = base / "lost_signal_phase10_voiced.mp4"
    tmp = base / "lost_signal_phase10_voiced_new.tmp.mp4"
    # Compress voice slightly and duck the music during spoken segments.
    filters = ("[1:a]aresample=48000,apad,atrim=duration=103,asetpts=PTS-STARTPTS,acompressor=threshold=0.08:ratio=2.5:attack=15:release=180,"
               "volume=1.2,alimiter=limit=0.90,asplit=2[v][side];"
               "[2:a]aresample=48000,apad,atrim=duration=103,asetpts=PTS-STARTPTS,volume=0.38[m];"
               "[m][side]sidechaincompress=threshold=0.018:ratio=7:attack=45:release=350[duck];"
               "[v][duck]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.92[a]")
    video_input = ["-i", str(source)] if video_duration >= DURATION - 0.1 else ["-i", str(source)]
    video_filters = ["-vf", "tpad=stop_mode=clone:stop_duration=103,trim=duration=103", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20"] if video_duration < DURATION - 0.1 else ["-c:v", "copy"]
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                    *video_input, "-i", str(voice), "-i", str(music),
                    "-filter_complex", filters, "-map", "0:v:0", "-map", "[a]",
                    *video_filters, "-c:a", "aac", "-b:a", "192k", "-t", "103",
                    "-movflags", "+faststart", str(tmp)], check=True)
    if not 100 <= probe(ffprobe, tmp) <= 106:
        raise RuntimeError("New video duration invalid; old version kept")
    tmp.replace(target)
    (audio / "score_manifest.json").write_text(json.dumps({
        "style": "original offline cinematic electronic score",
        "seconds": DURATION, "bpm": BPM, "sections": [0, 26, 53, 80, 103],
        "music_file": str(music), "video_file": str(target),
        "voice_ducking": True, "generated_locally": True,
        "note": "Programmatic synthesizer music; not an AI-composed studio recording."
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("MUSIC:", music, flush=True)
    print("VIDEO:", target, flush=True)
    print("Re-run Phase 11 delivery to refresh full and short exports.", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("OFFLINE SCORE ERROR:", exc, file=sys.stderr, flush=True)
        sys.exit(1)
