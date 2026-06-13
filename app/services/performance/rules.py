
"""BYS360 Performans Yönetimi için bağlayıcı kural sabitleri.

Faz 4 amacı:
- varsayılan ağırlığı 50/50/0'da sabitlemek
- 3. amiri varsayılanda yorumcu modunda tutmak
- kör değerlendirmeyi kapalı kabul etmek
- bilgi / uyarı / hata metinlerini tek yerde toplamak
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Final

AUTHORITATIVE_PERFORMANCE_RULESET_VERSION: Final[str] = "2026-04-18-chain-engine-lock-v1"

DEFAULT_TWO_MANAGER_WEIGHTS: Final[tuple[float, float, float]] = (50.0, 50.0, 0.0)
DEFAULT_THREE_MANAGER_SCORING_WEIGHTS: Final[tuple[float, float, float]] = (40.0, 40.0, 20.0)

PRESIDENT_LEVEL_REVIEW_ORDER: Final[tuple[int, int]] = (2, 1)
GROUP_LEVEL_REVIEW_ORDER_WITH_LEVEL3: Final[tuple[int, int, int]] = (3, 2, 1)
GROUP_LEVEL_REVIEW_ORDER_DEFAULT: Final[tuple[int, int]] = (2, 1)
COORDINATOR_SELF_REVIEW_ORDER: Final[tuple[int, int]] = (2, 1)

LEVEL_3_DEFAULT_MODE: Final[str] = "comment_only"
LEVEL_3_ALLOWED_MODES: Final[tuple[str, ...]] = ("off", "comment_only", "scoring")
BLIND_REVIEW_ALLOWED: Final[bool] = False

INFO_REASON_SPECIAL_SINGLE_MANAGER: Final[str] = "Özel tek amir kuralı uygulandı (100 / 0 / 0)."
INFO_REASON_HUKUK_SINGLE_MANAGER: Final[str] = "Hukuk Müşavirliği tek amir kuralı uygulandı (100 / 0 / 0)."
INFO_REASON_LEVEL3_COMMENT_ONLY: Final[str] = "3. amir yorumcu modunda; nihai puana etkisi 0."
INFO_REASON_DELEGATED_ASSIGNMENT: Final[str] = "Vekâlet nedeniyle görev aynı seviyede vekile yönlendirildi."
INFO_REASON_PRESIDENT_EXCLUDED: Final[str] = "Başkan performans değerlendirme zincirine dahil edilmez."
INFO_REASON_COORDINATOR_CHAIN_CORRECTED: Final[str] = "Koordinatör zinciri güncel kurala göre düzeltildi."
INFO_REASON_GROUP_STAFF_CHAIN_CORRECTED: Final[str] = "Çalışma grubu personeli zinciri nihai matrise göre düzeltildi."

WARNING_REASON_MANAGER_1_MISSING: Final[str] = "1. amir eksik veya pasif"
WARNING_REASON_MANAGER_2_MISSING: Final[str] = "2. amir eksik veya pasif"
WARNING_REASON_MANAGER_3_INVALID: Final[str] = "3. amir tanımlı ancak geçersiz/pasif"
WARNING_REASON_DUPLICATE_MANAGER: Final[str] = "Aynı kişi birden fazla amir seviyesine atanmış."
WARNING_REASON_SELF_MANAGER: Final[str] = "Personel kendisine amir atanamaz."
WARNING_REASON_PRESIDENT_MISSING: Final[str] = "Başkan kaydı bulunamadı veya pasif."

LEAVE_PERFORMANCE_MODE_DEFAULT: Final[str] = "partial"
LEAVE_PERFORMANCE_MODE_ALLOWED: Final[tuple[str, ...]] = ("exclude", "partial", "informational")

@dataclass(frozen=True)
class AuthoritativePerformanceRules:
    version: str = AUTHORITATIVE_PERFORMANCE_RULESET_VERSION
    default_weight_1: float = DEFAULT_TWO_MANAGER_WEIGHTS[0]
    default_weight_2: float = DEFAULT_TWO_MANAGER_WEIGHTS[1]
    default_weight_3: float = DEFAULT_TWO_MANAGER_WEIGHTS[2]
    level_3_default_mode: str = LEVEL_3_DEFAULT_MODE
    blind_review_allowed: bool = BLIND_REVIEW_ALLOWED

    def as_dict(self) -> Dict[str, object]:
        return {
            "version": self.version,
            "default_weights": {
                "manager_1": self.default_weight_1,
                "manager_2": self.default_weight_2,
                "manager_3": self.default_weight_3,
            },
            "level_3_default_mode": self.level_3_default_mode,
            "blind_review_allowed": self.blind_review_allowed,
            "leave_performance_mode_default": LEAVE_PERFORMANCE_MODE_DEFAULT,
            "leave_performance_modes": list(LEAVE_PERFORMANCE_MODE_ALLOWED),
            "president_level_review_order": list(PRESIDENT_LEVEL_REVIEW_ORDER),
            "group_level_review_order_with_level3": list(GROUP_LEVEL_REVIEW_ORDER_WITH_LEVEL3),
            "group_level_review_order_default": list(GROUP_LEVEL_REVIEW_ORDER_DEFAULT),
            "core_visibility_rules": {
                "blind_review_allowed": BLIND_REVIEW_ALLOWED,
                "employee_publish_gate": True,
                "president_scoring_excluded": True,
            },
            "rule_engine_source": "app.services.performance.chain_rule_engine",
            "authoritative_slot_matrix": {
                "group_staff": {"slot_1": "grup_baskani", "slot_2": "koordinator", "slot_3": "birim_amiri_optional"},
                "coordinator": {"slot_1": "baskan_yardimcisi", "slot_2": "grup_baskani"},
                "special_direct_president": ["baskan_danismani", "ozel_kalem", "ic_denetci"],
            },
        }


def get_authoritative_performance_rules_snapshot() -> Dict[str, object]:
    return AuthoritativePerformanceRules().as_dict()


__all__ = [
    "AUTHORITATIVE_PERFORMANCE_RULESET_VERSION",
    "AuthoritativePerformanceRules",
    "BLIND_REVIEW_ALLOWED",
    "COORDINATOR_SELF_REVIEW_ORDER",
    "DEFAULT_THREE_MANAGER_SCORING_WEIGHTS",
    "DEFAULT_TWO_MANAGER_WEIGHTS",
    "GROUP_LEVEL_REVIEW_ORDER_DEFAULT",
    "GROUP_LEVEL_REVIEW_ORDER_WITH_LEVEL3",
    "INFO_REASON_COORDINATOR_CHAIN_CORRECTED",
    "INFO_REASON_GROUP_STAFF_CHAIN_CORRECTED",
    "INFO_REASON_DELEGATED_ASSIGNMENT",
    "INFO_REASON_HUKUK_SINGLE_MANAGER",
    "INFO_REASON_LEVEL3_COMMENT_ONLY",
    "INFO_REASON_PRESIDENT_EXCLUDED",
    "INFO_REASON_SPECIAL_SINGLE_MANAGER",
    "LEAVE_PERFORMANCE_MODE_ALLOWED",
    "LEAVE_PERFORMANCE_MODE_DEFAULT",
    "LEVEL_3_ALLOWED_MODES",
    "LEVEL_3_DEFAULT_MODE",
    "PRESIDENT_LEVEL_REVIEW_ORDER",
    "WARNING_REASON_DUPLICATE_MANAGER",
    "WARNING_REASON_MANAGER_1_MISSING",
    "WARNING_REASON_MANAGER_2_MISSING",
    "WARNING_REASON_MANAGER_3_INVALID",
    "WARNING_REASON_PRESIDENT_MISSING",
    "WARNING_REASON_SELF_MANAGER",
    "get_authoritative_performance_rules_snapshot",
]

INFO_REASON_SPECIAL_MANAGER_CORRECTED = "Özel kural gereği zincir kurumsal sıraya göre düzeltildi."

INFO_REASON_MANAGER_CHAIN_REPAIRED = "Amir zinciri kurala göre onarıldı."

INFO_REASON_MANAGER_CHAIN_FILLED = "Eksik amir zinciri kurala göre dolduruldu."