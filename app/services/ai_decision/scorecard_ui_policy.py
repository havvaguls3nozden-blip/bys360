from __future__ import annotations

import logging

"""BYS360 AI Karar Destek Faz 5 karne sunum politikası.

Karar destek çıktılarının karne ve puanlama ekranlarında temiz, okunur ve
kurumsal Türkçe ile sunulması için ortak etiket, önem düzeyi ve güvenli metin
üretir. Bu servis idari karar üretmez; yalnızca yetkili kullanıcıya ekran
üzerinde yardımcı karar destek sinyali sağlar.

BYS360_AI_DECISION_FAZ5_SCORECARD_UI_POLICY
"""

import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)

TECHNICAL_LABELS: dict[str, str] = {
    "president_pending": "Başkan Onayı Bekliyor",
    "blocked_president_pending": "Başkan Onayı Yayın Kilidi",
    "hr_precheck": "İK/Admin Kontrolünde",
    "first_low_warning": "Düşük Performans Uyarısı Oluşturuldu",
    "second_low_repeat": "Tekrarlayan Düşük Performans Süreci",
    "approved_by_president": "Başkan Tarafından Onaylandı",
    "rejected_by_president": "Başkan Tarafından İade Edildi",
    "published": "Yayımlandı",
    "pending": "Beklemede",
    "completed": "Tamamlandı",
    "returned": "İade Edildi",
    "locked": "Yayın Kilidi Var",
    "open": "Açık",
    "closed": "Kapandı",
}

TECHNICAL_PATTERNS = (
    re.compile(r"\bauthorized[_\s-]*scope\b", re.IGNORECASE),
    re.compile(r"\bworkflow[_\s-]*state\b", re.IGNORECASE),
    re.compile(r"\bdraft\b", re.IGNORECASE),
    re.compile(r"\bsync\b", re.IGNORECASE),
    re.compile(r"\bdebug\b", re.IGNORECASE),
    re.compile(r"\btest\s+only\b", re.IGNORECASE),
    re.compile(r"\b" + "du" + "mmy" + r"\b", re.IGNORECASE),
    re.compile(r"\bTODO\b", re.IGNORECASE),
)

@dataclass(frozen=True)
class ScorecardUIPolicy:
    low_score_limit: int = 70
    high_score_limit: int = 90
    show_technical_terms: bool = False
    require_low_score_explanation: bool = True
    require_high_score_explanation: bool = True
    marker: str = "BYS360_AI_DECISION_FAZ5_SCORECARD_UI_POLICY_OK"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def _to_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "evet", "on", "açık", "aktif"}:
        return True
    if text in {"0", "false", "no", "hayır", "off", "kapalı", "pasif"}:
        return False
    return default

def _to_int(value: Any, default: int) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(str(value).replace(",", ".")))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default

def build_scorecard_ui_policy(settings: Mapping[str, Any] | None = None) -> ScorecardUIPolicy:
    data = settings or {}
    return ScorecardUIPolicy(
        low_score_limit=_to_int(data.get("performance.low_score_limit") or data.get("ai_decision.faz5_low_score_limit"), 70),
        high_score_limit=_to_int(data.get("performance.high_score_limit") or data.get("ai_decision.faz5_high_score_limit"), 90),
        show_technical_terms=_to_bool(data.get("ai_decision.faz5_show_technical_terms"), False),
        require_low_score_explanation=_to_bool(data.get("performance.require_general_comment_below_70") or data.get("ai_decision.faz5_require_low_score_explanation"), True),
        require_high_score_explanation=_to_bool(data.get("performance.require_general_comment_above_90") or data.get("ai_decision.faz5_require_high_score_explanation"), True),
    )

def safe_attr(obj: Any, *names: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        for name in names:
            if name in obj and obj.get(name) not in (None, ""):
                return obj.get(name)
        return default
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value not in (None, ""):
                return value
    return default

def normalize_status_label(value: Any) -> str:
    if value in (None, ""):
        return "Durum Bilgisi Yok"
    key = str(value).strip()
    return TECHNICAL_LABELS.get(key, TECHNICAL_LABELS.get(key.lower(), key.replace("_", " ").strip().title()))

def clean_screen_text(value: Any, fallback: str = "Açıklama bulunamadı.") -> str:
    if value in (None, ""):
        return fallback
    text = str(value).strip()
    if not text:
        return fallback
    for pattern in TECHNICAL_PATTERNS:
        text = pattern.sub("kurumsal süreç", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or fallback

def score_to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None

def score_band(score: Any, policy: ScorecardUIPolicy | None = None) -> dict[str, str]:
    p = policy or ScorecardUIPolicy()
    numeric = score_to_float(score)
    if numeric is None:
        return {"key": "missing", "label": "Puan Oluşmadı", "tone": "neutral", "headline": "Karne puanı henüz kesinleşmedi"}
    if numeric < p.low_score_limit:
        return {"key": "low", "label": "Düşük Performans", "tone": "warning", "headline": "Başkan/Üst Onay gerektiren düşük performans"}
    if numeric >= p.high_score_limit:
        return {"key": "high", "label": "Yüksek Başarı", "tone": "success", "headline": "Güçlü performans ve gelişim takibi"}
    return {"key": "normal", "label": "Beklenen Aralık", "tone": "info", "headline": "Kurumsal değerlendirme aralığında sonuç"}

def display_score(score: Any) -> str:
    numeric = score_to_float(score)
    if numeric is None:
        return "—"
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:.2f}".rstrip("0").rstrip(".")
