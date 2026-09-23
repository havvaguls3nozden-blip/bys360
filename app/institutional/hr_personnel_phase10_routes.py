from __future__ import annotations

# STATUS: ACTIVE
# BYS360_ROUTE_STATUS: ACTIVE_CHILD_IMPORT
# STATUS_SOURCE: app.institutional.routes LOADED_CHILD_ROUTE_MODULES
import logging
from collections import defaultdict
from datetime import date, timedelta

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import inspect

from app.extensions import db
from app.models import (
    PersonnelAssetAssignment,
    PersonnelAssetTransferLog,
    PersonnelDocument,
    PersonnelDocumentReminderLog,
    User,
)
from app.route_registry import main_bp
from app.route_support import (
    consume_form_token,
    issue_form_token,
    manager_required,
    menu_key_required,
    safe_db_rollback,
    safe_render,
)

from .hr_personnel_extension_routes import (
    _current_scope_bundle,
    _full_name,
    _normalize_text,
    _parse_date,
    _safe_int,
)

logger = logging.getLogger(__name__)

MONTH_LABELS = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
    7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık",
}
TRANSFER_STATUS_LABELS = {
    "completed": "Tamamlandı",
    "pending": "Beklemede",
    "cancelled": "İptal",
}


def _table_exists(table_name: str) -> bool:
    try:
        return table_name in set(inspect(db.engine).get_table_names())
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_personnel_phase10_routes.py:51")
        return False


def _scope_user_options(scope_users: list[User]) -> list[dict[str, object]]:
    rows = []
    for user in scope_users:
        rows.append({
            "id": int(user.id),
            "full_name": _full_name(user),
            "unit_name": (getattr(user, "birim", None) or getattr(user, "ust_birim", None) or "-").strip() or "-",
        })
    return rows


def _selected_user(scope_users: list[User], scope_user_ids: set[int]) -> User | None:
    selected_user_id = _safe_int(request.args.get("user_id") or request.form.get("user_id"))
    if selected_user_id and selected_user_id in scope_user_ids:
        return db.session.get(User, int(selected_user_id))
    return scope_users[0] if scope_users else None


def _asset_in_scope(asset_id: int | None, scope_user_ids: set[int]) -> PersonnelAssetAssignment:
    if not asset_id:
        raise ValueError("Zimmet kaydı bulunamadı.")
    row = PersonnelAssetAssignment.query.filter(
        PersonnelAssetAssignment.id == int(asset_id),
        PersonnelAssetAssignment.user_id.in_(list(scope_user_ids)),
    ).first()
    if not row:
        raise ValueError("Zimmet kaydı bu kapsam içinde bulunamadı.")
    return row


def _require_user_in_scope(user_id: int | None, scope_user_ids: set[int]) -> User:
    if not user_id or user_id not in scope_user_ids:
        raise ValueError("Seçilen personel bu kapsam içinde görünmüyor.")
    user = db.session.get(User, int(user_id))
    if not user:
        raise ValueError("Personel kaydı bulunamadı.")
    return user


def _transfer_status_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return TRANSFER_STATUS_LABELS.get(raw, "Bilinmiyor" if raw else "-")


def _document_category_label(value: str | None) -> str:
    raw = (value or "").strip()
    return raw.replace("_", " ").replace("-", " ").title() if raw else "Belge"


@main_bp.route("/hr-management/personnel-operations/dashboard")
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_dashboard():
    hr_scope, scope_users, scope_user_ids = _current_scope_bundle()
    selected_scope_mode = (hr_scope or {}).get("scope_mode") or "personal"
    today = date.today()
    dashboard_ready = all(
        _table_exists(name)
        for name in [
            "personnel_documents",
            "personnel_asset_assignments",
            "personnel_document_reminder_logs",
            "personnel_asset_transfer_logs",
        ]
    )
    stats = {
        "personnel_count": len(scope_user_ids),
        "expiring_30": 0,
        "expired": 0,
        "active_assets": 0,
        "overdue_assets": 0,
        "transfers_30": 0,
        "queued_reminders": 0,
    }
    expiring_rows: list[dict[str, object]] = []
    overdue_asset_rows: list[dict[str, object]] = []
    recent_transfer_rows: list[dict[str, object]] = []
    if dashboard_ready and scope_user_ids:
        docs = (
            PersonnelDocument.query
            .filter(PersonnelDocument.user_id.in_(list(scope_user_ids)), PersonnelDocument.expiry_date.isnot(None))
            .order_by(PersonnelDocument.expiry_date.asc(), PersonnelDocument.id.desc())
            .all()
        )
        for row in docs:
            days_left = (row.expiry_date - today).days if row.expiry_date else None
            if days_left is None:
                continue
            if days_left < 0:
                stats["expired"] += 1
            if days_left <= 30:
                stats["expiring_30"] += 1
                expiring_rows.append({
                    "user_id": int(row.user_id),
                    "user_name": _full_name(getattr(row, "user", None)),
                    "title": row.title or "Belge",
                    "category": _document_category_label(row.category),
                    "expiry_date": row.expiry_date,
                    "days_left": days_left,
                })
        assets = (
            PersonnelAssetAssignment.query
            .filter(PersonnelAssetAssignment.user_id.in_(list(scope_user_ids)))
            .order_by(PersonnelAssetAssignment.id.desc())
            .all()
        )
        for row in assets:
            status = (row.status or "assigned").strip().lower()
            if status != "returned":
                stats["active_assets"] += 1
                if row.due_return_date and row.due_return_date < today:
                    stats["overdue_assets"] += 1
                    overdue_asset_rows.append({
                        "user_name": _full_name(getattr(row, "user", None)),
                        "asset_name": row.asset_name or "Demirbaş",
                        "asset_code": row.asset_code or "-",
                        "due_return_date": row.due_return_date,
                    })
        reminder_rows = (
            PersonnelDocumentReminderLog.query
            .filter(PersonnelDocumentReminderLog.user_id.in_(list(scope_user_ids)))
            .order_by(PersonnelDocumentReminderLog.id.desc())
            .limit(200)
            .all()
        )
        stats["queued_reminders"] = sum(1 for row in reminder_rows if (row.status or "").strip().lower() == "queued")
        transfer_rows = (
            PersonnelAssetTransferLog.query
            .filter(
                (PersonnelAssetTransferLog.from_user_id.in_(list(scope_user_ids)))
                | (PersonnelAssetTransferLog.to_user_id.in_(list(scope_user_ids)))
            )
            .order_by(PersonnelAssetTransferLog.transfer_date.desc(), PersonnelAssetTransferLog.id.desc())
            .limit(100)
            .all()
        )
        recent_limit = today - timedelta(days=30)
        stats["transfers_30"] = sum(1 for row in transfer_rows if row.transfer_date and row.transfer_date >= recent_limit)
        for row in transfer_rows[:8]:
            recent_transfer_rows.append({
                "transfer_date": row.transfer_date,
                "asset_name": row.asset_name_snapshot or "Demirbaş",
                "asset_code": row.asset_code_snapshot or "-",
                "from_user_name": _full_name(getattr(row, "from_user", None)),
                "to_user_name": _full_name(getattr(row, "to_user", None)),
                "status_label": _transfer_status_label(row.handover_status),
            })
    return safe_render(
        "hr_personnel_dashboard.html",
        dashboard_ready=dashboard_ready,
        hr_scope=hr_scope,
        selected_scope_mode=selected_scope_mode,
        dashboard_stats=stats,
        expiring_rows=expiring_rows[:8],
        overdue_asset_rows=overdue_asset_rows[:8],
        recent_transfer_rows=recent_transfer_rows,
    )


@main_bp.route("/hr-management/personnel-operations/renewal-calendar")
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_renewal_calendar():
    hr_scope, scope_users, scope_user_ids = _current_scope_bundle()
    selected_scope_mode = (hr_scope or {}).get("scope_mode") or "personal"
    selected_user = _selected_user(scope_users, scope_user_ids)
    calendar_ready = _table_exists("personnel_documents")
    month_groups: list[dict[str, object]] = []
    summary = {"tracked": 0, "expired": 0, "critical": 0, "next_90": 0}
    if calendar_ready and scope_user_ids:
        q = PersonnelDocument.query.filter(
            PersonnelDocument.user_id.in_(list(scope_user_ids)),
            PersonnelDocument.expiry_date.isnot(None),
        )
        if selected_user:
            q = q.filter(PersonnelDocument.user_id == int(selected_user.id))
        rows = q.order_by(PersonnelDocument.expiry_date.asc(), PersonnelDocument.id.desc()).all()
        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        today = date.today()
        for row in rows:
            if not row.expiry_date:
                continue
            summary["tracked"] += 1
            days_left = (row.expiry_date - today).days
            if days_left < 0:
                summary["expired"] += 1
                bucket = "Süresi Dolanlar"
            else:
                if days_left <= 15:
                    summary["critical"] += 1
                if days_left <= 90:
                    summary["next_90"] += 1
                bucket = f"{MONTH_LABELS.get(row.expiry_date.month, row.expiry_date.month)} {row.expiry_date.year}"
            grouped[bucket].append({
                "user_id": int(row.user_id),
                "user_name": _full_name(getattr(row, "user", None)),
                "title": row.title or "Belge",
                "category": _document_category_label(row.category),
                "expiry_date": row.expiry_date,
                "days_left": days_left,
                "severity": "expired" if days_left < 0 else "critical" if days_left <= 15 else "soon" if days_left <= 45 else "planned",
            })
        def _bucket_order(name: str) -> tuple[int, int, int]:
            if name == "Süresi Dolanlar":
                return (0, 0, 0)
            try:
                month_name, year = name.split(" ")
                inv = {v: k for k, v in MONTH_LABELS.items()}
                return (1, int(year), inv.get(month_name, 99))
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_personnel_phase10_routes.py:266")
                return (9, 9999, 99)
        for bucket in sorted(grouped.keys(), key=_bucket_order):
            month_groups.append({"label": bucket, "rows": grouped[bucket]})
    return safe_render(
        "hr_personnel_renewal_calendar.html",
        calendar_ready=calendar_ready,
        hr_scope=hr_scope,
        selected_scope_mode=selected_scope_mode,
        scope_user_options=_scope_user_options(scope_users),
        selected_user=selected_user,
        selected_user_id=int(selected_user.id) if selected_user else None,
        month_groups=month_groups,
        renewal_summary=summary,
    )


@main_bp.route("/hr-management/personnel-operations/assets/transfers")
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_asset_transfer_center():
    hr_scope, scope_users, scope_user_ids = _current_scope_bundle()
    selected_scope_mode = (hr_scope or {}).get("scope_mode") or "personal"
    selected_user = _selected_user(scope_users, scope_user_ids)
    transfers_ready = _table_exists("personnel_asset_assignments") and _table_exists("personnel_asset_transfer_logs")
    selected_asset = None
    transfer_asset_id = _safe_int(request.args.get("asset_id"))
    if transfer_asset_id and transfers_ready:
        try:
            selected_asset = _asset_in_scope(transfer_asset_id, scope_user_ids)
            selected_user = db.session.get(User, int(selected_asset.user_id)) or selected_user
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_personnel_phase10_routes.py:298")
            selected_asset = None
    active_assets = []
    recent_transfers = []
    summary = {"active_assets": 0, "transfers_total": 0, "recent_30": 0}
    if transfers_ready and scope_user_ids:
        asset_query = PersonnelAssetAssignment.query.filter(PersonnelAssetAssignment.user_id.in_(list(scope_user_ids)))
        if selected_user:
            asset_query = asset_query.filter(PersonnelAssetAssignment.user_id == int(selected_user.id))
        for row in asset_query.order_by(PersonnelAssetAssignment.assigned_date.desc(), PersonnelAssetAssignment.id.desc()).all():
            if (row.status or "assigned").strip().lower() == "returned":
                continue
            summary["active_assets"] += 1
            active_assets.append({
                "id": int(row.id),
                "asset_name": row.asset_name or "Demirbaş",
                "asset_code": row.asset_code or "-",
                "serial_no": row.serial_no or "-",
                "assigned_date": row.assigned_date,
            })
        transfer_rows = (
            PersonnelAssetTransferLog.query
            .filter(
                (PersonnelAssetTransferLog.from_user_id.in_(list(scope_user_ids)))
                | (PersonnelAssetTransferLog.to_user_id.in_(list(scope_user_ids)))
            )
            .order_by(PersonnelAssetTransferLog.transfer_date.desc(), PersonnelAssetTransferLog.id.desc())
            .limit(200)
            .all()
        )
        today = date.today()
        summary["transfers_total"] = len(transfer_rows)
        summary["recent_30"] = sum(1 for row in transfer_rows if row.transfer_date and row.transfer_date >= today - timedelta(days=30))
        for row in transfer_rows[:16]:
            recent_transfers.append({
                "id": int(row.id),
                "transfer_date": row.transfer_date,
                "asset_name": row.asset_name_snapshot or "Demirbaş",
                "asset_code": row.asset_code_snapshot or "-",
                "from_user_name": _full_name(getattr(row, "from_user", None)),
                "to_user_name": _full_name(getattr(row, "to_user", None)),
                "status_label": _transfer_status_label(row.handover_status),
                "document_no": row.handover_document_no or "-",
                "note": row.note or "",
            })
    return safe_render(
        "hr_personnel_asset_transfer_center.html",
        transfers_ready=transfers_ready,
        hr_scope=hr_scope,
        selected_scope_mode=selected_scope_mode,
        scope_user_options=_scope_user_options(scope_users),
        selected_user=selected_user,
        selected_user_id=int(selected_user.id) if selected_user else None,
        selected_asset=selected_asset,
        active_assets=active_assets,
        recent_transfers=recent_transfers,
        transfer_summary=summary,
        transfer_form_token=issue_form_token("hr_personnel_asset_transfer_save", scope="hr_personnel_operations"),
    )


@main_bp.route("/hr-management/personnel-operations/assets/transfer", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_asset_transfer_save():
    if not consume_form_token("hr_personnel_asset_transfer_save", request.form.get("form_token"), scope="hr_personnel_operations"):
        flash("Form oturumu doğrulanamadı. Lütfen tekrar deneyin.", "warning")
        return redirect(url_for("main.hr_personnel_asset_transfer_center", scope=request.form.get("scope") or request.args.get("scope") or "personal", user_id=request.form.get("from_user_id") or request.args.get("user_id")))
    _, _, scope_user_ids = _current_scope_bundle()
    try:
        if not (_table_exists("personnel_asset_assignments") and _table_exists("personnel_asset_transfer_logs")):
            raise ValueError("Devir tabloları henüz hazır değil.")
        from_user = _require_user_in_scope(_safe_int(request.form.get("from_user_id")), scope_user_ids)
        to_user = _require_user_in_scope(_safe_int(request.form.get("to_user_id")), scope_user_ids)
        if int(from_user.id) == int(to_user.id):
            raise ValueError("Devir yapılacak kişi mevcut kullanıcıdan farklı olmalıdır.")
        asset = _asset_in_scope(_safe_int(request.form.get("asset_id")), scope_user_ids)
        if int(asset.user_id) != int(from_user.id):
            raise ValueError("Seçilen zimmet mevcut kullanıcıya ait görünmüyor.")
        transfer_date = _parse_date(request.form.get("transfer_date")) or date.today()
        note = _normalize_text(request.form.get("note"), limit=1000)
        row = PersonnelAssetTransferLog(
            asset_assignment_id=asset.id,
            from_user_id=from_user.id,
            to_user_id=to_user.id,
            transferred_by_id=current_user.id,
            transfer_date=transfer_date,
            transfer_type="devir",
            handover_status="completed",
            handover_document_no=_normalize_text(request.form.get("handover_document_no"), limit=120) or None,
            asset_name_snapshot=asset.asset_name or "Demirbaş",
            asset_code_snapshot=asset.asset_code or None,
            serial_no_snapshot=asset.serial_no or None,
            note=note or None,
        )
        asset.user_id = int(to_user.id)
        asset.assigned_by_id = current_user.id
        asset.received_by_id = int(to_user.id)
        asset.assigned_date = transfer_date
        asset.status = "assigned"
        if note:
            existing = (asset.note or "").strip()
            asset.note = f"{existing}\n[Devir {transfer_date.isoformat()}] {from_user.ad} {from_user.soyad} -> {to_user.ad} {to_user.soyad}: {note}".strip()
        db.session.add(row)
        db.session.add(asset)
        db.session.commit()
        flash("Zimmet devri kaydedildi.", "success")
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash("İşlem sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.", "danger")
    return redirect(url_for("main.hr_personnel_asset_transfer_center", scope=request.form.get("scope") or "personal", user_id=request.form.get("to_user_id") or request.form.get("from_user_id")))
