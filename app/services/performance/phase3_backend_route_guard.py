from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from flask import current_app, render_template

from app.models import PerformanceEvaluation, User

"""BYS360 Faz 3.3 — Backend route görünürlük/kapsam kilidi.

Menü görünürlüğü kullanıcı deneyimi içindir; gerçek veri koruması route ve
query seviyesinde burada yapılır. Bu servis, URL elle yazılsa bile kapsam dışı
performans verisinin dönmemesini sağlar.
"""

logger = logging.getLogger(__name__)

try:  # Faz 3.1 rol matrisi ana kaynak.
    from app.services.performance.phase3_role_matrix import (
        PHASE3_ACCESS_DENIED_MESSAGE,
        phase3_can_view_general,
        phase3_requires_own_record_only,
        phase3_requires_scope_filter,
        resolve_phase3_role_key,
    )
except Exception:  # pragma: no cover - overlay sırası bozulursa güvenli fallback.
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    PHASE3_ACCESS_DENIED_MESSAGE = "Bu sayfaya erişim yetkiniz bulunmamaktadır."

    def resolve_phase3_role_key(user_or_role: Any) -> str:
        role = str(getattr(user_or_role, "role", user_or_role) or "").strip().lower()
        if role in {"admin", "sistem_yoneticisi", "system_admin", "super_admin"}:
            return "admin_sistem_yoneticisi"
        if role in {"baskan", "başkan", "baskan_yardimcisi", "başkan_yardımcısı"}:
            return "baskan"
        if role in {"grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir"}:
            return "grup_baskani"
        if role in {"koordinator", "koordinatör", "birim_sorumlusu"}:
            return "koordinator"
        return "personel"

    def phase3_can_view_general(user_or_role: Any) -> bool:
        return resolve_phase3_role_key(user_or_role) in {"baskan", "admin_sistem_yoneticisi"}

    def phase3_requires_own_record_only(user_or_role: Any) -> bool:
        return resolve_phase3_role_key(user_or_role) == "personel"

    def phase3_requires_scope_filter(user_or_role: Any) -> bool:
        return resolve_phase3_role_key(user_or_role) in {"koordinator", "grup_baskani"}

BYS360_PHASE3_3_BACKEND_ROUTE_CONTROL_VERSION = "2026-05-01.phase3.3.backend-route.v1"
BYS360_PHASE3_3_BACKEND_ROUTE_CONTROL_MARKER = "BYS360_PHASE3_3_BACKEND_ROUTE_CONTROL"
BYS360_PHASE3_4_CORPORATE_ACCESS_DENIED_MARKER = "BYS360_PHASE3_4_CORPORATE_ACCESS_DENIED_BACKEND_GUARD"


def _safe_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_ids(rows: Iterable[Any]) -> set[int]:
    ids: set[int] = set()
    for row in rows or []:
        value = _safe_int(getattr(row, "id", row))
        if value is not None:
            ids.add(value)
    return ids


def phase3_denied_response(message: str | None = None, *, status_code: int = 403):
    """Yetkisiz backend erişiminde ham hata/beyaz ekran yerine güvenli çıktı döndürür.

    Faz 3.4 kurumsal erişim sayfası bu şablonu daha da geliştirecek. Bu fazda
    bile route beyaz ekrana düşmesin diye aynı kurumsal cümleyle güvenli fallback
    verilir.
    """
    safe_message = (message or PHASE3_ACCESS_DENIED_MESSAGE or "Bu sayfaya erişim yetkiniz bulunmamaktadır.").strip()
    try:
        return render_template(
            "errors/403.html",
            title="Erişim Yetkisi Bulunmamaktadır",
            message=safe_message,
        ), status_code
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return (
            f"""
            <html>
              <head><title>403 - Erişim Yetkisi Bulunmamaktadır</title></head>
              <body style="font-family:Arial,sans-serif;background:#f7f7f7;padding:40px;color:#222;">
                <main style="max-width:760px;margin:auto;background:#fff;border-radius:18px;padding:32px;box-shadow:0 12px 36px rgba(0,0,0,.08);">
                  <h2 style="color:#8B0000;margin-top:0;">Erişim Yetkisi Bulunmamaktadır</h2>
                  <p>{safe_message}</p>
                </main>
              </body>
            </html>
            """,
            status_code,
        )


def phase3_allowed_employee_ids(user: Any) -> set[int]:
    """Kullanıcının backend route düzeyinde görebileceği personel id seti.

    Kritik kural: boş set hiçbir zaman "herkes" anlamına gelmez. Query tarafında
    boş set güvenli biçimde `id == -1` filtresine çevrilmelidir.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return set()

    user_id = _safe_int(getattr(user, "id", None))
    role_key = resolve_phase3_role_key(user)

    if phase3_can_view_general(user):
        try:
            return _extract_ids(User.query.filter(User.role != "admin").with_entities(User.id).all())
        except Exception as exc:  # pragma: no cover
            current_app.logger.warning("Faz 3.3 genel kapsam id üretimi başarısız: %s", exc)
            return set()

    if phase3_requires_own_record_only(user):
        return {user_id} if user_id is not None else set()

    if phase3_requires_scope_filter(user):
        try:
            # Mevcut projedeki kapsam helper'ı; koordinatör/grup başkanı için merkezi kapsamı üretir.
            from app.view_helpers import build_surface_scope_context

            scope_ctx = build_surface_scope_context(user, None)
            ids = {_safe_int(value) for value in (scope_ctx.get("employee_ids") or [])}
            return {value for value in ids if value is not None}
        except Exception as exc:  # pragma: no cover
            current_app.logger.warning("Faz 3.3 kapsam id üretimi başarısız | role=%s | exc=%s", role_key, exc)
            return {user_id} if user_id is not None else set()

    return {user_id} if user_id is not None else set()


def phase3_can_view_employee(user: Any, employee_id: Any) -> bool:
    employee_id_int = _safe_int(employee_id)
    if employee_id_int is None:
        return False
    return employee_id_int in phase3_allowed_employee_ids(user)


def phase3_can_view_evaluation(user: Any, evaluation: Any) -> bool:
    if not evaluation:
        return False
    return phase3_can_view_employee(user, getattr(evaluation, "employee_id", None))


def phase3_enforce_evaluation_access(user: Any, evaluation: Any):
    """Route içinde doğrudan kullanılacak kısa kilit."""
    if phase3_can_view_evaluation(user, evaluation):
        return None
    return phase3_denied_response(PHASE3_ACCESS_DENIED_MESSAGE)


def phase3_filter_evaluation_query(query, user: Any):
    allowed_ids = phase3_allowed_employee_ids(user)
    if not allowed_ids:
        return query.filter(PerformanceEvaluation.id == -1)
    return query.filter(PerformanceEvaluation.employee_id.in_(allowed_ids))


def phase3_filter_user_query(query, user: Any):
    allowed_ids = phase3_allowed_employee_ids(user)
    if not allowed_ids:
        return query.filter(User.id == -1)
    return query.filter(User.id.in_(allowed_ids))


def phase3_can_open_performance_reports(user: Any) -> bool:
    """Personel rapor detayına giremez; yönetici ve genel görünüm rolleri girebilir."""
    role_key = resolve_phase3_role_key(user)
    return role_key in {"koordinator", "grup_baskani", "baskan", "admin_sistem_yoneticisi"}

# ---------------------------------------------------------------------------
# BYS360 Performans Tamamlama Faz 3 — merkezi görünürlük delegasyonu
# Menü görünürlüğü tek başına güvenlik değildir; backend route/query kapsamı
# completion_phase3_visibility_scope servisine bağlanır.
# ---------------------------------------------------------------------------
try:  # BYS360_PERFORMANCE_COMPLETION_PHASE3_BACKEND_GUARD_DELEGATION_IMPORT
    from app.services.performance.completion_phase3_visibility_scope import (
        phase3_allowed_employee_ids as _bys360_completion_phase3_allowed_employee_ids,
        phase3_can_open_performance_reports as _bys360_completion_phase3_can_open_performance_reports,
        phase3_can_view_employee as _bys360_completion_phase3_can_view_employee,
        phase3_can_view_evaluation as _bys360_completion_phase3_can_view_evaluation,
        phase3_denied_response as _bys360_completion_phase3_denied_response,
        phase3_enforce_evaluation_access as _bys360_completion_phase3_enforce_evaluation_access,
        phase3_filter_evaluation_query as _bys360_completion_phase3_filter_evaluation_query,
        phase3_filter_user_query as _bys360_completion_phase3_filter_user_query,
    )

    phase3_allowed_employee_ids = _bys360_completion_phase3_allowed_employee_ids
    phase3_can_open_performance_reports = _bys360_completion_phase3_can_open_performance_reports
    phase3_can_view_employee = _bys360_completion_phase3_can_view_employee
    phase3_can_view_evaluation = _bys360_completion_phase3_can_view_evaluation
    phase3_denied_response = _bys360_completion_phase3_denied_response
    phase3_enforce_evaluation_access = _bys360_completion_phase3_enforce_evaluation_access
    phase3_filter_evaluation_query = _bys360_completion_phase3_filter_evaluation_query
    phase3_filter_user_query = _bys360_completion_phase3_filter_user_query
    BYS360_PERFORMANCE_COMPLETION_PHASE3_BACKEND_GUARD_DELEGATED = True
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    BYS360_PERFORMANCE_COMPLETION_PHASE3_BACKEND_GUARD_DELEGATED = False

