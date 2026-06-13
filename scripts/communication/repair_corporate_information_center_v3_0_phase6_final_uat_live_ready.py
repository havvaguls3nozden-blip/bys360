from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_FINAL_UAT_LIVE_READY"
PHASE5 = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_CONTROL_PANEL"


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


def backup(path: Path, suffix: str = ".phase6_final_uat.bak") -> None:
    if not path.exists():
        return
    bak = path.with_suffix(path.suffix + suffix)
    if not bak.exists():
        shutil.copy2(path, bak)


def remove_service_block(text: str) -> str:
    pattern = r"\n?#\s*" + re.escape(VERSION) + r"_BEGIN.*?#\s*" + re.escape(VERSION) + r"_END\n?"
    return re.sub(pattern, "\n", text, flags=re.DOTALL)


def overlay_payload_root(root: Path) -> Path:
    return root / "overlay_payload"


def copy_payload_file(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Payload dosyası bulunamadı: {src}")
    backup(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def patch_service(root: Path) -> None:
    path = root / "app" / "services" / "corporate_information_center.py"
    block_path = overlay_payload_root(root) / "service_blocks" / "phase6_service_block.py.txt"
    if not path.exists():
        raise FileNotFoundError(f"Kurumsal bilgilendirme service dosyası bulunamadı: {path}")
    text = read_text(path)
    if "def context(" not in text:
        raise RuntimeError("Beklenen context fonksiyonu bulunamadı; önce Faz 3/5 paketleri uygulanmalı.")
    backup(path)
    block = read_text(block_path).strip()
    text = remove_service_block(text).rstrip() + "\n\n" + block + "\n"
    write_text(path, text)


def patch_templates(root: Path) -> None:
    payload = overlay_payload_root(root) / "app" / "templates" / "corporate_information_center"
    target = root / "app" / "templates" / "corporate_information_center"
    for name in ["base.html", "overview.html", "tasks.html", "recipients.html", "templates.html", "test.html", "logs.html", "system.html"]:
        copy_payload_file(payload / name, target / name)
    copy_payload_file(overlay_payload_root(root) / "app" / "static" / "css" / "corporate_information_center_v3_0_phase5.css", root / "app" / "static" / "css" / "corporate_information_center_v3_0_phase5.css")
    copy_payload_file(overlay_payload_root(root) / "app" / "static" / "css" / "corporate_information_center_v3_0_phase6.css", root / "app" / "static" / "css" / "corporate_information_center_v3_0_phase6.css")


def run_compile(root: Path) -> None:
    py = root / ".venv" / "Scripts" / "python.exe"
    python = str(py) if py.exists() else sys.executable
    files = [root / "app" / "services" / "corporate_information_center.py", root / "app" / "communication" / "corporate_information_center_routes.py"]
    res = subprocess.run([python, "-m", "py_compile", *[str(f) for f in files if f.exists()]], cwd=str(root), text=True, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError((res.stdout or "") + (res.stderr or ""))


def gate(root: Path) -> list[str]:
    checks: list[str] = []
    required = {
        root / "app/services/corporate_information_center.py": [VERSION, "def _cic_phase6_build", "phase6_uat_score", "_cic_phase6_previous_context"],
        root / "app/templates/corporate_information_center/base.html": [VERSION, "corporate_information_center_v3_0_phase6.css", "Final UAT"],
        root / "app/templates/corporate_information_center/overview.html": [VERSION, "Final UAT ve Canlı Hazırlık Paneli", "phase6.uat_score"],
        root / "app/templates/corporate_information_center/tasks.html": [VERSION, "Görev Çalıştırma Güvenlik Kapısı", "phase6.top_checks"],
        root / "app/templates/corporate_information_center/recipients.html": [VERSION, "Alıcı Veri Kalitesi", "phase6.recipient_quality"],
        root / "app/templates/corporate_information_center/templates.html": [VERSION, "Şablon Canlı Yayın Kontrolü", "phase6.template_quality"],
        root / "app/templates/corporate_information_center/test.html": [VERSION, "Gerçek Gönderim Son Kontrol Kapısı", "phase6.final_send_checks"],
        root / "app/templates/corporate_information_center/logs.html": [VERSION, "Denetim ve İzlenebilirlik Özeti", "phase6.log_quality"],
        root / "app/templates/corporate_information_center/system.html": [VERSION, "Final UAT Senaryo Kapısı", "phase6.scenarios"],
        root / "app/static/css/corporate_information_center_v3_0_phase6.css": [VERSION, "cic-phase6-scenarios", "cic-phase6-live-gate"],
    }
    for path, needles in required.items():
        if not path.exists():
            checks.append(f"Eksik dosya: {path}")
            continue
        text = read_text(path)
        for needle in needles:
            if needle not in text:
                checks.append(f"{path} içinde eksik ifade: {needle}")
    # CSRF token check in all POST forms
    for name in ["tasks.html", "recipients.html", "templates.html", "test.html", "system.html"]:
        p = root / "app/templates/corporate_information_center" / name
        if p.exists():
            t = read_text(p)
            if 'method="post"' in t.lower() and "cic_csrf()" not in t and "csrf_token" not in t:
                checks.append(f"{p} içinde CSRF token görünmüyor")
    try:
        run_compile(root)
    except Exception as exc:
        checks.append(str(exc))
    return checks


def write_uat_report(root: Path) -> None:
    report = root / "docs" / "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_UAT_LIVE_READY_REPORT.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(f"""# BYS360 Kurumsal Bilgilendirme Merkezi V3.0 Faz 6 UAT ve Canlı Hazırlık

Bu rapor, Faz 6 overlay uygulandıktan sonra sistemde bulunması gereken final UAT ve canlı hazırlık kapılarını özetler.

## Kontrol edilen ekranlar
- Genel Bakış
- Görevler
- Alıcılar
- Şablonlar
- Test Merkezi
- Gönderim Geçmişi
- Sistem

## UAT senaryoları
1. Kuru çalışma testi
2. Gerçek gönderim uyarısı
3. E-postası olmayan personel
4. Pasif personel kontrolü
5. Boş şablon kontrolü
6. Eksik konu kontrolü
7. Büyük alıcı grubu
8. SMTP ayarı
9. Başarılı gönderim logu
10. Başarısız gönderim logu

## Beklenen sonuç
Sistem ekranında Final UAT Senaryo Kapısı görünmeli; canlıya geçmeden önce kritik uyarılar kapatılmalıdır.

Versiyon: {VERSION}
""", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root_pos", nargs="?", default=None)
    parser.add_argument("--project-root", "-ProjectRoot", dest="project_root", default=None)
    parser.add_argument("--mode", "-Mode", dest="mode", default="all")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.project_root or args.project_root_pos or ".").resolve()
    print("BYS360 Kurumsal Bilgilendirme Merkezi Faz 6 Final UAT ve Canlı Hazırlık uygulanıyor...")
    print(f"ProjectRoot={root}")
    patch_service(root)
    patch_templates(root)
    write_uat_report(root)
    errors = gate(root)
    if errors:
        print(f"{VERSION}_GATE_FAIL")
        for err in errors:
            print("HATA:", err)
        return 2
    print(f"{VERSION}_APPLY_OK")
    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    print("Güncellenen dosyalar:")
    for rel in [
        "app/services/corporate_information_center.py",
        "app/templates/corporate_information_center/base.html",
        "app/templates/corporate_information_center/overview.html",
        "app/templates/corporate_information_center/tasks.html",
        "app/templates/corporate_information_center/recipients.html",
        "app/templates/corporate_information_center/templates.html",
        "app/templates/corporate_information_center/test.html",
        "app/templates/corporate_information_center/logs.html",
        "app/templates/corporate_information_center/system.html",
        "app/static/css/corporate_information_center_v3_0_phase6.css",
        "docs/BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_UAT_LIVE_READY_REPORT.md",
    ]:
        print(" -", rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
