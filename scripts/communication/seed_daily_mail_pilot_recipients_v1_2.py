from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

PILOT_EMAILS = ["mustafa.bektas@ktb.gov.tr", "havva.ozden@ktb.gov.tr"]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _norm(value: Any) -> str:
    return str(value or "").strip().casefold()


def _full_name(user: Any) -> str:
    parts = [
        getattr(user, "full_name", ""),
    ]
    if not str(parts[0] or "").strip():
        parts = [getattr(user, "ad", ""), getattr(user, "soyad", "")]
    name = " ".join(str(p or "").strip() for p in parts if str(p or "").strip())
    return name or str(getattr(user, "username", "") or getattr(user, "email", "") or getattr(user, "id", ""))


def _email_values(user: Any) -> list[str]:
    values = []
    for attr in ["email", "kurumsal_email", "work_email", "mail"]:
        value = getattr(user, attr, None)
        if value:
            values.append(str(value).strip())
    return values


def _find_by_email(User: Any, email: str) -> Any | None:
    email_norm = _norm(email)
    if not email_norm:
        return None
    users = User.query.filter(User.is_active.is_(True)).all()
    for user in users:
        if any(_norm(v) == email_norm for v in _email_values(user)):
            return user
    # Bazı kayıtlarda email username alanında tutulmuş olabilir.
    for user in users:
        if _norm(getattr(user, "username", "")) == email_norm:
            return user
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 günlük mail pilot alıcılarını e-posta adresine göre kilitler.")
    parser.add_argument("--email", action="append", default=[], help="Pilot alıcı e-posta adresi. Birden fazla verilebilir.")
    parser.add_argument("--disable", action="store_true", help="Günlük hava mailini pasife alır, alıcıları korur.")
    args = parser.parse_args()

    root = _project_root()
    os.chdir(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from app import create_app
    from app.extensions import db
    from app.models import User
    from app.services.daily_weather_mail import (
        current_config,
        ensure_daily_weather_defaults,
        set_setting_value,
    )

    app = create_app()
    with app.app_context():
        ensure_daily_weather_defaults()
        emails = args.email or PILOT_EMAILS
        selected = []
        missing = []
        seen = set()
        for email in emails:
            user = _find_by_email(User, email)
            if not user:
                missing.append(email)
                continue
            uid = int(user.id)
            if uid not in seen:
                seen.add(uid)
                selected.append(user)
        ids = [int(u.id) for u in selected]
        set_setting_value("daily_weather_mail.enabled", "0" if args.disable else "1")
        set_setting_value("daily_weather_mail.recipient_user_ids", json.dumps(ids, ensure_ascii=False))
        set_setting_value("daily_weather_mail.last_sent_date", "")
        set_setting_value("daily_weather_mail.pilot_mode", "1")
        set_setting_value("daily_weather_mail.pilot_emails", json.dumps(emails, ensure_ascii=False))
        db.session.commit()
        result = {
            "ok": bool(ids) and not missing,
            "version": "BYS360_DAILY_MAIL_PILOT_V1_2_EMAIL_RECIPIENTS",
            "selected_count": len(ids),
            "selected": [
                {"id": int(u.id), "name": _full_name(u), "email": str(getattr(u, "email", "") or "")} for u in selected
            ],
            "missing_emails": missing,
            "enabled": current_config().get("enabled"),
            "pilot_mode": True,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
