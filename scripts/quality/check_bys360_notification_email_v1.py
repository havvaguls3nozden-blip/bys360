from __future__ import annotations

import argparse
import py_compile
from pathlib import Path

REGISTRATION_LINE = '("app.services.notification_mailer", "register_notification_mailer")'


def main() -> None:
    parser = argparse.ArgumentParser(description="BYS360 Notification Email V1 check")
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    service = root / "app/services/notification_mailer.py"
    init_file = root / "app/__init__.py"
    if not service.exists():
        raise FileNotFoundError(service)
    if not init_file.exists():
        raise FileNotFoundError(init_file)
    service_text = service.read_text(encoding="utf-8")
    init_text = init_file.read_text(encoding="utf-8")
    checks = {
        "servis kayıt fonksiyonu": "def register_notification_mailer" in service_text,
        "after_flush dinleyici": "after_flush" in service_text,
        "after_commit mail gönderimi": "after_commit" in service_text,
        "mail log tipi": "system_notification_alert" in service_text,
        "mail_logs kaydı": "INSERT INTO mail_logs" in service_text,
        "uygulama kayıt satırı": REGISTRATION_LINE in init_text,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise RuntimeError("Eksik kontrol: " + ", ".join(failed))
    py_compile.compile(str(service), doraise=True)
    py_compile.compile(str(init_file), doraise=True)
    print("BYS360_NOTIFICATION_EMAIL_V1_CHECK_OK")


if __name__ == "__main__":
    main()
