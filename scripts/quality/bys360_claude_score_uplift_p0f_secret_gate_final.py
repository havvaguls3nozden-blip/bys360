from __future__ import annotations

import argparse
import json
import py_compile
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P0F_SECRET_GATE_FINAL_V1"


def compile_file(path: Path) -> bool:
    try:
        py_compile.compile(str(path), doraise=True)
        return True
    except Exception as exc:
        print(f"COMPILE_ERROR {path}: {exc}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--mode", default="all")
    parser.add_argument("--run-gate", action="store_true")
    parser.add_argument("--compile-all", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    gate = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)

    compile_ok = compile_file(gate)
    if args.compile_all:
        # Hafif kontrol: kritik kalite scriptleri derlensin. Tüm app derlemesini ayrıca kullanıcının mevcut gate'leri yapıyor.
        for path in [root / "scripts" / "quality" / "bys360_claude_score_uplift_p0f_secret_gate_final.py"]:
            compile_ok = compile_file(path) and compile_ok

    gate_ok = None
    gate_finding_count = None
    gate_warning_count = None
    if args.run_gate:
        proc = subprocess.run([sys.executable, str(gate), "--root", str(root)], text=True, capture_output=True)
        if proc.stdout:
            print(proc.stdout.strip())
        if proc.stderr:
            print(proc.stderr.strip(), file=sys.stderr)
        report_path = root / "reports" / "quality" / "BYS360_SECRET_REPO_GATE_V1_REPORT.json"
        if report_path.exists():
            data = json.loads(report_path.read_text(encoding="utf-8"))
            gate_ok = bool(data.get("ok"))
            gate_finding_count = data.get("finding_count")
            gate_warning_count = data.get("warning_count")
        else:
            gate_ok = proc.returncode == 0

    ok = compile_ok and (gate_ok is not False)
    report = {
        "ok": ok,
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "mode": args.mode,
        "changed_count": 1,
        "changed": ["scripts/quality/bys360_secret_repo_gate.py"],
        "compile_ok": compile_ok,
        "gate_ok": gate_ok,
        "gate_finding_count": gate_finding_count,
        "gate_warning_count": gate_warning_count,
        "report": str(report_dir / f"{PACKAGE}_REPORT.json"),
    }
    (report_dir / f"{PACKAGE}_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
