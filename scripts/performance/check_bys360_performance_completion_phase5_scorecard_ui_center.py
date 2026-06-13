# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, py_compile, sys
from datetime import datetime
from pathlib import Path
REQUIRED_FILES=["app/services/performance/phase5_scorecard_ui_policy.py","app/services/performance/phase5_4_status_language.py","app/templates/performance/_phase5_scorecard_ui_styles.html","app/templates/performance/_phase5_scorecard_ui_macros.html","app/static/css/performance_completion_phase5_scorecard_ui.css","app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_CENTER.md"]
MARKERS={"app/services/performance/phase5_scorecard_ui_policy.py":["BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_CENTER","BYS360_PERFORMANCE_COMPLETION_PHASE5_TECHNICAL_LANGUAGE_CLEANUP","BYS360_PERFORMANCE_COMPLETION_PHASE5_LARGE_SCORE_SURFACE","BYS360_PERFORMANCE_COMPLETION_PHASE5_MANAGER_OPINION_CARDS","BYS360_PERFORMANCE_COMPLETION_PHASE5_PROCESS_HISTORY_TURKISH","BYS360_PERFORMANCE_COMPLETION_PHASE5_MOBILE_LAYOUT"],"app/services/performance/phase5_4_status_language.py":["BYS360_PERFORMANCE_COMPLETION_PHASE5_STATUS_LANGUAGE_BRIDGE","phase5_4_status_label","phase5_4_clean_text"],"app/templates/performance/_phase5_scorecard_ui_styles.html":["BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_TEMPLATE","performance_completion_phase5_scorecard_ui.css"],"app/static/css/performance_completion_phase5_scorecard_ui.css":["BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_CSS","bys360-phase5-score-value","bys360-phase5-table-wrap","bys360-phase5-opinion-card"]}
TARGET_TEMPLATES=["app/templates/performance_scorecard_detail.html","app/templates/performance_v2_phase5_scorecard.html","app/templates/scorecard.html","app/templates/performance/president_approval_scorecard.html","app/templates/performance/president_approval_scorecard_v2.html","app/templates/performance/president_card_review.html","app/templates/performance_tasks.html","app/templates/performance/evaluation_form.html","app/templates/evaluation_form.html"]
def read(p:Path)->str: return p.read_text(encoding='utf-8-sig')
def smoke_policy(root:Path)->dict:
    sys.path.insert(0,str(root))
    from app.services.performance.phase5_scorecard_ui_policy import BYS360_PERFORMANCE_COMPLETION_PHASE5_VERSION,contains_visible_technical_language,phase5_clean_text,phase5_empty_message,phase5_manager_opinion_cards,phase5_score_band,phase5_score_display,phase5_scorecard_contract,phase5_status_label
    cleaned=phase5_clean_text('workflow_state / scorecard_pending / Faz 3 senkronu')
    cards=phase5_manager_opinion_cards([{'manager_level':'3','manager_name':'Test Amir','score':4.5,'opinion':'scorecard_pending','status':'third_manager_comment_pending'}])
    items={'version':BYS360_PERFORMANCE_COMPLETION_PHASE5_VERSION=='performance-completion-phase5-scorecard-ui-center-v1','status_president':phase5_status_label('blocked_president_pending')=='Başkan Onayı Yayın Kilidi','status_scorecard':phase5_status_label('scorecard_pending')=='Karne Yayın Süreci Bekliyor','clean_text':'scorecard_pending' not in cleaned and 'Faz 3' not in cleaned,'hidden_detector':contains_visible_technical_language('scorecard_pending') is True,'clean_detector':contains_visible_technical_language(cleaned) is False,'score_low':phase5_score_band(55).key=='low','score_high':phase5_score_band(95).key=='high','score_normal':phase5_score_band(78).key=='normal','score_display':phase5_score_display(88.50)=='88.5','manager_cards':bool(cards and cards[0]['level_label']=='3. Amir' and 'Karne' in cards[0]['opinion']),'empty_message':'henüz oluşmamış' in phase5_empty_message('process'),'contract':bool(phase5_scorecard_contract().get('technical_language_hidden'))}
    return {'ok':all(items.values()),'items':items,'cleaned':cleaned,'cards':cards[:1],'contract':phase5_scorecard_contract()}
def app_filter_check(root:Path)->dict:
    try:
        sys.path.insert(0,str(root)); from app import create_app; app=create_app(); filters=app.jinja_env.filters
        items={'phase5_status_label':'phase5_status_label' in filters,'phase5_clean_text':'phase5_clean_text' in filters,'phase5_score_display':'phase5_score_display' in filters,'phase5_4_status_label':'phase5_4_status_label' in filters}
        return {'ok':all(items.values()),'items':items}
    except Exception as exc: return {'ok':False,'error':str(exc)}
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root',required=True); args=ap.parse_args(); root=Path(args.project_root).resolve()
    result={'package':'performance_completion_phase5_scorecard_ui_center','version':'V1','project_root':str(root),'generated_at':datetime.now().isoformat(timespec='seconds'),'required_files':{'ok':True,'missing':[]},'markers':{'ok':True,'items':[]},'compile':{'ok':True,'errors':[]},'templates':{'ok':True,'items':[]},'policy_smoke':None,'app_filter_check':None,'ok':False}
    for rel in REQUIRED_FILES:
        if not (root/rel).exists(): result['required_files']['ok']=False; result['required_files']['missing'].append(rel)
    for rel,needles in MARKERS.items():
        text=read(root/rel) if (root/rel).exists() else ''; status={n:(n in text) for n in needles}; result['markers']['items'].append({'file':rel,'ok':all(status.values()),'markers':status})
    result['markers']['ok']=all(i['ok'] for i in result['markers']['items'])
    for rel in ['app/services/performance/phase5_scorecard_ui_policy.py','app/services/performance/phase5_4_status_language.py']:
        try: py_compile.compile(str(root/rel),doraise=True)
        except Exception as exc: result['compile']['ok']=False; result['compile']['errors'].append({'file':rel,'error':str(exc)})
    for rel in TARGET_TEMPLATES:
        path=root/rel
        if not path.exists(): result['templates']['items'].append({'file':rel,'exists':False,'bound':True}); continue
        text=read(path); bound='performance/_phase5_scorecard_ui_styles.html' in text and 'BYS360_PERFORMANCE_COMPLETION_PHASE5_TEMPLATE_BOUND' in text
        result['templates']['items'].append({'file':rel,'exists':True,'bound':bound})
    result['templates']['ok']=all(i['bound'] for i in result['templates']['items'])
    result['policy_smoke']=smoke_policy(root); result['app_filter_check']=app_filter_check(root)
    result['ok']=all([result['required_files']['ok'],result['markers']['ok'],result['compile']['ok'],result['templates']['ok'],result['policy_smoke']['ok'],result['app_filter_check']['ok']])
    print(json.dumps(result,ensure_ascii=False,indent=2)); print('BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_CENTER_CHECK_OK' if result['ok'] else 'BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_CENTER_CHECK_FAIL')
    return 0 if result['ok'] else 1
if __name__=='__main__': raise SystemExit(main())
