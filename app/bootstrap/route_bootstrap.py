
"""Route ve blueprint acilis katmani.

Bu dosya BYS360 uygulamasinda blueprint kayit sirasini tek yerde tutar.
Canli saglamlastirma Faz 1.11 kapsaminda daha onceki overlaylerde olusan
recursive duplicate-endpoint guard temizlenmis ve yalnizca bilinen Başkan/Üst
Onay iade endpoint cakismasini hedefleyen dar kapsamli guvenli kayit sarmali
birakilmistir.
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any

from flask import Blueprint, Flask

from app.route_registry import get_runtime_route_manifest


@dataclass(frozen=True)
class BlueprintRegistration:
    """Kaydedilecek blueprint icin kucuk, okunur sozlesme."""

    key: str
    module_path: str
    attribute_name: str
    required: bool = True


CORE_BLUEPRINT_SEQUENCE: tuple[BlueprintRegistration, ...] = (
    BlueprintRegistration(
        key="main",
        module_path="app.routes",
        attribute_name="main_bp",
        required=True,
    ),
    BlueprintRegistration(
        key="health",
        module_path="app.core.healthcheck",
        attribute_name="health_bp",
        required=True,
    ),
    BlueprintRegistration(
        key="strategic_performance",
        module_path="app.modules.strategic_performance.routes",
        attribute_name="strategic_performance_bp",
        required=False,
    ),
    BlueprintRegistration(
        key="ai_agent",
        module_path="app.ai_agent.routes",
        attribute_name="ai_agent_bp",
        required=False,
    ),  # BYS360_AG1_AI_AGENT_ROUTE_BOOTSTRAP
    BlueprintRegistration(
        key="digital_archive",
        module_path="app.digital_archive.routes",
        attribute_name="digital_archive_bp",
        required=False,
    ),  # BYS360_DA1B_DIGITAL_ARCHIVE_ROUTE_BOOTSTRAP

)


# BYS360_CANLI_SAGLAMLASTIRMA_FAZ1_11_ROUTE_BOOTSTRAP_RECURSION_FIX
_ALLOWED_DUPLICATE_ENDPOINTS = {
    "main.performance_low_score_president_reject",
}


def load_blueprint(registration: BlueprintRegistration) -> Blueprint:
    """Manifest satirindan Flask Blueprint nesnesini yukler."""
    try:
        module = import_module(registration.module_path)
    except ModuleNotFoundError as exc:
        if getattr(exc, "name", "") == registration.module_path and registration.required:
            raise ModuleNotFoundError(
                f"{registration.module_path} modulu bulunamadi. Kurulum eksik veya parcali kopyalanmis olabilir. "
                "Temiz kaynak paketiyle ilgili app dosyasini geri yukleyin."
            ) from exc
        raise

    blueprint = getattr(module, registration.attribute_name, None)
    if not isinstance(blueprint, Blueprint):
        raise RuntimeError(
            f"Blueprint sozlesmesi bozuk: {registration.module_path}.{registration.attribute_name} "
            "Flask Blueprint nesnesi degil."
        )
    return blueprint


def _is_allowed_duplicate_endpoint_error(message: str) -> bool:
    if "overwriting an existing endpoint function" not in message:
        return False
    return any(endpoint in message for endpoint in _ALLOWED_DUPLICATE_ENDPOINTS)


def _register_blueprint_with_narrow_duplicate_guard(app: Flask, blueprint: Blueprint) -> None:
    """Blueprint'i recursion olusturmadan kaydeder.

    Kritik nokta: Bu fonksiyon kendi kendini cagirmamalidir. Sadece Flask'in orijinal
    app.add_url_rule metodunu gecici olarak sarmalar ve app.register_blueprint(blueprint)
    cagrisini bir kez yapar.
    """
    original_add_url_rule = app.add_url_rule
    skipped: list[dict[str, str]] = []

    def _guarded_add_url_rule(rule, endpoint=None, view_func=None, **options):
        try:
            return original_add_url_rule(rule, endpoint=endpoint, view_func=view_func, **options)
        except AssertionError as exc:
            message = str(exc)
            if _is_allowed_duplicate_endpoint_error(message):
                skipped.append({"rule": str(rule), "endpoint": str(endpoint), "message": message})
                try:
                    app.logger.warning("BYS360 duplicate endpoint dar guard atladi: %s", message)
                except Exception:
                    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/bootstrap/route_bootstrap.py)")
                return None
            raise

    app.add_url_rule = _guarded_add_url_rule
    try:
        app.register_blueprint(blueprint)
    finally:
        app.add_url_rule = original_add_url_rule

    if skipped:
        app.extensions.setdefault("bys360_duplicate_endpoint_skipped", []).extend(skipped)


# Eski overlay isimleriyle cagrilan yardimcilar icin recursion yapmayan uyumluluk aliaslari.
def _phase6_4_register_blueprint_with_duplicate_endpoint_guard(app: Flask, blueprint: Blueprint) -> None:
    # BYS360_PHASE6_4_DUPLICATE_ENDPOINT_V4_GUARD_COMPAT
    return _register_blueprint_with_narrow_duplicate_guard(app, blueprint)


def _bys360_register_blueprint_safely(app: Flask, blueprint: Blueprint) -> None:
    # BYS360_PHASE6_4_DUPLICATE_ENDPOINT_TARGET_GUARD_COMPAT
    return _register_blueprint_with_narrow_duplicate_guard(app, blueprint)


def _bys360_phase1_7_register_blueprint_safely(app: Flask, blueprint: Blueprint) -> None:
    # Compatibility guard.
    return _register_blueprint_with_narrow_duplicate_guard(app, blueprint)


def register_application_blueprints(app: Flask) -> None:
    """Uygulamanin core blueprint kayitlarini manifest sirasiyla yapar."""
    registered: list[dict[str, Any]] = []

    for registration in CORE_BLUEPRINT_SEQUENCE:
        blueprint = load_blueprint(registration)
        if blueprint.name not in app.blueprints:
            _register_blueprint_with_narrow_duplicate_guard(app, blueprint)
        registered.append(
            {
                "key": registration.key,
                "module": registration.module_path,
                "attribute": registration.attribute_name,
                "blueprint": blueprint.name,
            }
        )

    app.extensions["blueprint_bootstrap_sequence"] = registered


def attach_runtime_route_manifest(app: Flask) -> None:
    """Runtime route manifestini uygulama extensions alanina yazar."""
    app.extensions["runtime_route_manifest"] = get_runtime_route_manifest()


def configure_route_bootstrap(app: Flask) -> None:
    """Blueprint kaydi ve route manifest baglama adimini tek cagriya indirir."""
    register_application_blueprints(app)
    attach_runtime_route_manifest(app)


def collect_blueprint_snapshot(app: Flask) -> dict[str, Any]:
    """Gate ve tanilama icin mevcut blueprint/route ozetini uretir."""
    blueprints = sorted(app.blueprints.keys())
    endpoints = sorted(rule.endpoint for rule in app.url_map.iter_rules())
    return {
        "blueprint_count": len(blueprints),
        "route_count": len(endpoints),
        "blueprints": blueprints,
        "endpoints": endpoints,
        "bootstrap_sequence": list(app.extensions.get("blueprint_bootstrap_sequence") or []),
    }


__all__ = [
    "BlueprintRegistration",
    "CORE_BLUEPRINT_SEQUENCE",
    "attach_runtime_route_manifest",
    "collect_blueprint_snapshot",
    "configure_route_bootstrap",
    "load_blueprint",
    "register_application_blueprints",
]
