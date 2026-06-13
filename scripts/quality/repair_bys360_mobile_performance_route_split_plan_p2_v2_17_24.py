# -*- coding: utf-8 -*-
"""
BYS360 Mobile Performance Route Split Plan P2 V2.17.24
Kod değiştirmez. Mobil performans API route dosyasını refactor öncesi analiz eder.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

VERSION = "V2.17.24"
PATCH_MARKER = "BYS360_MOBILE_PERFORMANCE_ROUTE_SPLIT_PLAN_P2_V2_17_24"
TARGET = Path("app/api/mobile/performance_routes.py")
SECONDARY = Path("app/api/mobile/routes.py")

GROUP_RULES: List[Tuple[str, List[str]]] = [
    ("performance_tasks", ["task", "assignment", "score_submit", "score_action", "score_form"]),
    ("performance_periods", ["period", "in_period", "note", "interim"]),
    ("performance_evaluation", ["criteria", "weight", "score", "evaluation", "form_payload", "items_from_models"]),
    ("performance_summary", ["summary", "full_feature"]),
    ("performance_scorecard", ["scorecard", "card"]),
    ("performance_reports", ["report", "risk", "archive", "history"]),
    ("performance_approvals", ["approval", "president", "publish_preapproval"]),
]

@dataclass
class FunctionInfo:
    name: str
    line: int
    end_line: int
    length: int
    group: str
    delegated: bool
    legacy: bool
    route_decorator: bool
    args: str
    suggested_service: str


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def safe_read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def classify(name: str) -> str:
    low = name.lower()
    for group, keys in GROUP_RULES:
        if any(k in low for k in keys):
            return group
    return "performance_misc"


def suggested_service(group: str) -> str:
    mapping = {
        "performance_tasks": "app/api/mobile/services/performance_task_service.py",
        "performance_periods": "app/api/mobile/services/performance_period_service.py",
        "performance_evaluation": "app/api/mobile/services/performance_evaluation_service.py",
        "performance_summary": "app/api/mobile/services/performance_summary_service.py",
        "performance_scorecard": "app/api/mobile/services/performance_scorecard_service.py",
        "performance_reports": "app/api/mobile/services/performance_summary_service.py",
        "performance_approvals": "app/api/mobile/services/performance_summary_service.py",
        "performance_misc": "app/api/mobile/services/performance_misc_service.py",
    }
    return mapping.get(group, "app/api/mobile/services/performance_misc_service.py")


def decorator_text(dec: ast.AST, source: str) -> str:
    try:
        return ast.get_source_segment(source, dec) or ""
    except Exception:
        return ""


def has_route_decorator(node: ast.FunctionDef, source: str) -> bool:
    for dec in node.decorator_list:
        txt = decorator_text(dec, source)
        if "route(" in txt or ".route" in txt or "add_url_rule" in txt:
            return True
    return False


def is_delegated(node: ast.FunctionDef, source: str) -> bool:
    seg = ast.get_source_segment(source, node) or ""
    return "services." in seg or "_service." in seg or "delegate" in seg.lower() or "handle_" in seg


def analyze_file(path: Path, project_root: Path) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "exists": path.exists(), "path": rel(path, project_root), "size_kb": 0,
        "line_count": 0, "syntax_ok": False, "syntax_error": "", "functions": [],
        "group_counts": {}, "route_decorator_count": 0, "delegated_count": 0, "legacy_count": 0,
    }
    if not path.exists():
        return info
    text = safe_read(path)
    info["size_kb"] = round(path.stat().st_size / 1024, 1)
    info["line_count"] = text.count("\n") + 1
    try:
        tree = ast.parse(text, filename=str(path))
        info["syntax_ok"] = True
    except SyntaxError as e:
        info["syntax_error"] = f"{e.msg} at line {e.lineno}"
        return info
    funcs: List[FunctionInfo] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            end = getattr(node, "end_lineno", node.lineno)
            group = classify(node.name)
            fi = FunctionInfo(
                name=node.name,
                line=node.lineno,
                end_line=end,
                length=max(0, end - node.lineno + 1),
                group=group,
                delegated=is_delegated(node, text),
                legacy=node.name.startswith("_bys360_legacy_"),
                route_decorator=has_route_decorator(node, text),
                args=", ".join(a.arg for a in node.args.args),
                suggested_service=suggested_service(group),
            )
            funcs.append(fi)
    funcs.sort(key=lambda x: (x.line, x.name))
    info["functions"] = [asdict(f) for f in funcs]
    info["route_decorator_count"] = sum(1 for f in funcs if f.route_decorator)
    info["delegated_count"] = sum(1 for f in funcs if f.delegated)
    info["legacy_count"] = sum(1 for f in funcs if f.legacy)
    group_counts: Dict[str, int] = {}
    for f in funcs:
        group_counts[f.group] = group_counts.get(f.group, 0) + 1
    info["group_counts"] = dict(sorted(group_counts.items(), key=lambda kv: kv[1], reverse=True))
    return info


def possible_secret_hits(project_root: Path, files: List[Path]) -> List[Dict[str, Any]]:
    patterns = [
        re.compile(r"(?i)(password|passwd|secret|api[_-]?key|token|dsn|smtp_pass|jwt|private_key)\s*[:=]"),
        re.compile(r"(?i)(postgresql|mysql|redis)://[^\s'\"]+"),
    ]
    hits = []
    for path in files:
        if not path.exists():
            continue
        for i, line in enumerate(safe_read(path).splitlines(), 1):
            if any(p.search(line) for p in patterns):
                hits.append({"path": rel(path, project_root), "line": i, "kind": "possible_secret_or_config_key"})
    return hits[:200]


def run_cmd(project_root: Path, cmd: List[str], timeout: int = 90) -> Dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        proc = subprocess.run(cmd, cwd=str(project_root), env=env, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout)
        return {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout_tail": (proc.stdout or "")[-4000:], "stderr_tail": (proc.stderr or "")[-4000:]}
    except Exception as e:
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": repr(e)}


def health(project_root: Path) -> Dict[str, Any]:
    comp = run_cmd(project_root, [sys.executable, "-m", "compileall", "app", "config.py", "scripts"], timeout=180)
    factory_code = "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints), len(app.url_map._rules))"
    app = run_cmd(project_root, [sys.executable, "-c", factory_code], timeout=120)
    app_ok = app["ok"] and "BYS360_APP_CREATE_OK" in (app.get("stdout_tail") or "")
    return {"compileall_ok": comp["ok"], "app_factory_ok": app_ok, "overall_ok": comp["ok"] and app_ok, "compileall": comp, "app_factory": app}


def urlmap_probe(project_root: Path) -> Dict[str, Any]:
    code = """
from app import create_app
import json
app=create_app()
rows=[]
for r in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
    methods=sorted([m for m in r.methods if m not in {'HEAD','OPTIONS'}])
    if r.rule.startswith('/api/mobile/performance'):
        rows.append({'rule': r.rule, 'endpoint': r.endpoint, 'methods': methods, 'arguments': sorted(list(r.arguments))})
print(json.dumps({'ok': True, 'count': len(rows), 'rows': rows}, ensure_ascii=False))
"""
    res = run_cmd(project_root, [sys.executable, "-c", code], timeout=120)
    parsed = {"ok": False, "count": 0, "rows": [], "raw": res}
    if res["ok"]:
        try:
            lines = [ln for ln in (res.get("stdout_tail") or "").splitlines() if ln.strip().startswith("{")]
            parsed = json.loads(lines[-1]) if lines else parsed
        except Exception as e:
            parsed["parse_error"] = repr(e)
    return parsed


def make_plan(perf: Dict[str, Any]) -> Dict[str, Any]:
    funcs = [f for f in perf.get("functions", []) if not f.get("delegated") and not f.get("legacy")]
    funcs.sort(key=lambda f: f.get("length", 0), reverse=True)
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for f in funcs:
        groups.setdefault(f["group"], []).append(f)
    order = ["performance_summary", "performance_scorecard", "performance_periods", "performance_evaluation", "performance_tasks", "performance_reports", "performance_approvals", "performance_misc"]
    first = next((f for f in funcs if f["group"] in {"performance_summary", "performance_scorecard"}), funcs[0] if funcs else None)
    return {"remaining_count": len(funcs), "top_remaining": funcs[:40], "groups": {g: groups.get(g, []) for g in order if groups.get(g)}, "recommended_order": order, "first_micro_candidate": first}


def markdown(report: Dict[str, Any]) -> str:
    perf = report["performance_file"]; mobile = report["mobile_routes_file"]; plan = report["plan"]; urlmap = report["urlmap"]; h = report.get("health_summary", {})
    lines = [f"# BYS360 Mobile Performance Route Split Plan P2 {VERSION}\n", "Bu rapor uygulama dosyalarını değiştirmez. Mobil performans API refactor’una başlamadan önce URL haritası, fonksiyon grupları ve güvenli mikro adım planını çıkarır.\n"]
    lines += ["## Özet", f"- mode: {report['mode']}", f"- performance_file_exists: {perf.get('exists')}", f"- performance_file_kb: {perf.get('size_kb')}", f"- performance_line_count: {perf.get('line_count')}", f"- performance_function_count: {len(perf.get('functions', []))}", f"- performance_delegated_count: {perf.get('delegated_count')}", f"- performance_legacy_count: {perf.get('legacy_count')}", f"- performance_urlmap_count: {urlmap.get('count', 0)}", f"- remaining_refactor_candidate_count: {plan.get('remaining_count', 0)}", f"- possible_secret_hit_count: {len(report.get('possible_secret_hits', []))}"]
    if h:
        lines += [f"- compileall_ok: {h.get('compileall_ok')}", f"- app_factory_ok: {h.get('app_factory_ok')}", f"- overall_ok: {h.get('overall_ok')}"]
    lines.append("")
    lines += ["## Dosya Özeti", "| Dosya | KB | Satır | Fonksiyon | Delegated | Legacy | Syntax |", "|---|---:|---:|---:|---:|---:|---|"]
    for d in [mobile, perf]:
        lines.append(f"| `{d.get('path')}` | {d.get('size_kb')} | {d.get('line_count')} | {len(d.get('functions', []))} | {d.get('delegated_count')} | {d.get('legacy_count')} | {d.get('syntax_ok')} |")
    lines += ["", "## Performans Fonksiyon Grup Dağılımı", "| Grup | Fonksiyon |", "|---|---:|"]
    for g, c in perf.get("group_counts", {}).items(): lines.append(f"| {g} | {c} |")
    lines += ["", "## Flask URLMap Performans Endpointleri", f"- count: {urlmap.get('count', 0)}", "| Method | Rule | Endpoint | Arg |", "|---|---|---|---|"]
    for r in urlmap.get("rows", [])[:120]:
        lines.append(f"| {','.join(r.get('methods', []))} | `{r.get('rule')}` | `{r.get('endpoint')}` | `{', '.join(r.get('arguments', []))}` |")
    lines += ["", "## Kalan Büyük Performans Adayları İlk 40", "| Fonksiyon | Satır | Uzunluk | Grup | Önerilen servis |", "|---|---:|---:|---|---|"]
    for f in plan.get("top_remaining", [])[:40]: lines.append(f"| `{f['name']}` | {f['line']} | {f['length']} | {f['group']} | `{f['suggested_service']}` |")
    first = plan.get("first_micro_candidate")
    lines += ["", "## Önerilen P2 Mikro Sıra", "1. Önce yalnızca okuma/özet üreten performans fonksiyonlarını servis delegasyonuna al.", "2. Puan gönderme, iade/ret, yayın/onay gibi işlem yapan endpointlere hemen dokunma.", "3. Route URL, endpoint ve blueprint adını kesinlikle değiştirme.", "4. Her mikro adım sonrası `compileall`, `create_app` ve mobil performance safe GET smoke testi çalıştır."]
    if first: lines.append(f"5. İlk mikro aday: `{first['name']}` → `{first['suggested_service']}`")
    lines += ["", "## Olası Secret / Config Sinyalleri", "Değerler rapora yazılmaz; sadece konum verilir.", "| Dosya | Satır | Tür |", "|---|---:|---|"]
    if report.get("possible_secret_hits"):
        for hit in report.get("possible_secret_hits", [])[:50]: lines.append(f"| `{hit['path']}` | {hit['line']} | {hit['kind']} |")
    else: lines.append("| - | - | - |")
    lines += ["", "## Sağlık Kontrolü"]
    if h: lines += [f"- compileall_ok: {h.get('compileall_ok')}", f"- app_factory_ok: {h.get('app_factory_ok')}", f"- overall_ok: {h.get('overall_ok')}"]
    else: lines.append("- Sağlık kontrolü bu modda çalıştırılmadı.")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--project-root", required=True); ap.add_argument("--mode", default="audit", choices=["audit", "all", "health"]); args = ap.parse_args()
    project_root = Path(args.project_root).resolve(); reports = project_root / "reports" / "quality"; reports.mkdir(parents=True, exist_ok=True)
    perf_path = project_root / TARGET; mobile_path = project_root / SECONDARY
    perf = analyze_file(perf_path, project_root); mobile = analyze_file(mobile_path, project_root)
    urlmap = urlmap_probe(project_root) if args.mode in {"audit", "all"} else {"ok": None, "count": 0, "rows": []}
    plan = make_plan(perf); secrets = possible_secret_hits(project_root, [perf_path, mobile_path]); hs = health(project_root) if args.mode in {"all", "health"} else {}
    report = {"version": VERSION, "mode": args.mode, "project_root": str(project_root), "performance_file": perf, "mobile_routes_file": mobile, "urlmap": urlmap, "plan": plan, "possible_secret_hits": secrets, "health_summary": hs}
    json_path = reports / "bys360_mobile_performance_route_split_plan_p2_v2_17_24_report.json"; md_path = reports / "bys360_mobile_performance_route_split_plan_p2_v2_17_24_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"); md_path.write_text(markdown(report), encoding="utf-8")
    summary = {"version": VERSION, "mode": args.mode, "performance_function_count": len(perf.get("functions", [])), "performance_urlmap_count": urlmap.get("count", 0), "remaining_count": plan.get("remaining_count", 0), "first_micro_candidate": plan.get("first_micro_candidate"), "compileall_ok": hs.get("compileall_ok") if hs else None, "app_factory_ok": hs.get("app_factory_ok") if hs else None, "overall_ok": hs.get("overall_ok") if hs else None, "json_report": rel(json_path, project_root), "md_report": rel(md_path, project_root)}
    print(json.dumps(summary, ensure_ascii=False, indent=2)); print(f"{PATCH_MARKER}_REPORT_OK")
    if args.mode in {"all", "health"}:
        if hs.get("overall_ok"): print(f"{PATCH_MARKER}_HEALTH_OK")
        else: print(f"{PATCH_MARKER}_HEALTH_FAIL"); return 1
    print(f"{PATCH_MARKER}_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
