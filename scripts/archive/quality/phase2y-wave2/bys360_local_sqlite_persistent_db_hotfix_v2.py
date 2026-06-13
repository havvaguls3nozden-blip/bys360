from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple


def _mask_uri(uri: str) -> str:
    if not uri:
        return ""
    if "@" in uri and "://" in uri:
        prefix, rest = uri.split("://", 1)
        if "@" in rest:
            host = rest.split("@", 1)[1]
            return f"{prefix}://***:***@{host}"
    return uri


def _sqlite_uri_from_path(path: Path) -> str:
    return "sqlite:///" + path.resolve().as_posix()


def _import_app_and_db() -> Tuple[Any, Any, str]:
    app_mod = importlib.import_module("app")
    create_app = getattr(app_mod, "create_app", None)
    if create_app is None:
        raise RuntimeError("app.create_app bulunamadi")

    db_obj = getattr(app_mod, "db", None)
    if db_obj is None:
        for candidate in ("app.extensions", "app.database", "app.models"):
            try:
                mod = importlib.import_module(candidate)
                db_obj = getattr(mod, "db", None)
                if db_obj is not None:
                    break
            except Exception:
                continue
    if db_obj is None:
        raise RuntimeError("Flask-SQLAlchemy db nesnesi bulunamadi")
    return create_app, db_obj, getattr(db_obj, "__module__", "unknown")


def _import_user_model() -> Tuple[Optional[Any], str]:
    candidates = [
        "app.models",
        "app.models.user",
        "app.models.users",
        "app.auth.models",
        "app.personnel.models",
    ]
    for name in candidates:
        try:
            mod = importlib.import_module(name)
        except Exception:
            continue
        user = getattr(mod, "User", None)
        if user is not None:
            return user, name + ".User"
    return None, ""


def _table_names(db_obj: Any) -> list[str]:
    try:
        inspector = db_obj.inspect(db_obj.engine)  # type: ignore[attr-defined]
    except Exception:
        try:
            from sqlalchemy import inspect

            inspector = inspect(db_obj.engine)
        except Exception:
            return []
    try:
        return sorted(inspector.get_table_names())
    except Exception:
        return []


def _set_attr_if_column(obj: Any, columns: Iterable[str], name: str, value: Any) -> None:
    if name in columns and hasattr(obj, name):
        try:
            setattr(obj, name, value)
        except Exception:
            pass


def _seed_local_admin(db_obj: Any, email: str, password: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "requested": bool(email and password),
        "created": False,
        "updated": False,
        "email": email,
        "password_set": False,
        "user_model_path": "",
        "error": "",
    }
    if not email or not password:
        result["error"] = "email/password verilmedi"
        return result

    User, user_path = _import_user_model()
    result["user_model_path"] = user_path
    if User is None:
        result["error"] = "User modeli bulunamadi"
        return result

    try:
        from werkzeug.security import generate_password_hash

        columns = set(getattr(User, "__table__").columns.keys())
        q = None
        if "email" in columns:
            q = User.query.filter_by(email=email).first()
        if q is None and "sicil_no" in columns:
            q = User.query.filter_by(sicil_no=email).first()

        if q is None:
            q = User()
            result["created"] = True
            db_obj.session.add(q)
        else:
            result["updated"] = True

        _set_attr_if_column(q, columns, "email", email)
        _set_attr_if_column(q, columns, "sicil_no", email)
        _set_attr_if_column(q, columns, "password_hash", generate_password_hash(password))
        _set_attr_if_column(q, columns, "ad", "BYS360")
        _set_attr_if_column(q, columns, "soyad", "Local")
        _set_attr_if_column(q, columns, "full_name", "BYS360 Local Admin")
        _set_attr_if_column(q, columns, "full_name_cache", "BYS360 Local Admin")
        _set_attr_if_column(q, columns, "role", "admin")
        _set_attr_if_column(q, columns, "role_label", "Admin")
        _set_attr_if_column(q, columns, "unvan", "Local Admin")
        _set_attr_if_column(q, columns, "birim", "BYS360 Local")
        _set_attr_if_column(q, columns, "ust_birim", "BYS360 Local")
        _set_attr_if_column(q, columns, "is_active", True)
        _set_attr_if_column(q, columns, "failed_login_attempts", 0)
        _set_attr_if_column(q, columns, "captcha_required", False)
        _set_attr_if_column(q, columns, "must_change_password", False)
        _set_attr_if_column(q, columns, "must_set_security_question", False)
        _set_attr_if_column(q, columns, "is_first_login", False)
        db_obj.session.commit()
        result["password_set"] = True
    except Exception as exc:  # noqa: BLE001 - report-only repair script
        try:
            db_obj.session.rollback()
        except Exception:
            pass
        result["error"] = repr(exc)
    return result


def run(root: Path, db_path: Path, create_local_admin: bool, email: str, password: str, allow_non_sqlite: bool) -> Dict[str, Any]:
    root = root.resolve()
    db_path = db_path.resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    reports_dir = root / "reports" / "local"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "BYS360_LOCAL_SQLITE_PERSISTENT_DB_HOTFIX_V2_REPORT.json"

    uri = _sqlite_uri_from_path(db_path)
    os.environ.setdefault("FLASK_APP", "app:create_app")
    os.environ["FLASK_ENV"] = os.environ.get("FLASK_ENV", "development")
    os.environ["APP_ENV"] = os.environ.get("APP_ENV", "development")
    os.environ["BYS360_ENV"] = os.environ.get("BYS360_ENV", "development")
    for key in (
        "DATABASE_URL",
        "SQLALCHEMY_DATABASE_URI",
        "BYS360_DATABASE_URL",
        "BYS360_SQLALCHEMY_DATABASE_URI",
        "APP_DATABASE_URL",
    ):
        os.environ[key] = uri

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    report: Dict[str, Any] = {
        "ok": False,
        "package": "BYS360_LOCAL_SQLITE_PERSISTENT_DB_HOTFIX_V2",
        "root": str(root),
        "mode": "local_sqlite_persistent_db_bootstrap",
        "live_safe": True,
        "target_sqlite_path": str(db_path),
        "target_database_uri_masked": _mask_uri(uri),
        "allow_non_sqlite": allow_non_sqlite,
    }

    try:
        create_app, db_obj, db_module = _import_app_and_db()
        app = create_app()
        effective_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        sqlite_detected = str(effective_uri).startswith("sqlite")
        persistent_sqlite_detected = sqlite_detected and ":memory:" not in str(effective_uri)
        report.update(
            {
                "db_module": db_module,
                "effective_database_uri_masked": _mask_uri(str(effective_uri)),
                "sqlite_detected": sqlite_detected,
                "persistent_sqlite_detected": persistent_sqlite_detected,
            }
        )

        if (not sqlite_detected) and (not allow_non_sqlite):
            report["error"] = "Uygulama SQLite disi DB ile acildi; local hotfix canli/PostgreSQL'e dokunmamak icin durdu."
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            return report
        if sqlite_detected and ":memory:" in str(effective_uri):
            report["error"] = "Uygulama hala sqlite:///:memory: ile aciliyor. Config env DB URI okumuyor olabilir. start_bys360_local_sqlite_persistent.ps1 ile baslatin."
            # Still try create_all for diagnostic, but do not mark ok.

        with app.app_context():
            before = _table_names(db_obj)
            report.update(
                {
                    "before_table_count": len(before),
                    "before_has_users": "users" in before,
                    "before_has_audit_logs": "audit_logs" in before,
                }
            )
            db_obj.create_all()
            after = _table_names(db_obj)
            report.update(
                {
                    "after_table_count": len(after),
                    "after_has_users": "users" in after,
                    "after_has_audit_logs": "audit_logs" in after,
                    "created_or_verified_tables": "users" in after and "audit_logs" in after,
                }
            )
            user_count_before = None
            user_count_after = None
            User, user_model_path = _import_user_model()
            report["user_model_path"] = user_model_path
            if User is not None:
                try:
                    user_count_before = int(User.query.count())
                except Exception:
                    user_count_before = None
            report["user_count_before_admin_seed"] = user_count_before
            if create_local_admin:
                report["local_admin"] = _seed_local_admin(db_obj, email, password)
            else:
                report["local_admin"] = {"requested": False}
            if User is not None:
                try:
                    user_count_after = int(User.query.count())
                except Exception:
                    user_count_after = None
            report["user_count_after"] = user_count_after

        db_file_exists = db_path.exists() and db_path.stat().st_size > 0
        report["db_file_exists"] = db_file_exists
        report["db_file_size_bytes"] = db_path.stat().st_size if db_path.exists() else 0
        report["start_script"] = str(root / "scripts" / "windows" / "start_bys360_local_sqlite_persistent.ps1")
        report["ok"] = bool(
            persistent_sqlite_detected
            and report.get("created_or_verified_tables")
            and report.get("after_has_users")
            and report.get("after_has_audit_logs")
            and db_file_exists
            and (not create_local_admin or report.get("local_admin", {}).get("password_set"))
        )
    except Exception as exc:  # noqa: BLE001 - repair script writes diagnostic report
        report["error"] = repr(exc)

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["report"] = str(report_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--db-path", default="")
    parser.add_argument("--create-local-admin", action="store_true")
    parser.add_argument("--local-admin-email", default="bys360@ktb.gov.tr")
    parser.add_argument("--local-admin-password", default="")
    parser.add_argument("--allow-non-sqlite", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    db_path = Path(args.db_path) if args.db_path else root / "instance" / "bys360_local_dev.sqlite3"
    report = run(
        root=root,
        db_path=db_path,
        create_local_admin=args.create_local_admin,
        email=args.local_admin_email,
        password=args.local_admin_password,
        allow_non_sqlite=args.allow_non_sqlite,
    )
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
