from __future__ import annotations



from app.core.datetime_utils import utc_now
"""BYS360 canlı çekirdek kurumsal/personel route düzeltmeleri.

Bu dosyanın amacı geçici shim yönlendirmelerini kaldırıp canlıda kalacak
Birim/Pozisyon, Personel Özlük, İzin-Devamsızlık ve Kontrol Paneli
bağlantılarını gerçek ekranlara bağlamaktır.

Kapsam dışı bırakılan repository/education/strategy/portal modülleri burada
bilinçli olarak yüklenmez. Dosya savunmacıdır: eksik tablo veya eksik opsiyonel
alt route modülü uygulamayı düşürmez, güvenli ve boş veriyle çalışan ekran açar.
"""

from datetime import date, datetime, timedelta
from importlib import import_module
from types import SimpleNamespace
from typing import Any, Iterable
import csv
import io

from flask import Response, current_app, flash, jsonify, redirect, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import inspect, or_
from werkzeug.routing import BuildError

from app.extensions import db
from app.route_registry import main_bp
from app.route_support import (
    consume_form_token,
    issue_form_token,
    manager_required,
    menu_key_required,
    safe_db_rollback,
    safe_render,
)

try:  # Modeller sürümler arasında parçalı olabilir; route katmanı düşmemeli.
    from app.models import (
        AssignmentCoverageLog,
        AttendanceException,
        DelegationAssignment,
        EvaluationAssignment,
        LeaveBalance,
        PerformanceEvaluation,
        PerformancePeriod,
        PersonnelLeave,
        User,
    )
except Exception:  # pragma: no cover - eski/eksik paketlerde savunmacı mod
    AssignmentCoverageLog = None
    AttendanceException = None
    DelegationAssignment = None
    EvaluationAssignment = None
    LeaveBalance = None
    PerformanceEvaluation = None
    PerformancePeriod = None
    PersonnelLeave = None
    User = None

try:
    from app.view_helpers import build_user_scope_context
except Exception:  # pragma: no cover
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_common.py:65")
    build_user_scope_context = None

try:
    from app.services.leave_delegation_service import (
        build_leave_delegation_health_snapshot,
        build_leave_overview,
        leave_module_ready,
    )
except Exception:  # pragma: no cover
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_common.py:74")
    build_leave_delegation_health_snapshot = None
    build_leave_overview = None
    leave_module_ready = None

try:
    from app.services.ai.dashboard_panels import build_hr_attendance_ai_panel, build_hr_leave_ai_panel
except Exception:  # pragma: no cover
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_common.py:81")
    build_hr_attendance_ai_panel = None
    build_hr_leave_ai_panel = None

LEGACY_SHIM = False
LEGACY_RUNTIME_STATUS = "active_live_core_routes"
LEGACY_ROUTE_FAMILY = "institutional_core_hr_routes"
LEGACY_NOTE = (
    "Geçici fallback yönlendirmeleri kaldırıldı; birim/pozisyon, personel özlük, "
    "izin-devamsızlık ve kontrol paneli canlı çekirdek route ailesine bağlandı."
)

LEAVE_TYPE_CHOICES = [
    ("yillik_izin", "Yıllık İzin"),
    ("mazeret_izni", "Mazeret İzni"),
    ("idari_izin", "İdari İzin"),
    ("saatlik_izin", "Saatlik İzin"),
    ("hastalik_raporu", "Hastalık / Rapor"),
    ("ucretsiz_izin", "Ücretsiz İzin"),
    ("diger", "Diğer"),
]

LEAVE_STATUS_CHOICES = [
    ("onaylandi", "Onaylandı"),
    ("bekliyor", "Bekliyor"),
    ("reddedildi", "Reddedildi"),
    ("taslak", "Taslak"),
]

ATTENDANCE_TYPE_CHOICES = [
    ("devamsizlik", "Devamsızlık"),
    ("eksik_mesai", "Eksik Mesai"),
    ("gorev_disinda", "Görev Dışı"),
    ("saha_gorevi", "Saha Görevi"),
    ("uzaktan_calisma", "Uzaktan Çalışma / İstisna"),
    ("diger", "Diğer"),
]

DELEGATION_SCOPE_CHOICES = [
    ("performance", "Performans"),
    ("full", "Genel Kapsam"),
]

DELEGATION_STATUS_CHOICES = [
    ("aktif", "Aktif"),
    ("bekliyor", "Bekliyor"),
    ("iptal", "İptal"),
    ("sona_erdi", "Sona Erdi"),
]

PERFORMANCE_MODE_LABELS = {
    "exclude": "Muaf",
    "partial": "Kısmi değerlendirme",
    "informational": "Bilgi amaçlı",
}

ACTIVE_STATUSES = {"aktif", "active", "onaylandi", "approved", "tamamlandi", "kayit"}
PENDING_STATUSES = {"bekliyor", "pending", "taslak"}


def _safe_import(module_name: str) -> bool:
    """Opsiyonel canlı alt route modülünü güvenli yükler."""
    try:
        import_module(module_name)
        return True
    except Exception as exc:  # pragma: no cover - import hatası ekranda değil logda kalır
        try:
            current_app.logger.warning("Kurumsal route modülü yüklenemedi | module=%s | error=%s", module_name, exc)
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/institutional/hr_common.py)")
        return False


def _endpoint_registered(endpoint: str) -> bool:
    raw = endpoint.split(".")[-1]
    view_functions = getattr(main_bp, "view_functions", {}) or {}
    return raw in view_functions or endpoint in view_functions or f"main.{raw}" in view_functions


def _url_or_hash(endpoint: str, **values: Any) -> str:
    try:
        return url_for(endpoint, **values)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_common.py:163")
        return "#"


def _table_exists(table_name: str | None) -> bool:
    if not table_name:
        return False
    try:
        engine = db.session.get_bind()
        if engine is None:
            return False
        return str(table_name) in set(inspect(engine).get_table_names())
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_common.py:175")
        return False


def _model_ready(model: Any) -> bool:
    return bool(model is not None and _table_exists(getattr(model, "__tablename__", "")))


def _safe_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text if text else default


def _safe_int(value: Any, default: int | None = None) -> int | None:
    try:
        raw = str(value or "").strip()
        return int(raw) if raw else default
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_common.py:192")
        return default


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        raw = str(value or "").strip().replace(",", ".")
        return float(raw) if raw else default
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_common.py:200")
        return default


def _current_user_id() -> int | None:
    try:
        return int(getattr(current_user, "id", 0) or 0) or None
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_common.py:207")
        return None


def _safe_commit(success_message: str, *, danger_prefix: str = "İşlem tamamlanamadı") -> bool:
    try:
        db.session.commit()
        flash(success_message, "success")
        return True
    except Exception as exc:
        safe_db_rollback()
        current_app.logger.exception("Personel kayıt işlemi tamamlanamadı")
        flash(f"{danger_prefix}: {exc}", "danger")
        return False


def _resolve_period_id_from_form() -> int | None:
    period_id = _safe_int(request.form.get("period_id"))
    if period_id:
        return period_id
    active_period = _active_period()
    return int(getattr(active_period, "id", 0) or 0) or None


def _date_range_weekday_count(start: date, end: date) -> float:
    if end < start:
        return 0.0
    total = 0
    cursor = start
    while cursor <= end:
        if cursor.weekday() < 5:
            total += 1
        cursor += timedelta(days=1)
    return float(total)


def _calculate_leave_day_count(start: date, end: date) -> float:
    explicit = _safe_float(request.form.get("approved_day_count"))
    if explicit is not None:
        return max(0.0, round(float(explicit), 2))
    if _safe_text(request.form.get("leave_type")).lower() == "saatlik_izin":
        hours = _safe_float(request.form.get("approved_hour_count"))
        if hours is not None:
            return max(0.0, round(float(hours) / 8.0, 2))
    days = _date_range_weekday_count(start, end)
    if _bool_from_form("start_half_day"):
        days -= 0.5
    if _bool_from_form("end_half_day"):
        days -= 0.5
    closed_days = _safe_float(request.form.get("closed_day_count"), 0.0) or 0.0
    days -= closed_days
    return max(0.0, round(days, 2))


def _active_delegation_exists(delegator_user_id: int, start_date: date, end_date: date) -> bool:
    if not _model_ready(DelegationAssignment):
        return False
    try:
        return bool(
            DelegationAssignment.query.filter(
                DelegationAssignment.delegator_user_id == delegator_user_id,
                DelegationAssignment.status.in_(["aktif", "onaylandi"]),
                DelegationAssignment.start_date <= end_date,
                DelegationAssignment.end_date >= start_date,
            ).first()
        )
    except Exception:
        safe_db_rollback()
        return False


def _leave_overlaps(user_id: int, start_date: date, end_date: date) -> bool:
    if not _model_ready(PersonnelLeave):
        return False
    try:
        return bool(
            PersonnelLeave.query.filter(
                PersonnelLeave.user_id == user_id,
                PersonnelLeave.status.in_(["onaylandi", "aktif", "bekliyor", "taslak"]),
                PersonnelLeave.start_date <= end_date,
                PersonnelLeave.end_date >= start_date,
            ).first()
        )
    except Exception:
        safe_db_rollback()
        return False


def _attendance_overlaps(user_id: int, record_date: date) -> bool:
    if not _model_ready(AttendanceException):
        return False
    try:
        return bool(
            AttendanceException.query.filter(
                AttendanceException.user_id == user_id,
                AttendanceException.record_date == record_date,
                AttendanceException.status.in_(["onaylandi", "aktif", "bekliyor", "taslak"]),
            ).first()
        )
    except Exception:
        safe_db_rollback()
        return False




__all__ = [name for name in globals() if not name.startswith("__")]

# BYS360_F821_CLEANUP_SAFE_V2: HR helper fallbacks.
def _bool_from_form(name: str) -> bool:
    value = str(request.form.get(name, "") or "").strip().lower()
    return value in {"1", "true", "on", "yes", "evet", "e"}


def _active_period():
    if PerformancePeriod is None:
        return None
    try:
        return PerformancePeriod.query.filter_by(is_active=True).order_by(PerformancePeriod.id.desc()).first()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 F821 V2: aktif performans dönemi okunamadı")
        return None
# BYS360 HR AppFactory HOTFIX V1
# hr_form_helpers.py bu helper'i import eder. F821 temizliği sırasında import listesine
# eklendiği halde hr_common.py içinde bulunmadığı için create_app import aşamasında düşüyordu.
def _parse_date(value: Any) -> date | None:
    """Form alanından gelen tarihi güvenli biçimde date nesnesine çevirir.

    Desteklenen formatlar:
    - YYYY-MM-DD / ISO date
    - DD.MM.YYYY
    - DD/MM/YYYY
    - DD-MM-YYYY

    Boş, None, null veya geçersiz değerlerde None döner; handler seviyesinde
    kullanıcıya kurumsal uyarı verilmesi korunur.
    """
    if value is None:
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text or text.lower() in {"none", "null", "undefined"}:
        return None

    # HTML date input varsayılanı: 2026-06-13
    try:
        return date.fromisoformat(text[:10])
    except Exception:
        pass

    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            from datetime import datetime
            return datetime.strptime(text, fmt).date()
        except Exception:
            continue
    return None
