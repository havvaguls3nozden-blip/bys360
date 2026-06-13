from __future__ import annotations

import ast
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

LIVE_ROOTS = {"app", "config.py", "wsgi.py", "run.py"}
EXCLUDE_DIRS = {".venv", "venv", "__pycache__", ".git", "node_modules", "reports", "backups", "archive", "overlays"}
CRITICAL_HINTS = (
    "auth", "security", "session", "permission", "csrf", "login", "user", "admin",
    "config", "mail", "notification", "performance", "api", "mobile", "settings",
    "database", "db", "scheduler", "task", "token", "password"
)
WEAK_NODES = (ast.Pass,)
LOG_NAMES = {"logger", "logging", "current_app"}

@dataclass
class ExceptionFinding:
    file: str
    line: int
    priority: str
    reason: str
    has_logging: bool
    has_reraise: bool
    handler_summary: str
    suggested_action: str


def is_live_file(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    parts = set(rel.parts)
    if parts & EXCLUDE_DIRS:
        return False
    if rel.parts[0] == "app":
        return True
    return str(rel).replace("\\", "/") in {"config.py", "wsgi.py", "run.py"}


def iter_py(root: Path):
    for p in root.rglob("*.py"):
        if is_live_file(p, root):
            yield p


def is_exception_type(node: ast.ExceptHandler) -> bool:
    t = node.type
    if t is None:
        return False
    if isinstance(t, ast.Name) and t.id == "Exception":
        return True
    if isinstance(t, ast.Tuple):
        return any(isinstance(e, ast.Name) and e.id == "Exception" for e in t.elts)
    return False


def contains_logging(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            f = child.func
            if isinstance(f, ast.Attribute):
                if isinstance(f.value, ast.Name) and f.value.id in LOG_NAMES:
                    return True
                if f.attr in {"exception", "error", "warning", "warn", "critical"}:
                    return True
            if isinstance(f, ast.Name) and f.id in {"log_exception", "record_exception", "capture_exception"}:
                return True
    return False


def contains_reraise(node: ast.AST) -> bool:
    return any(isinstance(child, ast.Raise) for child in ast.walk(node))


def is_weak_handler(node: ast.ExceptHandler) -> bool:
    if not node.body:
        return True
    if len(node.body) == 1 and isinstance(node.body[0], WEAK_NODES):
        return True
    if len(node.body) <= 2:
        # return None/False/[]/{} without logging or re-raise is weak
        for stmt in node.body:
            if isinstance(stmt, ast.Return):
                return True
            if isinstance(stmt, ast.Assign):
                continue
    return False


def handler_summary(node: ast.ExceptHandler) -> str:
    kinds = []
    for stmt in node.body[:4]:
        kinds.append(type(stmt).__name__)
    if len(node.body) > 4:
        kinds.append("...")
    return ", ".join(kinds) or "empty"


def priority_for(path: Path, root: Path, node: ast.ExceptHandler, has_log: bool, has_raise: bool, weak: bool) -> tuple[str, str, str]:
    rel = str(path.relative_to(root)).replace("\\", "/")
    lower = rel.lower()
    critical = any(h in lower for h in CRITICAL_HINTS)
    if critical and (weak or not has_log) and not has_raise:
        return "P0", "critical live path + weak/silent broad exception", "Add logger.exception(...), return user-safe message, keep traceback in logs; narrow exception type if possible."
    if critical:
        return "P1", "critical live path broad exception", "Review and narrow exception type; ensure logger.exception includes safe context."
    if (weak or not has_log) and not has_raise:
        return "P2", "weak/silent broad exception", "Add logging or re-raise; avoid swallowing production errors."
    return "P3", "broad exception with some handling", "Refactor gradually; narrow exception type when touching this code."


def scan(root: Path):
    findings: list[ExceptionFinding] = []
    syntax_errors = []
    for p in iter_py(root):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except SyntaxError as e:
            syntax_errors.append({"file": str(p.relative_to(root)), "line": e.lineno, "error": str(e)})
            continue
        except UnicodeDecodeError:
            try:
                tree = ast.parse(p.read_text(encoding="utf-8-sig"), filename=str(p))
            except Exception as e:
                syntax_errors.append({"file": str(p.relative_to(root)), "line": 0, "error": repr(e)})
                continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and is_exception_type(node):
                has_log = contains_logging(node)
                has_raise = contains_reraise(node)
                weak = is_weak_handler(node)
                priority, reason, action = priority_for(p, root, node, has_log, has_raise, weak)
                findings.append(ExceptionFinding(
                    file=str(p.relative_to(root)).replace("\\", "/"),
                    line=getattr(node, "lineno", 0),
                    priority=priority,
                    reason=reason,
                    has_logging=has_log,
                    has_reraise=has_raise,
                    handler_summary=handler_summary(node),
                    suggested_action=action,
                ))
    return findings, syntax_errors


def write_reports(root: Path, findings: list[ExceptionFinding], syntax_errors: list[dict]):
    outdir = root / "reports" / "quality"
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / "BYS360_OPS_HARDENING_V5_EXCEPTION_GUARDRAIL_REPORT.json"
    md_path = outdir / "BYS360_OPS_HARDENING_V5_EXCEPTION_GUARDRAIL_REPORT.md"
    counts = {p: sum(1 for f in findings if f.priority == p) for p in ["P0", "P1", "P2", "P3"]}
    per_file = {}
    for f in findings:
        per_file.setdefault(f.file, {"total": 0, "P0": 0, "P1": 0, "P2": 0, "P3": 0})
        per_file[f.file]["total"] += 1
        per_file[f.file][f.priority] += 1
    top_files = sorted(per_file.items(), key=lambda kv: (kv[1]["P0"], kv[1]["P1"], kv[1]["total"]), reverse=True)[:40]
    first_p0 = [asdict(f) for f in findings if f.priority == "P0"][:100]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "python_exception_findings": len(findings),
        "syntax_errors": syntax_errors,
        "priority_counts": counts,
        "top_files": [{"file": k, **v} for k, v in top_files],
        "first_p0_findings": first_p0,
        "guardrail_rule": "Yeni P0/P2 sessiz broad exception eklenmemeli; mevcut borç kademeli azaltılmalı.",
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = []
    lines.append("# BYS360 Operasyonel Sağlamlaştırma V5 — Exception Guardrail Raporu")
    lines.append("")
    lines.append(f"Oluşturma zamanı: `{payload['generated_at']}`")
    lines.append("")
    lines.append("## Özet")
    lines.append("")
    lines.append("| Alan | Değer |")
    lines.append("|---|---:|")
    lines.append(f"| Broad `except Exception` bulgusu | {len(findings)} |")
    for p in ["P0", "P1", "P2", "P3"]:
        lines.append(f"| {p} | {counts[p]} |")
    lines.append(f"| Syntax hatası | {len(syntax_errors)} |")
    lines.append("")
    lines.append("## En Öncelikli Dosyalar")
    lines.append("")
    lines.append("| Dosya | Toplam | P0 | P1 | P2 | P3 |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for file, c in top_files:
        lines.append(f"| `{file}` | {c['total']} | {c['P0']} | {c['P1']} | {c['P2']} | {c['P3']} |")
    lines.append("")
    lines.append("## İlk 100 P0 Bulgusu")
    lines.append("")
    lines.append("| Dosya | Satır | Sebep | İşlem |")
    lines.append("|---|---:|---|---|")
    for f in [x for x in findings if x.priority == "P0"][:100]:
        lines.append(f"| `{f.file}` | {f.line} | {f.reason} | {f.suggested_action} |")
    lines.append("")
    lines.append("## V6 İçin Uygulama Kuralı")
    lines.append("")
    lines.append("V6'da yalnızca bu rapordaki P0 listesinden başlanmalı. Öncelik: auth/security/session/permission/config/mail/notification/performance/API. Kör toplu dönüşüm yapılmamalı.")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path, json_path, payload


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path.cwd()
    findings, syntax_errors = scan(root)
    md, js, payload = write_reports(root, findings, syntax_errors)
    print(f"BYS360_OPS_EXCEPTION_GUARDRAIL_V5_REPORT={md}")
    print(f"BYS360_OPS_EXCEPTION_GUARDRAIL_V5_JSON={js}")
    print(json.dumps({
        "broad_except_exception": payload["python_exception_findings"],
        "p0_count": payload["priority_counts"]["P0"],
        "p1_count": payload["priority_counts"]["P1"],
        "p2_count": payload["priority_counts"]["P2"],
        "p3_count": payload["priority_counts"]["P3"],
        "syntax_errors": len(syntax_errors),
    }, ensure_ascii=False))
    return 1 if syntax_errors else 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
