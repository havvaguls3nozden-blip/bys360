# -*- coding: utf-8 -*-
from __future__ import annotations


import logging

"""BYS360 Faz 3.6 — Yayın sonrası aynı seviye puan görünürlüğü.

Bu servis Faz 3 görünürlük kurallarına ek, dar kapsamlı bir görünüm sağlar.
Amaç grup başkanlarının diğer grup başkanlarının, koordinatörlerin diğer
koordinatörlerin yalnızca yayınlanmış nihai puan özetini görebilmesidir.

Güvenlik sınırı:
- Yayınlanmamış/taslak kayıt gösterilmez.
- Kriter detayı, amir görüşleri, PDF ve detay karne bu görünümde açılmaz.
- Başkan/Admin genel görünüm kuralları bu servisten bağımsız çalışmaya devam eder.
"""

from typing import Any
logger = logging.getLogger(__name__)

BYS360_PHASE3_6_PEER_PUBLISHED_SCORE_VISIBILITY_MARKER = "BYS360_PHASE3_6_PEER_PUBLISHED_SCORE_VISIBILITY"
PEER_PUBLISHED_SCOPE_VALUE = "peer_published"
PEER_PUBLISHED_SCOPE_LABEL = "Aynı seviye yayınlanan karneler"
PEER_PUBLISHED_DETAIL_DENIED_REASON = (
    "Aynı seviye görünümünde yalnızca yayınlanmış nihai puan özeti gösterilir; "
    "detay karne ve PDF açılmaz."
)

GROUP_HEAD_ROLE_ALIASES = {
    "grup_baskani", "grup_başkanı", "grup başkanı", "grup baskani",
    "group_head", "mali_musavir", "mali_müşavir", "mali musavir", "mali müşavir",
}
COORDINATOR_ROLE_ALIASES = {
    "koordinator", "koordinatör", "coordinator", "birim_sorumlusu",
    "calisma_grubu_koordinatoru", "çalışma_grubu_koordinatörü",
}


def _ascii_tr(value: str) -> str:
    return (
        value.replace("İ", "i")
        .replace("I", "i")
        .replace("ı", "i")
        .replace("Ş", "s")
        .replace("ş", "s")
        .replace("Ğ", "g")
        .replace("ğ", "g")
        .replace("Ü", "u")
        .replace("ü", "u")
        .replace("Ö", "o")
        .replace("ö", "o")
        .replace("Ç", "c")
        .replace("ç", "c")
    )


def _normalize(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = " ".join(text.replace("-", "_").split())
    return text.replace(" ", "_")


def _candidate_roles(user_or_role: Any) -> list[str]:
    if user_or_role is None:
        return []
    if isinstance(user_or_role, str):
        return [user_or_role]
    values: list[str] = []
    for attr in ("role", "role_name", "rol", "user_role", "primary_role"):
        value = getattr(user_or_role, attr, None)
        if value:
            values.append(str(value))
    roles = getattr(user_or_role, "roles", None)
    if roles:
        try:
            for role in roles:
                values.append(str(getattr(role, "name", role)))
        except TypeError:
            values.append(str(roles))
    return values


def resolve_peer_role_family(user_or_role: Any) -> str | None:
    """Return 'group_head', 'coordinator' or None."""
    for candidate in _candidate_roles(user_or_role):
        norm = _normalize(candidate)
        ascii_norm = _ascii_tr(norm)
        loose_norm = norm.replace("_", " ")
        loose_ascii = ascii_norm.replace("_", " ")
        keys = {norm, ascii_norm, loose_norm, loose_ascii}
        if keys & GROUP_HEAD_ROLE_ALIASES:
            return "group_head"
        if keys & COORDINATOR_ROLE_ALIASES:
            return "coordinator"
    return None


def is_peer_published_scope(raw_scope: Any) -> bool:
    return str(raw_scope or "").strip().lower() == PEER_PUBLISHED_SCOPE_VALUE


def _same_peer_family(user: Any, family: str | None) -> bool:
    return bool(family and resolve_peer_role_family(user) == family)


def _is_active_user(user: Any) -> bool:
    value = getattr(user, "is_active", True)
    try:
        return bool(value() if callable(value) else value)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return True


def get_peer_published_employee_ids(viewer: Any) -> list[int]:
    """Return same-level user ids for group-head/coordinator peer score view."""
    family = resolve_peer_role_family(viewer)
    if not family:
        return []
    try:
        from app.models import User
        users = User.query.all()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return []

    ids: list[int] = []
    for user in users:
        user_id = getattr(user, "id", None)
        if not user_id or not _is_active_user(user):
            continue
        if _same_peer_family(user, family):
            try:
                ids.append(int(user_id))
            except Exception:
                logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/performance/peer_published_score_visibility.py:130)")
                continue
    return sorted(set(ids))


def can_use_peer_published_scope(viewer: Any) -> bool:
    return resolve_peer_role_family(viewer) in {"group_head", "coordinator"}


def peer_published_scope_note(viewer: Any) -> str:
    family = resolve_peer_role_family(viewer)
    if family == "group_head":
        return "Grup Başkanları için yalnızca yayınlanmış nihai puan özeti gösterilir."
    if family == "coordinator":
        return "Koordinatörler için yalnızca yayınlanmış nihai puan özeti gösterilir."
    return "Bu görünüm yalnızca aynı seviye yetkili roller için kullanılır."


def decorate_surface_scope_context_for_peer_published_scores(context: dict[str, Any], *, user: Any, raw_scope: Any) -> dict[str, Any]:
    """Add/activate the same-level published score scope on scorecard surfaces."""
    if not isinstance(context, dict):
        return context
    if not can_use_peer_published_scope(user):
        return context

    options = list(context.get("scope_options") or [])
    if not any(str(row.get("value")) == PEER_PUBLISHED_SCOPE_VALUE for row in options if isinstance(row, dict)):
        options.append({
            "value": PEER_PUBLISHED_SCOPE_VALUE,
            "label": PEER_PUBLISHED_SCOPE_LABEL,
            "description": peer_published_scope_note(user),
        })
    context["scope_options"] = options
    context["scope_option_pairs"] = [(row.get("value"), row.get("label")) for row in options if isinstance(row, dict)]

    if is_peer_published_scope(raw_scope):
        peer_ids = get_peer_published_employee_ids(user)
        context.update({
            "selected_scope": PEER_PUBLISHED_SCOPE_VALUE,
            "employee_ids": peer_ids,
            "scope_label": PEER_PUBLISHED_SCOPE_LABEL,
            "scope_heading": "Aynı seviye yayınlanan karneler",
            "scope_description": peer_published_scope_note(user),
            "scope_user_count": len(peer_ids),
            "peer_published_only": True,
            "peer_published_note": peer_published_scope_note(user),
        })
    return context


def _row_is_employee_visible(row: dict[str, Any]) -> bool:
    visibility = row.get("visibility") if isinstance(row, dict) else {}
    if isinstance(visibility, dict) and visibility.get("employee_visible"):
        return True
    return bool(row.get("published"))


def decorate_scorecard_context_for_peer_published_scores(scorecard: dict[str, Any], *, viewer: Any, scope_ctx: dict[str, Any]) -> dict[str, Any]:
    """Filter scorecard rows to published same-level summary rows when peer scope is active."""
    if not isinstance(scorecard, dict) or not isinstance(scope_ctx, dict):
        return scorecard
    if not scope_ctx.get("peer_published_only"):
        return scorecard

    allowed_ids = {int(item) for item in (scope_ctx.get("employee_ids") or []) if item is not None}
    safe_rows: list[dict[str, Any]] = []
    hidden = 0

    for row in list(scorecard.get("rows") or []):
        employee = row.get("employee") if isinstance(row, dict) else None
        employee_id = getattr(employee, "id", None) or getattr(row.get("evaluation"), "employee_id", None)
        try:
            employee_id_int = int(employee_id) if employee_id is not None else None
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            employee_id_int = None

        if not employee_id_int or employee_id_int not in allowed_ids or not _row_is_employee_visible(row):
            hidden += 1
            continue
        if not _same_peer_family(employee, resolve_peer_role_family(viewer)):
            hidden += 1
            continue

        row["peer_published_only"] = True
        row["peer_published_summary_note"] = "Yalnızca yayınlanmış nihai puan özeti"
        safe_rows.append(row)

    score_values = [float(row.get("final_total") or 0.0) for row in safe_rows]
    scorecard["rows"] = safe_rows
    scorecard["count"] = len(safe_rows)
    scorecard["hidden_count"] = int(scorecard.get("hidden_count") or 0) + hidden
    scorecard["published_count"] = len(safe_rows)
    scorecard["completed_count"] = len(safe_rows)
    scorecard["low_count"] = len([value for value in score_values if value < 70])
    scorecard["high_count"] = len([value for value in score_values if value > 90])
    scorecard["avg_score"] = round(sum(score_values) / len(score_values), 2) if score_values else 0.0
    scorecard["peer_published_visibility"] = {
        "active": True,
        "label": PEER_PUBLISHED_SCOPE_LABEL,
        "note": peer_published_scope_note(viewer),
        "privacy_note": "Detay karne, PDF, amir görüşü ve kriter dökümü bu görünümde açılmaz.",
    }
    return scorecard


def enforce_peer_published_detail_visibility(visibility: dict[str, Any], *, evaluation: Any, actor: Any, scope_ctx: dict[str, Any]) -> dict[str, Any]:
    """Block detail/PDF access for peer-published scope; only list summary is allowed."""
    if not isinstance(visibility, dict) or not isinstance(scope_ctx, dict):
        return visibility
    if not scope_ctx.get("peer_published_only"):
        return visibility

    allowed_ids = {int(item) for item in (scope_ctx.get("employee_ids") or []) if item is not None}
    employee = getattr(evaluation, "employee", None)
    try:
        employee_id = int(getattr(evaluation, "employee_id", None) or 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        employee_id = 0

    visible = bool(visibility.get("employee_visible"))
    same_family = _same_peer_family(employee, resolve_peer_role_family(actor))
    if employee_id in allowed_ids and visible and same_family:
        # Liste özeti izinli, detay/PDF özellikle kapalı tutulur.
        visibility = dict(visibility)
        visibility.update({
            "can_view": False,
            "can_view_unpublished": False,
            "peer_published_summary_only": True,
            "publish_label": "Yayınlanmış Özet",
            "reason": PEER_PUBLISHED_DETAIL_DENIED_REASON,
            "reason_code": "peer_published_summary_only",
            "lock_reason": PEER_PUBLISHED_DETAIL_DENIED_REASON,
            "next_action": "Aynı seviye puanları karne listesi özetinden izleyin.",
        })
        return visibility

    visibility = dict(visibility)
    visibility.update({
        "can_view": False,
        "can_view_unpublished": False,
        "peer_published_summary_only": True,
        "reason": "Bu kayıt aynı seviye yayınlanan puan görünürlüğü kapsamında değildir.",
        "reason_code": "peer_published_not_allowed",
        "lock_reason": "Bu kayıt aynı seviye yayınlanan puan görünürlüğü kapsamında değildir.",
    })
    return visibility
