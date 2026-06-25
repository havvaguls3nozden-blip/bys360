from __future__ import annotations

"""BYS360 Sistem Yöneticisi e-posta final kontrolü V2.16.1."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

OLD_EMAIL = "admin" + "@ktb.gov.tr"
NEW_EMAIL = "bys360" + "@ktb.gov.tr"
VERSION = "BYS360_SYSTEM_ADMIN_EMAIL_V2_16_1_CHECKFIX_CHECK"


def load_dotenv_safely(root: Path) -> None:
    env_path = root / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(env_path, override=False)
        return
    except Exception:
        pass
    try:
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        return


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _user_payload(user: Any) -> dict[str, Any] | None:
    if user is None:
        return None
    return {
        "id": int(user.id),
        "email": getattr(user, "email", None),
        "role": getattr(user, "role", None),
        "unvan": getattr(user, "unvan", None),
        "is_active": bool(getattr(user, "is_active", False)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=VERSION)
    parser.add_argument("--project-root", default=r"C:\bys360\project")
    args = parser.parse_args()

    root = Path(args.project_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"ProjectRoot bulunamadı: {root}")

    load_dotenv_safely(root)
    sys.path.insert(0, str(root))

    from sqlalchemy import func  # type: ignore

    from app import create_app  # type: ignore
    from app.models import User  # type: ignore

    app = create_app()
    with app.app_context():
        old_users = User.query.filter(func.lower(User.email) == OLD_EMAIL).order_by(User.id.asc()).all()
        target = User.query.filter(func.lower(User.email) == NEW_EMAIL).order_by(User.id.asc()).first()
        admin_users = User.query.filter(func.lower(func.coalesce(User.role, "")) == "admin").order_by(User.id.asc()).all()

        payload = {
            "version": VERSION,
            "expected_old_email_absent": OLD_EMAIL,
            "expected_admin_email_present": NEW_EMAIL,
            "old_email_count": len(old_users),
            "target_exists": target is not None,
            "target": _user_payload(target),
            "admin_user_count": len(admin_users),
            "admin_users": [_user_payload(u) for u in admin_users[:10]],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))

        if old_users:
            print("CHECK_FAIL: admin@ktb.gov.tr veritabanında hâlâ kullanıcı e-postası olarak mevcut.")
            return 2
        if target is None:
            print("CHECK_FAIL: bys360@ktb.gov.tr admin kullanıcı kaydı bulunamadı.")
            return 2
        if _norm(getattr(target, "role", "")) != "admin":
            print("CHECK_FAIL: bys360@ktb.gov.tr kullanıcısının rolü admin değil.")
            return 2
        if hasattr(target, "is_active") and not bool(getattr(target, "is_active", False)):
            print("CHECK_FAIL: bys360@ktb.gov.tr admin kullanıcısı aktif değil.")
            return 2

    print(f"{VERSION}_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
