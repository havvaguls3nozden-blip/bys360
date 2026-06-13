from __future__ import annotations
import argparse
from pathlib import Path
import sys

MARKERS = [
    ("app/static/css/corporate_information_center_v3_0_phase4_1.css", "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE4_1_REAL_ADVANCED_UI"),
    ("app/templates/corporate_information_center/base.html", "cic-hero-v4"),
    ("app/templates/corporate_information_center/overview.html", "Görev Akışı"),
    ("app/templates/corporate_information_center/tasks.html", "Görev Yönetimi"),
    ("app/templates/corporate_information_center/recipients.html", "Alıcı Yönetimi"),
    ("app/templates/corporate_information_center/templates.html", "Mail Şablonları"),
    ("app/templates/corporate_information_center/test.html", "Test Merkezi"),
    ("app/templates/corporate_information_center/logs.html", "Gönderim Geçmişi"),
    ("app/templates/corporate_information_center/system.html", "Sistem Ayarları"),
]

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", default=".")
    args = parser.parse_args()
    root = Path(args.ProjectRoot)
    errors=[]
    for rel, marker in MARKERS:
        p = root / rel
        if not p.exists():
            errors.append(f"Eksik dosya: {rel}")
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if marker not in txt:
            errors.append(f"Beklenen arayüz işareti yok: {rel} -> {marker}")
    if errors:
        print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE4_1_REAL_ADVANCED_UI_GATE_FAIL")
        for e in errors:
            print("HATA:", e)
        return 1
    print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE4_1_REAL_ADVANCED_UI_GATE_OK")
    print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE4_1_REAL_ADVANCED_UI_FINAL_OK")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
