from __future__ import annotations

PRIMARY_TERM_TR = "Değerlendirme Kriterleri"
PRIMARY_TERM_ASCII = "Degerlendirme Kriterleri"
PRIMARY_TERM = PRIMARY_TERM_TR

"""BYS360 Performans Amir Kuralları Sözleşmesi.

Bu dosya, performans değerlendirme motorunun değişmez iş kurallarını
tek noktada, test edilebilir ve izlenebilir biçimde kilitler.

Tasarım kararları:
- Rol isimleri ve terimler canonical Türkçedir (görünür arayüz ve testlerle uyumlu).
- ASCII uyumluluk değerleri _ASCII sabit alias'ları ile ayrıca korunur;
  bu sayede eski gate scriptleri ve veritabanı sorguları etkilenmez.
- process_order alanı tuple[str, ...] tipindedir; string "3->2->1" formatı
  normalize_process_order() ile dönüştürülebilir.

Kural özeti:
- Kör değerlendirme yoktur; sonraki amir önceki puanı ve kanaati görebilir.
- Yayın öncesi personele açılmaz; personel sonuçları yetkili onaydan sonra görür.
- TC yerine Sicil No yaklaşımı esastır.
- Ana terim "Değerlendirme Kriterleri"dir; "Yetkinlik" kullanılamaz.
- 70 altı ve 90 üstü eşiklerde ayrıntılı genel görüş zorunludur.
- 3. amir zorunlu değildir; yorum veya puan modu sistem ayarıyla yönetilir.
"""

from dataclasses import dataclass
from collections.abc import Iterable


# ---------------------------------------------------------------------------
# Birincil terim sabitleri
# ---------------------------------------------------------------------------


FORBIDDEN_PRIMARY_TERM = "Yetkinlik"


# ---------------------------------------------------------------------------
# Görünürlük ve kural sabitleri
# ---------------------------------------------------------------------------

NO_BLIND_EVALUATION                 = True
NO_PERSONNEL_VISIBILITY_BEFORE_PUBLISH = True
PERSON_RESULT_VISIBLE_ONLY_AFTER_PUBLISH = True
USE_EVALUATION_CRITERIA_TERM        = True
THIRD_MANAGER_OPTIONAL              = True
THIRD_MANAGER_COMMENT_OR_SCORE_MODE = True

LOW_SCORE_THRESHOLD  = 70
HIGH_SCORE_THRESHOLD = 90


# ---------------------------------------------------------------------------
# ManagerRule veri sınıfı
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ManagerRule:
    """Bir rol için amir zinciri ve işlem sırası sözleşmesi.

    Attributes:
        first_manager:  Canonical Türkçe 1. amir unvanı.
        second_manager: Canonical Türkçe 2. amir unvanı; tek amirli rollerde None.
        process_order:  Değerlendirme sırası tuple'ı — örn. ("3", "2", "1").
        third_manager:  3. amir; tanımlıysa Türkçe unvan, değilse None.
        note:           İnsan okunabilir açıklama (makine davranışını etkilemez).
        first_manager_ascii:  Geriye dönük uyumluluk için ASCII alias.
        second_manager_ascii: Geriye dönük uyumluluk için ASCII alias.
    """

    first_manager:       str
    second_manager:      str | None
    process_order:       tuple[str, ...]
    third_manager:       str | None = None
    note:                str        = ""
    first_manager_ascii: str        = ""
    second_manager_ascii: str       = ""

    def process_levels(self, *, has_third_manager: bool = False) -> tuple[str, ...]:
        """Üçüncü amir varlığına göre işlem sırası tuple'ını döndürür."""
        if not has_third_manager and "3" in self.process_order:
            return tuple(lvl for lvl in self.process_order if lvl != "3")
        return self.process_order


# ---------------------------------------------------------------------------
# Rol bazlı amir kuralları
# ---------------------------------------------------------------------------

PERFORMANCE_MANAGER_RULES: dict[str, ManagerRule] = {
    "working_group_personnel": ManagerRule(
        first_manager        = "Grup Başkanı",
        first_manager_ascii  = "Grup Baskani",
        second_manager       = "Koordinatör",
        second_manager_ascii = "Koordinator",
        third_manager        = "Koordinatöre bağlı birim amiri",
        process_order        = ("3", "2", "1"),
        note                 = "Çalışma grubu personelinde nihai 1. amir Grup Başkanı, 2. amir Koordinatör.",
    ),
    "coordinator": ManagerRule(
        first_manager        = "Başkan Yardımcısı",
        first_manager_ascii  = "Baskan Yardimcisi",
        second_manager       = "Grup Başkanı",
        second_manager_ascii = "Grup Baskani",
        third_manager        = None,
        process_order        = ("3", "2", "1"),
        note                 = "Koordinatör için nihai 1. amir Başkan Yardımcısı, 2. amir Grup Başkanı.",
    ),
    "group_head": ManagerRule(
        first_manager        = "Başkan",
        first_manager_ascii  = "Baskan",
        second_manager       = "Başkan Yardımcısı",
        second_manager_ascii = "Baskan Yardimcisi",
        third_manager        = None,
        process_order        = ("2", "1"),
        note                 = "Grup Başkanı için önce Başkan Yardımcısı, sonra Başkan akışı.",
    ),
    "legal_single_manager": ManagerRule(
        first_manager        = "Bağlı olduğu hukuk müşaviri",
        first_manager_ascii  = "Bagli Oldugu Hukuk Musaviri",
        second_manager       = None,
        second_manager_ascii = "",
        third_manager        = None,
        process_order        = ("1",),
        note                 = "Hukuk Müşavirliği tek amirli özel kural: 100/0/0.",
    ),
    "president_only_roles": ManagerRule(
        first_manager        = "Başkan",
        first_manager_ascii  = "Baskan",
        second_manager       = None,
        second_manager_ascii = "",
        third_manager        = None,
        process_order        = ("1",),
        note                 = "Başkan danışmanı, Özel Kalem ve İç Denetçi yalnızca Başkan tarafından değerlendirilir.",
    ),
}


# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------------------

def get_manager_rule(role_key: str) -> ManagerRule:
    """Rol anahtarına göre amir kuralını döndürür.

    Raises:
        KeyError: Bilinmeyen rol anahtarı.
    """
    if role_key not in PERFORMANCE_MANAGER_RULES:
        raise KeyError(f"Bilinmeyen performans rolü: {role_key!r}")
    return PERFORMANCE_MANAGER_RULES[role_key]


def is_single_manager_flow(role_key: str) -> bool:
    """Rol için tek amir akışı uygulanıyorsa True döner."""
    rule = get_manager_rule(role_key)
    return rule.second_manager is None and rule.third_manager is None


def build_process_order(role_key: str, *, has_third_manager: bool = False) -> tuple[str, ...]:
    """Üçüncü amir varlığına göre işlem sırasını döndürür."""
    return get_manager_rule(role_key).process_levels(has_third_manager=has_third_manager)


def third_manager_policy(mode: str) -> dict[str, object]:
    """Üçüncü amir moduna göre uygulama politikasını döndürür.

    Args:
        mode: "comment" veya "score"

    Returns:
        Politika sözlüğü.

    Raises:
        ValueError: Bilinmeyen mod.
    """
    if mode in {"comment", "comment_only", "yorum"}:
        return {
            "score_effect":       0,
            "status_text":        "yorum/görüş bekliyor",
            "score_input_enabled": False,
            "included_in_weight": False,
        }
    if mode in {"score", "scoring", "puan"}:
        return {
            "score_effect":       "dynamic",
            "status_text":        "puan girişi bekleniyor",
            "score_input_enabled": True,
            "included_in_weight": True,
        }
    raise ValueError(f"Bilinmeyen üçüncü amir modu: {mode!r}")


def requires_score_explanation(score: int) -> bool:
    """1 veya 5 puanında açıklama zorunluluğu kuralı."""
    return score in (1, 5)


def requires_detailed_general_opinion(total_score: float) -> bool:
    """Düşük veya yüksek toplam puanda ayrıntılı genel görüş zorunluluğu.

    Eşik değerleri dahil değil (sınır hariç).
    """
    return total_score < LOW_SCORE_THRESHOLD or total_score > HIGH_SCORE_THRESHOLD


def validate_weight_total(weights: dict[str, int | float]) -> bool:
    """Ağırlıkların toplamının 100 olduğunu doğrular (float toleranslı)."""
    return abs(sum(weights.values()) - 100) < 0.0001


def normalize_process_order(order: str | Iterable[str | int]) -> tuple[str, ...]:
    """String "3->2->1" veya iterable formatını tuple'a dönüştürür.

    Eski gate scriptleriyle uyumluluk için korunur.
    """
    if isinstance(order, str):
        return tuple(part.strip() for part in order.split("->") if part.strip())
    return tuple(str(item) for item in order)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    # Terim sabitleri
    "PRIMARY_TERM",
    "PRIMARY_TERM_TR",
    "PRIMARY_TERM_ASCII",
    "FORBIDDEN_PRIMARY_TERM",
    # Görünürlük sabitleri
    "NO_BLIND_EVALUATION",
    "NO_PERSONNEL_VISIBILITY_BEFORE_PUBLISH",
    "PERSON_RESULT_VISIBLE_ONLY_AFTER_PUBLISH",
    "USE_EVALUATION_CRITERIA_TERM",
    "THIRD_MANAGER_OPTIONAL",
    "THIRD_MANAGER_COMMENT_OR_SCORE_MODE",
    # Eşik değerleri
    "LOW_SCORE_THRESHOLD",
    "HIGH_SCORE_THRESHOLD",
    # Veri sınıfı & kural tablosu
    "ManagerRule",
    "PERFORMANCE_MANAGER_RULES",
    # Fonksiyonlar
    "get_manager_rule",
    "is_single_manager_flow",
    "build_process_order",
    "third_manager_policy",
    "requires_score_explanation",
    "requires_detailed_general_opinion",
    "validate_weight_total",
    "normalize_process_order",
]
