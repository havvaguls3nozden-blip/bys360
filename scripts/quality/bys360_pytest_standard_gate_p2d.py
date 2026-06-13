from __future__ import annotations

import argparse
import json
import os
import py_compile
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_CLAUDE_SCORE_UPLIFT_P2D_PYTEST_STANDARD_GATE"
REPORT_REL = Path("reports/architecture/BYS360_PYTEST_STANDARD_GATE_P2D_REPORT.json")

DEV_REQUIREMENTS = [
    "pytest>=8,<9",
]

PYTEST_INI_TEXT = """[pytest]\ntestpaths = tests\npython_files = test_*.py\naddopts = -q\n"""

P2D_TEST_TEXT = """from __future__ import annotations\n\nfrom pathlib import Path\n\n\ndef test_pytest_standard_files_exist():\n    root = Path(__file__).resolve().parents[2]\n    assert (root / \"requirements-dev.txt\").exists()\n    assert (root / \"scripts\" / \"quality\" / \"bys360_pytest_standard_gate_p2d.py\").exists()\n\n\ndef test_mobile_architecture_tests_exist():\n    root = Path(__file__).resolve().parents[2]\n    expected = [\n        \"tests/architecture/test_mobile_api_contract_p2a.py\",\n        \"tests/architecture/test_mobile_api_behavior_smoke_p2b.py\",\n        \"tests/architecture/test_mobile_api_request_level_smoke_p2c_v3.py\",\n    ]\n    missing = [item for item in expected if not (root / item).exists()]\n    assert missing == []\n"""


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def append_unique_lines(path: Path, lines: list[str]) -> dict[str, Any]:
    before = ""
    if path.exists():
        before = read_text(path)
    existing = {ln.strip().lower() for ln in before.splitlines() if ln.strip() and not ln.strip().startswith("#")}
    added: list[str] = []
    out = before.rstrip()
    for line in lines:
        normalized_name = re.split(r"[<>=!~ ]", line.strip(), 1)[0].lower()
        has_same_pkg = any(re.split(r"[<>=!~ ]", item, 1)[0].lower() == normalized_name for item in existing)
        if not has_same_pkg:
            added.append(line)
            out = (out + "\n" if out else "") + line
            existing.add(line.lower())
    if added or not path.exists():
        write_text(path, out.rstrip() + "\n")
    return {"path": str(path), "changed": bool(added or not before), "added": added}


def ensure_pytest_ini(root: Path) -> dict[str, Any]:
    path = root / "pytest.ini"
    if path.exists():
        return {"path": str(path), "changed": False, "reason": "already_exists"}
    write_text(path, PYTEST_INI_TEXT)
    return {"path": str(path), "changed": True, "reason": "created"}


def ensure_tests(root: Path) -> dict[str, Any]:
    path = root / "tests/architecture/test_pytest_standard_p2d.py"
    before = read_text(path) if path.exists() else ""
    if before == P2D_TEST_TEXT:
        return {"path": str(path), "changed": False}
    write_text(path, P2D_TEST_TEXT)
    return {"path": str(path), "changed": True}


def compile_files(root: Path) -> dict[str, Any]:
    rels = [
        "scripts/quality/bys360_pytest_standard_gate_p2d.py",
        "tests/architecture/test_pytest_standard_p2d.py",
        "tests/architecture/test_mobile_api_contract_p2a.py",
        "tests/architecture/test_mobile_api_behavior_smoke_p2b.py",
        "tests/architecture/test_mobile_api_request_level_smoke_p2c_v3.py",
    ]
    results = []
    ok = True
    for rel in rels:
        path = root / rel
        if not path.exists():
            results.append({"file": str(path), "ok": False, "error": "missing"})
            ok = False
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            results.append({"file": str(path), "ok": True, "error": ""})
        except Exception as exc:
            results.append({"file": str(path), "ok": False, "error": repr(exc)})
            ok = False
    return {"ok": ok, "results": results}


def run_cmd(cmd: list[str], cwd: Path, env: dict[str, str] | None = None, timeout: int = 120) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), env=env, text=True, capture_output=True, timeout=timeout)
        return {
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
            "ok": proc.returncode == 0,
            "cmd": cmd,
        }
    except Exception as exc:
        return {"returncode": -1, "stdout_tail": "", "stderr_tail": repr(exc), "ok": False, "cmd": cmd}


def module_available(module: str, root: Path) -> bool:
    proc = subprocess.run([sys.executable, "-c", f"import {module}; print('OK')"], cwd=str(root), text=True, capture_output=True)
    return proc.returncode == 0


def install_pytest(root: Path) -> dict[str, Any]:
    cmd = [sys.executable, "-m", "pip", "install", "pytest>=8,<9"]
    return run_cmd(cmd, cwd=root, timeout=300)


def run_app_factory(root: Path) -> dict[str, Any]:
    code = "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"
    env = os.environ.copy()
    env.setdefault("APP_ENV", "development")
    env.setdefault("SECRET_KEY", "bys360-local-smoke-only")
    env.setdefault("DATABASE_URL", "sqlite:///:memory:")
    env.setdefault("SENTRY_DSN", "")
    res = run_cmd([sys.executable, "-c", code], cwd=root, env=env, timeout=120)
    res["ok"] = res.get("returncode") == 0 and "APP_FACTORY_OK" in res.get("stdout_tail", "")
    return res


def run_secret_gate(root: Path) -> dict[str, Any]:
    gate = root / "scripts/quality/bys360_secret_repo_gate.py"
    if not gate.exists():
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": "secret gate script missing", "parsed": {}}
    candidates = [
        [sys.executable, str(gate), "--root", str(root)],
        [sys.executable, str(gate), str(root)],
        [sys.executable, str(gate)],
    ]
    last = None
    for cmd in candidates:
        res = run_cmd(cmd, cwd=root, timeout=180)
        last = res
        text = (res.get("stdout_tail") or "").strip()
        parsed: dict[str, Any] = {}
        if text:
            start = text.rfind("{")
            if start >= 0:
                try:
                    parsed = json.loads(text[start:])
                except Exception:
                    parsed = {}
        res["parsed"] = parsed
        if parsed.get("ok") is True and int(parsed.get("finding_count", 999)) == 0:
            res["ok"] = True
            return res
    assert last is not None
    last["ok"] = False
    return last


def run_pytest(root: Path) -> dict[str, Any]:
    tests = [
        "tests/architecture/test_pytest_standard_p2d.py",
        "tests/architecture/test_mobile_api_contract_p2a.py",
        "tests/architecture/test_mobile_api_behavior_smoke_p2b.py",
        "tests/architecture/test_mobile_api_request_level_smoke_p2c_v3.py",
    ]
    existing = [t for t in tests if (root / t).exists()]
    if not existing:
        return {"ok": False, "mode": "pytest", "returncode": -1, "stdout_tail": "", "stderr_tail": "no architecture tests found"}
    res = run_cmd([sys.executable, "-m", "pytest", *existing, "-q"], cwd=root, timeout=300)
    res["mode"] = "pytest"
    return res


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--mode", default="all")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--run-app-factory-smoke", action="store_true")
    parser.add_argument("--run-secret-gate", action="store_true")
    parser.add_argument("--run-pytest", action="store_true")
    parser.add_argument("--install-pytest", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report_path = root / REPORT_REL
    changed = []

    dev_req = append_unique_lines(root / "requirements-dev.txt", DEV_REQUIREMENTS)
    if dev_req.get("changed"):
        changed.append("requirements-dev.txt")
    pytest_ini = ensure_pytest_ini(root)
    if pytest_ini.get("changed"):
        changed.append("pytest.ini")
    test_file = ensure_tests(root)
    if test_file.get("changed"):
        changed.append("tests/architecture/test_pytest_standard_p2d.py")

    pytest_before = module_available("pytest", root)
    install_result = None
    if args.install_pytest and not pytest_before:
        install_result = install_pytest(root)
    pytest_installed = module_available("pytest", root)

    compile_result = compile_files(root) if args.compile_all else {"ok": True, "results": []}
    app_factory = run_app_factory(root) if args.run_app_factory_smoke else {"ok": True}
    secret_gate = run_secret_gate(root) if args.run_secret_gate else {"ok": True, "parsed": {"finding_count": 0}}
    pytest_result = run_pytest(root) if args.run_pytest and pytest_installed else {
        "ok": not args.run_pytest,
        "mode": "pytest_not_installed",
        "returncode": -1,
        "stdout_tail": "",
        "stderr_tail": "pytest module is not installed; run with -InstallPytest or install requirements-dev.txt",
    }

    ok = bool(
        compile_result.get("ok")
        and app_factory.get("ok")
        and secret_gate.get("ok")
        and (pytest_result.get("ok") if args.run_pytest else True)
        and pytest_installed
    )

    report = {
        "ok": ok,
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "mode": args.mode,
        "changed_count": len(changed),
        "changed": changed,
        "dev_requirements": dev_req,
        "pytest_ini": pytest_ini,
        "pytest_before": pytest_before,
        "pytest_installed": pytest_installed,
        "install_pytest_requested": bool(args.install_pytest),
        "install_pytest": install_result,
        "compile_ok": bool(compile_result.get("ok")),
        "compile_results": compile_result.get("results", []),
        "app_factory_ok": bool(app_factory.get("ok")),
        "app_factory_smoke": app_factory,
        "secret_gate_ok": bool(secret_gate.get("ok")),
        "secret_gate_finding_count": int(secret_gate.get("parsed", {}).get("finding_count", 0)) if isinstance(secret_gate.get("parsed"), dict) else None,
        "secret_gate": secret_gate,
        "pytest_ok": bool(pytest_result.get("ok")),
        "pytest_mode": pytest_result.get("mode"),
        "pytest": pytest_result,
        "report": str(report_path),
        "next_actions": [
            "P2D temizse local ve CI ortaminda gercek pytest kapisi standart kabul edilebilir.",
            "Bundan sonra yeni mimari testler tests/architecture altina eklenmeli ve python -m pytest ile calismalidir.",
            "P2E'de pytest kapisina mobil auth/dashboard/assistant request-level testleri daha ayrintili eklenebilir.",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": ok,
        "package": PACKAGE,
        "pytest_before": pytest_before,
        "pytest_installed": pytest_installed,
        "compile_ok": report["compile_ok"],
        "app_factory_ok": report["app_factory_ok"],
        "secret_gate_ok": report["secret_gate_ok"],
        "pytest_ok": report["pytest_ok"],
        "pytest_mode": report["pytest_mode"],
        "report": str(report_path),
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
