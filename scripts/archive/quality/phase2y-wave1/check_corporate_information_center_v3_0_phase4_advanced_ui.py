# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib, sys
VERSION = 'BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE4_ADVANCED_UI'
ROOT = pathlib.Path(__file__).resolve().parents[2]
checks = {
 'app/templates/corporate_information_center/base.html': ['BYS360 Kurumsal İletişim','cic-section-title','cic-progress'],
 'app/templates/corporate_information_center/tasks.html': ['data-confirm-real-send','csrf_token()','Kuru Çalışma'],
 'app/templates/corporate_information_center/test.html': ['last_result','cic_last_dispatch_result' if False else 'Son Test Sonucu','csrf_token()'],
 'app/templates/corporate_information_center/recipients.html': ['csrf_token()','Görünenleri Yöneticiye Ekle','Seçim Özeti'],
 'app/communication/corporate_information_center_routes.py': ['cic_last_dispatch_result','_session_safe_result','session.pop'],
}
missing=[]
for rel, markers in checks.items():
    p=ROOT/rel
    if not p.exists():
        missing.append(rel + ' dosyası yok')
        continue
    txt=p.read_text(encoding='utf-8', errors='ignore')
    for m in markers:
        if m not in txt:
            missing.append(rel + ' içinde eksik: ' + m)
if missing:
    print(VERSION + '_GATE_FAIL')
    for m in missing:
        print('HATA:', m)
    raise SystemExit(1)
print(VERSION + '_GATE_OK')
print(VERSION + '_FINAL_OK')
