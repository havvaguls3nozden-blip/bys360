from __future__ import annotations
import argparse, json, shutil, re
from pathlib import Path

VERSION = "BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3"
MARK_START = "# >>> BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3"
MARK_END = "# <<< BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3"

ROUTE_BLOCK = r'''
# >>> BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3

@dashboard_bp.route('/executive-summary/daily-weather-mail', methods=['GET', 'POST'])
@dashboard_bp.route('/yonetici-ozeti/gunluk-hava-maili', methods=['GET', 'POST'])
def executive_summary_daily_weather_mail_tasks_v13():
    """Yönetici Özeti altında çoklu günlük mail görevleri yönetim ekranı."""
    try:
        from flask import render_template, request, redirect, url_for, flash, jsonify
        from flask_login import current_user
        import json
        from pathlib import Path
        from app import db
        from sqlalchemy import text
    except Exception:
        return "Yönetici Özeti günlük mail görevleri yüklenemedi.", 500

    def _is_system_admin_user(user):
        names = set()
        for attr in ('role', 'role_name', 'user_role', 'title', 'permission_group'):
            val = getattr(user, attr, None)
            if val:
                names.add(str(val).strip().lower())
        roles = getattr(user, 'roles', None)
        if roles:
            try:
                for r in roles:
                    names.add(str(getattr(r, 'name', r)).strip().lower())
            except Exception:
                pass
        username = str(getattr(user, 'username', '') or '').lower()
        email = str(getattr(user, 'email', '') or '').lower()
        admin_tokens = ('admin', 'sistem yoneticisi', 'sistem yöneticisi', 'system_admin', 'superadmin')
        return any(t in n for n in names for t in admin_tokens) or username in ('admin','sysadmin') or email.startswith('admin@')

    if not getattr(current_user, 'is_authenticated', False):
        return redirect(url_for('auth.login'))
    if not _is_system_admin_user(current_user):
        return render_template('errors/403.html'), 403

    runtime_dir = Path('app/runtime')
    runtime_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = runtime_dir / 'executive_mail_tasks.json'
    default_tasks = [
        {'key':'morning_weather','title':'Sabah Hava Durumu ve Kıyafet Önerisi','type':'weather','enabled':True,'hour':'08','minute':'15','scope':'pilot','description':'Bugünkü hava durumu, yarın tahmini, genel kıyafet önerisi ve iyi dilek mesajı gönderir.'},
        {'key':'midday_pulse','title':'Gün Ortası Kurumsal Yoklama','type':'pulse','enabled':True,'hour':'13','minute':'00','scope':'pilot','description':'Günün nasıl geçtiğini soran, geri bildirim merkezine yönlendiren kısa kontrol maili gönderir.'},
        {'key':'evening_tomorrow','title':'Akşam Ertesi Gün Bilgilendirmesi','type':'tomorrow_weather','enabled':False,'hour':'17','minute':'00','scope':'pilot','description':'Ertesi gün beklenen hava durumunu ve kısa iyi akşamlar mesajını gönderir.'},
    ]
    if not cfg_path.exists():
        cfg_path.write_text(json.dumps({'pilot_mode': True, 'tasks': default_tasks}, ensure_ascii=False, indent=2), encoding='utf-8')
    data = json.loads(cfg_path.read_text(encoding='utf-8'))
    tasks = data.get('tasks') or default_tasks

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'save_tasks':
            new_tasks = []
            for t in tasks:
                key = t.get('key')
                item = dict(t)
                item['enabled'] = request.form.get(f'enabled_{key}') == 'on'
                item['hour'] = request.form.get(f'hour_{key}', item.get('hour','08')).zfill(2)[:2]
                item['minute'] = request.form.get(f'minute_{key}', item.get('minute','00')).zfill(2)[:2]
                new_tasks.append(item)
            data['tasks'] = new_tasks
            cfg_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            flash('Günlük mail görevleri kaydedildi.', 'success')
            return redirect(request.path)
        if action == 'test_selected':
            flash('Test gönderimi için sunucuda ilgili scripti çalıştırın: send_daily_weather_personnel_mail.py --force veya send_daily_pulse_check_mail.py', 'info')
            return redirect(request.path + '#test-gonderimi')

    recipients = []
    try:
        rows = db.session.execute(text("""
            SELECT id, full_name, email, username, is_active
            FROM users
            WHERE lower(coalesce(email,'')) IN ('mustafa.bektas@ktb.gov.tr','havva.ozden@ktb.gov.tr')
            ORDER BY full_name
        """)).fetchall()
        recipients = [dict(r._mapping) for r in rows]
    except Exception:
        recipients = []

    logs = []
    try:
        rows = db.session.execute(text("""
            SELECT id, recipient_email, subject, status, created_at
            FROM mail_logs
            ORDER BY created_at DESC
            LIMIT 20
        """)).fetchall()
        logs = [dict(r._mapping) for r in rows]
    except Exception:
        logs = []

    return render_template('executive_summary/daily_weather_mail_tasks.html', tasks=tasks, recipients=recipients, logs=logs, pilot_mode=data.get('pilot_mode', True))
# <<< BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3
'''


def copy_overlay(root: Path, rel: str, backup_root: Path, copied: list):
    src = Path(__file__).resolve().parents[2] / rel
    dst = root / rel
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        backup = backup_root / rel
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dst, backup)
        try:
            if dst.read_bytes() == src.read_bytes():
                copied.append({'file': rel, 'skipped': 'same_content'})
                return
        except Exception:
            pass
    shutil.copy2(src, dst)
    copied.append({'file': rel, 'copied': True})


def find_dashboard_routes(root: Path):
    candidates = [root/'app/dashboard/routes.py', root/'app/dashboard/executive_summary_routes.py']
    for c in candidates:
        if c.exists() and 'dashboard_bp' in c.read_text(encoding='utf-8', errors='ignore'):
            return c
    for p in (root/'app').rglob('*.py'):
        txt = p.read_text(encoding='utf-8', errors='ignore')
        if 'dashboard_bp' in txt and ('yonetici-ozeti' in txt or 'executive-summary' in txt):
            return p
    return None


def patch_routes(root: Path, backup_root: Path):
    target = find_dashboard_routes(root)
    if not target:
        return {'patched': False, 'reason': 'dashboard route file not found'}
    rel = target.relative_to(root)
    backup = backup_root / rel
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup)
    txt = target.read_text(encoding='utf-8', errors='ignore')
    if MARK_START in txt and MARK_END in txt:
        txt = re.sub(re.escape(MARK_START)+r'.*?'+re.escape(MARK_END), ROUTE_BLOCK.strip(), txt, flags=re.S)
    else:
        txt = txt.rstrip() + "\n\n" + ROUTE_BLOCK.strip() + "\n"
    target.write_text(txt, encoding='utf-8')
    return {'patched': True, 'file': str(rel)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--project-root', default=r'C:\bys360\project')
    args = ap.parse_args()
    root = Path(args.project_root)
    backup_root = root / 'backups' / VERSION
    backup_root.mkdir(parents=True, exist_ok=True)
    copied=[]
    for rel in [
        'app/templates/executive_summary/daily_weather_mail_tasks.html',
        'scripts/quality/check_executive_summary_daily_mail_tasks_v1_3.py',
        'scripts/windows/install_bys360_daily_pulse_mail_task.ps1',
    ]:
        copy_overlay(root, rel, backup_root, copied)
    route_result = patch_routes(root, backup_root)
    print(json.dumps({'ok': True, 'version': VERSION, 'copied': copied, 'route': route_result}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
