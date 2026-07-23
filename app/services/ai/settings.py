from __future__ import annotations

from typing import Any

from flask import current_app

from .client import get_provider_snapshot
from .module_scope import filter_visible_values
from .prompts import get_prompt_catalog_snapshot, get_prompt_registry_meta


def _status_badge(snapshot: dict[str, Any]) -> tuple[str, str]:
    if not snapshot.get("ai_enabled", True):
        return "warning", "Kapalı"
    if snapshot.get("ready_for_live_provider"):
        return "success", "Canlı sağlayıcı hazır"
    if snapshot.get("provider_mode") in {"stub", "internal_stub"}:
        return "muted", "Yerel taslak mod"
    if snapshot.get("allow_stub_fallback"):
        return "warning", "Yedek çalışma ile sürer"
    return "warning", "Eksik yapılandırma"


def build_ai_settings_snapshot() -> dict[str, Any]:
    provider = get_provider_snapshot()
    prompt_rows = get_prompt_catalog_snapshot()
    prompt_meta = get_prompt_registry_meta()
    tone, label = _status_badge(provider)
    allowed_roles = list(current_app.config.get("AI_ALLOWED_ROLES") or [])
    enabled_modules = filter_visible_values(list(current_app.config.get("AI_ENABLED_MODULES") or []))

    actions: list[dict[str, str]] = []
    if provider.get("provider_mode") in {"stub", "internal_stub"}:
        actions.append({
            "tone": "warning",
            "title": "Gerçek sağlayıcı henüz tanımlı değil",
            "body": "İsterseniz AI_PROVIDER_MODE=openai_compatible ve gerekli bağlantı değişkenleri ile canlı sağlayıcıya geçebilirsiniz.",
        })
        actions.append({
            "tone": "calm",
            "title": "Gelişmiş stub senaryoları etkin",
            "body": f"Yerel karar destek motoru {provider.get('stub_scenario_count') or 0} aktif senaryo ile performans, dashboard, HR ve destek akışlarını gerçek sağlayıcı olmadan da kurallı biçimde özetleyebilir.",
        })
    elif not provider.get("ready_for_live_provider"):
        actions.append({
            "tone": "warning",
            "title": "Sağlayıcı ayarları eksik",
            "body": "AI_BASE_URL veya AI_API_KEY boş görünüyor. Yedek çalışma açık olduğu için sistem tamamen durmaz ama gerçek model de kullanılmaz.",
        })
    else:
        actions.append({
            "tone": "success",
            "title": "Canlı sağlayıcıya hazır",
            "body": "Bağlantı bilgileri tamam görünüyor. Smoke ve preflight ekranlarıyla saha kontrolü yapabilirsiniz.",
        })

    if provider.get("require_real_provider_for_user_visible") and not provider.get("ready_for_live_provider"):
        actions.append({
            "tone": "warning",
            "title": "Kullanıcı görünür AI kilitli",
            "body": "Gerçek sağlayıcı hazır olmadan kullanıcıya görünen AI özetleri açılmayacak şekilde yapılandırılmış.",
        })

    if not prompt_meta.get("exists"):
        actions.append({
            "tone": "warning",
            "title": "İstem kaydı dosyası bulunamadı",
            "body": "Varsayılan istemler kullanılacak. Faz 2 ile gelen config/ai_prompt_registry.json dosyasını proje içinde koruyun.",
        })
    else:
        registry_rows = sum(1 for row in prompt_rows if row.get("source") == "registry")
        actions.append({
            "tone": "calm",
            "title": "İstem kaydı etkin",
            "body": f"{registry_rows} istem kaydı dosya tabanlı kayıt dosyasından okunuyor.",
        })

    env_rows = [
        {"name": "AI_ENABLED", "value": "True / False", "note": "AI katmanını tamamen açar veya kapatır."},
        {"name": "AI_PROVIDER_MODE", "value": "yerel taslak / OpenAI uyumlu servis", "note": "Kullanılacak sağlayıcı türü."},
        {"name": "AI_PROVIDER_NAME", "value": provider.get("provider_name") or "-", "note": "Log ve raporlarda görünen sağlayıcı etiketi."},
        {"name": "AI_MODEL_NAME", "value": provider.get("model_name") or "-", "note": "Gerçek model veya kurum içi etiket."},
        {"name": "AI_BASE_URL", "value": provider.get("base_url") or "-", "note": "OpenAI uyumlu servis kök adresi."},
        {"name": "AI_REQUEST_PATH", "value": provider.get("request_path") or "/chat/completions", "note": "Sağlayıcı çağrı yolu."},
        {"name": "AI_PROMPT_REGISTRY_PATH", "value": prompt_meta.get("path") or "-", "note": "Dosya tabanlı istem kaydı konumu."},
        {"name": "AI_ALLOWED_ROLES", "value": ", ".join(allowed_roles) if allowed_roles else "-", "note": "AI özetlerini görebilecek roller."},
        {"name": "AI_ENABLED_MODULES", "value": ", ".join(enabled_modules) if enabled_modules else "-", "note": "AI kullanımına açık modül listesi."},
        {"name": "AI_REQUIRE_REAL_PROVIDER_FOR_USER_VISIBLE", "value": str(provider.get("require_real_provider_for_user_visible")), "note": "Gerçek sağlayıcı hazır olmadan kullanıcı görünür AI özeti açılmasın."},
        {"name": "AI_STUB_INTELLIGENCE_LEVEL", "value": str(provider.get("stub_intelligence_level") or "advanced"), "note": "Yerel stub motorunun zeka seviyesi ve senaryo davranışıdır."},
    ]

    return {
        "provider": provider,
        "status_tone": tone,
        "status_label": label,
        "prompt_rows": prompt_rows,
        "prompt_meta": prompt_meta,
        "allowed_roles": allowed_roles,
        "enabled_modules": enabled_modules,
        "actions": actions,
        "env_rows": env_rows,
    }