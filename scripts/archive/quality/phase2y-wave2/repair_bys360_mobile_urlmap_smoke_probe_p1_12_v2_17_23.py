# -*- coding: utf-8 -*-
"""
BYS360 Mobile URLMap Smoke Probe P1.12 V2.17.23
Kod degistirmez. Flask app.url_map, mobil route sinyalleri ve saglik kontrolu raporlar.
"""
from __future__ import annotations

import argparse
import ast
import compileall
import json
import os
import sys
import traceback
from pathlib import Path
from datetime import datetime

VERSION = "V2.17.23"
REPORT_NAME = "bys360_mobile_urlmap_smoke_probe_p1_12_v2_17_23_report"


def rel(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root)).replace('\\', '/')
    except Exception:
        return str(p).replace('\\', '/')


def ensure_reports(root: Path) -> Path:
    d = root / 'reports' / 'quality'
    d.mkdir(parents=True, exist_ok=True)
    return d


def syntax_ok(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "missing"}
    try:
        ast.parse(path.read_text(encoding='utf-8', errors='replace'))
        return {"exists": True, "ok": True, "error": ""}
    except Exception as e:
        return {"exists": True, "ok": False, "error": f"{type(e).__name__}: {e}"}


def decorator_name(node: ast.AST) -> str:
    if isinstance(node, ast.Call):
        return decorator_name(node.func)
    if isinstance(node, ast.Attribute):
        base = decorator_name(node.value)
        return (base + '.' if base else '') + node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ''


def static_route_scan(root: Path) -> dict:
    files = [root/'app/api/mobile/routes.py', root/'app/api/mobile/performance_routes.py']
    out = []
    total_decorators = 0
    total_add_url_rule = 0
    total_functions = 0
    for p in files:
        item = {"path": rel(root,p), "exists": p.exists(), "syntax": syntax_ok(p), "functions": 0, "route_decorators": [], "add_url_rule_hits": 0}
        if p.exists() and item["syntax"]["ok"]:
            text = p.read_text(encoding='utf-8', errors='replace')
            item["add_url_rule_hits"] = text.count('add_url_rule(')
            try:
                tree = ast.parse(text)
                for n in ast.walk(tree):
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        item["functions"] += 1
                        for dec in n.decorator_list:
                            dn = decorator_name(dec)
                            if dn.endswith('.route') or dn == 'route' or '.route' in dn:
                                item["route_decorators"].append({"function": n.name, "line": n.lineno, "decorator": dn})
                total_decorators += len(item["route_decorators"])
                total_add_url_rule += item["add_url_rule_hits"]
                total_functions += item["functions"]
            except Exception as e:
                item["parse_error"] = repr(e)
        out.append(item)
    return {"files": out, "total_functions": total_functions, "total_route_decorators": total_decorators, "total_add_url_rule_hits": total_add_url_rule}


def make_app(root: Path):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    import importlib
    mod = importlib.import_module('app')
    if hasattr(mod, 'create_app'):
        app = mod.create_app()
    elif hasattr(mod, 'create_bys360_application'):
        app = mod.create_bys360_application()
    else:
        raise RuntimeError('app modulu icinde create_app veya create_bys360_application bulunamadi')
    return app


def url_map_probe(root: Path) -> dict:
    result = {"ok": False, "error": "", "blueprint_count": 0, "rule_count": 0, "mobile_rule_count": 0, "api_rule_count": 0, "mobile_rules": [], "safe_get_candidates": []}
    try:
        app = make_app(root)
        result["ok"] = True
        result["blueprint_count"] = len(getattr(app, 'blueprints', {}) or {})
        rules = list(app.url_map.iter_rules())
        result["rule_count"] = len(rules)
        mobile_rules = []
        api_rules = []
        for r in rules:
            methods = sorted([m for m in (r.methods or []) if m not in {'HEAD','OPTIONS'}])
            item = {
                "rule": str(r.rule),
                "endpoint": str(r.endpoint),
                "methods": methods,
                "arguments": sorted(list(r.arguments or [])),
                "defaults": dict(r.defaults or {}),
            }
            token = (item["rule"] + " " + item["endpoint"]).lower()
            if '/api' in token or 'api.' in token or 'api_' in token:
                api_rules.append(item)
            if 'mobile' in token or '/api/mobile' in token or 'api.mobile' in token:
                mobile_rules.append(item)
                if methods == ['GET'] and not item['arguments']:
                    result["safe_get_candidates"].append(item)
        result["api_rule_count"] = len(api_rules)
        result["mobile_rule_count"] = len(mobile_rules)
        result["mobile_rules"] = mobile_rules[:200]
        result["api_rules_sample"] = api_rules[:100]
    except Exception as e:
        result["ok"] = False
        result["error"] = ''.join(traceback.format_exception_only(type(e), e)).strip()
        result["trace_tail"] = traceback.format_exc()[-4000:]
    return result


def health(root: Path) -> dict:
    h = {"compileall_ok": False, "app_factory_ok": False, "overall_ok": False, "app_factory_error": ""}
    try:
        h["compileall_ok"] = bool(compileall.compile_dir(str(root/'app'), quiet=1)) and bool(compileall.compile_file(str(root/'config.py'), quiet=1) if (root/'config.py').exists() else True) and bool(compileall.compile_dir(str(root/'scripts'), quiet=1))
    except Exception as e:
        h["compileall_error"] = repr(e)
    try:
        app = make_app(root)
        h["app_factory_ok"] = True
        h["blueprint_count"] = len(getattr(app, 'blueprints', {}) or {})
        h["url_rule_count"] = len(list(app.url_map.iter_rules()))
    except Exception as e:
        h["app_factory_error"] = traceback.format_exc()[-4000:]
    h["overall_ok"] = bool(h.get("compileall_ok") and h.get("app_factory_ok"))
    return h


def write_reports(root: Path, report: dict):
    d = ensure_reports(root)
    json_path = d / f"{REPORT_NAME}.json"
    md_path = d / f"{REPORT_NAME}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = []
    lines.append(f"# BYS360 Mobile URLMap Smoke Probe P1.12 {VERSION}")
    lines.append("")
    lines.append("Bu rapor uygulama dosyalarını değiştirmez. Flask `app.url_map` üzerinden gerçek mobil/API endpoint haritasını kontrol eder.")
    lines.append("")
    lines.append("## Özet")
    um = report.get('url_map', {})
    st = report.get('static_scan', {})
    h = report.get('health_summary', {})
    lines += [
        f"- mode: {report.get('mode')}",
        f"- app_urlmap_ok: {um.get('ok')}",
        f"- blueprint_count: {um.get('blueprint_count', h.get('blueprint_count'))}",
        f"- url_rule_count: {um.get('rule_count', h.get('url_rule_count'))}",
        f"- api_rule_count: {um.get('api_rule_count')}",
        f"- mobile_rule_count: {um.get('mobile_rule_count')}",
        f"- safe_get_candidate_count: {len(um.get('safe_get_candidates', []))}",
        f"- static_route_decorator_count: {st.get('total_route_decorators')}",
        f"- static_add_url_rule_hits: {st.get('total_add_url_rule_hits')}",
        f"- compileall_ok: {h.get('compileall_ok')}",
        f"- app_factory_ok: {h.get('app_factory_ok')}",
        f"- overall_ok: {h.get('overall_ok')}",
    ]
    if um.get('error'):
        lines.append(f"- urlmap_error: `{um.get('error')}`")
    lines.append("")
    lines.append("## Mobil URL Haritası")
    lines.append("| Method | Rule | Endpoint | Arg |")
    lines.append("|---|---|---|---|")
    for item in um.get('mobile_rules', [])[:80]:
        lines.append(f"| {','.join(item.get('methods', []))} | `{item.get('rule')}` | `{item.get('endpoint')}` | `{','.join(item.get('arguments', []))}` |")
    if not um.get('mobile_rules'):
        lines.append("| - | Mobil endpoint bulunamadı | - | - |")
    lines.append("")
    lines.append("## Güvenli GET Smoke Adayları")
    lines.append("| Method | Rule | Endpoint |")
    lines.append("|---|---|---|")
    for item in um.get('safe_get_candidates', [])[:80]:
        lines.append(f"| GET | `{item.get('rule')}` | `{item.get('endpoint')}` |")
    if not um.get('safe_get_candidates'):
        lines.append("| - | Parametresiz GET mobil endpoint adayı bulunamadı. | - |")
    lines.append("")
    lines.append("## Statik Mobil Dosya Sinyalleri")
    lines.append("| Dosya | Fonksiyon | Route Decorator | add_url_rule | Syntax |")
    lines.append("|---|---:|---:|---:|---|")
    for f in st.get('files', []):
        lines.append(f"| `{f.get('path')}` | {f.get('functions')} | {len(f.get('route_decorators', []))} | {f.get('add_url_rule_hits')} | {f.get('syntax',{}).get('ok')} |")
    lines.append("")
    lines.append("## Sağlık Kontrolü")
    lines += [f"- compileall_ok: {h.get('compileall_ok')}", f"- app_factory_ok: {h.get('app_factory_ok')}", f"- overall_ok: {h.get('overall_ok')}"]
    if h.get('app_factory_error'):
        lines.append("\n```text\n" + h.get('app_factory_error','')[-2000:] + "\n```")
    md_path.write_text('\n'.join(lines)+"\n", encoding='utf-8')
    return str(json_path.relative_to(root)), str(md_path.relative_to(root))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', required=True)
    parser.add_argument('--mode', default='all', choices=['audit','health','all'])
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    os.chdir(root)
    report = {"version": VERSION, "mode": args.mode, "project_root": str(root), "generated_at": datetime.now().isoformat(timespec='seconds')}
    if args.mode in ('audit','all'):
        report['static_scan'] = static_route_scan(root)
        report['url_map'] = url_map_probe(root)
    if args.mode in ('health','all'):
        report['health_summary'] = health(root)
    else:
        report['health_summary'] = {}
    jp, mp = write_reports(root, report)
    print(json.dumps({
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "url_map_summary": {
            "ok": report.get('url_map',{}).get('ok'),
            "rule_count": report.get('url_map',{}).get('rule_count'),
            "mobile_rule_count": report.get('url_map',{}).get('mobile_rule_count'),
            "safe_get_candidate_count": len(report.get('url_map',{}).get('safe_get_candidates', [])),
        },
        "static_summary": {
            "route_decorator_count": report.get('static_scan',{}).get('total_route_decorators'),
            "add_url_rule_hits": report.get('static_scan',{}).get('total_add_url_rule_hits'),
        },
        "health_summary": report.get('health_summary', {}),
        "json_report": jp,
        "md_report": mp,
    }, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_URLMAP_SMOKE_PROBE_P1_12_V2_17_23_REPORT_OK")
    if args.mode in ('health','all'):
        if report.get('health_summary',{}).get('overall_ok'):
            print("BYS360_MOBILE_URLMAP_SMOKE_PROBE_P1_12_V2_17_23_HEALTH_OK")
        else:
            print("BYS360_MOBILE_URLMAP_SMOKE_PROBE_P1_12_V2_17_23_HEALTH_FAIL")
            return 1
    print("BYS360_MOBILE_URLMAP_SMOKE_PROBE_P1_12_V2_17_23_OK")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
