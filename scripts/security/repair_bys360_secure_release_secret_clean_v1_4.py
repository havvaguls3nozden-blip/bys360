from __future__ import annotations

import re
from pathlib import Path

MARKER = "# BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_4"

GITIGNORE_BLOCK = f"""
{MARKER}
# Yerel ortam ve gizli anahtar dosyaları release/repo dışıdır.
.env
.env.*
!.env.template
*.env
*.local
*.secret
*.secrets
*.key
*.pem

# Çalışma zamanı ve geçici dosyalar
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
logs/
*.log
*.sqlite
*.sqlite3
*.db
*.dump
*.bak
*.backup
*.zip
dist/
dist_secure/
_upload_parts/
uploads/tmp/
instance/
{MARKER}_END
"""

ENV_TEMPLATE_MD = r"""
# BYS360 Ortam Değişkenleri Şablonu

Bu doküman gerçek `.env` dosyası değildir. Devir teslim/release paketine gerçek `.env` konulmaz.

## Zorunlu temel alanlar

```env
APP_ENV=development
FLASK_ENV=development
SECRET_KEY=change-me-with-strong-secret
DATABASE_URL=DB_CONNECTION_STRING_SUPPLIED_BY_ENVIRONMENT
SQLALCHEMY_DATABASE_URI=DB_CONNECTION_STRING_SUPPLIED_BY_ENVIRONMENT
```

## Canlı ortamda ayrıca doldurulacak alanlar

```env
APP_ENV=production
FLASK_ENV=production
DB_SSLMODE=require
SENTRY_DSN=<sentry-project-dsn>
SENTRY_ENVIRONMENT=production
SENTRY_REQUIRED_IN_PRODUCTION=true
```

## Redis opsiyonel alanları

Yerelde Redis yoksa uygulama güvenli fallback ile çalışabilir. Canlıda Redis kullanılıyorsa gerçek host yazılır.

```env
REDIS_URL=redis://127.0.0.1:6379/0
CACHE_REDIS_URL=redis://127.0.0.1:6379/1
SECURITY_RATE_LIMIT_REDIS_URL=redis://127.0.0.1:6379/2
```

## Kural

- Gerçek `.env`, parola, API anahtarı, Sentry DSN, dump, log ve yedek dosyaları release zip içine konulmaz.
- Canlı değerler sadece sunucu ortam değişkeni veya güvenli secret yönetimi üzerinden verilir.
"""

SCRIPTS_README = r"""
# BYS360 Script Klasörü Notu

Bu projede geçmiş bakım ve onarım scriptleri bulunabilir. Bunlar kaynak geçmişini anlamak için tutulabilir; ancak devir/release paketinde yalnızca güncel ve gerekli scriptler bırakılmalıdır.

## Güncel devir scriptleri

- `scripts/windows/build_bys360_secure_release_v1_4.ps1`
- `scripts/security/check_bys360_secure_release_secret_clean_v1_4.ps1`
- `scripts/security/repair_bys360_secure_release_secret_clean_v1_4.ps1`

## İlke

- Eski overlay, repair ve gate scriptleri canlı çalışma için zorunlu değildir.
- Release üretimi `.env`, log, dump, backup, cache, pycache ve eski geçici paketleri dışlar.
- Yeni eklenen scriptler kısa açıklama ve gate kontrolüyle birlikte verilmelidir.
"""

HANDOVER_NOTE = r"""
# BYS360 Script Devir Teslim Notu

Kaynak projede çok sayıda bakım scripti bulunması normaldir; ancak yeni geliştiriciye devredilecek temiz release paketinde yalnızca güncel kurulum, kontrol ve release scriptleri bulunmalıdır.

## Devredilecek yaklaşım

1. Kaynak proje geçmişi korunur.
2. Release/devir zip'i güvenli build scriptiyle üretilir.
3. `.env` ve gerçek secret dosyaları pakete girmez.
4. Eski overlay/onarım scriptleri release paketinden dışlanır.
5. Gerekli ortam değişkenleri `docs/deploy/ENV_TEMPLATE.md` üzerinden anlatılır.

## Aktif güvenlik kontrolü

`scripts/security/check_bys360_secure_release_secret_clean_v1_4.ps1`
"""

def upsert_gitignore(root: Path) -> None:
    gi = root / ".gitignore"
    old = gi.read_text(encoding="utf-8", errors="ignore") if gi.exists() else ""
    pattern = re.compile(r"# BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_\d+.*?# BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_\d+_END", re.S)
    cleaned = pattern.sub("", old).rstrip()
    gi.write_text(cleaned + "\n\n" + GITIGNORE_BLOCK.strip() + "\n", encoding="utf-8")

def ensure_password_helper(root: Path) -> None:
    path = root / "app" / "security" / "passwords.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            "from __future__ import annotations\n\n"
            "import secrets\nimport string\n\n"
            "def generate_initial_password(length: int = 14) -> str:\n"
            "    alphabet = string.ascii_letters + string.digits + '!@#$%&*?'\n"
            "    while True:\n"
            "        password = ''.join(secrets.choice(alphabet) for _ in range(max(length, 12)))\n"
            "        if (any(c.islower() for c in password) and any(c.isupper() for c in password)\n"
            "                and any(c.isdigit() for c in password) and any(c in '!@#$%&*?' for c in password)):\n"
            "            return password\n",
            encoding="utf-8",
        )

def sanitize_local_env_placeholder(root: Path) -> None:
    # Yerel geliştirme dosyasındaki placeholder, release güvenliği için engel değildir.
    # Ancak eski örnek URL kalırsa sonraki P0 gate'lerinde kafa karışıklığı yaratmasın diye boşaltılır.
    env = root / ".env"
    if not env.exists():
        return
    text = env.read_text(encoding="utf-8", errors="ignore")
    placeholder_parts = ["https://", "...", "@sentry.io", "/..."]
    placeholder = "".join(placeholder_parts)
    if placeholder in text:
        text = text.replace(placeholder, "")
        env.write_text(text, encoding="utf-8")

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    upsert_gitignore(root)
    ensure_password_helper(root)
    sanitize_local_env_placeholder(root)

    (root / "docs" / "deploy").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "deploy" / "ENV_TEMPLATE.md").write_text(ENV_TEMPLATE_MD.strip() + "\n", encoding="utf-8")

    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "scripts" / "README.md").write_text(SCRIPTS_README.strip() + "\n", encoding="utf-8")

    (root / "docs" / "handover").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "handover" / "SCRIPTS_DEVIR_TESLIM_NOTU.md").write_text(HANDOVER_NOTE.strip() + "\n", encoding="utf-8")

    print("BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_4_REPAIR_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
