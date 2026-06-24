from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P0B_SECRET_GATE_PRECISION_V1"


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--mode", default="all", choices=["audit", "all"])
    parser.add_argument("--run-gate", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    source_gate = Path(__file__).resolve().parent / "bys360_secret_repo_gate.py"
    target_gate = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)

    changed = []
    if args.mode == "all":
        target_gate.parent.mkdir(parents=True, exist_ok=True)
        existing = target_gate.read_text(encoding="utf-8", errors="ignore") if target_gate.exists() else ""
        new_content = source_gate.read_text(encoding="utf-8")
        if existing != new_content:
            backup_dir = report_dir / "gate_precision_backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            if target_gate.exists():
                backup_name = f"bys360_secret_repo_gate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                shutil.copy2(target_gate, backup_dir / backup_name)
            target_gate.write_text(new_content, encoding="utf-8")
            changed.append(str(target_gate.relative_to(root)))

    gate_result = None
    if args.run_gate:
        completed = subprocess.run(
            [sys.executable, str(target_gate), "--root", str(root)],
            cwd=str(root),
            text=True,
            capture_output=True,
        )
        sys.stdout.write(completed.stdout)
        if completed.stderr:
            sys.stderr.write(completed.stderr)
        gate_result = {"returncode": completed.returncode, "ok": completed.returncode == 0}

    report = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "mode": args.mode,
        "changed": changed,
        "changed_count": len(changed),
        "gate_result": gate_result,
        "ok": (gate_result or {"ok": True}).get("ok", True),
        "notes": [
            "Bu paket secret gate'i .venv, reports, backups, quarantine, releases gibi üretilmiş/yerel klasörleri taramayacak şekilde hassaslaştırır.",
            "Environment variable referansı ve placeholder ifadeleri gerçek secret sayılmaz; gerçek token/parola biçimleri yine hata üretir.",
        ],
    }
    report_path = report_dir / f"{PACKAGE}_REPORT.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "package": PACKAGE, "changed_count": len(changed), "report": str(report_path)}, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
