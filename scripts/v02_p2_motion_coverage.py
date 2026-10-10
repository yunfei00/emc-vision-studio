"""Analyze actual source-motion coverage against the 103-second storyboard.

All inputs and outputs stay on the local machine. This script does not render media.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


def duration(ffprobe, path):
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    value = float(result.stdout.strip())
    if value <= 0:
        raise ValueError("Nonpositive clip duration")
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/AI-Video")
    args = parser.parse_args()
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe not on PATH")
    base = Path(args.root) / "private" / "lost-signal"
    plan_path = Path(__file__).resolve().parents[1] / "plans" / "phase8_lost_signal_storyboard.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    shots = [shot for act in plan["acts"] for shot in act["shots"]]
    if len(shots) != 19 or sum(int(s["seconds"]) for s in shots) != 103:
        raise RuntimeError("Unexpected storyboard")
    report = {"version": "v0.2-P2", "planned_seconds": 103, "shots": []}
    missing = []
    source_total = 0.0
    covered_total = 0.0
    for shot in shots:
        scene = shot["id"]
        seconds = int(shot["seconds"])
        source = base / ("phase6" if int(scene[1:]) <= 6 else "phase9") / (scene + ".mp4")
        if not source.is_file():
            missing.append(scene)
            continue
        actual = duration(ffprobe, source)
        covered = min(actual, seconds)
        source_total += actual
        covered_total += covered
        report["shots"].append({
            "scene": scene, "target_seconds": seconds,
            "source_seconds": round(actual, 3),
            "source_coverage_seconds": round(covered, 3),
            "uncovered_seconds": round(seconds - covered, 3),
            "coverage_percent": round(100 * covered / seconds, 1),
        })
    report["missing_scenes"] = missing
    report["source_total_seconds"] = round(source_total, 3)
    report["timeline_source_coverage_seconds"] = round(covered_total, 3)
    report["timeline_uncovered_seconds"] = round(103 - covered_total, 3)
    report["timeline_source_coverage_percent"] = round(100 * covered_total / 103, 1)
    report["interpretation"] = (
        "Duration-based upper bound on original source footage coverage; "
        "not measured optical motion or proof of non-static frames."
    )
    out = base / "v0.2" / "p2" / "motion_coverage.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("P2 COVERAGE COMPLETE")
    print("Shots:", len(report["shots"]), "/ 19")
    print("Missing:", len(missing))
    print("Original source seconds:", report["source_total_seconds"])
    print("Timeline source coverage:", report["timeline_source_coverage_seconds"], "/ 103")
    print("Uncovered seconds:", report["timeline_uncovered_seconds"])
    print("Coverage percent:", report["timeline_source_coverage_percent"])
    print("All outputs remain local.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("P2 COVERAGE ERROR:", type(error).__name__, str(error), file=sys.stderr)
        sys.exit(1)
