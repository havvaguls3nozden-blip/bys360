from __future__ import annotations



from flask import current_app, flash, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import case, func, or_

from app.extensions import db
from app.models import Notification
from app.route_registry import main_bp
from app.route_support import menu_key_required
from app.services.runtime_cache import get_or_set as _cache_get_or_set, invalidate as _cache_invalidate

from .shared import (
    _empty_notification_counts,
    _normalize_text_search,
    _redirect_notifications_view,
    _render_notifications_page,
    _safe_internal_redirect,
    _utcdate,
    _utcnow,
)
import logging
logger = logging.getLogger(__name__)

"""Canlı omurgaya uyarlanmış bildirim modülü."""

_NOTIFICATION_PAGE_SIZE = 80


def _normalize_notification_view() -> str:
    current_view = (request.args.get("view") or "").strip().lower()
    if not current_view:
        portal_filter = (request.args.get("filter") or "").strip().lower()
        current_view = {
            "unread": "unread",
            "messages": "system",
            "portal": "priority",
            "priority": "priority",
            "surveys": "surveys",
            "system": "system",
            "support": "support",
            "performance": "performance",
            "read": "read",
        }.get(portal_filter, "all")
    if current_view not in {"all", "unread", "read", "priority", "support", "performance", "surveys", "system"}:
        current_view = "all"
    return current_view


def _selected_notification_ids() -> list[int]:
    values: list[int] = []
    for raw_id in request.form.getlist("notification_ids"):
        try:
            values.append(int(raw_id))
        except (TypeError, ValueError):
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/communication/notifications_routes.py:53)")
            continue
    return values


def _normalize_token(value: str | None) -> str:
    return (value or "").strip().lower()


def _normalize_page() -> int:
    try:
        page = int(request.args.get("page") or 1)
    except (TypeError, ValueError):
        page = 1
    return max(page, 1)


def _invalidate_user_notification_cache(user_id: int | None) -> None:
    if user_id:
        _cache_invalidate(f"notification_unread_count:{int(user_id)}")


def _category_filter_expr(category: str):
    if category == "support":
        return or_(
            Notification.source_type.ilike("%support%"),
            Notification.notification_type.ilike("%support%"),
            Notification.notification_type.ilike("%ticket%"),
        )
    if category == "performance":
        return or_(
            Notification.notification_type.ilike("performance_%"),
            Notification.source_type.ilike("feedback_%"),
            Notification.source_type.in_(["feedback_digest", "system_published"]),
        )
    if category == "surveys":
        return or_(
            Notification.notification_type.ilike("survey%"),
            Notification.source_type == "survey",
        )
    return ~or_(
        _category_filter_expr("support"),
        _category_filter_expr("performance"),
        _category_filter_expr("surveys"),
    )


def _apply_query_filter(query, search_query: str):
    if not search_query:
        return query
    like = f"%{search_query}%"
    return query.filter(
        or_(
            Notification.title.ilike(like),
            Notification.body.ilike(like),
            Notification.notification_type.ilike(like),
            Notification.source_type.ilike(like),
            Notification.link_url.ilike(like),
        )
    )


def _apply_view_filter(query, current_view: str):
    if current_view == "all":
        return query
    if current_view == "unread":
        return query.filter(Notification.is_read.is_(False))
    if current_view == "read":
        return query.filter(Notification.is_read.is_(True))
    if current_view == "priority":
        return query.filter(Notification.priority.in_(["high", "urgent", "warning"]))
    return query.filter(_category_filter_expr(current_view))


def _notification_summary_counts(base_query) -> dict[str, int]:
    """Bildirim rozetlerini tek SQL aggregate sorgusunda hesaplar."""

    support_expr = _category_filter_expr("support")
    performance_expr = _category_filter_expr("performance")
    surveys_expr = _category_filter_expr("surveys")
    system_expr = _category_filter_expr("system")
    priority_expr = Notification.priority.in_(["high", "urgent", "warning"])
    row = base_query.with_entities(
        func.count(Notification.id).label("all_count"),
        func.coalesce(func.sum(case((Notification.is_read.is_(False), 1), else_=0)), 0).label("unread_count"),
        func.coalesce(func.sum(case((Notification.is_read.is_(True), 1), else_=0)), 0).label("read_count"),
        func.coalesce(func.sum(case((priority_expr, 1), else_=0)), 0).label("priority_count"),
        func.coalesce(func.sum(case((support_expr, 1), else_=0)), 0).label("support_count"),
        func.coalesce(func.sum(case((performance_expr, 1), else_=0)), 0).label("performance_count"),
        func.coalesce(func.sum(case((surveys_expr, 1), else_=0)), 0).label("surveys_count"),
        func.coalesce(func.sum(case((system_expr, 1), else_=0)), 0).label("system_count"),
    ).one()
    return {
        "all": int(row.all_count or 0),
        "unread": int(row.unread_count or 0),
        "read": int(row.read_count or 0),
        "priority": int(row.priority_count or 0),
        "support": int(row.support_count or 0),
        "performance": int(row.performance_count or 0),
        "surveys": int(row.surveys_count or 0),
        "system": int(row.system_count or 0),
    }


def _count_for(query) -> int:
    try:
        return int(query.order_by(None).count())
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/notifications_routes.py | line=163")
        return 0


def notifications_list_impl():
    """Kullanıcının bildirim kutusunu canlı omurgaya uygun filtrelerle döndürür."""
    current_view = _normalize_notification_view()
    q = _normalize_text_search(request.args.get("q"))
    page = _normalize_page()

    try:
        base_query = Notification.query.filter(Notification.user_id == current_user.id)
        filtered_query = _apply_view_filter(_apply_query_filter(base_query, q), current_view)

        notifications = (
            filtered_query
            .order_by(Notification.is_read.asc(), Notification.created_at.desc(), Notification.id.desc())
            .limit(_NOTIFICATION_PAGE_SIZE)
            .offset((page - 1) * _NOTIFICATION_PAGE_SIZE)
            .all()
        )

        filter_counts = _notification_summary_counts(base_query)
        unread_count = filter_counts["unread"]
        read_count = filter_counts["read"]
        priority_count = filter_counts["priority"]
        today = _utcdate()
        today_count = _count_for(base_query.filter(db.func.date(Notification.created_at) == today))

        return _render_notifications_page(
            notifications=notifications,
            unread_count=unread_count,
            read_count=read_count,
            priority_count=priority_count,
            today_count=today_count,
            current_view=current_view,
            search_query=q,
            filter_counts=filter_counts,
        )
    except Exception as exc:
        current_app.logger.exception("Bildirimler listelenirken hata: %s", exc)
        flash("Bildirimler açılırken bir sorun oldu. Sayfayı beyaz bırakmadım; bir kez daha deneyin.", "danger")
        return _render_notifications_page(
            notifications=[],
            unread_count=0,
            read_count=0,
            priority_count=0,
            today_count=0,
            current_view=current_view,
            search_query=q,
            filter_counts=_empty_notification_counts(),
        )


def notifications_unread_count_impl():
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({"ok": True, "unread_count": unread_count})


def notifications_mark_read_impl(notification_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()

    if not notification:
        flash("Bildirim bulunamadı.", "danger")
        return _redirect_notifications_view()

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = _utcnow()
        db.session.commit()
        _invalidate_user_notification_cache(current_user.id)

    if notification.link_url:
        return _safe_internal_redirect(notification.link_url)

    return _redirect_notifications_view()


def notifications_mark_unread_impl(notification_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()

    if not notification:
        flash("Bildirim bulunamadı.", "danger")
        return _redirect_notifications_view()

    if notification.is_read:
        notification.is_read = False
        notification.read_at = None
        db.session.commit()
        _invalidate_user_notification_cache(current_user.id)

    return _redirect_notifications_view()


def notifications_mark_all_read_impl():
    try:
        Notification.query.filter_by(user_id=current_user.id, is_read=False).update(
            {"is_read": True, "read_at": _utcnow()},
            synchronize_session=False,
        )
        db.session.commit()
        _invalidate_user_notification_cache(current_user.id)
        flash("Tüm bildirimler okundu olarak işaretlendi.", "success")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/notifications_routes.py | line=266")
        db.session.rollback()
        flash(f"Bildirimler güncellenirken hata oluştu: {exc}", "danger")

    return _redirect_notifications_view()


def notifications_bulk_mark_read_impl():
    notification_ids = _selected_notification_ids()

    if not notification_ids:
        flash("Okundu yapmak için en az bir bildirim seçin.", "warning")
        return _redirect_notifications_view()

    try:
        updated_count = (
            Notification.query
            .filter(Notification.user_id == current_user.id, Notification.id.in_(notification_ids))
            .update({"is_read": True, "read_at": _utcnow()}, synchronize_session=False)
        )
        db.session.commit()
        _invalidate_user_notification_cache(current_user.id)
        if updated_count:
            flash(f"{updated_count} bildirim okundu olarak işaretlendi.", "success")
        else:
            flash("Seçilen bildirimler bulunamadı.", "warning")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/notifications_routes.py | line=292")
        db.session.rollback()
        flash(f"Bildirimler güncellenirken hata oluştu: {exc}", "danger")

    return _redirect_notifications_view()


def notifications_bulk_mark_unread_impl():
    notification_ids = _selected_notification_ids()

    if not notification_ids:
        flash("Okunmamış yapmak için en az bir bildirim seçin.", "warning")
        return _redirect_notifications_view()

    try:
        updated_count = (
            Notification.query
            .filter(Notification.user_id == current_user.id, Notification.id.in_(notification_ids))
            .update({"is_read": False, "read_at": None}, synchronize_session=False)
        )
        db.session.commit()
        _invalidate_user_notification_cache(current_user.id)
        if updated_count:
            flash(f"{updated_count} bildirim okunmamış olarak işaretlendi.", "success")
        else:
            flash("Seçilen bildirimler bulunamadı.", "warning")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/notifications_routes.py | line=318")
        db.session.rollback()
        flash(f"Bildirimler güncellenirken hata oluştu: {exc}", "danger")

    return _redirect_notifications_view()


def notifications_bulk_delete_impl():
    notification_ids = _selected_notification_ids()

    if not notification_ids:
        flash("Silmek için en az bir bildirim seçin.", "warning")
        return _redirect_notifications_view()

    try:
        deleted_count = (
            Notification.query
            .filter(Notification.user_id == current_user.id, Notification.id.in_(notification_ids))
            .delete(synchronize_session=False)
        )
        db.session.commit()
        _invalidate_user_notification_cache(current_user.id)
        if deleted_count:
            flash(f"{deleted_count} bildirim kaldırıldı.", "success")
        else:
            flash("Seçilen bildirimler bulunamadı.", "warning")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/notifications_routes.py | line=344")
        db.session.rollback()
        flash(f"Bildirimler silinirken hata oluştu: {exc}", "danger")

    return _redirect_notifications_view()


@main_bp.route("/notifications")
@login_required
@menu_key_required("notifications")
def notifications_list():
    return notifications_list_impl()


@main_bp.route("/notifications/unread-count")
@login_required
def notifications_unread_count():
    # BYS360_CLAUDE_ROADMAP_PHASE4_SCALABILITY_PERFORMANCE_UNREAD_CACHE_ROUTE
    return notifications_unread_count_impl()


@main_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
@menu_key_required("notifications")
def notifications_mark_read(notification_id):
    return notifications_mark_read_impl(notification_id)


@main_bp.route("/notifications/<int:notification_id>/unread", methods=["POST"])
@login_required
@menu_key_required("notifications")
def notifications_mark_unread(notification_id):
    return notifications_mark_unread_impl(notification_id)


@main_bp.route("/notifications/mark-all-read", methods=["POST"])
@login_required
@menu_key_required("notifications")
def notifications_mark_all_read():
    return notifications_mark_all_read_impl()


@main_bp.route("/notifications/bulk-mark-read", methods=["POST"])
@login_required
@menu_key_required("notifications")
def notifications_bulk_mark_read():
    return notifications_bulk_mark_read_impl()


@main_bp.route("/notifications/bulk-mark-unread", methods=["POST"])
@login_required
@menu_key_required("notifications")
def notifications_bulk_mark_unread():
    return notifications_bulk_mark_unread_impl()


@main_bp.route("/notifications/bulk-delete", methods=["POST"])
@login_required
@menu_key_required("notifications")
def notifications_bulk_delete():
    return notifications_bulk_delete_impl()
