from __future__ import annotations
import argparse, ast, json, subprocess, sys
from pathlib import Path
from typing import Any
VERSION="V2.17.7"
MARKER="BYS360_MOBILE_SERVICE_SCAFFOLD_P1_2_V2_17_7"
SERVICE_FILES=json.loads('{"__init__.py": "\\"\\"\\"BYS360 Mobile API service scaffold.\\n\\nThis package is prepared for safe route refactoring. Existing URL paths,\\nendpoint names and blueprint registrations are intentionally not changed in P1.2.\\n\\"\\"\\"\\n\\n__all__ = [\\n    \\"auth_service\\",\\n    \\"dashboard_service\\",\\n    \\"profile_service\\",\\n    \\"personnel_service\\",\\n    \\"communication_service\\",\\n    \\"survey_service\\",\\n    \\"support_service\\",\\n    \\"assistant_service\\",\\n    \\"performance_period_service\\",\\n    \\"performance_task_service\\",\\n    \\"performance_evaluation_service\\",\\n    \\"performance_summary_service\\",\\n    \\"performance_scorecard_service\\",\\n]\\n", "base.py": "\\"\\"\\"Shared helpers for future BYS360 mobile API service extraction.\\n\\nP1.2 only creates the service foundation. Route functions remain in their current\\nfiles until P1.3+ micro-refactor packages move them one group at a time.\\n\\"\\"\\"\\n\\nfrom __future__ import annotations\\n\\nfrom typing import Any, Mapping\\n\\n\\ndef ok_payload(data: Mapping[str, Any] | None = None, **extra: Any) -> dict[str, Any]:\\n    payload: dict[str, Any] = {\\"ok\\": True}\\n    if data:\\n        payload.update(dict(data))\\n    if extra:\\n        payload.update(extra)\\n    return payload\\n\\n\\ndef error_payload(message: str, *, code: str = \\"mobile_error\\", status: int = 400, **extra: Any) -> dict[str, Any]:\\n    payload: dict[str, Any] = {\\"ok\\": False, \\"code\\": code, \\"message\\": message, \\"status\\": status}\\n    if extra:\\n        payload.update(extra)\\n    return payload\\n", "auth_service.py": "\\"\\"\\"Auth/Login service extraction target for app/api/mobile/routes.py.\\n\\nPlanned functions from P1.1: mobile_login and auth related helpers.\\nNo active route code is moved in P1.2.\\n\\"\\"\\"\\n\\nfrom __future__ import annotations\\n", "dashboard_service.py": "\\"\\"\\"Dashboard/KPI service extraction target for mobile routes.\\n\\nPlanned functions include mobile_dashboard_summary and mobile_kpi_target_*.\\nNo active route code is moved in P1.2.\\n\\"\\"\\"\\n\\nfrom __future__ import annotations\\n", "profile_service.py": "\\"\\"\\"Profile service extraction target for mobile routes.\\"\\"\\"\\n\\nfrom __future__ import annotations\\n", "personnel_service.py": "\\"\\"\\"Personnel service extraction target for mobile routes.\\"\\"\\"\\n\\nfrom __future__ import annotations\\n", "communication_service.py": "\\"\\"\\"Communication/message service extraction target for mobile routes.\\"\\"\\"\\n\\nfrom __future__ import annotations\\n", "survey_service.py": "\\"\\"\\"Survey service extraction target for mobile routes.\\"\\"\\"\\n\\nfrom __future__ import annotations\\n", "support_service.py": "\\"\\"\\"Support ticket service extraction target for mobile routes.\\"\\"\\"\\n\\nfrom __future__ import annotations\\n", "assistant_service.py": "\\"\\"\\"Assistant service extraction target for mobile routes.\\"\\"\\"\\n\\nfrom __future__ import annotations\\n", "performance_period_service.py": "\\"\\"\\"Performance period service extraction target for mobile performance routes.\\"\\"\\"\\n\\nfrom __future__ import annotations\\n", "performance_task_service.py": "\\"\\"\\"Performance task/scoring service extraction target for mobile performance routes.\\"\\"\\"\\n\\nfrom __future__ import annotations\\n", "performance_evaluation_service.py": "\\"\\"\\"Performance evaluation service extraction target for mobile performance routes.\\"\\"\\"\\n\\nfrom __future__ import annotations\\n", "performance_summary_service.py": "\\"\\"\\"Performance summary service extraction target for mobile performance routes.\\"\\"\\"\\n\\nfrom __future__ import annotations\\n", "performance_scorecard_service.py": "\\"\\"\\"Performance scorecard service extraction target for mobile performance routes.\\"\\"\\"\\n\\nfrom __future__ import annotations\\n", "split_manifest.py": "\\"\\"\\"Planned BYS360 mobile route split manifest.\\"\\"\\"\\n\\nfrom __future__ import annotations\\n\\nMOBILE_ROUTE_SPLIT_MANIFEST: dict[str, dict[str, object]] = {\\n    \\"app/api/mobile/routes.py\\": {\\n        \\"target_groups\\": {\\n            \\"auth\\": \\"app/api/mobile/services/auth_service.py\\",\\n            \\"dashboard\\": \\"app/api/mobile/services/dashboard_service.py\\",\\n            \\"profile\\": \\"app/api/mobile/services/profile_service.py\\",\\n            \\"personnel\\": \\"app/api/mobile/services/personnel_service.py\\",\\n            \\"communication\\": \\"app/api/mobile/services/communication_service.py\\",\\n            \\"survey\\": \\"app/api/mobile/services/survey_service.py\\",\\n            \\"support\\": \\"app/api/mobile/services/support_service.py\\",\\n            \\"assistant\\": \\"app/api/mobile/services/assistant_service.py\\",\\n        },\\n        \\"rule\\": \\"Do not change URL paths, endpoint names or blueprint registration during extraction.\\",\\n    },\\n    \\"app/api/mobile/performance_routes.py\\": {\\n        \\"target_groups\\": {\\n            \\"performance_periods\\": \\"app/api/mobile/services/performance_period_service.py\\",\\n            \\"performance_tasks\\": \\"app/api/mobile/services/performance_task_service.py\\",\\n            \\"performance_evaluation\\": \\"app/api/mobile/services/performance_evaluation_service.py\\",\\n            \\"performance_summary\\": \\"app/api/mobile/services/performance_summary_service.py\\",\\n            \\"performance_scorecard\\": \\"app/api/mobile/services/performance_scorecard_service.py\\",\\n        },\\n        \\"rule\\": \\"Move one function group per package and run compileall + create_app after every micro step.\\",\\n    },\\n}\\n"}')
NOTES='# BYS360 Mobile Route Refactor P1.2\n\nBu paket **route fonksiyonlarını taşımaz**. Amacı, P1.3 ve sonrası için güvenli servis klasörü, manifest ve sağlık kontrol omurgası kurmaktır.\n\n## P1.2 kapsamı\n\n- `app/api/mobile/services/` klasörü oluşturulur.\n- Mobil route grupları için servis dosyaları oluşturulur.\n- `split_manifest.py` ile hedef bölme haritası yazılır.\n- Aktif URL, endpoint, blueprint veya route decorator değiştirilmez.\n- `compileall` ve `create_app` sağlık testi yapılır.\n\n## P1.3 için önerilen ilk mikro adım\n\nEn güvenli başlangıç: `auth` ve `health` gibi küçük, düşük bağımlılıklı mobil fonksiyonlar.\n'

def safe_read(path: Path) -> str:
    try: return path.read_text(encoding="utf-8")
    except UnicodeDecodeError: return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError: return ""

def analyze_python_file(path: Path) -> dict[str, Any]:
    text=safe_read(path)
    info={"path":str(path).replace("\\","/"),"exists":path.exists(),"kb":round(path.stat().st_size/1024,1) if path.exists() else 0,"lines":text.count("\n")+(1 if text else 0),"syntax_ok":False,"functions":0,"route_markers":text.count("@") if text else 0}
    if not text: return info
    try:
        tree=ast.parse(text); info["syntax_ok"]=True; info["functions"]=sum(isinstance(n,(ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree))
    except SyntaxError as exc:
        info["syntax_error"]={"line":exc.lineno,"message":exc.msg}
    return info

def should_write(path: Path)->bool:
    if not path.exists(): return True
    text=safe_read(path)
    return MARKER in text or "P1.2" in text or "service extraction target" in text or path.name=="__init__.py"

def write_scaffold(root: Path)->dict[str,Any]:
    service_root=root/"app"/"api"/"mobile"/"services"; service_root.mkdir(parents=True, exist_ok=True)
    written=[]; skipped=[]
    for name,content in SERVICE_FILES.items():
        path=service_root/name; body=f"# {MARKER}\n"+content
        if should_write(path): path.write_text(body,encoding="utf-8"); written.append(str(path.relative_to(root)).replace("\\","/"))
        else: skipped.append(str(path.relative_to(root)).replace("\\","/"))
    notes_path=root/"app"/"docs"/"quality"/"BYS360_MOBILE_ROUTE_REFACTOR_P1_2_V2_17_7.md"; notes_path.parent.mkdir(parents=True, exist_ok=True); notes_path.write_text(NOTES,encoding="utf-8"); written.append(str(notes_path.relative_to(root)).replace("\\","/"))
    return {"service_root":str(service_root.relative_to(root)).replace("\\","/"),"written":written,"skipped_existing_custom":skipped}

def run_command(root:Path,args:list[str],timeout:int=90)->dict[str,Any]:
    try:
        p=subprocess.run(args,cwd=str(root),capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=timeout)
        return {"ok":p.returncode==0,"returncode":p.returncode,"stdout_tail":p.stdout[-6000:],"stderr_tail":p.stderr[-6000:]}
    except Exception as exc: return {"ok":False,"error":repr(exc)}

def health(root:Path)->dict[str,Any]:
    compileall=run_command(root,[sys.executable,"-m","compileall","app","config.py","scripts"],180)
    app_factory=run_command(root,[sys.executable,"-c","from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"],120)
    app_ok=bool(app_factory.get("ok")) and "BYS360_APP_CREATE_OK" in str(app_factory.get("stdout_tail",""))
    return {"compileall_ok":bool(compileall.get("ok")),"app_factory_ok":app_ok,"overall_ok":bool(compileall.get("ok")) and app_ok,"compileall":compileall,"app_factory":app_factory}

def build_report(root:Path,mode:str)->dict[str,Any]:
    targets=[root/"app"/"api"/"mobile"/"routes.py",root/"app"/"api"/"mobile"/"performance_routes.py"]
    service_root=root/"app"/"api"/"mobile"/"services"
    service_files=sorted(str(p.relative_to(root)).replace("\\","/") for p in service_root.glob("*.py")) if service_root.exists() else []
    return {"version":VERSION,"mode":mode,"project_root":str(root),"targets":[analyze_python_file(p) for p in targets],"service_root_exists":service_root.exists(),"service_file_count":len(service_files),"service_files":service_files}

def write_reports(root:Path,report:dict[str,Any])->None:
    d=root/"reports"/"quality"; d.mkdir(parents=True,exist_ok=True); jp=d/"bys360_mobile_service_scaffold_p1_2_v2_17_7_report.json"; mp=d/"bys360_mobile_service_scaffold_p1_2_v2_17_7_report.md"
    report["json_report"]=str(jp.relative_to(root)).replace("\\","/"); report["md_report"]=str(mp.relative_to(root)).replace("\\","/")
    jp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# BYS360 Mobile Service Scaffold P1.2 V2.17.7","","Bu rapor P1.2 servis omurgası ve sağlık kontrol sonucunu gösterir.","","## Hedef Dosyalar","","| Yol | KB | Satır | Fonksiyon | Syntax |","|---|---:|---:|---:|---|"]
    for item in report.get("targets",[]): lines.append(f"| `{item['path']}` | {item['kb']} | {item['lines']} | {item['functions']} | {item['syntax_ok']} |")
    lines += ["","## Servis Omurgası","",f"- service_root_exists: {report.get('service_root_exists')}",f"- service_file_count: {report.get('service_file_count')}"]
    for f in report.get("service_files",[]): lines.append(f"- `{f}`")
    if "apply" in report: lines += ["","## Apply",f"- written: {len(report['apply'].get('written',[]))}",f"- skipped_existing_custom: {len(report['apply'].get('skipped_existing_custom',[]))}"]
    if "health" in report: lines += ["","## Sağlık Kontrolü",f"- compileall_ok: {report['health'].get('compileall_ok')}",f"- app_factory_ok: {report['health'].get('app_factory_ok')}",f"- overall_ok: {report['health'].get('overall_ok')}"]
    mp.write_text("\n".join(lines)+"\n",encoding="utf-8")

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--project-root",required=True); ap.add_argument("--mode",choices=["audit","apply","health","all"],default="audit"); args=ap.parse_args(); root=Path(args.project_root).resolve()
    report=build_report(root,args.mode)
    if args.mode in {"apply","all"}: apply_result=write_scaffold(root); report=build_report(root,args.mode); report["apply"]=apply_result
    if args.mode in {"health","all"}: report["health"]=health(root)
    write_reports(root,report); print(json.dumps(report,ensure_ascii=False,indent=2)); tag="BYS360_MOBILE_SERVICE_SCAFFOLD_P1_2_"+VERSION.replace(".","_"); print(tag+"_REPORT_OK")
    if args.mode in {"health","all"}:
        if report.get("health",{}).get("overall_ok"): print(tag+"_HEALTH_OK")
        else: print(tag+"_HEALTH_FAIL"); return 1
    if args.mode in {"apply","all"}: print(tag+"_APPLY_OK")
    print(tag+"_OK"); return 0
if __name__=="__main__": raise SystemExit(main())
