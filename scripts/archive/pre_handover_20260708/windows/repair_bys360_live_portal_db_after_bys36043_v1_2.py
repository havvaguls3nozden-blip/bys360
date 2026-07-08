
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, text

VERSION = "BYS360_LIVE_PORTAL_DB_FIX_AFTER_BYS36043_V1_2"

SAFE_DEFAULTS: dict[str, str] = {
    "portal_profiles.is_wall_enabled": "true",
    "portal_profiles.default_post_visibility": "'public'",
    "portal_groups.group_type": "'official'",
    "portal_groups.visibility_scope": "'members'",
    "portal_groups.is_active": "true",
    "portal_groups.requires_approval": "true",
    "portal_group_members.member_role": "'member'",
    "portal_group_members.status": "'active'",
    "portal_posts.body": "''",
    "portal_posts.post_type": "'normal'",
    "portal_posts.visibility_scope": "'public'",
    "portal_posts.status": "'published'",
    "portal_posts.comments_enabled": "true",
    "portal_posts.is_pinned": "false",
    "portal_posts.is_featured_home": "false",
    "portal_posts.published_at": "CURRENT_TIMESTAMP",
    "portal_post_reactions.reaction_type": "'like'",
    "portal_post_comments.body": "''",
    "portal_post_comments.status": "'published'",
    "portal_comment_reactions.reaction_type": "'like'",
    "portal_post_reports.reason": "''",
    "portal_post_reports.status": "'open'",
    "portal_moderation_logs.action_type": "'note'",
    "portal_pinned_posts.pin_scope": "'home'",
    "portal_pinned_posts.is_active": "true",
    "portal_activity_logs.entity_type": "'post'",
    "portal_activity_logs.action_type": "'update'",
}

PORTAL_MENU_KEYS = {
    "portal_feed", "portal_people", "portal_profiles", "portal_post_create", "portal_wall_post",
    "portal_post_interact", "portal_post_report", "portal_post_delete", "portal_groups",
    "portal_group_create", "portal_moderation",
}
PORTAL_DEFAULTS = {
    "admin": set(PORTAL_MENU_KEYS),
    "baskan": set(PORTAL_MENU_KEYS),
    "baskan_yardimcisi": set(PORTAL_MENU_KEYS),
    "grup_baskani": set(PORTAL_MENU_KEYS),
    "mali_musavir": set(PORTAL_MENU_KEYS),
    "koordinator": set(PORTAL_MENU_KEYS) - {"portal_moderation"},
    "birim_sorumlusu": set(PORTAL_MENU_KEYS) - {"portal_moderation"},
    "personel": set(PORTAL_MENU_KEYS) - {"portal_group_create", "portal_moderation"},
}
USER_CORE_KEYS = {"portal_feed", "portal_profiles", "portal_people", "portal_groups"}


def q(preparer: Any, name: str) -> str:
    return preparer.quote(name)


def table_exists(conn: Any, table_name: str) -> bool:
    return bool(conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = current_schema() AND table_name = :table_name
        )
    """), {"table_name": table_name}).scalar())


def columns_meta(conn: Any, table_name: str) -> dict[str, dict[str, Any]]:
    rows = conn.execute(text("""
        SELECT column_name, data_type, udt_name, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = :table_name
        ORDER BY ordinal_position
    """), {"table_name": table_name}).mappings().all()
    return {r["column_name"]: dict(r) for r in rows}


def infer_default(table_name: str, column: Any) -> str | None:
    key = f"{table_name}.{column.name}"
    if key in SAFE_DEFAULTS:
        return SAFE_DEFAULTS[key]
    if column.name in {"created_at", "updated_at"}:
        return "CURRENT_TIMESTAMP"
    if column.default is not None and getattr(column.default, "is_scalar", False):
        value = column.default.arg
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            return "'" + value.replace("'", "''") + "'"
        if value is not None:
            return str(value)
    return None


def set_default_and_backfill(conn: Any, preparer: Any, table_name: str, column_name: str, default_sql: str) -> None:
    conn.execute(text(f"ALTER TABLE {q(preparer, table_name)} ALTER COLUMN {q(preparer, column_name)} SET DEFAULT {default_sql}"))
    conn.execute(text(f"UPDATE {q(preparer, table_name)} SET {q(preparer, column_name)} = {default_sql} WHERE {q(preparer, column_name)} IS NULL"))


def add_missing_model_columns(conn: Any, db: Any, portal_models: list[Any]) -> list[str]:
    preparer = db.engine.dialect.identifier_preparer
    added: list[str] = []
    for model in portal_models:
        table = model.__table__
        if not table_exists(conn, table.name):
            table.create(bind=conn, checkfirst=True)
            added.append(f"created_table:{table.name}")
        existing = set(columns_meta(conn, table.name))
        for column in table.columns:
            if column.name in existing:
                continue
            ddl_type = column.type.compile(dialect=db.engine.dialect)
            default = infer_default(table.name, column)
            ddl = f"ALTER TABLE {q(preparer, table.name)} ADD COLUMN IF NOT EXISTS {q(preparer, column.name)} {ddl_type}"
            if default is not None:
                ddl += f" DEFAULT {default}"
            # Eski canlı satırlar patlamasın diye kolon eklerken NOT NULL zorlamıyoruz.
            conn.execute(text(ddl))
            added.append(f"{table.name}.{column.name}")
        # Mevcut kolonların varsayılanlarını/backfill'ini de düzelt.
        current_cols = set(columns_meta(conn, table.name))
        for column in table.columns:
            if column.name in current_cols:
                default = infer_default(table.name, column)
                if default is not None:
                    set_default_and_backfill(conn, preparer, table.name, column.name, default)
    return added


def set_known_legacy_defaults(conn: Any, preparer: Any) -> list[str]:
    changed: list[str] = []
    legacy_defaults: dict[str, dict[str, str]] = {
        "portal_posts": {
            "visibility_type": "'public'",
            "post_type": "'normal'",
            "status": "'published'",
            "comments_enabled": "true",
            "is_pinned": "false",
            "is_featured_home": "false",
            "created_at": "CURRENT_TIMESTAMP",
            "updated_at": "CURRENT_TIMESTAMP",
            "published_at": "CURRENT_TIMESTAMP",
        },
        "portal_groups": {
            "visibility_type": "'members'",
            "visibility_scope": "'members'",
            "group_type": "'official'",
            "status": "'active'",
            "state": "'active'",
            "is_private": "false",
            "is_system": "false",
            "is_locked": "false",
            "is_archived": "false",
            "is_deleted": "false",
            "is_active": "true",
            "requires_approval": "false",
            "allow_member_posts": "false",
            "allow_file_uploads": "false",
            "allow_comments": "true",
            "allow_reactions": "true",
            "post_policy": "'members'",
            "member_policy": "'members'",
            "join_policy": "'approval'",
            "comment_policy": "'members'",
            "reaction_policy": "'members'",
            "created_at": "CURRENT_TIMESTAMP",
            "updated_at": "CURRENT_TIMESTAMP",
        },
        "portal_post_comments": {
            "status": "'published'",
            "created_at": "CURRENT_TIMESTAMP",
            "updated_at": "CURRENT_TIMESTAMP",
        },
        "portal_post_attachments": {
            "created_at": "CURRENT_TIMESTAMP",
            "updated_at": "CURRENT_TIMESTAMP",
        },
    }
    for table_name, defaults in legacy_defaults.items():
        if not table_exists(conn, table_name):
            continue
        cols = columns_meta(conn, table_name)
        for col, default in defaults.items():
            if col in cols:
                set_default_and_backfill(conn, preparer, table_name, col, default)
                changed.append(f"default:{table_name}.{col}")
    return changed


def sync_legacy_aliases(conn: Any, preparer: Any) -> list[str]:
    changed: list[str] = []
    if table_exists(conn, "portal_posts"):
        cols = columns_meta(conn, "portal_posts")
        if {"author_id", "author_user_id"}.issubset(cols):
            conn.execute(text("UPDATE portal_posts SET author_id = author_user_id WHERE author_id IS NULL AND author_user_id IS NOT NULL"))
            conn.execute(text("UPDATE portal_posts SET author_user_id = author_id WHERE author_user_id IS NULL AND author_id IS NOT NULL"))
            changed.append("sync:portal_posts.author_id")
        if {"visibility_type", "visibility_scope"}.issubset(cols):
            conn.execute(text("UPDATE portal_posts SET visibility_type = COALESCE(visibility_type, visibility_scope, 'public') WHERE visibility_type IS NULL"))
            conn.execute(text("UPDATE portal_posts SET visibility_scope = COALESCE(visibility_scope, visibility_type, 'public') WHERE visibility_scope IS NULL"))
            changed.append("sync:portal_posts.visibility")
        if {"created_by_user_id", "author_user_id"}.issubset(cols):
            conn.execute(text("UPDATE portal_posts SET created_by_user_id = author_user_id WHERE created_by_user_id IS NULL AND author_user_id IS NOT NULL"))
            changed.append("sync:portal_posts.created_by_user_id")
    if table_exists(conn, "portal_groups"):
        cols = columns_meta(conn, "portal_groups")
        if {"owner_id", "owner_user_id"}.issubset(cols):
            conn.execute(text("UPDATE portal_groups SET owner_id = owner_user_id WHERE owner_id IS NULL AND owner_user_id IS NOT NULL"))
            changed.append("sync:portal_groups.owner_id")
        if {"created_by_id", "owner_user_id"}.issubset(cols):
            conn.execute(text("UPDATE portal_groups SET created_by_id = owner_user_id WHERE created_by_id IS NULL AND owner_user_id IS NOT NULL"))
            changed.append("sync:portal_groups.created_by_id")
        if {"visibility_type", "visibility_scope"}.issubset(cols):
            conn.execute(text("UPDATE portal_groups SET visibility_type = COALESCE(visibility_type, visibility_scope, 'members') WHERE visibility_type IS NULL"))
            conn.execute(text("UPDATE portal_groups SET visibility_scope = COALESCE(visibility_scope, visibility_type, 'members') WHERE visibility_scope IS NULL"))
            changed.append("sync:portal_groups.visibility")
    if table_exists(conn, "portal_post_comments"):
        cols = columns_meta(conn, "portal_post_comments")
        if {"author_id", "author_user_id"}.issubset(cols):
            conn.execute(text("UPDATE portal_post_comments SET author_id = author_user_id WHERE author_id IS NULL AND author_user_id IS NOT NULL"))
            conn.execute(text("UPDATE portal_post_comments SET author_user_id = author_id WHERE author_user_id IS NULL AND author_id IS NOT NULL"))
            changed.append("sync:portal_post_comments.author_id")
    return changed


def build_trigger(conn: Any, db: Any, table_name: str) -> bool:
    if not table_exists(conn, table_name):
        return False
    cols = columns_meta(conn, table_name)
    preparer = db.engine.dialect.identifier_preparer
    lines: list[str] = []

    def has(c: str) -> bool:
        return c in cols

    def assign(c: str, expr: str) -> None:
        if has(c):
            lines.append(f"IF NEW.{q(preparer, c)} IS NULL THEN NEW.{q(preparer, c)} := {expr}; END IF;")

    if table_name == "portal_posts":
        if has("author_id") and has("author_user_id"):
            lines.append(f"IF NEW.{q(preparer,'author_id')} IS NULL AND NEW.{q(preparer,'author_user_id')} IS NOT NULL THEN NEW.{q(preparer,'author_id')} := NEW.{q(preparer,'author_user_id')}; END IF;")
            lines.append(f"IF NEW.{q(preparer,'author_user_id')} IS NULL AND NEW.{q(preparer,'author_id')} IS NOT NULL THEN NEW.{q(preparer,'author_user_id')} := NEW.{q(preparer,'author_id')}; END IF;")
        if has("visibility_type") and has("visibility_scope"):
            assign("visibility_type", f"COALESCE(NEW.{q(preparer,'visibility_scope')}, 'public')")
            assign("visibility_scope", f"COALESCE(NEW.{q(preparer,'visibility_type')}, 'public')")
        else:
            assign("visibility_type", "'public'")
            assign("visibility_scope", "'public'")
        for col, expr in {"post_type":"'normal'", "status":"'published'", "comments_enabled":"true", "is_pinned":"false", "is_featured_home":"false", "created_at":"CURRENT_TIMESTAMP", "updated_at":"CURRENT_TIMESTAMP", "published_at":"CURRENT_TIMESTAMP"}.items():
            assign(col, expr)
    elif table_name == "portal_groups":
        if has("owner_id") and has("owner_user_id"):
            lines.append(f"IF NEW.{q(preparer,'owner_id')} IS NULL AND NEW.{q(preparer,'owner_user_id')} IS NOT NULL THEN NEW.{q(preparer,'owner_id')} := NEW.{q(preparer,'owner_user_id')}; END IF;")
        if has("created_by_id") and has("owner_user_id"):
            lines.append(f"IF NEW.{q(preparer,'created_by_id')} IS NULL AND NEW.{q(preparer,'owner_user_id')} IS NOT NULL THEN NEW.{q(preparer,'created_by_id')} := NEW.{q(preparer,'owner_user_id')}; END IF;")
        if has("visibility_type") and has("visibility_scope"):
            assign("visibility_type", f"COALESCE(NEW.{q(preparer,'visibility_scope')}, 'members')")
            assign("visibility_scope", f"COALESCE(NEW.{q(preparer,'visibility_type')}, 'members')")
        else:
            assign("visibility_type", "'members'")
            assign("visibility_scope", "'members'")
        for col, expr in {"group_type":"'official'", "status":"'active'", "state":"'active'", "is_private":"false", "is_system":"false", "is_locked":"false", "is_archived":"false", "is_deleted":"false", "is_active":"true", "requires_approval":"false", "allow_member_posts":"false", "allow_file_uploads":"false", "allow_comments":"true", "allow_reactions":"true", "post_policy":"'members'", "member_policy":"'members'", "join_policy":"'approval'", "comment_policy":"'members'", "reaction_policy":"'members'", "created_at":"CURRENT_TIMESTAMP", "updated_at":"CURRENT_TIMESTAMP"}.items():
            assign(col, expr)
    elif table_name == "portal_post_comments":
        if has("author_id") and has("author_user_id"):
            lines.append(f"IF NEW.{q(preparer,'author_id')} IS NULL AND NEW.{q(preparer,'author_user_id')} IS NOT NULL THEN NEW.{q(preparer,'author_id')} := NEW.{q(preparer,'author_user_id')}; END IF;")
            lines.append(f"IF NEW.{q(preparer,'author_user_id')} IS NULL AND NEW.{q(preparer,'author_id')} IS NOT NULL THEN NEW.{q(preparer,'author_user_id')} := NEW.{q(preparer,'author_id')}; END IF;")
        for col, expr in {"status":"'published'", "created_at":"CURRENT_TIMESTAMP", "updated_at":"CURRENT_TIMESTAMP"}.items():
            assign(col, expr)

    if not lines:
        return False
    function_name = f"bys360_{table_name}_live_restore_compat_v1"
    trigger_name = f"trg_bys360_{table_name}_live_restore_compat_v1"
    body = "\n            ".join(lines)
    conn.execute(text(f"""
        CREATE OR REPLACE FUNCTION {function_name}()
        RETURNS trigger AS $$
        BEGIN
            {body}
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))
    conn.execute(text(f"DROP TRIGGER IF EXISTS {trigger_name} ON {q(preparer, table_name)}"))
    conn.execute(text(f"""
        CREATE TRIGGER {trigger_name}
        BEFORE INSERT OR UPDATE ON {q(preparer, table_name)}
        FOR EACH ROW
        EXECUTE FUNCTION {function_name}();
    """))
    return True


def seed_permissions(db: Any, models_module: Any) -> dict[str, int]:
    RoleMenuDefault = getattr(models_module, "RoleMenuDefault")
    UserMenuPermission = getattr(models_module, "UserMenuPermission")
    User = getattr(models_module, "User")
    changes = {"role_inserted": 0, "role_updated": 0, "user_inserted": 0, "user_updated": 0}
    for role, visible_keys in PORTAL_DEFAULTS.items():
        for key in sorted(PORTAL_MENU_KEYS):
            visible = key in visible_keys
            row = RoleMenuDefault.query.filter_by(role_name=role, menu_key=key).first()
            if row is None:
                db.session.add(RoleMenuDefault(role_name=role, menu_key=key, is_visible=visible, source_type="portal_db_fix", note="BYS360 43 sonrası portal DB fix V1.2"))
                changes["role_inserted"] += 1
            elif bool(row.is_visible) != bool(visible):
                row.is_visible = visible
                row.source_type = "portal_db_fix"
                row.note = "BYS360 43 sonrası portal DB fix V1.2"
                changes["role_updated"] += 1
    for user in User.query.filter_by(is_active=True).all():
        for key in sorted(USER_CORE_KEYS):
            row = UserMenuPermission.query.filter_by(user_id=user.id, menu_key=key).first()
            if row is None:
                db.session.add(UserMenuPermission(user_id=user.id, menu_key=key, is_visible=True, source_type="portal_db_fix"))
                changes["user_inserted"] += 1
            elif not bool(row.is_visible):
                row.is_visible = True
                row.source_type = "portal_db_fix"
                changes["user_updated"] += 1
    db.session.commit()
    return changes


def gate(conn: Any, portal_models: list[Any]) -> list[str]:
    errors: list[str] = []
    for model in portal_models:
        table = model.__table__
        if not table_exists(conn, table.name):
            errors.append(f"Eksik portal tablosu: {table.name}")
            continue
        existing = set(columns_meta(conn, table.name))
        for col in table.columns:
            if col.name not in existing:
                errors.append(f"Eksik portal kolonu: {table.name}.{col.name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=os.getcwd())
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    os.chdir(project_root)
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from app import create_app
    from app.extensions import db
    import app.models as models_module
    try:
        from app.models import (
            PortalActivityLog, PortalCommentReaction, PortalGroup, PortalGroupMember,
            PortalModerationLog, PortalPinnedPost, PortalPost, PortalPostAttachment,
            PortalPostAudience, PortalPostComment, PortalPostReaction, PortalPostReport,
            PortalProfile, PortalSavedPost,
        )
    except Exception:
        from app.models.portal_models import (
            PortalActivityLog, PortalCommentReaction, PortalGroup, PortalGroupMember,
            PortalModerationLog, PortalPinnedPost, PortalPost, PortalPostAttachment,
            PortalPostAudience, PortalPostComment, PortalPostReaction, PortalPostReport,
            PortalProfile, PortalSavedPost,
        )
    portal_models = [
        PortalProfile, PortalGroup, PortalGroupMember, PortalPost, PortalPostAudience,
        PortalPostAttachment, PortalPostReaction, PortalPostComment, PortalCommentReaction,
        PortalSavedPost, PortalPostReport, PortalModerationLog, PortalPinnedPost, PortalActivityLog,
    ]

    app = create_app()
    report: dict[str, Any] = {"version": VERSION, "project_root": str(project_root)}
    with app.app_context():
        with db.engine.begin() as conn:
            preparer = db.engine.dialect.identifier_preparer
            report["added"] = add_missing_model_columns(conn, db, portal_models)
            report["legacy_defaults"] = set_known_legacy_defaults(conn, preparer)
            report["legacy_sync"] = sync_legacy_aliases(conn, preparer)
            triggers = []
            for table_name in ("portal_posts", "portal_groups", "portal_post_comments"):
                if build_trigger(conn, db, table_name):
                    triggers.append(table_name)
            report["triggers"] = triggers
            errors = gate(conn, portal_models)
            if errors:
                report["errors"] = errors
                print(json.dumps(report, ensure_ascii=False, indent=2))
                print(f"{VERSION}_GATE_FAIL")
                return 1
        report["permissions"] = seed_permissions(db, models_module)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"{VERSION}_APPLY_OK")
    print(f"{VERSION}_GATE_OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"{VERSION}_FAIL")
        print(str(exc))
        raise
