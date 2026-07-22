from __future__ import annotations

# --- BYS360 third-manager Excel import compatibility patch ---


THIRD_MANAGER_STANDARD_KEY = "ucuncu_yonetici_sicil"
THIRD_MANAGER_HEADER_ALIASES = [
    "ucuncu_yonetici_sicil",
    "üçüncü yönetici sicil",
    "ucuncu yonetici sicil",
    "3. amir sicil",
    "3 amir sicil",
    "new_y3",
]

from dataclasses import dataclass
from typing import Any

PRESIDENCY_SINGLE_MANAGER_UNITS = {
    "DANIŞMANLIK",
    "DANISMANLIK",
    "İÇ DENETİM",
    "IC DENETIM",
}

INFO_EXCEPTION_RULES = {
    "special_presidency_single_manager",
    "top_office_node_exception",
}


def _s(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _role(value: Any) -> str:
    return _s(value).lower()


def display_name(user_like: Any) -> str:
    if user_like is None:
        return ""
    if isinstance(user_like, dict):
        full_name = _s(user_like.get("full_name"))
        if full_name:
            return full_name
        return f"{_s(user_like.get('ad'))} {_s(user_like.get('soyad'))}".strip()
    full_name = _s(getattr(user_like, "full_name", ""))
    if full_name:
        return full_name
    return f"{_s(getattr(user_like, 'ad', ''))} {_s(getattr(user_like, 'soyad', ''))}".strip()


@dataclass
class ChainSlots:
    manager_1: str = ""
    manager_2: str = ""
    manager_3: str = ""


def get_chain_slots(row: dict[str, Any]) -> ChainSlots:
    """
    Kurumsal slotlar:
    1. amir = Grup Başkanı / Başkan
    2. amir = Koordinatör / Başkan Yardımcısı
    3. amir = varsa koordinatöre bağlı birim amiri
    """
    return ChainSlots(
        manager_1=_s(row.get("manager_1") or row.get("manager_1_name") or row.get("yonetici_sicil")),
        manager_2=_s(row.get("manager_2") or row.get("manager_2_name") or row.get("ikinci_yonetici_sicil")),
        manager_3=_s(row.get("manager_3") or row.get("manager_3_name") or row.get("ucuncu_yonetici_sicil")),
    )


def get_flow_order(row: dict[str, Any]) -> list[int]:
    """
    İşlem sırası slot değildir.
    Başkanlık: 2 -> 1
    Grup / çalışma grubu: varsa 3 -> 2 -> 1, yoksa 2 -> 1
    """
    role = _role(row.get("role"))
    birim = _s(row.get("birim")).upper()
    ust_birim = _s(row.get("ust_birim")).upper()
    slots = get_chain_slots(row)

    if role == "baskan":
        return []
    if role == "baskan_yardimcisi":
        return [1]
    if birim == "BAŞKANLIK" or ust_birim == "BAŞKANLIK":
        return [2, 1]
    if slots.manager_3:
        return [3, 2, 1]
    return [2, 1]


def is_info_exception(row: dict[str, Any]) -> bool:
    rule = _s(row.get("exception_rule"))
    if rule in INFO_EXCEPTION_RULES:
        return True
    role = _role(row.get("role"))
    birim = _s(row.get("birim")).upper()
    if role == "baskan":
        return True
    if birim in PRESIDENCY_SINGLE_MANAGER_UNITS:
        return True
    if birim == "HUKUK MÜŞAVİRLİĞİ" and role == "personel":
        return True
    return False


def validate_chain_slots(row: dict[str, Any]) -> list[str]:
    """
    Slot doğrulaması:
    - 1. amir slotu dolu mu?
    - 2. amir slotu gerekli ise dolu mu?
    - 3. amir slotu yalnızca tanımlı yapılarda dikkate alınır
    """
    if is_info_exception(row):
        return []

    role = _role(row.get("role"))
    slots = get_chain_slots(row)
    issues: list[str] = []

    if not slots.manager_1:
        issues.append("1. amir eksik veya pasif")

    # Başkan yardımcısı için sadece başkan gerekir
    if role == "baskan_yardimcisi":
        return issues

    # Grup / çalışma grubu ve başkanlık seviyesinde 2. amir de zorunlu akış slotudur
    if not slots.manager_2:
        issues.append("2. amir eksik veya pasif")

    # 3. amir zorunlu değil; sadece doluysa gösterilir
    return issues


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    item = dict(row or {})
    slots = get_chain_slots(item)
    item["manager_1"] = slots.manager_1
    item["manager_2"] = slots.manager_2
    item["manager_3"] = slots.manager_3
    item["flow_order"] = get_flow_order(item)
    item["slot_issues"] = validate_chain_slots(item)

    if is_info_exception(item):
        item["effective_severity"] = "info"
        item["exception_note"] = item.get("exception_note") or "Özel tek amir / üst yönetim istisnası"
    elif item["slot_issues"]:
        item["effective_severity"] = "critical"
    elif _s(item.get("warnings")):
        item["effective_severity"] = "warning"
    else:
        item["effective_severity"] = item.get("effective_severity") or "success"

    return item


def ensure_iterable_users(value: Any) -> list[Any]:
    """
    'User' object is not iterable kırığını kapatır.
    Tek user gelirse listeye sarar, None gelirse boş döner.
    """
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]