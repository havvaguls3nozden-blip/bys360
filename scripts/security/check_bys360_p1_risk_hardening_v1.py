from __future__ import annotations

import os
import re
import sys
from pathlib import Path

MARKERS = {
    "app/services/personnel/excel_import_guard.py": ["validate_personnel_import_rows_for_commit", "MOJIBAKE_MARKERS", "mükerrer Sicil No"],
    "app/admin/ops_routes.py": ["validate_personnel_import_rows_for_commit", "Excel ön kontrolü başarısız"],
    "app/admin/routes.py": ["validate_personnel_import_rows_for_commit", "rows_for_preflight"],
    "app/ai/routes.py": ["get_provider_snapshot", "provider_status", "ai_provider_snapshot"],
    "app/templates/ai_decision/faz1_health_layout.html": ["AI sağlayıcı kontrolü gerekli", "decision-provider-warning-v1"],
    "app/services/performance/period_state_guard.py": ["validate_scoring_window", "validate_publish_window", "Puanlama dönemi henüz başlamadı"],
    "app/services/performance_v2/evaluation_workspace.py": ["ensure_scoring_window_open(assignment.period)"],
    "app/services/performance_v2/publish_workspace.py": ["validate_publish_window(period)", "validate_unpublish_allowed(period)"],
    "app/pwa/routes.py": ["/pwa/csrf-refresh", "X-BYS360-CSRF-Refresh"],
    "app/services/redis_config_guard.py": ["sanitize_redis_url", "redis_url_docker_hostname_unresolved"],
    "config.py": ["_normalize_runtime_redis_url", "PDF_EXPORT_MAX_ROWS_INLINE", "REDIS_CONFIG_WARNING"],
    "app/services/pdf_export_guard.py": ["validate_inline_pdf_export", "PDF_EXPORT_MAX_ROWS_INLINE"],
    "app/performance/reporting_routes.py": ["validate_inline_pdf_export", "Performans raporu PDF"],
}


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def env_pairs(env_path: Path) -> dict[str, str]:
    if not env_path.exists():
        return {}
    rows: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        rows[k.strip()] = v.strip().strip('"').strip("'")
    return rows


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    failures: list[str] = []
    warnings: list[str] = []
    for rel, needles in MARKERS.items():
        path = root / rel
        if not path.exists():
            failures.append(f"eksik dosya: {rel}")
            continue
        text = read(path)
        for needle in needles:
            if needle not in text:
                failures.append(f"marker bulunamadı: {rel} -> {needle}")

    env = env_pairs(root / ".env")
    for key in ("REDIS_URL", "CACHE_REDIS_URL", "SECURITY_RATE_LIMIT_REDIS_URL"):
        value = env.get(key, "")
        if re.search(r"redis://redis(:|/|$)", value, flags=re.I) and env.get("BYS360_DEPLOYMENT_MODE", "").lower() not in {"docker", "compose", "container"}:
            warnings.append(f".env {key}=redis://redis... bare-metal/canlı için riskli; runtime güvenli fallback uygular. Kalıcı çözüm: 127.0.0.1/gerçek host kullanın veya BYS360_DEPLOYMENT_MODE=docker belirtin.")

    if env.get("AI_PROVIDER_MODE", "").lower() == "openai_compatible" and not env.get("AI_API_KEY"):
        warnings.append("AI_PROVIDER_MODE=openai_compatible fakat AI_API_KEY boş; kullanıcı görünür ekranda sağlayıcı uyarısı gösterilecek, canlı model çalışmayacak.")

    if failures:
        print("BYS360_P1_RISK_HARDENING_V1_GATE_FAIL")
        for failure in failures:
            print(" - " + failure)
        return 1
    print("BYS360_P1_RISK_HARDENING_V1_GATE_OK")
    for warning in warnings:
        print(" - UYARI: " + warning)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
