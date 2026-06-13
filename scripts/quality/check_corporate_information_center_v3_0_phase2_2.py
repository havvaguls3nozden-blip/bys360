from __future__ import annotations
import json, sys
from pathlib import Path
VERSION='BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE2_2_RECIPIENT_UX'

def main():
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--project-root', default='.')
    root=Path(p.parse_args().project_root)
    errors=[]
    rec=root/'app/templates/corporate_information_center/recipients.html'
    base=root/'app/templates/corporate_information_center/base.html'
    svc=root/'app/services/corporate_information_center.py'
    for f in [rec,base,svc]:
        if not f.exists(): errors.append(f'eksik: {f}')
    if rec.exists():
        t=rec.read_text(encoding='utf-8',errors='ignore')
        for token in ['data-action="select-visible-staff"','data-action="select-all-managers"','data-preset="pilot"','cicSearch','cicUnit','Alıcıları Kaydet']:
            if token not in t: errors.append(f'alıcı UX token yok: {token}')
        bad=['Yö','Gö','AlÄ','Ü','Ö','ş','ı']
        if any(b in t for b in bad): errors.append('recipients.html içinde bozuk Türkçe karakter izi var')
    if base.exists():
        t=base.read_text(encoding='utf-8',errors='ignore')
        for token in ['Kurumsal Bilgilendirme Merkezi','Görev Yönetimi','Gönderim Geçmişi']:
            if token not in t: errors.append(f'base token yok: {token}')
        if any(b in t for b in ['Yö','Gö','AlÄ','ş','ı']): errors.append('base.html içinde bozuk Türkçe karakter izi var')
    if svc.exists():
        t=svc.read_text(encoding='utf-8',errors='ignore')
        if 'return q.order_by(User.id.asc()).limit(limit).all()' not in t: errors.append('list_users güvenli User.id sıralaması yok')
        if 'return q.order_by(User.id.asc()).all()' not in t: errors.append('aktif personel güvenli User.id sıralaması yok')
    print(json.dumps({'ok':not errors,'version':VERSION,'errors':errors},ensure_ascii=False,indent=2))
    if errors: raise SystemExit(1)
    print(VERSION+'_CHECK_OK')
if __name__=='__main__': main()
