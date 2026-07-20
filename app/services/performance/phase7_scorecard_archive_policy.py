"""
BYS360 Performans Tamamlama Faz 7
Geçmiş Yıl Karne ve Puan Arşivi Politika Merkezi

Amaç:
- Eski yıllara ait performans puanları kurumsal arşive alınabilsin.
- Personel yalnızca kendi geçmiş performansını görebilsin.
- Yönetici yalnızca yetkili organizasyon kapsamındaki geçmiş kayıtları görebilsin.
- Başkan/Admin genel arşiv görünürlüğüne sahip olsun.
- Arşiv kaydı kaynak, yıl, dönem, puan ve açıklama bilgisiyle izlenebilir olsun.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any
from collections.abc import Iterable, Mapping

logger = logging.getLogger(__name__)


PHASE7_POLICY_MARKER = "BYS360_PERFORMANCE_COMPLETION_PHASE7_SCORECARD_ARCHIVE_POLICY"

ARCHIVE_SOURCE_MANUAL = "manual"
ARCHIVE_SOURCE_EXCEL = "excel"
ARCHIVE_SOURCE_SYSTEM = "system"

ARCHIVE_SOURCE_LABELS = {
    ARCHIVE_SOURCE_MANUAL: "Manuel Eski Puan Girişi",
    ARCHIVE_SOURCE_EXCEL: "Excel/Toplu Aktarım",
    ARCHIVE_SOURCE_SYSTEM: "Sistem Karne Kaydı",
}

ARCHIVE_VISIBILITY_LABELS = {
    "self": "Kendi Geçmiş Performansı",
    "scope": "Yetkili Kapsam Geçmişi",
    "all": "Genel Geçmiş Arşiv",
    "denied": "Erişim Yetkisi Yok",
}


@dataclass(frozen=True)
class ArchiveVisibilityDecision:
    allowed: bool
    scope: str
    label: str
    can_view_person_detail: bool
    can_view_source_document: bool
    reason: str


@dataclass(frozen=True)
class ArchiveRecordNormalized:
    employee_id: int | None
    year: int
    period_title: str
    score: float
    source_type: str
    source_label: str
    note: str
    valid: bool
    errors: tuple[str, ...]


def _to_int(value: Any, default: int | None = None) -> int | None:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _to_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace(",", "."))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _role_names(user: Any) -> set[str]:
    names: set[str] = set()
    if user is None:
        return names

    for attr in ("role", "rol", "role_name", "unvan", "title"):
        val = getattr(user, attr, None)
        if val:
            names.add(str(val).strip().lower())

    roles = getattr(user, "roles", None)
    if roles:
        try:
            for role in roles:
                for attr in ("name", "role_name", "title"):
                    val = getattr(role, attr, None)
                    if val:
                        names.add(str(val).strip().lower())
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/phase7_scorecard_archive_policy.py")
    return names


def _normalize_role_name(value: Any) -> str:
    text = str(value or "").strip().lower().replace("\u0307", "")
    return " ".join(
        text.replace("_", " ").replace("-", " ").split()
    )


def _is_admin_or_president(user: Any) -> bool:
    global_roles = {
        "admin",
        "administrator",
        "super admin",
        "system admin",
        "admin sistem yöneticisi",
        "admin sistem yoneticisi",
        "sistem yöneticisi",
        "sistem yoneticisi",
        "başkan",
        "baskan",
        "başkanlık",
        "baskanlik",
        "president",
        "başkan yardımcısı",
        "baskan yardimcisi",
    }
    return any(
        _normalize_role_name(role) in global_roles
        for role in _role_names(user)
    )


def _is_scope_manager(user: Any) -> bool:
    manager_roles = {
        "grup başkanı",
        "grup baskani",
        "koordinatör",
        "koordinator",
    }
    normalized_roles = {_normalize_role_name(role) for role in _role_names(user)}
    return any(
        role in manager_roles or role.startswith("personel ve destek")
        for role in normalized_roles
    )


def resolve_archive_visibility(
    *,
    viewer: Any,
    employee_id: Any,
    scope_employee_ids: Iterable[Any] | None = None,
    allow_source_document_for_scope: bool = False,
) -> ArchiveVisibilityDecision:
    viewer_id = _to_int(getattr(viewer, "id", None))
    target_id = _to_int(employee_id)

    if viewer_id is not None and target_id is not None and viewer_id == target_id:
        return ArchiveVisibilityDecision(
            allowed=True,
            scope="self",
            label=ARCHIVE_VISIBILITY_LABELS["self"],
            can_view_person_detail=True,
            can_view_source_document=False,
            reason="Personel kendi geçmiş performans kaydını görüntüleyebilir.",
        )

    if _is_admin_or_president(viewer):
        return ArchiveVisibilityDecision(
            allowed=True,
            scope="all",
            label=ARCHIVE_VISIBILITY_LABELS["all"],
            can_view_person_detail=True,
            can_view_source_document=True,
            reason="Başkan/Admin genel geçmiş arşiv kapsamına sahiptir.",
        )

    scope_ids = {_to_int(x) for x in (scope_employee_ids or [])}
    if _is_scope_manager(viewer) and target_id in scope_ids:
        return ArchiveVisibilityDecision(
            allowed=True,
            scope="scope",
            label=ARCHIVE_VISIBILITY_LABELS["scope"],
            can_view_person_detail=True,
            can_view_source_document=bool(allow_source_document_for_scope),
            reason="Yönetici yalnızca yetkili organizasyon kapsamındaki geçmiş kaydı görüntüleyebilir.",
        )

    return ArchiveVisibilityDecision(
        allowed=False,
        scope="denied",
        label=ARCHIVE_VISIBILITY_LABELS["denied"],
        can_view_person_detail=False,
        can_view_source_document=False,
        reason="Bu geçmiş performans kaydına erişim yetkiniz bulunmamaktadır.",
    )


def normalize_archive_source(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"excel", "xlsx", "import", "toplu", "aktarim", "aktarım"}:
        return ARCHIVE_SOURCE_EXCEL
    if raw in {"system", "sistem", "scorecard", "karne"}:
        return ARCHIVE_SOURCE_SYSTEM
    return ARCHIVE_SOURCE_MANUAL


def normalize_archive_record(row: Mapping[str, Any]) -> ArchiveRecordNormalized:
    errors: list[str] = []

    employee_id = _to_int(row.get("employee_id") or row.get("personel_id") or row.get("user_id"))
    if employee_id is None:
        errors.append("Personel bilgisi eksik.")

    year = _to_int(row.get("year") or row.get("yil") or row.get("calendar_year"))
    current_year = date.today().year
    if year is None:
        errors.append("Yıl bilgisi eksik.")
        year = current_year
    elif year < 2000 or year > current_year + 1:
        errors.append("Yıl bilgisi geçerli aralıkta değil.")

    period_title = str(row.get("period_title") or row.get("period") or row.get("donem") or f"{year} Performans Dönemi").strip()
    if not period_title:
        errors.append("Dönem başlığı eksik.")

    score = _to_float(row.get("score") or row.get("final_score") or row.get("puan"))
    if score is None:
        errors.append("Puan bilgisi eksik.")
        score = 0.0
    elif score < 0 or score > 100:
        errors.append("Puan 0-100 aralığında olmalıdır.")

    source_type = normalize_archive_source(row.get("source_type") or row.get("kaynak"))
    note = str(row.get("note") or row.get("aciklama") or row.get("description") or "").strip()

    return ArchiveRecordNormalized(
        employee_id=employee_id,
        year=int(year),
        period_title=period_title,
        score=float(score),
        source_type=source_type,
        source_label=ARCHIVE_SOURCE_LABELS[source_type],
        note=note,
        valid=not errors,
        errors=tuple(errors),
    )


def sanitize_archive_import_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    normalized: list[ArchiveRecordNormalized] = []
    valid_count = 0
    error_count = 0

    for row in rows or []:
        item = normalize_archive_record(row)
        normalized.append(item)
        if item.valid:
            valid_count += 1
        else:
            error_count += 1

    return {
        "rows": normalized,
        "total": len(normalized),
        "valid_count": valid_count,
        "error_count": error_count,
        "ready_for_import": error_count == 0,
    }


def archive_score_band(score: Any) -> str:
    numeric = _to_float(score, 0.0) or 0.0
    if numeric < 70:
        return "Düşük Performans"
    if numeric >= 90:
        return "Çok Başarılı"
    return "Beklenen Düzey"


def build_archive_summary(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    scores: list[float] = []
    years: set[int] = set()
    low_count = 0
    high_count = 0

    for row in rows or []:
        score = _to_float(row.get("score") or row.get("final_score") or row.get("puan"))
        year = _to_int(row.get("year") or row.get("yil") or row.get("calendar_year"))
        if score is not None:
            scores.append(score)
            if score < 70:
                low_count += 1
            if score >= 90:
                high_count += 1
        if year is not None:
            years.add(year)

    avg = round(sum(scores) / len(scores), 2) if scores else None
    return {
        "total_records": len(scores),
        "average_score": avg,
        "year_count": len(years),
        "low_score_count": low_count,
        "high_score_count": high_count,
    }


def phase7_archive_contract() -> dict[str, Any]:
    return {
        "historical_score_archive": True,
        "manual_old_score_entry": True,
        "excel_import_supported": True,
        "personnel_self_history_only": True,
        "manager_scope_limited_history": True,
        "president_admin_full_archive": True,
        "source_document_tracking": True,
        "archive_summary_without_leaking_person_details": True,
        "phase_marker": PHASE7_POLICY_MARKER,
    }

# BYS360_PERFORMANCE_COMPLETION_PHASE7_SCORECARD_ARCHIVE_BOUND
# Geçmiş yıl karne/puan arşivi phase7_scorecard_archive_policy sözleşmesini kullanır.
