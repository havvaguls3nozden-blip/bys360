# -*- coding: utf-8 -*-
"""
BYS360 Secure Release & Script Handover V1.3 repair helper.
- Does not delete project scripts.
- Creates safe handover documentation.
- Normalizes release policy so .env.example is not shipped inside secure release zips.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from datetime import datetime

BANNER = "BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_3_REPAIR_OK"

SCRIPTS_README = """# BYS360 Script Kullanım Rehberi

Bu klasördeki scriptler proje geliştirme, gate kontrolü, güvenli release üretimi ve bakım işlemleri için kullanılır.

## Devir teslim kuralı

Tüm geçmiş overlay/repair/check scriptleri canlı uygulamanın çalışması için zorunlu değildir. Kaynak proje içinde izlenebilirlik için kalabilir; ancak devredilecek güvenli release paketinde yalnızca güncel ve bakımda kullanılacak scriptler tutulmalıdır.

## Güncel güvenli release hattı

- `scripts/security/check_bys360_secure_release_secret_clean_v1_3.ps1`
- `scripts/security/repair_bys360_secure_release_secret_clean_v1_3.ps1`
- `scripts/windows/build_bys360_secure_release_v1_3.ps1`

## Eski versioned scriptler

`*_v1.ps1`, `*_v1_1.ps1`, `*_v1_2.ps1` gibi eski güvenlik overlay scriptleri kaynak geçmişi için kalabilir; fakat V1.3 güvenli release üretiminde pakete alınmaz.

## Silme politikası

Bu overlay eski scriptleri silmez. Silme işlemi elle yapılacaksa önce yedek alınmalı ve hangi scriptin Scheduled Task, kurulum veya gate tarafından kullanıldığı kontrol edilmelidir.
"""

HANDOVER_DOC = """# BYS360 Script Devir Teslim Notu

## Kısa cevap

Script dosyalarının proje kaynak klasöründe bulunması tek başına sorun değildir. Ancak devredilecek paket içinde yüzlerce eski repair/check/overlay scriptinin aynı seviyede kalması yeni geliştirici için kafa karıştırır.

## Önerilen yapı

1. Kaynak projede script geçmişi korunabilir.
2. Güvenli release paketinde sadece güncel bakım scriptleri yer almalıdır.
3. Eski overlay scriptleri release dışı bırakılmalıdır.
4. Her güvenlik veya deployment scriptinin amacı kısa dokümanda yazmalıdır.
5. `.env`, `.env.example`, dump, log, zip, cache ve backup dosyaları release paketine girmemelidir.

## Güncel aktif scriptler

- Güvenli release kontrolü: `scripts/security/check_bys360_secure_release_secret_clean_v1_3.ps1`
- Güvenli release onarım/doküman hazırlığı: `scripts/security/repair_bys360_secure_release_secret_clean_v1_3.ps1`
- Güvenli release üretimi: `scripts/windows/build_bys360_secure_release_v1_3.ps1`

## Devrederken söylenecek cümle

BYS360 kaynak projesinde geçmiş overlay ve kontrol scriptleri izlenebilirlik için tutulmuştur. Canlı dağıtım için kullanılacak güncel güvenli release hattı V1.3 scriptleridir. Eski scriptler release paketine dahil edilmez; gerektiğinde geçmiş bakım kaydı olarak incelenir.
"""

ENV_TEMPLATE_DOC = """# BYS360 Ortam Değişkenleri Şablonu

Bu dosya `.env.example` yerine güvenli dokümantasyon olarak tutulur. Gerçek parola, DSN, API anahtarı veya canlı bağlantı değeri yazılmaz.

```env
APP_ENV=development
FLASK_ENV=development
SECRET_KEY=CHANGE_ME_WITH_STRONG_RANDOM_VALUE
DATABASE_URL=DB_CONNECTION_STRING_SUPPLIED_BY_ENVIRONMENT
SQLALCHEMY_DATABASE_URI=DB_CONNECTION_STRING_SUPPLIED_BY_ENVIRONMENT
DB_SSLMODE=require
SENTRY_DSN=
SENTRY_ENVIRONMENT=development
SENTRY_REQUIRED_IN_PRODUCTION=false
AI_API_KEY=
REDIS_URL=redis://127.0.0.1:6379/0
CACHE_REDIS_URL=redis://127.0.0.1:6379/1
SECURITY_RATE_LIMIT_REDIS_URL=redis://127.0.0.1:6379/2
CSP_ENABLED=true
CSP_NONCE_ENABLED=true
CSP_ALLOW_UNSAFE_INLINE_SCRIPT=false
```

## Canlı ortam notu

Canlı ortamda Sentry DSN gerçek proje DSN'i ile doldurulmalı, PostgreSQL bağlantısı `sslmode=require` veya mümkünse `verify-full` kullanılmalıdır.
"""


def write_if_changed(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old != content:
        path.write_text(content, encoding="utf-8")


def ensure_gitignore(project: Path) -> None:
    gi = project / ".gitignore"
    block = """

# BYS360 secure release / secret hygiene
.env
.env.*
!.env.example
*.log
*.dump
*.sql.gz
*.sqlite
*.sqlite3
*.db
*.bak
*.tmp
*.zip
_upload_parts/
dist_secure/
__pycache__/
*.pyc
""".strip()
    existing = gi.read_text(encoding="utf-8", errors="ignore") if gi.exists() else ""
    if "# BYS360 secure release / secret hygiene" not in existing:
        gi.write_text((existing.rstrip() + "\n\n" + block + "\n"), encoding="utf-8")


def sanitize_env_example(project: Path) -> None:
    env_example = project / ".env.example"
    content = """# BYS360 local development environment template
# Do not put real passwords, DSNs, API keys or live secrets in this file.
APP_ENV=development
FLASK_ENV=development
SECRET_KEY=
DATABASE_URL=DB_CONNECTION_STRING_SUPPLIED_BY_ENVIRONMENT
SQLALCHEMY_DATABASE_URI=DB_CONNECTION_STRING_SUPPLIED_BY_ENVIRONMENT
DB_SSLMODE=require
SENTRY_DSN=
SENTRY_ENVIRONMENT=development
SENTRY_REQUIRED_IN_PRODUCTION=false
AI_API_KEY=
REDIS_URL=redis://127.0.0.1:6379/0
CACHE_REDIS_URL=redis://127.0.0.1:6379/1
SECURITY_RATE_LIMIT_REDIS_URL=redis://127.0.0.1:6379/2
CSP_ENABLED=true
CSP_NONCE_ENABLED=true
CSP_ALLOW_UNSAFE_INLINE_SCRIPT=false
"""
    write_if_changed(env_example, content)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    project = Path(args.project_root).resolve()

    write_if_changed(project / "scripts" / "README.md", SCRIPTS_README)
    write_if_changed(project / "docs" / "handover" / "SCRIPTS_DEVIR_TESLIM_NOTU.md", HANDOVER_DOC)
    write_if_changed(project / "docs" / "deploy" / "ENV_TEMPLATE.md", ENV_TEMPLATE_DOC)
    sanitize_env_example(project)
    ensure_gitignore(project)

    print(BANNER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
