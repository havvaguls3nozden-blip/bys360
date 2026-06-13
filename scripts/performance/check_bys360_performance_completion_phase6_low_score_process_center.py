# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,json,py_compile,subprocess,sys
from datetime import datetime
from pathlib import Path
REQUIRED_FILES=["app/services/performance/phase6_low_score_process_center.py","app/templates/performance/_phase6_low_score_process_panel.html","app/static/css/performance_completion_phase6_low_score_process.css","app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE6_LOW_SCORE_PROCESS_CENTER.md"]
MARKERS={"app/services/performance/phase6_low_score_process_center.py":["BYS360_PERFORMANCE_COMPLETION_PHASE6_LOW_SCORE_PROCESS_CENTER","BYS360_PERFORMANCE_COMPLETION_PHASE6_NO_FAKE_APPROVAL","BYS360_PERFORMANCE_COMPLETION_PHASE6_PUBLISH_LOCK","BYS360_PERFORMANCE_COMPLETION_PHASE6_FIRST_SECOND_TRACKING","BYS360_PERFORMANCE_COMPLETION_PHASE6_PROCESS_RECORD_REQUIRED","should_create_phase6_president_approval_record","phase6_publish_block_reason_from_process"],"app/services/performance/low_score_process_service.py":["BYS360_PERFORMANCE_COMPLETION_PHASE6_LOW_SCORE_SERVICE_BRIDGE","phase6_publish_block_reason_from_process","is_phase6_process_finalized_for_publish"],"app/services/performance/publish_preflight_rules.py":["BYS360_PERFORMANCE_COMPLETION_PHASE6_PREFLIGHT_BOUND"],"app/templates/performance/_phase6_low_score_process_panel.html":["BYS360_PERFORMANCE_COMPLETION_PHASE6_LOW_SCORE_PROCESS_TEMPLATE"]}
TARGET_TEMPLATES=["app/templates/performance/president_approval_scorecard.html","app/templates/performance/president_approval_scorecard_v2.html","app/templates/performance/president_card_review.html","app/templates/performance_low_score_processes.html","app/templates/performance/process_engine_president_approvals.html"]
def read(p:Path)->str: return p.read_text(encoding="utf-8-sig")
def smoke_policy(root:Path)->dict:
    sys.path.insert(0,str(root))
    from app.services.performance.phase6_low_score_process_center import BYS360_PERFORMANCE_COMPLETION_PHASE6_VERSION, filter_phase6_real_low_score_approvals, phase6_contract, phase6_process_steps, phase6_status_label, resolve_phase6_low_score_process, should_create_phase6_president_approval_record
    pending=resolve_phase6_low_score_process(final_score=62,approval_status="president_pending")
    first_block=resolve_phase6_low_score_process(final_score=62,approval_status="approved_by_president",process_record_exists=False,warning_record_exists=False,sequence_no=1)
    first_ready=resolve_phase6_low_score_process(final_score=62,approval_status="approved_by_president",process_record_exists=True,warning_record_exists=True,sequence_no=1)
    second_block=resolve_phase6_low_score_process(final_score=62,approval_status="approved_by_president",process_record_exists=False,administrative_process_exists=False,sequence_no=2)
    normal=resolve_phase6_low_score_process(final_score=82)
    filtered=filter_phase6_real_low_score_approvals([{"final_score":91},{"final_score":55,"approval_status":"president_pending"}])
    steps=phase6_process_steps(pending)
    items={"version":BYS360_PERFORMANCE_COMPLETION_PHASE6_VERSION=="performance-completion-phase6-low-score-process-center-v1","fake_above_70":should_create_phase6_president_approval_record(80) is False,"create_below_70":should_create_phase6_president_approval_record(69,existing_record=False) is True,"existing_no_duplicate":should_create_phase6_president_approval_record(69,existing_record=True) is False,"pending_blocks":pending.can_publish is False and "Onay" in pending.block_reason,"first_warning_blocks":first_block.can_publish is False and "uyarı" in first_block.block_reason.lower(),"first_ready":first_ready.can_publish is True,"second_admin_blocks":second_block.can_publish is False and "Tekrarlayan" in second_block.warning_label,"normal_ready":normal.can_publish is True and normal.approval_required is False,"labels":phase6_status_label("blocked_president_pending")=="Başkan/Üst Onay Yayın Kilidi","filter_real":len(filtered)==1 and filtered[0]["final_score"]==55,"steps":bool(steps and steps[2]["state"]=="active"),"contract":bool(phase6_contract().get("fake_approval_records_forbidden"))}
    return {"ok":all(items.values()),"items":items,"pending":pending.as_dict(),"contract":phase6_contract()}
def app_check(root:Path)->dict:
    code="""from app import create_app
app=create_app()
with app.app_context():
    from app.services.performance.phase6_low_score_process_center import seed_phase6_low_score_process_settings
    import json
    print(json.dumps(seed_phase6_low_score_process_settings(), ensure_ascii=False))
"""
    proc=subprocess.run([sys.executable,"-c",code],cwd=str(root),text=True,capture_output=True); lines=(proc.stdout or "").strip().splitlines(); payload=lines[-1] if lines else "{}"
    try: data=json.loads(payload)
    except Exception: data={"ok":False,"stdout":proc.stdout,"stderr":proc.stderr,"returncode":proc.returncode}
    if proc.returncode!=0: data["ok"]=False; data["stderr"]=proc.stderr
    return data
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--project-root",required=True); args=ap.parse_args(); root=Path(args.project_root).resolve()
    result={"package":"performance_completion_phase6_low_score_process_center","version":"V1","project_root":str(root),"generated_at":datetime.now().isoformat(timespec="seconds"),"required_files":{"ok":True,"missing":[]},"markers":{"ok":True,"items":[]},"compile":{"ok":True,"errors":[]},"templates":{"ok":True,"items":[]},"policy_smoke":None,"app_check":None,"ok":False}
    for rel in REQUIRED_FILES:
        if not (root/rel).exists(): result["required_files"]["ok"]=False; result["required_files"]["missing"].append(rel)
    for rel,needles in MARKERS.items():
        text=read(root/rel) if (root/rel).exists() else ""; status={n:(n in text) for n in needles}; result["markers"]["items"].append({"file":rel,"ok":all(status.values()),"markers":status})
    result["markers"]["ok"]=all(i["ok"] for i in result["markers"]["items"])
    for rel in ["app/services/performance/phase6_low_score_process_center.py","app/services/performance/low_score_process_service.py","app/services/performance/publish_preflight_rules.py"]:
        if not (root/rel).exists(): continue
        try: py_compile.compile(str(root/rel),doraise=True)
        except Exception as exc: result["compile"]["ok"]=False; result["compile"]["errors"].append({"file":rel,"error":str(exc)})
    for rel in TARGET_TEMPLATES:
        path=root/rel
        if not path.exists(): result["templates"]["items"].append({"file":rel,"exists":False,"bound":True}); continue
        text=read(path); bound="performance/_phase6_low_score_process_panel.html" in text or "BYS360_PERFORMANCE_COMPLETION_PHASE6_TEMPLATE_BOUND" in text; result["templates"]["items"].append({"file":rel,"exists":True,"bound":bound})
    result["templates"]["ok"]=all(i["bound"] for i in result["templates"]["items"]); result["policy_smoke"]=smoke_policy(root); result["app_check"]=app_check(root)
    result["ok"]=all([result["required_files"]["ok"],result["markers"]["ok"],result["compile"]["ok"],result["templates"]["ok"],result["policy_smoke"]["ok"],bool(result["app_check"].get("ok"))])
    print(json.dumps(result,ensure_ascii=False,indent=2)); print("BYS360_PERFORMANCE_COMPLETION_PHASE6_LOW_SCORE_PROCESS_CENTER_CHECK_OK" if result["ok"] else "BYS360_PERFORMANCE_COMPLETION_PHASE6_LOW_SCORE_PROCESS_CENTER_CHECK_FAIL"); return 0 if result["ok"] else 1
if __name__=="__main__": raise SystemExit(main())
