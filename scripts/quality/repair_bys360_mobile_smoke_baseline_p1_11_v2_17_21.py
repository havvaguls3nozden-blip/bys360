# -*- coding: utf-8 -*-
"""
BYS360 Mobile Smoke Baseline P1.11 V2.17.21
- Uygulama dosyalarını değiştirmez.
- Mobil API route/refactor kapanışı sonrası URL haritası ve güvenli sağlık temelini çıkarır.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

VERSION = "V2.17.21"
SLUG = "bys360_mobile_smoke_baseline_p1_11_v2_17_21"
MARKER_JSON = "__BYS360_JSON__"

EXCLUDED_DIR_NAMES = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", "build", "dist", "_local_quarantine", "reports", ".idea", ".vscode",
}


def rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")


def should_skip(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except Exception:
        parts = path.parts
    return any(part in EXCLUDED_DIR_NAMES for part in parts)


def run_cmd(cmd: List[str], cwd: Path, timeout: int = 120) -> Dict[str, Any]:
    try:
        cp = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout_tail": (cp.stdout or "")[-6000:],
            "stderr_tail": (cp.stderr or "")[-6000:],
        }
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "returncode": 124,
            "stdout_tail": (e.stdout or "")[-6000:] if isinstance(e.stdout, str) else "",
            "stderr_tail": "TimeoutExpired",
        }
    except Exception as e:
        return {"ok": False, "returncode": 1, "stdout_tail": "", "stderr_tail": repr(e)}


def compileall_health(root: Path) -> Dict[str, Any]:
    targets = ["app", "config.py", "scripts"]
    existing = [t for t in targets if (root / t).exists()]
    if not existing:
        return {"ok": False, "returncode": 1, "stdout_tail": "", "stderr_tail": "compileall target yok"}
    return run_cmd([sys.executable, "-m", "compileall", *existing], root, timeout=240)


def app_factory_health(root: Path) -> Dict[str, Any]:
    code = r'''
import json
try:
    from app import create_app
    app = create_app()
except Exception:
    try:
        from app import create_bys360_application
        app = create_bys360_application()
    except Exception as exc:
        import traceback
        print("__BYS360_JSON__" + json.dumps({"ok": False, "error": repr(exc), "traceback": traceback.format_exc()[-3000:]}, ensure_ascii=False))
        raise SystemExit(1)
print("__BYS360_JSON__" + json.dumps({"ok": True, "blueprint_count": len(app.blueprints), "route_count": len(list(app.url_map.iter_rules()))}, ensure_ascii=False))
'''
    res = run_cmd([sys.executable, "-c", code], root, timeout=180)
    parsed = None
    for line in (res.get("stdout_tail") or "").splitlines():
        if line.startswith(MARKER_JSON):
            try:
                parsed = json.loads(line[len(MARKER_JSON):])
            except Exception:
                parsed = None
    res["parsed"] = parsed
    if parsed and parsed.get("ok"):
        res["ok"] = True
    return res


def url_map_inventory(root: Path) -> Dict[str, Any]:
    code = r'''
import json
try:
    from app import create_app
    app = create_app()
except Exception:
    from app import create_bys360_application
    app = create_bys360_application()
items=[]
for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r.rule)):
    methods=sorted([m for m in rule.methods if m not in {"HEAD", "OPTIONS"}])
    item={"rule": str(rule.rule), "endpoint": str(rule.endpoint), "methods": methods, "arguments": sorted(list(rule.arguments or []))}
    if "mobile" in item["rule"].lower() or "mobile" in item["endpoint"].lower():
        items.append(item)
print("__BYS360_JSON__" + json.dumps({"ok": True, "mobile_route_count": len(items), "mobile_routes": items}, ensure_ascii=False))
'''
    res = run_cmd([sys.executable, "-c", code], root, timeout=180)
    parsed: Dict[str, Any] = {"ok": False, "mobile_route_count": 0, "mobile_routes": []}
    for line in (res.get("stdout_tail") or "").splitlines():
        if line.startswith(MARKER_JSON):
            try:
                parsed = json.loads(line[len(MARKER_JSON):])
            except Exception as exc:
                parsed = {"ok": False, "error": repr(exc), "mobile_routes": []}
    parsed["subprocess"] = res
    return parsed


def analyze_mobile_files(root: Path) -> Dict[str, Any]:
    targets = [root / "app/api/mobile/routes.py", root / "app/api/mobile/performance_routes.py"]
    out: List[Dict[str, Any]] = []
    delegated_total = 0
    legacy_total = 0
    function_total = 0
    for path in targets:
        item: Dict[str, Any] = {"path": rel(path, root), "exists": path.exists()}
        if not path.exists():
            out.append(item)
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        item["kb"] = round(len(text.encode("utf-8")) / 1024, 1)
        item["lines"] = text.count("\n") + 1
        try:
            tree = ast.parse(text)
            funcs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            item["syntax_ok"] = True
            item["function_count"] = len(funcs)
            function_total += len(funcs)
            item["delegated_count"] = sum(1 for n in funcs if "return " in ast.get_source_segment(text, n)[:400] and "_service." in ast.get_source_segment(text, n)[:1000])
            item["legacy_count"] = sum(1 for n in funcs if n.name.startswith("_bys360_legacy"))
            delegated_total += item["delegated_count"]
            legacy_total += item["legacy_count"]
            item["top_functions"] = sorted([
                {"name": n.name, "line": n.lineno, "length": (getattr(n, "end_lineno", n.lineno) or n.lineno) - n.lineno + 1}
                for n in funcs
            ], key=lambda x: x["length"], reverse=True)[:15]
        except SyntaxError as exc:
            item["syntax_ok"] = False
            item["syntax_error"] = f"{exc.filename}:{exc.lineno}: {exc.msg}"
        out.append(item)
    return {
        "target_files": out,
        "function_total": function_total,
        "delegated_total": delegated_total,
        "legacy_total": legacy_total,
    }


def safe_get_candidates(routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Sadece dinamik parametresiz GET mobile endpointleri smoke adayıdır.
    candidates = []
    for r in routes:
        rule = r.get("rule", "")
        methods = r.get("methods", [])
        args = r.get("arguments", [])
        if "GET" in methods and not args and "<" not in rule:
            candidates.append(r)
    return candidates[:20]


def write_reports(root: Path, data: Dict[str, Any]) -> Tuple[Path, Path]:
    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / f"{SLUG}_report.json"
    md_path = report_dir / f"{SLUG}_report.md"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    lines: List[str] = []
    lines.append(f"# BYS360 Mobile Smoke Baseline P1.11 {VERSION}")
    lines.append("")
    lines.append("Bu rapor uygulama dosyalarını değiştirmez. Mobil API refactor dalı sonrası endpoint haritası, servis delegasyon özeti ve sağlık temelini çıkarır.")
    lines.append("")
    lines.append("## Özet")
    summary = data.get("summary", {})
    for k, v in summary.items():
        lines.append(f"- {k}: {v}")
    lines.append("")

    mf = data.get("mobile_files", {})
    lines.append("## Mobil Dosya Özeti")
    lines.append("| Dosya | KB | Satır | Fonksiyon | Delegated | Legacy | Syntax |")
    lines.append("|---|---:|---:|---:|---:|---:|---|")
    for item in mf.get("target_files", []):
        lines.append(f"| `{item.get('path')}` | {item.get('kb','')} | {item.get('lines','')} | {item.get('function_count','')} | {item.get('delegated_count','')} | {item.get('legacy_count','')} | {item.get('syntax_ok','')} |")
    lines.append("")

    url = data.get("url_map", {})
    routes = url.get("mobile_routes", [])
    lines.append("## Mobil URL Haritası")
    lines.append(f"- mobile_route_count: {url.get('mobile_route_count', 0)}")
    lines.append("")
    lines.append("| Method | Rule | Endpoint | Arg |")
    lines.append("|---|---|---|---|")
    for r in routes[:80]:
        lines.append(f"| {','.join(r.get('methods', []))} | `{r.get('rule')}` | `{r.get('endpoint')}` | `{','.join(r.get('arguments', []))}` |")
    if len(routes) > 80:
        lines.append(f"\n_İlk 80 gösterildi; toplam {len(routes)} kayıt JSON raporda._")
    lines.append("")

    lines.append("## Güvenli Smoke Test Adayları")
    smoke_candidates = data.get("smoke_candidates", [])
    if not smoke_candidates:
        lines.append("Parametresiz GET mobil endpoint adayı bulunamadı veya route haritası alınamadı.")
    else:
        for r in smoke_candidates:
            lines.append(f"- `{r.get('rule')}` → `{r.get('endpoint')}`")
    lines.append("")

    lines.append("## Kalan Büyük Fonksiyonlar")
    lines.append("| Dosya | Fonksiyon | Satır | Uzunluk |")
    lines.append("|---|---|---:|---:|")
    for item in mf.get("target_files", []):
        for fn in item.get("top_functions", [])[:10]:
            lines.append(f"| `{item.get('path')}` | `{fn.get('name')}` | {fn.get('line')} | {fn.get('length')} |")
    lines.append("")

    h = data.get("health_summary", {})
    lines.append("## Sağlık Kontrolü")
    lines.append(f"- compileall_ok: {h.get('compileall_ok')}")
    lines.append(f"- app_factory_ok: {h.get('app_factory_ok')}")
    lines.append(f"- overall_ok: {h.get('overall_ok')}")
    lines.append("")
    lines.append("## Öneri")
    lines.append("Mobil refactor dalında bundan sonra performans route dosyasına geçmeden önce gerçek cihaz veya test client ile login, dashboard, profil, destek, mesajlaşma ve asistan smoke testi yapılmalıdır. Survey tarafı rollback gördüğü için ayrıca manuel kod incelemesiyle ele alınmalıdır.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--mode", choices=["audit", "health", "all"], default="all")
    args = ap.parse_args()
    root = Path(args.project_root).resolve()

    data: Dict[str, Any] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mobile_files": {},
        "url_map": {},
        "smoke_candidates": [],
        "health_summary": {},
        "summary": {},
    }

    if args.mode in {"audit", "all"}:
        mf = analyze_mobile_files(root)
        data["mobile_files"] = mf
        url = url_map_inventory(root)
        data["url_map"] = {k: v for k, v in url.items() if k != "subprocess"}
        data["url_map_subprocess_ok"] = url.get("subprocess", {}).get("ok")
        routes = data["url_map"].get("mobile_routes", [])
        data["smoke_candidates"] = safe_get_candidates(routes)
        data["summary"].update({
            "target_file_count": len([x for x in mf.get("target_files", []) if x.get("exists")]),
            "total_functions": mf.get("function_total", 0),
            "delegated_functions_in_targets": mf.get("delegated_total", 0),
            "legacy_functions_in_targets": mf.get("legacy_total", 0),
            "mobile_route_count": data["url_map"].get("mobile_route_count", 0),
            "safe_get_smoke_candidate_count": len(data["smoke_candidates"]),
        })

    if args.mode in {"health", "all"}:
        comp = compileall_health(root)
        app = app_factory_health(root)
        health = {
            "compileall_ok": bool(comp.get("ok")),
            "app_factory_ok": bool(app.get("ok")),
            "overall_ok": bool(comp.get("ok") and app.get("ok")),
            "compileall": comp,
            "app_factory": app,
        }
        data["health_summary"] = health
        data["summary"].update({
            "compileall_ok": health["compileall_ok"],
            "app_factory_ok": health["app_factory_ok"],
            "overall_ok": health["overall_ok"],
        })

    json_path, md_path = write_reports(root, data)
    data["json_report"] = rel(json_path, root)
    data["md_report"] = rel(md_path, root)

    print(json.dumps({
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "summary": data.get("summary"),
        "health_summary": {k: v for k, v in data.get("health_summary", {}).items() if not isinstance(v, dict)},
        "json_report": data["json_report"],
        "md_report": data["md_report"],
    }, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_SMOKE_BASELINE_P1_11_V2_17_21_REPORT_OK")
    if args.mode in {"health", "all"}:
        if data.get("health_summary", {}).get("overall_ok"):
            print("BYS360_MOBILE_SMOKE_BASELINE_P1_11_V2_17_21_HEALTH_OK")
        else:
            print("BYS360_MOBILE_SMOKE_BASELINE_P1_11_V2_17_21_HEALTH_FAIL")
            return 1
    print("BYS360_MOBILE_SMOKE_BASELINE_P1_11_V2_17_21_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
