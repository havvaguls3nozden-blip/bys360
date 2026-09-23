from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any
from urllib import error as urlerror, request as urlrequest

from flask import current_app

from .module_scope import visible_module_options
from .stub_engine import build_stub_response, get_stub_engine_snapshot

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AIResult:
    text: str
    provider_name: str = "internal_stub_plus"
    model_name: str = "bys360-ai-stub-v2"
    prompt_version: str | None = None
    latency_ms: int | None = None
    token_in: int | None = None
    token_out: int | None = None
    error_message: str | None = None


class BaseAIClient:
    provider_mode = "stub"

    def generate(self, *, system_prompt: str, user_prompt: str, prompt_version: str | None = None) -> AIResult:  # pragma: no cover - interface
        raise NotImplementedError


class StubAIClient(BaseAIClient):
    provider_mode = "stub"

    def __init__(self, *, provider_name: str | None = None, model_name: str | None = None, note: str | None = None):
        self.provider_name = provider_name or current_app.config.get("AI_PROVIDER_NAME", "internal_stub_plus")
        self.model_name = model_name or current_app.config.get("AI_MODEL_NAME", "bys360-ai-stub-v2")
        self.note = (note or "").strip() or None

    def generate(self, *, system_prompt: str, user_prompt: str, prompt_version: str | None = None) -> AIResult:
        started = time.perf_counter()
        response_text = build_stub_response(system_prompt=system_prompt, user_prompt=user_prompt, prompt_version=prompt_version)
        if not str(response_text or "").strip():
            response_text = current_app.config.get(
                "AI_STUB_DEFAULT_RESPONSE",
                (
                    "AI servisi henüz gerçek modele bağlanmadı. Bu nedenle denetimli stub cevap üretildi. "
                    "Kurumsal entegrasyon tamamlandığında bu alan gerçek özet ve öneriler döndürecek."
                ),
            )
        if self.note:
            response_text = f"{response_text}\n\nNot: {self.note}"
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return AIResult(
            text=response_text,
            provider_name=self.provider_name,
            model_name=self.model_name,
            prompt_version=prompt_version,
            latency_ms=elapsed_ms,
            token_in=max(len((system_prompt or "") + (user_prompt or "")) // 4, 1),
            token_out=max(len(response_text) // 4, 1),
            error_message=self.note,
        )


class OpenAICompatibleAIClient(BaseAIClient):
    provider_mode = "openai_compatible"

    def __init__(self, *, base_url: str, api_key: str, model_name: str, request_path: str, timeout_seconds: int, temperature: float, max_output_tokens: int):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key or ""
        self.model_name = model_name
        self.request_path = request_path if request_path.startswith("/") else f"/{request_path}"
        self.timeout_seconds = max(int(timeout_seconds or 30), 1)
        self.temperature = float(temperature or 0.2)
        self.max_output_tokens = max(int(max_output_tokens or 700), 64)

    def _extract_text(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices") or []
        if not choices:
            return ""
        first = choices[0] or {}
        message = first.get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str) and text.strip():
                        parts.append(text.strip())
            return "\n".join(part for part in parts if part).strip()
        text = first.get("text")
        if isinstance(text, str):
            return text.strip()
        return ""

    def generate(self, *, system_prompt: str, user_prompt: str, prompt_version: str | None = None) -> AIResult:
        started = time.perf_counter()
        target_url = f"{self.base_url}{self.request_path}"
        body = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": user_prompt or ""},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_output_tokens,
        }
        request_obj = urlrequest.Request(
            target_url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urlrequest.urlopen(request_obj, timeout=self.timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace")
            payload = json.loads(raw or "{}")
        response_text = self._extract_text(payload) or current_app.config.get(
            "AI_STUB_DEFAULT_RESPONSE",
            "AI sağlayıcısından boş cevap döndü; güvenli varsayılan içerik kullanıldı.",
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        usage = payload.get("usage") or {}
        return AIResult(
            text=response_text,
            provider_name=current_app.config.get("AI_PROVIDER_NAME", "openai_compatible"),
            model_name=self.model_name,
            prompt_version=prompt_version,
            latency_ms=elapsed_ms,
            token_in=int(usage.get("prompt_tokens") or max(len((system_prompt or "") + (user_prompt or "")) // 4, 1)),
            token_out=int(usage.get("completion_tokens") or max(len(response_text) // 4, 1)),
        )


def _trim_prompt(value: str) -> str:
    text = (value or "").strip()
    limit = int(current_app.config.get("AI_MAX_INPUT_CHARS", 12000) or 12000)
    return text[:limit]


def _resolve_stub(note: str | None = None) -> StubAIClient:
    provider_name = current_app.config.get("AI_PROVIDER_NAME", "internal_stub_plus")
    model_name = current_app.config.get("AI_MODEL_NAME", "bys360-ai-stub-v2")
    if note:
        provider_name = f"{provider_name}_fallback"
    return StubAIClient(provider_name=provider_name, model_name=model_name, note=note)


def build_ai_client() -> BaseAIClient:
    provider_mode = str(current_app.config.get("AI_PROVIDER_MODE", "stub") or "stub").strip().lower()
    if provider_mode in {"stub", "internal_stub"}:
        return _resolve_stub()

    if provider_mode == "openai_compatible":
        base_url = str(current_app.config.get("AI_BASE_URL", "") or "").strip().rstrip("/")
        api_key = str(current_app.config.get("AI_API_KEY", "") or "").strip()
        request_path = str(current_app.config.get("AI_REQUEST_PATH", "/chat/completions") or "/chat/completions").strip()
        if base_url and api_key:
            return OpenAICompatibleAIClient(
                base_url=base_url,
                api_key=api_key,
                model_name=str(current_app.config.get("AI_MODEL_NAME", "gpt-4.1-mini") or "gpt-4.1-mini"),
                request_path=request_path,
                timeout_seconds=int(current_app.config.get("AI_HTTP_TIMEOUT_SECONDS", 30) or 30),
                temperature=float(current_app.config.get("AI_TEMPERATURE", 0.2) or 0.2),
                max_output_tokens=int(current_app.config.get("AI_MAX_OUTPUT_TOKENS", 700) or 700),
            )
        if current_app.config.get("AI_ALLOW_STUB_FALLBACK", True):
            return _resolve_stub("OpenAI-compatible sağlayıcı ayarları eksik olduğu için güvenli fallback etkin.")
        return _resolve_stub("OpenAI-compatible sağlayıcı ayarları eksik.")

    return _resolve_stub(f"Tanımsız AI sağlayıcı modu: {provider_mode}")


def get_ai_client() -> BaseAIClient:
    client = build_ai_client()
    if isinstance(client, StubAIClient):
        return client
    return _WrappedClient(client)


class _WrappedClient(BaseAIClient):
    def __init__(self, inner: BaseAIClient):
        self.inner = inner

    def generate(self, *, system_prompt: str, user_prompt: str, prompt_version: str | None = None) -> AIResult:
        safe_system = _trim_prompt(system_prompt)
        safe_user = _trim_prompt(user_prompt)
        try:
            return self.inner.generate(system_prompt=safe_system, user_prompt=safe_user, prompt_version=prompt_version)
        except (urlerror.HTTPError, urlerror.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            if current_app.config.get("AI_ALLOW_STUB_FALLBACK", True):
                logger.exception("BYS360 AI: gerçek sağlayıcıya erişilemedi, stub yanıta düşülüyor | exc=%s", exc)
                return _resolve_stub("Gerçek sağlayıcıya erişilemedi.").generate(
                    system_prompt=safe_system,
                    user_prompt=safe_user,
                    prompt_version=prompt_version,
                )
            raise


def get_provider_snapshot() -> dict[str, Any]:
    provider_mode = str(current_app.config.get("AI_PROVIDER_MODE", "stub") or "stub").strip().lower()
    base_url = str(current_app.config.get("AI_BASE_URL", "") or "").strip()
    has_api_key = bool(str(current_app.config.get("AI_API_KEY", "") or "").strip())
    ready_for_live_provider = provider_mode == "openai_compatible" and bool(base_url) and has_api_key
    masked_base_url = base_url
    if len(masked_base_url) > 48:
        masked_base_url = masked_base_url[:45] + "..."
    enabled_modules = visible_module_options(current_app.config.get("AI_ENABLED_MODULES") or ())
    stub_snapshot = get_stub_engine_snapshot()
    return {
        "ai_enabled": bool(current_app.config.get("AI_ENABLED", True)),
        "provider_mode": provider_mode,
        "provider_name": str(current_app.config.get("AI_PROVIDER_NAME", "internal_stub_plus") or "internal_stub_plus"),
        "model_name": str(current_app.config.get("AI_MODEL_NAME", "bys360-ai-stub-v2") or "bys360-ai-stub-v2"),
        "base_url": masked_base_url or "-",
        "has_api_key": has_api_key,
        "request_path": str(current_app.config.get("AI_REQUEST_PATH", "/chat/completions") or "/chat/completions"),
        "timeout_seconds": int(current_app.config.get("AI_HTTP_TIMEOUT_SECONDS", 30) or 30),
        "temperature": float(current_app.config.get("AI_TEMPERATURE", 0.2) or 0.2),
        "max_output_tokens": int(current_app.config.get("AI_MAX_OUTPUT_TOKENS", 700) or 700),
        "allow_stub_fallback": bool(current_app.config.get("AI_ALLOW_STUB_FALLBACK", True)),
        "max_input_chars": int(current_app.config.get("AI_MAX_INPUT_CHARS", 12000) or 12000),
        "ready_for_live_provider": ready_for_live_provider,
        "require_real_provider_for_user_visible": bool(current_app.config.get("AI_REQUIRE_REAL_PROVIDER_FOR_USER_VISIBLE", False)),
        "enabled_modules": enabled_modules,
        "using_stub_mode": provider_mode in {"stub", "internal_stub"},
        "live_readiness_label": "hazır" if ready_for_live_provider else "hazır değil",
        "stub_intelligence_level": str(current_app.config.get("AI_STUB_INTELLIGENCE_LEVEL", stub_snapshot.get("intelligence_level") or "advanced") or "advanced"),
        "stub_scenario_count": int(stub_snapshot.get("scenario_count") or 0),
        "stub_supported_features": list(stub_snapshot.get("supported_features") or []),
    }
