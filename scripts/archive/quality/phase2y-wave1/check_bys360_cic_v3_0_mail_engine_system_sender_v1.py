from __future__ import annotations
import argparse
from pathlib import Path
VERSION="BYS360_CIC_V3_0_MAIL_ENGINE_SYSTEM_SENDER_V1"

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("-ProjectRoot", default=r"C:\bys360\project"); args=ap.parse_args()
    root=Path(args.ProjectRoot)
    service=root/"app/services/corporate_information_center.py"
    routes=root/"app/communication/corporate_information_center_routes.py"
    errors=[]
    if not service.exists(): errors.append(f"Eksik service: {service}")
    else:
        text=service.read_text(encoding="utf-8", errors="replace")
        for token in [VERSION, "def _cic_mail_settings", "def _cic_send_email_direct", "MAIL_DEFAULT_SENDER", "SMTP_SERVER", "İlk hata", "last_error"]:
            if token not in text:
                errors.append(f"service içinde eksik ifade: {token}")
        if "ok, msg = send_email(" in text:
            errors.append("send_task hâlâ eski send_email çağrısını kullanıyor")
    if not routes.exists(): errors.append(f"Eksik routes: {routes}")
    if errors:
        print(f"{VERSION}_GATE_FAIL")
        for e in errors: print("HATA:", e)
        return 1
    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
