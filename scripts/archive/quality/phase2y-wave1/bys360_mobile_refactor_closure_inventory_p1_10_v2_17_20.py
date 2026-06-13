from __future__ import annotations

import argparse
import ast
import json
import os
import py_compile
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

VERSION = "V2.17.20"
REPORT_JSON = Path("reports/quality/bys360_mobile_refactor_closure_inventory_p1_10_v2_17_20_report.json")
REPORT_MD = Path("reports/quality/bys360_mobile_refactor_closure_inventory_p1_10_v2_17_20_report.md")
TARGET_FILES = [
    Path("app/api/mobile/routes.py"),
    Path("app/api/mobile/performance_routes.py"),
]
SERVICE_DIR = Path("app/api/mobile/services")
SECRET_PATTERNS = [
    "password", "passwd", "secret", "token", "api_key", "apikey", "smtp", "credential", "private_key", "dsn"
]

@dataclass
class FunctionInfo:
    file: str
    name: str
    line: int
    end_line: int
    lines: int
    route_decorator: bool
    delegated: bool
    legacy: bool
    group: str
    arg: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def decorator_is_route(d: ast.AST) -> bool:
    try:
        s = ast.unparse(d)
    except Exception:
        s = ""
    return ".route(" in s or s.endswith(".route") or "mobile_bp.route" in s or "bp.route" in s


def arg_names(fn: ast.FunctionDef) -> str:
    parts: list[str] = []
    for a in list(fn.args.posonlyargs) + list(fn.args.args):
        parts.append(a.arg)
    if fn.args.vararg:
        parts.append("*" + fn.args.vararg.arg)
    for a in fn.args.kwonlyargs:
        parts.append(a.arg)
    if fn.args.kwarg:
        parts.append("**" + fn.args.kwarg.arg)
    return ", ".join(parts)


def classify(name: str, file_rel: str) -> str:
    n = name.lower()
    f = file_rel.lower()
    if "performance" in f or "performance" in n:
        if "task" in n:
            return "performance_tasks"
        if "period" in n or "note" in n:
            return "performance_periods"
        if "summary" in n:
            return "performance_summary"
        if "scorecard" in n or "score" in n or "evaluation" in n or "criteria" in n or "weight" in n:
            return "performance_evaluation"
        return "performance_misc"
    if "login" in n or "refresh" in n or n.endswith("_me") or "auth" in n:
        return "auth"
    if "dashboard" in n or "kpi" in n or "target" in n:
        return "dashboard"
    if "profile" in n:
        return "profile"
    if "personnel" in n or "created_personnel" in n:
        return "personnel"
    if "survey" in n or "anket" in n:
        return "survey"
    if "support" in n or "ticket" in n:
        return "support"
    if "communication" in n or "thread" in n or "message" in n:
        return "communication"
    if "assistant" in n or "ask" in n:
        return "assistant"
    if "health" in n:
        return "health"
    return "misc"


def analyze_file(root: Path, rel: Path) -> dict[str, Any]:
    path = root / rel
    result: dict[str, Any] = {
        "path": str(rel).replace("\\", "/"),
        "exists": path.exists(),
        "size_kb": 0.0,
        "line_count": 0,
        "syntax_ok": False,
        "syntax_error": "",
        "function_count": 0,
        "route_decorator_count": 0,
        "delegated_count": 0,
        "legacy_count": 0,
        "functions": [],
        "groups": {},
        "remaining_candidates": [],
        "possible_secret_hit_count": 0,
        "possible_secret_locations": [],
    }
    if not path.exists():
        return result
    text = read_text(path)
    lines = text.splitlines()
    result["size_kb"] = round(len(text.encode("utf-8", errors="ignore")) / 1024, 1)
    result["line_count"] = len(lines)

    for idx, line in enumerate(lines, 1):
        low = line.lower()
        if any(p in low for p in SECRET_PATTERNS):
            if "os.getenv" in low or "getenv(" in low or "env" in low or "placeholder" in low:
                continue
            result["possible_secret_hit_count"] += 1
            if len(result["possible_secret_locations"]) < 25:
                result["possible_secret_locations"].append({"line": idx, "hint": line.strip()[:120]})

    try:
        tree = ast.parse(text)
        result["syntax_ok"] = True
    except SyntaxError as e:
        result["syntax_error"] = f"line {e.lineno}: {e.msg}"
        return result

    legacy_names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("_bys360_legacy_")}
    service_markers = ("_service", "delegate_", "services.")
    funcs: list[FunctionInfo] = []
    for n in tree.body:
        if not isinstance(n, ast.FunctionDef):
            continue
        start = n.lineno
        end = getattr(n, "end_lineno", start)
        src = "\n".join(lines[start-1:end])
        delegated = any(m in src for m in service_markers)
        legacy = ("_bys360_legacy_" + n.name) in legacy_names or n.name.startswith("_bys360_legacy_")
        route = any(decorator_is_route(d) for d in n.decorator_list)
        group = classify(n.name, result["path"])
        info = FunctionInfo(
            file=result["path"],
            name=n.name,
            line=start,
            end_line=end,
            lines=max(1, end - start + 1),
            route_decorator=route,
            delegated=delegated,
            legacy=legacy,
            group=group,
            arg=arg_names(n),
        )
        funcs.append(info)

    result["function_count"] = len(funcs)
    result["route_decorator_count"] = sum(1 for f in funcs if f.route_decorator)
    result["delegated_count"] = sum(1 for f in funcs if f.delegated and not f.name.startswith("_bys360_legacy_"))
    result["legacy_count"] = sum(1 for f in funcs if f.name.startswith("_bys360_legacy_"))
    groups: dict[str, int] = {}
    for f in funcs:
        if f.name.startswith("_bys360_legacy_"):
            continue
        groups[f.group] = groups.get(f.group, 0) + 1
    result["groups"] = dict(sorted(groups.items(), key=lambda x: (-x[1], x[0])))
    result["functions"] = [asdict(f) for f in funcs]

    remaining = [
        f for f in funcs
        if not f.delegated and not f.name.startswith("_bys360_legacy_") and (f.lines >= 20 or f.route_decorator)
    ]
    remaining.sort(key=lambda f: (-f.lines, f.file, f.line))
    result["remaining_candidates"] = [asdict(f) for f in remaining[:40]]
    return result


def analyze_services(root: Path) -> dict[str, Any]:
    service_root = root / SERVICE_DIR
    files = sorted(service_root.glob("*.py")) if service_root.exists() else []
    service_items = []
    total_delegate = 0
    for p in files:
        text = read_text(p)
        delegate_count = text.count("def delegate_")
        total_delegate += delegate_count
        ok, err = py_ok(p)
        service_items.append({
            "path": safe_rel(p, root),
            "size_kb": round(len(text.encode("utf-8", errors="ignore")) / 1024, 1),
            "line_count": len(text.splitlines()),
            "delegate_count": delegate_count,
            "syntax_ok": ok,
            "syntax_error": err,
        })
    return {
        "service_root_exists": service_root.exists(),
        "service_file_count": len(files),
        "total_delegate_functions": total_delegate,
        "files": service_items,
    }


def py_ok(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "missing"
    try:
        py_compile.compile(str(path), doraise=True)
        return True, ""
    except Exception as e:
        return False, str(e)


def run_cmd(root: Path, cmd: list[str], timeout: int = 90) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        cp = subprocess.run(
            cmd,
            cwd=str(root),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=env,
        )
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout_tail": cp.stdout[-5000:],
            "stderr_tail": cp.stderr[-5000:],
        }
    except Exception as e:
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": str(e)}


def health(root: Path) -> dict[str, Any]:
    compile_res = run_cmd(root, [sys.executable, "-m", "compileall", "app", "config.py", "scripts"], timeout=120)
    factory_code = "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"
    factory_res = run_cmd(root, [sys.executable, "-c", factory_code], timeout=120)
    return {
        "compileall_ok": bool(compile_res["ok"]),
        "app_factory_ok": bool(factory_res["ok"] and "BYS360_APP_CREATE_OK" in factory_res.get("stdout_tail", "")),
        "overall_ok": bool(compile_res["ok"] and factory_res["ok"] and "BYS360_APP_CREATE_OK" in factory_res.get("stdout_tail", "")),
        "compileall": compile_res,
        "app_factory": factory_res,
    }


def build_report(root: Path, mode: str) -> dict[str, Any]:
    file_reports = [analyze_file(root, rel) for rel in TARGET_FILES]
    service_report = analyze_services(root)
    totals = {
        "target_file_count": len(file_reports),
        "total_lines": sum(int(r.get("line_count", 0)) for r in file_reports),
        "total_functions": sum(int(r.get("function_count", 0)) for r in file_reports),
        "total_route_decorators": sum(int(r.get("route_decorator_count", 0)) for r in file_reports),
        "total_delegated_functions": sum(int(r.get("delegated_count", 0)) for r in file_reports),
        "total_legacy_functions": sum(int(r.get("legacy_count", 0)) for r in file_reports),
        "total_remaining_candidates": sum(len(r.get("remaining_candidates", [])) for r in file_reports),
        "total_possible_secret_hits": sum(int(r.get("possible_secret_hit_count", 0)) for r in file_reports),
    }
    group_totals: dict[str, int] = {}
    for r in file_reports:
        for k, v in r.get("groups", {}).items():
            group_totals[k] = group_totals.get(k, 0) + int(v)
    totals["group_totals"] = dict(sorted(group_totals.items(), key=lambda x: (-x[1], x[0])))
    remaining_all: list[dict[str, Any]] = []
    for r in file_reports:
        remaining_all.extend(r.get("remaining_candidates", []))
    remaining_all.sort(key=lambda x: (-int(x.get("lines", 0)), x.get("file", ""), int(x.get("line", 0))))
    h = health(root) if mode in ("health", "all") else {}
    return {
        "version": VERSION,
        "mode": mode,
        "project_root": str(root),
        "summary": totals,
        "files": file_reports,
        "services": service_report,
        "top_remaining_candidates": remaining_all[:30],
        "health_summary": h,
        "json_report": str(REPORT_JSON),
        "md_report": str(REPORT_MD),
    }


def md_table(rows: list[dict[str, Any]], cols: list[tuple[str, str]]) -> str:
    if not rows:
        return "_Kayıt yok._\n"
    header = "| " + " | ".join(title for _, title in cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    out = [header, sep]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(key, "")).replace("|", "\\|") for key, _ in cols) + " |")
    return "\n".join(out) + "\n"


def write_reports(root: Path, report: dict[str, Any]) -> None:
    write_text(root / REPORT_JSON, json.dumps(report, ensure_ascii=False, indent=2))
    md: list[str] = []
    md.append(f"# BYS360 Mobile Refactor Closure Inventory P1.10 {VERSION}\n")
    md.append("Bu rapor uygulama dosyalarını değiştirmez. Mobil API refactor dalının kapanış envanterini çıkarır.\n")
    s = report["summary"]
    md.append("## Özet\n")
    for k in ["target_file_count", "total_lines", "total_functions", "total_route_decorators", "total_delegated_functions", "total_legacy_functions", "total_remaining_candidates", "total_possible_secret_hits"]:
        md.append(f"- {k}: {s.get(k)}")
    md.append("\n## Grup Dağılımı\n")
    group_rows = [{"group": k, "count": v} for k, v in s.get("group_totals", {}).items()]
    md.append(md_table(group_rows, [("group", "Grup"), ("count", "Fonksiyon")]))
    md.append("\n## Hedef Dosyalar\n")
    file_rows = []
    for r in report["files"]:
        file_rows.append({
            "path": r["path"], "kb": r["size_kb"], "lines": r["line_count"],
            "func": r["function_count"], "routes": r["route_decorator_count"],
            "delegated": r["delegated_count"], "legacy": r["legacy_count"],
            "remaining": len(r.get("remaining_candidates", [])), "syntax": r["syntax_ok"],
        })
    md.append(md_table(file_rows, [("path", "Yol"), ("kb", "KB"), ("lines", "Satır"), ("func", "Fonksiyon"), ("routes", "Route"), ("delegated", "Delegated"), ("legacy", "Legacy"), ("remaining", "Kalan Aday"), ("syntax", "Syntax")]))
    md.append("\n## Servis Omurgası\n")
    sv = report["services"]
    md.append(f"- service_root_exists: {sv.get('service_root_exists')}")
    md.append(f"- service_file_count: {sv.get('service_file_count')}")
    md.append(f"- total_delegate_functions: {sv.get('total_delegate_functions')}\n")
    md.append(md_table(sv.get("files", []), [("path", "Yol"), ("size_kb", "KB"), ("line_count", "Satır"), ("delegate_count", "Delegate"), ("syntax_ok", "Syntax")]))
    md.append("\n## Kalan Refactor Adayları İlk 30\n")
    md.append(md_table(report.get("top_remaining_candidates", []), [("file", "Dosya"), ("name", "Fonksiyon"), ("line", "Satır"), ("lines", "Uzunluk"), ("group", "Grup"), ("route_decorator", "Route"), ("delegated", "Delegated")]))
    md.append("\n## Önerilen Sonraki Sıra\n")
    md.append("1. Kalan adayları en küçük ve bağımlılığı en az gruptan ele al.\n")
    md.append("2. Survey tarafında önce neden rollback gerektiğini kod incelemesiyle netleştir; zorlamadan ilerle.\n")
    md.append("3. Performans route refactor'una geçmeden önce mobil smoke test listesini çalıştır.\n")
    md.append("4. Her mikro adım sonrası compileall ve create_app kontrolünü koru.\n")
    h = report.get("health_summary") or {}
    md.append("\n## Sağlık Kontrolü\n")
    if h:
        md.append(f"- compileall_ok: {h.get('compileall_ok')}\n")
        md.append(f"- app_factory_ok: {h.get('app_factory_ok')}\n")
        md.append(f"- overall_ok: {h.get('overall_ok')}\n")
    else:
        md.append("- Bu çalıştırmada sağlık kontrolü istenmedi.\n")
    write_text(root / REPORT_MD, "\n".join(md))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default="C:/bys360/project")
    parser.add_argument("--mode", choices=["audit", "health", "all"], default="audit")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    report = build_report(root, args.mode)
    write_reports(root, report)
    print(json.dumps({
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "summary": report.get("summary", {}),
        "health_summary": {k: v for k, v in (report.get("health_summary") or {}).items() if k in ("compileall_ok", "app_factory_ok", "overall_ok")},
        "json_report": str(REPORT_JSON),
        "md_report": str(REPORT_MD),
    }, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_REFACTOR_CLOSURE_INVENTORY_P1_10_V2_17_20_REPORT_OK")
    health_summary = report.get("health_summary") or {}
    if args.mode in ("health", "all"):
        if health_summary.get("overall_ok"):
            print("BYS360_MOBILE_REFACTOR_CLOSURE_INVENTORY_P1_10_V2_17_20_HEALTH_OK")
        else:
            print("BYS360_MOBILE_REFACTOR_CLOSURE_INVENTORY_P1_10_V2_17_20_HEALTH_FAIL")
            return 1
    print("BYS360_MOBILE_REFACTOR_CLOSURE_INVENTORY_P1_10_V2_17_20_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
