from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

DANGEROUS_PASSWORD_PATTERNS = [
    r'initial_password\s*=\s*["\']123456["\']',
    r'initial_password\s*=\s*["\']123456["\']\s*,',
    r'set_password\(\s*["\']123456["\']\s*\)',
    r'password_hash\s*=\s*generate_password_hash\(\s*["\']123456["\']\s*\)',
]

PLACEHOLDER_SENTRY_TOKENS = (
    '${SENTRY_DSN}',
    'sentry.io/...',
    'your-public-key',
    'project-id',
    'change-me',
)

SKIP_DIRS = {
    '.git', '.venv', 'venv', '__pycache__', '.pytest_cache', 'node_modules',
    'build', 'dist', 'release', 'reports', 'logs', 'uploads', 'media',
    '.dart_tool', '.gradle', '.idea', '.vscode',
}


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')


def iter_source_files(root: Path):
    for path in root.rglob('*'):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in {'.py', '.html', '.js', '.css', '.ps1', '.md', '.txt', '.env', '.example'}:
            yield path


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


def postgres_sslmode_is_disable(db_url: str) -> bool:
    parsed = urlparse((db_url or '').strip())
    if not (parsed.scheme or '').lower().startswith('postgres'):
        return False
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    return (query.get('sslmode') or '').strip().lower() == 'disable'


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
    ]
    for file_path in required_files:
        if not file_path.exists():
            failures.append(f'Eksik dosya: {file_path.relative_to(root)}')

    gitignore = read_text(root / '.gitignore') if (root / '.gitignore').exists() else ''
    if '.env' not in gitignore or '!.env.example' not in gitignore:
        failures.append('.gitignore içinde .env dışlama kuralı yok veya .env.example istisnası eksik.')

    for source in iter_source_files(root / 'app'):
        text = read_text(source)
        for pattern in DANGEROUS_PASSWORD_PATTERNS:
            if re.search(pattern, text):
                failures.append(f'Tehlikeli sabit ilk şifre kalmış: {source.relative_to(root)} :: {pattern}')

    bootstrap = read_text(root / 'app' / 'bootstrap' / 'application_bootstrap.py') if (root / 'app' / 'bootstrap' / 'application_bootstrap.py').exists() else ''
    if 'configure_optional_sentry(app)' not in bootstrap:
        failures.append('Sentry bootstrap akışına bağlanmamış.')

    monitoring = read_text(root / 'app' / 'core' / 'monitoring.py') if (root / 'app' / 'core' / 'monitoring.py').exists() else ''
    if '_looks_like_placeholder_dsn' not in monitoring or 'bys360_sentry_enabled' not in monitoring:
        failures.append('Sentry placeholder kontrolü veya etkinlik işareti eksik.')

    config = read_text(root / 'config.py') if (root / 'config.py').exists() else ''
    if 'DB_ALLOW_SSL_DISABLE' not in config or 'query[\'sslmode\'] = requested_sslmode' not in config:
        failures.append('DB SSL disable değerini production/staging için güvenli değere yükselten kontrol eksik.')
    if 'CSP_NONCE_ENABLED' not in config or 'CSP_ALLOW_UNSAFE_INLINE_SCRIPT' not in config:
        failures.append('CSP nonce ayarları config içinde yok.')
    if 'CSP_SCRIPT_SRC = os.getenv(\'CSP_SCRIPT_SRC\', "\'self\' https:")' not in config:
        failures.append('CSP_SCRIPT_SRC varsayılanı unsafe-inline içermeyecek şekilde güncellenmemiş.')

    headers = read_text(root / 'app' / 'security' / 'headers.py') if (root / 'app' / 'security' / 'headers.py').exists() else ''
    script_default_match = re.search(r'"script-src"\s*:\s*"([^"]*)"', headers)
    script_default = script_default_match.group(1) if script_default_match else ''
    if 'inject_csp_nonce_into_html' not in headers or "'unsafe-inline'" in script_default:
        failures.append('CSP header/nonce uygulaması eksik veya DEFAULT_CSP script tarafında unsafe-inline içeriyor.')

    env = parse_env(root / '.env')
    sentry_dsn = env.get('SENTRY_DSN', '')
    if sentry_dsn and any(token in sentry_dsn.lower() for token in PLACEHOLDER_SENTRY_TOKENS):
        failures.append('.env içindeki SENTRY_DSN placeholder görünüyor; gerçek DSN girilmeli veya boş bırakılmalı.')
    if postgres_sslmode_is_disable(env.get('DATABASE_URL', '')) and env.get('APP_ENV', '').lower() in {'production', 'staging'}:
        failures.append('.env DATABASE_URL production/staging için sslmode=disable içeriyor; sslmode=require yapılmalı.')

    if failures:
        print('BYS360_P0_SECURITY_OBSERVABILITY_V1_GATE_FAIL')
        for item in failures:
            print(' - ' + item)
        return 1

    print('BYS360_P0_SECURITY_OBSERVABILITY_V1_GATE_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
