from __future__ import annotations



from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from flask import current_app

from app.services.config_hardening_service import build_safe_env_patch
from app.services.security_hardening_service import run_security_and_access_audit


def _project_root() -> Path:
    return Path(current_app.root_path).parent


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _mask_suggestions(suggestions: dict[str, str]) -> dict[str, str]:
    masked: dict[str, str] = {}
    for key, value in (suggestions or {}).items():
        if key == "SECRET_KEY":
            masked[key] = "Yeni güçlü secret üretin"
        else:
            masked[key] = value
    return masked


def _find_recent_files(base: Path, *, days: int = 7, patterns: tuple[str, ...] = ("*",)) -> list[dict[str, Any]]:
    if not base.exists() or not base.is_dir():
        return []
    now = datetime.now()
    threshold = now - timedelta(days=max(int(days or 0), 1))
    rows: list[dict[str, Any]] = []
    for pattern in patterns:
        for path in base.glob(pattern):
            if not path.is_file():
                continue
            try:
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
                size = path.stat().st_size
            except OSError:
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/go_live_readiness_service.py:47)")
                continue
            if mtime < threshold:
                continue
            rows.append(
                {
                    "name": path.name,
                    "path": str(path),
                    "modified_at": mtime,
                    "size": size,
                }
            )
    rows.sort(key=lambda item: item["modified_at"], reverse=True)
    return rows[:12]


def _build_env_checks(config: dict[str, Any]) -> list[dict[str, Any]]:
    def gate(label: str, ok: bool, detail: str, owner: str = "BT") -> dict[str, Any]:
        return {
            "label": label,
            "status": "pass" if ok else "fail",
            "detail": detail,
            "owner": owner,
        }

    return [
        gate(
            "APP_ENV production/staging",
            str(config.get("APP_ENV") or "").strip().lower() in {"production", "staging"},
            f"Mevcut değer: {config.get('APP_ENV') or '-'}",
        ),
        gate(
            "STRICT_ENV_VALIDATION",
            _safe_bool(config.get("STRICT_ENV_VALIDATION")),
            f"Mevcut değer: {config.get('STRICT_ENV_VALIDATION')}",
        ),
        gate(
            "STRICT_SCHEMA_CHECK",
            _safe_bool(config.get("STRICT_SCHEMA_CHECK")),
            f"Mevcut değer: {config.get('STRICT_SCHEMA_CHECK')}",
        ),
        gate(
            "SESSION_COOKIE_SECURE",
            _safe_bool(config.get("SESSION_COOKIE_SECURE")),
            f"Mevcut değer: {config.get('SESSION_COOKIE_SECURE')}",
        ),
        gate(
            "REMEMBER_COOKIE_SECURE",
            _safe_bool(config.get("REMEMBER_COOKIE_SECURE")),
            f"Mevcut değer: {config.get('REMEMBER_COOKIE_SECURE')}",
        ),
        gate(
            "PROXY_FIX_ENABLED",
            _safe_bool(config.get("PROXY_FIX_ENABLED")),
            f"Mevcut değer: {config.get('PROXY_FIX_ENABLED')}",
        ),
        gate(
            "MAINTENANCE_MODE kapalı",
            not _safe_bool(config.get("MAINTENANCE_MODE")),
            f"Mevcut değer: {config.get('MAINTENANCE_MODE')}",
            owner="BT / Yönetim",
        ),
        gate(
            "HEALTHCHECK_PATH tanımlı",
            bool(str(config.get("HEALTHCHECK_PATH") or "").strip()),
            f"Mevcut değer: {config.get('HEALTHCHECK_PATH') or '-'}",
        ),
    ]


def _build_backup_checks(config: dict[str, Any], project_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    backup_root = Path(str(config.get("BACKUP_ROOT") or project_root / "backups"))
    recent_backups = _find_recent_files(backup_root, days=14, patterns=("*.dump", "*.sql", "*.backup"))
    checks = [
        {
            "label": "Yedek klasörü erişilebilir",
            "status": "pass" if backup_root.exists() else "fail",
            "detail": str(backup_root),
            "owner": "BT",
        },
        {
            "label": "Son 14 günde yedek var",
            "status": "pass" if recent_backups else "warn",
            "detail": f"Bulunan yedek: {len(recent_backups)}",
            "owner": "BT",
        },
    ]
    summary = {
        "path": str(backup_root),
        "exists": backup_root.exists(),
        "recent_files": recent_backups,
    }
    return checks, summary


def _build_log_checks(config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    log_root = Path(str(config.get("LOG_FOLDER") or _project_root() / "logs"))
    recent_logs = _find_recent_files(log_root, days=7, patterns=("*.log", "*.txt"))
    checks = [
        {
            "label": "Log klasörü erişilebilir",
            "status": "pass" if log_root.exists() else "fail",
            "detail": str(log_root),
            "owner": "BT",
        },
        {
            "label": "Uygulama logu üretiliyor",
            "status": "pass" if any("app" in row["name"].lower() for row in recent_logs) else "warn",
            "detail": "bys360-app.log son günlerde güncellenmeli.",
            "owner": "BT",
        },
        {
            "label": "Operasyon logu üretiliyor",
            "status": "pass" if any("ops" in row["name"].lower() for row in recent_logs) else "warn",
            "detail": "bys360-ops.log son günlerde güncellenmeli.",
            "owner": "BT",
        },
    ]
    summary = {
        "path": str(log_root),
        "exists": log_root.exists(),
        "recent_files": recent_logs,
    }
    return checks, summary


def _gate_counts(gates: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"pass": 0, "warn": 0, "fail": 0}
    for gate in gates:
        status = str(gate.get("status") or "").strip().lower()
        if status in counts:
            counts[status] += 1
    return counts


def _score_from_gates(gates: list[dict[str, Any]]) -> int:
    if not gates:
        return 0
    pass_count = sum(1 for gate in gates if gate.get("status") == "pass")
    warn_count = sum(1 for gate in gates if gate.get("status") == "warn")
    total = len(gates)
    raw = ((pass_count * 1.0) + (warn_count * 0.5)) / total
    return int(round(raw * 100))


def build_go_live_readiness_context() -> dict[str, Any]:
    project_root = _project_root()
    env_path = project_root / ".env"
    config_map = dict(current_app.config)

    env_findings, env_suggestions = build_safe_env_patch(env_path, apply_safe_env=False)
    security_report = run_security_and_access_audit()

    env_gates = _build_env_checks(config_map)
    backup_gates, backup_summary = _build_backup_checks(config_map, project_root)
    log_gates, log_summary = _build_log_checks(config_map)

    gates: list[dict[str, Any]] = []
    gates.extend(env_gates)
    gates.extend(backup_gates)
    gates.extend(log_gates)

    if env_findings:
        gates.append(
            {
                "label": "Ortam dosyası güvenli öneri",
                "status": "warn" if not any(item.severity == "critical" for item in env_findings) else "fail",
                "detail": f".env incelemesinde {len(env_findings)} bulgu tespit edildi.",
                "owner": "BT",
            }
        )

    if security_report.critical_count > 0:
        gates.append(
            {
                "label": "Güvenlik kritik bulguları",
                "status": "fail",
                "detail": f"{security_report.critical_count} kritik bulgu var.",
                "owner": "BT / İdare",
            }
        )
    elif security_report.warning_count > 0:
        gates.append(
            {
                "label": "Güvenlik uyarıları",
                "status": "warn",
                "detail": f"{security_report.warning_count} uyarı kaydı var.",
                "owner": "BT / İdare",
            }
        )
    else:
        gates.append(
            {
                "label": "Güvenlik görünümü",
                "status": "pass",
                "detail": "Kritik bulgu görünmüyor.",
                "owner": "BT / İdare",
            }
        )

    counts = _gate_counts(gates)
    readiness_score = _score_from_gates(gates)

    if counts["fail"] > 0:
        decision = "Blokajlar kapanmadan canlıya geçmeyin"
        tone = "danger"
    elif counts["warn"] > 0:
        decision = "Canlıya yakın, ama kontrollü kapanış gerekli"
        tone = "warning"
    else:
        decision = "Canlıya çıkış için görünüm güçlü"
        tone = "success"

    blockers = [gate for gate in gates if gate.get("status") == "fail"]
    warnings = [gate for gate in gates if gate.get("status") == "warn"]
    highlights = [
        {
            "title": "Hazırlık skoru",
            "body": f"Genel canlıya hazırlık skoru {readiness_score}/100 görünüyor.",
        },
        {
            "title": "Güvenlik görünümü",
            "body": f"Kritik: {security_report.critical_count} · Uyarı: {security_report.warning_count} · Bilgi: {security_report.info_count}",
        },
        {
            "title": "Yedek ve log takibi",
            "body": f"Son 14 günde {len(backup_summary['recent_files'])} yedek, son 7 günde {len(log_summary['recent_files'])} log hareketi bulundu.",
        },
    ]

    return {
        "generated_at": datetime.now(),
        "project_root": str(project_root),
        "env_path": str(env_path),
        "readiness_score": readiness_score,
        "rollout_decision": decision,
        "rollout_tone": tone,
        "counts": counts,
        "gates": gates,
        "blockers": blockers,
        "warnings": warnings,
        "highlights": highlights,
        "security_report": security_report.to_dict(),
        "env_findings": [asdict(item) for item in env_findings],
        "env_suggestions": _mask_suggestions(env_suggestions),
        "backup_summary": backup_summary,
        "log_summary": log_summary,
    }