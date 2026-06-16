from __future__ import annotations

from .attachments import (
    attachment_icon_class,
    attachment_is_image,
    attachment_is_video,
    format_attachment_file_size,
    get_message_attachment_for_user,
    normalize_incoming_message_files,
    remove_message_attachment_file,
    save_message_attachment,
)
from .compose import (
    ComposeUserCard,
    build_compose_user_card,
    build_compose_user_cards,
    build_recent_message_users_for_compose,
    load_active_compose_users,
    load_all_active_compose_users,
    resolve_active_recipient,
    sort_compose_users,
    user_display_name,
    user_initials,
)
from .constants import (
    COMPOSE_USER_SOFT_LIMIT,
    INBOX_THREAD_FETCH_LIMIT,
    INBOX_THREAD_FETCH_LIMIT_SEARCH,
    MESSAGE_LIVE_ENDPOINTS,
    MESSAGE_REQUIRED_MODEL_NAMES,
    REACTION_OPTIONS,
    THREAD_MESSAGE_SOFT_LIMIT,
)
from .contracts import MessageEndpointContract, MessageLiveContract, build_message_live_contract
from .formatting import format_dt_label, message_sender_initials, message_sender_name
from .inbox import (
    build_inbox_thread_collection,
    build_thread_card,
    build_thread_counts_payload,
    normalize_inbox_filter,
    normalize_inbox_scope,
    resolve_selected_inbox_thread,
)
from .presence import build_thread_presence
from .reactions import normalize_reaction_value, toggle_message_reaction
from .repository import orm_entity, participant_for_thread, thread_for_user
from .serialization import build_reaction_map, serialize_attachment, serialize_message
from .state import (
    MessageStateChangeResult,
    blocked_state,
    mark_thread_read_for_user,
    ok_state,
    toggle_thread_archive_for_user,
    toggle_thread_mute_for_user,
    toggle_thread_pin_for_user,
)

from .lifecycle import (
    MessageAttachmentDownloadResult,
    MessageMutationResult,
    delete_message_for_user,
    edit_message_for_user,
    resolve_message_attachment_download_for_user,
)

from .sending import (
    MessageSendResult,
    append_thread_message_with_attachments,
    create_direct_message_with_attachments,
    resolve_thread_for_sending,
)
from .typing import normalize_typing_flag, update_thread_typing_state
from .thread_detail import (
    build_thread_activity_payload,
    build_thread_live_payload,
    load_thread_detail_payload,
)

__all__ = [
    "COMPOSE_USER_SOFT_LIMIT",
    "ComposeUserCard",
    "INBOX_THREAD_FETCH_LIMIT",
    "INBOX_THREAD_FETCH_LIMIT_SEARCH",
    "MESSAGE_LIVE_ENDPOINTS",
    "MESSAGE_REQUIRED_MODEL_NAMES",
    "MessageEndpointContract",
    "MessageLiveContract",
    "MessageStateChangeResult",
    "MessageSendResult",
    "resolve_message_attachment_download_for_user",
    "edit_message_for_user",
    "delete_message_for_user",
    "MessageMutationResult",
    "MessageAttachmentDownloadResult",
    "REACTION_OPTIONS",
    "THREAD_MESSAGE_SOFT_LIMIT",
    "attachment_icon_class",
    "attachment_is_image",
    "attachment_is_video",
    "blocked_state",
    "build_compose_user_card",
    "build_compose_user_cards",
    "build_recent_message_users_for_compose",
    "load_active_compose_users",
    "load_all_active_compose_users",
    "resolve_active_recipient",
    "sort_compose_users",
    "build_message_live_contract",
    "resolve_selected_inbox_thread",
    "normalize_inbox_scope",
    "normalize_inbox_filter",
    "build_thread_activity_payload",
    "build_thread_live_payload",
    "load_thread_detail_payload",
    "build_thread_counts_payload",
    "build_thread_card",
    "build_inbox_thread_collection",
    "build_reaction_map",
    "build_thread_presence",
    "format_attachment_file_size",
    "format_dt_label",
    "get_message_attachment_for_user",
    "message_sender_initials",
    "message_sender_name",
    "normalize_reaction_value",
    "toggle_message_reaction",
    "normalize_typing_flag",
    "update_thread_typing_state",
    "normalize_incoming_message_files",
    "append_thread_message_with_attachments",
    "create_direct_message_with_attachments",
    "resolve_thread_for_sending",
    "ok_state",
    "mark_thread_read_for_user",
    "toggle_thread_archive_for_user",
    "toggle_thread_mute_for_user",
    "toggle_thread_pin_for_user",
    "orm_entity",
    "participant_for_thread",
    "remove_message_attachment_file",
    "save_message_attachment",
    "serialize_attachment",
    "serialize_message",
    "thread_for_user",
    "user_display_name",
    "user_initials",
]
