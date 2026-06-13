from __future__ import annotations
import argparse, json
from app import create_app
from app.models import SystemSetting
VERSION="BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE2_1_RECIPIENT_GROUPS"

def _loads(key):
    row=SystemSetting.query.filter_by(setting_key=key).first()
    if not row or not row.value_text: return []
    try: return json.loads(row.value_text)
    except Exception: return []

def main():
    p=argparse.ArgumentParser(); p.add_argument('--project-root', default='.')
    p.parse_args()
    app=create_app(); errors=[]
    with app.app_context():
        staff=_loads('corporate_information_center.staff_recipient_ids')
        managers=_loads('corporate_information_center.manager_recipient_ids')
        cic_staff=_loads('cic.recipients.staff_ids')
        cic_managers=_loads('cic.recipients.manager_ids')
        if not staff: errors.append('personel alıcı grubu boş')
        if not managers: errors.append('yönetici alıcı grubu boş')
        if not cic_staff: errors.append('otomasyon motoru personel alıcı grubu boş')
        if not cic_managers: errors.append('otomasyon motoru yönetici alıcı grubu boş')
        payload={"ok": not errors, "version": VERSION, "errors": errors, "staff_count": len(staff), "manager_count": len(managers), "cic_staff_count": len(cic_staff), "cic_manager_count": len(cic_managers)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    if errors: raise SystemExit(1)
    print(VERSION+'_CHECK_OK')
if __name__=='__main__': main()
