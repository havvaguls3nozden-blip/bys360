from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

"""BYS360 özel kapsam dönemlerinde puanlanacak personel ile değerlendirici amiri ayırır.

Bu servis özellikle birime özel, kategori/grup özel ve seçili personele özel dönemlerde
şu ayrımı garanti eder:

1. Puanlanacak personel: dönem kapsamında gerçekten değerlendirilecek çalışanlar.
2. Değerlendirici amir: yalnızca zincirde görev alacak kişiler.

Genel/Tüm Kurum döneminde mevcut davranışa dokunulmaz.
Özel kapsamlı dönemlerde amirler yalnızca görev sahibi olarak kalır; açıkça seçili
personel kapsamına yazılmadıkça puanlanacak kişi listesine girmez.
"""

logger = logging.getLogger(__name__)

BYS360_SELECTED_SCOPE_ASSESSOR_FIX_MARKER = "BYS360_PERFORMANCE_SELECTED_SCOPE_ASSESSOR_FIX_V2"

try:
    from app.services.performance.period_scope_contract import (
        SCOPE_ALL,
        SCOPE_SELECTED_PERSONNEL,
        normalize_period_scope_type,
    )
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    SCOPE_ALL = "all"
    SCOPE_SELECTED_PERSONNEL = "selected_personnel"

    def normalize_period_scope_type(value: object) -> str:
        raw = str(value or "").strip().lower().replace("-", "_")
        aliases = {
            "": "all",
            "all": "all",
            "tum_kurum": "all",
            "tüm kurum": "all",
            "selected_personnel": "selected_personnel",
            "seçili personel": "selected_personnel",
            "secilmis_personel": "selected_personnel",
        }
        return aliases.get(raw, raw or "all")

try:
    from app.services.performance.period_scope_assignment import (
        employee_identity_tokens,
        split_selected_personnel_filter,
    )
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    def employee_identity_tokens(employee: Any) -> set[str]:
        values = {
            getattr(employee, "id", None),
            getattr(employee, "sicil_no", None),
            getattr(employee, "email", None),
            getattr(employee, "full_name", None),
            f"{getattr(employee, 'ad', '') or ''} {getattr(employee, 'soyad', '') or ''}",
        }
        return {str(v).strip().lower() for v in values if str(v or "").strip()}

    def split_selected_personnel_filter(value: object) -> set[str]:
        import re
        return {item.strip().lower() for item in re.split(r"[\n,;|]+", str(value or "")) if item.strip()}


def _safe_int(value: object) -> int | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(value)  # type: ignore[call-overload]  # defensive parse; TypeError/ValueError caught below
    except (TypeError, ValueError):
        return None


def _norm(value: object) -> str:
    return str(value or "").strip().lower()


def _period_scope_type(period: Any) -> str:
    return normalize_period_scope_type(getattr(period, "scope_type", None) or "all")


def is_specific_period_scope(period: Any) -> bool:
    """Tüm kurum dışındaki dönem kapsamlarında True döner."""
    return _period_scope_type(period) != SCOPE_ALL


def explicitly_selected_employee_ids(period: Any, employees: Iterable[Any]) -> set[int]:
    """Seçili personel kapsamında açıkça seçilen personel ID'lerini döndürür."""
    if _period_scope_type(period) != SCOPE_SELECTED_PERSONNEL:
        return set()
    selected_tokens = split_selected_personnel_filter(getattr(period, "scope_personnel_filter", None))
    if not selected_tokens:
        return set()
    explicit: set[int] = set()
    for employee in list(employees or []):
        employee_id = _safe_int(getattr(employee, "id", None))
        if employee_id is None:
            continue
        if employee_identity_tokens(employee).intersection(selected_tokens):
            explicit.add(employee_id)
    return explicit


def _manager_ids_for_employee(employee: Any, period: Any) -> set[int]:
    """Bir personelin V2 çözülmüş zincirindeki amir ID'lerini güvenli şekilde bulur."""
    manager_ids: set[int] = set()
    try:
        from app.services.performance_v2.chain import build_resolved_chain
        resolved = build_resolved_chain(employee=employee, period=period)
        for payload in getattr(resolved, "levels", {}).values():
            manager_id = _safe_int(getattr(payload, "evaluator_id", None))
            if manager_id:
                manager_ids.add(manager_id)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            from app.services.performance.hierarchy import build_manager_chain_for_user
            chain = build_manager_chain_for_user(employee=employee, period=period)
            for attr in ("manager_1_id", "manager_2_id", "manager_3_id"):
                manager_id = _safe_int(getattr(chain, attr, None))
                if manager_id:
                    manager_ids.add(manager_id)
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            return set()
    return manager_ids


def _looks_like_assessor_role(employee: Any) -> bool:
    """Özel dönemlerde amir rolünde olan kişileri puanlanacak listeden korur."""
    fields = [
        getattr(employee, "role", None),
        getattr(employee, "role_label", None),
        getattr(employee, "unvan", None),
        getattr(employee, "gorev", None),
        getattr(employee, "görev", None),
    ]
    text = " ".join(_norm(item) for item in fields if _norm(item))
    assessor_tokens = (
        "başkan",
        "baskan",
        "başkan yardımcısı",
        "baskan yardimcisi",
        "grup başkanı",
        "grup baskani",
        "koordinatör",
        "koordinator",
        "müdür",
        "mudur",
        "amir",
        "sorumlu",
        "hukuk müşaviri",
        "hukuk musaviri",
        "iç denetçi",
        "ic denetci",
        "özel kalem",
        "ozel kalem",
    )
    return any(token in text for token in assessor_tokens)


def split_scored_employees_from_assessor_only(period: Any, employees: Iterable[Any]) -> tuple[list[Any], list[Any]]:
    """Puanlanacak personel listesinden yalnızca değerlendirici olarak gelen amirleri ayırır.

    Kapsam ``Tüm Kurum`` ise mevcut genel puanlama davranışı korunur ve listeye
    müdahale edilmez. Özel kapsamlarda ise hem çözülmüş zincirde amir olanlar hem
    de yönetici/amiri belirten rol-unvanlar puanlanacak listeden ayrılır. Seçili
    personel döneminde kişi açıkça yazıldıysa puanlanabilir; bu bilinçli seçimdir.
    """
    employee_list = list(employees or [])
    if not employee_list or not is_specific_period_scope(period):
        return employee_list, []

    explicit_ids = explicitly_selected_employee_ids(period, employee_list)
    selected_personnel_scope = _period_scope_type(period) == SCOPE_SELECTED_PERSONNEL

    assessor_ids: set[int] = set()
    for employee in employee_list:
        assessor_ids.update(_manager_ids_for_employee(employee, period))

    scored: list[Any] = []
    assessor_only: list[Any] = []
    for employee in employee_list:
        employee_id = _safe_int(getattr(employee, "id", None))
        explicit_selected = bool(employee_id and employee_id in explicit_ids)
        is_assessor = bool(employee_id and employee_id in assessor_ids) or _looks_like_assessor_role(employee)

        # Seçili personel döneminde kullanıcı amiri bilerek seçtiyse puanlanabilir.
        # Birim/kategori/özel grup dönemlerinde amirler açıkça hedef değil, görev sahibidir.
        if is_assessor and not (selected_personnel_scope and explicit_selected):
            assessor_only.append(employee)
        else:
            scored.append(employee)
    return scored, assessor_only


def assessor_only_exclusion_note(employee: Any) -> str:
    name = (
        getattr(employee, "full_name", None)
        or f"{getattr(employee, 'ad', '') or ''} {getattr(employee, 'soyad', '') or ''}".strip()
        or "Amir"
    )
    return f"{name} bu özel dönem kapsamında yalnızca değerlendirici amir olarak tutuldu; puanlanacak personel listesine eklenmedi."


__all__ = [
    "BYS360_SELECTED_SCOPE_ASSESSOR_FIX_MARKER",
    "is_specific_period_scope",
    "explicitly_selected_employee_ids",
    "split_scored_employees_from_assessor_only",
    "assessor_only_exclusion_note",
]
