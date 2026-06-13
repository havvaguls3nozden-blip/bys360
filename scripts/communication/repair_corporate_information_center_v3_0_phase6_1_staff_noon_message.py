from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = 'BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_1_STAFF_NOON_MESSAGE'
BASE_KEY = "corporate_information_center"
NEW_SUBJECT = 'BYS360 Gün Ortası Destek Hatırlatması'
NEW_BODY = 'Sayın {ad_soyad},\n\nGününüz nasıl geçiyor?\n\nSistemde destek ihtiyacı duyduğunuz bir konu var mı?\n\nBYS360 kullanımı sırasında destek, öneri, hata bildirimi veya geliştirme ihtiyacı oluşursa Geri Bildirim Merkezi üzerinden bize iletebilirsiniz.\n\nGeri bildirim bağlantısı:\n{geri_bildirim_baglantisi}\n\nİyi çalışmalar dileriz.\n\nBYS360\nÇanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı'


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def backup(path: Path, suffix: str = ".phase6_1_noon_message.bak") -> None:
    if not path.exists():
        return
    bak = path.with_suffix(path.suffix + suffix)
    if not bak.exists():
        shutil.copy2(path, bak)


def _replace_staff_noon_block(text: str) -> str:
    start = text.find('"staff_noon"')
    if start < 0:
        raise RuntimeError("staff_noon görev tanımı bulunamadı.")
    end = text.find('"staff_evening"', start)
    if end < 0:
        raise RuntimeError("staff_noon görev tanımı sonu bulunamadı.")
    block = text[start:end]
    if VERSION not in text:
        block = "# " + VERSION + "\n    " + block.lstrip()
    block = re.sub(r'"subject"\s*:\s*"[^"]*"', '"subject": ' + repr(NEW_SUBJECT).replace("'", '"'), block, count=1)
    block = re.sub(r'"body"\s*:\s*""".*?"""', '"body": """' + NEW_BODY + '"""', block, count=1, flags=re.DOTALL)
    return text[:start] + block + text[end:]


def patch_service_file(root: Path) -> None:
    path = root / "app" / "services" / "corporate_information_center.py"
    if not path.exists():
        raise FileNotFoundError(f"Kurumsal Bilgilendirme servis dosyası bulunamadı: {path}")
    text = read_text(path)
    backup(path)
    text = _replace_staff_noon_block(text)
    write_text(path, text)


def update_database_setting(root: Path) -> str:
    # Mevcut sistem ayarı varsa onu da günceller; çünkü get_template önce system_settings değerini okur.
    sys.path.insert(0, str(root))
    try:
        from wsgi import app  # type: ignore
        from app.services.corporate_information_center import set_setting  # type: ignore
        from app.extensions import db  # type: ignore
        with app.app_context():
            set_setting(f"{BASE_KEY}.template.staff_noon.subject", NEW_SUBJECT, label="Personel Öğlen Bilgilendirmesi konusu", value_type="string")
            set_setting(f"{BASE_KEY}.template.staff_noon.body", NEW_BODY, label="Personel Öğlen Bilgilendirmesi metni", value_type="text")
            db.session.commit()
        return "DB_OK"
    except Exception as exc:
        return "DB_WARNING: " + str(exc)[:240]


def run_compile(root: Path) -> None:
    py = root / ".venv" / "Scripts" / "python.exe"
    python = str(py) if py.exists() else sys.executable
    target = root / "app" / "services" / "corporate_information_center.py"
    res = subprocess.run([python, "-m", "py_compile", str(target)], cwd=str(root), text=True, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError((res.stdout or "") + (res.stderr or ""))


def gate(root: Path, check_db: bool = False) -> list[str]:
    checks: list[str] = []
    path = root / "app" / "services" / "corporate_information_center.py"
    if not path.exists():
        checks.append(f"Eksik dosya: {path}")
    else:
        text = read_text(path)
        for needle in [VERSION, '"staff_noon"', "Gününüz nasıl geçiyor?", "Sistemde destek ihtiyacı duyduğunuz bir konu var mı?", "BYS360 Gün Ortası Destek Hatırlatması"]:
            if needle not in text:
                checks.append(f"{path} içinde eksik ifade: {needle}")
    try:
        run_compile(root)
    except Exception as exc:
        checks.append(str(exc))
    if check_db:
        sys.path.insert(0, str(root))
        try:
            from wsgi import app  # type: ignore
            from app.services.corporate_information_center import get_template  # type: ignore
            with app.app_context():
                tmpl = get_template("staff_noon")
                body = tmpl.get("body", "")
                subject = tmpl.get("subject", "")
                if "Gününüz nasıl geçiyor?" not in body:
                    checks.append("Veritabanındaki staff_noon şablonu güncel görünmüyor.")
                if NEW_SUBJECT not in subject:
                    checks.append("Veritabanındaki staff_noon konusu güncel görünmüyor.")
        except Exception as exc:
            checks.append("DB kontrolü yapılamadı: " + str(exc)[:240])
    return checks


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("project_root_pos", nargs="?", default=None)
    p.add_argument("--project-root", "-ProjectRoot", dest="project_root", default=None)
    p.add_argument("--mode", "-Mode", dest="mode", default="all")
    p.add_argument("--check-db", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.project_root or args.project_root_pos or ".").resolve()
    print("BYS360 Kurumsal Bilgilendirme Merkezi gün ortası mail metni güncelleniyor...")
    print(f"ProjectRoot={root}")
    patch_service_file(root)
    db_status = update_database_setting(root)
    print(db_status)
    checks = gate(root, check_db=False)
    if checks:
        print(VERSION + "_GATE_FAIL")
        for c in checks:
            print("HATA:", c)
        return 2
    print(VERSION + "_APPLY_OK")
    print(VERSION + "_GATE_OK")
    print(VERSION + "_FINAL_OK")
    print("Güncellenen görev: staff_noon / Personel Öğlen Bilgilendirmesi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
