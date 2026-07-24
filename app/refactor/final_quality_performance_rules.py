
"""BYS360 Final Quality Faz 2 performans kural matrisi sözleşmesi.

Bu modül runtime akışını değiştirmez; veritabanı, route, blueprint veya
şema işlemi yapmaz. Amaç, nihai performans amir kurallarını test edilebilir
sabit sözleşmeye dönüştürmektir.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, cast


@dataclass(frozen=True)
class PerformanceRoleRule:
    key: str
    title: str
    first_manager: str
    second_manager: str | None
    third_manager: str | None
    process_order: tuple[str, ...]
    single_manager: bool
    fake_waiting_forbidden: bool
    weight_profile: tuple[int, int, int] | None
    note: str


@dataclass(frozen=True)
class ThirdManagerModeRule:
    mode: str
    title: str
    score_enabled: bool
    score_impact_percent: int | None
    status_label: str
    included_in_final_score: bool


@dataclass(frozen=True)
class PerformanceVisibilityRule:
    key: str
    enabled: bool
    note: str


@dataclass(frozen=True)
class ScoreExplanationRule:
    key: str
    threshold_or_score: int
    required: bool
    note: str


PERFORMANCE_ROLE_RULES: Final[tuple[PerformanceRoleRule, ...]] = (
    PerformanceRoleRule(
        key="calisma_grubu_personeli",
        title="Çalışma grubu personeli",
        first_manager="grup_baskani",
        second_manager="koordinator",
        third_manager="koordinatore_bagli_birim_amiri_opsiyonel",
        process_order=("third", "second", "first"),
        single_manager=False,
        fake_waiting_forbidden=False,
        weight_profile=None,
        note="Nihai üst amir Grup Başkanıdır; Koordinatör ikinci seviyede yer alır.",
    ),
    PerformanceRoleRule(
        key="koordinator",
        title="Koordinatör",
        first_manager="baskan_yardimcisi",
        second_manager="grup_baskani",
        third_manager="opsiyonel",
        process_order=("third", "second", "first"),
        single_manager=False,
        fake_waiting_forbidden=False,
        weight_profile=None,
        note="Koordinatör için 1. amir Başkan Yardımcısı, 2. amir Grup Başkanıdır.",
    ),
    PerformanceRoleRule(
        key="grup_baskani",
        title="Grup Başkanı",
        first_manager="baskan",
        second_manager="baskan_yardimcisi",
        third_manager="ozel_yapiya_gore_opsiyonel",
        process_order=("second", "first"),
        single_manager=False,
        fake_waiting_forbidden=False,
        weight_profile=None,
        note="Standart akışta önce Başkan Yardımcısı, sonra Başkan değerlendirir.",
    ),
    PerformanceRoleRule(
        key="baskanlik_seviyesi",
        title="Başkanlık seviyesi",
        first_manager="baskan",
        second_manager="baskan_yardimcisi",
        third_manager=None,
        process_order=("second", "first"),
        single_manager=False,
        fake_waiting_forbidden=False,
        weight_profile=None,
        note="Başkanlık katmanında puanlama sırası önce 2. amir, sonra 1. amirdir.",
    ),
    PerformanceRoleRule(
        key="hukuk_musavirine_bagli_hukuk_personeli",
        title="Hukuk müşavirine bağlı hukuk personeli",
        first_manager="bagli_oldugu_hukuk_musaviri",
        second_manager=None,
        third_manager=None,
        process_order=("first",),
        single_manager=True,
        fake_waiting_forbidden=True,
        weight_profile=(100, 0, 0),
        note="Tek amirli özel akış; sahte 2. veya 3. amir bekleme durumu üretilemez.",
    ),
    PerformanceRoleRule(
        key="hukuk_musaviri_sorumlu_hukuk_musaviri",
        title="Hukuk müşaviri / sorumlu hukuk müşaviri",
        first_manager="baskan",
        second_manager="baskan_yardimcisi",
        third_manager=None,
        process_order=("second", "first"),
        single_manager=False,
        fake_waiting_forbidden=False,
        weight_profile=None,
        note="Genel hukuk tek-amir kuralından ayrı üst rol istisnası.",
    ),
    PerformanceRoleRule(
        key="baskan_tek_degerlendirici_ozel_roller",
        title="Başkan danışmanı / Özel Kalem / İç Denetçi",
        first_manager="baskan",
        second_manager=None,
        third_manager=None,
        process_order=("first",),
        single_manager=True,
        fake_waiting_forbidden=True,
        weight_profile=(100, 0, 0),
        note="Sadece Başkan tarafından puanlanır; tek görev oluşur.",
    ),
)


THIRD_MANAGER_MODE_RULES: Final[tuple[ThirdManagerModeRule, ...]] = (
    ThirdManagerModeRule(
        mode="comment_only",
        title="3. amir yorum modu",
        score_enabled=False,
        score_impact_percent=0,
        status_label="yorum/görüş bekliyor",
        included_in_final_score=False,
    ),
    ThirdManagerModeRule(
        mode="score_contributor",
        title="3. amir puan modu",
        score_enabled=True,
        score_impact_percent=None,
        status_label="puan bekliyor",
        included_in_final_score=True,
    ),
)


PERFORMANCE_VISIBILITY_RULES: Final[tuple[PerformanceVisibilityRule, ...]] = (
    PerformanceVisibilityRule("no_blind_evaluation", True, "Sonraki amir önceki puanı ve genel kanaati görebilir."),
    PerformanceVisibilityRule("publish_required_before_employee_visibility", True, "Personel sonucu İK/Admin yayınlamadan göremez."),
    PerformanceVisibilityRule("manager_visibility_separate_from_employee_visibility", True, "Amir görünürlüğü ile personel görünürlüğü ayrıdır."),
    PerformanceVisibilityRule("no_fake_waiting_status_for_single_manager", True, "Tek amirli akışta sahte 2. veya 3. amir bekleme durumu yazılamaz."),
    PerformanceVisibilityRule("third_manager_comment_status_is_not_score_waiting", True, "3. amir yorum modunda statü puan bekliyor değil, yorum/görüş bekliyor olmalıdır."),
    PerformanceVisibilityRule("term_degerlendirme_kriterleri", True, "Ana terim Değerlendirme Kriterleri olmalıdır; Yetkinlik ana ekran terimi değildir."),
)


SCORE_EXPLANATION_RULES: Final[tuple[ScoreExplanationRule, ...]] = (
    ScoreExplanationRule("score_1_comment_required", 1, True, "1 puan verildiğinde açıklama zorunludur."),
    ScoreExplanationRule("score_5_comment_required", 5, True, "5 puan verildiğinde açıklama zorunludur."),
    ScoreExplanationRule("final_below_70_general_comment_required", 70, True, "Nihai sonuç 70 altındaysa ayrıntılı genel görüş zorunludur."),
    ScoreExplanationRule("final_above_90_general_comment_required", 90, True, "Nihai sonuç 90 üstündeyse ayrıntılı genel görüş zorunludur."),
)


PERFORMANCE_SCORING_CONTRACT: Final[dict[str, object]] = {
    "criteria_score_min": 1,
    "criteria_score_max": 5,
    "converted_scale_max": 100,
    "weight_total_percent": 100,
    "failure_threshold_below": 70,
    "high_success_threshold_above": 90,
    "primary_term": "Değerlendirme Kriterleri",
    "forbidden_primary_term": "Yetkinlik",
}

SPECIAL_SINGLE_MANAGER_ROLE_KEYS: Final[tuple[str, ...]] = (
    "hukuk_musavirine_bagli_hukuk_personeli",
    "baskan_tek_degerlendirici_ozel_roller",
)

SPECIAL_PRESIDENT_ONLY_ROLES: Final[tuple[str, ...]] = (
    "baskan_danismani",
    "ozel_kalem",
    "ic_denetci",
)

FINAL_QUALITY_FAZ2_VERSION: Final[str] = "2026-04-21-final-quality-faz2-performance-rule-matrix"


def get_role_rule(key: str) -> PerformanceRoleRule:
    for rule in PERFORMANCE_ROLE_RULES:
        if rule.key == key:
            return rule
    raise KeyError(key)


def get_third_manager_mode(mode: str) -> ThirdManagerModeRule:
    for rule in THIRD_MANAGER_MODE_RULES:
        if rule.mode == mode:
            return rule
    raise KeyError(mode)


def validate_weight_profile(profile: tuple[int, int, int]) -> bool:
    return sum(profile) == int(cast(int, PERFORMANCE_SCORING_CONTRACT["weight_total_percent"]))


def get_contract_summary() -> dict[str, object]:
    return {
        "version": FINAL_QUALITY_FAZ2_VERSION,
        "role_rule_count": len(PERFORMANCE_ROLE_RULES),
        "third_manager_mode_count": len(THIRD_MANAGER_MODE_RULES),
        "visibility_rule_count": len(PERFORMANCE_VISIBILITY_RULES),
        "score_explanation_rule_count": len(SCORE_EXPLANATION_RULES),
        "runtime_mutation": False,
    }


__all__ = [
    "FINAL_QUALITY_FAZ2_VERSION",
    "PERFORMANCE_ROLE_RULES",
    "THIRD_MANAGER_MODE_RULES",
    "PERFORMANCE_VISIBILITY_RULES",
    "SCORE_EXPLANATION_RULES",
    "PERFORMANCE_SCORING_CONTRACT",
    "SPECIAL_SINGLE_MANAGER_ROLE_KEYS",
    "SPECIAL_PRESIDENT_ONLY_ROLES",
    "get_role_rule",
    "get_third_manager_mode",
    "validate_weight_profile",
    "get_contract_summary",
]
