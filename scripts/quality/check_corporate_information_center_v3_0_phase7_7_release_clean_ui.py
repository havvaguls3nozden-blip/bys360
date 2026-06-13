
from pathlib import Path
import argparse
VERSION = 'BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_7_RELEASE_CLEAN_UI'

def fail(msg):
    print(f"{VERSION}_GATE_FAIL")
    print("HATA: "+msg)
    raise SystemExit(2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ProjectRoot','--ProjectRoot', default='C:/bys360/project')
    args = parser.parse_args()
    root = Path(args.ProjectRoot)
    system = root/'app/templates/corporate_information_center/system.html'
    base = root/'app/templates/corporate_information_center/base.html'
    if not system.exists(): fail('system.html bulunamadı')
    text = system.read_text(encoding='utf-8')
    required = [VERSION,'release-hero','Kurumsal Bilgilendirme Merkezi yayına hazır.','Pilot test ekranına git','Yönetici kontrol listesi','Teknik ayarlar ve zamanlanmış iş komutu','release-btn primary','href="/dashboard/kurumsal-bilgilendirme/test"']
    for token in required:
        if token not in text: fail(f'system.html içinde eksik ifade: {token}')
    bad_tokens = ['color:#0d6efd','btn-link','href="#"',"\">') }}?v",'expected token']
    for token in bad_tokens:
        if token in text: fail(f'system.html içinde istenmeyen ifade: {token}')
    if base.exists():
        b = base.read_text(encoding='utf-8')
        if "\">') }}?v" in b or "2_15_18\">')" in b:
            fail('base.html içinde bozuk CSS/Jinja kalıntısı var')
    try:
        from jinja2 import Environment
        env = Environment()
        env.parse(text)
        if base.exists(): env.parse(base.read_text(encoding='utf-8'))
    except Exception as exc:
        fail(f'Jinja sözdizimi doğrulaması başarısız: {exc}')
    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
