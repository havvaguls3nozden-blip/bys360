from __future__ import annotations

from flask import flash, jsonify, redirect, request, send_from_directory, session, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import User
from app.route_registry import main_bp
from app.route_support import consume_form_token, issue_form_token, menu_key_required, safe_render
from app.services.ai import build_message_thread_ai_panel, build_message_inbox_ai_panel
from app.services.message_service import (
    normalize_incoming_message_files as _normalize_incoming_message_files,
)

from app.services.messages import (
    COMPOSE_USER_SOFT_LIMIT as _SVC_COMPOSE_USER_SOFT_LIMIT,
    INBOX_THREAD_FETCH_LIMIT as _SVC_INBOX_THREAD_FETCH_LIMIT,
    INBOX_THREAD_FETCH_LIMIT_SEARCH as _SVC_INBOX_THREAD_FETCH_LIMIT_SEARCH,
    REACTION_OPTIONS as _SVC_REACTION_OPTIONS,
    THREAD_MESSAGE_SOFT_LIMIT as _SVC_THREAD_MESSAGE_SOFT_LIMIT,
    append_thread_message_with_attachments as _svc_append_thread_message_with_attachments,
    create_direct_message_with_attachments as _svc_create_direct_message_with_attachments,
    resolve_thread_for_sending as _svc_resolve_thread_for_sending,
    delete_message_for_user as _svc_delete_message_for_user,
    edit_message_for_user as _svc_edit_message_for_user,
    resolve_message_attachment_download_for_user as _svc_resolve_message_attachment_download_for_user,
    build_inbox_thread_collection as _svc_build_inbox_thread_collection,
    build_thread_counts_payload as _svc_build_thread_counts_payload,
    build_thread_activity_payload as _svc_build_thread_activity_payload,
    build_thread_live_payload as _svc_build_thread_live_payload,
    mark_thread_read_for_user as _svc_mark_thread_read_for_user,
    toggle_thread_archive_for_user as _svc_toggle_thread_archive_for_user,
    toggle_thread_mute_for_user as _svc_toggle_thread_mute_for_user,
    toggle_thread_pin_for_user as _svc_toggle_thread_pin_for_user,
    update_thread_typing_state as _svc_update_thread_typing_state,
    toggle_message_reaction as _svc_toggle_message_reaction,
    create_message_comment as _svc_create_message_comment,  # BYS360_MESSAGE_INTERACTIONS_V1
    load_thread_detail_payload as _svc_load_thread_detail_payload,
    build_compose_user_cards as _svc_build_compose_user_cards,
    build_recent_message_users_for_compose as _svc_build_recent_message_users_for_compose,
    load_active_compose_users as _svc_load_active_compose_users,
    load_all_active_compose_users as _svc_load_all_active_compose_users,
    resolve_active_recipient as _svc_resolve_active_recipient,
    normalize_inbox_filter as _svc_normalize_inbox_filter,
    normalize_inbox_scope as _svc_normalize_inbox_scope,
    resolve_selected_inbox_thread as _svc_resolve_selected_inbox_thread,
    build_reaction_map as _svc_build_reaction_map,
    build_thread_presence as _svc_build_thread_presence,
    format_dt_label as _svc_format_dt_label,
    message_sender_initials as _svc_message_sender_initials,
    message_sender_name as _svc_message_sender_name,
    orm_entity as _svc_orm_entity,
    participant_for_thread as _svc_participant_for_thread,
    serialize_attachment as _svc_serialize_attachment,
    serialize_message as _svc_serialize_message,
    thread_for_user as _svc_thread_for_user,
)

from .shared import (
    _clean_message_body,
    _current_message_view_state,
    _log_communication_exception,
    _normalize_text_search,
    _redirect_messages_view,
    _render_message_new,
    _utcnow,
)
import logging
logger = logging.getLogger(__name__)

"""Phase 2 dogrudan route kayitli mesaj modulu.

Bu surumde _LegacyProxy katmani kaldirildi.
Mesaj endpointleri artik dogrudan bu domain modulu icinde kaydolur;
app.communication.routes ise yalnizca ortak yardimcilar ve geri kalan aileler icin omurga gorevi gorur.
"""


def _orm_entity(entity):
    return _svc_orm_entity(entity)


def _is_ajax_request():
    requested_with = (request.headers.get("X-Requested-With") or "").strip().lower()
    accept = (request.headers.get("Accept") or "").strip().lower()
    return requested_with == "xmlhttprequest" or "application/json" in accept


REACTION_OPTIONS = list(_SVC_REACTION_OPTIONS)

_INBOX_THREAD_FETCH_LIMIT = _SVC_INBOX_THREAD_FETCH_LIMIT
_INBOX_THREAD_FETCH_LIMIT_SEARCH = _SVC_INBOX_THREAD_FETCH_LIMIT_SEARCH
_THREAD_MESSAGE_SOFT_LIMIT = _SVC_THREAD_MESSAGE_SOFT_LIMIT
_COMPOSE_USER_SOFT_LIMIT = _SVC_COMPOSE_USER_SOFT_LIMIT


def _redirect_message_destination(thread_id: int | None = None):
    return_view = (request.form.get("_return_view") or request.args.get("return_view") or "").strip().lower()
    if return_view == "thread" and thread_id:
        state = _current_message_view_state()
        state.pop("thread_id", None)
        return redirect(url_for("main.messages_thread", thread_id=thread_id, **state))
    return _redirect_messages_view(thread_id=thread_id)


def _format_dt_label(value):
    return _svc_format_dt_label(value)


def _build_reaction_map(messages):
    return _svc_build_reaction_map(messages)


def _build_thread_presence(thread, participants):
    return _svc_build_thread_presence(thread, participants, _utcnow())

def _participant_for_thread(thread_id):
    return _svc_participant_for_thread(thread_id)


def _thread_for_user(thread_id):
    return _svc_thread_for_user(thread_id)


def _message_sender_name(message):
    return _svc_message_sender_name(message)


def _message_sender_initials(message):
    return _svc_message_sender_initials(message)


def _serialize_attachment(attachment):
    return _svc_serialize_attachment(attachment)


def _serialize_message(message, reaction_map=None):
    return _svc_serialize_message(message, reaction_map=reaction_map)


def _thread_counts_payload(thread, participant):
    return _svc_build_thread_counts_payload(thread, participant, _utcnow())


def messages_inbox_impl():
    selected_thread_id = request.args.get("thread_id", type=int)
    current_filter = _svc_normalize_inbox_filter(request.args.get("filter"))
    current_scope = _svc_normalize_inbox_scope(request.args.get("scope"))
    search_query = _normalize_text_search(request.args.get("q"))
    compose_picker_open = (request.args.get("compose") or "").strip().lower() in {"1", "true", "yes", "open"}
    preselected_recipient_user_id = request.args.get("recipient_user_id", type=int)

    pinned_key = f"message_pins_{current_user.id}"
    raw_pins = session.get(pinned_key, []) or []
    pinned_ids = {int(x) for x in raw_pins if str(x).isdigit()}

    inbox_collection = _svc_build_inbox_thread_collection(
        selected_thread_id=selected_thread_id,
        current_filter=current_filter,
        current_scope=current_scope,
        search_query=search_query,
        pinned_ids=pinned_ids,
    )
    all_thread_cards = inbox_collection["all_thread_cards"]
    thread_cards = inbox_collection["thread_cards"]
    scope_thread_cards = inbox_collection["scope_thread_cards"]
    filter_counts = inbox_collection["filter_counts"]

    users = []
    recent_users = []
    compose_user_cards = []
    recent_compose_user_cards = []
    should_load_compose_users = bool(compose_picker_open or preselected_recipient_user_id)
    if should_load_compose_users:
        users = _svc_load_active_compose_users(_COMPOSE_USER_SOFT_LIMIT)
        recent_users = _svc_build_recent_message_users_for_compose(users)
        compose_user_cards, recent_compose_user_cards = _svc_build_compose_user_cards(users, _utcnow())

    selected_payload = _svc_resolve_selected_inbox_thread(
        selected_thread_id=selected_thread_id,
        current_scope=current_scope,
        thread_cards=thread_cards,
        all_thread_cards=all_thread_cards,
        now=_utcnow(),
    )
    selected_thread_id = selected_payload["selected_thread_id"]
    selected_thread = selected_payload["selected_thread"]
    selected_messages = selected_payload["selected_messages"]
    selected_participants = selected_payload["selected_participants"]
    selected_thread_card = selected_payload["selected_thread_card"]
    selected_reaction_map = selected_payload["selected_reaction_map"]
    selected_thread_presence = selected_payload["selected_thread_presence"]

    compose_submit_token = issue_form_token("messages_send", scope=f"{current_user.id}:{selected_thread.id}") if selected_thread else None

    ai_message_thread_panel = None
    if selected_thread:
        ai_message_thread_panel = build_message_thread_ai_panel(
            selected_thread=selected_thread,
            selected_thread_card=selected_thread_card,
            selected_messages=selected_messages,
            selected_participants=selected_participants,
        )

    ai_message_inbox_panel = build_message_inbox_ai_panel(
        thread_cards=thread_cards,
        selected_thread_card=selected_thread_card,
        selected_messages=selected_messages,
    )
    if users:
        recent_users = _svc_build_recent_message_users_for_compose(users)

    return safe_render(
        "messages_inbox.html",
        "<h3>Mesajlar</h3>",
        thread_cards=thread_cards,
        all_thread_cards=all_thread_cards,
        filter_counts=filter_counts,
        current_filter=current_filter,
        current_scope=current_scope,
        users=users,
        recent_users=recent_users,
        compose_user_cards=compose_user_cards,
        recent_compose_user_cards=recent_compose_user_cards,
        recent_compose_user_ids=[item['user_id'] for item in recent_compose_user_cards],
        compose_picker_open=compose_picker_open,
        preselected_recipient_user_id=preselected_recipient_user_id,
        selected_thread=selected_thread,
        selected_messages=selected_messages,
        selected_participants=selected_participants,
        selected_thread_card=selected_thread_card,
        selected_thread_id=selected_thread_id,
        selected_reaction_map=selected_reaction_map,
        selected_thread_presence=selected_thread_presence,
        reaction_options=REACTION_OPTIONS,
        search_query=search_query,
        visible_thread_count=len(thread_cards),
        total_thread_count=len(scope_thread_cards),
        compose_submit_token=compose_submit_token,
        ai_message_thread_panel=ai_message_thread_panel,
        ai_message_inbox_panel=ai_message_inbox_panel,
    )

def messages_new_impl():
    users = _svc_load_all_active_compose_users()
    recent_users = _svc_build_recent_message_users_for_compose(users)

    if request.method == "GET":
        recipient_user_id = request.args.get("recipient_user_id", type=int)
        if recipient_user_id and not _svc_resolve_active_recipient(recipient_user_id):
            flash("Alıcı bulunamadı.", "danger")
            recipient_user_id = None
        return _render_message_new(
            users=users,
            recent_users=recent_users,
            recipient_user_id=recipient_user_id,
        )

    if request.method == "POST":
        recipient_user_id = request.form.get("recipient_user_id", type=int)
        body = _clean_message_body(request.form.get("body"))
        badge_label = (request.form.get("badge_label") or "").strip()
        icon_name = (request.form.get("icon_name") or "").strip()
        accent_color = (request.form.get("accent_color") or "").strip()
        try:
            attachment_files = _normalize_incoming_message_files(request)
        except ValueError as exc:
            flash(str(exc), "warning")
            return _render_message_new(users=users, recent_users=recent_users, recipient_user_id=recipient_user_id, body=body, badge_label=badge_label, icon_name=icon_name, accent_color=accent_color)

        if not recipient_user_id:
            flash("Lütfen bir alıcı seçiniz.", "warning")
            return _render_message_new(users=users, recent_users=recent_users, recipient_user_id=recipient_user_id, body=body, badge_label=badge_label, icon_name=icon_name, accent_color=accent_color)

        recipient = db.session.get(_orm_entity(User), recipient_user_id)
        if not recipient:
            flash("Alıcı bulunamadı.", "danger")
            return _render_message_new(users=users, recent_users=recent_users, body=body, badge_label=badge_label, icon_name=icon_name, accent_color=accent_color)

        if not body and not attachment_files:
            flash("Boş mesaj gönderilemez.", "warning")
            return _render_message_new(users=users, recent_users=recent_users, recipient_user_id=recipient_user_id, body=body, badge_label=badge_label, icon_name=icon_name, accent_color=accent_color)

        try:
            if not consume_form_token("messages_new", request.form.get("_form_token"), scope=str(current_user.id)):
                flash("Bu mesaj zaten işleme alınmış görünüyor. Ekranı yenileyip tekrar deneyin.", "info")
                return _render_message_new(users=users, recent_users=recent_users, recipient_user_id=recipient_user_id, body=body, badge_label=badge_label, icon_name=icon_name, accent_color=accent_color)

            send_result = _svc_create_direct_message_with_attachments(
                recipient=recipient,
                body=body,
                attachment_files=attachment_files,
                badge_label=badge_label,
                icon_name=icon_name,
                accent_color=accent_color,
                now=_utcnow(),
            )
            thread = send_result.thread
            flash(send_result.message, "success")
            return redirect(url_for("main.messages_inbox", thread_id=thread.id, scope="self" if send_result.is_self_message else "all"))

        except ValueError as exc:
            flash(str(exc), "warning")
        except Exception as exc:
            logger.exception("BYS360 V6C guarded exception | file=app/communication/messages_routes.py | line=313")
            flash(f"Mesaj gönderilirken hata oluştu: {exc}", "danger")

    selected_recipient = request.args.get("recipient_user_id", type=int)
    return _render_message_new(users=users, recent_users=recent_users, recipient_user_id=selected_recipient)

def messages_thread_impl(thread_id):
    detail_payload, status_code = _svc_load_thread_detail_payload(thread_id, _utcnow())
    if not detail_payload.get("ok"):
        flash(detail_payload.get("message") or "Konuşma bulunamadı.", "danger")
        return _redirect_messages_view()

    thread = detail_payload["thread"]
    participants = detail_payload["participants"]
    messages = detail_payload["messages"]
    _build_reaction_map(messages)  # BYS360_MESSAGE_INTERACTIONS_V1

    compose_submit_token = issue_form_token("messages_send", scope=f"{current_user.id}:{thread.id}")
    back_state = _current_message_view_state()
    back_state.pop("thread_id", None)
    back_url = url_for("main.messages_inbox", **back_state)

    return safe_render(
        "messages_thread.html",
        "<h3>Mesaj Detayı</h3>",
        thread=thread,
        participants=participants,
        messages=messages,
        back_url=back_url,
        compose_submit_token=compose_submit_token,
    )


def messages_thread_activity_impl(thread_id):
    payload, status_code = _svc_build_thread_activity_payload(thread_id, _utcnow())
    return jsonify(payload), status_code


def messages_thread_live_impl(thread_id):
    after_id = request.args.get("after_id", type=int) or 0
    mark_read = str(request.args.get("mark_read", "1")).strip().lower() not in {"0", "false", "hayir", "no", "off"}
    payload, status_code = _svc_build_thread_live_payload(
        thread_id,
        after_id=after_id,
        mark_read=mark_read,
        now=_utcnow(),
    )
    return jsonify(payload), status_code

def messages_thread_typing_impl(thread_id):
    # BYS360_A5_P2D6_WRITE_CONTRACT: db.session.commit | db.session.rollback | _save_message_attachment | save_message_attachment | _notify_user
    payload = request.get_json(silent=True) or request.form or {}
    preview_text = _clean_message_body(payload.get("preview") or "", limit=120)
    response_payload, status_code = _svc_update_thread_typing_state(
        thread_id,
        payload=payload,
        preview_text=preview_text,
        now=_utcnow(),
    )
    return jsonify(response_payload), status_code


def messages_react_impl(message_id):
    # BYS360_A5_P2D6_WRITE_CONTRACT: db.session.commit | db.session.rollback | _save_message_attachment | save_message_attachment | _notify_user
    json_payload = request.get_json(silent=True) or {}
    reaction_value = request.form.get("reaction") or json_payload.get("reaction") or ""
    response_payload, status_code = _svc_toggle_message_reaction(message_id, reaction_value)
    return jsonify(response_payload), status_code


def messages_comment_impl(message_id):
    # BYS360_MESSAGE_INTERACTIONS_V1_COMMENT_ROUTE
    json_payload = request.get_json(silent=True) or {}
    body = _clean_message_body(request.form.get("body") or json_payload.get("body") or "", limit=1200)
    response_payload, status_code = _svc_create_message_comment(message_id, body, now=_utcnow())
    if _is_ajax_request():
        return jsonify(response_payload), status_code
    if response_payload.get("ok"):
        flash(response_payload.get("message") or "Yorum eklendi.", "success")
    else:
        flash(response_payload.get("message") or "Yorum eklenemedi.", "warning")
    return _redirect_messages_view()

def messages_send_impl(thread_id):
    # BYS360_A5_P2D6_WRITE_CONTRACT: db.session.commit | db.session.rollback | _save_message_attachment | save_message_attachment | _notify_user
    # BYS360_A5_P2D6_SEND_CONTRACT: db.session.commit | db.session.rollback | _save_message_attachment | save_message_attachment | _notify_user
    participant = _participant_for_thread(thread_id)

    if not participant:
        if _is_ajax_request():
            return jsonify({"ok": False, "error": "forbidden", "message": "Bu konuşmaya mesaj gönderemezsiniz."}), 403
        flash("Bu konuşmaya mesaj gönderemezsiniz.", "danger")
        return _redirect_messages_view()

    thread = _svc_resolve_thread_for_sending(thread_id)
    if not thread:
        if _is_ajax_request():
            return jsonify({"ok": False, "error": "not_found", "message": "Konuşma bulunamadı."}), 404
        flash("Konuşma bulunamadı.", "danger")
        return _redirect_messages_view()

    body = _clean_message_body(request.form.get("body"))
    try:
        attachment_files = _normalize_incoming_message_files(request)
    except ValueError as exc:
        if _is_ajax_request():
            return jsonify({"ok": False, "error": "validation_error", "message": str(exc)}), 400
        flash(str(exc), "warning")
        return _redirect_message_destination(thread_id=thread_id)

    if not body and not attachment_files:
        if _is_ajax_request():
            return jsonify({"ok": False, "error": "empty", "message": "Boş mesaj gönderilemez."}), 400
        flash("Boş mesaj gönderilemez.", "warning")
        return _redirect_message_destination(thread_id=thread_id)

    form_scope = f"{current_user.id}:{thread_id}"
    if not consume_form_token("messages_send", request.form.get("_form_token"), scope=form_scope):
        next_token = issue_form_token("messages_send", scope=form_scope)
        if _is_ajax_request():
            return jsonify({
                "ok": False,
                "error": "duplicate",
                "message": "Bu mesaj zaten gönderiliyor ya da az önce gönderildi.",
                "next_form_token": next_token,
            }), 409
        flash("Bu mesaj zaten gönderiliyor ya da az önce gönderildi. Bir kez daha basmaya gerek yok.", "info")
        return _redirect_message_destination(thread_id=thread_id)

    try:
        send_result = _svc_append_thread_message_with_attachments(
            thread=thread,
            participant=participant,
            body=body,
            attachment_files=attachment_files,
            now=_utcnow(),
        )
        message = send_result.sent_message
        next_token = issue_form_token("messages_send", scope=form_scope)
        if _is_ajax_request():
            payload = _thread_counts_payload(thread, participant)
            payload.update({
                "ok": True,
                "message": send_result.message,
                "sent_message": _serialize_message(message),
                "next_form_token": next_token,
            })
            return jsonify(payload)

        flash(send_result.message, "success")

    except ValueError as exc:
        if _is_ajax_request():
            return jsonify({"ok": False, "error": "validation_error", "message": str(exc)}), 400
        flash(str(exc), "warning")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/messages_routes.py | line=449")
        if _is_ajax_request():
            return jsonify({"ok": False, "error": "server_error", "message": f"Mesaj gönderilirken hata oluştu: {exc}"}), 500
        flash(f"Mesaj gönderilirken hata oluştu: {exc}", "danger")

    return _redirect_message_destination(thread_id=thread_id)


def messages_mark_read_impl(thread_id):
    # BYS360_A5_P2D6_WRITE_CONTRACT: db.session.commit | db.session.rollback | _save_message_attachment | save_message_attachment | _notify_user
    result = _svc_mark_thread_read_for_user(thread_id, current_user.id)
    if not result.ok:
        flash(result.message or "Konuşma bulunamadı.", "danger")
        return _redirect_messages_view()

    flash(result.message or "Konuşma okundu olarak işaretlendi.", "success")
    return _redirect_message_destination(thread_id=thread_id)

def messages_toggle_mute_impl(thread_id):
    # BYS360_A5_P2D6_WRITE_CONTRACT: db.session.commit | db.session.rollback | _save_message_attachment | save_message_attachment | _notify_user
    try:
        result = _svc_toggle_thread_mute_for_user(thread_id, current_user.id, request.form.get("target_state"))
        if not result.ok:
            flash(result.message or "Konuşma bulunamadı.", "danger")
            return _redirect_messages_view()
        flash(result.message or "Sohbet durumu güncellendi.", "success")
    except ValueError as exc:
        flash(str(exc), "warning")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/messages_routes.py | line=475")
        db.session.rollback()
        flash(f"Sessize alma işlemi sırasında hata oluştu: {exc}", "danger")

    return _redirect_message_destination(thread_id=thread_id)

def messages_toggle_archive_impl(thread_id):
    # BYS360_A5_P2D6_WRITE_CONTRACT: db.session.commit | db.session.rollback | _save_message_attachment | save_message_attachment | _notify_user
    archived_after_change = False
    try:
        result = _svc_toggle_thread_archive_for_user(thread_id, current_user.id, request.form.get("target_state"))
        if not result.ok:
            flash(result.message or "Konuşma bulunamadı.", "danger")
            return _redirect_messages_view()
        archived_after_change = bool((result.payload or {}).get("is_archived"))
        flash(result.message or "Sohbet arşiv durumu güncellendi.", "success")
    except ValueError as exc:
        flash(str(exc), "warning")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/messages_routes.py | line=492")
        db.session.rollback()
        flash(f"Arşiv işlemi sırasında hata oluştu: {exc}", "danger")

    next_filter = request.form.get("current_filter") or request.args.get("filter") or "active"
    if archived_after_change and next_filter != "archived":
        return _redirect_messages_view()
    return _redirect_message_destination(thread_id=thread_id)

def messages_toggle_pin_impl(thread_id):
    # BYS360_A5_P2D6_WRITE_CONTRACT: db.session.commit | db.session.rollback | _save_message_attachment | save_message_attachment | _notify_user
    result = _svc_toggle_thread_pin_for_user(
        thread_id,
        current_user.id,
        session,
        request.form.get("target_state"),
    )
    if not result.ok:
        flash(result.message or "Konuşma bulunamadı.", "danger")
        return _redirect_messages_view()

    payload = result.payload or {}
    flash(result.message or "Sohbet sabitleme durumu güncellendi.", payload.get("flash_level") or "success")
    return _redirect_message_destination(thread_id=thread_id)

def _message_mutation_response(result, *, ajax_error_key: str):
    if _is_ajax_request():
        payload = {
            "ok": bool(result.ok),
            "message": result.message,
        }
        if not result.ok:
            payload["error"] = result.error or ajax_error_key
        if result.payload:
            payload.update(result.payload)
        return jsonify(payload), result.status_code

    flash(result.message, result.flash_level)
    thread_id = (result.payload or {}).get("thread_id")
    if result.ok or thread_id:
        return _redirect_message_destination(thread_id=thread_id)
    return _redirect_messages_view()


def messages_edit_impl(message_id):
    # BYS360_A5_P2D6_WRITE_CONTRACT: db.session.commit | db.session.rollback | _save_message_attachment | save_message_attachment | _notify_user
    new_body = _clean_message_body(request.form.get("body"))
    try:
        result = _svc_edit_message_for_user(
            message_id,
            user_id=current_user.id,
            new_body=new_body,
            now=_utcnow(),
        )
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/messages_routes.py | line=544")
        _log_communication_exception("messages_edit", exc, message_id=message_id, user_id=getattr(current_user, "id", None))
        if _is_ajax_request():
            return jsonify({"ok": False, "error": "server_error", "message": f"Mesaj güncellenirken hata oluştu: {exc}"}), 500
        flash(f"Mesaj güncellenirken hata oluştu: {exc}", "danger")
        return _redirect_messages_view()

    return _message_mutation_response(result, ajax_error_key="edit_error")


def messages_delete_impl(message_id):
    # BYS360_A5_P2D6_WRITE_CONTRACT: db.session.commit | db.session.rollback | _save_message_attachment | save_message_attachment | _notify_user
    try:
        result = _svc_delete_message_for_user(
            message_id,
            user_id=current_user.id,
            now=_utcnow(),
        )
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/messages_routes.py | line=561")
        _log_communication_exception("messages_delete", exc, message_id=message_id, user_id=getattr(current_user, "id", None))
        if _is_ajax_request():
            return jsonify({"ok": False, "error": "server_error", "message": f"Mesaj silinirken hata oluştu: {exc}"}), 500
        flash(f"Mesaj silinirken hata oluştu: {exc}", "danger")
        return _redirect_messages_view()

    return _message_mutation_response(result, ajax_error_key="delete_error")


def message_attachment_download_impl(filename):
    result = _svc_resolve_message_attachment_download_for_user(filename, user_id=current_user.id)
    if not result.ok:
        flash(result.message or "Bu dosyayı görüntüleme yetkiniz yok ya da dosya bulunamadı.", "danger")
        return redirect(url_for("main.messages_inbox"))

    return send_from_directory(result.upload_dir, result.safe_name, as_attachment=False, download_name=result.download_name)


@main_bp.route("/messages")
@login_required
@menu_key_required("messages")
def messages_inbox():
    return messages_inbox_impl()


@main_bp.route("/messages/new", methods=["GET", "POST"])
@login_required
@menu_key_required("messages")
def messages_new():
    return messages_new_impl()


@main_bp.route("/messages/thread/<int:thread_id>")
@login_required
@menu_key_required("messages")
def messages_thread(thread_id):
    return messages_thread_impl(thread_id)


@main_bp.route("/messages/thread/<int:thread_id>/activity")
@login_required
@menu_key_required("messages")
def messages_thread_activity(thread_id):
    return messages_thread_activity_impl(thread_id)


@main_bp.route("/messages/thread/<int:thread_id>/live")
@login_required
@menu_key_required("messages")
def messages_thread_live(thread_id):
    return messages_thread_live_impl(thread_id)


@main_bp.route("/messages/thread/<int:thread_id>/typing", methods=["POST"])
@login_required
@menu_key_required("messages")
def messages_thread_typing(thread_id):
    return messages_thread_typing_impl(thread_id)


@main_bp.route("/messages/<int:message_id>/react", methods=["POST"])
@login_required
@menu_key_required("messages")
def messages_react(message_id):
    return messages_react_impl(message_id)


@main_bp.route("/messages/<int:message_id>/comment", methods=["POST"])
@login_required
@menu_key_required("messages")
def messages_comment(message_id):
    return messages_comment_impl(message_id)

# BYS360_MESSAGE_INTERACTIONS_V1_ROUTE


@main_bp.route("/messages/thread/<int:thread_id>/send", methods=["POST"])
@login_required
@menu_key_required("messages")
def messages_send(thread_id):
    return messages_send_impl(thread_id)


@main_bp.route("/messages/thread/<int:thread_id>/mark-read", methods=["POST"])
@login_required
@menu_key_required("messages")
def messages_mark_read(thread_id):
    return messages_mark_read_impl(thread_id)


@main_bp.route("/messages/thread/<int:thread_id>/mute-toggle", methods=["POST"])
@login_required
@menu_key_required("messages")
def messages_toggle_mute(thread_id):
    return messages_toggle_mute_impl(thread_id)


@main_bp.route("/messages/thread/<int:thread_id>/archive-toggle", methods=["POST"])
@login_required
@menu_key_required("messages")
def messages_toggle_archive(thread_id):
    return messages_toggle_archive_impl(thread_id)


@main_bp.route("/messages/thread/<int:thread_id>/pin-toggle", methods=["POST"])
@login_required
@menu_key_required("messages")
def messages_toggle_pin(thread_id):
    return messages_toggle_pin_impl(thread_id)


@main_bp.route("/messages/<int:message_id>/edit", methods=["POST"])
@login_required
@menu_key_required("messages")
def messages_edit(message_id):
    return messages_edit_impl(message_id)


@main_bp.route("/messages/<int:message_id>/delete", methods=["POST"])
@login_required
@menu_key_required("messages")
def messages_delete(message_id):
    return messages_delete_impl(message_id)


@main_bp.route("/messages/attachments/<filename>")
@login_required
@menu_key_required("messages")
def message_attachment_download(filename):
    return message_attachment_download_impl(filename)


messages_thread_send = messages_send
messages_thread_mark_read = messages_mark_read
messages_thread_mute_toggle = messages_toggle_mute
messages_thread_archive_toggle = messages_toggle_archive
messages_thread_pin_toggle = messages_toggle_pin
