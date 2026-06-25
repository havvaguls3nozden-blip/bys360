from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import inspect

ROOT = Path(r"C:\bys360\project")
REPORT = ROOT / "reports" / "architecture" / "BYS360_PHASE4A_MESSAGE_COMMENTS_ENSURE_TABLE_V1_REPORT.json"


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).strip()


def find_message_comment_model(db):
    for mapper in db.Model.registry.mappers:
        cls = mapper.class_
        table = getattr(getattr(cls, "__table__", None), "name", None)
        name = getattr(cls, "__name__", "")
        if table == "message_comments" or name == "MessageComment":
            return cls
    return None


def main() -> int:
    branch = git("branch", "--show-current")
    head = git("rev-parse", "--short", "HEAD")

    result = {
        "package": "BYS360_PHASE4A_MESSAGE_COMMENTS_ENSURE_TABLE_V1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "branch": branch,
        "head": head,
        "app_factory_ok": False,
        "sqlite_guard_ok": False,
        "model_found": False,
        "table_existed_before": False,
        "table_exists_after": False,
        "columns_after": [],
        "created_table": False,
        "ensure_ok": False,
        "error": None,
    }

    try:
        from app import create_app, db

        app = create_app()
        result["app_factory_ok"] = True

        with app.app_context():
            backend = db.engine.url.get_backend_name()
            result["db_backend"] = backend

            # Canlıya yanlışlıkla uygulanmasın diye bu adım sadece SQLite local/dev için serbest.
            if backend != "sqlite":
                result["error"] = f"Bu script güvenlik gereği sadece SQLite local/dev DB için çalışır. Backend={backend}"
                REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 2

            result["sqlite_guard_ok"] = True

            model = find_message_comment_model(db)
            result["model_found"] = model is not None

            if model is None:
                result["error"] = "MessageComment/message_comments modeli bulunamadı."
                REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 3

            inspector = inspect(db.engine)
            before_tables = set(inspector.get_table_names())
            result["table_existed_before"] = "message_comments" in before_tables

            if not result["table_existed_before"]:
                model.__table__.create(bind=db.engine, checkfirst=True)
                result["created_table"] = True

            inspector = inspect(db.engine)
            after_tables = set(inspector.get_table_names())
            result["table_exists_after"] = "message_comments" in after_tables

            if result["table_exists_after"]:
                result["columns_after"] = [
                    c["name"] for c in inspector.get_columns("message_comments")
                ]

            required = [
                "id",
                "message_id",
                "user_id",
                "body",
                "is_deleted",
                "edited_at",
                "created_at",
                "updated_at",
            ]

            result["missing_columns_after"] = [
                c for c in required if c not in result["columns_after"]
            ]

            result["ensure_ok"] = bool(
                branch == "phase4a-offline-stabilization-v1"
                and result["app_factory_ok"]
                and result["sqlite_guard_ok"]
                and result["model_found"]
                and result["table_exists_after"]
                and result["missing_columns_after"] == []
            )

    except Exception as exc:
        result["error"] = repr(exc)

    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "ensure_ok": result["ensure_ok"],
        "branch": result["branch"],
        "db_backend": result.get("db_backend"),
        "model_found": result["model_found"],
        "table_existed_before": result["table_existed_before"],
        "created_table": result["created_table"],
        "table_exists_after": result["table_exists_after"],
        "columns_after": result["columns_after"],
        "missing_columns_after": result.get("missing_columns_after"),
        "error": result["error"],
        "report": str(REPORT),
    }, ensure_ascii=False, indent=2))

    return 0 if result["ensure_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
