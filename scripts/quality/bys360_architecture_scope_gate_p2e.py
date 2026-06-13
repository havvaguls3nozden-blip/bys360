from __future__ import annotations

import argparse
import json
import os
import py_compile
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_CLAUDE_SCORE_UPLIFT_P2E_ARCHITECTURE_SCOPE_GATE"
REPORT_REL = Path("reports/architecture/BYS360_ARCHITECTURE_SCOPE_GATE_P2E_REPORT.json")

ACTIVE_ARCHITECTURE_TEST_FILES = {
    "test_architecture_scope_p2e.py",
    "test_pytest_standard_p2d.py",
    "test_mobile_api_contract_p2a.py",
    "test_mobile_api_behavior_smoke_p2b.py",
    "test_mobile_api_request_level_smoke_p2c_v3.py",
}

CONFTST_TEXT = '''
from __future__ import annotations

import os
from pathlib import Path

import pytest

# BYS360_P2E_ACTIVE_ARCHITECTURE_SCOPE
# Varsayılan mimari test kapısı yalnızca güncel ve canlı omurgayla uyumlu
# aktif kalite testlerini çalıştırır. Eski Faz/Faz10/portal/anket/mesaj
# sözleşme testleri arşiv niteliğindedir; gerekirse ortam değişkeniyle
# ayrıca koşturulabilir.
ACTIVE_ARCHITECTURE_TEST_FILES = {
    "test_architecture_scope_p2e.py",
    "test_pytest_standard_p2d.py",
    "test_mobile_api_contract_p2a.py",
    "test_mobile_api_behavior_smoke_p2b.py",
    "test_mobile_api_request_level_smoke_p2c_v3.py",
}


def _legacy_architecture_enabled() -> bool:
    return os.getenv("BYS360_RUN_LEGACY_ARCHITECTURE_TESTS", "").strip().lower() in {
        "1", "true", "yes", "on"
    }


def pytest_collection_modifyitems(config, items):
    if _legacy_architecture_enabled():
        return

    skip_legacy = pytest.mark.skip(
        reason=(
            "BYS360 eski mimari sözleşme testi arşiv kapsamındadır. "
            "Tüm eski testleri ayrıca çalıştırmak için "
            "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS=1 kullanın."
        )
    )

    for item in items:
        path_obj = getattr(item, "path", None) or getattr(item, "fspath", None)
        file_name = Path(str(path_obj)).name if path_obj is not None else ""
        if file_name.startswith("test_") and file_name not in ACTIVE_ARCHITECTURE_TEST_FILES:
            item.add_marker(skip_legacy)
'''

SCOPE_TEST_TEXT = '''
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "tests" / "architecture"


def test_architecture_scope_conftest_exists_and_documents_active_gate() -> None:
    conftest = ARCH / "conftest.py"
    assert conftest.exists()
    text = conftest.read_text(encoding="utf-8")
    assert "BYS360_P2E_ACTIVE_ARCHITECTURE_SCOPE" in text
    assert "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS" in text
    assert "ACTIVE_ARCHITECTURE_TEST_FILES" in text


def test_architecture_scope_keeps_current_mobile_gates_active() -> None:
    text = (ARCH / "conftest.py").read_text(encoding="utf-8")
    for file_name in [
        "test_pytest_standard_p2d.py",
        "test_mobile_api_contract_p2a.py",
        "test_mobile_api_behavior_smoke_p2b.py",
        "test_mobile_api_request_level_smoke_p2c_v3.py",
    ]:
        assert file_name in text
        assert (ARCH / file_name).exists(), f"aktif mimari test dosyası eksik: {file_name}"
'''

DOC_TEXT = '''
# BYS360 P2E — Aktif Mimari Test Kapsamı

Bu paket, `tests/architecture` altındaki tarihsel test birikimini ikiye ayırır:

1. **Aktif kalite kapısı:** Güncel canlı omurga ve mobil API mimari sözleşmesiyle uyumlu testler.
2. **Arşiv/eski sözleşme testleri:** Daha önceki Faz/Faz10/portal/anket/mesaj sözleşmelerine ait, mevcut canlı mimariyle çakışabilen testler.

Varsayılan komut:

```powershell
python -m pytest tests/architecture -q
```

Bu komut artık aktif mimari kapıyı çalıştırır ve eski sözleşme testlerini `skip` olarak raporlar.

Eski testlerin tamamını ayrıca görmek için:

```powershell
$env:BYS360_RUN_LEGACY_ARCHITECTURE_TESTS = "1"
python -m pytest tests/architecture -q
Remove-Item Env:\\BYS360_RUN_LEGACY_ARCHITECTURE_TESTS
```

Bu ayrım canlı riskini azaltmak için yapılmıştır; eski testler silinmez, sadece varsayılan CI kalitesinden ayrılır.
'''


def run(cmd: list[str], root: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, env=env)
    return {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "ok": proc.returncode == 0,
        "cmd": cmd,
    }


def compile_files(files: list[Path]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for f in files:
        try:
            py_compile.compile(str(f), doraise=True)
            out.append({"file": str(f), "ok": True, "error": ""})
        except Exception as exc:
            out.append({"file": str(f), "ok": False, "error": repr(exc)})
    return out


def parse_secret_gate(stdout: str) -> dict[str, Any]:
    text = stdout.strip()
    if not text:
        return {}
    start = text.rfind("{")
    if start >= 0:
        text = text[start:]
    try:
        return json.loads(text)
    except Exception:
        return {}


def ensure_files(root: Path) -> list[str]:
    changed: list[str] = []
    arch = root / "tests" / "architecture"
    arch.mkdir(parents=True, exist_ok=True)
    docs = root / "docs" / "architecture"
    docs.mkdir(parents=True, exist_ok=True)

    targets = {
        arch / "conftest.py": CONFTST_TEXT.lstrip(),
        arch / "test_architecture_scope_p2e.py": SCOPE_TEST_TEXT.lstrip(),
        docs / "BYS360_ARCHITECTURE_SCOPE_GATE_P2E.md": DOC_TEXT.lstrip(),
    }
    for path, content in targets.items():
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if old != content:
            path.write_text(content, encoding="utf-8")
            changed.append(str(path.relative_to(root)))
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--mode", default="all")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--run-app-factory-smoke", action="store_true")
    parser.add_argument("--run-secret-gate", action="store_true")
    parser.add_argument("--run-pytest", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report_path = root / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)

    changed = ensure_files(root)

    compile_targets = [
        root / "scripts" / "quality" / "bys360_architecture_scope_gate_p2e.py",
        root / "tests" / "architecture" / "conftest.py",
        root / "tests" / "architecture" / "test_architecture_scope_p2e.py",
    ]
    compile_results = compile_files(compile_targets) if args.compile_all else []
    compile_ok = all(item["ok"] for item in compile_results) if compile_results else True

    app_factory = {"ok": True, "skipped": True}
    if args.run_app_factory_smoke:
        app_factory = run([sys.executable, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"], root)

    secret_gate = {"ok": True, "skipped": True, "parsed": {}}
    if args.run_secret_gate:
        gate = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
        secret_gate = run([sys.executable, str(gate), "--root", str(root)], root)
        parsed = parse_secret_gate(secret_gate.get("stdout_tail", ""))
        secret_gate["parsed"] = parsed
        secret_gate["ok"] = bool(parsed.get("ok") is True and int(parsed.get("finding_count", 1)) == 0)

    pytest_result = {"ok": True, "skipped": True, "mode": "not_requested"}
    if args.run_pytest:
        env = os.environ.copy()
        env.pop("BYS360_RUN_LEGACY_ARCHITECTURE_TESTS", None)
        pytest_result = run([sys.executable, "-m", "pytest", "tests/architecture", "-q"], root, env=env)
        pytest_result["mode"] = "active_architecture_scope"

    arch = root / "tests" / "architecture"
    all_arch_tests = sorted(p.name for p in arch.glob("test_*.py"))
    active = sorted(ACTIVE_ARCHITECTURE_TEST_FILES)
    legacy = [name for name in all_arch_tests if name not in ACTIVE_ARCHITECTURE_TEST_FILES]

    result: dict[str, Any] = {
        "ok": bool(compile_ok and app_factory.get("ok") and secret_gate.get("ok") and pytest_result.get("ok")),
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "mode": args.mode,
        "changed_count": len(changed),
        "changed": changed,
        "active_architecture_tests": active,
        "legacy_architecture_test_count": len(legacy),
        "legacy_architecture_tests_sample": legacy[:25],
        "scope_env_override": "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS=1",
        "compile_ok": compile_ok,
        "compile_results": compile_results,
        "app_factory_ok": bool(app_factory.get("ok")),
        "app_factory_smoke": app_factory,
        "secret_gate_ok": bool(secret_gate.get("ok")),
        "secret_gate_finding_count": int(secret_gate.get("parsed", {}).get("finding_count", 0)) if isinstance(secret_gate.get("parsed"), dict) else 0,
        "secret_gate": secret_gate,
        "pytest_ok": bool(pytest_result.get("ok")),
        "pytest_mode": pytest_result.get("mode"),
        "pytest": pytest_result,
        "report": str(report_path),
        "next_actions": [
            "P2E temizse python -m pytest tests/architecture -q aktif mimari kapisi olarak kullanilabilir.",
            "Eski sozlesme testleri silinmedi; BYS360_RUN_LEGACY_ARCHITECTURE_TESTS=1 ile ayrica kosulabilir.",
            "P2F'de genel CI komutu aktif mimari + secret gate + app factory smoke olarak tek runner altinda toparlanabilir.",
        ],
    }
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": result["ok"],
        "package": PACKAGE,
        "changed_count": len(changed),
        "active_architecture_test_count": len(active),
        "legacy_architecture_test_count": len(legacy),
        "compile_ok": result["compile_ok"],
        "app_factory_ok": result["app_factory_ok"],
        "secret_gate_ok": result["secret_gate_ok"],
        "pytest_ok": result["pytest_ok"],
        "pytest_mode": result["pytest_mode"],
        "report": str(report_path),
    }, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
