from pathlib import Path
import argparse

VERSION = "BYS360_CIC_V3_0_RECIPIENTS_SAVE_PERSISTENCE_V2_1_GATE_FIX"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ProjectRoot', default='C:/bys360/project')
    args = parser.parse_args()
    root = Path(args.ProjectRoot)
    path = root / 'app' / 'templates' / 'corporate_information_center' / 'recipients.html'
    errors = []
    if not path.exists():
        errors.append(f"Eksik şablon: {path}")
    else:
        text = path.read_text(encoding='utf-8', errors='ignore')
        required = [
            'staff_user_ids',
            'manager_user_ids',
            'cicStaffUserIds',
            'cicManagerUserIds',
            VERSION,
            'function sync(form)',
        ]
        for item in required:
            if item not in text:
                errors.append(f"{path} içinde eksik ifade: {item}")
        if '\\n' in text[:500] or "url_for(\\'static\\'" in text:
            errors.append(f"{path} içinde kaçışlı newline/tırnak kalıntısı var")
    if errors:
        print(f"{VERSION}_GATE_FAIL")
        for e in errors:
            print('HATA:', e)
        return 1
    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
