from __future__ import annotations

import logging
import re
import unicodedata
from collections.abc import Iterable, Sequence

"""BYS360 Faz 8.4 — dönem kapsamına göre görev üretimi filtresi.

Bu servis görev üretimi sırasında hangi personelin ilgili performans dönemine
ait olduğunu belirler. Kural güvenli varsayımla çalışır: kapsam özel ise hedef
bilgi yoksa personel kapsam dışı kabul edilir; boş yönetici/kategori kapsamı
hiçbir zaman tüm kurum anlamına gelmez.
"""

logger = logging.getLogger(__name__)

TR_ASCII_MAP = str.maketrans({
    "ç": "c", "Ç": "c",
    "ğ": "g", "Ğ": "g",
    "ı": "i", "İ": "i", "I": "i",
    "ö": "o", "Ö": "o",
    "ş": "s", "Ş": "s",
    "ü": "u", "Ü": "u",
})

try:  # Faz 8.2 sözleşmesi varsa onu kullan.
    from app.services.performance.period_scope_contract import (
        SCOPE_ALL,
        SCOPE_CATEGORY,
        SCOPE_SELECTED_PERSONNEL,
        SCOPE_UNIT,
        SCOPE_UPPER_UNIT,
        get_period_scope_label,
        normalize_period_scope_type,
    )
except Exception:  # pragma: no cover - eski paket güvenliği
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    SCOPE_ALL = "all"
    SCOPE_UNIT = "unit"
    SCOPE_UPPER_UNIT = "upper_unit"
    SCOPE_CATEGORY = "category"
    SCOPE_SELECTED_PERSONNEL = "selected_personnel"

    def normalize_period_scope_type(value: object) -> str:
        raw = str(value or "").strip().lower().replace("-", "_")
        aliases = {
            "": SCOPE_ALL,
            "all": SCOPE_ALL,
            "tum_kurum": SCOPE_ALL,
            "tüm kurum": SCOPE_ALL,
            "unit": SCOPE_UNIT,
            "birim": SCOPE_UNIT,
            "upper_unit": SCOPE_UPPER_UNIT,
            "ust_birim": SCOPE_UPPER_UNIT,
            "üst_birim": SCOPE_UPPER_UNIT,
            "category": SCOPE_CATEGORY,
            "kategori": SCOPE_CATEGORY,
            "selected_personnel": SCOPE_SELECTED_PERSONNEL,
            "seçili personel": SCOPE_SELECTED_PERSONNEL,
            "secilmis_personel": SCOPE_SELECTED_PERSONNEL,
        }
        return aliases.get(raw, SCOPE_ALL)

    def get_period_scope_label(value: object) -> str:
        return {
            SCOPE_ALL: "Tüm Kurum",
            SCOPE_UNIT: "Birim",
            SCOPE_UPPER_UNIT: "Üst Birim",
            SCOPE_CATEGORY: "Kategori",
            SCOPE_SELECTED_PERSONNEL: "Seçili Personel",
        }.get(normalize_period_scope_type(value), "Tüm Kurum")

try:  # Faz 8.3 özel senaryo varsayılanları varsa onları da uygula.
    from app.services.performance.period_special_scenario_contract import (
        build_special_scenario_defaults,
        get_special_period_scenario_label,
        normalize_special_period_scenario,
    )
except Exception:  # pragma: no cover - eski paket güvenliği
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    def normalize_special_period_scenario(value: object) -> str:
        return str(value or "").strip()

    def get_special_period_scenario_label(value: object) -> str:
        return str(value or "").strip() or "Senaryo seçmeyin"

    def build_special_scenario_defaults(value: object) -> dict[str, str]:
        return {}


def _safe_text(value: object) -> str:
    return str(value or "").strip()


def normalize_match_text(value: object) -> str:
    """Türkçe karakterleri ve boşlukları normalize ederek güvenli eşleşme anahtarı üretir."""
    text = _safe_text(value)
    if not text:
        return ""
    translated = text.translate(TR_ASCII_MAP)
    folded = unicodedata.normalize("NFKD", translated)
    plain = "".join(ch for ch in folded if not unicodedata.combining(ch))
    plain = plain.replace("–", "-").replace("—", "-").replace("_", " ")
    plain = re.sub(r"[^a-zA-Z0-9@.\-\s]", " ", plain)
    return " ".join(plain.lower().split())


def split_selected_personnel_filter(value: object) -> set[str]:
    raw = _safe_text(value)
    if not raw:
        return set()
    parts = re.split(r"[\n,;|]+", raw)
    tokens: set[str] = set()
    for part in parts:
        item = normalize_match_text(part)
        if item:
            tokens.add(item)
    return tokens


def _employee_full_name(employee) -> str:
    cached = _safe_text(getattr(employee, "full_name", None))
    if cached:
        return cached
    cached = _safe_text(getattr(employee, "full_name_cache", None))
    if cached:
        return cached
    return " ".join(part for part in (_safe_text(getattr(employee, "ad", None)), _safe_text(getattr(employee, "soyad", None))) if part)


def employee_identity_tokens(employee) -> set[str]:
    values = {
        getattr(employee, "id", None),
        getattr(employee, "sicil_no", None),
        getattr(employee, "email", None),
        _employee_full_name(employee),
        f"{_safe_text(getattr(employee, 'ad', None))} {_safe_text(getattr(employee, 'soyad', None))}",
    }
    return {normalize_match_text(value) for value in values if normalize_match_text(value)}


def employee_category_tokens(employee) -> set[str]:
    values = {
        getattr(employee, "personnel_category", None),
        getattr(employee, "kategori", None),
        getattr(employee, "category", None),
        getattr(employee, "personel_kategori", None),
    }
    category_obj = getattr(employee, "performance_category", None)
    for attr in ("name", "title", "label", "category_name"):
        values.add(getattr(category_obj, attr, None))
    return {normalize_match_text(value) for value in values if normalize_match_text(value)}


def employee_unit_tokens(employee) -> set[str]:
    org = getattr(employee, "organization_unit", None)
    values = {
        getattr(employee, "birim", None),
        getattr(org, "name", None),
        getattr(org, "title", None),
        getattr(org, "unit_name", None),
    }
    return {normalize_match_text(value) for value in values if normalize_match_text(value)}

def _matches_scope_token(target: object, tokens: set[str]) -> bool:
    """Kapsam etiketi ile personel etiketini güvenli/esnek eşleştirir.

    Kurumda aynı birim farklı listelerde "Bilgi Teknolojileri",
    "Bilgi Teknolojileri Çalışma Grubu" gibi geçebildiği için yalnızca
    bire bir eşleşmeye bağlı kalmayız. Kısa ve boş değerler tüm kuruma
    yayılmasın diye en az 4 karakter koşulu korunur.
    """
    needle = normalize_match_text(target)
    if not needle:
        return False
    for token in tokens or set():
        token_text = normalize_match_text(token)
        if not token_text:
            continue
        if needle == token_text:
            return True
        if len(needle) >= 4 and len(token_text) >= 4 and (needle in token_text or token_text in needle):
            return True
    return False


def employee_upper_unit_tokens(employee) -> set[str]:
    org = getattr(employee, "organization_unit", None)
    parent = getattr(org, "parent", None)
    values = {
        getattr(employee, "ust_birim", None),
        getattr(employee, "üst_birim", None),
        getattr(org, "parent_name", None),
        getattr(parent, "name", None),
        getattr(parent, "title", None),
    }
    return {normalize_match_text(value) for value in values if normalize_match_text(value)}


def _effective_period_scope(period) -> dict[str, object]:
    scenario = normalize_special_period_scenario(getattr(period, "special_scenario_type", None))
    defaults = build_special_scenario_defaults(scenario) if scenario else {}

    raw_scope = getattr(period, "scope_type", None)
    scope_type = normalize_period_scope_type(raw_scope)
    if defaults.get("scope_type") and (not _safe_text(raw_scope) or scope_type == SCOPE_ALL):
        scope_type = normalize_period_scope_type(defaults.get("scope_type"))

    category_label = _safe_text(getattr(period, "scope_category_label", None)) or _safe_text(defaults.get("scope_category_label"))
    unit_label = _safe_text(getattr(period, "scope_unit_label", None)) or _safe_text(defaults.get("scope_unit_label"))
    selected_filter = _safe_text(getattr(period, "scope_personnel_filter", None)) or _safe_text(defaults.get("scope_personnel_filter"))

    return {
        "scope_type": scope_type,
        "scope_label": get_period_scope_label(scope_type),
        "scope_unit_label": unit_label,
        "scope_category_label": category_label,
        "scope_personnel_filter": selected_filter,
        "special_scenario_type": scenario,
        "special_scenario_label": get_special_period_scenario_label(scenario) if scenario else "",
    }


def employee_matches_period_scope(employee, period) -> bool:
    scope = _effective_period_scope(period)
    scope_type = str(scope.get("scope_type") or SCOPE_ALL)

    if scope_type == SCOPE_ALL:
        return True

    if scope_type == SCOPE_UNIT:
        return _matches_scope_token(scope.get("scope_unit_label"), employee_unit_tokens(employee))

    if scope_type == SCOPE_UPPER_UNIT:
        return _matches_scope_token(scope.get("scope_unit_label"), employee_upper_unit_tokens(employee))

    if scope_type == SCOPE_CATEGORY:
        return _matches_scope_token(scope.get("scope_category_label"), employee_category_tokens(employee))

    if scope_type == SCOPE_SELECTED_PERSONNEL:
        selected = split_selected_personnel_filter(scope.get("scope_personnel_filter"))
        identities = employee_identity_tokens(employee)
        return bool(selected and identities.intersection(selected))

    return False


def filter_period_scope_employees(employees: Iterable[object], period) -> list[object]:
    return [employee for employee in list(employees or []) if employee_matches_period_scope(employee, period)]


def period_scope_employee_ids(employees: Iterable[object], period) -> set[int]:
    ids: set[int] = set()
    for employee in filter_period_scope_employees(employees, period):
        raw_id = getattr(employee, "id", None)
        if raw_id is None:
            continue
        try:
            ids.add(int(raw_id))
        except (TypeError, ValueError):
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/performance/period_scope_assignment.py:235)")
            continue
    return ids


def build_period_scope_generation_payload(period, all_employees: Sequence[object], matched_employees: Sequence[object]) -> dict[str, object]:
    scope = _effective_period_scope(period)
    all_count = len(list(all_employees or []))
    matched_count = len(list(matched_employees or []))
    payload = dict(scope)
    payload.update({
        "all_candidate_count": all_count,
        "matched_count": matched_count,
        "out_of_scope_count": max(all_count - matched_count, 0),
        "matched_employee_ids": [getattr(employee, "id", None) for employee in matched_employees or []],
    })
    return payload


def deactivate_out_of_scope_assignments_for_period(period, allowed_employee_ids: set[int], *, run_key: str | None = None, actor_user_id: int | None = None) -> int:
    """Kapsam dışı aktif görevleri pasifleştirir.

    Faz 8.4 güvenlik ilkesi: dönem kapsamı daraldığında önceki geniş kapsamdan
    kalan bekleyen görevler görünmeye/devam etmeyecek. Tamamlanmış kayıtlar
    denetim izi için silinmez.
    """
    if period is None or getattr(period, "id", None) is None:
        return 0

    from app.extensions import db
    from app.models import AssignmentCoverageLog, EvaluationAssignment

    query = EvaluationAssignment.query.filter(EvaluationAssignment.period_id == period.id)
    if allowed_employee_ids:
        query = query.filter(~EvaluationAssignment.employee_id.in_(list(allowed_employee_ids)))

    changed = 0
    for assignment in query.all():
        if getattr(assignment, "completed_at", None):
            continue
        if getattr(assignment, "status", None) != "kapsam_disi":
            assignment.status = "kapsam_disi"
            assignment.coverage_note = "Dönem kapsamı dışında kaldığı için görev pasifleştirildi."
            db.session.add(assignment)
            changed += 1
            try:
                db.session.add(AssignmentCoverageLog(
                    period_id=period.id,
                    employee_id=assignment.employee_id,
                    manager_level=getattr(assignment, "manager_level", None),
                    event_scope="generation",
                    event_type="cleared",
                    severity="info",
                    reason="Dönem kapsamı dışında kaldığı için görev pasifleştirildi.",
                    run_key=run_key,
                    created_by_user_id=actor_user_id,
                ))
            except Exception:
                logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
                import logging
                logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/period_scope_assignment.py")
    return changed


__all__ = [
    "normalize_match_text",
    "_matches_scope_token",
    "split_selected_personnel_filter",
    "employee_identity_tokens",
    "employee_category_tokens",
    "employee_unit_tokens",
    "employee_upper_unit_tokens",
    "employee_matches_period_scope",
    "filter_period_scope_employees",
    "period_scope_employee_ids",
    "build_period_scope_generation_payload",
    "deactivate_out_of_scope_assignments_for_period",
]

# BYS360_PERFORMANCE_COMPLETION_PHASE8_PERIOD_SCOPE_BOUND
# Çoklu dönem ve kapsamlı görev üretimi phase8_period_scope_policy sözleşmesini kullanır.
