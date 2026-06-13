from __future__ import annotations

import argparse
from pathlib import Path

VERSION = "BYS360_CIC_V3_0_MAIL_ENGINE_SYSTEM_SENDER_V1_1"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-ProjectRoot", default=r"C:\bys360\project")
    args = ap.parse_args()
    root = Path(args.ProjectRoot)
    service = root / "app" / "services" / "corporate_information_center.py"
    routes = root / "app" / "communication" / "corporate_information_center_routes.py"
    errors = []
    if not service.exists():
        errors.append(f"Eksik service dosyası: {service}")
    else:
        text = service.read_text(encoding="utf-8", errors="replace")
        required = [
            "BYS360_CIC_V3_0_MAIL_ENGINE_SYSTEM_SENDER_V1_1_BEGIN",
            "def _cic_v11_mail_settings",
            "def _cic_v11_send_email_direct",
            "def send_task(task_key",
            "MAIL_SERVER / SMTP_SERVER sistem ayarı bulunamadı",
            "İlk hata:",
            "set_setting(f\"{BASE_KEY}.last_error\"",
        ]
        for item in required:
            if item not in text:
                errors.append(f"service içinde eksik ifade: {item}")
        if text.rfind("def send_task(") < text.find("BYS360_CIC_V3_0_MAIL_ENGINE_SYSTEM_SENDER_V1_1_BEGIN"):
            errors.append("Final send_task bloğu dosyanın sonunda görünmüyor.")
        try:
            compile(text, str(service), "exec")
        except Exception as exc:
            errors.append(f"service Python compile hatası: {type(exc).__name__}: {exc}")
    if not routes.exists():
        errors.append(f"Eksik route dosyası: {routes}")

    if errors:
        print(f"{VERSION}_GATE_FAIL")
        for err in errors:
            print("HATA:", err)
        return 1
    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
