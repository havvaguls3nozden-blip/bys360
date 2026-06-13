from __future__ import annotations

import py_compile
import sys
from pathlib import Path

VERSION = "BYS360_CSRF_MAIN_LOGIN_HOTFIX_V2_15_14"
ROOT = Path(__file__).resolve().parents[2]
path = ROOT / "app" / "__init__.py"
errors = []
text = path.read_text(encoding="utf-8") if path.exists() else ""
if 'BYS360_CSRF_MAIN_LOGIN_HOTFIX_V2_15_14' not in text:
    errors.append("app/__init__.py CSRF hotfix etiketi bulunamadi")
if 'for endpoint in ("main.login", "auth.login", "login")' not in text and "for endpoint in ('main.login', 'auth.login', 'login')" not in text:
    errors.append("CSRF login endpoint sirasi main.login ile baslamiyor")
if 'for endpoint in ("auth.login", "login", "main.login")' in text or "for endpoint in ('auth.login', 'login', 'main.login')" in text:
    errors.append("Eski hatali CSRF endpoint sirasi hala duruyor")
if "BYS360 kalite denetimi: except bloğu loglandı (app/__init__.py:111)" in text:
    errors.append("CSRF handler icinde gereksiz exception logu hala duruyor")
try:
    py_compile.compile(str(path), doraise=True)
except Exception as exc:
    errors.append(f"app/__init__.py compile hatasi: {exc}")
if errors:
    print(f"{VERSION}_GATE_FAIL")
    for e in errors:
        print(f"HATA: {e}")
    sys.exit(1)
print(f"{VERSION}_GATE_OK")
print(f"{VERSION}_FINAL_OK")
