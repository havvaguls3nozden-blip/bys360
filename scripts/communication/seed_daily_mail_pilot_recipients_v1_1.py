from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _norm(value: Any) -> str:
    return str(value or "").strip().casefold()


def _full_name(user: Any) -> str:
    parts = [getattr(user, "ad", ""), getattr(user, "soyad", "")]
    name = " ".join(str(p or "").strip() for p in parts if str(p or "").strip())
    return name or str(getattr(user, "username", "") or getattr(user, "email", "") or getattr(user, "id", ""))


def _haystack(user: Any) -> str:
    values = [
        getattr(user, "ad", ""),
        getattr(user, "soyad", ""),
        getattr(user, "username", ""),
        getattr(user, "email", ""),
        getattr(user, "kurumsal_email", ""),
        getattr(user, "birim", ""),
        getattr(user, "unvan", ""),
        getattr(user, "gorev", ""),
    ]
    return _norm(" | ".join(str(v or "") for v in values))


def _find_one(User: Any, term: str) -> Any | None:
    term_norm = _norm(term)
    if not term_norm:
        return None
    users = User.query.filter(User.is_active.is_(True)).all()
    # 1) Exact full name / exact email / exact username
    for user in users:
        full = _norm(_full_name(user))
        if full == term_norm or _norm(getattr(user, "email", "")) == term_norm or _norm(getattr(user, "username", "")) == term_norm:
            return user
    # 2) All words contained
    words = [w for w in term_norm.replace("@", " ").replace(".", " ").split() if w]
    if words:
        candidates = []
        for user in users:
            h = _haystack(user)
            if all(w in h for w in words):
                candidates.append(user)
        if len(candidates) == 1:
            return candidates[0]
        # Prefer title/name signals for Mustafa Bektaş if more than one Mustafa exists
        if "mustafa" in words:
            for user in candidates:
                h = _haystack(user)
                if "bekta" in h or "personel" in h or "destek" in h or "grup" in h:
                    return user
        if candidates:
            return candidates[0]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 günlük mail pilot alıcılarını sadece seçili iki kişiye kilitler.")
    parser.add_argument("--pilot", action="append", default=[], help="Pilot alıcı arama ifadesi. Örn: 'Mustafa Bektaş' veya 'Gülsen'")
    parser.add_argument("--mustafa", default="Mustafa Bektaş", help="Mustafa Başkan için arama ifadesi")
    parser.add_argument("--gulsen", default="Gülsen", help="Gülsen için arama ifadesi")
    parser.add_argument("--disable", action="store_true", help="Günlük hava mailini pasife alır, alıcıları korur")
    args = parser.parse_args()

    root = _project_root()
    os.chdir(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from app import create_app
    from app.models import User
    from app.services.daily_weather_mail import ensure_daily_weather_defaults, set_setting_value, current_config
    from app.extensions import db

    app = create_app()
    with app.app_context():
        ensure_daily_weather_defaults()
        terms = args.pilot or [args.mustafa, args.gulsen]
        selected = []
        missing = []
        seen = set()
        for term in terms:
            user = _find_one(User, term)
            if not user:
                missing.append(term)
                continue
            uid = int(getattr(user, "id"))
            if uid not in seen:
                seen.add(uid)
                selected.append(user)
        ids = [int(getattr(u, "id")) for u in selected]
        set_setting_value("daily_weather_mail.enabled", "0" if args.disable else "1")
        set_setting_value("daily_weather_mail.recipient_user_ids", json.dumps(ids, ensure_ascii=False))
        # Aynı gün yeniden test edebilmek için pilot kurulumunda tarih kilidini temizliyoruz.
        set_setting_value("daily_weather_mail.last_sent_date", "")
        db.session.commit()
        result = {
            "ok": bool(ids) and not missing,
            "version": "BYS360_DAILY_MAIL_PILOT_V1_1",
            "selected_count": len(ids),
            "selected": [
                {"id": int(getattr(u, "id")), "name": _full_name(u), "email": str(getattr(u, "email", "") or "")} for u in selected
            ],
            "missing": missing,
            "enabled": current_config().get("enabled"),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
