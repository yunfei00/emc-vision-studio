"""Validate P4 local keyframes without uploading private files."""
import argparse
import hashlib
import json
from pathlib import Path

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/AI-Video/private/lost-signal/v0.2")
    parser.add_argument("--manifest")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    storyboard = json.loads((Path(__file__).resolve().parents[1] / "plans/phase8_lost_signal_storyboard.json").read_text(encoding="utf-8"))
    shots = [s for act in storyboard["acts"] for s in act["shots"]]
    errors = []
    if len(shots) != 19 or len({s["id"] for s in shots}) != 19 or sum(s["seconds"] for s in shots) != 103:
        errors.append("Storyboard count/order/duration invalid")
    manifests = [Path(args.manifest)] if args.manifest else list(root.rglob("manifest.json"))
    if len(manifests) != 1:
        raise SystemExit("Expected one manifest.json; found " + str(manifests))
    data = json.loads(manifests[0].read_text(encoding="utf-8-sig"))
    mapping = next((data[k] for k in ("shots", "keyframes", "images") if isinstance(data, dict) and k in data), data)
    if isinstance(mapping, list):
        mapping = {str(v.get("id", v.get("scene", ""))): v for v in mapping if isinstance(v, dict)}
    if not isinstance(mapping, dict):
        raise SystemExit("Unsupported manifest mapping")
    if set(mapping) != {s["id"] for s in shots}:
        errors.append("Missing or extra scene mappings")
    seen = {}
    rows = []
    for shot in shots:
        sid = shot["id"]
        value = mapping.get(sid)
        if isinstance(value, dict):
            value = next((value[k] for k in ("file", "path", "image", "keyframe", "filename", "source") if isinstance(value.get(k), str)), None)
        row = {"scene": sid, "file": value}
        if not isinstance(value, str):
            errors.append(sid + " missing/unrecognized file field")
        else:
            relative = Path(value)
            path = (root / relative).resolve()
            if relative.is_absolute() or not path.is_relative_to(root):
                errors.append(sid + " unsafe path")
            elif not path.is_file():
                errors.append(sid + " missing image")
            else:
                try:
                    from PIL import Image
                    with Image.open(path) as image:
                        image.verify()
                    with Image.open(path) as image:
                        row["resolution"] = [image.width, image.height]
                except Exception as exc:
                    errors.append(sid + " invalid image: " + str(exc))
                row["sha256"] = digest(path)
                if row["sha256"] in seen:
                    errors.append("Duplicate content: " + seen[row["sha256"]] + " / " + sid)
                seen[row["sha256"]] = sid
        rows.append(row)
    a, b = (next((r for r in rows if r["scene"] == sid), {}) for sid in ("S009", "S018"))
    if a.get("sha256") and a.get("sha256") == b.get("sha256"):
        errors.append("S009 and S018 identical")
    refs = [str(p.relative_to(root)) for p in root.rglob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp") and any(t in str(p).lower() for t in ("reference", "character"))]
    report = {"status": "FAIL" if errors else "PASS_MAPPING_ONLY", "errors": errors, "shots": rows, "reference_candidates": refs, "storyboard_order": [s["id"] for s in shots], "note": "Reference count, visual duplicates and character consistency require visual review."}
    output = root / "p4" / "reports" / "asset_acceptance.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "errors": errors, "reference_candidates": refs, "report": str(output)}, ensure_ascii=False, indent=2))
    raise SystemExit(2 if errors else 0)

if __name__ == "__main__":
    main()
