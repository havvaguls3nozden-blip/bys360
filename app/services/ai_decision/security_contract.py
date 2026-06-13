
"""AI Karar Destek güvenlik ve KVKK sözleşmesi.

Bu katman prompt hazırlamadan önce uygulanacak temel maskeleme ve görünürlük
kurallarını tarif eder. Faz 0'da veritabanı veya route davranışı değiştirilmez.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Final


@dataclass(frozen=True)
class SafetyRule:
    key: str
    label: str
    description: str
    enforcement: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


SENSITIVE_FIELD_NAMES: Final[frozenset[str]] = frozenset(
    {
        "tckn",
        "tc_kimlik_no",
        "identity_no",
        "password",
        "password_hash",
        "phone",
        "manual_phone",
        "email",
        "e_posta",
        "manual_email",
        "address",
        "home_address",
        "birth_date",
        "iban",
        "token",
        "secret",
    }
)

SAFETY_RULES: Final[tuple[SafetyRule, ...]] = (
    SafetyRule(
        key="redact_before_prompt",
        label="Prompt öncesi maskeleme",
        description="Kişisel veri ve kimlik bilgileri AI sağlayıcısına açık metin olarak gönderilmez.",
        enforcement="service_gate",
    ),
    SafetyRule(
        key="log_minimization",
        label="Log minimizasyonu",
        description="AI istek/yanıt logları gereksiz kişisel veri taşımayacak şekilde kısaltılır ve maskelenir.",
        enforcement="request_log_service",
    ),
    SafetyRule(
        key="human_review",
        label="İnsan onayı",
        description="AI önerisi karar yerine geçmez; yönetici/İK incelemesi için karar destek notu üretir.",
        enforcement="ui_copy_and_status",
    ),
    SafetyRule(
        key="role_visibility",
        label="Yetki bazlı görünürlük",
        description="AI içgörüleri kullanıcının zaten görmeye yetkili olduğu veri kapsamından üretilecek şekilde sınırlandırılır.",
        enforcement="permission_gate",
    ),
    SafetyRule(
        key="no_secret_storage",
        label="Sır saklamama",
        description="API anahtarları, parola ve gizli bilgiler log/cache/öneri satırlarına yazılmaz.",
        enforcement="static_and_runtime_guard",
    ),
)


def normalize_field_name(field_name: str | None) -> str:
    return str(field_name or "").strip().lower()


def should_redact_field(field_name: str | None) -> bool:
    return normalize_field_name(field_name) in SENSITIVE_FIELD_NAMES


def redact_mapping_for_ai(payload: dict[str, Any]) -> dict[str, Any]:
    """Nested dict/list payload için hafif ve bağımlılıksız maskeleme.

    Mevcut ``app.services.ai.redaction`` daha geniş metin maskeleme yapıyor.
    Bu fonksiyon Faz 0 sözleşmesinde bağımlılığı düşük, test edilebilir bir
    tamamlayıcıdır.
    """

    def _redact(value: Any, *, key: str | None = None) -> Any:
        if should_redact_field(key):
            return "***"
        if isinstance(value, dict):
            return {item_key: _redact(item_value, key=str(item_key)) for item_key, item_value in value.items()}
        if isinstance(value, list):
            return [_redact(item) for item in value]
        if isinstance(value, tuple):
            return tuple(_redact(item) for item in value)
        return value

    return _redact(payload) if isinstance(payload, dict) else {}


def get_ai_safety_rules() -> list[dict[str, str]]:
    return [rule.to_dict() for rule in SAFETY_RULES]
