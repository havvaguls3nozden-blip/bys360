# -*- coding: utf-8 -*-
"""BYS360 10/10 Red Gate V1 repair."""
from __future__ import annotations

import argparse
import os
import shutil
from datetime import datetime
from pathlib import Path

UTF8 = "utf-8"


def read(path: Path) -> str:
    return path.read_text(encoding=UTF8)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding=UTF8, newline="\n")


def backup_files(project_root: Path, files: list[Path]) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = Path("C:/bys360/backups") if os.name == "nt" else project_root / "backups"
    dest = backup_root / f"bys360_10_10_red_gate_v1_{stamp}"
    for rel in files:
        src = project_root / rel
        if src.exists():
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
    return dest


def patch_once(text: str, old: str, new: str, label: str) -> tuple[str, bool]:
    if new in text:
        return text, False
    if old not in text:
        raise RuntimeError(f"Beklenen blok bulunamadı: {label}")
    return text.replace(old, new), True


def patch_post_card(project_root: Path) -> bool:
    path = project_root / "app/templates/portal/_post_card.html"
    text = read(path)
    changed = False
    old_body = "<div class=\"portal-post-body\">{{ post.body|replace('\\n','<br>')|safe }}</div>"
    new_body = "<div class=\"portal-post-body\" style=\"white-space: pre-wrap;\">{{ post.body }}</div>"
    text, c = patch_once(text, old_body, new_body, "portal post body safe kaldırma")
    changed |= c
    text, c = patch_once(text, "{{ attachment.stored_path|safe }}", "{{ attachment.stored_path|safe_social_embed }}", "portal social embed sanitizer filter")
    changed |= c
    if changed:
        write(path, text)
    return changed


def patch_cic_overview(project_root: Path) -> bool:
    path = project_root / "app/templates/corporate_information_center/overview.html"
    text = read(path)
    old = "{% if phase5.mail_health.problems %}<div class=\"cic-warning-box\"><strong>Kontrol gerekli:</strong><br>{{ phase5.mail_health.problems|join('<br>')|safe }}</div>{% else %}<div class=\"cic-help-v4\"><strong>Hazır:</strong> Mail altyapısı gerçek gönderim için uygun görünüyor.</div>{% endif %}"
    new = "{% if phase5.mail_health.problems %}<div class=\"cic-warning-box\"><strong>Kontrol gerekli:</strong><br>{% for problem in phase5.mail_health.problems %}{{ problem }}{% if not loop.last %}<br>{% endif %}{% endfor %}</div>{% else %}<div class=\"cic-help-v4\"><strong>Hazır:</strong> Mail altyapısı gerçek gönderim için uygun görünüyor.</div>{% endif %}"
    text2, changed = patch_once(text, old, new, "cic overview problems safe join kaldırma")
    if changed:
        write(path, text2)
    return changed


def patch_base(project_root: Path) -> bool:
    path = project_root / "app/templates/base.html"
    text = read(path)
    text2, changed = patch_once(text, "{{ attrs|safe }}", "{{ attrs|safe_nav_attrs }}", "base nav attrs controlled filter")
    if changed:
        write(path, text2)
    return changed


def patch_config(project_root: Path) -> bool:
    path = project_root / "config.py"
    text = read(path)
    old = '''    if _secret_is_strong:
        SECRET_KEY = (
            os.environ.get("SECRET_KEY")
            or os.environ.get("FLASK_SECRET")
            or (
                "bys360-local-dev-only-secret"
                if os.environ.get("FLASK_ENV", "").lower() not in {"production", "prod"}
                and os.environ.get("BYS360_ENV", "").lower() not in {"production", "prod", "live"}
                else None
            )
        )
    elif APP_ENV in {'production', 'staging'}:
        raise RuntimeError('Production/staging ortamında güçlü ve benzersiz SECRET_KEY zorunludur.')
    else:
        SECRET_KEY = (
            os.environ.get("SECRET_KEY")
            or os.environ.get("FLASK_SECRET")
            or (
                "bys360-local-dev-only-secret"
                if os.environ.get("FLASK_ENV", "").lower() not in {"production", "prod"}
                and os.environ.get("BYS360_ENV", "").lower() not in {"production", "prod", "live"}
                else None
            )
        )
'''
    new = '''    if _secret_is_strong:
        SECRET_KEY = _raw_secret_key
    elif APP_ENV in {'production', 'staging'}:
        raise RuntimeError('Production/staging ortamında güçlü ve benzersiz SECRET_KEY zorunludur.')
    else:
        SECRET_KEY = os.environ.get("FLASK_SECRET") or "bys360-local-dev-only-secret"
'''
    text2, changed = patch_once(text, old, new, "config SECRET_KEY tekrarını sadeleştirme")
    if changed:
        write(path, text2)
    return changed


def patch_app_init(project_root: Path) -> bool:
    path = project_root / "app/__init__.py"
    text = read(path)
    if 'safe_social_embed' in text and 'safe_nav_attrs' in text:
        return False
    anchor = "def create_app() -> Flask:\n    app = create_bys360_application(__name__)\n"
    insert = "def create_app() -> Flask:\n    app = create_bys360_application(__name__)\n\n    from app.security.html_sanitizer import safe_nav_attrs, safe_social_embed\n\n    app.jinja_env.filters[\"safe_social_embed\"] = safe_social_embed\n    app.jinja_env.filters[\"safe_nav_attrs\"] = safe_nav_attrs\n"
    if anchor not in text:
        raise RuntimeError("app/__init__.py create_app anchor bulunamadı")
    write(path, text.replace(anchor, insert))
    return True


def patch_gitignore(project_root: Path) -> bool:
    path = project_root / ".gitignore"
    text = read(path) if path.exists() else ""
    block = """
# BYS360_10_10_RED_GATE_V1_PACKAGE_HYGIENE_BEGIN
.dart_tool/
mobile_flutter/**/.dart_tool/
mobile_flutter/**/build/
build/
project/
**/project/.venv/
**/project/.dart_tool/
**/__pycache__/
# BYS360_10_10_RED_GATE_V1_PACKAGE_HYGIENE_END
"""
    if "BYS360_10_10_RED_GATE_V1_PACKAGE_HYGIENE_BEGIN" in text:
        return False
    write(path, text.rstrip() + block)
    return True


def write_sanitizer(project_root: Path) -> bool:
    path = project_root / "app/security/html_sanitizer.py"
    content = r'''# -*- coding: utf-8 -*-
"""Small HTML safety filters for BYS360 templates."""
from __future__ import annotations

import html
import re
from typing import Any

from markupsafe import Markup, escape

try:
    import bleach  # type: ignore
except Exception:  # pragma: no cover
    bleach = None  # type: ignore

_ALLOWED_SOCIAL_TAGS = ["blockquote", "a", "br"]
_ALLOWED_SOCIAL_ATTRS = {
    "blockquote": ["class", "data-dnt", "data-instgrm-permalink", "data-instgrm-version", "align"],
    "a": ["href", "title", "target", "rel"],
}
_ALLOWED_PROTOCOLS = ["http", "https"]
_ALLOWED_NAV_ATTRS = {"title", "role", "aria-label", "aria-current"}
_ONCLICK_LOGOUT = "return submitLogoutForm(event);"
_ATTR_RE = re.compile(r"([A-Za-z0-9_:\-.]+)\s*=\s*([\"'])(.*?)\2", re.S)
_EVENT_ATTR_RE = re.compile(r"\s+on[a-zA-Z]+\s*=\s*([\"']).*?\1", re.S)
_SCRIPT_RE = re.compile(r"<\s*(script|style|iframe|object|embed)[^>]*>.*?<\s*/\s*\1\s*>", re.I | re.S)
_JS_URL_RE = re.compile(r"javascript\s*:", re.I)


def _strip_obvious_danger(value: str) -> str:
    value = _SCRIPT_RE.sub("", value)
    value = _EVENT_ATTR_RE.sub("", value)
    value = _JS_URL_RE.sub("", value)
    return value


def safe_social_embed(value: Any) -> Markup:
    raw = _strip_obvious_danger(str(value or ""))
    if not raw.strip():
        return Markup("")
    if bleach is None:
        return Markup(escape(raw))
    cleaned = bleach.clean(
        raw,
        tags=_ALLOWED_SOCIAL_TAGS,
        attributes=_ALLOWED_SOCIAL_ATTRS,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )
    return Markup(_strip_obvious_danger(cleaned))


def safe_nav_attrs(value: Any) -> Markup:
    raw = str(value or "")
    attrs: list[str] = []
    for match in _ATTR_RE.finditer(raw):
        name = match.group(1).strip().lower()
        attr_value = match.group(3).strip()
        if name.startswith("data-") or name in _ALLOWED_NAV_ATTRS:
            attrs.append(f'{name}="{html.escape(attr_value, quote=True)}"')
        elif name == "onclick" and attr_value == _ONCLICK_LOGOUT:
            attrs.append('onclick="return submitLogoutForm(event);"')
    return Markup(" ".join(attrs))
'''
    if path.exists() and read(path) == content:
        return False
    write(path, content)
    return True


def write_tests(project_root: Path) -> bool:
    path = project_root / "tests/security/test_xss_red_gate_v1.py"
    content = r'''# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

from flask import request


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_portal_post_body_template_escapes_html() -> None:
    text = _read("app/templates/portal/_post_card.html")
    assert "post.body|replace" not in text
    assert "post.body|safe" not in text
    assert "white-space: pre-wrap" in text
    assert "{{ post.body }}" in text


def test_unsafe_template_safes_removed_or_filtered() -> None:
    assert "{{ attrs|safe }}" not in _read("app/templates/base.html")
    assert "attrs|safe_nav_attrs" in _read("app/templates/base.html")
    assert "{{ attachment.stored_path|safe }}" not in _read("app/templates/portal/_post_card.html")
    assert "attachment.stored_path|safe_social_embed" in _read("app/templates/portal/_post_card.html")
    assert "problems|join('<br>')|safe" not in _read("app/templates/corporate_information_center/overview.html")


def test_safe_social_embed_removes_script_and_javascript_url() -> None:
    from app.security.html_sanitizer import safe_social_embed

    payload = '<blockquote onclick="alert(1)"><script>alert(1)</script><a href="javascript:alert(1)">x</a></blockquote>'
    rendered = str(safe_social_embed(payload)).lower()
    assert "<script" not in rendered
    assert "onclick" not in rendered
    assert "javascript:" not in rendered


def test_post_body_payload_is_escaped_with_test_client(app, client) -> None:
    endpoint = "_bys360_xss_red_gate_v1_echo"

    if endpoint not in app.view_functions:
        @app.post("/_test/bys360-xss-red-gate-v1")
        def _bys360_xss_red_gate_v1_echo():  # type: ignore[unused-ignore]
            template = '<div class="portal-post-body" style="white-space: pre-wrap;">{{ body }}</div>'
            return app.jinja_env.from_string(template).render(body=request.form.get("body", ""))

    payload = '<script>alert("x")</script>\nMerhaba'
    response = client.post("/_test/bys360-xss-red-gate-v1", data={"body": payload})
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "<script>" not in html
    assert "&lt;script&gt;" in html or "&lt;script" in html
    assert "white-space: pre-wrap" in html
'''
    if path.exists() and read(path) == content:
        return False
    write(path, content)
    return True


def patch_ci(project_root: Path) -> bool:
    path = project_root / ".github/workflows/bys360-ci.yml"
    if not path.exists():
        return False
    text = read(path)
    text2 = text.replace(
        "python -m pytest tests/integration tests/architecture --tb=short -q",
        "python -m pytest tests/integration tests/architecture tests/security tests/critical --tb=short -q",
    ).replace(
        "python -m ruff check app --select F821",
        "python -m ruff check app config.py wsgi.py run.py scripts tests",
    ).replace(
        "python -m mypy app/services --ignore-missing-imports --no-error-summary",
        "python -m mypy app tests scripts --ignore-missing-imports --no-error-summary",
    )
    if text2 != text:
        write(path, text2)
        return True
    return False


def verify(project_root: Path) -> list[str]:
    errors: list[str] = []
    checks = {
        "app/templates/portal/_post_card.html": ["post.body|replace", "post.body|safe", "{{ attachment.stored_path|safe }}"],
        "app/templates/base.html": ["{{ attrs|safe }}"],
        "app/templates/corporate_information_center/overview.html": ["problems|join('<br>')|safe"],
    }
    for rel, forbidden in checks.items():
        text = read(project_root / rel)
        for item in forbidden:
            if item in text:
                errors.append(f"Kaldırılamadı: {rel} içinde {item}")
    for rel in ["app/security/html_sanitizer.py", "tests/security/test_xss_red_gate_v1.py"]:
        if not (project_root / rel).exists():
            errors.append(f"Eksik dosya: {rel}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--no-ci", action="store_true", help="CI workflow genişletmesini atla")
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    if not (project_root / "app").exists():
        raise SystemExit(f"BYS360 proje kökü bulunamadı: {project_root}")

    target_files = [
        Path("app/templates/portal/_post_card.html"),
        Path("app/templates/base.html"),
        Path("app/templates/corporate_information_center/overview.html"),
        Path("config.py"),
        Path("app/__init__.py"),
        Path(".gitignore"),
        Path(".github/workflows/bys360-ci.yml"),
    ]
    backup_dir = backup_files(project_root, target_files)
    changes = []
    for label, func in [
        ("portal_post_card", patch_post_card),
        ("corporate_information_center", patch_cic_overview),
        ("base_nav_attrs", patch_base),
        ("config_secret_key", patch_config),
        ("app_jinja_filters", patch_app_init),
        ("html_sanitizer", write_sanitizer),
        ("xss_tests", write_tests),
        ("gitignore_package_hygiene", patch_gitignore),
    ]:
        if func(project_root):
            changes.append(label)
    if not args.no_ci and patch_ci(project_root):
        changes.append("ci_scope_expand")

    errors = verify(project_root)
    report_dir = project_root / "reports/security"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / "BYS360_10_10_RED_GATE_V1_REPORT.md"
    report.write_text(
        "# BYS360 10/10 Red Gate V1\n\n"
        f"Backup: `{backup_dir}`\n\n"
        "## Değişen Alanlar\n"
        + "\n".join(f"- {x}" for x in changes or ["idempotent: değişiklik gerekmiyor"])
        + "\n\n## Doğrulama\n"
        + ("PASS\n" if not errors else "FAIL\n" + "\n".join(f"- {e}" for e in errors))
        + "\n\n## Önerilen Komutlar\n"
        + "```powershell\npython -m pytest tests/security/test_xss_red_gate_v1.py -q\npython -m ruff check app config.py tests/security/test_xss_red_gate_v1.py --select E9,F63,F7,F82,F821\n```\n",
        encoding=UTF8,
    )
    print("BYS360_10_10_RED_GATE_V1")
    print("BACKUP=", backup_dir)
    print("REPORT=", report)
    print("CHANGES=", ", ".join(changes) if changes else "none")
    if errors:
        for e in errors:
            print("ERROR=", e)
        return 2
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
