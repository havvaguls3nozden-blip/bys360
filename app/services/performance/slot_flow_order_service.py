from __future__ import annotations

from typing import Any

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


def _safe_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _role_key(value: Any) -> str:
    return _safe_str(value).lower()


def slot_map_from_row(row: dict[str, Any]) -> dict[str, str]:
    """
    Slot = kurumsal amir alanı
    manager_1 -> 1. amir
    manager_2 -> 2. amir
    manager_3 -> 3. amir
    """
    return {
        "manager_1": _safe_str(row.get("manager_1") or row.get("manager_1_name") or row.get("yonetici_sicil")),
        "manager_2": _safe_str(row.get("manager_2") or row.get("manager_2_name") or row.get("ikinci_yonetici_sicil")),
        "manager_3": _safe_str(row.get("manager_3") or row.get("manager_3_name") or row.get("ucuncu_yonetici_sicil")),
    }


def flow_order_for_row(row: dict[str, Any]) -> list[int]:
    """
    Akış sırası slot numarası değildir.
    Başkanlık: 2 -> 1
    Grup / çalışma grubu: varsa 3 -> 2 -> 1
    """
    role = _role_key(row.get("role"))
    birim = _safe_str(row.get("birim")).upper()
    ust_birim = _safe_str(row.get("ust_birim")).upper()

    if role in {"baskan", "baskan_yardimcisi"} or birim == "BAŞKANLIK" or ust_birim == "BAŞKANLIK":
        return [2, 1]

    slots = slot_map_from_row(row)
    if slots["manager_3"]:
        return [3, 2, 1]
    return [2, 1]


def build_health_issues_from_slots(row: dict[str, Any]) -> list[str]:
    """
    Sağlık kartı slot doluluğunu kontrol eder.
    Akış sırasını '1. amir yok' diye ters yorumlamaz.
    """
    slots = slot_map_from_row(row)
    role = _role_key(row.get("role"))
    birim = _safe_str(row.get("birim")).upper()
    _safe_str(row.get("ust_birim")).upper()

    # info istisnaları
    if row.get("exception_rule") in {"special_presidency_single_manager", "top_office_node_exception"}:
        return []

    # Başkanlık üst düğümleri ve özel başkanlık birimleri
    if role == "baskan":
        return []
    if birim in {"DANIŞMANLIK", "DANISMANLIK", "İÇ DENETİM", "IC DENETIM"}:
        return []  # tek amir istisnası
    if birim == "HUKUK MÜŞAVİRLİĞİ":
        # Aynı hukuk yapısında ast-üst tek amirli kayıt varsa 2. amir aramayız.
        if slots["manager_1"] and not slots["manager_2"] and not slots["manager_3"]:
            return []
        if role == "personel":
            return [] if slots["manager_1"] else ["1. amir eksik veya pasif"]

    issues: list[str] = []
    if not slots["manager_1"]:
        issues.append("1. amir eksik veya pasif")
    if not slots["manager_2"]:
        issues.append("2. amir eksik veya pasif")
    if slot_map_from_row(row)["manager_3"] and not slots["manager_3"]:
        issues.append("3. amir eksik veya pasif")
    return issues