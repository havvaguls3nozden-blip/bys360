# -*- coding: utf-8 -*-
"""
BYS360 Kurumsal Bilgilendirme Merkezi V3.0 Faz 7.11
Template uyumluluk ve toplu 500 hata düzeltmesi.

Düzeltir:
- Faz 7.9/7.10 sonrası kaybolan cic_csrf makrosunu geri ekler.
- status_pill makrosunu base içinde kalıcı tutar.
- logs.html içindeki phase6.log_quality.items kullanımını Jinja için güvenli hale getirir.
- Eski literal \n / kaçışlı tırnak kalıntılarını temizler.
"""
from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

MARKER = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_11_TEMPLATE_COMPAT_FIX"

CIC_CSRF_MACRO = """{# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_11_TEMPLATE_COMPAT_FIX: CSRF macro #}
{% macro cic_csrf() -%}
  {% if csrf_token is defined %}
    <input type=\"hidden\" name=\"csrf_token\" value=\"{{ csrf_token() }}\">
  {% endif %}
{%- endmacro %}
"""

STATUS_PILL_MACRO = """{# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_11_TEMPLATE_COMPAT_FIX: status macro #}
{% macro status_pill(status, label=None) -%}
  {% set _status = (status|string|lower) if status is not none else 'ok' %}
  {% set _label = label if label is not none else (status if status is not none else 'Hazır') %}
  {% if _status in ['ok', 'success', 'successful', 'ready', 'healthy', 'active', 'passed', 'complete', 'completed', 'sent', 'hazır', 'tamam', 'basarili', 'başarılı'] %}
    <span class=\"cic-badge ok\"><i class=\"fa-solid fa-circle-check\"></i> {{ _label }}</span>
  {% elif _status in ['warning', 'warn', 'pending', 'waiting', 'risk', 'attention', 'review', 'uyari', 'uyarı', 'bekliyor', 'kontrol'] %}
    <span class=\"cic-badge warning\"><i class=\"fa-solid fa-triangle-exclamation\"></i> {{ _label }}</span>
  {% elif _status in ['danger', 'error', 'failed', 'fail', 'missing', 'critical', 'blocked', 'inactive', 'hata', 'hatali', 'hatalı', 'eksik', 'kritik'] %}
    <span class=\"cic-badge danger\"><i class=\"fa-solid fa-circle-xmark\"></i> {{ _label }}</span>
  {% else %}
    <span class=\"cic-badge neutral\"><i class=\"fa-solid fa-circle-info\"></i> {{ _label }}</span>
  {% endif %}
{%- endmacro %}
"""

CSS_PATCH = """

/* BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_11_TEMPLATE_COMPAT_FIX */
.cic-badge{
  display:inline-flex;
  align-items:center;
  gap:7px;
  min-height:28px;
  padding:6px 12px;
  border-radius:999px;
  font-size:12px;
  line-height:1;
  font-weight:800;
  letter-spacing:.01em;
  white-space:nowrap;
  border:1px solid rgba(15,23,42,.10);
  background:#fff;
  color:#1f2937;
  box-shadow:0 8px 22px rgba(15,23,42,.05);
}
.cic-badge.ok{background:#ecfdf5;color:#047857;border-color:#a7f3d0;}
.cic-badge.warning{background:#fffbeb;color:#92400e;border-color:#fde68a;}
.cic-badge.danger{background:#fef2f2;color:#991b1b;border-color:#fecaca;}
.cic-badge.neutral{background:#f8fafc;color:#334155;border-color:#e2e8f0;}
.cic-badge i{font-size:12px;}
"""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def backup(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bdir = path.parent / "_backup_phase7_11"
    bdir.mkdir(exist_ok=True)
    target = bdir / f"{path.name}.{stamp}.bak"
    target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def normalize_template_text(text: str) -> str:
    if "\\n" in text and text.count("\n") < 8:
        text = text.replace("\\n", "\n")
    text = text.replace("\\'", "'").replace('\\"', '"')
    return text


def insert_macros_after_extra_head(text: str, macros: str) -> str:
    end_head = "{% endblock %}"
    idx = text.find(end_head)
    if idx != -1:
        insert_pos = idx + len(end_head)
        return text[:insert_pos] + "\n\n" + macros.rstrip() + "\n" + text[insert_pos:]
    needle = "{% block content %}"
    if needle in text:
        return text.replace(needle, macros.rstrip() + "\n\n" + needle, 1)
    return macros.rstrip() + "\n\n" + text


def ensure_base_macros(root: Path) -> list[str]:
    changed: list[str] = []
    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    if not base.exists():
        raise FileNotFoundError(f"base.html bulunamadı: {base}")
    text = normalize_template_text(read_text(base))
    original = text
    add_parts = []
    if "{% macro cic_csrf" not in text:
        add_parts.append(CIC_CSRF_MACRO)
    if "{% macro status_pill" not in text:
        add_parts.append(STATUS_PILL_MACRO)
    if add_parts:
        text = insert_macros_after_extra_head(text, "\n".join(add_parts))
    if MARKER not in text:
        text = text.replace("{% block content %}", "{# " + MARKER + " #}\n{% block content %}", 1)
    if text != original:
        backup(base)
        write_text(base, text)
        changed.append(str(base.relative_to(root)))
    return changed


def patch_log_items(root: Path) -> list[str]:
    changed: list[str] = []
    logs = root / "app" / "templates" / "corporate_information_center" / "logs.html"
    if not logs.exists():
        return changed
    text = normalize_template_text(read_text(logs))
    original = text
    replacements = {
        "phase6.log_quality.items": "phase6.log_quality['items']|default([])",
        "phase6.audit_quality.items": "phase6.audit_quality['items']|default([])",
        "phase6.live_quality.items": "phase6.live_quality['items']|default([])",
        "phase6.release_checks.items": "phase6.release_checks['items']|default([])",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"(phase\d+\.[A-Za-z0-9_]+)\.items(?!\s*\()", r"\1['items']|default([])", text)
    if text != original:
        backup(logs)
        write_text(logs, text)
        changed.append(str(logs.relative_to(root)))
    return changed


def patch_child_literal_newlines(root: Path) -> list[str]:
    changed: list[str] = []
    tmpl_dir = root / "app" / "templates" / "corporate_information_center"
    if not tmpl_dir.exists():
        return changed
    for path in sorted(tmpl_dir.glob("*.html")):
        text = read_text(path)
        normalized = normalize_template_text(text)
        if normalized != text:
            backup(path)
            write_text(path, normalized)
            changed.append(str(path.relative_to(root)))
    return changed


def ensure_css(root: Path) -> list[str]:
    changed: list[str] = []
    css_dir = root / "app" / "static" / "css"
    candidates = [
        css_dir / "corporate_information_center_v3_0_phase7_8_base_header_pro.css",
        css_dir / "corporate_information_center_v3_0_phase7_7_release_clean.css",
        css_dir / "corporate_information_center_v3_0_phase7_4_release_pro.css",
        css_dir / "corporate_information_center_v3_0_phase7.css",
        css_dir / "corporate_information_center_v3_0_phase4_1.css",
    ]
    for path in candidates:
        if path.exists():
            text = read_text(path)
            if MARKER not in text:
                backup(path)
                write_text(path, text.rstrip() + CSS_PATCH)
                changed.append(str(path.relative_to(root)))
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", default=r"C:\bys360\project")
    parser.add_argument("-Mode", default="all")
    args = parser.parse_args()
    root = Path(args.ProjectRoot)
    print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_11_TEMPLATE_COMPAT_FIX_APPLY_START")
    print(f"ProjectRoot={root}")
    changed: list[str] = []
    changed += patch_child_literal_newlines(root)
    changed += ensure_base_macros(root)
    changed += patch_log_items(root)
    changed += ensure_css(root)
    print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_11_TEMPLATE_COMPAT_FIX_APPLY_OK")
    if changed:
        print("Güncellenen dosyalar:")
        for item in changed:
            print(f" - {item}")
    else:
        print("Güncellenecek dosya bulunmadı; yapı zaten uyumlu görünüyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
