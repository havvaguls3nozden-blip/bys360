# -*- coding: utf-8 -*-
"""BYS360 Mobile Performance Refactor Closure P2.7 V2.17.32

Kod degistirmez. P2 performans mobil API servis delegasyonu sonrasi kapanis envanteri,
URL haritasi ve saglik kontrolu uretir.
"""
from __future__ import annotations

import argparse
import ast
import json
import py_compile
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

VERSION = "V2.17.32"
TAG = "BYS360_MOBILE_PERFORMANCE_REFACTOR_CLOSURE_P2_7_V2_17_32"
REPORT_JSON_REL = Path("reports/quality/bys360_mobile_performance_refactor_closure_p2_7_v2_17_32_report.json")
REPORT_MD_REL = Path("reports/quality/bys360_mobile_performance_refactor_closure_p2_7_v2_17_32_report.md")
TARGET_FILES = [
    Path("app/api/mobile/routes.py"),
    Path("app/api/mobile/performance_routes.py"),
]
SERVICE_FILES = [
    Path("app/api/mobile/services/performance_summary_service.py"),
    Path("app/api/mobile/services/performance_task_service.py"),
    Path("app/api/mobile/services/performance_period_service.py"),
    Path("app/api/mobile/services/performance_evaluation_service.py"),
    Path("app/api/mobile/services/performance_scorecard_service.py"),
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def compile_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "file_not_found"}
    try:
        py_compile.compile(str(path), doraise=True)
        return {"exists": True, "ok": True, "error": ""}
    except Exception as exc:  # noqa: BLE001
        return {"exists": True, "ok": False, "error": str(exc)}


def run_cmd(root: Path, args: List[str], timeout: int = 180) -> Dict[str, Any]:
    try:
        cp = subprocess.run(
            args,
            cwd=str(root),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
        )
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout_tail": (cp.stdout or "")[-5000:],
            "stderr_tail": (cp.stderr or "")[-5000:],
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": repr(exc)}


def health(root: Path) -> Dict[str, Any]:
    compileall = run_cmd(root, [sys.executable, "-m", "compileall", "app", "config.py", "scripts"], timeout=240)
    app_factory = run_cmd(
        root,
        [sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"],
        timeout=240,
    )
    return {
        "compileall_ok": bool(compileall.get("ok")),
        "app_factory_ok": bool(app_factory.get("ok")) and "BYS360_APP_CREATE_OK" in (app_factory.get("stdout_tail") or ""),
        "overall_ok": bool(compileall.get("ok")) and bool(app_factory.get("ok")) and "BYS360_APP_CREATE_OK" in (app_factory.get("stdout_tail") or ""),
        "compileall": compileall,
        "app_factory": app_factory,
    }


@dataclass
class FuncRow:
    file: str
    name: str
    line: int
    length: int
    group: str
    delegated: bool
    legacy: bool
    route_decorator: bool
    likely_write: bool


def group_for(name: str) -> str:
    n = name.lower()
    if "score" in n or "task" in n or "assignment" in n or "return" in n or "withdraw" in n:
        return "performance_tasks"
    if "period" in n or "note" in n or "interim" in n:
        return "performance_periods"
    if "criteria" in n or "weight" in n or "form" in n or "evaluation" in n:
        return "performance_evaluation"
    if "summary" in n or "report" in n or "risk" in n or "archive" in n or "suggestion" in n:
        return "performance_summary_reports"
    if "approval" in n or "publish" in n or "president" in n:
        return "performance_approvals"
    return "performance_misc"


def is_likely_write(name: str) -> bool:
    n = name.lower()
    return any(k in n for k in ["submit", "create", "add", "post", "reply", "send", "mark", "action", "publish", "approval", "approve", "return", "withdraw", "delete", "update"])


def is_delegated(src: str, name: str) -> bool:
    if name.startswith("_bys360_legacy_"):
        return False
    markers = [
        "app.api.mobile.services",
        "_service.",
        "delegate_",
        f"{name}_delegate",
        "performance_summary_service",
        "performance_task_service",
        "performance_period_service",
        "performance_evaluation_service",
    ]
    return any(m in src for m in markers)


def has_route_decorator(node: ast.AST) -> bool:
    decorators = getattr(node, "decorator_list", [])
    for dec in decorators:
        s = ast.unparse(dec) if hasattr(ast, "unparse") else ""
        if ".route" in s or "route(" in s or "mobile_api" in s:
            return True
    return False


def analyze_file(root: Path, rel: Path) -> Dict[str, Any]:
    path = root / rel
    row: Dict[str, Any] = {
        "path": str(rel).replace("\\", "/"),
        "exists": path.exists(),
        "kb": 0.0,
        "line_count": 0,
        "function_count": 0,
        "delegated_count": 0,
        "legacy_count": 0,
        "remaining_candidate_count": 0,
        "syntax": compile_file(path),
        "functions": [],
    }
    if not path.exists():
        return row
    text = read_text(path)
    lines = text.splitlines()
    row["kb"] = round(path.stat().st_size / 1024, 1)
    row["line_count"] = len(lines)
    try:
        tree = ast.parse(text)
    except Exception as exc:  # noqa: BLE001
        row["parse_error"] = str(exc)
        return row
    funcs: List[FuncRow] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = getattr(node, "lineno", 0)
            end = getattr(node, "end_lineno", start)
            src = "\n".join(lines[max(start - 1, 0):end])
            legacy = node.name.startswith("_bys360_legacy_")
            delegated = is_delegated(src, node.name)
            # candidate: public or helper performance/mobile function, not legacy, not already delegated
            name_l = node.name.lower()
            candidate = ("performance" in name_l or node.name.startswith("_v") or node.name in {"_label", "_period_scope", "_period_progress", "_assignment_item"}) and not legacy and not delegated
            funcs.append(FuncRow(
                file=str(rel).replace("\\", "/"),
                name=node.name,
                line=start,
                length=max(end - start + 1, 1),
                group=group_for(node.name),
                delegated=delegated,
                legacy=legacy,
                route_decorator=has_route_decorator(node),
                likely_write=is_likely_write(node.name),
            ))
    row["functions"] = [asdict(f) for f in funcs]
    row["function_count"] = len(funcs)
    row["delegated_count"] = sum(1 for f in funcs if f.delegated)
    row["legacy_count"] = sum(1 for f in funcs if f.legacy)
    row["remaining_candidate_count"] = sum(1 for f in funcs if ("performance" in f.name.lower() or f.name.startswith("_v") or f.name in {"_label", "_period_scope", "_period_progress", "_assignment_item"}) and not f.legacy and not f.delegated)
    return row


def analyze_services(root: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rel in SERVICE_FILES:
        path = root / rel
        item = {
            "path": str(rel).replace("\\", "/"),
            "exists": path.exists(),
            "kb": 0.0,
            "line_count": 0,
            "delegate_count": 0,
            "syntax": compile_file(path),
        }
        if path.exists():
            text = read_text(path)
            item["kb"] = round(path.stat().st_size / 1024, 1)
            item["line_count"] = len(text.splitlines())
            item["delegate_count"] = text.count("def ")
        out.append(item)
    return out


def urlmap_probe(root: Path) -> Dict[str, Any]:
    code = r'''
import json
from app import create_app
app=create_app()
rows=[]
for r in sorted(app.url_map.iter_rules(), key=lambda x: str(x.rule)):
    methods=sorted([m for m in r.methods if m not in {"HEAD","OPTIONS"}])
    if str(r.rule).startswith('/api/mobile/performance'):
        rows.append({"rule": str(r.rule), "endpoint": r.endpoint, "methods": methods, "arguments": sorted(list(r.arguments))})
print(json.dumps({"ok": True, "rows": rows, "count": len(rows)}, ensure_ascii=False))
'''
    res = run_cmd(root, [sys.executable, "-c", code], timeout=240)
    data: Dict[str, Any] = {"ok": False, "count": 0, "rows": [], "raw": res}
    if res.get("ok"):
        stdout = res.get("stdout_tail") or ""
        # last JSON object line
        for line in reversed(stdout.splitlines()):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    parsed = json.loads(line)
                    data.update(parsed)
                    data["ok"] = bool(parsed.get("ok"))
                    break
                except Exception:
                    continue
    return data


def build_report(root: Path, mode: str) -> Dict[str, Any]:
    files = [analyze_file(root, rel) for rel in TARGET_FILES]
    services = analyze_services(root)
    all_funcs: List[Dict[str, Any]] = []
    for f in files:
        all_funcs.extend(f.get("functions", []))
    remaining = [f for f in all_funcs if ("performance" in f["name"].lower() or f["name"].startswith("_v") or f["name"] in {"_label", "_period_scope", "_period_progress", "_assignment_item"}) and not f["legacy"] and not f["delegated"]]
    remaining_sorted = sorted(remaining, key=lambda x: x["length"], reverse=True)
    delegated = [f for f in all_funcs if f["delegated"]]
    legacy = [f for f in all_funcs if f["legacy"]]
    urlmap = urlmap_probe(root)
    h = health(root)
    group_counts: Dict[str, int] = {}
    remaining_read_only: List[Dict[str, Any]] = []
    remaining_write_like: List[Dict[str, Any]] = []
    for f in remaining:
        group_counts[f["group"]] = group_counts.get(f["group"], 0) + 1
        if f["likely_write"]:
            remaining_write_like.append(f)
        else:
            remaining_read_only.append(f)
    return {
        "version": VERSION,
        "mode": mode,
        "project_root": str(root),
        "summary": {
            "target_file_count": len(files),
            "total_functions": len(all_funcs),
            "delegated_functions": len(delegated),
            "legacy_functions": len(legacy),
            "remaining_candidates": len(remaining),
            "remaining_read_only_like": len(remaining_read_only),
            "remaining_write_like": len(remaining_write_like),
            "performance_urlmap_count": int(urlmap.get("count") or 0),
            "service_file_count": sum(1 for s in services if s["exists"]),
            "service_delegate_function_count": sum(int(s.get("delegate_count") or 0) for s in services),
            "compileall_ok": h["compileall_ok"],
            "app_factory_ok": h["app_factory_ok"],
            "overall_ok": h["overall_ok"],
        },
        "files": files,
        "services": services,
        "urlmap": urlmap,
        "group_counts": dict(sorted(group_counts.items(), key=lambda kv: kv[1], reverse=True)),
        "delegated_top": sorted(delegated, key=lambda x: x["line"])[:80],
        "legacy_top": sorted(legacy, key=lambda x: x["length"], reverse=True)[:30],
        "remaining_top": remaining_sorted[:40],
        "remaining_read_only_like_top": sorted(remaining_read_only, key=lambda x: x["length"], reverse=True)[:30],
        "remaining_write_like_top": sorted(remaining_write_like, key=lambda x: x["length"], reverse=True)[:30],
        "health_summary": h,
    }


def md_table(headers: List[str], rows: List[List[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(x).replace("\n", " ") for x in r) + " |")
    return "\n".join(lines)


def write_reports(root: Path, report: Dict[str, Any]) -> None:
    json_path = root / REPORT_JSON_REL
    md_path = root / REPORT_MD_REL
    write_text(json_path, json.dumps(report, ensure_ascii=False, indent=2))
    s = report["summary"]
    lines: List[str] = []
    lines.append("# BYS360 Mobile Performance Refactor Closure P2.7 V2.17.32")
    lines.append("")
    lines.append("Bu rapor uygulama dosyalarını değiştirmez. P2 performans mobil API delegasyon dalının kapanış envanterini çıkarır.")
    lines.append("")
    lines.append("## Özet")
    for k, v in s.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Hedef Dosyalar")
    lines.append(md_table(["Dosya", "KB", "Satır", "Fonksiyon", "Delegated", "Legacy", "Kalan Aday", "Syntax"], [
        [f["path"], f["kb"], f["line_count"], f["function_count"], f["delegated_count"], f["legacy_count"], f["remaining_candidate_count"], f["syntax"].get("ok")]
        for f in report["files"]
    ]))
    lines.append("")
    lines.append("## Performans URLMap")
    lines.append(f"- count: {report['urlmap'].get('count', 0)}")
    lines.append(md_table(["Method", "Rule", "Endpoint", "Arg"], [
        [",".join(r.get("methods", [])), r.get("rule", ""), r.get("endpoint", ""), ",".join(r.get("arguments", []))]
        for r in report["urlmap"].get("rows", [])[:80]
    ]))
    lines.append("")
    lines.append("## Servis Dosyaları")
    lines.append(md_table(["Dosya", "KB", "Satır", "Def", "Syntax"], [
        [x["path"], x["kb"], x["line_count"], x["delegate_count"], x["syntax"].get("ok")]
        for x in report["services"]
    ]))
    lines.append("")
    lines.append("## Kalan Aday Grup Dağılımı")
    if report["group_counts"]:
        lines.append(md_table(["Grup", "Adet"], [[k, v] for k, v in report["group_counts"].items()]))
    else:
        lines.append("Kalan aday bulunmadı.")
    lines.append("")
    lines.append("## Kalan Büyük Adaylar İlk 40")
    lines.append(md_table(["Dosya", "Fonksiyon", "Satır", "Uzunluk", "Grup", "Write-like"], [
        [f["file"], f["name"], f["line"], f["length"], f["group"], f["likely_write"]]
        for f in report["remaining_top"]
    ]))
    lines.append("")
    lines.append("## Kalan Okuma Benzeri Güvenli Adaylar")
    lines.append(md_table(["Dosya", "Fonksiyon", "Satır", "Uzunluk", "Grup"], [
        [f["file"], f["name"], f["line"], f["length"], f["group"]]
        for f in report["remaining_read_only_like_top"]
    ]))
    lines.append("")
    lines.append("## İşlem Yapan / Daha Riskli Adaylar")
    lines.append(md_table(["Dosya", "Fonksiyon", "Satır", "Uzunluk", "Grup"], [
        [f["file"], f["name"], f["line"], f["length"], f["group"]]
        for f in report["remaining_write_like_top"]
    ]))
    lines.append("")
    lines.append("## Legacy Gövdeler İlk 30")
    lines.append(md_table(["Dosya", "Fonksiyon", "Satır", "Uzunluk"], [
        [f["file"], f["name"], f["line"], f["length"]]
        for f in report["legacy_top"]
    ]))
    lines.append("")
    lines.append("## Öneri")
    lines.append("P2 okuma/özet/rapor delegasyon dalı sağlıklı görünüyorsa bu noktada mobil performans smoke test yapılmalı. Puan gönderme, iade/ret, yayın/onay ve not oluşturma gibi yazma işlemleri ayrı P3 dalı olarak ele alınmalıdır. Legacy gövdeler ise en az bir smoke test turundan sonra ayrı temizlik paketinde azaltılmalıdır.")
    lines.append("")
    lines.append("## Sağlık Kontrolü")
    lines.append(f"- compileall_ok: {s['compileall_ok']}")
    lines.append(f"- app_factory_ok: {s['app_factory_ok']}")
    lines.append(f"- overall_ok: {s['overall_ok']}")
    write_text(md_path, "\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "all", "health"], default="all")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    report = build_report(root, args.mode)
    write_reports(root, report)
    print(json.dumps({
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "summary": report["summary"],
        "json_report": str(REPORT_JSON_REL),
        "md_report": str(REPORT_MD_REL),
    }, ensure_ascii=False, indent=2))
    print(f"{TAG}_REPORT_OK")
    if report["summary"].get("overall_ok"):
        print(f"{TAG}_HEALTH_OK")
        print(f"{TAG}_OK")
        return 0
    print(f"{TAG}_HEALTH_FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
