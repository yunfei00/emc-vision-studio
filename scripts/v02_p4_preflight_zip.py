"""P4 offline preflight for the actual P3 ZIP layout; no network or uploads."""
import hashlib
import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path("D:/AI-Video/private/lost-signal/v0.2")
STORY = Path(__file__).resolve().parents[1] / "plans/phase8_lost_signal_storyboard.json"

def run(root=ROOT):
    root = Path(root)
    errors, warnings, rows = [], [], []
    story = json.loads(STORY.read_text(encoding="utf-8"))
    shots = [s for act in story["acts"] for s in act["shots"]]
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        errors.append("缺少根目录 manifest.json，请检查 ZIP 是否多解压了一层目录")
        data = {}
    else:
        data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    records = data.get("shots", [])
    if not isinstance(records, list):
        errors.append("manifest.shots 不是列表")
        records = []
    by_id = {r.get("shot"): r for r in records if isinstance(r, dict)}
    if len(by_id) != 19 or len(records) != 19:
        errors.append("manifest 镜头数量或编号重复")
    hashes = defaultdict(list)
    elapsed = 0
    for idx, s in enumerate(shots, 1):
        sid, duration = s["id"], s["seconds"]
        rec = by_id.get(sid, {})
        expected = f"{idx:03d}_{sid}_{elapsed:03d}s.png"
        name = rec.get("filename", "")
        path = root / "keyframes" / name
        if name != expected or rec.get("start_seconds") != elapsed or rec.get("duration_seconds") != duration:
            errors.append(f"{sid} 时间线或文件名不一致，预期 {expected}")
        row = {"shot": sid, "expected": expected, "exists": path.is_file()}
        if not path.is_file():
            errors.append(f"{sid} 图片缺失: {path}")
        else:
            blob = path.read_bytes()
            digest = hashlib.sha256(blob).hexdigest()
            hashes[digest].append(sid)
            row["sha256"] = digest
            if rec.get("sha256") and rec["sha256"] != digest:
                errors.append(f"{sid} SHA256 与 manifest 不一致")
            try:
                from PIL import Image
                with Image.open(path) as im:
                    im.verify()
                with Image.open(path) as im:
                    row["size"] = [im.width, im.height]
                    if abs(im.width / im.height - 16/9) > 0.04:
                        warnings.append(f"{sid} 图片不是接近 16:9")
            except ImportError:
                warnings.append("未安装 Pillow，跳过图片解码验证")
            except Exception as exc:
                errors.append(f"{sid} 图片解码失败: {exc}")
        rows.append(row)
        elapsed += duration
    if elapsed != 103 or data.get("total_seconds") != 103:
        errors.append("总时长不是 103 秒")
    for digest, ids in hashes.items():
        if len(ids) > 1:
            errors.append("重复图片内容: " + ", ".join(ids))
    chars = sorted(str(p.relative_to(root)) for p in (root / "characters").glob("*.png"))
    if len(chars) < 2:
        warnings.append("角色参考图少于两张")
    report = {"status": "FAIL" if errors else "PASS", "errors": errors, "warnings": sorted(set(warnings)), "characters": chars, "shots": rows}
    dest = root / "p4" / "reports" / "preflight.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("P4:", report["status"])
    print("图片:", sum(x["exists"] for x in rows), "/19; 角色图:", len(chars))
    for e in errors: print("错误:", e)
    for w in sorted(set(warnings)): print("提示:", w)
    print("报告:", dest)
    return 1 if errors else 0

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=str(ROOT))
    args = p.parse_args()
    raise SystemExit(run(args.root))
