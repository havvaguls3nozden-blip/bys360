
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path


PLACEHOLDERS = {
    "",
    "CHANGE_ME",
    "changeme",
    "change_me",
    "placeholder",
    "dummy",
    "none",
    "null",
    "your-secret-key",
    "your-sentry-dsn",
    "set_in_production",
    "__SET_IN_PRODUCTION__",
}


REQUIRED_KEYS = [
    "SECRET_KEY",
    "DATABASE_URL",
    "SENTRY_DSN",
    "SESSION_COOKIE_SECURE",
    "REMEMBER_COOKIE_SECURE",
    "WTF_CSRF_ENABLED",
    "CSP_ENABLED",
]


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value

    return values


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def falsy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"0", "false", "no", "off", ""}


def is_placeholder(value: str | None) -> bool:
    clean = str(value or "").strip()
    return clean in PLACEHOLDERS or clean.lower() in PLACEHOLDERS


def mask_value(key: str, value: str | None) -> str:
    if value is None:
        return ""
    if any(token in key.upper() for token in ["SECRET", "PASSWORD", "TOKEN", "KEY", "DSN"]):
        return "***MASKED***" if value else ""
    return value


def validate(values: dict[str, str], source_name: str, strict: bool) -> dict:
    findings = []

    def add(rule: str, severity: str, status: str, message: str, key: str = "") -> None:
        findings.append(
            {
                "rule": rule,
                "severity": severity,
                "status": status,
                "key": key,
                "message": message,
            }
        )

    for key in REQUIRED_KEYS:
        value = values.get(key)
        if value is None:
            add("REQUIRED_KEY_PRESENT", "high", "fail" if strict else "warn", f"{key} tan?ml? de?il.", key)
        elif is_placeholder(value):
            add("NO_PLACEHOLDER_VALUE", "high", "fail" if strict else "warn", f"{key} placeholder/bo? g?r?n?yor.", key)
        else:
            add("REQUIRED_KEY_PRESENT", "info", "pass", f"{key} tan?ml?.", key)

    secret = values.get("SECRET_KEY", "")
    if secret and not is_placeholder(secret) and len(secret) >= 32:
        add("SECRET_KEY_STRONG", "info", "pass", "SECRET_KEY uzunlu?u yeterli.", "SECRET_KEY")
    else:
        add("SECRET_KEY_STRONG", "high", "fail" if strict else "warn", "SECRET_KEY en az 32 karakter ve placeholder olmayan de?er olmal?.", "SECRET_KEY")

    db_url = values.get("DATABASE_URL") or values.get("SQLALCHEMY_DATABASE_URI") or ""
    if db_url:
        if db_url.startswith("postgresql"):
            add("DATABASE_IS_POSTGRESQL", "info", "pass", "DATABASE_URL PostgreSQL g?r?n?yor.", "DATABASE_URL")
        else:
            add("DATABASE_IS_POSTGRESQL", "high", "fail" if strict else "warn", "Canl?/pilot DATABASE_URL PostgreSQL olmal?.", "DATABASE_URL")

        if "sslmode=disable" in db_url.lower():
            add("DATABASE_SSL_NOT_DISABLED", "high", "fail", "DATABASE_URL i?inde sslmode=disable var.", "DATABASE_URL")
        elif re.search(r"sslmode=(require|verify-ca|verify-full)", db_url, flags=re.I):
            add("DATABASE_SSL_NOT_DISABLED", "info", "pass", "DATABASE_URL SSL modu g?venli g?r?n?yor.", "DATABASE_URL")
        else:
            add("DATABASE_SSL_NOT_DISABLED", "high", "fail" if strict else "warn", "DATABASE_URL i?inde sslmode=require/verify-ca/verify-full beklenir.", "DATABASE_URL")
    else:
        add("DATABASE_IS_POSTGRESQL", "high", "fail" if strict else "warn", "DATABASE_URL yok.", "DATABASE_URL")

    sentry = values.get("SENTRY_DSN", "")
    if sentry and not is_placeholder(sentry) and sentry.startswith(("http://", "https://")):
        add("SENTRY_DSN_VALID_SHAPE", "info", "pass", "SENTRY_DSN bi?imi uygun g?r?n?yor.", "SENTRY_DSN")
    else:
        add("SENTRY_DSN_VALID_SHAPE", "high", "fail" if strict else "warn", "Canl?/pilot i?in ger?ek SENTRY_DSN gerekir.", "SENTRY_DSN")

    debug_values = [
        values.get("DEBUG"),
        values.get("FLASK_DEBUG"),
    ]
    if any(truthy(v) for v in debug_values):
        add("DEBUG_DISABLED", "high", "fail", "DEBUG/FLASK_DEBUG a??k g?r?n?yor.", "DEBUG")
    else:
        add("DEBUG_DISABLED", "info", "pass", "DEBUG/FLASK_DEBUG a??k de?il.", "DEBUG")

    for key in ["SESSION_COOKIE_SECURE", "REMEMBER_COOKIE_SECURE"]:
        if truthy(values.get(key)):
            add("SECURE_COOKIE_ENABLED", "info", "pass", f"{key}=true.", key)
        else:
            add("SECURE_COOKIE_ENABLED", "medium", "fail" if strict else "warn", f"{key}=true olmal?.", key)

    if values.get("WTF_CSRF_ENABLED") is not None and falsy(values.get("WTF_CSRF_ENABLED")):
        add("CSRF_ENABLED", "high", "fail", "WTF_CSRF_ENABLED false g?r?n?yor.", "WTF_CSRF_ENABLED")
    else:
        add("CSRF_ENABLED", "info", "pass", "CSRF kapal? g?r?nm?yor.", "WTF_CSRF_ENABLED")

    if values.get("CSP_ENABLED") is not None and falsy(values.get("CSP_ENABLED")):
        add("CSP_ENABLED", "medium", "fail" if strict else "warn", "CSP_ENABLED false g?r?n?yor.", "CSP_ENABLED")
    else:
        add("CSP_ENABLED", "info", "pass", "CSP kapal? g?r?nm?yor.", "CSP_ENABLED")

    failed = [f for f in findings if f["status"] == "fail"]
    warned = [f for f in findings if f["status"] == "warn"]
    passed = [f for f in findings if f["status"] == "pass"]

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": source_name,
        "strict": strict,
        "passed": len(passed),
        "warnings": len(warned),
        "failed": len(failed),
        "ok": len(failed) == 0,
        "masked_values": {k: mask_value(k, v) for k, v in values.items() if k in REQUIRED_KEYS or k in {"DEBUG", "FLASK_DEBUG", "SQLALCHEMY_DATABASE_URI"}},
        "findings": findings,
    }


def write_reports(result: dict) -> None:
    out_json = Path("reports/security/BYS360_A6E_PRODUCTION_ENV_CONTRACT_REPORT.json")
    out_md = Path("reports/security/BYS360_A6E_PRODUCTION_ENV_CONTRACT_REPORT.md")

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A?ama 6E ?retim Ortam De?i?kenleri S?zle?mesi",
        "",
        f"Tarih: {result['generated_at']}",
        f"Kaynak: {result['source']}",
        f"Strict mod: {result['strict']}",
        "",
        "## ?zet",
        "",
        f"- OK: {result['ok']}",
        f"- Passed: {result['passed']}",
        f"- Warnings: {result['warnings']}",
        f"- Failed: {result['failed']}",
        "",
        "## Bulgular",
        "",
    ]

    for f in result["findings"]:
        lines.extend(
            [
                f"### {f['status'].upper()} ? {f['rule']}",
                f"- Seviye: {f['severity']}",
                f"- Anahtar: `{f['key']}`",
                f"- Mesaj: {f['message']}",
                "",
            ]
        )

    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("A6E_ENV_CONTRACT_JSON:", out_json)
    print("A6E_ENV_CONTRACT_MD:", out_md)
    print("A6E_OK:", result["ok"])
    print("A6E_PASSED:", result["passed"])
    print("A6E_WARNINGS:", result["warnings"])
    print("A6E_FAILED:", result["failed"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=".env.production.example")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    env_path = Path(args.env_file)
    values = parse_env_file(env_path)
    values.update({k: v for k, v in os.environ.items() if k in REQUIRED_KEYS or k in {"DEBUG", "FLASK_DEBUG", "SQLALCHEMY_DATABASE_URI"}})

    result = validate(values, str(env_path), strict=args.strict)
    write_reports(result)

    return 1 if args.strict and not result["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
