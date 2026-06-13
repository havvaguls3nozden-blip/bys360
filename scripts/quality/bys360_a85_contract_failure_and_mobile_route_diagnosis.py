from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
import ast
import json
import re
import subprocess
import sys

ROOT = Path(".").resolve()
OUT_JSON = Path("reports/quality/BYS360_A85_CONTRACT_FAILURE_AND_MOBILE_ROUTE_DIAGNOSIS.json")
OUT_MD = Path("reports/quality/BYS360_A85_CONTRACT_FAILURE_AND_MOBILE_ROUTE_DIAGNOSIS.md")

PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"

PYTEST_CMD = [
    str(PYTHON),
    "-m",
    "pytest",
    "tests",
    "--ignore=tests/_archive_a5_obsolete",
    "-m",
    "not live and not realdb and not slow",
    "-q",
]

MOBILE_ROOT = ROOT / "app" / "api" / "mobile"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return ""


def extract_ast_mobile_routes(path: Path) -> list[dict]:
    text = read_text(path)
    routes = []

    try:
        tree = ast.parse(text, filename=str(path))
    except Exception as exc:
        return [{
            "source": "ast_parse_error",
            "file": rel(path),
            "line": 0,
            "rule": "",
            "methods": [],
            "function": "",
            "error": repr(exc),
        }]

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue

            func = dec.func
            if not isinstance(func, ast.Attribute):
                continue

            owner = func.value
            if not isinstance(owner, ast.Name):
                continue

            if owner.id not in {"mobile_api_bp", "mobile_bp"}:
                continue

            if func.attr not in {"get", "post", "put", "patch", "delete", "route"}:
                continue

            rule = ""
            methods = []

            if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                rule = dec.args[0].value

            for kw in dec.keywords:
                if kw.arg == "methods":
                    try:
                        value = ast.literal_eval(kw.value)
                        if isinstance(value, (list, tuple)):
                            methods = [str(v).upper() for v in value]
                    except Exception:
                        pass

            if not methods:
                methods = ["GET"] if func.attr == "route" else [func.attr.upper()]

            routes.append({
                "source": "ast_decorator",
                "file": rel(path),
                "line": getattr(dec, "lineno", getattr(node, "lineno", 0)),
                "rule": rule,
                "methods": methods,
                "function": node.name,
                "error": "",
            })

    return routes


def extract_string_mobile_routes(path: Path) -> list[dict]:
    text = read_text(path)
    routes = []

    pattern = re.compile(
        r'@(?:mobile_api_bp|mobile_bp)\.(get|post|put|patch|delete|route)\(\s*[\'"]([^\'"]+)[\'"]',
        re.IGNORECASE,
    )

    for match in pattern.finditer(text):
        attr = match.group(1).lower()
        rule = match.group(2)
        methods = ["GET"] if attr == "route" else [attr.upper()]
        line = text[:match.start()].count("\n") + 1

        routes.append({
            "source": "string_or_bridge_decorator",
            "file": rel(path),
            "line": line,
            "rule": rule,
            "methods": methods,
            "function": "",
            "error": "",
        })

    return routes


def normalize_rule(rule: str) -> str:
    rule = "/" + str(rule or "").strip().lstrip("/")
    return rule.replace("//", "/")


def full_mobile_rule(rule: str) -> str:
    return "/api/mobile" + normalize_rule(rule)


def collect_mobile_routes() -> list[dict]:
    routes = []

    if not MOBILE_ROOT.exists():
        return routes

    for path in sorted(MOBILE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue

        ast_routes = extract_ast_mobile_routes(path)
        string_routes = extract_string_mobile_routes(path)

        # AST gerçek decoratorları alır; bridge dosyalarında route string içinde olduğu için string parser da gerekir.
        combined = ast_routes + [
            r for r in string_routes
            if not any(
                r["rule"] == a.get("rule")
                and r["file"] == a.get("file")
                and r["line"] == a.get("line")
                for a in ast_routes
            )
        ]

        for item in combined:
            item["normalized_rule"] = normalize_rule(item.get("rule", ""))
            item["full_rule"] = full_mobile_rule(item.get("rule", ""))
            routes.append(item)

    return routes


def diagnose_mobile_duplicates(routes: list[dict]) -> dict:
    by_method_path = defaultdict(list)
    by_path_only = defaultdict(list)

    for r in routes:
        for method in r.get("methods") or ["GET"]:
            by_method_path[(method.upper(), r["full_rule"])].append(r)
        by_path_only[r["full_rule"]].append(r)

    exact_duplicates = {
        f"{method} {path}": items
        for (method, path), items in by_method_path.items()
        if len(items) > 1
    }

    path_only_duplicates = {
        path: items
        for path, items in by_path_only.items()
        if len(items) > 1
    }

    method_aware_ok_but_path_duplicate = {}

    for path, items in path_only_duplicates.items():
        method_set = []
        for item in items:
            method_set.extend([m.upper() for m in item.get("methods") or []])
        if len(method_set) == len(set(method_set)):
            method_aware_ok_but_path_duplicate[path] = items

    return {
        "total_mobile_routes_found": len(routes),
        "exact_duplicate_count": len(exact_duplicates),
        "path_only_duplicate_count": len(path_only_duplicates),
        "method_aware_ok_but_path_duplicate_count": len(method_aware_ok_but_path_duplicate),
        "exact_duplicates": exact_duplicates,
        "path_only_duplicates": path_only_duplicates,
        "method_aware_ok_but_path_duplicate": method_aware_ok_but_path_duplicate,
    }


def run_pytest_contract_suite() -> dict:
    if not PYTHON.exists():
        return {
            "ok": False,
            "returncode": -1,
            "cmd": PYTEST_CMD,
            "stdout": "",
            "stderr": f"Python bulunamadı: {PYTHON}",
            "failures": [],
            "errors": [],
            "summary": {},
        }

    proc = subprocess.run(
        PYTEST_CMD,
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="ignore",
        timeout=900,
    )

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    combined = stdout + "\n" + stderr

    failures = []
    errors = []

    for line in combined.splitlines():
        stripped = line.strip()

        if stripped.startswith("FAILED "):
            failures.append(stripped)

        if stripped.startswith("ERROR "):
            errors.append(stripped)

    # Pytest summary örnekleri:
    # 735 passed, 2 skipped, 42 deselected, 32 warnings
    # 6 failed, 700 passed...
    summary = {}
    summary_pattern = re.compile(r"(\d+)\s+(failed|passed|error|errors|skipped|deselected|warnings|warning)")
    for num, key in summary_pattern.findall(combined):
        normalized = key.lower()
        if normalized == "error":
            normalized = "errors"
        if normalized == "warning":
            normalized = "warnings"
        summary[normalized] = int(num)

    # Kısa teşhis için sadece ilk 200 satır değil, son 400 satır daha faydalı.
    tail_lines = combined.splitlines()[-400:]

    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "cmd": PYTEST_CMD,
        "failures": failures,
        "errors": errors,
        "failure_count": len(failures),
        "error_count": len(errors),
        "summary": summary,
        "tail": "\n".join(tail_lines),
    }


def count_ps1_files() -> dict:
    ps1_files = []
    for path in ROOT.rglob("*.ps1"):
        parts = set(path.parts)
        if ".venv" in parts or "__pycache__" in parts:
            continue
        ps1_files.append(rel(path))

    return {
        "count": len(ps1_files),
        "sample": ps1_files[:80],
    }


def archive_status() -> dict:
    archive = ROOT / "tests" / "_archive_a5_obsolete"
    files = []

    if archive.exists():
        for path in archive.rglob("*"):
            if path.is_file():
                files.append(rel(path))

    return {
        "exists": archive.exists(),
        "file_count": len(files),
        "sample": files[:80],
    }


def classify_failure_line(line: str) -> dict:
    item = {
        "raw": line,
        "file": "",
        "test": "",
        "reason": "",
        "diagnosis": "",
        "suggested_fix": "",
    }

    text = line.strip()

    # FAILED tests/mobile/test_x.py::test_name - AssertionError...
    m = re.match(r"FAILED\s+(.+?)::([^\s]+)\s+-\s+(.+)", text)
    if m:
        item["file"] = m.group(1)
        item["test"] = m.group(2)
        item["reason"] = m.group(3)
    else:
        m2 = re.match(r"ERROR\s+(.+?)\s+-\s+(.+)", text)
        if m2:
            item["file"] = m2.group(1)
            item["reason"] = m2.group(2)

    low = text.lower()

    if "duplicate" in low or "mükerrer" in low:
        item["diagnosis"] = "Duplicate route/contract çakışması."
        item["suggested_fix"] = "Route contract method-aware yapılmalı veya gerçek aynı METHOD+PATH çakışması tekilleştirilmeli."
    elif "route" in low and ("24" in low or "count" in low):
        item["diagnosis"] = "Mobil route sayısı sözleşme beklentisiyle uyuşmuyor."
        item["suggested_fix"] = "Beklenen endpoint sayısı güncel mimariye göre revize edilmeli veya eksik/fazla endpoint temizlenmeli."
    elif "archive" in low or "_archive_a5_obsolete" in low:
        item["diagnosis"] = "Arşiv test klasörü hâlâ test/CI kapsamına giriyor."
        item["suggested_fix"] = "tests/_archive_a5_obsolete depodan silinmeli veya CI ignore kalıcı yapılmalı."
    elif ".ps1" in low:
        item["diagnosis"] = "Depoda eski/çok sayıda PowerShell bakım scripti contract borcu oluşturuyor."
        item["suggested_fix"] = "Gerekli scriptler scripts/windows altında tutulup eski overlay/repair ps1 dosyaları arşiv dışına alınmalı."
    elif "release" in low or "zip" in low or ".env" in low:
        item["diagnosis"] = "Release/evidence paketi sızıntı veya paketleme contract riski."
        item["suggested_fix"] = "Zip üretimi leak gate ok:true şartına bağlanmalı; .env/log/sample dosyaları kesin dışlanmalı."
    elif "import" in low or "modulenotfound" in low:
        item["diagnosis"] = "Test ortam bağımlılığı veya import contract hatası."
        item["suggested_fix"] = "CI venv bağımlılıkları sabitlenmeli; test marker/ignore düzeni netleştirilmeli."
    elif item["raw"]:
        item["diagnosis"] = "Sözleşme/test assertion hatası."
        item["suggested_fix"] = "İlgili test dosyasındaki beklenen sözleşme ile canlı kod karşılaştırılmalı."

    return item


def main() -> int:
    routes = collect_mobile_routes()
    mobile_diag = diagnose_mobile_duplicates(routes)
    pytest_diag = run_pytest_contract_suite()

    failure_lines = pytest_diag.get("failures", []) + pytest_diag.get("errors", [])
    classified_failures = [classify_failure_line(line) for line in failure_lines]

    ps1_diag = count_ps1_files()
    archive_diag = archive_status()

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A85_CONTRACT_FAILURE_AND_MOBILE_ROUTE_DIAGNOSIS",
        "diagnosis_only": True,
        "mobile_routes": routes,
        "mobile_duplicate_diagnosis": mobile_diag,
        "pytest_contract_run": {
            k: v for k, v in pytest_diag.items()
            if k not in {"tail"}
        },
        "pytest_tail": pytest_diag.get("tail", ""),
        "classified_failures": classified_failures,
        "classified_failure_count": len(classified_failures),
        "ps1_files": ps1_diag,
        "archive_status": archive_diag,
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A8.5 Contract Failure ve Mobil Route Teşhis Raporu",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Özet",
        "",
        f"- Diagnosis only: {result['diagnosis_only']}",
        f"- Mobil route sayısı: {mobile_diag['total_mobile_routes_found']}",
        f"- Exact duplicate METHOD+PATH sayısı: {mobile_diag['exact_duplicate_count']}",
        f"- Path-only duplicate sayısı: {mobile_diag['path_only_duplicate_count']}",
        f"- Method-aware OK ama path-only duplicate sayısı: {mobile_diag['method_aware_ok_but_path_duplicate_count']}",
        f"- Pytest return code: {pytest_diag.get('returncode')}",
        f"- Pytest failure line count: {pytest_diag.get('failure_count')}",
        f"- Pytest error line count: {pytest_diag.get('error_count')}",
        f"- Classified failure count: {len(classified_failures)}",
        f"- PS1 dosya sayısı: {ps1_diag['count']}",
        f"- tests/_archive_a5_obsolete var mı: {archive_diag['exists']}",
        f"- tests/_archive_a5_obsolete dosya sayısı: {archive_diag['file_count']}",
        "",
        "## Mükerrer Mobil Route Teşhisi",
        "",
    ]

    if mobile_diag["exact_duplicates"]:
        lines.append("### Gerçek exact duplicate METHOD+PATH bulundu")
        lines.append("")
        for key, items in mobile_diag["exact_duplicates"].items():
            lines.append(f"#### {key}")
            for item in items:
                lines.append(f"- `{item['file']}:{item['line']}` function=`{item.get('function', '')}` source=`{item.get('source', '')}`")
            lines.append("")
    else:
        lines.append("Exact duplicate METHOD+PATH bulunmadı.")
        lines.append("")

    if mobile_diag["method_aware_ok_but_path_duplicate"]:
        lines.append("### Aynı path, farklı method kullanan adaylar")
        lines.append("")
        for path, items in mobile_diag["method_aware_ok_but_path_duplicate"].items():
            lines.append(f"#### {path}")
            for item in items:
                lines.append(f"- methods={item.get('methods')} `{item['file']}:{item['line']}` function=`{item.get('function', '')}`")
            lines.append("")
        lines.append("Not: Bunlar Flask açısından genelde geçerli olabilir; contract sadece path bazlı duplicate bakıyorsa false-positive üretir.")
        lines.append("")

    lines.extend([
        "## Pytest / Contract Hataları",
        "",
        f"- Komut: `{' '.join(PYTEST_CMD)}`",
        f"- Return code: `{pytest_diag.get('returncode')}`",
        f"- Summary: `{pytest_diag.get('summary')}`",
        "",
    ])

    if classified_failures:
        for idx, item in enumerate(classified_failures, 1):
            lines.extend([
                f"### {idx}. {item['file']}::{item['test']}",
                f"- Ham satır: `{item['raw']}`",
                f"- Neden: `{item['reason']}`",
                f"- Teşhis: {item['diagnosis']}",
                f"- Önerilen düzeltme: {item['suggested_fix']}",
                "",
            ])
    else:
        lines.append("Pytest FAILED/ERROR satırı yakalanmadı. Ayrıntı için JSON içindeki pytest_tail alanına bakılmalı.")
        lines.append("")

    lines.extend([
        "## PS1 ve Arşiv Durumu",
        "",
        f"- PS1 dosya sayısı: {ps1_diag['count']}",
        f"- tests/_archive_a5_obsolete mevcut: {archive_diag['exists']}",
        f"- tests/_archive_a5_obsolete dosya sayısı: {archive_diag['file_count']}",
        "",
        "## Pytest Son 400 Satır",
        "",
        "```text",
        pytest_diag.get("tail", "")[-12000:],
        "```",
    ])

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A85_DIAGNOSIS_JSON:", OUT_JSON)
    print("A85_DIAGNOSIS_MD:", OUT_MD)
    print("A85_MOBILE_ROUTE_COUNT:", mobile_diag["total_mobile_routes_found"])
    print("A85_EXACT_DUPLICATE_COUNT:", mobile_diag["exact_duplicate_count"])
    print("A85_PATH_ONLY_DUPLICATE_COUNT:", mobile_diag["path_only_duplicate_count"])
    print("A85_METHOD_AWARE_OK_PATH_DUPLICATE_COUNT:", mobile_diag["method_aware_ok_but_path_duplicate_count"])
    print("A85_PYTEST_RETURN_CODE:", pytest_diag.get("returncode"))
    print("A85_CLASSIFIED_FAILURE_COUNT:", len(classified_failures))
    print("A85_PS1_COUNT:", ps1_diag["count"])
    print("A85_ARCHIVE_EXISTS:", archive_diag["exists"])
    print("A85_ARCHIVE_FILE_COUNT:", archive_diag["file_count"])

    # Teşhis scripti düzeltme yapmaz; rapor üretebildiyse 0 ile çıkar.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
