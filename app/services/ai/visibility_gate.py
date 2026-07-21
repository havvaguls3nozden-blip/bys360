from __future__ import annotations

from app.core.datetime_utils import utc_now

"""Faz 10: AI yetki, KVKK maskeleme ve güvenli görünürlük kapısı.

Bu servis yalnızca okuma yapar. AI ekranlarının hangi rol için hangi kapsamda
okunabileceğini, KVKK maskeleme zorunluluğunu ve güvenli export sınırını
tek yerde tanımlar. Ham istem/yanıt metni döndürmez, öneri uygulamaz, kayıt
oluşturmaz, kayıt güncellemez ve nihai idari karar vermez.
"""

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func

from app.extensions import db
from app.models import (
    AIRecommendation,
    AIRedactionRule,
    AIRequestLog,
    RoleMenuDefault,
    User,
    UserMenuPermission,
)
from app.services.ai.module_scope import filter_visible_values, is_visible_ai_module

# Faz 10 güvenlik sözleşmesi
DB_WRITE_ENABLED = False
AI_FINAL_DECISION_ENABLED = False
AI_AUTO_APPLY_ENABLED = False
RAW_AI_PAYLOAD_VISIBLE = False
RAW_AI_EXPORT_ENABLED = False
SAFE_CSV_EXPORT_ENABLED = True
KVKK_MASKING_REQUIRED = True
PERSONAL_DATA_EXPORT_ENABLED = False
HUMAN_REVIEW_REQUIRED = True
DEFAULT_LOOKBACK_DAYS = 30
MAX_LOOKBACK_DAYS = 180

AI_MENU_KEY = "ai_center"
SLOW_LATENCY_MS = 1800
LIVE_MODULE_ORDER = ("performance", "hr", "survey", "feedback", "communication", "support", "analysis_center", "dashboard")
REMOVED_MODULES = ("education", "strategy", "repository", "portal")
SENSITIVE_FIELD_ALIASES = (
    "tc",
    "tckn",
    "kimlik",
    "sicil",
    "telefon",
    "phone",
    "gsm",
    "email",
    "e-posta",
    "iban",
    "ad",
    "soyad",
    "full_name",
    "personel",
    "adres",
)
MODULE_LABELS = {
    "performance": "Performans",
    "hr": "Personel / İzin",
    "survey": "Anket",
    "feedback": "Geri Bildirim / Nabız",
    "communication": "İletişim",
    "support": "Yardım Merkezi",
    "analysis_center": "Analiz Merkezi",
    "dashboard": "Dashboard",
    "general": "Genel",
    "": "Genel",
}
ROLE_LABELS = {
    "admin": "Admin",
    "baskan": "Başkan",
    "baskan_yardimcisi": "Başkan Yardımcısı",
    "grup_baskani": "Grup Başkanı",
    "mali_musavir": "Mali Müşavir",
    "koordinator": "Koordinatör",
    "birim_sorumlusu": "Birim Sorumlusu",
    "personel": "Personel",
}

# Görünürlük politikası: ham AI metin hiçbir rolde açılmaz. CSV yalnız güvenli matris verir.
ROLE_POLICIES: dict[str, dict[str, Any]] = {
    "admin": {
        "scope": "tam_yonetisim",
        "can_view_ai_center": True,
        "can_export_safe_csv": True,
        "can_view_operational_counts": True,
        "visible_modules": LIVE_MODULE_ORDER,
        "row_limit": 1000,
        "masking_mode": "strict",
        "note": "Tüm canlı AI yönetişim panellerini ham metinsiz izler.",
    },
    "baskan": {
        "scope": "kurumsal_ozet",
        "can_view_ai_center": True,
        "can_export_safe_csv": True,
        "can_view_operational_counts": True,
        "visible_modules": LIVE_MODULE_ORDER,
        "row_limit": 500,
        "masking_mode": "strict",
        "note": "Kurumsal özet, risk ve öncelik görünürlüğü vardır; ham kişisel veri görünmez.",
    },
    "baskan_yardimcisi": {
        "scope": "kurumsal_ozet",
        "can_view_ai_center": True,
        "can_export_safe_csv": True,
        "can_view_operational_counts": True,
        "visible_modules": LIVE_MODULE_ORDER,
        "row_limit": 500,
        "masking_mode": "strict",
        "note": "Yönetsel özet ve modül risklerini görür; ham AI payload kapalıdır.",
    },
    "grup_baskani": {
        "scope": "yonetsel_modul_ozeti",
        "can_view_ai_center": True,
        "can_export_safe_csv": False,
        "can_view_operational_counts": True,
        "visible_modules": ("performance", "hr", "feedback", "survey", "support", "dashboard"),
        "row_limit": 250,
        "masking_mode": "strict",
        "note": "Yönetsel modül özetlerini görür; dışa aktarım kapalıdır.",
    },
    "mali_musavir": {
        "scope": "kurumsal_ozet",
        "can_view_ai_center": True,
        "can_export_safe_csv": True,
        "can_view_operational_counts": True,
        "visible_modules": LIVE_MODULE_ORDER,
        "row_limit": 500,
        "masking_mode": "strict",
        "note": "Admin ailesi seviyesinde güvenli özet ve matris çıktısı alabilir.",
    },
    "koordinator": {
        "scope": "sinirli_yonetsel_ozet",
        "can_view_ai_center": False,
        "can_export_safe_csv": False,
        "can_view_operational_counts": False,
        "visible_modules": ("performance", "feedback", "survey", "support"),
        "row_limit": 100,
        "masking_mode": "strict",
        "note": "AI merkezine doğrudan erişim kapalı; ileride yönetici özetleri ayrı verilebilir.",
    },
    "birim_sorumlusu": {
        "scope": "sinirli_birim_ozeti",
        "can_view_ai_center": False,
        "can_export_safe_csv": False,
        "can_view_operational_counts": False,
        "visible_modules": ("support", "feedback"),
        "row_limit": 50,
        "masking_mode": "strict",
        "note": "AI merkezine erişim kapalı; yalnız modül içi güvenli özet yaklaşımı desteklenir.",
    },
    "personel": {
        "scope": "kisisel_sonuc_yok",
        "can_view_ai_center": False,
        "can_export_safe_csv": False,
        "can_view_operational_counts": False,
        "visible_modules": tuple(),
        "row_limit": 0,
        "masking_mode": "deny",
        "note": "Personel rolünde AI yönetim ekranı ve export kapalıdır.",
    },
}

_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_IBAN_RE = re.compile(r"\bTR\d{2}[\s\d]{10,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?90\s*)?0?5\d{2}[\s\-.]?\d{3}[\s\-.]?\d{2}[\s\-.]?\d{2}(?!\d)")
_TCKN_RE = re.compile(r"(?<!\d)[1-9]\d{10}(?!\d)")
_SICIL_RE = re.compile(r"(?i)\b(sicil\s*(?:no|numarası|numarasi)?\s*[:#-]?\s*)([A-Z0-9-]{3,20})\b")


@dataclass(frozen=True)
class ModuleVisibilitySignal:
    module_type: str
    request_total: int = 0
    masked_total: int = 0
    unmasked_total: int = 0
    user_visible_total: int = 0
    failed_total: int = 0
    warning_total: int = 0
    slow_total: int = 0
    active_redaction_rules: int = 0
    open_recommendations: int = 0


def _safe_int(value: Any, default: int, minimum: int = 1, maximum: int = MAX_LOOKBACK_DAYS) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    return max(min(parsed, maximum), minimum)


def _clean_key(value: Any, fallback: str = "general") -> str:
    text = str(value or "").strip().lower()
    return text or fallback


def _role_key(user_or_role: Any) -> str:
    if isinstance(user_or_role, str):
        return _clean_key(user_or_role, "personel")
    return _clean_key(getattr(user_or_role, "role", ""), "personel")


def _role_label(role_key: str) -> str:
    return ROLE_LABELS.get(role_key, role_key.replace("_", " ").title())


def _module_label(module_type: Any) -> str:
    key = _clean_key(module_type)
    return MODULE_LABELS.get(key, key.replace("_", " ").title())


def _visible_module_filter(query, column):
    hidden = [key for key in REMOVED_MODULES if not is_visible_ai_module(key)]
    if not hidden:
        return query
    return query.filter(func.lower(func.coalesce(column, "")).notin_(hidden))


def _rollback() -> None:
    try:
        db.session.rollback()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai/visibility_gate.py")
def _safe_count(query) -> int:
    try:
        return int(query.count() or 0)
    except Exception:
        _rollback()
        return 0


def _safe_rows(query, limit: int = 5000) -> list[Any]:
    try:
        return query.limit(limit).all()
    except Exception:
        _rollback()
        return []


def _policy_for_role(role: str) -> dict[str, Any]:
    role_key = _clean_key(role, "personel")
    base = dict(ROLE_POLICIES.get(role_key) or ROLE_POLICIES["personel"])
    base["role"] = role_key
    base["role_label"] = _role_label(role_key)
    base["visible_modules"] = filter_visible_values(base.get("visible_modules") or [])
    base["raw_payload_visible"] = RAW_AI_PAYLOAD_VISIBLE
    base["raw_export_enabled"] = RAW_AI_EXPORT_ENABLED
    base["kvkk_masking_required"] = KVKK_MASKING_REQUIRED
    base["personal_data_export_enabled"] = PERSONAL_DATA_EXPORT_ENABLED
    base["human_review_required"] = HUMAN_REVIEW_REQUIRED
    return base


def get_ai_visibility_policy(user: Any) -> dict[str, Any]:
    """Kullanıcının AI görünürlük politikasını döndürür; veri yazmaz."""
    return _policy_for_role(_role_key(user))


def mask_sensitive_text(value: Any, *, field_name: str = "", role: str = "") -> str:
    """KVKK güvenli metin maskeleme yardımcısı.

    Ham AI request/response ekranlara taşınmaz; bu yardımcı yalnız kısa not,
    başlık ve export alanları için savunmacı maskeleme uygular.
    """
    if value is None:
        return ""
    text = str(value)
    if not text:
        return ""
    key = _clean_key(field_name, "")
    role_key = _clean_key(role, "personel")
    if role_key == "personel":
        return "•••"
    text = _EMAIL_RE.sub("[e-posta maskeli]", text)
    text = _IBAN_RE.sub("[iban maskeli]", text)
    text = _PHONE_RE.sub("[telefon maskeli]", text)
    text = _TCKN_RE.sub("[kimlik maskeli]", text)
    text = _SICIL_RE.sub(lambda m: f"{m.group(1)}[sicil maskeli]", text)
    if any(alias in key for alias in SENSITIVE_FIELD_ALIASES):
        return "[KVKK alanı maskeli]"
    return " ".join(text.replace("\r", " ").replace("\n", " ").split())[:240]


def _role_matrix(role_filter: str = "") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    roles = [role_filter] if role_filter else list(ROLE_POLICIES)
    for role in roles:
        policy = _policy_for_role(role)
        rows.append(
            {
                "role": policy["role"],
                "role_label": policy["role_label"],
                "scope": policy["scope"],
                "can_view_ai_center": policy["can_view_ai_center"],
                "can_export_safe_csv": policy["can_export_safe_csv"],
                "raw_payload_visible": policy["raw_payload_visible"],
                "raw_export_enabled": policy["raw_export_enabled"],
                "kvkk_masking_required": policy["kvkk_masking_required"],
                "visible_modules": policy["visible_modules"],
                "visible_module_labels": [_module_label(value) for value in policy["visible_modules"]],
                "row_limit": policy["row_limit"],
                "note": policy["note"],
                "tone": "success" if policy["can_view_ai_center"] else "muted",
            }
        )
    return rows


def _menu_permission_rows() -> list[dict[str, Any]]:
    role_defaults: dict[str, bool] = {}
    user_overrides: Counter[str] = Counter()
    try:
        for role_name, visible in (
            db.session.query(RoleMenuDefault.role_name, RoleMenuDefault.is_visible)
            .filter(RoleMenuDefault.menu_key == AI_MENU_KEY)
            .limit(200)
            .all()
        ):
            role_defaults[_clean_key(role_name, "personel")] = bool(visible)
    except Exception:
        _rollback()
    try:
        for visible, count in (
            db.session.query(UserMenuPermission.is_visible, func.count(UserMenuPermission.id))
            .filter(UserMenuPermission.menu_key == AI_MENU_KEY)
            .group_by(UserMenuPermission.is_visible)
            .limit(20)
            .all()
        ):
            user_overrides["visible" if visible else "hidden"] += int(count or 0)
    except Exception:
        _rollback()

    rows = []
    for role in ROLE_POLICIES:
        policy = _policy_for_role(role)
        configured = role_defaults.get(role)
        rows.append(
            {
                "role": role,
                "role_label": _role_label(role),
                "policy_visible": policy["can_view_ai_center"],
                "configured_visible": configured,
                "state_label": "Uyumlu" if configured is None or configured == policy["can_view_ai_center"] else "Kontrol gerekli",
                "tone": "success" if configured is None or configured == policy["can_view_ai_center"] else "warning",
            }
        )
    return [
        {
            "override_visible": int(user_overrides.get("visible", 0)),
            "override_hidden": int(user_overrides.get("hidden", 0)),
            "rows": rows,
        }
    ]


def _user_role_counts() -> dict[str, int]:
    counts = {role: 0 for role in ROLE_POLICIES}
    try:
        for role, count in (
            db.session.query(User.role, func.count(User.id))
            .filter(User.is_active.is_(True))
            .group_by(User.role)
            .limit(100)
            .all()
        ):
            key = _clean_key(role, "personel")
            counts[key] = counts.get(key, 0) + int(count or 0)
    except Exception:
        _rollback()
    return counts


def _redaction_counter(module_filter: str = "") -> Counter[str]:
    counter: Counter[str] = Counter()
    try:
        query = AIRedactionRule.query.filter(AIRedactionRule.is_active.is_(True))
        query = _visible_module_filter(query, AIRedactionRule.module_type)
        if module_filter:
            query = query.filter(func.lower(AIRedactionRule.module_type) == module_filter)
        for module, count in query.with_entities(AIRedactionRule.module_type, func.count(AIRedactionRule.id)).group_by(AIRedactionRule.module_type).all():
            counter[_clean_key(module)] += int(count or 0)
    except Exception:
        _rollback()
    return counter


def _recommendation_counter(since: datetime, module_filter: str = "") -> Counter[str]:
    counter: Counter[str] = Counter()
    try:
        query = AIRecommendation.query.filter(AIRecommendation.created_at >= since, func.lower(AIRecommendation.status) == "open")
        query = _visible_module_filter(query, AIRecommendation.module_type)
        if module_filter:
            query = query.filter(func.lower(AIRecommendation.module_type) == module_filter)
        for module, count in query.with_entities(AIRecommendation.module_type, func.count(AIRecommendation.id)).group_by(AIRecommendation.module_type).all():
            counter[_clean_key(module)] += int(count or 0)
    except Exception:
        _rollback()
    return counter


def _module_signals(since: datetime, module_filter: str = "") -> list[ModuleVisibilitySignal]:
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    try:
        query = AIRequestLog.query.filter(AIRequestLog.created_at >= since)
        query = _visible_module_filter(query, AIRequestLog.module_type)
        if module_filter:
            query = query.filter(func.lower(AIRequestLog.module_type) == module_filter)
        rows = query.with_entities(
            AIRequestLog.module_type,
            AIRequestLog.status,
            AIRequestLog.was_masked,
            AIRequestLog.was_user_visible,
            AIRequestLog.latency_ms,
        ).limit(5000).all()
    except Exception:
        _rollback()
        rows = []

    for module, status, was_masked, was_user_visible, latency_ms in rows:
        key = _clean_key(module)
        status_key = _clean_key(status, "completed")
        grouped[key]["request_total"] += 1
        if was_masked is True:
            grouped[key]["masked_total"] += 1
        if was_masked is False:
            grouped[key]["unmasked_total"] += 1
        if was_user_visible is True:
            grouped[key]["user_visible_total"] += 1
        if status_key in {"failed", "error"}:
            grouped[key]["failed_total"] += 1
        if status_key == "warning":
            grouped[key]["warning_total"] += 1
        if latency_ms is not None and int(latency_ms or 0) >= SLOW_LATENCY_MS:
            grouped[key]["slow_total"] += 1

    redaction = _redaction_counter(module_filter)
    recommendations = _recommendation_counter(since, module_filter)
    keys = set(grouped) | set(redaction) | set(recommendations)
    if module_filter:
        keys.add(module_filter)
    if not keys:
        for visible_key in filter_visible_values(LIVE_MODULE_ORDER):
            keys.add(visible_key)

    signals = []
    for key in sorted(keys, key=lambda x: (LIVE_MODULE_ORDER.index(x) if x in LIVE_MODULE_ORDER else 99, _module_label(x))):
        values = grouped[key]
        signals.append(
            ModuleVisibilitySignal(
                module_type=key,
                request_total=int(values.get("request_total") or 0),
                masked_total=int(values.get("masked_total") or 0),
                unmasked_total=int(values.get("unmasked_total") or 0),
                user_visible_total=int(values.get("user_visible_total") or 0),
                failed_total=int(values.get("failed_total") or 0),
                warning_total=int(values.get("warning_total") or 0),
                slow_total=int(values.get("slow_total") or 0),
                active_redaction_rules=int(redaction.get(key, 0)),
                open_recommendations=int(recommendations.get(key, 0)),
            )
        )
    return signals


def _risk_score(signal: ModuleVisibilitySignal) -> int:
    score = 0
    score += min(signal.unmasked_total * 18, 54)
    score += min(signal.user_visible_total * 2, 20)
    score += min(signal.failed_total * 6, 24)
    score += min(signal.warning_total * 4, 16)
    score += min(signal.open_recommendations * 3, 18)
    score += min(signal.slow_total * 2, 10)
    if signal.request_total and signal.active_redaction_rules == 0:
        score += 22
    return min(score, 100)


def _risk_label(score: int) -> str:
    if score >= 75:
        return "Kritik kontrol"
    if score >= 45:
        return "Kontrol gerekli"
    if score >= 20:
        return "İzleme"
    return "Uygun"


def _risk_tone(score: int) -> str:
    if score >= 75:
        return "danger"
    if score >= 45:
        return "warning"
    if score >= 20:
        return "calm"
    return "success"


def _module_row(signal: ModuleVisibilitySignal) -> dict[str, Any]:
    score = _risk_score(signal)
    reasons: list[str] = []
    if signal.unmasked_total:
        reasons.append(f"{signal.unmasked_total} maskesiz AI isteği")
    if signal.request_total and signal.active_redaction_rules == 0:
        reasons.append("aktif maskeleme kuralı görünmüyor")
    if signal.user_visible_total:
        reasons.append(f"{signal.user_visible_total} kullanıcıya görünür AI çıktısı")
    if signal.failed_total:
        reasons.append(f"{signal.failed_total} hata")
    if signal.open_recommendations:
        reasons.append(f"{signal.open_recommendations} açık öneri")
    if not reasons:
        reasons.append("KVKK görünürlük sinyali düşük")
    return {
        "module_type": signal.module_type,
        "module_label": _module_label(signal.module_type),
        "request_total": signal.request_total,
        "masked_total": signal.masked_total,
        "unmasked_total": signal.unmasked_total,
        "user_visible_total": signal.user_visible_total,
        "failed_total": signal.failed_total,
        "warning_total": signal.warning_total,
        "slow_total": signal.slow_total,
        "active_redaction_rules": signal.active_redaction_rules,
        "open_recommendations": signal.open_recommendations,
        "risk_score": score,
        "risk_label": _risk_label(score),
        "tone": _risk_tone(score),
        "reasons": reasons[:4],
        "safe_action": _safe_action(signal),
    }


def _safe_action(signal: ModuleVisibilitySignal) -> str:
    if signal.unmasked_total:
        return "Önce maskeleme kuralları ve AI çıktı görünürlüğü kontrol edilmeli; ham metin export edilmemeli."
    if signal.request_total and signal.active_redaction_rules == 0:
        return "Bu modül için en az bir aktif maskeleme kuralı tanımı gözden geçirilmeli."
    if signal.user_visible_total:
        return "Kullanıcıya açılan AI çıktıları rol ve menü yetkisiyle birlikte izlenmeli."
    if signal.failed_total:
        return "Hata kayıtları prompt kalitesi ve sağlayıcı yanıtlarıyla birlikte incelenmeli."
    return "Mevcut görünürlük kapısı yeterli; düzenli izleme sürdürülebilir."


def _summary_cards(module_rows: list[dict[str, Any]], role_rows: list[dict[str, Any]], role_counts: dict[str, int]) -> list[dict[str, Any]]:
    total_requests = sum(row["request_total"] for row in module_rows)
    total_unmasked = sum(row["unmasked_total"] for row in module_rows)
    total_rules = sum(row["active_redaction_rules"] for row in module_rows)
    raw_roles = sum(1 for row in role_rows if row["raw_payload_visible"])
    denied_roles = sum(1 for row in role_rows if not row["can_view_ai_center"])
    admin_users = sum(role_counts.get(role, 0) for role in ("admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"))
    return [
        {
            "label": "AI yönetim yetkili kullanıcı",
            "value": admin_users,
            "mini": "Admin ailesi kapsamı; personel rolü kapalıdır.",
            "tone": "calm",
        },
        {
            "label": "Ham AI metin görünürlüğü",
            "value": raw_roles,
            "mini": "Tüm roller için ham request/response kapalı olmalıdır.",
            "tone": "success" if raw_roles == 0 else "danger",
        },
        {
            "label": "KVKK maskesiz istek",
            "value": total_unmasked,
            "mini": f"Son panel aralığında toplam {total_requests} AI isteği okundu.",
            "tone": "danger" if total_unmasked else "success",
        },
        {
            "label": "Aktif maskeleme kuralı",
            "value": total_rules,
            "mini": "Modül bazlı redaction kural kapsaması.",
            "tone": "success" if total_rules else "warning",
        },
        {
            "label": "AI merkezi kapalı rol",
            "value": denied_roles,
            "mini": "Koordinatör, birim sorumlusu ve personel için yönetim ekranı kapalıdır.",
            "tone": "muted",
        },
    ]


def _module_options(module_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    values = {row.get("module_type") for row in module_rows if row.get("module_type")}
    for live_module in LIVE_MODULE_ORDER:
        values.add(live_module)
    ordered = filter_visible_values(values)
    ordered.sort(key=lambda item: (LIVE_MODULE_ORDER.index(item) if item in LIVE_MODULE_ORDER else 99, _module_label(item)))
    return [{"value": key, "label": _module_label(key)} for key in ordered]


def build_ai_visibility_gate_snapshot(
    *,
    current_user: Any,
    lookback_days: Any = DEFAULT_LOOKBACK_DAYS,
    module_type: str = "",
    role_name: str = "",
) -> dict[str, Any]:
    """Faz 10 panel payloadı. Yalnız okuma ve bellek içi hesaplama yapar."""
    days = _safe_int(lookback_days, DEFAULT_LOOKBACK_DAYS, 1, MAX_LOOKBACK_DAYS)
    module_filter = _clean_key(module_type, "") if module_type else ""
    role_filter = _clean_key(role_name, "") if role_name else ""
    if module_filter and not is_visible_ai_module(module_filter):
        module_filter = ""
    if role_filter and role_filter not in ROLE_POLICIES:
        role_filter = ""
    now = utc_now()
    since = now - timedelta(days=days)

    module_rows = [_module_row(signal) for signal in _module_signals(since, module_filter)]
    module_rows.sort(key=lambda row: (-int(row.get("risk_score") or 0), row.get("module_label") or ""))
    role_rows = _role_matrix(role_filter)
    role_counts = _user_role_counts()
    menu_permissions = _menu_permission_rows()
    current_policy = get_ai_visibility_policy(current_user)

    visibility_contract = {
        "DB_WRITE_ENABLED": DB_WRITE_ENABLED,
        "AI_FINAL_DECISION_ENABLED": AI_FINAL_DECISION_ENABLED,
        "AI_AUTO_APPLY_ENABLED": AI_AUTO_APPLY_ENABLED,
        "RAW_AI_PAYLOAD_VISIBLE": RAW_AI_PAYLOAD_VISIBLE,
        "RAW_AI_EXPORT_ENABLED": RAW_AI_EXPORT_ENABLED,
        "SAFE_CSV_EXPORT_ENABLED": SAFE_CSV_EXPORT_ENABLED,
        "KVKK_MASKING_REQUIRED": KVKK_MASKING_REQUIRED,
        "PERSONAL_DATA_EXPORT_ENABLED": PERSONAL_DATA_EXPORT_ENABLED,
        "HUMAN_REVIEW_REQUIRED": HUMAN_REVIEW_REQUIRED,
    }

    guardrails = [
        {
            "title": "Ham istem/yanıt kapısı",
            "body": "Ham AI istem ve yanıt alanları panelde ve exportta açılmaz; yalnız sayısal sinyal ve maske durumu okunur.",
            "tone": "success" if not RAW_AI_PAYLOAD_VISIBLE and not RAW_AI_EXPORT_ENABLED else "danger",
        },
        {
            "title": "KVKK maskeleme zorunluluğu",
            "body": "TC, e-posta, telefon, sicil, ad-soyad ve IBAN benzeri alanlar güvenli görünürlükte maskelenir.",
            "tone": "success" if KVKK_MASKING_REQUIRED else "warning",
        },
        {
            "title": "Rol bazlı görünürlük",
            "body": "AI merkezi admin ailesiyle sınırlıdır; koordinatör/birim/personel seviyesinde yönetim paneli kapalı tutulur.",
            "tone": "success",
        },
        {
            "title": "Canlı kapsam filtresi",
            "body": "Eğitim, Strateji, Belge Deposu ve Portal izleri güncel canlı görünürlük kapısına taşınmaz.",
            "tone": "success",
        },
        {
            "title": "İnsan onayı",
            "body": "AI çıktısı karar değildir; görünürlük kapısı yalnız güvenli inceleme alanı sağlar.",
            "tone": "success" if HUMAN_REVIEW_REQUIRED else "warning",
        },
    ]

    return {
        "page_title": "AI Yetki, KVKK Maskeleme ve Güvenli Görünürlük Kapısı",
        "generated_at": now,
        "lookback_days": days,
        "filters": {"module_type": module_filter, "role_name": role_filter},
        "current_policy": current_policy,
        "role_rows": role_rows,
        "role_counts": role_counts,
        "module_rows": module_rows,
        "module_options": _module_options(module_rows),
        "role_options": [{"value": role, "label": _role_label(role)} for role in ROLE_POLICIES],
        "menu_permissions": menu_permissions[0] if menu_permissions else {"rows": [], "override_visible": 0, "override_hidden": 0},
        "summary_cards": _summary_cards(module_rows, role_rows, role_counts),
        "guardrails": guardrails,
        "visibility_contract": visibility_contract,
        "safety_contract": visibility_contract,
        "masked_examples": [
            {"field": "email", "raw": "ornek.kullanici@kurum.gov.tr", "masked": mask_sensitive_text("ornek.kullanici@kurum.gov.tr", field_name="email", role=current_policy["role"])},
            {"field": "telefon", "raw": "05xx xxx xx xx", "masked": mask_sensitive_text("0532 123 45 67", field_name="telefon", role=current_policy["role"])},
            {"field": "sicil_no", "raw": "SICIL-12345", "masked": mask_sensitive_text("Sicil No: SICIL-12345", field_name="sicil_no", role=current_policy["role"])},
            {"field": "ai_payload", "raw": "Ham AI metni", "masked": "[ham AI metni kapalı]"},
        ],
    }


def export_visibility_gate_rows(snapshot: dict[str, Any]) -> list[list[Any]]:
    """Güvenli CSV satırları. Ham AI metni ve kişisel veri içermez."""
    rows: list[list[Any]] = []
    for row in snapshot.get("role_rows") or []:
        rows.append(
            [
                "role_policy",
                row.get("role_label"),
                row.get("scope"),
                "evet" if row.get("can_view_ai_center") else "hayir",
                "evet" if row.get("can_export_safe_csv") else "hayir",
                "evet" if row.get("kvkk_masking_required") else "hayir",
                "evet" if row.get("raw_payload_visible") else "hayir",
                "",
                "",
                "",
                "",
                mask_sensitive_text(row.get("note"), role="admin"),
            ]
        )
    for row in snapshot.get("module_rows") or []:
        rows.append(
            [
                "module_signal",
                row.get("module_label"),
                "canli_modul",
                "",
                "",
                "evet",
                "hayir",
                row.get("request_total"),
                row.get("unmasked_total"),
                row.get("active_redaction_rules"),
                row.get("risk_label"),
                mask_sensitive_text(row.get("safe_action"), role="admin"),
            ]
        )
    for row in (snapshot.get("menu_permissions") or {}).get("rows") or []:
        rows.append(
            [
                "menu_permission",
                row.get("role_label"),
                AI_MENU_KEY,
                "evet" if row.get("policy_visible") else "hayir",
                "",
                "evet",
                "hayir",
                "",
                "",
                "",
                row.get("state_label"),
                "Rol varsayılanı ve Faz 10 politika matrisi karşılaştırması.",
            ]
        )
    return rows
