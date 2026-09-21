"""BYS360 Assistant V2 -- structured domain vocabulary / ontology.

A `ModuleVocabulary` entry per module, keyed by the SAME `module_key` values
`app.services.settings.module_registry.MODULE_REGISTRY` already defines
(`test_every_module_vocabulary_key_exists_in_module_registry` enforces
this) -- this is deliberately additive metadata on top of the existing
module registry, not a second, independent module list (the project's own
stance against scattered/duplicated registries).

`core_terms` are the base Turkish words for a module's domain; `synonym_map`
gives, per core term, the common variants/synonyms a real user might type.
`intent_router.py` uses `expand_query_tokens()` (built from this file) to
widen a raw query's token set with synonyms and a light, conservative
suffix-stripped form before scoring against capability `intent_tags` --
this is the "tied to capability/module metadata rather than scattered
strings" requirement: the vocabulary lives in ONE place, keyed by the same
module_key every capability already carries.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_TOKEN_RE = re.compile(r"[a-zçğıöşü0-9]+", re.IGNORECASE)

# A small, conservative list of common Turkish suffixes, longest-first, used
# ONLY to derive an additional candidate token for matching (never to
# replace the original token) -- deliberately not a real morphological
# analyzer. Stripping is applied at most once per token and only when the
# remaining stem is at least 3 characters, to avoid over-stripping short
# words into meaningless fragments.
#
# "mı"/"mi"/"mu"/"mü" and "m" (1st-person singular possessive, e.g.
# "kotam" -> "kota", "kotamı" -> "kota") were added as a real gap found by
# testing: a query like "dosya kotam ne kadar?" scored zero extra points
# against the "quota" tag because "kotam"/"kotamı" never reduced to the
# bare "kota" the tag's canonical-form bridge expands to. Placed before
# the shorter existing single-letter suffixes so "kotamı" strips to
# "kota" in one step rather than the incomplete "kotam".
_SUFFIXES = (
    "lerinden", "larından", "lerinde", "larında", "lerini", "larını",
    "lerin", "ların", "leri", "ları", "nden", "ndan", "deki", "daki",
    "nin", "nın", "nun", "nün", "ler", "lar", "den", "dan", "de", "da",
    "in", "ın", "un", "ün", "mı", "mi", "mu", "mü",
    "i", "ı", "u", "ü", "m",
)


def _strip_light_suffix(token: str) -> str | None:
    for suffix in _SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[: -len(suffix)]
    return None


_ASCII_FOLD_MAP = str.maketrans(
    {"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u", "i": "i"}
)


def _ascii_fold(token: str) -> str:
    """Strips Turkish diacritics for a supplementary, diacritics-insensitive
    match (ö/o, ü/u, ş/s, ç/c, ğ/g, ı/i all fold together). This exists
    because real data in this codebase (capability intent_tags, older
    content) is not always consistently accented -- e.g. "dönem" vs
    "donem" -- and a user's own typed query may not be either. This is
    ADDITIVE: exact Turkish tokens are always tried first via the plain
    token set; ascii-folded forms only widen the match, never replace the
    original token."""
    return token.translate(_ASCII_FOLD_MAP)


@dataclass(frozen=True)
class ModuleVocabulary:
    module_key: str
    core_terms: tuple[str, ...]
    synonym_map: dict[str, tuple[str, ...]] = field(default_factory=dict)


MODULE_VOCABULARIES: tuple[ModuleVocabulary, ...] = (
    ModuleVocabulary(
        module_key="personnel_hr",
        core_terms=("personel", "çalışan", "birim", "izin", "sicil", "görev", "unvan"),
        synonym_map={
            "personel": ("çalışan", "çalışanlar", "personeller", "kişi"),
            "birim": ("departman", "bölüm", "ekip"),
            "izin": ("izinler", "izin talebi", "izin talepleri"),
        },
    ),
    ModuleVocabulary(
        module_key="performance_mgmt",
        core_terms=("performans", "değerlendirme", "dönem", "puan", "hedef", "toplantı", "kpi"),
        synonym_map={
            "değerlendirme": ("değerlendirmeler", "değerlendirilme", "skor"),
            "dönem": ("periyot", "sezon"),
            "tamamlanmamış": ("eksik", "bekleyen", "tamamlanmayan"),
        },
    ),
    ModuleVocabulary(
        module_key="portal",
        core_terms=("portal", "haber", "duyuru", "içerik", "yayın", "gönderi"),
        synonym_map={
            "duyuru": ("duyurular", "bildirim metni"),
            "haber": ("haberler", "içerik"),
        },
    ),
    ModuleVocabulary(
        module_key="file_center",
        core_terms=("dosya", "belge", "doküman", "klasör", "kota"),
        synonym_map={
            "dosya": ("dosyalar", "belgeler"),
            "belge": ("doküman", "evrak"),
        },
    ),
    ModuleVocabulary(
        module_key="communication",
        core_terms=("iletişim", "duyuru", "mesaj", "bildirim"),
        synonym_map={
            "mesaj": ("mesajlar", "yazışma"),
        },
    ),
    ModuleVocabulary(
        module_key="surveys",
        core_terms=("anket", "soru", "cevap", "katılım", "sonuç"),
        synonym_map={
            "anket": ("anketler", "form"),
            "katılım": ("yanıt", "yanıtlar"),
        },
    ),
    ModuleVocabulary(
        module_key="support_help",
        core_terms=("destek", "talep", "kayıt", "sorun", "yardım", "makale"),
        synonym_map={
            "talep": ("talepler", "bilet", "ticket"),
            "destek": ("yardım", "servis masası"),
        },
    ),
    ModuleVocabulary(
        module_key="ai_decision_support",
        core_terms=("öneri", "karar", "analiz"),
        synonym_map={
            "öneri": ("öneriler", "tavsiye"),
        },
    ),
    ModuleVocabulary(
        module_key="virtual_assistant",
        core_terms=("asistan", "yetenek", "modül"),
        synonym_map={
            "yetenek": ("yetenekler", "kapasite"),
        },
    ),
    ModuleVocabulary(
        module_key="dashboard",
        core_terms=("dashboard", "panel", "özet", "widget"),
        synonym_map={},
    ),
    ModuleVocabulary(
        module_key="settings_auth",
        core_terms=("ayar", "yetki", "rol", "menü"),
        synonym_map={
            "yetki": ("izin", "yetkilendirme"),
        },
    ),
    ModuleVocabulary(
        module_key="notifications",
        core_terms=("bildirim", "okunmamış", "uyarı"),
        synonym_map={
            "bildirim": ("bildirimler", "uyarılar"),
        },
    ),
    ModuleVocabulary(
        module_key="email_automation",
        core_terms=("e-posta", "mail", "otomasyon", "gönderim"),
        synonym_map={
            "mail": ("e-posta", "eposta"),
        },
    ),
    ModuleVocabulary(
        module_key="scheduled_jobs",
        core_terms=("zamanlanmış", "iş", "görev", "otomasyon"),
        synonym_map={},
    ),
    ModuleVocabulary(
        module_key="security_session",
        core_terms=("güvenlik", "oturum", "captcha", "politika"),
        synonym_map={},
    ),
    ModuleVocabulary(
        module_key="audit",
        core_terms=("değişiklik", "kayıt", "geçmiş", "denetim"),
        synonym_map={
            "değişiklik": ("değişiklikler", "revizyon"),
        },
    ),
)

# A number of capability `intent_tags` in the registry were written in
# English (e.g. "personnel", "hr", "performance", "period", "record",
# "list") rather than Turkish -- a real gap discovered by testing, not a
# hypothetical one: a Turkish query like "personel listele" scored zero
# against a tag set of ("personnel", "hr", "list", "directory") with no
# bridge between "personel" and "personnel". This maps every known EN/TR
# variant of a concept to exactly ONE shared canonical token (deliberately
# NOT a symmetric "expand to every sibling synonym" fan-out -- an earlier
# version of this bridge did that and caused "hr" and "personnel" to each
# independently re-expand to include the other plus every other synonym,
# which inflated the shared module-level tags identically across every
# capability in a module and drowned out the tags that actually
# differentiate them). Both the query and each tag get the SAME one-token
# canonicalization, so they still overlap correctly without the fan-out.
_CANONICAL_FORM: dict[str, str] = {
    "personnel": "personel", "hr": "personel", "staff": "personel", "employee": "personel",
    "performance": "performans", "period": "dönem", "evaluation": "değerlendirme",
    "record": "kayıt", "list": "liste", "listele": "liste", "directory": "liste",
    "search": "arama", "read": "oku", "lookup": "bul", "summary": "özet", "discover": "keşfet",
    "portal": "portal", "post": "gönderi", "posts": "gönderiler", "moderation": "moderasyon",
    "file_center": "dosya", "file": "dosya", "quota": "kota", "storage": "depolama", "scan": "tarama",
    "communication": "iletişim", "announcement": "duyuru", "message": "mesaj", "messages": "mesajlar",
    "survey": "anket", "surveys": "anketler", "result": "sonuç", "results": "sonuçlar",
    "support": "destek", "ticket": "talep", "tickets": "talepler", "article": "makale", "help": "yardım",
    "recommendation": "öneri", "recommendations": "öneriler", "usage": "kullanım", "governance": "yönetişim",
    "assistant": "asistan", "capability": "yetenek", "capabilities": "yetenekler", "module": "modül", "modules": "modüller",
    "dashboard": "panel", "widget": "widget",
    "settings": "ayar", "role": "rol", "menu": "menü", "permission": "yetki", "override": "geçersiz",
    "coverage": "kapsam",
    "notification": "bildirim", "notifications": "bildirimler", "unread": "okunmamış",
    "email": "e-posta", "automation": "otomasyon", "reminder": "hatırlatma", "health": "sağlık",
    "scheduled_jobs": "zamanlanmış", "job": "iş", "digest": "özet",
    "security": "güvenlik", "session": "oturum", "policy": "politika", "captcha": "captcha",
    "audit": "denetim", "change": "değişiklik", "log": "kayıt", "detail": "detay",
    "pending": "bekleyen", "incomplete": "tamamlanmamış", "self": "kendi", "explain": "açıkla",
}


_BY_MODULE_KEY = {v.module_key: v for v in MODULE_VOCABULARIES}


def get_module_vocabulary(module_key: str) -> ModuleVocabulary | None:
    return _BY_MODULE_KEY.get(module_key)


def _normalize_tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall((text or "").lower()))


def expand_query_tokens(text: str) -> set[str]:
    """Tokenizes `text`, then widens the token set with:
      1. each token's light-suffix-stripped stem (if any), and
      2. any synonym-map entry whose key OR whose synonym variants overlap
         a token already present.
    This is used by `intent_router.py` before scoring against capability
    `intent_tags`, so a query like "çalışanları listele" also matches tags
    written around "personel" without needing every synonym spelled out on
    every single capability."""
    tokens = _normalize_tokens(text)
    if not tokens:
        return tokens
    expanded = set(tokens)
    for token in tokens:
        stem = _strip_light_suffix(token)
        if stem:
            expanded.add(stem)
    # Ascii-fold every token/stem found so far (additive, see _ascii_fold's
    # own docstring for why) -- done as a separate pass over a snapshot so
    # folding a fold is a no-op rather than compounding.
    for token in tuple(expanded):
        expanded.add(_ascii_fold(token))
    # Bridge English <-> Turkish tag words to one shared canonical token
    # (see _CANONICAL_FORM's own comment for why this is one-directional-
    # per-token rather than a symmetric synonym fan-out).
    for token in tuple(expanded):
        canonical = _CANONICAL_FORM.get(token)
        if canonical:
            expanded.add(canonical)
    for vocabulary in MODULE_VOCABULARIES:
        for core_term, variants in vocabulary.synonym_map.items():
            term_tokens = _normalize_tokens(core_term)
            for variant in variants:
                variant_tokens = _normalize_tokens(variant)
                if variant_tokens & expanded:
                    expanded |= term_tokens
                if term_tokens & expanded:
                    expanded |= variant_tokens
    return expanded


__all__ = [
    "ModuleVocabulary",
    "MODULE_VOCABULARIES",
    "get_module_vocabulary",
    "expand_query_tokens",
]
