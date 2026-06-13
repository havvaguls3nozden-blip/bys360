# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VERSION = "V2.17.34"
SLUG = "bys360_mobile_performance_write_route_plan_p3_v2_17_34"
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
WRITE_HINTS = (
    "submit", "create", "add", "update", "delete", "remove", "action", "return",
    "withdraw", "approve", "approval", "publish", "preapproval", "score", "note",
    "mark", "send", "reply"
)
HIGH_RISK_HINTS = (
    "score_submit", "score_action", "return", "withdraw", "approve", "approval",
    "publish", "create_in_period_note"
)

@dataclass
class FuncInfo:
    name: str
    line: int
    end_line: int
    length: int
    arg: str
    delegated: bool
    legacy: bool
    group: str
    write_like: bool
    risk: str


def rel(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root)).replace('\\', '/')
    except Exception:
        return str(p).replace('\\', '/')


def read_text(p: Path) -> str:
    return p.read_text(encoding='utf-8', errors='replace')


def safe_compile_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "missing"}
    try:
        compile(read_text(path), str(path), 'exec')
        return {"exists": True, "ok": True, "error": ""}
    except Exception as exc:
        return {"exists": True, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def run_cmd(args: List[str], cwd: Path, timeout: int = 120) -> Dict[str, Any]:
    try:
        cp = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            encoding='utf-8',
            errors='replace',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout_tail": cp.stdout[-5000:],
            "stderr_tail": cp.stderr[-5000:],
        }
    except Exception as exc:
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": f"{type(exc).__name__}: {exc}"}


def classify_group(name: str) -> str:
    n = name.lower()
    if 'task' in n or 'assignment' in n or 'score_form' in n or 'score_submit' in n or 'score_action' in n:
        return 'performance_tasks'
    if 'period' in n or 'note' in n:
        return 'performance_periods'
    if 'criteria' in n or 'weight' in n or 'approval' in n or 'preapproval' in n:
        return 'performance_evaluation'
    if 'report' in n or 'risk' in n or 'history' in n or 'summary' in n or 'suggestion' in n:
        return 'performance_summary_reports'
    return 'performance_misc'


def classify_risk(name: str, route_methods: List[str], length: int, write_like: bool) -> str:
    n = name.lower()
    if any(h in n for h in HIGH_RISK_HINTS) or any(m in WRITE_METHODS for m in route_methods):
        if length >= 80 or 'score_submit' in n:
            return 'high'
        return 'medium'
    if write_like:
        return 'medium'
    if length >= 50:
        return 'medium'
    return 'low'


def ast_functions(path: Path, route_method_by_func: Dict[str, List[str]]) -> Tuple[List[FuncInfo], str]:
    if not path.exists():
        return [], 'missing'
    text = read_text(path)
    try:
        tree = ast.parse(text)
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"
    funcs: List[FuncInfo] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, 'end_lineno', node.lineno)
            body_txt = ast.get_source_segment(text, node) or ''
            args = [a.arg for a in list(node.args.posonlyargs) + list(node.args.args)]
            if node.args.vararg:
                args.append('*' + node.args.vararg.arg)
            args.extend(a.arg for a in node.args.kwonlyargs)
            if node.args.kwarg:
                args.append('**' + node.args.kwarg.arg)
            methods = route_method_by_func.get(node.name, [])
            n = node.name.lower()
            write_like = bool(any(h in n for h in WRITE_HINTS) or any(m in WRITE_METHODS for m in methods))
            length = max(0, end - node.lineno + 1)
            funcs.append(FuncInfo(
                name=node.name,
                line=node.lineno,
                end_line=end,
                length=length,
                arg=', '.join(args),
                delegated=('_bys360_legacy_' in body_txt or '_service.' in body_txt or 'services.' in body_txt),
                legacy=node.name.startswith('_bys360_legacy_'),
                group=classify_group(node.name),
                write_like=write_like,
                risk=classify_risk(node.name, methods, length, write_like),
            ))
    funcs.sort(key=lambda f: (f.line, f.name))
    return funcs, ''


def app_urlmap(root: Path) -> Dict[str, Any]:
    code = """
import json
from app import create_app
app=create_app()
out=[]
for rule in app.url_map.iter_rules():
    methods=sorted([m for m in rule.methods if m not in ('HEAD','OPTIONS')])
    out.append({'rule': str(rule), 'endpoint': rule.endpoint, 'methods': methods, 'arguments': sorted(list(rule.arguments))})
print('BYS360_URLMAP_JSON_START')
print(json.dumps(out, ensure_ascii=False))
print('BYS360_URLMAP_JSON_END')
"""
    res = run_cmd([sys.executable, '-c', code], root, timeout=120)
    rules: List[Dict[str, Any]] = []
    text = (res.get('stdout_tail', '') or '') + '\n' + (res.get('stderr_tail', '') or '')
    m = re.search(r'BYS360_URLMAP_JSON_START\s*(.*?)\s*BYS360_URLMAP_JSON_END', text, re.S)
    if m:
        try:
            rules = json.loads(m.group(1))
        except Exception as exc:
            res['parse_error'] = f"{type(exc).__name__}: {exc}"
    return {"raw": res, "rules": rules}


def health(root: Path) -> Dict[str, Any]:
    compileall = run_cmd([sys.executable, '-m', 'compileall', 'app', 'config.py', 'scripts'], root, timeout=180)
    factory = run_cmd([sys.executable, '-c', "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"], root, timeout=120)
    combined = (factory.get('stdout_tail', '') or '') + (factory.get('stderr_tail', '') or '')
    return {
        "compileall_ok": bool(compileall.get('ok')),
        "app_factory_ok": bool(factory.get('ok') and 'BYS360_APP_CREATE_OK' in combined),
        "overall_ok": bool(compileall.get('ok') and factory.get('ok') and 'BYS360_APP_CREATE_OK' in combined),
        "compileall": compileall,
        "app_factory": factory,
    }


def write_report(root: Path, data: Dict[str, Any]) -> Tuple[Path, Path]:
    report_dir = root / 'reports' / 'quality'
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / f'{SLUG}_report.json'
    md_path = report_dir / f'{SLUG}_report.md'
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    lines: List[str] = []
    lines.append('# BYS360 Mobile Performance Write Route Plan P3 V2.17.34')
    lines.append('')
    lines.append('Bu rapor uygulama dosyalarını değiştirmez. P3 yazma/işlem endpointleri için risk envanteri çıkarır.')
    lines.append('')
    lines.append('## Özet')
    for k, v in data['summary'].items():
        lines.append(f'- {k}: {v}')
    lines.append('')
    lines.append('## Performans Yazma URLMap')
    lines.append('| Method | Rule | Endpoint | Arg | Risk |')
    lines.append('|---|---|---|---|---|')
    for r in data['write_urlmap']:
        lines.append(f"| {','.join(r['methods'])} | `{r['rule']}` | `{r['endpoint']}` | `{', '.join(r.get('arguments', []))}` | {r.get('risk','')} |")
    if not data['write_urlmap']:
        lines.append('| | Yazma endpointi bulunamadı | | | |')
    lines.append('')
    lines.append('## Yazma / İşlem Adayları')
    lines.append('| Fonksiyon | Satır | Uzunluk | Grup | Route Method | Delegated | Legacy | Risk | Öneri |')
    lines.append('|---|---:|---:|---|---|---:|---:|---|---|')
    for f in data['write_candidates'][:60]:
        lines.append(f"| `{f['name']}` | {f['line']} | {f['length']} | {f['group']} | {','.join(f.get('route_methods', []))} | {f['delegated']} | {f['legacy']} | {f['risk']} | {f['recommendation']} |")
    lines.append('')
    lines.append('## Okuma Benzeri ama P3 Öncesi Ayrılabilecek Yardımcılar')
    lines.append('| Fonksiyon | Satır | Uzunluk | Grup | Risk |')
    lines.append('|---|---:|---:|---|---|')
    for f in data['read_like_candidates'][:40]:
        lines.append(f"| `{f['name']}` | {f['line']} | {f['length']} | {f['group']} | {f['risk']} |")
    lines.append('')
    lines.append('## Önerilen P3 Sırası')
    lines.append('1. Gerçek kullanıcı/token ile mobil performans smoke testi yapılmadan puan gönderme ve onay endpointlerine dokunma.')
    lines.append('2. İlk kod değişikliği gerekiyorsa yazma endpointi değil, sadece helper/payload fonksiyonlarını servis katmanına al.')
    lines.append('3. Puan gönderme için ayrı P3.1: `mobile_performance_task_score_submit` yalnız başına ve rollback zorunlu.')
    lines.append('4. Dönem içi not oluşturma için ayrı P3.2: `mobile_performance_create_in_period_note_v2853` yalnız başına.')
    lines.append('5. Onay/yayın/iade-ret fonksiyonları en sona bırakılmalı.')
    lines.append('')
    lines.append('## Sağlık Kontrolü')
    h = data['health_summary']
    lines.append(f"- compileall_ok: {h.get('compileall_ok')}")
    lines.append(f"- app_factory_ok: {h.get('app_factory_ok')}")
    lines.append(f"- overall_ok: {h.get('overall_ok')}")
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    return json_path, md_path


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--project-root', required=True)
    ap.add_argument('--mode', default='all', choices=['audit', 'all'])
    ns = ap.parse_args(argv)
    root = Path(ns.project_root).resolve()
    perf = root / 'app' / 'api' / 'mobile' / 'performance_routes.py'
    routes = root / 'app' / 'api' / 'mobile' / 'routes.py'
    urlmap = app_urlmap(root)
    perf_rules: List[Dict[str, Any]] = []
    route_methods_by_func: Dict[str, List[str]] = {}
    for r in urlmap.get('rules', []):
        if '/api/mobile/performance' in r.get('rule', ''):
            perf_rules.append(r)
            func = str(r.get('endpoint','')).split('.')[-1]
            route_methods_by_func.setdefault(func, [])
            route_methods_by_func[func].extend(r.get('methods', []))
    write_urlmap: List[Dict[str, Any]] = []
    for r in perf_rules:
        methods = r.get('methods', [])
        if any(m in WRITE_METHODS for m in methods):
            func = str(r.get('endpoint','')).split('.')[-1]
            rr = dict(r)
            rr['risk'] = 'high' if 'score' in func.lower() else 'medium'
            write_urlmap.append(rr)
    funcs, parse_error = ast_functions(perf, route_methods_by_func)
    def to_dict(f: FuncInfo) -> Dict[str, Any]:
        route_methods = route_methods_by_func.get(f.name, [])
        if f.risk == 'high':
            recommendation = 'P3 ayrı paket; rollback ve gerçek token smoke zorunlu.'
        elif any(m in WRITE_METHODS for m in route_methods):
            recommendation = 'Tek endpoint olarak ele al; route/endpoint değişmesin.'
        else:
            recommendation = 'Önce helper/service delegasyonu yapılabilir.'
        return {
            'name': f.name, 'line': f.line, 'end_line': f.end_line, 'length': f.length,
            'arg': f.arg, 'delegated': f.delegated, 'legacy': f.legacy, 'group': f.group,
            'write_like': f.write_like, 'risk': f.risk, 'route_methods': route_methods,
            'recommendation': recommendation,
        }
    write_candidates = [to_dict(f) for f in funcs if not f.legacy and (f.write_like or route_methods_by_func.get(f.name)) and f.risk in ('high','medium')]
    write_candidates.sort(key=lambda x: ({'high':0,'medium':1,'low':2}.get(x['risk'], 9), -x['length'], x['line']))
    read_like = [to_dict(f) for f in funcs if not f.legacy and not f.write_like and f.length >= 8]
    read_like.sort(key=lambda x: (-x['length'], x['line']))
    h = health(root) if ns.mode == 'all' else {"compileall_ok": None, "app_factory_ok": None, "overall_ok": None}
    summary = {
        'mode': ns.mode,
        'performance_file_exists': perf.exists(),
        'performance_file_kb': round(perf.stat().st_size / 1024, 1) if perf.exists() else 0,
        'performance_function_count': len(funcs),
        'performance_parse_error': parse_error,
        'performance_urlmap_count': len(perf_rules),
        'write_urlmap_count': len(write_urlmap),
        'write_candidate_count': len(write_candidates),
        'high_risk_write_candidate_count': sum(1 for x in write_candidates if x['risk'] == 'high'),
        'read_like_candidate_count': len(read_like),
        'routes_file_compile_ok': safe_compile_file(routes).get('ok'),
        'performance_file_compile_ok': safe_compile_file(perf).get('ok'),
        'compileall_ok': h.get('compileall_ok'),
        'app_factory_ok': h.get('app_factory_ok'),
        'overall_ok': h.get('overall_ok'),
    }
    data = {
        'version': VERSION,
        'mode': ns.mode,
        'project_root': str(root),
        'summary': summary,
        'write_urlmap': write_urlmap,
        'write_candidates': write_candidates,
        'read_like_candidates': read_like,
        'health_summary': h,
    }
    jp, mp = write_report(root, data)
    print(json.dumps({'version': VERSION, 'mode': ns.mode, 'project_root': str(root), 'summary': summary, 'json_report': rel(root, jp), 'md_report': rel(root, mp)}, ensure_ascii=False, indent=2))
    print('BYS360_MOBILE_PERFORMANCE_WRITE_ROUTE_PLAN_P3_V2_17_34_REPORT_OK')
    if ns.mode == 'all':
        if h.get('overall_ok'):
            print('BYS360_MOBILE_PERFORMANCE_WRITE_ROUTE_PLAN_P3_V2_17_34_HEALTH_OK')
        else:
            print('BYS360_MOBILE_PERFORMANCE_WRITE_ROUTE_PLAN_P3_V2_17_34_HEALTH_FAIL')
            return 1
    print('BYS360_MOBILE_PERFORMANCE_WRITE_ROUTE_PLAN_P3_V2_17_34_OK')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
