"""Prepare a local shot-by-shot motion extension plan without generating media."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/AI-Video")
    args = parser.parse_args()
    folder = Path(args.root) / "private" / "lost-signal" / "v0.2" / "p2"
    report_path = folder / "motion_coverage.json"
    if not report_path.is_file():
        raise FileNotFoundError("Run v02_p2_motion_coverage.py first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    shots = report.get("shots", [])
    if len(shots) != 19 or report.get("missing_scenes"):
        raise RuntimeError("Expected all 19 original shots before planning")
    entries = []
    for shot in shots:
        gap = max(0.0, float(shot["uncovered_seconds"]))
        entries.append({
            "scene": shot["scene"],
            "target_seconds": shot["target_seconds"],
            "source_seconds": shot["source_seconds"],
            "gap_seconds": round(gap, 3),
            "recommended_action": "generate_continuation" if gap >= 1 else "review",
            "priority": "high" if gap >= 3 else ("medium" if gap >= 1 else "low"),
            "status": "not_started",
        })
    result = {
        "version": "v0.2-P2-extension-plan",
        "policy": "Plan only. No freeze frames, synthetic motion claims, or GPU execution.",
        "source_coverage_seconds": report["timeline_source_coverage_seconds"],
        "uncovered_seconds": report["timeline_uncovered_seconds"],
        "shots_story_order": entries,
        "priority_order": sorted(entries, key=lambda item: (-item["gap_seconds"], item["scene"])),
    }
    output = folder / "motion_extension_plan.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("P2 EXTENSION PLAN COMPLETE")
    print("Shots:", len(entries))
    print("Uncovered seconds:", result["uncovered_seconds"])
    print("High priority:", sum(item["priority"] == "high" for item in entries))
    print("Medium priority:", sum(item["priority"] == "medium" for item in entries))
    print("All outputs remain local.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("P2 EXTENSION PLAN ERROR:", type(error).__name__, str(error), file=sys.stderr)
        sys.exit(1)
