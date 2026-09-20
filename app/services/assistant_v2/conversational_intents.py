"""BYS360 Assistant V2 -- native conversational intents (mandate Phase E/F).

Deterministic, table-driven recognition of six conversational intents that
are NOT business capability queries: GREETING, HELP, THANKS,
ASSISTANT_IDENTITY, CAPABILITY_EXPLANATION, and (as a fallback classification
returned here rather than in safety_classifier.py) NONE when nothing
matches. These never route through capability_dispatcher -- there is no
authorization check for "hello", and a conversational answer never contains
BYS360 business data, so composing one needs no capability result at all.

This module is checked only AFTER safety_classifier.classify() has already
returned SUPPORTED_BUSINESS_QUERY (see service.py's ordering) -- a
sensitive/out-of-scope request is decided once, by that classifier, not
re-litigated here.

Response text is generated entirely by this module (BYS360 Native Response
Engine, no external AI) -- see ASSISTANT_IDENTITY_ANSWER for the
institutional (never individual-developer) identity wording the mandate
requires.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

ASSISTANT_IDENTITY_ANSWER = (
    "Ben BYS360 Kurumsal Asistanı'yım. BYS360 modülleri, yetkileriniz ve sistemde erişebildiğiniz "
    "bilgiler üzerinden size yardımcı olurum. Teknik olarak BYS360 AI Core tarafından çalıştırılırım: "
    "harici bir yapay zekâ servisi veya üçüncü taraf dil modeli kullanmadan, BYS360'ın kendi modül, "
    "yetki, veri erişimi, alan sözlüğü, kural ve ilişki motorları üzerinden doğal dil sorularınızı çözerim."
)

CAPABILITY_EXPLANATION_ANSWER = (
    "BYS360 içinde yetkiniz dahilindeki modüller hakkında sorular sorabilirsiniz -- örneğin personel "
    "kayıtları, performans dönemleri ve değerlendirmeleri, portal duyuruları, anketler, destek talepleri, "
    "bildirimler ve daha fazlası. Yalnızca erişim yetkiniz olan verileri gösteririm; hassas kişisel veri "
    "göstermem, idari karar vermem ve performans puanı belirlemem."
)

_HELP_ANSWER = (
    "Buradayım. BYS360 içinde yapmak istediğiniz işlemi yazabilirsiniz -- örneğin \"personel listele\", "
    "\"aktif performans dönemlerini göster\" veya \"destek taleplerimi göster\" gibi. Yetkiniz olan modüller "
    "hakkında ne sorabileceğimi öğrenmek için \"neler yapabilirsin?\" diyebilirsiniz."
)

_THANKS_ANSWER = "Rica ederim. Başka bir konuda yardımcı olabileceğim bir şey varsa yazabilirsiniz."


class ConversationalIntent(StrEnum):
    NONE = "NONE"
    GREETING = "GREETING"
    HELP = "HELP"
    THANKS = "THANKS"
    ASSISTANT_IDENTITY = "ASSISTANT_IDENTITY"
    CAPABILITY_EXPLANATION = "CAPABILITY_EXPLANATION"


@dataclass(frozen=True)
class ConversationalMatch:
    intent: ConversationalIntent
    answer: str | None = None


def _normalize(text: str) -> str:
    text = str(text or "").strip().lower()
    return (
        text.replace("ı", "i").replace("İ", "i").replace("ş", "s").replace("ğ", "g")
        .replace("ü", "u").replace("ö", "o").replace("ç", "c")
    )


# Checked in this fixed order -- identity/capability-explanation before the
# broader greeting pattern, since "sen nesin" could otherwise be caught by a
# looser greeting regex.
_RULES: tuple[tuple[re.Pattern[str], ConversationalIntent], ...] = (
    (re.compile(r"\b(seni kim|kim gelistirdi|kim yapti|gelistiren kim|sen ne|sen nesin|nesin sen)\b"), ConversationalIntent.ASSISTANT_IDENTITY),
    (re.compile(r"\b(neler yapabilirsin|ne yaparsin|ne ise yararsin|hangi konularda yardimci)\b"), ConversationalIntent.CAPABILITY_EXPLANATION),
    (re.compile(r"\b(tesekkur|sagol|sagolun|elinize saglik)\b"), ConversationalIntent.THANKS),
    (re.compile(r"\b(yardim et|yardimci olur musun|nasil kullanilir|ne yapmaliyim)\b"), ConversationalIntent.HELP),
    (re.compile(r"\b(selam|merhaba|gunaydin|iyi aksamlar|iyi gunler|iyi geceler)\b"), ConversationalIntent.GREETING),
)

_ANSWERS: dict[ConversationalIntent, str] = {
    ConversationalIntent.ASSISTANT_IDENTITY: ASSISTANT_IDENTITY_ANSWER,
    ConversationalIntent.CAPABILITY_EXPLANATION: CAPABILITY_EXPLANATION_ANSWER,
    ConversationalIntent.THANKS: _THANKS_ANSWER,
    ConversationalIntent.HELP: _HELP_ANSWER,
    ConversationalIntent.GREETING: (
        "Merhaba. BYS360 içinde hangi işlemde yardımcı olabilirim? Örneğin personel, performans, "
        "portal, anket veya destek talepleriyle ilgili bir soru sorabilirsiniz."
    ),
}


def detect(text: str) -> ConversationalMatch:
    normalized = _normalize(text)
    if not normalized:
        return ConversationalMatch(intent=ConversationalIntent.NONE)
    for pattern, intent in _RULES:
        if pattern.search(normalized):
            return ConversationalMatch(intent=intent, answer=_ANSWERS[intent])
    return ConversationalMatch(intent=ConversationalIntent.NONE)


__all__ = [
    "ConversationalIntent",
    "ConversationalMatch",
    "ASSISTANT_IDENTITY_ANSWER",
    "CAPABILITY_EXPLANATION_ANSWER",
    "detect",
]
