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
from typing import Any

VERSION = "V2.17.43"
SLUG = "bys360_mobile_performance_p3_helper_closure_smoke_v2_17_43"

REFACTORED_HELPER_TARGETS = [
    "_v2835_score_form_payload",
    "_v2837_action_capabilities",
    "_v2837_find_return_target",
    "_v2837_return_assignment",
    "_v2837_withdraw_assignment",
    "_v2853_note_type_label",
    "_v2853_note_bool",
    "mobile_performance_in_period_notes",
    "mobile_performance_in_period_notes_v2853",
    "mobile_performance_note_scorecard_v2863a",
    "mobile_performance_period_detail",
    "_period_progress",
]

WRITE_ENDPOINT_TARGETS = [
    "mobile_performance_create_in_period_note_v2853",
    "mobile_performance_task_score_action",
    "mobile_performance_task_score_submit",
]

SENSITIVE_WRITE_TARGETS = [
    "mobile_performance_task_score_submit",
    "mobile_performance_task_score_action",
    "mobile_performance_create_in_period_note_v2853",
    "mobile_performance_publish_preapproval",
    "mobile_performance_approvals",
    "mobile_performance_president_approvals_alias",
]

SERVICE_FILES = [
    "app/api/mobile/services/performance_task_service.py",
    "app/api/mobile/services/performance_period_service.py",
    "app/api/mobile/services/performance_summary_service.py",
    "app/api/mobile/services/performance_evaluation_service.py",
    "app/api/mobile/services/performance_scorecard_service.py",
]


def run_cmd(args: list[str], cwd: Path, timeout: int = 90) -> dict[str, Any]:
    try:
        cp = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
        )
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout_tail": cp.stdout[-6000:],
            "stderr_tail": cp.stderr[-6000:],
        }
    except Exception as exc:
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": repr(exc)}


def compile_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "file not found"}
    try:
        ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
        return {"exists": True, "ok": True, "error": ""}
    except SyntaxError as exc:
        return {"exists": True, "ok": False, "error": f"{exc.msg} at line {exc.lineno}"}
    except Exception as exc:
        return {"exists": True, "ok": False, "error": repr(exc)}


def function_index(path: Path) -> tuple[dict[str, dict[str, Any]], str]:
    if not path.exists():
        return {}, "file not found"
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        return {}, f"{exc.msg} at line {exc.lineno}"
    lines = text.splitlines()
    out: dict[str, dict[str, Any]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            end = getattr(node, "end_lineno", node.lineno)
            body_text = "\n".join(lines[node.lineno - 1:end])
            delegated = any(s in body_text for s in [
                "performance_task_service",
                "performance_period_service",
                "performance_summary_service",
                "performance_evaluation_service",
                "delegate_",
                "handle_",
                "return _service.",
                "return service.",
            ])
            out[node.name] = {
                "name": node.name,
                "line": node.lineno,
                "end_line": end,
                "length": max(0, end - node.lineno + 1),
                "delegated": delegated,
                "legacy": node.name.startswith("_bys360_legacy_"),
                "arg": ", ".join(a.arg for a in node.args.args),
            }
    return out, ""


def get_urlmap(root: Path) -> dict[str, Any]:
    code = r'''
import json
from app import create_app
app = create_app()
rows = []
for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r)):
    methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
    for method in methods:
        rows.append({
            "method": method,
            "rule": str(rule),
            "endpoint": rule.endpoint,
            "arguments": sorted(rule.arguments),
        })
print(json.dumps({"ok": True, "rows": rows}, ensure_ascii=False))
'''
    cp = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(root),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=90,
    )
    if cp.returncode != 0:
        return {"ok": False, "rows": [], "error": cp.stderr[-4000:]}
    # stdout may include logs before json; take last json-looking line
    for line in reversed(cp.stdout.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except Exception:
                pass
    return {"ok": False, "rows": [], "error": "json output not found", "stdout_tail": cp.stdout[-4000:], "stderr_tail": cp.stderr[-4000:]}


def route_to_test_path(rule: str) -> str:
    # Replace Flask converters with safe numeric/string sample values.
    s = rule
    s = re.sub(r"<int:([^>]+)>", "1", s)
    s = re.sub(r"<string:([^>]+)>", "sample", s)
    s = re.sub(r"<uuid:([^>]+)>", "00000000-0000-0000-0000-000000000000", s)
    s = re.sub(r"<path:([^>]+)>", "sample", s)
    s = re.sub(r"<([^>]+)>", "1", s)
    return s


def options_dryrun(root: Path, rules: list[dict[str, Any]]) -> dict[str, Any]:
    payload = json.dumps(rules, ensure_ascii=False)
    code = r'''
import json, sys
from app import create_app
app = create_app()
rules = json.loads(sys.stdin.read() or "[]")
results = []
with app.test_client() as client:
    for row in rules:
        path = row.get("test_path") or row.get("rule")
        try:
            resp = client.open(path, method="OPTIONS")
            status = int(resp.status_code)
            ok = status < 500
            note = "OPTIONS dry-run; gercek yazma metodu calistirilmadi."
        except Exception as exc:
            status = -1
            ok = False
            note = repr(exc)
        results.append({**row, "status": status, "ok": ok, "note": note})
print(json.dumps({"ok": all(r["ok"] for r in results), "results": results}, ensure_ascii=False))
'''
    cp = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(root),
        input=payload,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )
    if cp.returncode != 0:
        return {"ok": False, "results": [], "error": cp.stderr[-4000:]}
    for line in reversed(cp.stdout.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except Exception:
                pass
    return {"ok": False, "results": [], "error": "json output not found", "stdout_tail": cp.stdout[-4000:]}


def make_md(report: dict[str, Any]) -> str:
    lines: list[str] = []
    s = report["summary"]
    lines.append(f"# BYS360 Mobile Performance P3 Helper Closure Smoke {VERSION}")
    lines.append("")
    lines.append("Bu rapor uygulama dosyalarini degistirmez. P3 helper delegasyon dalinin kapanis envanterini ve yazma endpointleri icin guvenli OPTIONS dry-run sonucunu cikarir.")
    lines.append("")
    lines.append("## Ozet")
    for k, v in s.items():
        lines.append(f"- {k}: {v}")
    lines.append("")

    lines.append("## P3 Refactor Helper Hedefleri")
    lines.append("| Fonksiyon | Var | Satir | Uzunluk | Delegated | Legacy | Arg |")
    lines.append("|---|---:|---:|---:|---:|---:|---|")
    for row in report["refactored_helpers"]:
        lines.append(f"| `{row['name']}` | {row['exists']} | {row.get('line','')} | {row.get('length','')} | {row.get('delegated','')} | {row.get('legacy','')} | `{row.get('arg','')}` |")
    lines.append("")

    lines.append("## Yazma Endpointleri OPTIONS Dry-run")
    lines.append("Gercek POST/PUT/PATCH/DELETE cagrisi yapilmaz; sadece route seviyesinde 5xx/exception kontrolu icin OPTIONS kullanilir.")
    lines.append("")
    lines.append("| Method | Rule | Endpoint | Status | OK | Not |")
    lines.append("|---|---|---|---:|---|---|")
    for row in report["options_dryrun"].get("results", []):
        lines.append(f"| {row.get('method','')} | `{row.get('rule','')}` | `{row.get('endpoint','')}` | {row.get('status','')} | {row.get('ok','')} | {row.get('note','')} |")
    lines.append("")

    lines.append("## Hala Dokunulmamasi Onerilen Hassas Fonksiyonlar")
    lines.append("| Fonksiyon | Var | Satir | Uzunluk | Delegated | Legacy | Arg |")
    lines.append("|---|---:|---:|---:|---:|---:|---|")
    for row in report["sensitive_targets"]:
        lines.append(f"| `{row['name']}` | {row['exists']} | {row.get('line','')} | {row.get('length','')} | {row.get('delegated','')} | {row.get('legacy','')} | `{row.get('arg','')}` |")
    lines.append("")

    lines.append("## Servis Dosyalari")
    lines.append("| Dosya | Var | KB | Fonksiyon | Syntax |")
    lines.append("|---|---:|---:|---:|---|")
    for row in report["service_files"]:
        lines.append(f"| `{row['path']}` | {row['exists']} | {row.get('kb','')} | {row.get('function_count','')} | {row.get('syntax_ok','')} |")
    lines.append("")

    lines.append("## Saglik Kontrolu")
    h = report["health_summary"]
    lines.append(f"- compileall_ok: {h.get('compileall_ok')}")
    lines.append(f"- app_factory_ok: {h.get('app_factory_ok')}")
    lines.append(f"- overall_ok: {h.get('overall_ok')}")
    lines.append("")
    lines.append("## Oneri")
    lines.append("P3 helper delegasyonlari saglikli gorunuyorsa bir sonraki adim gercek POST fonksiyonlarini degil, once yetkili mobil kullanici ile login + performans GET smoke turunu calistirmaktir. Puan gonderme ve score-action endpointleri ayrica tokenli smoke ve rollback paketiyle ele alinmalidir.")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=os.getcwd())
    ap.add_argument("--mode", default="all", choices=["audit", "health", "all"])
    args = ap.parse_args()
    root = Path(args.project_root).resolve()
    reports = root / "reports" / "quality"
    reports.mkdir(parents=True, exist_ok=True)

    perf_path = root / "app" / "api" / "mobile" / "performance_routes.py"
    funcs, parse_error = function_index(perf_path)

    refactored_helpers = []
    for name in REFACTORED_HELPER_TARGETS:
        row = funcs.get(name, {"name": name})
        refactored_helpers.append({"exists": name in funcs, **row})

    sensitive_targets = []
    for name in SENSITIVE_WRITE_TARGETS:
        row = funcs.get(name, {"name": name})
        sensitive_targets.append({"exists": name in funcs, **row})

    service_rows = []
    for rel in SERVICE_FILES:
        path = root / rel
        idx, err = function_index(path)
        syntax = compile_file(path)
        service_rows.append({
            "path": rel,
            "exists": path.exists(),
            "kb": round(path.stat().st_size / 1024, 1) if path.exists() else 0,
            "function_count": len(idx),
            "syntax_ok": syntax.get("ok"),
            "syntax_error": syntax.get("error"),
        })

    urlmap = {"ok": False, "rows": []}
    write_rules: list[dict[str, Any]] = []
    opt = {"ok": True, "results": []}
    if args.mode in {"audit", "all", "health"}:
        urlmap = get_urlmap(root)
        if urlmap.get("ok"):
            for row in urlmap.get("rows", []):
                if row.get("rule", "").startswith("/api/mobile/performance") and row.get("method") in {"POST", "PUT", "PATCH", "DELETE"}:
                    row = dict(row)
                    row["test_path"] = route_to_test_path(row["rule"])
                    write_rules.append(row)
    if args.mode in {"all", "health"} and write_rules:
        opt = options_dryrun(root, write_rules)

    compileall = {"ok": None}
    app_factory = {"ok": None}
    if args.mode in {"all", "health"}:
        compileall = run_cmd([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], root, timeout=180)
        app_factory = run_cmd([sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"], root, timeout=120)

    health = {
        "compileall_ok": bool(compileall.get("ok")) if args.mode in {"all", "health"} else None,
        "app_factory_ok": bool(app_factory.get("ok")) if args.mode in {"all", "health"} else None,
    }
    health["overall_ok"] = (health["compileall_ok"] is not False) and (health["app_factory_ok"] is not False) and (opt.get("ok") is not False)

    delegated_refactored = sum(1 for r in refactored_helpers if r.get("delegated"))
    missing_refactored = [r["name"] for r in refactored_helpers if not r.get("exists")]
    not_delegated_refactored = [r["name"] for r in refactored_helpers if r.get("exists") and not r.get("delegated")]
    summary = {
        "mode": args.mode,
        "performance_file_exists": perf_path.exists(),
        "performance_parse_error": parse_error,
        "performance_function_count": len(funcs),
        "refactored_helper_target_count": len(REFACTORED_HELPER_TARGETS),
        "refactored_helper_delegated_count": delegated_refactored,
        "refactored_helper_missing_count": len(missing_refactored),
        "refactored_helper_not_delegated_count": len(not_delegated_refactored),
        "urlmap_ok": bool(urlmap.get("ok")),
        "performance_write_rule_count": len(write_rules),
        "options_dryrun_count": len(opt.get("results", [])),
        "options_dryrun_ok_count": sum(1 for r in opt.get("results", []) if r.get("ok")),
        "options_server_error_count": sum(1 for r in opt.get("results", []) if isinstance(r.get("status"), int) and r.get("status", 0) >= 500),
        "service_file_count": len(service_rows),
        **health,
    }

    report = {
        "version": VERSION,
        "summary": summary,
        "performance_file_compile": compile_file(perf_path),
        "refactored_helpers": refactored_helpers,
        "missing_refactored_helpers": missing_refactored,
        "not_delegated_refactored_helpers": not_delegated_refactored,
        "sensitive_targets": sensitive_targets,
        "write_rules": write_rules,
        "options_dryrun": opt,
        "service_files": service_rows,
        "health_summary": health,
        "compileall": compileall,
        "app_factory": app_factory,
    }

    json_path = reports / f"{SLUG}_report.json"
    md_path = reports / f"{SLUG}_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(make_md(report), encoding="utf-8")

    print(json.dumps({
        "version": VERSION,
        "mode": args.mode,
        "summary": summary,
        "json_report": str(json_path.relative_to(root)),
        "md_report": str(md_path.relative_to(root)),
    }, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_PERFORMANCE_P3_HELPER_CLOSURE_SMOKE_V2_17_43_REPORT_OK")
    if args.mode in {"all", "health"} and health["overall_ok"]:
        print("BYS360_MOBILE_PERFORMANCE_P3_HELPER_CLOSURE_SMOKE_V2_17_43_HEALTH_OK")
    print("BYS360_MOBILE_PERFORMANCE_P3_HELPER_CLOSURE_SMOKE_V2_17_43_OK")
    print("Rapor dosyalari:")
    print(f"- {md_path.relative_to(root)}")
    print(f"- {json_path.relative_to(root)}")
    return 0 if health["overall_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
