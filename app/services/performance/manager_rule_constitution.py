
"""BYS360 Performans Amir Kuralları Anayasası.

Bu dosya canlı davranış değiştirmez. Performans modülündeki amir zinciri,
görünürlük, yayın, açıklama, 3. amir, hukuk istisnası ve tek-Başkan özel rol
kurallarını tek okunabilir sözleşmede tutar. Guard/gate scriptleri bu dosyayı
referans alarak eski yanlış kuralların tekrar koda sızmasını engeller.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Mapping

CONSTITUTION_VERSION = "2026-04-20-claude-faz4-performance-manager-rules"

# Temel ilkeler
BLIND_REVIEW_ALLOWED: bool = False
NEXT_MANAGER_SEES_PREVIOUS_SCORE_AND_COMMENT: bool = True
EMPLOYEE_RESULT_REQUIRES_PUBLISH: bool = True
MANAGER_OWN_RESULT_REQUIRES_PUBLISH: bool = True

# Puan ve açıklama kuralları
LOW_SCORE_THRESHOLD: float = 70.0
HIGH_SCORE_THRESHOLD: float = 90.0
COMMENT_REQUIRED_FOR_SCORES: tuple[int, int] = (1, 5)
GENERAL_COMMENT_REQUIRED_BELOW: float = 70.0
GENERAL_COMMENT_REQUIRED_ABOVE: float = 90.0
SCORE_MIN: int = 1
SCORE_MAX: int = 5
SCORE_TARGET_SCALE: int = 100

# Terminoloji
MAIN_CRITERIA_TERM = "Değerlendirme Kriterleri"
FORBIDDEN_MAIN_TERM = "Yetkinlik"

# Akış ve 3. amir modları
DEFAULT_SINGLE_MANAGER_FLOW: tuple[int, ...] = (1,)
DEFAULT_TWO_MANAGER_FLOW: tuple[int, ...] = (2, 1)
DEFAULT_THREE_MANAGER_FLOW: tuple[int, ...] = (3, 2, 1)
LEVEL_3_ALLOWED_MODES: tuple[str, ...] = ("off", "comment_only", "scoring")
LEVEL_3_DEFAULT_MODE: str = "comment_only"

# Ağırlık sözleşmeleri. Toplam her zaman 100 olmalıdır.
SINGLE_MANAGER_WEIGHTS: Mapping[int, float] = {1: 100.0, 2: 0.0, 3: 0.0}
TWO_MANAGER_WEIGHTS: Mapping[int, float] = {1: 50.0, 2: 50.0, 3: 0.0}
THREE_MANAGER_COMMENT_WEIGHTS: Mapping[int, float] = {1: 50.0, 2: 50.0, 3: 0.0}
THREE_MANAGER_SCORING_WEIGHTS: Mapping[int, float] = {1: 40.0, 2: 40.0, 3: 20.0}

SPECIAL_DIRECT_PRESIDENT_TITLES: tuple[str, ...] = (
    "baskan_danismani",
    "ozel_kalem",
    "ic_denetci",
)


@dataclass(frozen=True)
class ManagerRoleContract:
    code: str
    display_name: str
    slot_1: str
    slot_2: str | None
    slot_3: str | None
    flow: tuple[int, ...]
    weights: Mapping[int, float]
    note: str

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["flow"] = list(self.flow)
        data["weights"] = {str(k): v for k, v in self.weights.items()}
        return data


ROLE_CONTRACTS: Mapping[str, ManagerRoleContract] = {
    "group_staff": ManagerRoleContract(
        code="group_staff",
        display_name="Çalışma grubu personeli",
        slot_1="grup_baskani",
        slot_2="koordinator",
        slot_3="koordinatore_bagli_birim_amiri_optional",
        flow=DEFAULT_THREE_MANAGER_FLOW,
        weights=THREE_MANAGER_COMMENT_WEIGHTS,
        note="1. amir Grup Başkanı, 2. amir Koordinatör, varsa 3. amir Koordinatöre bağlı birim amiri.",
    ),
    "coordinator": ManagerRoleContract(
        code="coordinator",
        display_name="Koordinatör",
        slot_1="baskan_yardimcisi",
        slot_2="grup_baskani",
        slot_3="optional_defined_level_3",
        flow=DEFAULT_THREE_MANAGER_FLOW,
        weights=THREE_MANAGER_COMMENT_WEIGHTS,
        note="1. amir Başkan Yardımcısı, 2. amir Grup Başkanı; işlem sırası varsa 3 sonra 2 sonra 1.",
    ),
    "group_manager": ManagerRoleContract(
        code="group_manager",
        display_name="Grup Başkanı",
        slot_1="baskan",
        slot_2="baskan_yardimcisi",
        slot_3="optional_special_level_3",
        flow=DEFAULT_TWO_MANAGER_FLOW,
        weights=TWO_MANAGER_WEIGHTS,
        note="1. amir Başkan, 2. amir Başkan Yardımcısı; işlem sırası 2 sonra 1.",
    ),
    "presidency_level": ManagerRoleContract(
        code="presidency_level",
        display_name="Başkanlık seviyesi",
        slot_1="baskan",
        slot_2="baskan_yardimcisi",
        slot_3=None,
        flow=DEFAULT_TWO_MANAGER_FLOW,
        weights=TWO_MANAGER_WEIGHTS,
        note="Başkanlık katmanında önce 2. amir, sonra 1. amir puanlar.",
    ),
    "hukuk_single_manager": ManagerRoleContract(
        code="hukuk_single_manager",
        display_name="Hukuk müşavirine bağlı hukuk personeli",
        slot_1="bagli_oldugu_hukuk_musaviri",
        slot_2=None,
        slot_3=None,
        flow=DEFAULT_SINGLE_MANAGER_FLOW,
        weights=SINGLE_MANAGER_WEIGHTS,
        note="Tek amirli özel kural; 2. ve 3. amir görevi ya da sahte bekleme üretilmez.",
    ),
    "hukuk_chief_exception": ManagerRoleContract(
        code="hukuk_chief_exception",
        display_name="Hukuk müşaviri / sorumlu hukuk müşaviri",
        slot_1="baskan",
        slot_2="baskan_yardimcisi",
        slot_3=None,
        flow=DEFAULT_TWO_MANAGER_FLOW,
        weights=TWO_MANAGER_WEIGHTS,
        note="Genel hukuk tek-amir kuralının üst rol istisnası.",
    ),
    "direct_president_titles": ManagerRoleContract(
        code="direct_president_titles",
        display_name="Başkan danışmanı / Özel Kalem / İç Denetçi",
        slot_1="baskan",
        slot_2=None,
        slot_3=None,
        flow=DEFAULT_SINGLE_MANAGER_FLOW,
        weights=SINGLE_MANAGER_WEIGHTS,
        note="Sadece Başkan değerlendirir; 2. ve 3. amir görevi oluşmaz.",
    ),
}


FORBIDDEN_OLD_RULES: tuple[str, ...] = (
    "calisma_grubu_personeli_slot_1_koordinator",
    "koordinator_slot_1_grup_baskani",
    "grup_baskani_slot_1_baskan_yardimcisi",
    "two_manager_flow_1_to_2",
    "three_manager_flow_1_to_2_to_3",
    "blind_review_enabled",
    "level_3_always_comment_only_without_setting",
    "fake_second_manager_waiting_in_single_manager_case",
    "president_waiting_fake_status",
)


def _weight_total(weights: Mapping[int, float]) -> float:
    return round(sum(float(value) for value in weights.values()), 4)


def validate_constitution_self_check() -> list[str]:
    errors: list[str] = []
    if BLIND_REVIEW_ALLOWED:
        errors.append("Kör değerlendirme kapalı olmalıdır.")
    if not EMPLOYEE_RESULT_REQUIRES_PUBLISH:
        errors.append("Personel sonucu yayın/onay öncesi açılmamalıdır.")
    if COMMENT_REQUIRED_FOR_SCORES != (1, 5):
        errors.append("Açıklama zorunluluğu yalnızca 1 ve 5 puan için sabitlenmelidir.")
    if LOW_SCORE_THRESHOLD != 70.0 or HIGH_SCORE_THRESHOLD != 90.0:
        errors.append("70/90 eşikleri değişmemelidir.")
    if LEVEL_3_DEFAULT_MODE not in LEVEL_3_ALLOWED_MODES:
        errors.append("3. amir varsayılan modu izinli modlar içinde değil.")
    for name, weights in {
        "single": SINGLE_MANAGER_WEIGHTS,
        "two": TWO_MANAGER_WEIGHTS,
        "three_comment": THREE_MANAGER_COMMENT_WEIGHTS,
        "three_scoring": THREE_MANAGER_SCORING_WEIGHTS,
    }.items():
        if _weight_total(weights) != 100.0:
            errors.append(f"{name} ağırlık toplamı 100 değil: {_weight_total(weights)}")
    if ROLE_CONTRACTS["group_staff"].slot_1 != "grup_baskani" or ROLE_CONTRACTS["group_staff"].slot_2 != "koordinator":
        errors.append("Çalışma grubu personeli slot sözleşmesi bozulmuş.")
    if ROLE_CONTRACTS["coordinator"].slot_1 != "baskan_yardimcisi" or ROLE_CONTRACTS["coordinator"].slot_2 != "grup_baskani":
        errors.append("Koordinatör slot sözleşmesi bozulmuş.")
    if ROLE_CONTRACTS["group_manager"].slot_1 != "baskan" or ROLE_CONTRACTS["group_manager"].slot_2 != "baskan_yardimcisi":
        errors.append("Grup Başkanı slot sözleşmesi bozulmuş.")
    if ROLE_CONTRACTS["hukuk_single_manager"].flow != DEFAULT_SINGLE_MANAGER_FLOW:
        errors.append("Hukuk tek-amir akışı tek görev üretmelidir.")
    return errors


def get_manager_rule_snapshot() -> dict[str, object]:
    return {
        "version": CONSTITUTION_VERSION,
        "blind_review_allowed": BLIND_REVIEW_ALLOWED,
        "employee_result_requires_publish": EMPLOYEE_RESULT_REQUIRES_PUBLISH,
        "next_manager_sees_previous_score_and_comment": NEXT_MANAGER_SEES_PREVIOUS_SCORE_AND_COMMENT,
        "score": {
            "scale": [SCORE_MIN, SCORE_MAX],
            "target_scale": SCORE_TARGET_SCALE,
            "comment_required_for_scores": list(COMMENT_REQUIRED_FOR_SCORES),
            "general_comment_required_below": GENERAL_COMMENT_REQUIRED_BELOW,
            "general_comment_required_above": GENERAL_COMMENT_REQUIRED_ABOVE,
        },
        "level_3": {
            "allowed_modes": list(LEVEL_3_ALLOWED_MODES),
            "default_mode": LEVEL_3_DEFAULT_MODE,
            "comment_mode_weight": THREE_MANAGER_COMMENT_WEIGHTS[3],
            "scoring_mode_weight": THREE_MANAGER_SCORING_WEIGHTS[3],
        },
        "terms": {
            "main": MAIN_CRITERIA_TERM,
            "forbidden_main": FORBIDDEN_MAIN_TERM,
        },
        "roles": {key: contract.as_dict() for key, contract in ROLE_CONTRACTS.items()},
        "special_direct_president_titles": list(SPECIAL_DIRECT_PRESIDENT_TITLES),
        "forbidden_old_rules": list(FORBIDDEN_OLD_RULES),
    }


__all__ = [
    "BLIND_REVIEW_ALLOWED",
    "COMMENT_REQUIRED_FOR_SCORES",
    "CONSTITUTION_VERSION",
    "DEFAULT_SINGLE_MANAGER_FLOW",
    "DEFAULT_THREE_MANAGER_FLOW",
    "DEFAULT_TWO_MANAGER_FLOW",
    "EMPLOYEE_RESULT_REQUIRES_PUBLISH",
    "FORBIDDEN_OLD_RULES",
    "GENERAL_COMMENT_REQUIRED_ABOVE",
    "GENERAL_COMMENT_REQUIRED_BELOW",
    "HIGH_SCORE_THRESHOLD",
    "LEVEL_3_ALLOWED_MODES",
    "LEVEL_3_DEFAULT_MODE",
    "LOW_SCORE_THRESHOLD",
    "MAIN_CRITERIA_TERM",
    "ManagerRoleContract",
    "NEXT_MANAGER_SEES_PREVIOUS_SCORE_AND_COMMENT",
    "ROLE_CONTRACTS",
    "SINGLE_MANAGER_WEIGHTS",
    "SPECIAL_DIRECT_PRESIDENT_TITLES",
    "THREE_MANAGER_COMMENT_WEIGHTS",
    "THREE_MANAGER_SCORING_WEIGHTS",
    "TWO_MANAGER_WEIGHTS",
    "get_manager_rule_snapshot",
    "validate_constitution_self_check",
]
