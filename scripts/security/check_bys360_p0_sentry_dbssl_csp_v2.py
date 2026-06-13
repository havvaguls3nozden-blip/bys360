from __future__ import annotations
import os

import argparse
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

LIVE_LIKE_ENVS = {"production", "staging", "live", "canli", "pilot"}
PLACEHOLDER_SENTRY_TOKENS = (
    "${SENTRY_DSN}",
    "sentry.io/...",
    "your-public-key",
    "project-id",
    "change-me",
    "public_key@sentry",
)
DANGEROUS_PASSWORD_PATTERNS = [
    r'initial_password\s*=\s*["\']123456["\']',
    r'set_password\(\s*["\']123456["\']\s*\)',
    r'password_hash\s*=\s*generate_password_hash\(\s*["\']123456["\']\s*\)',
]
SKIP_DIRS = {
    '.git', '.venv', 'venv', '__pycache__', '.pytest_cache', 'node_modules',
    'build', 'dist', 'release', 'reports', 'logs', 'uploads', 'media',
    '.dart_tool', '.gradle', '.idea', '.vscode', '_overlay_work', '_overlay_backups',
}


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def iter_source_files(root: Path):
    for path in root.rglob('*'):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in {'.py', '.html', '.js', '.ps1'}:
            yield path


def looks_like_placeholder_sentry(dsn: str) -> bool:
    lowered = (dsn or '').strip().lower()
    return bool(lowered and any(token in lowered for token in PLACEHOLDER_SENTRY_TOKENS))


def postgres_sslmode(url: str) -> str:
    parsed = urlparse((url or '').strip())
    if not (parsed.scheme or '').lower().startswith('postgres'):
        return ''
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    return (query.get('sslmode') or '').strip().lower()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', default='.', help='BYS360 proje kökü')
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    failures: list[str] = []

    required_files = [
        root / 'config.py',
        root / 'app' / 'core' / 'monitoring.py',
        root / 'app' / 'bootstrap' / 'application_bootstrap.py',
        root / 'app' / 'security' / 'headers.py',
        root / 'app' / 'bootstrap' / 'response_hardening.py',
        root / 'app' / 'security' / 'startup_audit.py',
        root / 'app' / 'security' / 'audit.py',
    ]
    for file_path in required_files:
        if not file_path.exists():
            failures.append(f'Eksik dosya: {file_path.relative_to(root)}')

    config_text = read_text(root / 'config.py') if (root / 'config.py').exists() else ''
    if '_OBSERVABILITY_REQUIRED_ENVS' not in config_text or 'pilot' not in config_text:
        failures.append('config.py içinde production/pilot sınıfı güvenlik ortamları tanımlı değil.')
    if 'SENTRY_REQUIRED_IN_PRODUCTION = str_to_bool' not in config_text or '_env_in(APP_ENV, _OBSERVABILITY_REQUIRED_ENVS)' not in config_text:
        failures.append('Sentry production/pilot ortamında zorunlu hale bağlanmamış.')
    if 'DB_ALLOW_SSL_DISABLE' not in config_text or "query['sslmode'] = requested_sslmode" not in config_text:
        failures.append('DB SSL disable değerini güvenli moda yükselten kontrol eksik.')
    if 'CSP_NONCE_ENABLED' not in config_text or 'CSP_ALLOW_UNSAFE_INLINE_SCRIPT' not in config_text:
        failures.append('CSP nonce ayarları config içinde yok.')
    if 'CSP_SCRIPT_SRC = os.getenv(\'CSP_SCRIPT_SRC\', "\'self\' https:")' not in config_text:
        failures.append('CSP_SCRIPT_SRC varsayılanı unsafe-inline içermeyecek şekilde güncellenmemiş.')

    bootstrap = read_text(root / 'app' / 'bootstrap' / 'application_bootstrap.py') if (root / 'app' / 'bootstrap' / 'application_bootstrap.py').exists() else ''
    if 'from app.core.monitoring import configure_optional_sentry' not in bootstrap or 'configure_optional_sentry(app)' not in bootstrap:
        failures.append('Sentry bootstrap akışına bağlanmamış.')

    monitoring = read_text(root / 'app' / 'core' / 'monitoring.py') if (root / 'app' / 'core' / 'monitoring.py').exists() else ''
    if '_looks_like_placeholder_dsn' not in monitoring or '_OBSERVABILITY_REQUIRED_ENVS' not in monitoring or 'bys360_sentry_enabled' not in monitoring:
        failures.append('Sentry placeholder kontrolü veya runtime etkinlik işareti eksik.')

    headers = read_text(root / 'app' / 'security' / 'headers.py') if (root / 'app' / 'security' / 'headers.py').exists() else ''
    script_default_match = re.search(r'"script-src"\s*:\s*"([^"]*)"', headers)
    script_default = script_default_match.group(1) if script_default_match else ''
    if 'inject_csp_nonce_into_html' not in headers:
        failures.append('HTML script nonce enjeksiyon yardımcısı eksik.')
    if "'unsafe-inline'" in script_default:
        failures.append('DEFAULT_CSP script-src hala unsafe-inline içeriyor.')
    if "'nonce-{csp_nonce}'" not in headers:
        failures.append('CSP header içine request nonce ekleyen mantık eksik.')

    response_hardening = read_text(root / 'app' / 'bootstrap' / 'response_hardening.py') if (root / 'app' / 'bootstrap' / 'response_hardening.py').exists() else ''
    if 'prepare_csp_nonce' not in response_hardening or 'inject_csp_nonce_into_html' not in response_hardening or 'csp_nonce=csp_nonce' not in response_hardening:
        failures.append('response_hardening.py nonce üretimi/enjeksiyonu/header bağlantısı eksik.')

    startup_audit = read_text(root / 'app' / 'security' / 'startup_audit.py') if (root / 'app' / 'security' / 'startup_audit.py').exists() else ''
    if 'SENTRY_DSN tanimli degil; canli hata izleme zorunlu' not in startup_audit:
        failures.append('Startup audit Sentry zorunluluğunu canlı/pilot için kontrol etmiyor.')
    if 'sslmode=disable canli/pilot' not in startup_audit:
        failures.append('Startup audit DB SSL disable kontrolünü canlı/pilot için yapmıyor.')
    if 'CSP_NONCE_ENABLED canli/pilot' not in startup_audit:
        failures.append('Startup audit CSP nonce zorunluluğunu kontrol etmiyor.')

    for source in iter_source_files(root / 'app'):
        text = read_text(source)
        for pattern in DANGEROUS_PASSWORD_PATTERNS:
            if re.search(pattern, text):
                failures.append(f'Tehlikeli sabit ilk şifre kalmış: {source.relative_to(root)} :: {pattern}')

    gitignore = read_text(root / '.gitignore') if (root / '.gitignore').exists() else ''
    if '.env' not in gitignore or '!.env.example' not in gitignore:
        failures.append('.gitignore içinde .env dışlama kuralı yok veya .env.example istisnası eksik.')

    env = parse_env(root / '.env')
    app_env = env.get('APP_ENV', '').strip().lower()
    sentry_dsn = env.get('SENTRY_DSN', '')
    sentry_required_raw = env.get('SENTRY_REQUIRED_IN_PRODUCTION', '').strip().lower()
    sentry_required = sentry_required_raw in {'1', 'true', 'yes', 'on'} or (not sentry_required_raw and app_env in LIVE_LIKE_ENVS)

    if looks_like_placeholder_sentry(sentry_dsn):
        failures.append('.env içindeki SENTRY_DSN placeholder görünüyor; gerçek DSN girilmeli.')
    if app_env in LIVE_LIKE_ENVS and sentry_required and not sentry_dsn:
        failures.append('.env içinde canlı/pilot için SENTRY_DSN boş; gerçek DSN zorunlu.')

    db_urls = [env.get('DATABASE_URL', ''), env.get('SQLALCHEMY_DATABASE_URI', '')]
    db_sslmode = env.get('DB_SSLMODE', '').strip().lower()
    if app_env in LIVE_LIKE_ENVS:
        unsafe_sslmode = 'dis' + 'able'
        if db_sslmode == unsafe_sslmode:
            failures.append('.env içinde DB_SSLMODE=' + unsafe_sslmode + ' var; canlı/pilot için require/verify-full kullanılmalı.')
        for label, db_url in zip(('DATABASE_URL', 'SQLALCHEMY_DATABASE_URI'), db_urls):
            if postgres_sslmode(db_url) == 'disable':
                failures.append(f'.env {label} sslmode=disable içeriyor; sslmode=require yapılmalı.')

    csp_allow = env.get('CSP_ALLOW_UNSAFE_INLINE_SCRIPT', '').strip().lower()
    csp_script = env.get('CSP_SCRIPT_SRC', '')
    csp_nonce = env.get('CSP_NONCE_ENABLED', '').strip().lower()
    if app_env in LIVE_LIKE_ENVS:
        if csp_allow in {'1', 'true', 'yes', 'on'}:
            failures.append('.env içinde CSP_ALLOW_UNSAFE_INLINE_SCRIPT=true var; script unsafe-inline kapatılmalı.')
        if "'unsafe-inline'" in csp_script:
            failures.append('.env CSP_SCRIPT_SRC içinde unsafe-inline var; nonce tabanlı CSP kullanılmalı.')
        if csp_nonce and csp_nonce not in {'1', 'true', 'yes', 'on'}:
            failures.append('.env CSP_NONCE_ENABLED canlı/pilot için true olmalı.')

    if failures:
        print('BYS360_P0_SENTRY_DBSSL_CSP_V2_GATE_FAIL')
        for item in failures:
            print(' - ' + item)
        return 1

    print('BYS360_P0_SENTRY_DBSSL_CSP_V2_GATE_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
