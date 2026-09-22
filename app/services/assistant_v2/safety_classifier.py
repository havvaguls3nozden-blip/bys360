"""BYS360 Assistant V2 -- native safety/scope classifier (mandate Phase C).

Deterministic, regex/vocabulary-based classification, run BEFORE intent
routing and BEFORE any capability is dispatched. No external model, no
giant if/elif chain -- classification is table-driven (a tuple of
`(pattern, category)` rules checked in a fixed, documented priority order).

The `SENSITIVE_PATTERNS` and `OUT_OF_SCOPE_HINTS` values below are copied
verbatim (not reinvented) from the legacy chain's own
`app/services/ai_agent/assistant_chatgpt_like_v31.py` (`SENSITIVE_PATTERNS`,
`OUT_OF_SCOPE_HINTS`) -- this project's own "preserve useful legacy
behavior, don't reinvent it" instruction applied literally. They are
reproduced here as an independent, V2-owned copy rather than imported from
the legacy module, so this classifier has zero runtime dependency on the
legacy chain (consistent with keeping assistant_v2 free of legacy imports,
matching the same architectural boundary already enforced for
app.services.ai in test_assistant_v2_external_ai_absence_contract_v1.py).

Priority order (checked in this fixed sequence, first match wins):
  1. SENSITIVE_REQUEST  -- a request that combines a data-access verb with
     a sensitive-content noun (performance score, TC kimlik, salary, etc.)
  2. OUT_OF_SCOPE        -- a question about something BYS360 has no data
     for at all (weather, stock prices, news, sports)
  3. SUPPORTED_BUSINESS_QUERY -- everything else, handed to the normal
     intent router
Nothing here can itself grant or deny data access -- a SENSITIVE_REQUEST
classification means the assistant refuses to even attempt an answer, it
does not mean "answer minus the sensitive field."
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class SafetyCategory(StrEnum):
    SUPPORTED_BUSINESS_QUERY = "SUPPORTED_BUSINESS_QUERY"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    SENSITIVE_REQUEST = "SENSITIVE_REQUEST"


@dataclass(frozen=True)
class SafetyClassification:
    category: SafetyCategory
    matched_rule: str | None = None


# Verbatim copy from assistant_chatgpt_like_v31.py's SENSITIVE_PATTERNS --
# see this module's own docstring for why this is a copy, not an import.
_SENSITIVE_PATTERNS: tuple[str, ...] = (
    r"(?=.*\b(goster|göster|gostermek|göstermek|ver|ac|aç|goruntule|görüntüle|goruntulemek|görüntülemek|gormek|görmek|bak|listele|paylas|paylaş|oku|indir|kopyala)\b)(?=.*\b(performans\s+puan\w*|performans\s+sonuc\w*|puan\w*|notun\w*|notunu\w*|karnesin\w*|karne\w*|amir\s+gorus\w*|amir\s+görüş\w*|yonetici\s+gorus\w*|yönetici\s+görüş\w*|anket\s+cevab\w*|anket\s+cevap\w*|anket\s+yanit\w*|anket\s+yanıt\w*|mesaj\s+icerig\w*|mesaj\s+içerig\w*|mesaj\s+içeriğ\w*|mesaj\s+metn\w*|mesaj\s+yazism\w*|mesaj\s+yazışm\w*|mesajlar\w*|ozel\s+mesaj\w*|özel\s+mesaj\w*|tc\b|kimlik\s+no\w*|telefon\w*|adres\w*|maas\w*|maaş\w*|dogum\s+tarih\w*|doğum\s+tarih\w*)\b).*",
    r"\b(performans puani belirle|performans puanı belirle|isimi sonlandir|işimi sonlandır|isten cikar|işten çıkar|idari karar ver)\b",
    r"\b(kim ne yazmis|kim ne yazmış|ozel mesaj|özel mesaj)\b",
)

# Verbatim copy from assistant_chatgpt_like_v31.py's OUT_OF_SCOPE_HINTS.
_OUT_OF_SCOPE_HINTS: tuple[str, ...] = (
    "hava durumu", "borsa", "dolar", "euro", "haber", "film", "yemek tarifi", "siyaset", "futbol", "magazin",
)

# BYS360's own "günlük bilgilendirme e-postası" feature is genuinely named
# using the words "hava durumu" (it includes a daily weather section) --
# a real, in-scope admin query like "Günlük hava durumu e-posta ayarlarını
# göster" was being misclassified OUT_OF_SCOPE by the "hava durumu" hint
# above (mandate: post-production live defect, weather-mail intent/
# routing). This is a narrow, explicit co-occurrence exception for that
# ONE hint only -- it does not loosen OUT_OF_SCOPE detection for genuine
# weather chit-chat ("bugün hava durumu nasıl", with none of these
# markers present), and none of the other hints (borsa/dolar/euro/haber/
# film/yemek tarifi/siyaset/futbol/magazin) are touched.
_HAVA_DURUMU_FEATURE_CONTEXT_MARKERS: tuple[str, ...] = ("e-posta", "eposta", "mail", "ayar", "yapilandirma")


def _normalize(text: str) -> str:
    text = str(text or "").strip().lower()
    return (
        text.replace("ı", "i").replace("İ", "i").replace("ş", "s").replace("ğ", "g")
        .replace("ü", "u").replace("ö", "o").replace("ç", "c")
    )


def classify(text: str) -> SafetyClassification:
    normalized = _normalize(text)
    if not normalized:
        return SafetyClassification(category=SafetyCategory.SUPPORTED_BUSINESS_QUERY)

    for pattern in _SENSITIVE_PATTERNS:
        if re.search(pattern, normalized):
            return SafetyClassification(category=SafetyCategory.SENSITIVE_REQUEST, matched_rule=pattern)

    for hint in _OUT_OF_SCOPE_HINTS:
        if hint not in normalized:
            continue
        if hint == "hava durumu" and any(marker in normalized for marker in _HAVA_DURUMU_FEATURE_CONTEXT_MARKERS):
            continue
        return SafetyClassification(category=SafetyCategory.OUT_OF_SCOPE, matched_rule=hint)

    return SafetyClassification(category=SafetyCategory.SUPPORTED_BUSINESS_QUERY)


__all__ = ["SafetyCategory", "SafetyClassification", "classify"]
