from __future__ import annotations

import py_compile
import re
import sys
from pathlib import Path

VERSION = "BYS360_CSRF_FORM_TOKEN_AND_REFERRER_HOTFIX_V2_15_15"
ROOT = Path(__file__).resolve().parents[2]
errors: list[str] = []

init_path = ROOT / "app" / "__init__.py"
init_text = init_path.read_text(encoding="utf-8") if init_path.exists() else ""
if VERSION not in init_text:
    errors.append("app/__init__.py içinde V2.15.15 referrer CSRF hotfix etiketi yok")
if 'for endpoint in ("main.login", "auth.login", "login")' not in init_text and "for endpoint in ('main.login', 'auth.login', 'login')" not in init_text:
    errors.append("CSRF login endpoint sırası main.login ile başlamıyor")
if 'request.referrer' not in init_text or 'request.path.startswith("/dashboard/")' not in init_text:
    errors.append("CSRF handler dashboard/referrer dönüş mantığı eksik")
if "BYS360 kalite denetimi: except bloğu loglandı (app/__init__.py:111)" in init_text:
    errors.append("CSRF handler içinde eski gereksiz exception logu hâlâ duruyor")
try:
    py_compile.compile(str(init_path), doraise=True)
except Exception as exc:
    errors.append(f"app/__init__.py compile hatası: {exc}")

base = ROOT / "app" / "templates" / "corporate_information_center"
for name in ("tasks.html", "recipients.html", "templates.html", "system.html", "test.html"):
    path = base / name
    if not path.exists():
        errors.append(f"Eksik şablon: {path}")
        continue
    text = path.read_text(encoding="utf-8")
    post_form_count = len(re.findall(r"<form\b(?=[^>]*\bmethod\s*=\s*['\"]post['\"])[^>]*>", text, flags=re.IGNORECASE))
    token_count = text.count('name="csrf_token"') + text.count("name='csrf_token'")
    if post_form_count and token_count < post_form_count:
        errors.append(f"{name} içinde POST form sayısı kadar CSRF token yok: form={post_form_count}, token={token_count}")
    if name == "test.html" and "csrf_token()" not in text:
        errors.append("test.html mail test formunda csrf_token() eksik")

if errors:
    print(f"{VERSION}_GATE_FAIL")
    for e in errors:
        print("HATA:", e)
    sys.exit(1)
print(f"{VERSION}_GATE_OK")
print(f"{VERSION}_FINAL_OK")
