from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

PACKAGE = "BYS360_OPS_HARDENING_V4_EXCEPTION_TRIAGE"

CANDIDATE_DIRS = ["app"]
CANDIDATE_FILES = ["config.py", "wsgi.py", "run.py", "asgi.py", "manage.py"]
EXCLUDE_PARTS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
    "node_modules", "dist", "build", "reports", "backups", "archive",
}
CRITICAL_HINTS = {
    "auth", "login", "security", "csrf", "csp", "session", "password", "permission",
    "role", "admin", "performance", "mail", "email", "notification", "mobile", "api",
    "ai", "config", "sentry", "database", "db", "jwt", "token", "upload", "import",
}
LOGGING_FUNC_HINTS = {
    "exception", "error", "warning", "warn", "critical", "capture_exception",
    "capture_message", "logger", "current_app", "logging", "sentry_sdk",
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def iter_py_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for d in CANDIDATE_DIRS:
        base = root / d
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            rel_parts = set(p.relative_to(root).parts)
            if rel_parts & EXCLUDE_PARTS:
                continue
            files.append(p)
    for f in CANDIDATE_FILES:
        p = root / f
        if p.exists() and p.suffix == ".py":
            files.append(p)
    return sorted(set(files))


def node_name(node: ast.AST | None) -> str:
    if node is None:
        return ""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = node_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Tuple):
        return ",".join(node_name(elt) for elt in node.elts)
    if isinstance(node, ast.Subscript):
        return node_name(node.value)
    return node.__class__.__name__


def is_broad_exception(handler: ast.ExceptHandler) -> bool:
    typ = node_name(handler.type)
    parts = {p.strip() for p in typ.replace("(", "").replace(")", "").split(",") if p.strip()}
    return "Exception" in parts or typ == "Exception"


def call_name(call: ast.Call) -> str:
    return node_name(call.func)


def contains_logging_call(nodes: Iterable[ast.AST]) -> bool:
    for node in nodes:
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                name = call_name(child).lower()
                if any(h in name for h in LOGGING_FUNC_HINTS):
                    return True
    return False


def literal_empty_return(node: ast.Return) -> str | None:
    val = node.value
    if val is None:
        return "return_without_value"
    if isinstance(val, ast.Constant):
        if val.value is None:
            return "return_none"
        if val.value is False:
            return "return_false"
        if val.value == "":
            return "return_empty_string"
    if isinstance(val, (ast.List, ast.Tuple, ast.Set)) and len(val.elts) == 0:
        return "return_empty_collection"
    if isinstance(val, ast.Dict) and len(val.keys) == 0:
        return "return_empty_collection"
    return None


def handler_shape(handler: ast.ExceptHandler) -> Dict[str, Any]:
    body = handler.body or []
    wrapper = ast.Module(body=body, type_ignores=[])
    has_log = contains_logging_call(body)
    has_raise = any(isinstance(n, ast.Raise) for n in ast.walk(wrapper))
    has_flash = any(isinstance(n, ast.Call) and "flash" in call_name(n).lower() for item in body for n in ast.walk(item))
    has_abort = any(isinstance(n, ast.Call) and ("abort" in call_name(n).lower() or "render_template" in call_name(n).lower()) for item in body for n in ast.walk(item))
    body_types = [type(n).__name__ for n in body[:5]]

    silent_reason = None
    if len(body) == 1 and isinstance(body[0], ast.Pass):
        silent_reason = "pass_only"
    elif len(body) == 1 and isinstance(body[0], ast.Return):
        silent_reason = literal_empty_return(body[0])
    elif not has_log and not has_raise and not has_flash and not has_abort:
        silent_reason = "no_logging_or_user_visible_handling"

    return {
        "has_logging": has_log,
        "has_raise": has_raise,
        "has_user_visible_handling": has_flash or has_abort,
        "silent_reason": silent_reason,
        "body_preview": body_types,
    }


def risk_level(rel: str, shape: Dict[str, Any]) -> str:
    lower = rel.lower().replace("\\", "/")
    is_critical = any(h in lower for h in CRITICAL_HINTS)
    if shape.get("silent_reason") in {"pass_only", "return_none", "return_false", "return_empty_collection", "no_logging_or_user_visible_handling"} and is_critical:
        return "P0"
    if shape.get("silent_reason") and is_critical:
        return "P1"
    if shape.get("silent_reason"):
        return "P2"
    if not shape.get("has_logging") and not shape.get("has_raise"):
        return "P2"
    return "P3"


def category_for_path(rel: str) -> str:
    parts = rel.replace("\\", "/").split("/")
    if parts and parts[0] == "app" and len(parts) > 1:
        return f"app/{parts[1]}"
    return parts[0] if parts else rel


def scan_file(root: Path, path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    text = read_text(path)
    rel = str(path.relative_to(root))
    syntax_errors: List[Dict[str, Any]] = []
    findings: List[Dict[str, Any]] = []
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        syntax_errors.append({"file": rel, "line": exc.lineno, "error": str(exc)})
        return findings, syntax_errors

    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if not is_broad_exception(node):
            continue
        shape = handler_shape(node)
        findings.append({
            "file": rel,
            "line": getattr(node, "lineno", None),
            "exception_name": node.name,
            "category": category_for_path(rel),
            "risk": risk_level(rel, shape),
            **shape,
        })
    return findings, syntax_errors


def run_compileall(root: Path) -> bool:
    targets = [str(root / "app")]
    for f in CANDIDATE_FILES:
        p = root / f
        if p.exists():
            targets.append(str(p))
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", *targets],
            cwd=str(root), text=True, capture_output=True, timeout=240,
        )
        if completed.returncode != 0:
            print(completed.stdout)
            print(completed.stderr, file=sys.stderr)
        return completed.returncode == 0
    except Exception as exc:
        print(f"compileall calistirilamadi: {exc}", file=sys.stderr)
        return False


def table_counts(counter: Counter, headers: Tuple[str, str], limit: int = 30) -> str:
    rows = [f"| {headers[0]} | {headers[1]} |", "|---|---:|"]
    for k, v in counter.most_common(limit):
        rows.append(f"| `{k}` | {v} |")
    return "\n".join(rows)


def findings_table(items: List[Dict[str, Any]], limit: int = 80) -> str:
    rows = ["| Risk | Dosya | Satır | Durum |", "|---|---|---:|---|"]
    for f in items[:limit]:
        status = f.get("silent_reason") or ("log var" if f.get("has_logging") else "log yok")
        rows.append(f"| {f['risk']} | `{f['file']}` | {f.get('line') or ''} | {status} |")
    return "\n".join(rows)


def write_reports(root: Path, files: List[Path], findings: List[Dict[str, Any]], syntax_errors: List[Dict[str, Any]], compile_ok: bool) -> Dict[str, Any]:
    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    md_path = report_dir / "BYS360_OPS_HARDENING_V4_EXCEPTION_TRIAGE_REPORT.md"
    json_path = report_dir / "BYS360_OPS_HARDENING_V4_EXCEPTION_TRIAGE_REPORT.json"

    by_risk = Counter(f["risk"] for f in findings)
    by_category = Counter(f["category"] for f in findings)
    by_file = Counter(f["file"] for f in findings)
    silent = [f for f in findings if f.get("silent_reason")]
    no_logging = [f for f in findings if not f.get("has_logging") and not f.get("has_raise")]
    p0 = [f for f in findings if f["risk"] == "P0"]
    p1 = [f for f in findings if f["risk"] == "P1"]

    summary = {
        "package": PACKAGE,
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "python_files_scanned": len(files),
        "syntax_errors": len(syntax_errors),
        "broad_except_exception": len(findings),
        "p0_count": by_risk.get("P0", 0),
        "p1_count": by_risk.get("P1", 0),
        "p2_count": by_risk.get("P2", 0),
        "p3_count": by_risk.get("P3", 0),
        "silent_or_weak_handling": len(silent),
        "without_logging_or_reraise": len(no_logging),
        "compileall_ok": compile_ok,
        "report_md": str(md_path),
        "report_json": str(json_path),
    }

    payload = {
        "summary": summary,
        "by_risk": dict(by_risk),
        "by_category": dict(by_category),
        "top_files": by_file.most_common(100),
        "p0_findings": p0[:500],
        "p1_findings": p1[:500],
        "silent_findings_sample": silent[:500],
        "syntax_errors": syntax_errors,
        "all_findings": findings,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md = f"""# BYS360 Operasyonel Sağlamlaştırma V4 — Exception Triage Raporu

Bu rapor kod değiştirmez. Amaç `except Exception` borcunu canlı aday kod içinde risk seviyesine göre ayırmaktır.

## Özet

| Alan | Değer |
|---|---:|
| Taranan Python dosyası | {len(files)} |
| broad `except Exception` | {len(findings)} |
| P0 | {by_risk.get('P0', 0)} |
| P1 | {by_risk.get('P1', 0)} |
| P2 | {by_risk.get('P2', 0)} |
| P3 | {by_risk.get('P3', 0)} |
| Sessiz/zayıf yakalama | {len(silent)} |
| Log veya re-raise olmayan | {len(no_logging)} |
| Syntax hatası | {len(syntax_errors)} |
| compileall | {'OK' if compile_ok else 'FAIL'} |

## Risk Anlamı

- **P0:** kritik canlı yol + sessiz/zayıf hata yakalama. Önce bunlar düzeltilmeli.
- **P1:** kritik canlı yol + geniş exception, fakat nispeten daha az riskli gövde.
- **P2:** kritik olmayan dosyada sessiz/zayıf geniş exception veya log/re-raise eksikliği.
- **P3:** loglanan veya tekrar yükseltilen geniş exception. Kademeli refactor adayı.

## Risk Dağılımı

{table_counts(by_risk, ('Risk', 'Adet'))}

## Modül/Klasör Dağılımı

{table_counts(by_category, ('Alan', 'Adet'), 60)}

## En Çok Geniş Exception Olan Dosyalar

{table_counts(by_file, ('Dosya', 'Adet'), 60)}

## P0 İlk İnceleme Listesi

{findings_table(p0, 100)}

## P1 İlk İnceleme Listesi

{findings_table(p1, 100)}

## Sonraki Faz Önerisi

1. P0 listesinden başlanmalı.
2. Auth/security/session/permission/config/mail/notification/performance/API dosyaları önce ele alınmalı.
3. Sessiz `pass`, `return None`, `return False`, `return []` blokları loglanmalı veya özel exception sınıfıyla ayrıştırılmalı.
4. Kullanıcıya dönmesi gereken hatalarda teknik traceback yerine kurumsal Türkçe mesaj korunmalı.
5. Her küçük temizlik sonrası `compileall` ve smoke test çalıştırılmalı.

## Not

Bu rapor exception gövdelerindeki gerçek veri değerlerini göstermez; yalnızca dosya/satır ve davranış sınıfı üretir.
"""
    md_path.write_text(md, encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "all", "compile"], default="all")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    if not root.exists():
        print(f"Project root bulunamadi: {root}", file=sys.stderr)
        return 2

    files = iter_py_files(root)
    findings: List[Dict[str, Any]] = []
    syntax_errors: List[Dict[str, Any]] = []
    for p in files:
        f, s = scan_file(root, p)
        findings.extend(f)
        syntax_errors.extend(s)

    compile_ok = True
    if args.mode in {"all", "compile"}:
        compile_ok = run_compileall(root)
    summary = write_reports(root, files, findings, syntax_errors, compile_ok)

    print(f"BYS360_OPS_EXCEPTION_TRIAGE_V4_REPORT={summary['report_md']}")
    print(f"BYS360_OPS_EXCEPTION_TRIAGE_V4_JSON={summary['report_json']}")
    print(json.dumps({k: summary[k] for k in [
        "python_files_scanned", "syntax_errors", "broad_except_exception", "p0_count", "p1_count", "p2_count", "p3_count", "silent_or_weak_handling", "without_logging_or_reraise", "compileall_ok"
    ]}, ensure_ascii=False))
    if syntax_errors or not compile_ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
