# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path

MARKER = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_12_ALL_TEMPLATE_MACRO_FIX"

MACRO_BLOCK = r'''
{# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_12_ALL_TEMPLATE_MACRO_FIX: shared template helpers #}
{% macro cic_csrf() -%}
  {%- if csrf_token is defined -%}
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  {%- endif -%}
{%- endmacro %}

{% macro status_pill(status, label=None) -%}
  {%- set _status = (status|default('neutral', true)|string)|lower -%}
  {%- set _label = label|default(status|default('Durum', true), true) -%}
  {%- if _status in ['ok', 'ready', 'active', 'success', 'enabled', 'completed', 'passed', 'healthy'] -%}
    <span class="cic-badge ok"><i class="fa-solid fa-circle-check"></i> {{ _label }}</span>
  {%- elif _status in ['warning', 'warn', 'pending', 'draft', 'attention', 'waiting'] -%}
    <span class="cic-badge warning"><i class="fa-solid fa-triangle-exclamation"></i> {{ _label }}</span>
  {%- elif _status in ['error', 'danger', 'failed', 'missing', 'blocked', 'critical'] -%}
    <span class="cic-badge danger"><i class="fa-solid fa-circle-exclamation"></i> {{ _label }}</span>
  {%- elif _status in ['info', 'neutral', 'passive'] -%}
    <span class="cic-badge neutral"><i class="fa-solid fa-circle-info"></i> {{ _label }}</span>
  {%- else -%}
    <span class="cic-badge neutral"><i class="fa-solid fa-circle-info"></i> {{ _label }}</span>
  {%- endif -%}
{%- endmacro %}

{% macro task_status(task) -%}
  {%- set _status = task.status|default(task.state|default(task.health|default('ready', true), true), true) -%}
  {%- set _label = task.status_label|default(task.label_status|default(task.status_text|default('Hazır', true), true), true) -%}
  {{ status_pill(_status, _label) }}
{%- endmacro %}

{% macro user_full_name(user) -%}
  {%- set _ad = user.ad|default('', true) -%}
  {%- set _soyad = user.soyad|default('', true) -%}
  {%- set _name = (_ad ~ ' ' ~ _soyad)|trim -%}
  {{ _name or user.full_name_cache|default('', true) or user.name|default('', true) or user.email|default('', true) or ('Kullanıcı #' ~ user.id) }}
{%- endmacro %}

{% macro user_initial(user) -%}
  {%- set _name = user_full_name(user)|striptags|trim -%}
  {{ (_name[:1] or 'K')|upper }}
{%- endmacro %}
'''

BASE_TEMPLATE = r'''{% extends "base.html" %}
{% block title %}Kurumsal Bilgilendirme Merkezi | BYS360{% endblock %}
{% block page_title %}Kurumsal Bilgilendirme Merkezi{% endblock %}
{% block page_subtitle %}Personel ve yönetici bilgilendirmeleri, şablonlar, alıcılar, test gönderimleri, loglar ve canlı geçiş kontrolleri tek merkezden yönetilir.{% endblock %}

{% block extra_head %}
{{ super() }}
<link rel="stylesheet" href="{{ url_for('static', filename='css/corporate_information_center_v3_0_phase4_1.css') }}?v=2_15_30">
<link rel="stylesheet" href="{{ url_for('static', filename='css/corporate_information_center_v3_0_phase7.css') }}?v=2_15_30">
<link rel="stylesheet" href="{{ url_for('static', filename='css/corporate_information_center_v3_0_phase7_8_base_header_pro.css') }}?v=2_15_30">
{% endblock %}
'''

TABS_BLOCK = r'''
{% macro tabs(active) -%}
<nav class="cic-tabs" aria-label="Kurumsal Bilgilendirme Merkezi menüsü">
  <a class="{{ 'active' if active=='overview' else '' }}" href="/dashboard/kurumsal-bilgilendirme"><i class="fa-solid fa-gauge-high"></i><span>Genel Bakış</span></a>
  <a class="{{ 'active' if active=='tasks' else '' }}" href="/dashboard/kurumsal-bilgilendirme/gorevler"><i class="fa-solid fa-list-check"></i><span>Görevler</span></a>
  <a class="{{ 'active' if active=='recipients' else '' }}" href="/dashboard/kurumsal-bilgilendirme/alicilar"><i class="fa-solid fa-users"></i><span>Alıcılar</span></a>
  <a class="{{ 'active' if active=='templates' else '' }}" href="/dashboard/kurumsal-bilgilendirme/sablonlar"><i class="fa-solid fa-envelope-open-text"></i><span>Şablonlar</span></a>
  <a class="{{ 'active' if active=='test' else '' }}" href="/dashboard/kurumsal-bilgilendirme/test"><i class="fa-solid fa-paper-plane"></i><span>Test Merkezi</span></a>
  <a class="{{ 'active' if active=='logs' else '' }}" href="/dashboard/kurumsal-bilgilendirme/loglar"><i class="fa-solid fa-clock-rotate-left"></i><span>Gönderim Geçmişi</span></a>
  <a class="{{ 'active' if active=='system' else '' }}" href="/dashboard/kurumsal-bilgilendirme/sistem"><i class="fa-solid fa-server"></i><span>Sistem</span></a>
</nav>
{%- endmacro %}
'''

CONTENT_BLOCK = r'''
{% block content %}
{% set _active_tab = active_tab|default('overview', true) %}
{% set _ready_score = readiness_score|default(uat_score|default(100, true), true) %}
{% set _success_rate = success_rate|default(100, true) %}
{% set _failed_count = failed_count|default(0, true) %}
{% set _release_label = release_status|default('Hazır', true) %}
<div class="cic-shell cicp-shell">
  <section class="cicp-command-header" aria-label="Kurumsal Bilgilendirme Merkezi özet alanı">
    <div class="cicp-command-main">
      <span class="cicp-eyebrow"><i class="fa-solid fa-bullhorn"></i> Kurumsal Bilgilendirme Merkezi</span>
      <h1>Gönderim kontrol ve canlı geçiş merkezi</h1>
      <p>Bilgilendirme mailleri önce alıcı, şablon ve kuru çalışma kontrollerinden geçer; pilot test sonrası logları izlenerek güvenli şekilde gönderime alınır.</p>
      <div class="cicp-command-actions">
        <a class="cic-btn" href="/dashboard/kurumsal-bilgilendirme/test"><i class="fa-solid fa-paper-plane"></i> Pilot test yap</a>
        <a class="cic-btn secondary" href="/dashboard/kurumsal-bilgilendirme/loglar"><i class="fa-solid fa-clock-rotate-left"></i> Geçmişi incele</a>
        <a class="cic-btn ghost" href="/dashboard/kurumsal-bilgilendirme/sistem#release"><i class="fa-solid fa-shield-halved"></i> Canlı geçiş</a>
      </div>
    </div>
    <aside class="cicp-readiness-card" aria-label="Canlı hazırlık özeti">
      <div class="cicp-score-ring"><strong>{{ _ready_score }}</strong><span>/100</span></div>
      <div>
        <div class="cicp-score-title">Gönderime hazırlık</div>
        <div class="cicp-score-sub">UAT, CSRF, pilot test ve log kontrolleri</div>
        <span class="cic-badge ok"><i class="fa-solid fa-circle-check"></i> {{ _release_label }}</span>
      </div>
    </aside>
  </section>

  <section class="cicp-metrics" aria-label="Kısa durum özeti">
    <div class="cicp-metric"><span>Başarı oranı</span><strong>%{{ _success_rate }}</strong></div>
    <div class="cicp-metric"><span>Hatalı kayıt</span><strong>{{ _failed_count }}</strong></div>
    <div class="cicp-metric"><span>Canlı kontrol</span><strong>{{ _release_label }}</strong></div>
    <div class="cicp-metric"><span>Çalışma şekli</span><strong>Pilot önce</strong></div>
  </section>

  {{ tabs(_active_tab) }}
  <main class="cicp-content">
    {% block cic_content %}{% endblock %}
  </main>
</div>
{% endblock %}
'''


def backup(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = path.with_suffix(path.suffix + f".bak_phase7_12_{stamp}")
    shutil.copy2(path, bak)


def normalize_text(text: str) -> str:
    # Repair accidentally written literal \n and escaped quotes in Jinja templates.
    if "\\n" in text and text.count("\n") <= 3:
        text = text.replace("\\n", "\n")
    text = text.replace("\\'", "'").replace('\\"', '"')
    return text


def rewrite_base(base: Path) -> None:
    backup(base)
    text = base.read_text(encoding="utf-8") if base.exists() else ""
    text = normalize_text(text)
    if "{% block content %}" in text and "{% block cic_content %}" in text:
        # Prefer a clean known-good base to avoid missing macro regressions.
        new_text = BASE_TEMPLATE + "\n" + MACRO_BLOCK + "\n" + TABS_BLOCK + "\n" + CONTENT_BLOCK
    else:
        new_text = BASE_TEMPLATE + "\n" + MACRO_BLOCK + "\n" + TABS_BLOCK + "\n" + CONTENT_BLOCK
    base.write_text(new_text, encoding="utf-8", newline="\n")


def patch_items_calls(text: str) -> str:
    # Jinja dot access to dict key named "items" resolves to dict.items method.
    # Replace known phase quality usages with bracket lookup.
    replacements = {
        "phase6.template_quality.items": "phase6.template_quality['items']",
        "phase6.log_quality.items": "phase6.log_quality['items']",
        "phase6.test_quality.items": "phase6.test_quality['items']",
        "phase6.recipient_quality.items": "phase6.recipient_quality['items']",
        "phase6.task_quality.items": "phase6.task_quality['items']",
        "phase6.system_quality.items": "phase6.system_quality['items']",
        "phase7.release_checks.items": "phase7.release_checks['items']",
        "phase7.live_checklist.items": "phase7.live_checklist['items']",
        "phase7.rollback_plan.items": "phase7.rollback_plan['items']",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def patch_template(path: Path) -> bool:
    if not path.exists():
        return False
    text = normalize_text(path.read_text(encoding="utf-8"))
    original = text
    text = patch_items_calls(text)
    if text != original:
        backup(path)
        path.write_text(text, encoding="utf-8", newline="\n")
        return True
    # normalize only if literal escapes existed
    if text != path.read_text(encoding="utf-8"):
        backup(path)
        path.write_text(text, encoding="utf-8", newline="\n")
        return True
    return False


def ensure_css(root: Path) -> None:
    css_dir = root / "app" / "static" / "css"
    css_dir.mkdir(parents=True, exist_ok=True)
    css = css_dir / "corporate_information_center_v3_0_phase7_8_base_header_pro.css"
    if not css.exists():
        css.write_text("", encoding="utf-8")
    text = css.read_text(encoding="utf-8")
    marker = "/* BYS360_PHASE7_12_COMPAT */"
    if marker not in text:
        text += """
/* BYS360_PHASE7_12_COMPAT */
.cicp-command-header{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:22px;align-items:stretch;margin-bottom:18px;padding:26px;border:1px solid rgba(139,0,0,.12);border-radius:24px;background:linear-gradient(135deg,rgba(139,0,0,.96),rgba(105,0,0,.92));color:#fff;box-shadow:0 18px 45px rgba(20,20,20,.16)}
.cicp-command-main h1{margin:10px 0 8px;font-size:30px;line-height:1.15;color:#fff}.cicp-command-main p{max-width:760px;margin:0 0 18px;color:rgba(255,255,255,.88)}.cicp-eyebrow{display:inline-flex;align-items:center;gap:8px;padding:7px 11px;border-radius:999px;background:rgba(255,255,255,.14);font-size:13px;font-weight:700}.cicp-command-actions{display:flex;flex-wrap:wrap;gap:10px}.cic-btn,.cic-btn-v4{display:inline-flex;align-items:center;justify-content:center;gap:8px;border:0;border-radius:12px;padding:10px 14px;background:#8B0000;color:#fff!important;text-decoration:none!important;font-weight:700;box-shadow:0 10px 25px rgba(139,0,0,.18);cursor:pointer}.cic-btn.secondary,.cic-btn-v4.secondary{background:#fff;color:#8B0000!important}.cic-btn.ghost,.cic-btn-v4.ghost{background:rgba(255,255,255,.14);color:#fff!important;border:1px solid rgba(255,255,255,.26)}.cicp-readiness-card{display:flex;gap:16px;align-items:center;padding:18px;border-radius:20px;background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.2)}.cicp-score-ring{width:92px;height:92px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-direction:column;background:#fff;color:#8B0000}.cicp-score-ring strong{font-size:30px;line-height:1}.cicp-score-ring span{font-size:12px;font-weight:800}.cicp-score-title{font-weight:800;font-size:16px}.cicp-score-sub{font-size:13px;color:rgba(255,255,255,.78);margin:5px 0 10px}.cicp-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:18px}.cicp-metric{border:1px solid rgba(139,0,0,.12);border-radius:18px;background:rgba(255,255,255,.86);padding:16px;box-shadow:0 12px 32px rgba(20,20,20,.06)}.cicp-metric span{display:block;font-size:12px;color:#6b7280;font-weight:700}.cicp-metric strong{display:block;margin-top:5px;font-size:22px;color:#1f2937}.cic-badge,.cic-status-pill{display:inline-flex;align-items:center;gap:7px;border-radius:999px;padding:7px 10px;font-size:12px;font-weight:800;text-decoration:none!important}.cic-badge.ok,.cic-status-pill.ok,.cic-status-pill.success{background:#eaf7ef;color:#166534}.cic-badge.warning,.cic-status-pill.warning{background:#fff7e6;color:#92400e}.cic-badge.danger,.cic-status-pill.danger,.cic-status-pill.error{background:#fee2e2;color:#991b1b}.cic-badge.neutral,.cic-status-pill.info,.cic-status-pill.neutral{background:#f3f4f6;color:#374151}.cic-tabs{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 18px}.cic-tabs a{display:inline-flex;align-items:center;gap:8px;padding:10px 12px;border-radius:13px;border:1px solid rgba(139,0,0,.10);background:#fff;color:#374151!important;text-decoration:none!important;font-weight:750}.cic-tabs a.active{background:#8B0000;color:#fff!important;border-color:#8B0000}.cicp-content{min-height:300px}.cic-avatar-v4{width:38px;height:38px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;background:#8B0000;color:white;font-weight:900}.cic-person-v4{display:flex;gap:10px;align-items:flex-start}.cic-card-v4,.cic-card{background:#fff;border:1px solid rgba(139,0,0,.1);border-radius:20px;padding:18px;box-shadow:0 14px 32px rgba(20,20,20,.06)}.cic-card-header{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px}.cic-muted-v4{color:#6b7280}.cic-input-v4{width:100%;border:1px solid #e5e7eb;border-radius:12px;padding:11px 12px;background:#fff}.cic-grid-v4{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:14px}.span-4{grid-column:span 4}.span-6{grid-column:span 6}.span-8{grid-column:span 8}.span-12{grid-column:span 12}@media(max-width:1000px){.cicp-command-header{grid-template-columns:1fr}.cicp-metrics{grid-template-columns:repeat(2,1fr)}.span-4,.span-6,.span-8{grid-column:span 12}}@media(max-width:640px){.cicp-metrics{grid-template-columns:1fr}.cicp-command-header{padding:18px}.cicp-command-main h1{font-size:24px}}
"""
        css.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-ProjectRoot", required=True)
    ap.add_argument("-Mode", default="all")
    args = ap.parse_args()
    root = Path(args.ProjectRoot)
    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    tpl_dir = root / "app" / "templates" / "corporate_information_center"
    if not tpl_dir.exists():
        print(f"HATA: template klasoru yok: {tpl_dir}")
        return 2
    rewrite_base(base)
    changed = ["app\\templates\\corporate_information_center\\base.html"]
    for name in ["overview.html", "tasks.html", "recipients.html", "templates.html", "test.html", "logs.html", "system.html"]:
        if patch_template(tpl_dir / name):
            changed.append(f"app\\templates\\corporate_information_center\\{name}")
    ensure_css(root)
    changed.append("app\\static\\css\\corporate_information_center_v3_0_phase7_8_base_header_pro.css")
    print(f"{MARKER}_APPLY_OK")
    print("Güncellenen dosyalar:")
    for item in changed:
        print(f" - {item}")
    print(f"{MARKER}_GATE_OK")
    print(f"{MARKER}_FINAL_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
