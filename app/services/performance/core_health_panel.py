from __future__ import annotations


import logging

from app.core.datetime_utils import utc_now
"""BYS360 Dalga 8 çekirdek sağlık paneli.

Onarım yapmaz; performans çekirdeğinin zincir, görünürlük, yayın, route,
güvenlik ve canlı omurga durumunu tek sözleşmede raporlar.
"""

from dataclasses import dataclass
from typing import Any, Iterable

from flask import current_app, has_app_context

from app.models import EvaluationAssignment, OrganizationUnit, PerformanceEvaluation, PerformancePeriod, User
from app.services.performance.chain_rule_engine import (
    RULE_ENGINE_VERSION,
    assert_chain_constitution_alignment,
    get_chain_rule_matrix_snapshot,
)
from app.services.performance.health_report import build_performance_task_health_report
from app.services.performance.publish_guard import build_publish_preflight_report
from app.services.performance.visibility_guard import BLIND_REVIEW_ALLOWED, VISIBILITY_RULE_VERSION
logger = logging.getLogger(__name__)

CORE_HEALTH_VERSION = "2026-04-18-dalga8-core-health-v1"

REQUIRED_ENDPOINTS = {
    "main.performance_operations_center": "Performans Operasyon Merkezi",
    "main.performance_task_management_health": "Görev Sağlık Raporu",
    "main.performance_v2_phase5_publish_preflight": "Yayın Ön Kontrol",
    "main.performance_team_compare": "Personel Analizi",
}
REQUIRED_ROUTES = {
    "/performance/personel-analizi": "Personel Analizi URL",
    "/performance/core-health": "Çekirdek Sağlık Paneli",
}


@dataclass(slots=True)
class CoreFinding:
    title: str
    detail: str
    severity: str = "info"
    source: str = "core"
    action: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "title": self.title,
            "detail": self.detail,
            "severity": self.severity,
            "source": self.source,
            "action": self.action,
        }


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _safe_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _safe_count(model: Any) -> int | None:
    try:
        return int(model.query.count())
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None


def _count_label(value: int | None) -> str:
    return "-" if value is None else str(value)


def _model_counter_cards() -> list[dict[str, Any]]:
    return [
        {"label": "Aktif kullanıcı", "value": _count_label(_safe_count(User)), "key": "users"},
        {"label": "Birim kaydı", "value": _count_label(_safe_count(OrganizationUnit)), "key": "units"},
        {"label": "Dönem", "value": _count_label(_safe_count(PerformancePeriod)), "key": "periods"},
        {"label": "Görev", "value": _count_label(_safe_count(EvaluationAssignment)), "key": "assignments"},
        {"label": "Karne", "value": _count_label(_safe_count(PerformanceEvaluation)), "key": "evaluations"},
    ]


def _endpoint_findings() -> tuple[list[CoreFinding], list[dict[str, Any]]]:
    findings: list[CoreFinding] = []
    rows: list[dict[str, Any]] = []
    if not has_app_context():
        return [CoreFinding("Uygulama bağlamı yok", "Route kontrolü için Flask app context gerekir.", "warning", "route")], rows
    view_functions = current_app.view_functions
    route_paths = {rule.rule for rule in current_app.url_map.iter_rules()}
    for endpoint, label in REQUIRED_ENDPOINTS.items():
        ok = endpoint in view_functions
        rows.append({"name": label, "key": endpoint, "ok": ok, "type": "endpoint"})
        if not ok:
            findings.append(CoreFinding(label, f"{endpoint} endpoint'i kayıtlı görünmüyor.", "blocker", "route", "Route import zincirini kontrol edin."))
    for path, label in REQUIRED_ROUTES.items():
        ok = path in route_paths
        rows.append({"name": label, "key": path, "ok": ok, "type": "url"})
        if not ok:
            findings.append(CoreFinding(label, f"{path} URL'i kayıtlı görünmüyor.", "blocker", "route", "core_health_routes importunu kontrol edin."))
    return findings, rows


def _constitution_findings() -> tuple[list[CoreFinding], dict[str, Any]]:
    findings: list[CoreFinding] = []
    snapshot = get_chain_rule_matrix_snapshot()
    try:
        assert_chain_constitution_alignment()
    except AssertionError:
        findings.append(CoreFinding("Zincir anayasası uyuşmuyor", "Personel / Koordinatör / Grup Başkanı slotları nihai kuralla uyumlu değil.", "blocker", "chain", "chain_rule_engine.py dosyasını düzeltin."))
    if BLIND_REVIEW_ALLOWED:
        findings.append(CoreFinding("Kör değerlendirme açık", "Sonraki amir önceki puan ve kanaati görmelidir.", "blocker", "visibility", "BLIND_REVIEW_ALLOWED False olmalı."))
    if snapshot.get("visibility", {}).get("employee_result_requires_publish") is not True:
        findings.append(CoreFinding("Yayın kilidi zayıf", "Personel sonuçları yayın/onay olmadan açılmamalıdır.", "blocker", "visibility"))
    return findings, snapshot


def _security_findings() -> tuple[list[CoreFinding], list[dict[str, Any]]]:
    findings: list[CoreFinding] = []
    rows: list[dict[str, Any]] = []
    if not has_app_context():
        return findings, rows
    checks = [
        ("SECRET_KEY", bool(current_app.config.get("SECRET_KEY")), "SECRET_KEY tanımlı değil."),
        ("SESSION_COOKIE_HTTPONLY", current_app.config.get("SESSION_COOKIE_HTTPONLY", True) is True, "SESSION_COOKIE_HTTPONLY açık olmalı."),
        ("WTF_CSRF_ENABLED", current_app.config.get("WTF_CSRF_ENABLED", True) is True, "CSRF kapalı görünmemeli."),
        ("SESSION_COOKIE_SAMESITE", _safe_text(current_app.config.get("SESSION_COOKIE_SAMESITE")) in {"Lax", "Strict", "None"}, "SESSION_COOKIE_SAMESITE açık bir değer almalı."),
    ]
    for key, ok, detail in checks:
        rows.append({"key": key, "ok": bool(ok)})
        if not ok:
            findings.append(CoreFinding(key, detail, "warning", "security", "config.py veya .env ayarlarını kontrol edin."))
    return findings, rows


def _period_options() -> list[Any]:
    try:
        return PerformancePeriod.query.order_by(PerformancePeriod.id.desc()).limit(50).all()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return []


def _choose_period(period: Any | None = None) -> Any | None:
    if period is not None:
        return period
    try:
        return PerformancePeriod.query.filter_by(is_active=True).order_by(PerformancePeriod.id.desc()).first()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None


def _compact_task_health(period: Any | None) -> tuple[list[CoreFinding], dict[str, Any]]:
    if not period:
        return [CoreFinding("Aktif dönem yok", "Görev ve yayın kontrolleri dönem üzerinden okunur.", "warning", "period", "Aktif performans dönemi seçin veya oluşturun.")], {}
    try:
        report = build_performance_task_health_report(period, None) or {}
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return [CoreFinding("Görev sağlık raporu okunamadı", str(exc), "warning", "task_health")], {}
    summary = report.get("summary") or {}
    critical = (
        _safe_int(summary.get("duplicate_level_count"))
        + _safe_int(summary.get("mismatch_count"))
        + _safe_int(summary.get("orphan_evaluation_count"))
        + _safe_int(summary.get("orphan_assignment_count"))
        + _safe_int(summary.get("uncovered_count"))
    )
    findings: list[CoreFinding] = []
    if critical > 0:
        findings.append(CoreFinding("Görev sağlığında kritik kayıt var", f"Toplam {critical} kritik görev/eşleşme sinyali görünüyor.", "blocker", "task_health", "Görev Sağlık Raporu ekranından ayrıntıya bakın."))
    return findings, {"summary": summary, "critical_count": critical}


def _compact_publish_preflight(period: Any | None) -> tuple[list[CoreFinding], dict[str, Any]]:
    try:
        report = build_publish_preflight_report(period=period) or {}
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return [CoreFinding("Yayın ön kontrol okunamadı", str(exc), "warning", "publish")], {}
    findings: list[CoreFinding] = []
    for row in report.get("blockers") or []:
        findings.append(CoreFinding(_safe_text(row.get("title"), "Yayın blokajı"), _safe_text(row.get("detail")), "blocker", "publish", "Yayın Ön Kontrol ekranında kapatın."))
    for row in report.get("warnings") or []:
        findings.append(CoreFinding(_safe_text(row.get("title"), "Yayın uyarısı"), _safe_text(row.get("detail")), "warning", "publish"))
    return findings, report


def _split_findings(findings: Iterable[CoreFinding]) -> dict[str, list[dict[str, str]]]:
    result = {"blockers": [], "warnings": [], "infos": []}
    for finding in findings:
        if finding.severity == "blocker":
            result["blockers"].append(finding.as_dict())
        elif finding.severity == "warning":
            result["warnings"].append(finding.as_dict())
        else:
            result["infos"].append(finding.as_dict())
    return result


def _score(blocker_count: int, warning_count: int) -> dict[str, Any]:
    value = max(0, min(100, 100 - (blocker_count * 14) - (warning_count * 4)))
    if blocker_count:
        return {"value": value, "label": "Blokaj var", "tone": "critical"}
    if warning_count:
        return {"value": min(value, 89), "label": "Kontrollü ilerleyin", "tone": "watch"}
    return {"value": max(value, 95), "label": "Çekirdek sağlıklı", "tone": "ok"}


def build_core_health_panel_snapshot(*, period: Any | None = None, viewer: Any | None = None) -> dict[str, Any]:
    period = _choose_period(period)
    all_findings: list[CoreFinding] = []
    constitution_findings, chain_snapshot = _constitution_findings()
    route_findings, route_rows = _endpoint_findings()
    security_findings, security_rows = _security_findings()
    task_findings, task_health = _compact_task_health(period)
    publish_findings, publish_preflight = _compact_publish_preflight(period)
    all_findings.extend(constitution_findings + route_findings + security_findings + task_findings + publish_findings)
    split = _split_findings(all_findings)
    readiness = _score(len(split["blockers"]), len(split["warnings"]))
    return {
        "version": CORE_HEALTH_VERSION,
        "generated_at": utc_now(),
        "period": period,
        "periods": _period_options(),
        "readiness": readiness,
        "blockers": split["blockers"],
        "warnings": split["warnings"],
        "infos": split["infos"],
        "chain_snapshot": chain_snapshot,
        "route_rows": route_rows,
        "security_rows": security_rows,
        "model_cards": _model_counter_cards(),
        "task_health": task_health,
        "publish_preflight": publish_preflight,
        "rule_versions": [
            {"label": "Çekirdek Sağlık", "value": CORE_HEALTH_VERSION},
            {"label": "Zincir Motoru", "value": RULE_ENGINE_VERSION},
            {"label": "Görünürlük Kilidi", "value": VISIBILITY_RULE_VERSION},
        ],
    }


__all__ = ["CORE_HEALTH_VERSION", "build_core_health_panel_snapshot"]
