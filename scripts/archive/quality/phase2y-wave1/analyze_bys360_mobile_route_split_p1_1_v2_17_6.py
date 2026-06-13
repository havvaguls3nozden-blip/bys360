# -*- coding: utf-8 -*-
"""
BYS360 Mobile Route Split Plan P1.1 V2.17.6

Bu script uygulama dosyalarını değiştirmez. Yalnızca büyük mobil route dosyalarını analiz eder,
endpoint/URL bozmadan yapılacak güvenli refactor planını raporlar.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "V2.17.6"
SENTINEL = "BYS360_MOBILE_ROUTE_SPLIT_PLAN_P1_1_V2_17_6"

TARGETS = [
    "app/api/mobile/routes.py",
    "app/api/mobile/performance_routes.py",
]

EXCLUDE_DIR_PARTS = {
    ".venv", "venv", "__pycache__", ".git", "node_modules", "build", "dist",
    "_local_quarantine", "reports", ".pytest_cache", ".mypy_cache",
}

GROUP_RULES: List[Tuple[str, Tuple[str, ...], str]] = [
    ("auth", ("login", "logout", "token", "csrf", "session", "password", "auth", "refresh"), "app/api/mobile/auth_routes.py"),
    ("dashboard", ("dashboard", "home", "summary", "stats", "weather", "kpi"), "app/api/mobile/dashboard_routes.py"),
    ("profile", ("profile", "me", "account", "avatar", "photo"), "app/api/mobile/profile_routes.py"),
    ("personnel", ("personnel", "employee", "staff", "person", "people", "hr_", "leave", "attendance"), "app/api/mobile/personnel_routes.py"),
    ("performance", ("performance", "evaluation", "score", "scorecard", "period", "task", "criteria", "assignment", "low_score"), "app/api/mobile/performance_core_routes.py"),
    ("communication", ("message", "thread", "notification", "announcement", "mail", "inbox", "chat"), "app/api/mobile/communication_routes.py"),
    ("support", ("support", "ticket", "help", "feedback", "rating"), "app/api/mobile/support_routes.py"),
    ("survey", ("survey", "poll", "question", "answer"), "app/api/mobile/survey_routes.py"),
    ("assistant", ("assistant", "ai_agent", "agent", "knowledge", "guide", "chatbot"), "app/api/mobile/assistant_routes.py"),
    ("upload_file", ("upload", "file", "attachment", "download", "media"), "app/api/mobile/file_routes.py"),
    ("health", ("health", "ping", "status", "version", "manifest"), "app/api/mobile/health_routes.py"),
]

PERFORMANCE_GROUP_RULES: List[Tuple[str, Tuple[str, ...], str]] = [
    ("performance_summary", ("summary", "dashboard", "overview", "stats"), "app/api/mobile/performance_summary_routes.py"),
    ("performance_periods", ("period", "calendar", "active"), "app/api/mobile/performance_period_routes.py"),
    ("performance_tasks", ("task", "assignment", "my_", "pending", "waiting"), "app/api/mobile/performance_task_routes.py"),
    ("performance_evaluation", ("evaluation", "evaluate", "score", "criteria", "item", "submit", "save"), "app/api/mobile/performance_evaluation_routes.py"),
    ("performance_scorecard", ("scorecard", "card", "archive", "published", "result"), "app/api/mobile/performance_scorecard_routes.py"),
]

SECRET_PATTERNS = [
    re.compile(r"(?i)(secret|password|passwd|pwd|token|api[_-]?key|dsn|smtp|database_url|db_password)\s*[:=]"),
    re.compile(r"(?i)(postgresql|mysql|redis|smtp)://[^\s'\"]+"),
]

ROUTE_PATTERNS = [
    re.compile(r"@\s*[\w\.]+\.route\s*\("),
    re.compile(r"\.add_url_rule\s*\("),
    re.compile(r"@\s*[\w\.]+\.(get|post|put|delete|patch)\s*\("),
]


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except Exception:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def short_ast_expr(node: ast.AST) -> str:
    try:
        return ast.unparse(node)[:220]
    except Exception:
        return node.__class__.__name__


def classify_function(name: str, source_rel: str) -> Tuple[str, str]:
    lower = name.lower()
    rules = PERFORMANCE_GROUP_RULES if source_rel.endswith("performance_routes.py") else GROUP_RULES
    for group, keys, target in rules:
        if any(k in lower for k in keys):
            return group, target
    return "misc", "app/api/mobile/misc_routes.py" if "mobile/routes.py" in source_rel else "app/api/mobile/performance_misc_routes.py"


def line_span(node: ast.AST, total_lines: int) -> Tuple[int, int, int]:
    start = getattr(node, "lineno", 1) or 1
    end = getattr(node, "end_lineno", start) or start
    end = max(start, min(end, total_lines))
    return start, end, end - start + 1


def extract_imports(tree: ast.AST) -> List[str]:
    imports: List[str] = []
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(short_ast_expr(node))
    return imports


def analyze_file(path: Path, root: Path) -> Dict[str, Any]:
    source_rel = rel(path, root)
    result: Dict[str, Any] = {
        "path": source_rel,
        "exists": path.exists(),
        "syntax_ok": False,
        "size_kb": 0,
        "line_count": 0,
        "imports": [],
        "route_markers": [],
        "functions": [],
        "groups": {},
        "possible_secret_hits": [],
        "errors": [],
    }
    if not path.exists():
        result["errors"].append("Dosya bulunamadı.")
        return result
    text = read_text(path)
    lines = text.splitlines()
    result["size_kb"] = round(path.stat().st_size / 1024, 1)
    result["line_count"] = len(lines)
    for idx, line in enumerate(lines, start=1):
        if any(p.search(line) for p in ROUTE_PATTERNS):
            result["route_markers"].append({"line": idx, "text": line.strip()[:260]})
        if any(p.search(line) for p in SECRET_PATTERNS):
            # Değer göstermiyoruz; yalnızca konum ve anahtar izini maskeleyerek veriyoruz.
            result["possible_secret_hits"].append({"line": idx, "hint": re.sub(r"=.*", "=<masked>", line.strip()[:160])})
    try:
        tree = ast.parse(text, filename=source_rel)
        result["syntax_ok"] = True
    except SyntaxError as exc:
        result["errors"].append(f"SyntaxError: {exc}")
        return result
    result["imports"] = extract_imports(tree)
    groups: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"target_file": "", "function_count": 0, "total_lines": 0, "functions": []})
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start, end, count = line_span(node, len(lines))
            group, target = classify_function(node.name, source_rel)
            decorators = [short_ast_expr(d) for d in getattr(node, "decorator_list", [])]
            entry = {
                "name": node.name,
                "async": isinstance(node, ast.AsyncFunctionDef),
                "start_line": start,
                "end_line": end,
                "line_count": count,
                "decorators": decorators,
                "suggested_group": group,
                "suggested_target_file": target,
            }
            result["functions"].append(entry)
            groups[group]["target_file"] = target
            groups[group]["function_count"] += 1
            groups[group]["total_lines"] += count
            groups[group]["functions"].append(node.name)
    result["groups"] = dict(sorted(groups.items(), key=lambda kv: (-kv[1]["total_lines"], kv[0])))
    return result


def run_cmd(args: List[str], cwd: Path, timeout: int = 120) -> Dict[str, Any]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            env=env,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-6000:],
            "stderr_tail": proc.stderr[-6000:],
        }
    except Exception as exc:
        return {"ok": False, "returncode": None, "stdout_tail": "", "stderr_tail": repr(exc)}


def health(root: Path) -> Dict[str, Any]:
    compile_result = run_cmd([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], root, timeout=180)
    factory_code = "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"
    factory_result = run_cmd([sys.executable, "-c", factory_code], root, timeout=120)
    return {
        "compileall_ok": bool(compile_result.get("ok")),
        "app_factory_ok": bool(factory_result.get("ok")) and "BYS360_APP_CREATE_OK" in factory_result.get("stdout_tail", ""),
        "overall_ok": bool(compile_result.get("ok")) and bool(factory_result.get("ok")) and "BYS360_APP_CREATE_OK" in factory_result.get("stdout_tail", ""),
        "compileall": compile_result,
        "app_factory": factory_result,
    }


def write_reports(root: Path, report: Dict[str, Any]) -> Dict[str, str]:
    out_dir = root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "bys360_mobile_route_split_plan_p1_1_v2_17_6_report.json"
    md_path = out_dir / "bys360_mobile_route_split_plan_p1_1_v2_17_6_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_md(report), encoding="utf-8")
    return {"json_report": rel(json_path, root), "md_report": rel(md_path, root)}


def render_md(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# BYS360 Mobile Route Split Plan P1.1 V2.17.6")
    lines.append("")
    lines.append("Bu rapor uygulama dosyalarını değiştirmez. Amaç, mobil API route dosyalarını endpoint ve URL bozmadan nasıl böleceğimizi netleştirmektir.")
    lines.append("")
    summary = report.get("summary", {})
    lines.append("## Özet")
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.append("")

    lines.append("## Dosya Bazlı Analiz")
    for item in report.get("targets", []):
        lines.append(f"### `{item.get('path')}`")
        lines.append(f"- Boyut: {item.get('size_kb')} KB")
        lines.append(f"- Satır: {item.get('line_count')}")
        lines.append(f"- Syntax OK: {item.get('syntax_ok')}")
        lines.append(f"- Fonksiyon: {len(item.get('functions', []))}")
        lines.append(f"- Route marker: {len(item.get('route_markers', []))}")
        lines.append(f"- Olası secret konumu: {len(item.get('possible_secret_hits', []))}")
        if item.get("errors"):
            lines.append("- Hatalar: " + "; ".join(item.get("errors", [])))
        lines.append("")
        lines.append("#### Önerilen Gruplar")
        groups = item.get("groups", {})
        if not groups:
            lines.append("- Grup çıkarılamadı.")
        else:
            lines.append("| Grup | Hedef dosya | Fonksiyon | Tahmini satır |")
            lines.append("|---|---|---:|---:|")
            for group, data in groups.items():
                lines.append(f"| {group} | `{data.get('target_file')}` | {data.get('function_count')} | {data.get('total_lines')} |")
        lines.append("")
        lines.append("#### En Büyük Fonksiyonlar")
        funcs = sorted(item.get("functions", []), key=lambda f: f.get("line_count", 0), reverse=True)[:20]
        if funcs:
            lines.append("| Fonksiyon | Satır | Önerilen grup | Hedef dosya |")
            lines.append("|---|---:|---|---|")
            for f in funcs:
                lines.append(f"| `{f.get('name')}` | {f.get('line_count')} | {f.get('suggested_group')} | `{f.get('suggested_target_file')}` |")
        lines.append("")

    lines.append("## Güvenli Refactor Sırası")
    lines.append("1. Yeni hedef route dosyalarını boş blueprint olarak değil, mevcut blueprint'i kullanan yardımcı modüller olarak tasarla.")
    lines.append("2. İlk adımda sadece servis/helper fonksiyonlarını ayır; route decorator ve URL tanımlarını yerinde bırak.")
    lines.append("3. İkinci adımda route fonksiyonlarını küçük dosyalara taşı; blueprint adı, endpoint adı ve URL path aynı kalmalı.")
    lines.append("4. Her mikro adım sonrası `python -m compileall app config.py scripts` ve `create_app` testi çalışmalı.")
    lines.append("5. Mobil app tarafında login, dashboard, profil, performans özeti, destek ve anket smoke test yapılmalı.")
    lines.append("")
    health_data = report.get("health_summary", {})
    if health_data:
        lines.append("## Sağlık Kontrolü")
        lines.append(f"- compileall_ok: {health_data.get('compileall_ok')}")
        lines.append(f"- app_factory_ok: {health_data.get('app_factory_ok')}")
        lines.append(f"- overall_ok: {health_data.get('overall_ok')}")
        lines.append("")
    lines.append("## Not")
    lines.append("Bu paket P1.1 plan paketidir; kod taşıma yapmaz. Kod taşıma bir sonraki P1.2 paketinde küçük ve geri alınabilir adımlarla yapılmalıdır.")
    return "\n".join(lines) + "\n"


def build_report(root: Path, mode: str) -> Dict[str, Any]:
    analyzed = [analyze_file(root / target, root) for target in TARGETS]
    all_functions = sum(len(item.get("functions", [])) for item in analyzed)
    all_lines = sum(int(item.get("line_count", 0)) for item in analyzed)
    all_secret_hits = sum(len(item.get("possible_secret_hits", [])) for item in analyzed)
    groups_total: Dict[str, int] = defaultdict(int)
    for item in analyzed:
        for group, data in item.get("groups", {}).items():
            groups_total[group] += int(data.get("function_count", 0))
    h = health(root) if mode in {"health", "all"} else {}
    report = {
        "version": VERSION,
        "mode": mode,
        "project_root": str(root),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "target_file_count": len(TARGETS),
            "total_lines_in_targets": all_lines,
            "total_functions_in_targets": all_functions,
            "possible_secret_hit_count_in_targets": all_secret_hits,
            "group_count": len(groups_total),
            "top_groups": dict(sorted(groups_total.items(), key=lambda kv: (-kv[1], kv[0]))[:12]),
        },
        "targets": analyzed,
        "health_summary": h,
    }
    paths = write_reports(root, report)
    report.update(paths)
    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--mode", choices=["audit", "health", "all"], default="audit")
    args = parser.parse_args(argv)
    root = Path(args.project_root).resolve()
    report = build_report(root, args.mode)
    print(json.dumps({k: v for k, v in report.items() if k not in {"targets"}}, ensure_ascii=False, indent=2))
    print(f"{SENTINEL}_REPORT_OK")
    if args.mode in {"health", "all"}:
        if report.get("health_summary", {}).get("overall_ok"):
            print(f"{SENTINEL}_HEALTH_OK")
        else:
            print(f"{SENTINEL}_HEALTH_FAIL")
            return 1
    print(f"{SENTINEL}_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
