

"""Excel import sonrasi otomatik hiyerarsi ve gorev yenileme servisi."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections.abc import Iterable

from flask import current_app

from app.extensions import db
from app.models import PerformancePeriod, User
from app.services.auto_hierarchy_service import auto_apply_manager_chains
from app.services.hierarchy_admin_service import ensure_unit_exists_strict, sync_organization_units_from_users
from app.services.assignment_sync_service import sync_assignments_for_active_period


@dataclass(slots=True)
class ExcelAutoPipelineSummary:
    ok: bool
    scope_user_count: int
    relinked_unit_count: int
    chain_updated_count: int
    chain_skipped_count: int
    warnings: list[str]
    active_period_id: int | None
    assignment_created_count: int
    assignment_existing_count: int
    assignment_skipped_count: int
    assignment_warning_count: int
    assignment_info_count: int
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "scope_user_count": self.scope_user_count,
            "relinked_unit_count": self.relinked_unit_count,
            "chain_updated_count": self.chain_updated_count,
            "chain_skipped_count": self.chain_skipped_count,
            "warnings": list(self.warnings or []),
            "active_period_id": self.active_period_id,
            "assignment_created_count": self.assignment_created_count,
            "assignment_existing_count": self.assignment_existing_count,
            "assignment_skipped_count": self.assignment_skipped_count,
            "assignment_warning_count": self.assignment_warning_count,
            "assignment_info_count": self.assignment_info_count,
            "notes": list(self.notes or []),
        }


def _safe(value: Any) -> str:
    return str(value or "").strip()


def _is_system_user(user: User | None) -> bool:
    if not user:
        return True
    role = _safe(getattr(user, "role", "")).lower()
    if role == "admin":
        return True
    if _safe(getattr(user, "birim", "")).lower() == "bys360":
        return True
    if _safe(getattr(user, "ust_birim", "")).lower() == "bys360":
        return True
    return False


def _resolve_scope_users(scope_users: Iterable[User] | None = None, sicils: list[str] | None = None) -> list[User]:
    if scope_users is not None:
        users = list(scope_users)
    elif sicils:
        normalized = {_safe(item) for item in sicils if _safe(item)}
        users = list(User.query.filter(User.sicil_no.in_(normalized)).order_by(User.id.asc()).all())
    else:
        query = User.query.filter(User.role != "admin")
        if hasattr(User, "is_active"):
            query = query.filter(User.is_active == True)  # noqa: E712
        users = list(query.order_by(User.id.asc()).all())
    return [user for user in users if not _is_system_user(user)]


def _relink_units_for_scope(scope_users: list[User]) -> int:
    if not scope_users:
        return 0
    relinked = 0
    for user in scope_users:
        birim = _safe(getattr(user, "birim", ""))
        ust_birim = _safe(getattr(user, "ust_birim", ""))
        if not birim:
            continue
        role = _safe(getattr(user, "role", ""))
        unit = ensure_unit_exists_strict(birim, ust_birim, role)
        if not unit:
            continue
        if getattr(user, "organization_unit_id", None) != unit.id:
            user.organization_unit_id = unit.id
            relinked += 1
    db.session.flush()
    return relinked


def _resolve_active_period_id(explicit_period_id: int | None = None) -> int | None:
    if explicit_period_id:
        return explicit_period_id
    row = (
        PerformancePeriod.query
        .filter_by(is_active=True)
        .order_by(PerformancePeriod.id.desc())
        .first()
    )
    return row.id if row else None


def run_excel_post_import_pipeline(
    *,
    scope_users: Iterable[User] | None = None,
    sicils: list[str] | None = None,
    actor_user_id: int | None = None,
    period_id: int | None = None,
    fill_only_missing: bool = False,
    commit: bool = True,
) -> ExcelAutoPipelineSummary:
    users = _resolve_scope_users(scope_users=scope_users, sicils=sicils)
    warnings: list[str] = []
    notes: list[str] = []

    try:
        relinked_count = _relink_units_for_scope(users) if users else sync_organization_units_from_users(commit=False)

        chain_result = auto_apply_manager_chains(
            users if users else None,
            fill_only_missing=True,
            commit=False,
            preserve_explicit_chain=True,  # BYS360_EXPLICIT_MANAGER_CHAIN_V2
        ) or {}

        raw_warnings = list(chain_result.get("warnings") or [])
        warnings.extend(raw_warnings[:200])

        active_period_id = _resolve_active_period_id(period_id)
        assignment_created = 0
        assignment_existing = 0
        assignment_skipped = 0
        assignment_warning_count = 0
        assignment_info_count = 0

        if active_period_id:
            assignment_result = sync_assignments_for_active_period(
                period_id=active_period_id,
                sicils=[_safe(getattr(user, "sicil_no", "")) for user in users],
                commit=False,
            )
            payload = assignment_result.to_dict()
            assignment_created = int(payload.get("created", 0) or 0)
            assignment_existing = int(payload.get("existing", 0) or 0)
            assignment_skipped = int(payload.get("skipped", 0) or 0)
            assignment_warning_count = int(payload.get("warning_count", 0) or 0)
            assignment_info_count = int(payload.get("info_count", 0) or 0)
            warnings.extend(list(payload.get("warnings") or [])[:200])
            notes.extend(list(payload.get("info_notes") or [])[:50])
            if payload.get("message"):
                notes.append(_safe(payload.get("message")))
        else:
            notes.append("Aktif donem bulunamadi; zincir guncellendi ancak gorev yenilenmedi.")

        if commit:
            db.session.commit()
        else:
            db.session.flush()

        return ExcelAutoPipelineSummary(
            ok=True,
            scope_user_count=len(users),
            relinked_unit_count=relinked_count,
            chain_updated_count=int(chain_result.get("updated_count", 0) or 0),
            chain_skipped_count=int(chain_result.get("skipped_count", 0) or 0),
            warnings=warnings,
            active_period_id=active_period_id,
            assignment_created_count=assignment_created,
            assignment_existing_count=assignment_existing,
            assignment_skipped_count=assignment_skipped,
            assignment_warning_count=assignment_warning_count,
            assignment_info_count=assignment_info_count,
            notes=notes,
        )
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Excel post-import pipeline hata verdi.")
        return ExcelAutoPipelineSummary(
            ok=False,
            scope_user_count=len(users),
            relinked_unit_count=0,
            chain_updated_count=0,
            chain_skipped_count=0,
            warnings=warnings + [f"Pipeline hatasi: {exc}"],
            active_period_id=period_id,
            assignment_created_count=0,
            assignment_existing_count=0,
            assignment_skipped_count=0,
            assignment_warning_count=0,
            assignment_info_count=0,
            notes=notes,
        )