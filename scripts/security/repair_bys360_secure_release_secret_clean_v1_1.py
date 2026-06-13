from __future__ import annotations

import argparse
import re
from pathlib import Path

MARKER = "# BYS360 secure release secret clean v1.1"

ENV_EXAMPLE = """# BYS360 environment template
# Bu dosya örnektir. Gerçek parola, DSN veya API anahtarı yazmayın.

APP_ENV=development
FLASK_ENV=development
APP_BASE_URL=http://127.0.0.1:8000

SECRET_KEY=CHANGE_ME_GENERATE_STRONG_SECRET
DATABASE_URL=DB_CONNECTION_STRING_SUPPLIED_BY_ENVIRONMENT
SQLALCHEMY_DATABASE_URI=DB_CONNECTION_STRING_SUPPLIED_BY_ENVIRONMENT
DB_SSLMODE=require
DB_ALLOW_SSL_DISABLE=false

SENTRY_DSN=
SENTRY_ENVIRONMENT=development
SENTRY_REQUIRED_IN_PRODUCTION=false

AI_API_KEY=
REDIS_URL=redis://127.0.0.1:6379/0
CACHE_REDIS_URL=redis://127.0.0.1:6379/1
SECURITY_RATE_LIMIT_REDIS_URL=redis://127.0.0.1:6379/2
BYS360_DEPLOYMENT_MODE=local

CSP_ENABLED=true
CSP_REPORT_ONLY=true
CSP_NONCE_ENABLED=true
CSP_ALLOW_UNSAFE_INLINE_SCRIPT=false
"""

GITIGNORE_BLOCK = """
# BYS360 secure release secret clean v1.1
.env
.env.*
!.env.example
*.env.backup*
*.bak
*.backup
*.dump
*.sql.dump
*.db
*.sqlite
*.sqlite3
*.log
logs/
log/
instance/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
.venv/
venv/
dist/
dist_secure/
_upload_parts/
*.zip
*.7z
*.rar
""".strip()

RUNBOOK = """# BYS360 Güvenli Release ve Secret Temizliği V1.1

Bu runbook, geliştirme klasöründen güvenli release paketi üretmek için kullanılır.

## Amaç

- Gerçek `.env` dosyalarının release paketine girmesini engellemek.
- `.env.example` dosyasını yalnızca örnek anahtarlarla tutmak.
- Sabit ilk şifre kullanımını kaldırmak.
- Secret taramasında gate araçlarının kendi imzalarını yanlışlıkla bulmasını engellemek.

## Kullanım

```powershell
cd C:\\bys360\\project
powershell -ExecutionPolicy Bypass -File .\\scripts\\security\\repair_bys360_secure_release_secret_clean_v1_1.ps1 -ProjectRoot "C:\\bys360\\project"
python -m compileall app config.py scripts
powershell -ExecutionPolicy Bypass -File .\\scripts\\security\\check_bys360_secure_release_secret_clean_v1_1.ps1 -ProjectRoot "C:\\bys360\\project"
powershell -ExecutionPolicy Bypass -File .\\scripts\\windows\\build_bys360_secure_release_v1_1.ps1 -ProjectRoot "C:\\bys360\\project"
```

## Not

Canlı Sentry DSN ve canlı veritabanı parolası `.env.example` içine yazılmaz. Gerçek değerler sadece sunucudaki `.env` içinde tutulur.
"""

PASSWORD_HELPER = '''"""BYS360 secure password helpers."""
from __future__ import annotations

import secrets
import string


def generate_initial_password(length: int = 14) -> str:
    """Generate a strong temporary password for new users."""
    length = max(12, int(length or 14))
    alphabet = string.ascii_letters + string.digits + "!@#$%*-_"
    while True:
        value = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.islower() for c in value)
            and any(c.isupper() for c in value)
            and any(c.isdigit() for c in value)
            and any(c in "!@#$%*-_" for c in value)
        ):
            return value
'''


def ensure_gitignore(project: Path) -> None:
    p = project / ".gitignore"
    current = p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""
    if MARKER not in current:
        if current and not current.endswith("\n"):
            current += "\n"
        current += "\n" + GITIGNORE_BLOCK + "\n"
        p.write_text(current, encoding="utf-8")


def write_env_example(project: Path) -> None:
    (project / ".env.example").write_text(ENV_EXAMPLE, encoding="utf-8")


def ensure_password_helper(project: Path) -> None:
    p = project / "app" / "security" / "passwords.py"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists() or "generate_initial_password" not in p.read_text(encoding="utf-8", errors="ignore"):
        p.write_text(PASSWORD_HELPER, encoding="utf-8")


def patch_hardcoded_passwords(project: Path) -> None:
    app_dir = project / "app"
    if not app_dir.exists():
        return
    for p in app_dir.rglob("*.py"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        original = text
        text = re.sub(r'initial_password\s*=\s*["\']123456["\']', 'initial_password = generate_initial_password()', text)
        text = re.sub(r'\.set_password\(\s*["\']123456["\']\s*\)', '.set_password(generate_initial_password())', text)
        text = re.sub(r'set_password\(\s*["\']123456["\']\s*\)', 'set_password(generate_initial_password())', text)
        if text != original:
            if "generate_initial_password" not in original:
                lines = text.splitlines()
                insert_at = 0
                for i, line in enumerate(lines[:80]):
                    if line.startswith("from __future__"):
                        insert_at = i + 1
                lines.insert(insert_at, "from app.security.passwords import generate_initial_password")
                text = "\n".join(lines) + ("\n" if original.endswith("\n") else "")
            p.write_text(text, encoding="utf-8")


def sanitize_docs(project: Path) -> None:
    docs = project / "docs" / "security"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "SECURE_RELEASE_SECRET_CLEAN_V1_1_RUNBOOK.md").write_text(RUNBOOK, encoding="utf-8")
    for p in docs.glob("*.md"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        text = text.replace("SENTRY_DSN_DEGERI_BU_DOSYAYA_YAZILMAZ", "SENTRY_DSN gerçek değerini Sentry proje ayarlarından alın")
        text = re.sub(r"SENTRY_DSN\s*=\s*https://[^\s]+", "SENTRY_DSN=", text)
        p.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    project = Path(args.project_root).resolve()
    ensure_gitignore(project)
    write_env_example(project)
    ensure_password_helper(project)
    patch_hardcoded_passwords(project)
    sanitize_docs(project)
    print("BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_1_REPAIR_OK")


if __name__ == "__main__":
    main()
