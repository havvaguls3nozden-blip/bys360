from __future__ import annotations

from flask import flash, redirect, request, url_for
import logging
logger = logging.getLogger(__name__)

_ANNOUNCEMENT_THREAD_FETCH_LIMIT = 60
from flask_login import current_user, login_required
from sqlalchemy import func

from app.extensions import db
from app.models import Message, MessageThread, MessageThreadParticipant, User
from app.route_registry import main_bp
from app.route_support import consume_form_token, issue_form_token, menu_key_required, safe_render
from app.services.ai import build_announcement_form_ai_panel, build_announcements_ai_panel
from app.services.message_service import can_use_announcement_tools as _can_use_announcement_tools, notify_user as _notify_user

from .shared import _clean_message_body, _log_communication_exception, _normalize_text_search, _utcnow


def _announcement_preview_maps(users) -> dict[str, dict[str, int]]:
    role_counts: dict[str, int] = {}
    unit_counts: dict[str, int] = {}
    user_counts: dict[str, int] = {}
    for user in users or []:
        user_counts[str(user.id)] = 1
        role = (getattr(user, "role", "") or "").strip()
        unit = (getattr(user, "birim", "") or "").strip()
        if role:
            role_counts[role] = role_counts.get(role, 0) + 1
        if unit:
            unit_counts[unit] = unit_counts.get(unit, 0) + 1
    return {"role": role_counts, "unit": unit_counts, "user": user_counts}


def _announcement_distinct_active_user_values(column) -> list[str]:
    rows = (
        db.session.query(column.label("value"))
        .filter(User.is_active.is_(True), column.isnot(None), func.trim(column) != "")
        .group_by(column)
        .order_by(func.lower(func.trim(column)).asc(), column.asc())
        .all()
    )
    values: list[str] = []
    seen: set[str] = set()
    for row in rows:
        value = str(getattr(row, "value", "") or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        values.append(value)
    return values


def _announcement_recipient_users(target_type: str, target_values) -> list[User] | None:
    normalized_type = (target_type or "all").strip().lower()
    query = User.query.filter(User.is_active.is_(True), User.id != current_user.id)

    if normalized_type == "all":
        return query.order_by(User.ad.asc(), User.soyad.asc(), User.id.asc()).all()

    if normalized_type == "role":
        cleaned = [str(value).strip().lower() for value in (target_values or []) if str(value).strip()]
        if not cleaned:
            return []
        return (
            query
            .filter(func.lower(func.trim(func.coalesce(User.role, ""))).in_(cleaned))
            .order_by(User.ad.asc(), User.soyad.asc(), User.id.asc())
            .all()
        )

    if normalized_type == "unit":
        cleaned = [str(value).strip().lower() for value in (target_values or []) if str(value).strip()]
        if not cleaned:
            return []
        return (
            query
            .filter(func.lower(func.trim(func.coalesce(User.birim, ""))).in_(cleaned))
            .order_by(User.ad.asc(), User.soyad.asc(), User.id.asc())
            .all()
        )

    if normalized_type == "user":
        cleaned_ids: list[int] = []
        for value in target_values or []:
            raw = str(value).strip()
            if not raw.isdigit():
                continue
            parsed = int(raw)
            if parsed not in cleaned_ids:
                cleaned_ids.append(parsed)
        if not cleaned_ids:
            return []
        return (
            query
            .filter(User.id.in_(cleaned_ids))
            .order_by(User.ad.asc(), User.soyad.asc(), User.id.asc())
            .all()
        )

    return None


def _render_announcement_form(*, subject: str = "", body: str = "", target_type: str = "all", target_values=None, users=None, birimler=None, roles=None):
    users = users or []
    preview_counts = _announcement_preview_maps(users)
    selected_target_values = [str(value) for value in (target_values or []) if str(value).strip()]
    submit_token = issue_form_token("announcement_send", scope=str(current_user.id))
    ai_announcement_form_panel = build_announcement_form_ai_panel(
        users=users,
        preview_counts=preview_counts,
        target_type=target_type,
        target_values=selected_target_values,
        subject=subject,
        body=body,
    )
    return safe_render(
        "announcement_new.html",
        "<h3>Duyuru Gönder</h3>",
        users=users,
        birimler=birimler or [],
        roles=roles or [],
        total_user_count=len(users),
        preview_counts=preview_counts,
        selected_subject=subject,
        selected_body=body,
        selected_target_type=target_type,
        selected_target_values=selected_target_values,
        submit_token=submit_token,
        ai_announcement_form_panel=ai_announcement_form_panel,
    )


@main_bp.route("/announcements")
@login_required
@menu_key_required("announcements")
def announcements_list():
    # BYS360 kesin rota hizalama:
    # Genel > Duyurular menüsü artık video destekli pop-up Duyuru Yönetimi yüzeyidir.
    # Eski mesaj-akışı duyuruları kaybolmaz; sadece açıkça mode=flow/legacy, view veya q ile çağrılır.
    mode = (request.args.get("mode") or "").strip().lower()
    if (
        mode not in {"flow", "legacy"}
        and not request.args.get("view")
        and not request.args.get("q")
    ):
        return redirect(url_for("main.announcement_popup_manage"))

    view = (request.args.get("view") or "all").strip().lower()
    if view not in {"all", "incoming", "outgoing", "unread"}:
        view = "all"
    q = _normalize_text_search(request.args.get("q")).lower()

    participant_rows = (
        MessageThreadParticipant.query
        .filter_by(user_id=current_user.id)
        .filter(MessageThreadParticipant.left_at.is_(None))
        .all()
    )
    thread_ids = [p.thread_id for p in participant_rows]
    all_threads = []
    if thread_ids:
        thread_fetch_limit = 180 if q else _ANNOUNCEMENT_THREAD_FETCH_LIMIT
        all_threads = (
            MessageThread.query
            .filter(MessageThread.id.in_(thread_ids), MessageThread.thread_type == "announcement")
            .order_by(MessageThread.last_message_at.desc().nullslast(), MessageThread.id.desc())
            .limit(thread_fetch_limit)
            .all()
        )

    incoming_rows, outgoing_rows, unread_rows = [], [], []
    participant_map = {p.thread_id: p for p in participant_rows}

    for thread in all_threads:
        first_message = (
            thread.messages.filter(Message.is_deleted.is_(False))
            .order_by(Message.sent_at.asc(), Message.id.asc())
            .first()
        )
        last_message = (
            thread.messages.filter(Message.is_deleted.is_(False))
            .order_by(Message.sent_at.desc(), Message.id.desc())
            .first()
        )
        sender = first_message.sender if first_message else None
        active_participants = thread.participants.filter(MessageThreadParticipant.left_at.is_(None)).all()
        recipient_participants = [p for p in active_participants if p.user_id != thread.created_by_user_id]
        recipient_count = len(recipient_participants)
        read_count = 0
        pending_count = recipient_count
        if last_message:
            read_count = len([
                p for p in recipient_participants
                if p.last_read_message_id and p.last_read_message_id >= last_message.id
            ])
            pending_count = max(recipient_count - read_count, 0)
        read_rate = round((read_count / recipient_count) * 100, 1) if recipient_count else 0

        my_participant = participant_map.get(thread.id)
        if my_participant and my_participant.last_read_message_id:
            unread_count = thread.messages.filter(
                Message.id > my_participant.last_read_message_id,
                Message.sender_user_id != current_user.id,
                Message.is_deleted.is_(False),
            ).count()
        else:
            unread_count = thread.messages.filter(
                Message.sender_user_id != current_user.id,
                Message.is_deleted.is_(False),
            ).count()

        haystack = f"{thread.subject or ''} {(first_message.body if first_message else '')}".lower()
        if q and q not in haystack:
            continue

        personal_state_label = "Henüz okumadınız" if unread_count > 0 else "Okudunuz"
        personal_state_tone = "danger" if unread_count > 0 else "success"
        if recipient_count <= 0:
            delivery_state_label = "Alıcı yok"
        elif pending_count <= 0:
            delivery_state_label = "Tamamı okudu"
        elif read_count <= 0:
            delivery_state_label = "Henüz açılmadı"
        else:
            delivery_state_label = "Kısmen okundu"

        row = {
            "thread": thread,
            "message": first_message,
            "sender": sender,
            "recipient_count": recipient_count,
            "unread_count": unread_count,
            "read_count": read_count,
            "pending_count": pending_count,
            "read_rate": read_rate,
            "personal_state_label": personal_state_label,
            "personal_state_tone": personal_state_tone,
            "delivery_state_label": delivery_state_label,
            "delivery_detail": f"{read_count} okudu · {pending_count} bekliyor" if recipient_count else "Alıcı bulunmuyor",
            "open_url": url_for("main.messages_inbox", thread_id=thread.id),
        }
        if thread.created_by_user_id == current_user.id:
            outgoing_rows.append(row)
        else:
            incoming_rows.append(row)
            if unread_count > 0:
                unread_rows.append(row)

    visible_incoming = incoming_rows if view in {"all", "incoming", "unread"} else []
    visible_outgoing = outgoing_rows if view in {"all", "outgoing"} else []
    if view == "unread":
        visible_incoming = unread_rows

    total_outgoing_recipients = sum(row["recipient_count"] for row in outgoing_rows)
    total_outgoing_reads = sum(row["read_count"] for row in outgoing_rows)
    overall_read_rate = round((total_outgoing_reads / total_outgoing_recipients) * 100, 1) if total_outgoing_recipients else 0

    ai_announcements_panel = build_announcements_ai_panel(
        incoming_rows=visible_incoming,
        outgoing_rows=visible_outgoing,
        unread_rows=unread_rows,
        overall_read_rate=overall_read_rate,
        total_outgoing_reads=total_outgoing_reads,
        total_outgoing_recipients=total_outgoing_recipients,
        current_view=view,
    )

    return safe_render(
        "announcements_list.html",
        "<h3>Duyurular</h3>",
        incoming_rows=visible_incoming,
        outgoing_rows=visible_outgoing,
        raw_incoming_rows=incoming_rows,
        raw_outgoing_rows=outgoing_rows,
        unread_rows=unread_rows,
        overall_read_rate=overall_read_rate,
        total_outgoing_reads=total_outgoing_reads,
        total_outgoing_recipients=total_outgoing_recipients,
        current_view=view,
        search_query=q,
        can_manage_announcements=True,
        ai_announcements_panel=ai_announcements_panel,
    )


@main_bp.route("/announcements/new", methods=["GET", "POST"])
@login_required
@menu_key_required("announcements")
def announcements_new():
    # Menüdeki /announcements/new artık yeni pop-up duyuru formuna gider.
    # Eski toplu mesaj duyurusu gerekiyorsa /announcements/new?mode=flow kullanılabilir.
    mode = (request.args.get("mode") or "").strip().lower()
    if request.method == "GET" and mode not in {"flow", "legacy"}:
        return redirect(url_for("main.announcement_popup_new"))
    if not _can_use_announcement_tools(current_user):
        flash("Bu alana erişim yetkiniz yok.", "danger")
        return redirect(url_for("main.dashboard"))

    users = (
        User.query
        .filter(User.is_active.is_(True))
        .order_by(User.ad.asc(), User.soyad.asc(), User.id.asc())
        .all()
    )

    birimler = _announcement_distinct_active_user_values(User.birim)
    roles = _announcement_distinct_active_user_values(User.role)

    if request.method == "POST":
        subject = _normalize_text_search(request.form.get("subject"), limit=255)
        body = _clean_message_body(request.form.get("body"))
        target_type = (request.form.get("target_type") or "all").strip()
        target_values = request.form.getlist("target_values")

        if not subject:
            flash("Duyuru başlığı zorunludur.", "warning")
            return _render_announcement_form(
                subject=subject,
                body=body,
                target_type=target_type,
                target_values=target_values,
                users=users,
                birimler=birimler,
                roles=roles,
            )

        if not body:
            flash("Duyuru içeriği zorunludur.", "warning")
            return _render_announcement_form(
                subject=subject,
                body=body,
                target_type=target_type,
                target_values=target_values,
                users=users,
                birimler=birimler,
                roles=roles,
            )

        try:
            if not consume_form_token("announcement_send", request.form.get("_form_token"), scope=str(current_user.id)):
                flash("Bu duyuru zaten işleme alınmış görünüyor. Çift gönderimi engellemek için ikinci isteği durdurdum.", "info")
                return _render_announcement_form(
                    subject=subject,
                    body=body,
                    target_type=target_type,
                    target_values=target_values,
                    users=users,
                    birimler=birimler,
                    roles=roles,
                )

            recipient_users = _announcement_recipient_users(target_type, target_values)
            if recipient_users is None:
                flash("Geçersiz hedef kitle seçimi.", "danger")
                return _render_announcement_form(
                    subject=subject,
                    body=body,
                    target_type=target_type,
                    target_values=target_values,
                    users=users,
                    birimler=birimler,
                    roles=roles,
                )

            if not recipient_users:
                flash("Gönderilecek alıcı bulunamadı.", "warning")
                return _render_announcement_form(
                    subject=subject,
                    body=body,
                    target_type=target_type,
                    target_values=target_values,
                    users=users,
                    birimler=birimler,
                    roles=roles,
                )

            announcement_thread = MessageThread(
                thread_type="announcement",
                subject=subject,
                created_by_user_id=current_user.id,
                is_active=True,
                last_message_at=_utcnow(),
            )
            db.session.add(announcement_thread)
            db.session.flush()

            db.session.add(MessageThreadParticipant(
                thread_id=announcement_thread.id,
                user_id=current_user.id,
                joined_at=_utcnow(),
            ))

            for recipient in recipient_users:
                db.session.add(MessageThreadParticipant(
                    thread_id=announcement_thread.id,
                    user_id=recipient.id,
                    joined_at=_utcnow(),
                ))

            first_message = Message(
                thread_id=announcement_thread.id,
                sender_user_id=current_user.id,
                body=body,
                message_type="announcement",
                sent_at=_utcnow(),
                is_deleted=False,
            )
            db.session.add(first_message)
            db.session.flush()

            sender_participant = MessageThreadParticipant.query.filter_by(
                thread_id=announcement_thread.id,
                user_id=current_user.id,
            ).first()
            if sender_participant:
                sender_participant.last_read_message_id = first_message.id

            for recipient in recipient_users:
                _notify_user(
                    recipient.id,
                    title=f"Yeni duyuru: {subject}",
                    body=body[:220],
                    notification_type="announcement",
                    source_type="message_thread",
                    source_id=announcement_thread.id,
                    link_url=url_for("main.messages_inbox", thread_id=announcement_thread.id),
                    priority="high",
                )

            db.session.commit()
            flash(f"Duyuru {len(recipient_users)} kullanıcıya gönderildi. Okunma takibi birazdan duyurular ekranına düşer.", "success")
            return redirect(url_for("main.messages_inbox", thread_id=announcement_thread.id))
        except Exception as exc:
            logger.exception("BYS360 V6C guarded exception | file=app/communication/announcements_routes.py | line=435")
            db.session.rollback()
            _log_communication_exception(
                "announcements_new",
                exc,
                subject=subject,
                target_type=target_type,
                user_id=getattr(current_user, "id", None),
            )
            flash(f"Duyuru gönderilirken hata oluştu: {exc}", "danger")
            return _render_announcement_form(
                subject=subject,
                body=body,
                target_type=target_type,
                target_values=target_values,
                users=users,
                birimler=birimler,
                roles=roles,
            )

    return _render_announcement_form(users=users, birimler=birimler, roles=roles)


__all__ = ["announcements_list", "announcements_new"]
