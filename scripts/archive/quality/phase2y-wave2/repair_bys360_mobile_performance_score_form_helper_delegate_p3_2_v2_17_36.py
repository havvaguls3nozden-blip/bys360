
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, ast, json, os, py_compile, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path
VERSION="V2.17.36"
TARGET_REL=Path("app/api/mobile/performance_routes.py")
SERVICE_REL=Path("app/api/mobile/services/performance_task_service.py")
REPORT_JSON=Path("reports/quality/bys360_mobile_performance_score_form_helper_delegate_p3_2_v2_17_36_report.json")
REPORT_MD=Path("reports/quality/bys360_mobile_performance_score_form_helper_delegate_p3_2_v2_17_36_report.md")
TARGET_NAME="_v2835_score_form_payload"
LEGACY_NAME="_bys360_legacy__v2835_score_form_payload"
DELEGATE_NAME="delegate_v2835_score_form_payload"

def read_text(p:Path)->str:
    return p.read_text(encoding="utf-8", errors="replace")
def write_text(p:Path,t:str)->None:
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(t, encoding="utf-8", newline="\n")
def compile_one(p:Path)->dict:
    if not p.exists(): return {"exists":False,"ok":False,"error":"missing"}
    try:
        py_compile.compile(str(p), doraise=True); return {"exists":True,"ok":True,"error":""}
    except Exception as e: return {"exists":True,"ok":False,"error":str(e)}
def parse_tree(p:Path):
    try: return ast.parse(read_text(p)), ""
    except Exception as e: return None, str(e)
def find_func(tree,name):
    if tree is None: return None
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name: return n
    return None
def has_route_decorator(n)->bool:
    if not n: return False
    for d in n.decorator_list:
        try: txt=ast.unparse(d)
        except Exception: txt=""
        if ".route" in txt or "route(" in txt or "add_url_rule" in txt: return True
    return False
def looks_delegated(text,n)->bool:
    if not n or not getattr(n,"end_lineno",None): return False
    block="\n".join(text.splitlines()[n.lineno-1:n.end_lineno])
    return DELEGATE_NAME in block or "performance_task_service" in block
def simple_args(n):
    a=n.args; parts=[]; calls=[]; pos=list(a.posonlyargs)+list(a.args)
    defaults=[None]*(len(pos)-len(a.defaults))+list(a.defaults)
    for arg,default in zip(pos,defaults):
        name=arg.arg
        if default is None: parts.append(name)
        else:
            try: dt=ast.unparse(default)
            except Exception: dt="None"
            parts.append(f"{name}={dt}")
        calls.append(name)
    if a.vararg:
        parts.append("*"+a.vararg.arg); calls.append("*"+a.vararg.arg)
    elif a.kwonlyargs: parts.append("*")
    for arg,default in zip(a.kwonlyargs,a.kw_defaults):
        name=arg.arg
        if default is None: parts.append(name)
        else:
            try: dt=ast.unparse(default)
            except Exception: dt="None"
            parts.append(f"{name}={dt}")
        calls.append(f"{name}={name}")
    if a.kwarg:
        parts.append("**"+a.kwarg.arg); calls.append("**"+a.kwarg.arg)
    return ", ".join(parts), ", ".join(calls)
def ensure_service_delegate(service_path:Path)->dict:
    service_path.parent.mkdir(parents=True, exist_ok=True)
    text=read_text(service_path) if service_path.exists() else "# -*- coding: utf-8 -*-\n"
    if DELEGATE_NAME in text:
        return {"path":str(service_path),"changed":False,"compile":compile_one(service_path)}
    addition = (
        "\n\n# P3.2 V2.17.36 - route URL/endpoint degistirmeden helper delegasyonu\n"
        f"def {DELEGATE_NAME}(*args, **kwargs):\n"
        "    # Import local tutulur; blueprint kayit sirasini etkilemez.\n"
        "    from app.api.mobile import performance_routes as _routes\n"
        f"    legacy = getattr(_routes, \"{LEGACY_NAME}\", None)\n"
        "    if legacy is None:\n"
        f"        raise RuntimeError(\"{LEGACY_NAME} bulunamadi; P3.2 delegasyon eksik veya geri alinmis olabilir.\")\n"
        "    return legacy(*args, **kwargs)\n"
    )
    write_text(service_path, text.rstrip()+addition)
    return {"path":str(service_path),"changed":True,"compile":compile_one(service_path)}
def patch_target(project_root:Path,target_path:Path,service_path:Path)->dict:
    text=read_text(target_path); tree,perr=parse_tree(target_path)
    if perr: return {"routes_changed":False,"patched_functions":[],"backup":"","error":perr,"rolled_back":False}
    node=find_func(tree,TARGET_NAME); legacy=find_func(tree,LEGACY_NAME)
    if not node: return {"routes_changed":False,"patched_functions":[],"backup":"","error":"target_missing","rolled_back":False}
    if legacy or looks_delegated(text,node): return {"routes_changed":False,"patched_functions":[],"backup":"","error":"already_delegated_or_legacy_exists","rolled_back":False}
    if has_route_decorator(node): return {"routes_changed":False,"patched_functions":[],"backup":"","error":"target_has_route_decorator_unexpected","rolled_back":False}
    ts=datetime.now().strftime("%Y%m%d_%H%M%S"); q=project_root/"_local_quarantine"/f"bys360_mobile_performance_score_form_helper_delegate_p3_2_{ts}"; backup=q/TARGET_REL
    backup.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(target_path,backup)
    lines=text.splitlines(); start=node.lineno-1; end=node.end_lineno; block=lines[start:end]; renamed=block[:]
    for i,line in enumerate(renamed):
        s=line.lstrip()
        if s.startswith(f"def {TARGET_NAME}("):
            indent=line[:len(line)-len(s)]; renamed[i]=indent+s.replace(f"def {TARGET_NAME}(", f"def {LEGACY_NAME}(",1); break
    sig,call=simple_args(node)
    wrapper=["", f"def {TARGET_NAME}({sig}):", f"    from app.api.mobile.services.performance_task_service import {DELEGATE_NAME}", f"    return {DELEGATE_NAME}({call})" if call else f"    return {DELEGATE_NAME}()"]
    write_text(target_path, "\n".join(lines[:start]+renamed+wrapper+lines[end:])+"\n")
    service=ensure_service_delegate(service_path); tc={"routes":compile_one(target_path),"service":compile_one(service_path)}
    rolled=False; err=""
    if not tc["routes"]["ok"] or not tc["service"]["ok"]:
        shutil.copy2(backup,target_path); rolled=True; err="target_or_service_compile_failed_after_patch"; tc={"routes":compile_one(target_path),"service":compile_one(service_path)}
    return {"routes_changed":not rolled,"patched_functions":[] if rolled else [TARGET_NAME],"backup":str(backup.relative_to(project_root)),"error":err,"rolled_back":rolled,"service":service,"target_compile":tc}
def health(project_root:Path)->dict:
    env=os.environ.copy(); env.setdefault("PYTHONIOENCODING","utf-8")
    def run(cmd):
        p=subprocess.run(cmd,cwd=str(project_root),text=True,encoding="utf-8",errors="replace",capture_output=True,env=env)
        return {"ok":p.returncode==0,"returncode":p.returncode,"stdout_tail":p.stdout[-4000:],"stderr_tail":p.stderr[-4000:]}
    comp=run([sys.executable,"-m","compileall","app","config.py","scripts"])
    fac=run([sys.executable,"-c","from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"])
    return {"compileall_ok":comp["ok"],"app_factory_ok":fac["ok"],"overall_ok":comp["ok"] and fac["ok"],"compileall":comp,"app_factory":fac}
def audit(project_root:Path)->dict:
    target=project_root/TARGET_REL; service=project_root/SERVICE_REL; tree,perr=parse_tree(target) if target.exists() else (None,"missing"); text=read_text(target) if target.exists() else ""; node=find_func(tree,TARGET_NAME); legacy=find_func(tree,LEGACY_NAME); funcs=[]
    if node:
        funcs.append({"name":TARGET_NAME,"exists":True,"line":node.lineno,"end_line":getattr(node,"end_lineno",node.lineno),"length":getattr(node,"end_lineno",node.lineno)-node.lineno+1,"route_decorator":has_route_decorator(node),"delegated":looks_delegated(text,node),"legacy":legacy is not None,"patchable":bool(node and not legacy and not looks_delegated(text,node) and not has_route_decorator(node)),"arg":simple_args(node)[0]})
    else: funcs.append({"name":TARGET_NAME,"exists":False})
    return {"target_exists":target.exists(),"target_path":str(TARGET_REL),"target_compile":compile_one(target),"service_exists":service.exists(),"service_path":str(SERVICE_REL),"service_compile":compile_one(service) if service.exists() else {"exists":False,"ok":False,"error":"missing"},"parse_error":perr,"candidate_count":1 if node else 0,"delegated_count":1 if node and looks_delegated(text,node) else 0,"patchable_count":1 if node and not legacy and not looks_delegated(text,node) and not has_route_decorator(node) else 0,"functions":funcs}
def write_report(project_root:Path,result:dict)->None:
    jp=project_root/REPORT_JSON; mp=project_root/REPORT_MD; jp.parent.mkdir(parents=True,exist_ok=True); write_text(jp,json.dumps(result,ensure_ascii=False,indent=2))
    a=result.get("audit",{}); ap=result.get("apply",{}); h=result.get("health_summary",{}); rows=[]
    for f in a.get("functions",[]): rows.append(f"| `{f.get('name','')}` | {f.get('exists','')} | {f.get('line','')} | {f.get('length','')} | {f.get('route_decorator','')} | {f.get('delegated','')} | {f.get('legacy','')} | {f.get('patchable','')} | `{f.get('arg','')}` |")
    md=f"""# BYS360 Mobile Performance Score Form Helper Delegate P3.2 V2.17.36

Bu rapor yazma endpointlerine dokunmadan puan formu payload helper fonksiyonunun servis delegasyonu sonucunu gösterir.

## Durum
- mode: {result.get('mode')}

## Audit
- target_exists: {a.get('target_exists')}
- target_compile: `{a.get('target_compile')}`
- service_compile: `{a.get('service_compile')}`

| Fonksiyon | Var | Satır | Uzunluk | Route Decorator | Delegated | Legacy | Patchable | Arg |
|---|---:|---:|---:|---:|---:|---:|---:|---|
{chr(10).join(rows)}

## Apply
- service: `{ap.get('service')}`
- routes_changed: `{ap.get('routes_changed')}`
- patched_functions: `{ap.get('patched_functions')}`
- backup: `{ap.get('backup','')}`
- error: `{ap.get('error','')}`
- rolled_back: `{ap.get('rolled_back','')}`
- target_compile: `{ap.get('target_compile','')}`

## Sağlık Kontrolü
- compileall_ok: {h.get('compileall_ok')}
- app_factory_ok: {h.get('app_factory_ok')}
- overall_ok: {h.get('overall_ok')}

## Not
Bu adım gerçek POST yazma endpointlerini çalıştırmaz ve URL/endpoint/blueprint adlarını değiştirmez. `mobile_performance_task_score_submit` gibi yüksek riskli fonksiyonlar ayrı P3 paketine bırakılmıştır.
"""
    write_text(mp,md)
def main()->int:
    pr=argparse.ArgumentParser(); pr.add_argument("--project-root",required=True); pr.add_argument("--mode",choices=["audit","all"],default="audit"); ns=pr.parse_args(); project_root=Path(ns.project_root).resolve(); result={"version":VERSION,"mode":ns.mode,"project_root":str(project_root)}; result["audit"]=audit(project_root); result["apply"]={}
    if ns.mode=="all": result["apply"]=patch_target(project_root,project_root/TARGET_REL,project_root/SERVICE_REL); result["audit_after"]=audit(project_root); result["health_summary"]=health(project_root)
    else: result["health_summary"]={}
    result["json_report"]=str(REPORT_JSON); result["md_report"]=str(REPORT_MD); write_report(project_root,result); print(json.dumps({k:v for k,v in result.items() if k!="health_summary"},ensure_ascii=False,indent=2)); print("BYS360_MOBILE_PERFORMANCE_SCORE_FORM_HELPER_DELEGATE_P3_2_V2_17_36_REPORT_OK")
    if ns.mode=="all":
        if result.get("health_summary",{}).get("overall_ok"):
            if result.get("apply",{}).get("rolled_back"):
                print("BYS360_MOBILE_PERFORMANCE_SCORE_FORM_HELPER_DELEGATE_P3_2_V2_17_36_APPLY_ROLLBACK"); return 1
            print("BYS360_MOBILE_PERFORMANCE_SCORE_FORM_HELPER_DELEGATE_P3_2_V2_17_36_HEALTH_OK"); print("BYS360_MOBILE_PERFORMANCE_SCORE_FORM_HELPER_DELEGATE_P3_2_V2_17_36_APPLY_OK"); print("BYS360_MOBILE_PERFORMANCE_SCORE_FORM_HELPER_DELEGATE_P3_2_V2_17_36_OK"); return 0
        print("BYS360_MOBILE_PERFORMANCE_SCORE_FORM_HELPER_DELEGATE_P3_2_V2_17_36_HEALTH_FAIL"); return 1
    print("BYS360_MOBILE_PERFORMANCE_SCORE_FORM_HELPER_DELEGATE_P3_2_V2_17_36_OK"); return 0
if __name__=="__main__": raise SystemExit(main())
