from __future__ import annotations

import argparse
import json
import re
from typing import Any

from app import create_app
from app.extensions import db
from app.models import User, SystemSetting

VERSION = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE2_1_RECIPIENT_GROUPS"
PILOT_EMAILS = {"mustafa.bektas@ktb.gov.tr", "havva.ozden@ktb.gov.tr"}
MANAGER_KEYWORDS = (
    "başkan", "baskan", "başkan yardımc", "baskan yardimc", "grup başkan", "grup baskan",
    "koordinatör", "koordinator", "müdür", "mudur", "şef", "sef"
)
EXCLUDE_MANAGER_KEYWORDS = ("personel", "işçi", "isci", "memur", "uzman yardımc", "uzman yardimc")


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    repl = {"ı":"i", "İ":"i", "ğ":"g", "Ğ":"g", "ü":"u", "Ü":"u", "ş":"s", "Ş":"s", "ö":"o", "Ö":"o", "ç":"c", "Ç":"c"}
    for a,b in repl.items(): text = text.replace(a,b)
    return re.sub(r"\s+", " ", text)


def _label(user: User) -> str:
    for parts in (("ad","soyad"), ("first_name","last_name")):
        vals=[]
        for p in parts:
            try: vals.append(str(getattr(user,p,"") or ""))
            except Exception: vals.append("")
        full=" ".join(v for v in vals if v).strip()
        if full: return full
    for attr in ("full_name", "name", "full_name_cache", "username", "email"):
        try:
            v=getattr(user, attr, None)
            if v: return str(v)
        except Exception: pass
    return f"Kullanıcı #{getattr(user,'id','')}"


def _field_text(user: User) -> str:
    parts=[]
    for attr in ("role", "role_name", "role_label", "unvan", "title", "gorev", "position", "birim", "ust_birim", "department"):
        try:
            v=getattr(user, attr, None)
            if v: parts.append(str(v))
        except Exception:
            pass
    return _norm(" ".join(parts))


def _is_active(user: User) -> bool:
    try:
        v = getattr(user, "is_active", True)
        if callable(v): v = v()
        return bool(v)
    except Exception:
        return True


def _email(user: User) -> str:
    try: return str(getattr(user, "email", "") or "").strip().lower()
    except Exception: return ""


def _is_manager(user: User) -> bool:
    txt = _field_text(user)
    if not txt:
        return False
    hit = any(_norm(k) in txt for k in MANAGER_KEYWORDS)
    if not hit:
        return False
    # Başkan, başkan yardımcısı, grup başkanı ve koordinatör her durumda yönetici kabul edilir.
    strong = any(k in txt for k in ("baskan", "grup baskan", "koordinator", "mudur"))
    if strong:
        return True
    return not any(_norm(k) in txt for k in EXCLUDE_MANAGER_KEYWORDS)


def _set_setting(key: str, value: Any, label: str = "") -> None:
    raw = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    row = SystemSetting.query.filter_by(setting_key=key).first()
    if not row:
        row = SystemSetting(setting_key=key, group_key="corporate_information_center", label=label or key, value_type="json" if raw.startswith("[") or raw.startswith("{") else "string")
        db.session.add(row)
    row.value_text = raw
    row.group_key = "corporate_information_center"
    if label:
        row.label = label


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["pilot", "all"], default="all", help="pilot: sadece iki pilot mail; all: aktif personel + tespit edilen yöneticiler")
    ap.add_argument("--staff-all-active", action="store_true", default=True)
    args = ap.parse_args()

    app = create_app()
    with app.app_context():
        users = [u for u in User.query.all() if _is_active(u) and _email(u)]
        pilot = [u for u in users if _email(u) in PILOT_EMAILS]
        managers = [u for u in users if _is_manager(u)]

        # Mustafa Başkan pilot listede ise yönetici alıcılarında mutlaka bulunsun.
        for u in pilot:
            if _email(u) == "mustafa.bektas@ktb.gov.tr" and getattr(u, "id", None) not in {getattr(m,"id",None) for m in managers}:
                managers.append(u)

        if args.mode == "pilot":
            staff_ids = [int(u.id) for u in pilot]
            manager_ids = [int(u.id) for u in pilot if _email(u) == "mustafa.bektas@ktb.gov.tr"] or [int(u.id) for u in pilot]
            staff_mode = "manual"
        else:
            staff_ids = [int(u.id) for u in users]
            manager_ids = [int(u.id) for u in managers]
            staff_mode = "all_active"

        # Yeni Kurumsal Bilgilendirme Merkezi ayarları
        _set_setting("corporate_information_center.staff_recipient_mode", staff_mode, "Personel alıcı modu")
        _set_setting("corporate_information_center.staff_recipient_ids", staff_ids, "Personel alıcıları")
        _set_setting("corporate_information_center.manager_recipient_ids", manager_ids, "Yönetici alıcıları")
        _set_setting("corporate_information_center.pilot_recipient_ids", [int(u.id) for u in pilot], "Pilot alıcıları")

        # Faz 2 otomasyon motoru ayarları: runner bu anahtarları okuyor.
        _set_setting("cic.recipients.staff_ids", staff_ids, "CIC personel alıcıları")
        _set_setting("cic.recipients.manager_ids", manager_ids, "CIC yönetici alıcıları")
        _set_setting("cic.recipients.pilot_ids", [int(u.id) for u in pilot], "CIC pilot alıcıları")
        _set_setting("cic.recipients.mode", args.mode, "CIC alıcı modu")
        db.session.commit()

        payload = {
            "ok": True,
            "version": VERSION,
            "mode": args.mode,
            "staff_count": len(staff_ids),
            "manager_count": len(manager_ids),
            "pilot_count": len(pilot),
            "pilot": [{"id": int(u.id), "name": _label(u), "email": _email(u)} for u in pilot],
            "managers_sample": [{"id": int(u.id), "name": _label(u), "email": _email(u)} for u in managers[:20]],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if not pilot:
            print("UYARI: Pilot alıcılar bulunamadı. Mail adreslerini users.email alanında kontrol edin.")
        if not staff_ids or not manager_ids:
            return 2
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
