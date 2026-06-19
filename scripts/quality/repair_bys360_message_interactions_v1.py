from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

MARKER = "BYS360_MESSAGE_INTERACTIONS_V1"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def backup(path: Path, backup_root: Path, project_root: Path) -> None:
    if not path.exists():
        return
    rel = path.resolve().relative_to(project_root.resolve())
    target = backup_root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(path, target)


def replace_once(text: str, old: str, new: str, label: str) -> tuple[str, bool]:
    if old not in text:
        raise RuntimeError(f"Beklenen blok bulunamadı: {label}")
    return text.replace(old, new, 1), True


def append_before(text: str, needle: str, addition: str, label: str) -> tuple[str, bool]:
    if addition.strip() in text:
        return text, False
    if needle not in text:
        raise RuntimeError(f"Beklenen ekleme noktası bulunamadı: {label}")
    return text.replace(needle, addition + needle, 1), True


def patch_constants(path: Path) -> bool:
    text = read(path)
    changed = False
    old = 'REACTION_OPTIONS: list[str] = ["👍", "❤️", "👏", "✅", "👀", "🙏"]'
    new = 'REACTION_OPTIONS: list[str] = ["👍", "👎", "❤️", "👏", "✅", "👀", "🙏"]  # BYS360_MESSAGE_INTERACTIONS_V1'
    if old in text:
        text = text.replace(old, new, 1)
        changed = True
    elif 'REACTION_OPTIONS: list[str] = ["👍", "👎"' not in text:
        raise RuntimeError("REACTION_OPTIONS satırı bulunamadı")

    if '"/messages/<int:message_id>/comment",' not in text:
        text, did = replace_once(
            text,
            '    "/messages/<int:message_id>/react",\n',
            '    "/messages/<int:message_id>/react",\n    "/messages/<int:message_id>/comment",  # BYS360_MESSAGE_INTERACTIONS_V1\n',
            "MESSAGE_LIVE_ENDPOINTS comment",
        )
        changed = changed or did

    if '"MessageComment",' not in text:
        text, did = replace_once(
            text,
            '    "MessageReaction",\n',
            '    "MessageReaction",\n    "MessageComment",  # BYS360_MESSAGE_INTERACTIONS_V1\n',
            "MESSAGE_REQUIRED_MODEL_NAMES MessageComment",
        )
        changed = changed or did

    if changed:
        write(path, text)
    return changed


def patch_model(path: Path) -> bool:
    text = read(path)
    if 'class MessageComment' in text:
        return False
    block = '''\n\nclass MessageComment(TimestampMixin, db.Model):\n    __tablename__ = "message_comments"\n\n    id = db.Column(db.Integer, primary_key=True)\n    message_id = db.Column(\n        db.Integer,\n        db.ForeignKey("messages.id", ondelete="CASCADE"),\n        nullable=False,\n        index=True,\n    )\n    user_id = db.Column(\n        db.Integer,\n        db.ForeignKey("users.id", ondelete="CASCADE"),\n        nullable=False,\n        index=True,\n    )\n    body = db.Column(db.Text, nullable=False)\n    is_deleted = db.Column(db.Boolean, nullable=False, default=False, index=True)\n    edited_at = db.Column(db.DateTime, nullable=True)\n\n    message = db.relationship(\n        "Message",\n        backref=db.backref("comments", lazy="dynamic", cascade="all, delete-orphan"),\n    )\n    user = db.relationship("User", foreign_keys=[user_id])\n\n    def __repr__(self):\n        return f"<MessageComment message={self.message_id} user={self.user_id}>"\n\n# BYS360_MESSAGE_INTERACTIONS_V1_MODEL\n'''
    needle = '\n\nclass MessageTypingState(TimestampMixin, db.Model):\n'
    text, _ = replace_once(text, needle, block + needle, "MessageTypingState öncesi MessageComment")
    write(path, text)
    return True


def patch_models_init(path: Path) -> bool:
    text = read(path)
    changed = False
    if 'MessageComment' not in text.split('from .communication_models import (', 1)[1].split(')', 1)[0]:
        text, did = replace_once(
            text,
            '    MessageAttachment,\n    MessageReaction,\n',
            '    MessageAttachment,\n    MessageReaction,\n    MessageComment,  # BYS360_MESSAGE_INTERACTIONS_V1\n',
            "communication model imports",
        )
        changed = changed or did
    if '"MessageComment"' not in text.split('__all__ = [', 1)[1]:
        text, did = replace_once(
            text,
            '    "MessageReaction",\n',
            '    "MessageReaction",\n    "MessageComment",  # BYS360_MESSAGE_INTERACTIONS_V1\n',
            "__all__ MessageComment",
        )
        changed = changed or did
    if changed:
        write(path, text)
    return changed


def patch_schema_guard(path: Path) -> bool:
    text = read(path)
    if 'table="message_comments"' in text:
        return False
    block = '''TableRepair(\n    table="message_comments",\n    create_sql="""\n    CREATE TABLE IF NOT EXISTS message_comments (\n        id SERIAL PRIMARY KEY,\n        message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,\n        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,\n        body TEXT NOT NULL,\n        is_deleted BOOLEAN NOT NULL DEFAULT FALSE,\n        edited_at TIMESTAMP NULL,\n        created_at TIMESTAMP NOT NULL DEFAULT NOW(),\n        updated_at TIMESTAMP NOT NULL DEFAULT NOW()\n    )\n    """,\n    column_sql=(\n        "ALTER TABLE message_comments ADD COLUMN IF NOT EXISTS message_id INTEGER",\n        "ALTER TABLE message_comments ADD COLUMN IF NOT EXISTS user_id INTEGER",\n        "ALTER TABLE message_comments ADD COLUMN IF NOT EXISTS body TEXT NOT NULL DEFAULT ''",\n        "ALTER TABLE message_comments ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE",\n        "ALTER TABLE message_comments ADD COLUMN IF NOT EXISTS edited_at TIMESTAMP NULL",\n        "ALTER TABLE message_comments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT NOW()",\n        "ALTER TABLE message_comments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT NOW()",\n    ),\n    index_sql=(\n        "CREATE INDEX IF NOT EXISTS ix_message_comments_message_id ON message_comments (message_id)",\n        "CREATE INDEX IF NOT EXISTS ix_message_comments_user_id ON message_comments (user_id)",\n        "CREATE INDEX IF NOT EXISTS ix_message_comments_is_deleted ON message_comments (is_deleted)",\n        "CREATE INDEX IF NOT EXISTS ix_message_comments_created_at ON message_comments (created_at)",\n    ),\n),\n# BYS360_MESSAGE_INTERACTIONS_V1_SCHEMA\n'''
    needle = 'TableRepair(\n    table="message_typing_states",'
    text, _ = append_before(text, needle, block, "message_typing_states öncesi message_comments")
    write(path, text)
    return True


def write_comments_service(path: Path) -> bool:
    content = '''from __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom typing import Any\n\nfrom flask import url_for\nfrom flask_login import current_user\n\nfrom app.extensions import db\nfrom app.models import Message, MessageComment, MessageThreadParticipant\nfrom app.services.message_service import notify_user\n\nfrom .repository import orm_entity, participant_for_thread\nfrom .serialization import serialize_comment\n\n\n@dataclass\nclass MessageCommentResult:\n    ok: bool\n    message: str\n    comment: Any | None = None\n    message_row: Any | None = None\n    comment_count: int = 0\n\n\ndef _comment_count(message: Message) -> int:\n    try:\n        return (\n            MessageComment.query\n            .filter_by(message_id=message.id, is_deleted=False)\n            .count()\n        )\n    except Exception:\n        return 0\n\n\ndef create_message_comment(message_id: int, body: str, *, now) -> tuple[dict[str, Any], int]:\n    \"\"\"Mesaj altına yetki kontrollü yorum ekler.\n\n    Yorumlar, konuşma katılımcılarıyla sınırlıdır. Sayfa yenilemeden çalışan web\n    arayüzü için JSON payload döner; normal CSRF koruması route katmanında kalır.\n    \"\"\"\n\n    message = db.session.get(orm_entity(Message), message_id)\n    if not message or getattr(message, "is_deleted", False):\n        return {"ok": False, "error": "not_found", "message": "Mesaj bulunamadı."}, 404\n\n    participant = participant_for_thread(getattr(message, "thread_id", None))\n    if not participant:\n        return {"ok": False, "error": "forbidden", "message": "Bu mesaja yorum yapma yetkiniz bulunmamaktadır."}, 403\n\n    cleaned_body = (body or "").strip()[:1200]\n    if not cleaned_body:\n        return {"ok": False, "error": "empty", "message": "Boş yorum gönderilemez."}, 400\n\n    try:\n        comment = MessageComment(\n            message_id=message.id,\n            user_id=current_user.id,\n            body=cleaned_body,\n        )\n        db.session.add(comment)\n        db.session.flush()\n\n        sender_id = getattr(message, "sender_user_id", None)\n        if sender_id and int(sender_id) != int(current_user.id):\n            sender_participant = (\n                MessageThreadParticipant.query\n                .filter_by(thread_id=message.thread_id, user_id=sender_id)\n                .filter(MessageThreadParticipant.left_at.is_(None))\n                .first()\n            )\n            if sender_participant and not getattr(sender_participant, "is_muted", False):\n                notify_user(\n                    sender_id,\n                    title="Mesajınıza yorum yapıldı",\n                    body="BYS360 mesajınız için yeni bir yorum var.",\n                    notification_type="message_comment",\n                    source_type="message",\n                    source_id=message.id,\n                    link_url=url_for("main.messages_inbox", thread_id=message.thread_id),\n                    priority="normal",\n                )\n\n        db.session.commit()\n        return {\n            "ok": True,\n            "message": "Yorum eklendi.",\n            "message_id": message.id,\n            "comment": serialize_comment(comment),\n            "comment_count": _comment_count(message),\n        }, 200\n    except Exception as exc:  # pragma: no cover - canlı DB guard\n        db.session.rollback()\n        return {"ok": False, "error": "server_error", "message": f"Yorum eklenirken hata oluştu: {exc}"}, 500\n\n# BYS360_MESSAGE_INTERACTIONS_V1_COMMENTS_SERVICE\n'''
    if path.exists() and MARKER in read(path):
        return False
    write(path, content)
    return True


def patch_serialization(path: Path) -> bool:
    text = read(path)
    changed = False
    if 'MessageComment' not in text.split('\n', 20)[0:20].__str__():
        text, did = replace_once(
            text,
            'from app.models import MessageAttachment, MessageReaction\n',
            'from app.models import MessageAttachment, MessageComment, MessageReaction  # BYS360_MESSAGE_INTERACTIONS_V1\n',
            "serialization imports",
        )
        changed = changed or did

    if 'def serialize_comment' not in text:
        block = '''\n\ndef serialize_comment(comment: Any) -> dict[str, Any]:\n    \"\"\"Mesaj yorumu için güvenli JSON payload üretir.\"\"\"\n\n    user = getattr(comment, "user", None)\n    full_name = getattr(user, "full_name", None)\n    fallback_name = " ".join([str(getattr(user, "ad", "") or "").strip(), str(getattr(user, "soyad", "") or "").strip()]).strip() if user else ""\n    created_at = getattr(comment, "created_at", None)\n    edited_at = getattr(comment, "edited_at", None)\n    return {\n        "id": getattr(comment, "id", None),\n        "message_id": getattr(comment, "message_id", None),\n        "user_id": getattr(comment, "user_id", None),\n        "user_name": full_name or fallback_name or "Kullanıcı",\n        "body": getattr(comment, "body", "") or "",\n        "created_at": created_at.isoformat() if created_at else None,\n        "created_at_label": format_dt_label(created_at) or "-",\n        "edited_at": edited_at.isoformat() if edited_at else None,\n        "is_mine": getattr(comment, "user_id", None) == getattr(current_user, "id", None),\n    }\n\n\ndef _comments_for_message(message: Any) -> list[dict[str, Any]]:\n    try:\n        rows = (\n            message.comments\n            .filter_by(is_deleted=False)\n            .order_by(MessageComment.id.asc())\n            .all()\n        )\n    except Exception:\n        logger.exception("BYS360 message comments serialization guard")\n        rows = []\n    return [serialize_comment(row) for row in rows]\n\n# BYS360_MESSAGE_INTERACTIONS_V1_SERIALIZATION\n'''
        needle = '\ndef serialize_message(message: Any, reaction_map: dict[int, list[dict[str, Any]]] | None = None) -> dict[str, Any]:\n'
        text, did = append_before(text, needle, block, "serialize_message öncesi comments")
        changed = changed or did

    if '"comments": _comments_for_message(message),' not in text:
        text, did = replace_once(
            text,
            '        "reactions": reactions,\n        "reaction_options": REACTION_OPTIONS,\n',
            '        "reactions": reactions,\n        "comments": _comments_for_message(message),\n        "comment_count": len(_comments_for_message(message)),\n        "reaction_options": REACTION_OPTIONS,\n',
            "serialize_message comments payload",
        )
        changed = changed or did

    if changed:
        write(path, text)
    return changed


def patch_messages_init(path: Path) -> bool:
    text = read(path)
    changed = False
    if 'from .comments import MessageCommentResult, create_message_comment' not in text:
        text, did = replace_once(
            text,
            'from .reactions import normalize_reaction_value, toggle_message_reaction\n',
            'from .reactions import normalize_reaction_value, toggle_message_reaction\nfrom .comments import MessageCommentResult, create_message_comment  # BYS360_MESSAGE_INTERACTIONS_V1\n',
            "messages package comments import",
        )
        changed = changed or did
    if 'MessageCommentResult' not in text.split('__all__ = [', 1)[1]:
        text, did = replace_once(
            text,
            '    "MessageSendResult",\n',
            '    "MessageSendResult",\n    "MessageCommentResult",  # BYS360_MESSAGE_INTERACTIONS_V1\n',
            "__all__ MessageCommentResult",
        )
        changed = changed or did
    if '    "create_message_comment",' not in text:
        text, did = replace_once(
            text,
            '    "toggle_message_reaction",\n',
            '    "toggle_message_reaction",\n    "create_message_comment",  # BYS360_MESSAGE_INTERACTIONS_V1\n',
            "__all__ create_message_comment",
        )
        changed = changed or did
    if changed:
        write(path, text)
    return changed


def patch_routes(path: Path) -> bool:
    text = read(path)
    changed = False
    if 'create_message_comment as _svc_create_message_comment' not in text:
        text, did = replace_once(
            text,
            '    toggle_message_reaction as _svc_toggle_message_reaction,\n',
            '    toggle_message_reaction as _svc_toggle_message_reaction,\n    create_message_comment as _svc_create_message_comment,  # BYS360_MESSAGE_INTERACTIONS_V1\n',
            "routes comments import",
        )
        changed = changed or did

    if 'def messages_comment_impl' not in text:
        block = '''\n\ndef messages_comment_impl(message_id):\n    # BYS360_MESSAGE_INTERACTIONS_V1_COMMENT_ROUTE\n    json_payload = request.get_json(silent=True) or {}\n    body = _clean_message_body(request.form.get("body") or json_payload.get("body") or "", limit=1200)\n    response_payload, status_code = _svc_create_message_comment(message_id, body, now=_utcnow())\n    if _is_ajax_request():\n        return jsonify(response_payload), status_code\n    if response_payload.get("ok"):\n        flash(response_payload.get("message") or "Yorum eklendi.", "success")\n    else:\n        flash(response_payload.get("message") or "Yorum eklenemedi.", "warning")\n    return _redirect_messages_view()\n'''
        needle = '\ndef messages_send_impl(thread_id):\n'
        text, did = append_before(text, needle, block, "messages_send_impl öncesi messages_comment_impl")
        changed = changed or did

    if 'selected_reaction_map = _build_reaction_map(messages)' not in text:
        text, did = replace_once(
            text,
            '    messages = detail_payload["messages"]\n\n    compose_submit_token = issue_form_token("messages_send", scope=f"{current_user.id}:{thread.id}")\n',
            '    messages = detail_payload["messages"]\n    selected_reaction_map = _build_reaction_map(messages)  # BYS360_MESSAGE_INTERACTIONS_V1\n\n    compose_submit_token = issue_form_token("messages_send", scope=f"{current_user.id}:{thread.id}")\n',
            "thread detail reaction map",
        )
        changed = changed or did

    if 'selected_reaction_map=selected_reaction_map,' not in text:
        text, did = replace_once(
            text,
            '        messages=messages,\n        back_url=back_url,\n',
            '        messages=messages,\n        selected_reaction_map=selected_reaction_map,  # BYS360_MESSAGE_INTERACTIONS_V1\n        reaction_options=REACTION_OPTIONS,  # BYS360_MESSAGE_INTERACTIONS_V1\n        back_url=back_url,\n',
            "thread render reaction map",
        )
        changed = changed or did

    if '@main_bp.route("/messages/<int:message_id>/comment", methods=["POST"])' not in text:
        route_block = '''\n\n@main_bp.route("/messages/<int:message_id>/comment", methods=["POST"])\n@login_required\n@menu_key_required("messages")\ndef messages_comment(message_id):\n    return messages_comment_impl(message_id)\n\n# BYS360_MESSAGE_INTERACTIONS_V1_ROUTE\n'''
        needle = '\n\n@main_bp.route("/messages/thread/<int:thread_id>/send", methods=["POST"])\n'
        text, did = append_before(text, needle, route_block, "messages_send route öncesi messages_comment route")
        changed = changed or did

    if changed:
        write(path, text)
    return changed


INTERACTION_BLOCK = '''\n\n                  {# BYS360_MESSAGE_INTERACTIONS_V1_BLOCK_START #}\n                  {% set reaction_items = (selected_reaction_map.get(message.id, []) if selected_reaction_map is defined and selected_reaction_map else []) %}\n                  {% set message_comments = (message.comments.all() if message.comments is defined and not message.is_deleted else []) %}\n                  <div class="msg-interactions" data-message-interactions data-message-id="{{ message.id }}">\n                    <div class="msg-reaction-summary" data-message-reactions>\n                      {% for reaction_item in reaction_items %}\n                        <span class="msg-reaction-pill {% if reaction_item.mine %}mine{% endif %}"><span>{{ reaction_item.emoji }}</span><strong>{{ reaction_item.count }}</strong></span>\n                      {% endfor %}\n                    </div>\n\n                    {% if not message.is_deleted %}\n                    <div class="msg-reaction-actions">\n                      {% for reaction_option in reaction_options %}\n                        <form method="POST" action="{{ url_for('main.messages_react', message_id=message.id) }}" class="js-message-reaction-form" data-message-id="{{ message.id }}">\n                          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">\n                          <input type="hidden" name="reaction" value="{{ reaction_option }}">\n                          <button type="submit" class="msg-reaction-btn" title="Tepki ver">{{ reaction_option }}</button>\n                        </form>\n                      {% endfor %}\n                      <button type="button" class="msg-reaction-btn comment-toggle" data-message-comment-toggle data-message-id="{{ message.id }}">\n                        <i class="fa-regular fa-comment"></i> Yorum\n                      </button>\n                    </div>\n                    {% endif %}\n\n                    <div class="msg-comments" data-message-comments>\n                      {% for comment in message_comments %}\n                        {% if not comment.is_deleted %}\n                          {% set comment_name = comment.user.full_name if comment.user and comment.user.full_name else (((comment.user.ad or '') ~ ' ' ~ (comment.user.soyad or ''))|trim if comment.user else 'Kullanıcı') %}\n                          <div class="msg-comment-item" data-comment-id="{{ comment.id }}">\n                            <strong>{{ comment_name }}</strong>\n                            <span>{{ comment.body }}</span>\n                            <small>{{ comment.created_at.strftime('%d.%m.%Y %H:%M') if comment.created_at else '-' }}</small>\n                          </div>\n                        {% endif %}\n                      {% endfor %}\n                    </div>\n\n                    {% if not message.is_deleted %}\n                    <form method="POST" action="{{ url_for('main.messages_comment', message_id=message.id) }}" class="msg-comment-form js-message-comment-form" data-message-id="{{ message.id }}" hidden>\n                      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">\n                      <input type="text" name="body" maxlength="1200" autocomplete="off" placeholder="Bu mesaja yorum yazın...">\n                      <button type="submit"><i class="fa-solid fa-paper-plane"></i></button>\n                    </form>\n                    {% endif %}\n                  </div>\n                  {# BYS360_MESSAGE_INTERACTIONS_V1_BLOCK_END #}\n'''


def patch_template(path: Path) -> bool:
    text = read(path)
    if 'BYS360_MESSAGE_INTERACTIONS_V1_BLOCK_START' in text:
        return False

    end_marker = "{% if message.edited_at %}<span>düzenlendi</span>{% endif %}"
    pos = text.find(end_marker)
    if pos < 0:
        raise RuntimeError(f"Beklenen blok bulunamadı: {path.name} msg-meta edited marker")
    close_pos = text.find("</div>", pos)
    if close_pos < 0:
        raise RuntimeError(f"Beklenen blok bulunamadı: {path.name} msg-meta close")
    insert_at = close_pos + len("</div>")
    text = text[:insert_at] + INTERACTION_BLOCK + text[insert_at:]

    # Cache busting for static JS/CSS to make live browser pick up the change.
    text = text.replace(
        "{{ url_for('static', filename='css/messages_messenger_mobile.css') }}",
        "{{ url_for('static', filename='css/messages_messenger_mobile.css') }}?v=message-interactions-v1",
    )
    text = text.replace(
        "{{ url_for('static', filename='js/messages_messenger_mobile.js') }}",
        "{{ url_for('static', filename='js/messages_messenger_mobile.js') }}?v=message-interactions-v1",
    )
    write(path, text)
    return True


def patch_js(path: Path) -> bool:
    text = read(path)
    changed = False
    if 'BYS360_MESSAGE_INTERACTIONS_V1_JS' not in text:
        insertion = r'''

  // BYS360_MESSAGE_INTERACTIONS_V1_JS
  function messageCsrfToken(){
    const input = document.querySelector('input[name="csrf_token"]');
    return input ? input.value : '';
  }

  function showMessageInlineFeedback(form, text, type){
    if(!form) return;
    let box = form.querySelector('.msg-inline-feedback');
    if(!box){
      box = document.createElement('div');
      box.className = 'msg-inline-feedback';
      form.appendChild(box);
    }
    box.textContent = text || '';
    box.dataset.type = type || 'info';
    box.hidden = !text;
  }

  function renderReactionSummary(holder, reactions){
    if(!holder) return;
    holder.innerHTML = '';
    (reactions || []).forEach(function(item){
      const pill = document.createElement('span');
      pill.className = 'msg-reaction-pill' + (item.mine ? ' mine' : '');
      const emoji = document.createElement('span');
      emoji.textContent = item.emoji || '';
      const count = document.createElement('strong');
      count.textContent = String(item.count || 0);
      pill.appendChild(emoji);
      pill.appendChild(count);
      holder.appendChild(pill);
    });
  }

  function renderCommentItem(comment){
    const item = document.createElement('div');
    item.className = 'msg-comment-item';
    if(comment && comment.id){ item.dataset.commentId = String(comment.id); }
    const name = document.createElement('strong');
    name.textContent = (comment && comment.user_name) || 'Kullanıcı';
    const body = document.createElement('span');
    body.textContent = (comment && comment.body) || '';
    const date = document.createElement('small');
    date.textContent = (comment && comment.created_at_label) || '-';
    item.appendChild(name);
    item.appendChild(body);
    item.appendChild(date);
    return item;
  }

  function renderAttachmentElement(attachment){
    const url = attachment.preview_url || attachment.download_url || '#';
    const name = attachment.original_filename || 'Dosya';
    if(attachment.is_image){
      const a = document.createElement('a');
      a.className = 'msg-attachment is-image';
      a.href = url;
      a.target = '_blank';
      const img = document.createElement('img');
      img.src = url;
      img.alt = name;
      a.appendChild(img);
      return a;
    }
    const a = document.createElement('a');
    a.className = 'msg-attachment';
    a.href = attachment.download_url || url;
    a.target = '_blank';
    const icon = document.createElement('i');
    icon.className = attachment.icon_class || 'fa-solid fa-paperclip';
    const span = document.createElement('span');
    span.textContent = name;
    a.appendChild(icon);
    a.appendChild(span);
    return a;
  }

  function buildMessageActions(message){
    const interactions = document.createElement('div');
    interactions.className = 'msg-interactions';
    interactions.dataset.messageInteractions = '1';
    interactions.dataset.messageId = String(message.id || '');

    const summary = document.createElement('div');
    summary.className = 'msg-reaction-summary';
    summary.dataset.messageReactions = '1';
    renderReactionSummary(summary, message.reactions || []);
    interactions.appendChild(summary);

    const actions = document.createElement('div');
    actions.className = 'msg-reaction-actions';
    (message.reaction_options || ['👍','👎','❤️','👏','✅']).forEach(function(emoji){
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/messages/' + encodeURIComponent(message.id) + '/react';
      form.className = 'js-message-reaction-form';
      form.dataset.messageId = String(message.id || '');
      const csrf = document.createElement('input');
      csrf.type = 'hidden'; csrf.name = 'csrf_token'; csrf.value = messageCsrfToken();
      const reaction = document.createElement('input');
      reaction.type = 'hidden'; reaction.name = 'reaction'; reaction.value = emoji;
      const btn = document.createElement('button');
      btn.type = 'submit'; btn.className = 'msg-reaction-btn'; btn.textContent = emoji;
      form.appendChild(csrf); form.appendChild(reaction); form.appendChild(btn);
      actions.appendChild(form);
    });
    const commentBtn = document.createElement('button');
    commentBtn.type = 'button';
    commentBtn.className = 'msg-reaction-btn comment-toggle';
    commentBtn.dataset.messageCommentToggle = '1';
    commentBtn.dataset.messageId = String(message.id || '');
    commentBtn.innerHTML = '<i class="fa-regular fa-comment"></i> Yorum';
    actions.appendChild(commentBtn);
    interactions.appendChild(actions);

    const comments = document.createElement('div');
    comments.className = 'msg-comments';
    comments.dataset.messageComments = '1';
    (message.comments || []).forEach(function(comment){ comments.appendChild(renderCommentItem(comment)); });
    interactions.appendChild(comments);

    const cform = document.createElement('form');
    cform.method = 'POST';
    cform.action = '/messages/' + encodeURIComponent(message.id) + '/comment';
    cform.className = 'msg-comment-form js-message-comment-form';
    cform.dataset.messageId = String(message.id || '');
    cform.hidden = true;
    const csrf = document.createElement('input'); csrf.type = 'hidden'; csrf.name = 'csrf_token'; csrf.value = messageCsrfToken();
    const input = document.createElement('input'); input.type = 'text'; input.name = 'body'; input.maxLength = 1200; input.autocomplete = 'off'; input.placeholder = 'Bu mesaja yorum yazın...';
    const send = document.createElement('button'); send.type = 'submit'; send.innerHTML = '<i class="fa-solid fa-paper-plane"></i>';
    cform.appendChild(csrf); cform.appendChild(input); cform.appendChild(send);
    interactions.appendChild(cform);
    return interactions;
  }

  function appendMessageToList(message){
    const box = document.getElementById('msgMessages');
    if(!box || !message) return;
    const empty = box.querySelector('.msg-empty');
    if(empty){ empty.remove(); }

    const row = document.createElement('div');
    row.className = 'msg-row' + (message.is_mine ? ' mine' : '');
    row.dataset.messageRow = '1';
    row.dataset.messageId = String(message.id || '');

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';

    const author = document.createElement('div');
    author.className = 'msg-author';
    author.textContent = message.sender_name || 'Kullanıcı';
    bubble.appendChild(author);

    if(message.body){
      const text = document.createElement('div');
      text.className = 'msg-text';
      text.textContent = message.body;
      bubble.appendChild(text);
    }

    if(message.attachments && message.attachments.length){
      const attachments = document.createElement('div');
      attachments.className = 'msg-attachments';
      message.attachments.forEach(function(attachment){ attachments.appendChild(renderAttachmentElement(attachment)); });
      bubble.appendChild(attachments);
    }

    const meta = document.createElement('div');
    meta.className = 'msg-meta';
    const date = document.createElement('span');
    date.textContent = message.sent_at_label || '-';
    meta.appendChild(date);
    bubble.appendChild(meta);
    bubble.appendChild(buildMessageActions(message));

    row.appendChild(bubble);
    box.appendChild(row);
    decorateMessageLinks();
    scrollMessagesToBottom();
  }

  function resetComposeForm(form, payload){
    const textarea = form.querySelector('textarea[name="body"]');
    if(textarea){ textarea.value = ''; autogrow(textarea); }
    const fileInput = form.querySelector('.js-message-attachment-input');
    if(fileInput){ fileInput.value = ''; }
    const preview = form.querySelector('.js-message-attachment-preview');
    if(preview){ preview.innerHTML = ''; preview.hidden = true; }
    const token = form.querySelector('input[name="_form_token"]');
    if(token && payload && payload.next_form_token){ token.value = payload.next_form_token; }
  }
'''
        needle = '  document.addEventListener(\'DOMContentLoaded\', function(){\n'
        text, did = append_before(text, needle, insertion, "DOMContentLoaded öncesi JS helpers")
        changed = changed or did

    old_block = '''    document.querySelectorAll('.msg-compose-form').forEach(function(form){\n      let submitted = false;\n      const fileInput = form.querySelector('.js-message-attachment-input');\n      if(fileInput){\n        fileInput.addEventListener('change', function(){ renderAttachmentPreview(form); });\n      }\n      form.addEventListener('submit', function(event){\n        if(submitted){\n          event.preventDefault();\n          return false;\n        }\n        const textarea = form.querySelector('textarea[name="body"]');\n        const files = fileInput ? Array.from(fileInput.files || []) : [];\n        const body = textarea ? (textarea.value || '').trim() : '';\n        if(!body && !files.length){\n          event.preventDefault();\n          if(textarea){ textarea.focus(); }\n          return false;\n        }\n        submitted = true;\n        const btn = form.querySelector('.msg-send');\n        if(btn){\n          btn.disabled = true;\n          btn.classList.add('is-busy');\n        }\n      });\n    });\n'''
    new_block = '''    document.querySelectorAll('.msg-compose-form').forEach(function(form){\n      let submitted = false;\n      const fileInput = form.querySelector('.js-message-attachment-input');\n      if(fileInput){\n        fileInput.addEventListener('change', function(){ renderAttachmentPreview(form); });\n      }\n      form.addEventListener('submit', function(event){\n        const textarea = form.querySelector('textarea[name="body"]');\n        const files = fileInput ? Array.from(fileInput.files || []) : [];\n        const body = textarea ? (textarea.value || '').trim() : '';\n        if(!body && !files.length){\n          event.preventDefault();\n          if(textarea){ textarea.focus(); }\n          return false;\n        }\n        event.preventDefault();\n        if(submitted){ return false; }\n        submitted = true;\n        const btn = form.querySelector('.msg-send');\n        if(btn){\n          btn.disabled = true;\n          btn.classList.add('is-busy');\n        }\n        showMessageInlineFeedback(form, 'Mesaj gönderiliyor...', 'info');\n        fetch(form.action, {\n          method: 'POST',\n          body: new FormData(form),\n          headers: {\n            'X-Requested-With': 'XMLHttpRequest',\n            'Accept': 'application/json'\n          },\n          credentials: 'same-origin'\n        }).then(function(response){\n          return response.json().catch(function(){ return {}; }).then(function(payload){\n            if(!response.ok || !payload.ok){\n              throw payload || { message: 'Mesaj gönderilemedi.' };\n            }\n            return payload;\n          });\n        }).then(function(payload){\n          if(payload.sent_message){ appendMessageToList(payload.sent_message); }\n          resetComposeForm(form, payload);\n          showMessageInlineFeedback(form, payload.message || 'Mesaj gönderildi.', 'success');\n          setTimeout(function(){ showMessageInlineFeedback(form, '', 'info'); }, 1800);\n        }).catch(function(error){\n          showMessageInlineFeedback(form, (error && error.message) || 'Mesaj gönderilemedi. Lütfen tekrar deneyin.', 'error');\n        }).finally(function(){\n          submitted = false;\n          if(btn){\n            btn.disabled = false;\n            btn.classList.remove('is-busy');\n          }\n        });\n        return false;\n      });\n    });\n\n    document.addEventListener('submit', function(event){\n      const reactionForm = event.target.closest('.js-message-reaction-form');\n      if(reactionForm){\n        event.preventDefault();\n        const messageId = reactionForm.dataset.messageId || '';\n        const btn = reactionForm.querySelector('button');\n        if(btn){ btn.disabled = true; }\n        fetch(reactionForm.action, {\n          method: 'POST',\n          body: new FormData(reactionForm),\n          headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },\n          credentials: 'same-origin'\n        }).then(function(response){\n          return response.json().catch(function(){ return {}; }).then(function(payload){\n            if(!response.ok || !payload.ok){ throw payload || {}; }\n            return payload;\n          });\n        }).then(function(payload){\n          const root = document.querySelector('[data-message-interactions][data-message-id="' + CSS.escape(String(messageId || payload.message_id || '')) + '"]');\n          renderReactionSummary(root ? root.querySelector('[data-message-reactions]') : null, payload.reactions || []);\n        }).catch(function(){\n          window.alert('Tepki kaydedilemedi. Lütfen tekrar deneyin.');\n        }).finally(function(){\n          if(btn){ btn.disabled = false; }\n        });\n        return false;\n      }\n\n      const commentForm = event.target.closest('.js-message-comment-form');\n      if(commentForm){\n        event.preventDefault();\n        const input = commentForm.querySelector('input[name="body"]');\n        const body = input ? (input.value || '').trim() : '';\n        if(!body){ if(input){ input.focus(); } return false; }\n        const btn = commentForm.querySelector('button');\n        if(btn){ btn.disabled = true; }\n        fetch(commentForm.action, {\n          method: 'POST',\n          body: new FormData(commentForm),\n          headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },\n          credentials: 'same-origin'\n        }).then(function(response){\n          return response.json().catch(function(){ return {}; }).then(function(payload){\n            if(!response.ok || !payload.ok){ throw payload || {}; }\n            return payload;\n          });\n        }).then(function(payload){\n          const root = document.querySelector('[data-message-interactions][data-message-id="' + CSS.escape(String(payload.message_id || commentForm.dataset.messageId || '')) + '"]');\n          const list = root ? root.querySelector('[data-message-comments]') : null;\n          if(list && payload.comment){ list.appendChild(renderCommentItem(payload.comment)); }\n          if(input){ input.value = ''; input.focus(); }\n        }).catch(function(error){\n          window.alert((error && error.message) || 'Yorum eklenemedi. Lütfen tekrar deneyin.');\n        }).finally(function(){\n          if(btn){ btn.disabled = false; }\n        });\n        return false;\n      }\n    });\n\n    document.addEventListener('click', function(event){\n      const toggle = event.target.closest('[data-message-comment-toggle]');\n      if(!toggle) return;\n      const messageId = toggle.dataset.messageId || '';\n      const root = document.querySelector('[data-message-interactions][data-message-id="' + CSS.escape(String(messageId)) + '"]');\n      const form = root ? root.querySelector('.js-message-comment-form') : null;\n      if(!form) return;\n      form.hidden = !form.hidden;\n      if(!form.hidden){\n        const input = form.querySelector('input[name="body"]');\n        if(input){ input.focus(); }\n      }\n    });\n'''
    if old_block in text:
        text = text.replace(old_block, new_block, 1)
        changed = True
    elif 'Mesaj gönderiliyor...' not in text:
        raise RuntimeError("JS compose submit bloğu bulunamadı")

    if changed:
        write(path, text)
    return changed


def patch_css(path: Path) -> bool:
    text = read(path)
    if 'BYS360_MESSAGE_INTERACTIONS_V1_CSS' in text:
        return False
    css = r'''

/* BYS360_MESSAGE_INTERACTIONS_V1_CSS */
.msg-interactions{margin-top:8px;display:grid;gap:8px}
.msg-reaction-summary{display:flex;flex-wrap:wrap;gap:6px;min-height:0}
.msg-reaction-pill{display:inline-flex;align-items:center;gap:4px;padding:3px 8px;border-radius:999px;background:#fff;border:1px solid rgba(139,0,0,.14);font-size:.78rem;color:#374151;box-shadow:0 4px 10px rgba(15,23,42,.04)}
.msg-reaction-pill.mine{background:rgba(139,0,0,.08);border-color:rgba(139,0,0,.28);color:var(--msg-brand)}
.msg-reaction-pill strong{font-size:.72rem;font-weight:900}
.msg-reaction-actions{display:flex;align-items:center;gap:6px;flex-wrap:wrap;justify-content:flex-end}
.msg-reaction-actions form{display:inline-flex;margin:0}
.msg-reaction-btn{min-height:30px;min-width:32px;border:1px solid rgba(139,0,0,.12);border-radius:999px;background:rgba(255,255,255,.86);color:#374151;font-weight:900;font-size:.78rem;display:inline-flex;align-items:center;justify-content:center;gap:5px;cursor:pointer;transition:.16s ease;padding:5px 9px}
.msg-reaction-btn:hover{transform:translateY(-1px);background:rgba(139,0,0,.06);border-color:rgba(139,0,0,.26);color:var(--msg-brand)}
.msg-reaction-btn:disabled{opacity:.65;cursor:wait;transform:none}
.msg-reaction-btn.comment-toggle{font-size:.76rem;color:var(--msg-brand)}
.msg-comments{display:grid;gap:6px;margin-left:8px}
.msg-comment-item{display:grid;gap:2px;padding:7px 9px;border-radius:12px;background:rgba(255,255,255,.72);border:1px solid rgba(15,23,42,.07);font-size:.78rem;color:#374151}
.msg-comment-item strong{font-size:.74rem;color:var(--msg-brand);font-weight:900}
.msg-comment-item span{white-space:pre-wrap;word-break:break-word;line-height:1.45}
.msg-comment-item small{font-size:.68rem;color:#9ca3af;font-weight:800;justify-self:end}
.msg-comment-form{display:grid;grid-template-columns:minmax(0,1fr) 38px;gap:6px;align-items:center;margin-top:2px}
.msg-comment-form[hidden]{display:none!important}
.msg-comment-form input[name="body"]{min-height:38px;border-radius:999px;border:1px solid rgba(139,0,0,.13);background:#fff;padding:8px 12px;font-size:.82rem;outline:none;color:#374151}
.msg-comment-form input[name="body"]:focus{border-color:rgba(139,0,0,.35);box-shadow:0 0 0 3px rgba(139,0,0,.08)}
.msg-comment-form button{width:38px;height:38px;border:none;border-radius:999px;background:var(--msg-brand);color:#fff;display:inline-flex;align-items:center;justify-content:center;cursor:pointer}
.msg-comment-form button:disabled{opacity:.7;cursor:wait}
.msg-inline-feedback{grid-column:1 / -1;padding:7px 10px;border-radius:12px;font-size:.78rem;font-weight:800;background:rgba(15,23,42,.04);color:#475569}
.msg-inline-feedback[hidden]{display:none!important}
.msg-inline-feedback[data-type="success"]{background:rgba(22,163,74,.08);color:#166534}
.msg-inline-feedback[data-type="error"]{background:rgba(220,38,38,.08);color:#991b1b}
@media (max-width:767.98px){.msg-reaction-actions{justify-content:flex-start}.msg-comment-form{grid-template-columns:minmax(0,1fr) 36px}.msg-comment-form button{width:36px;height:36px}}
'''
    write(path, text + css)
    return True


def apply(project_root: Path, mode: str) -> dict[str, object]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / "backups" / f"message_interactions_v1_{timestamp}"
    files = [
        project_root / "app/models/communication_models.py",
        project_root / "app/models/__init__.py",
        project_root / "app/schema_guard_core_maintenances.py",
        project_root / "app/services/messages/constants.py",
        project_root / "app/services/messages/serialization.py",
        project_root / "app/services/messages/__init__.py",
        project_root / "app/communication/messages_routes.py",
        project_root / "app/templates/messages_inbox.html",
        project_root / "app/templates/messages_thread.html",
        project_root / "app/static/js/messages_messenger_mobile.js",
        project_root / "app/static/css/messages_messenger_mobile.css",
    ]
    for file in files:
        if not file.exists():
            raise FileNotFoundError(f"Dosya bulunamadı: {file}")
        backup(file, backup_root, project_root)

    changes: list[str] = []
    patchers = [
        ("model", lambda: patch_model(project_root / "app/models/communication_models.py")),
        ("models_init", lambda: patch_models_init(project_root / "app/models/__init__.py")),
        ("schema_guard", lambda: patch_schema_guard(project_root / "app/schema_guard_core_maintenances.py")),
        ("constants", lambda: patch_constants(project_root / "app/services/messages/constants.py")),
        ("comments_service", lambda: write_comments_service(project_root / "app/services/messages/comments.py")),
        ("serialization", lambda: patch_serialization(project_root / "app/services/messages/serialization.py")),
        ("messages_package", lambda: patch_messages_init(project_root / "app/services/messages/__init__.py")),
        ("routes", lambda: patch_routes(project_root / "app/communication/messages_routes.py")),
        ("messages_inbox_template", lambda: patch_template(project_root / "app/templates/messages_inbox.html")),
        ("messages_thread_template", lambda: patch_template(project_root / "app/templates/messages_thread.html")),
        ("messages_js", lambda: patch_js(project_root / "app/static/js/messages_messenger_mobile.js")),
        ("messages_css", lambda: patch_css(project_root / "app/static/css/messages_messenger_mobile.css")),
    ]
    for name, fn in patchers:
        if fn():
            changes.append(name)

    return {
        "ok": True,
        "mode": mode,
        "changed_count": len(changes),
        "changes": changes,
        "backup_root": str(backup_root),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", default="all", choices=["all", "repair"])
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    result = apply(project_root, args.mode)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
