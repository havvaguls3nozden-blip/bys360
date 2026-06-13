# -*- coding: utf-8 -*-
"""
BYS360 Corporate Information Center V3.0 Phase 7.9
Fixes base.html that was accidentally written as a one-line escaped string with literal \n and \' sequences.
Writes a clean Jinja template with real newlines and professional header layout.
"""
from __future__ import annotations

import argparse
import datetime as _dt
from pathlib import Path
import sys

PHASE = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_9_BASE_REAL_NEWLINES_FIX"

BASE_TEMPLATE = r'''{% extends "base.html" %}
{% block title %}Kurumsal Bilgilendirme Merkezi | BYS360{% endblock %}
{% block page_title %}Kurumsal Bilgilendirme Merkezi{% endblock %}
{% block page_subtitle %}Personel ve yönetici bilgilendirmeleri, şablonlar, alıcılar, test gönderimleri, loglar ve canlı geçiş kontrolleri tek merkezden yönetilir.{% endblock %}

{% block extra_head %}
{{ super() }}
<link rel="stylesheet" href="{{ url_for('static', filename='css/corporate_information_center_v3_0_phase7_9_base_clean.css') }}?v=2_15_29">
{% endblock %}

{% macro tabs(active) -%}
<nav class="cic-tabs" aria-label="Kurumsal Bilgilendirme Merkezi menüsü">
  <a class="{% if active == 'overview' %}active{% endif %}" href="/dashboard/kurumsal-bilgilendirme"><i class="fa-solid fa-gauge-high"></i><span>Genel Bakış</span></a>
  <a class="{% if active == 'tasks' %}active{% endif %}" href="/dashboard/kurumsal-bilgilendirme/gorevler"><i class="fa-solid fa-list-check"></i><span>Görevler</span></a>
  <a class="{% if active == 'recipients' %}active{% endif %}" href="/dashboard/kurumsal-bilgilendirme/alicilar"><i class="fa-solid fa-users"></i><span>Alıcılar</span></a>
  <a class="{% if active == 'templates' %}active{% endif %}" href="/dashboard/kurumsal-bilgilendirme/sablonlar"><i class="fa-solid fa-envelope-open-text"></i><span>Şablonlar</span></a>
  <a class="{% if active == 'test' %}active{% endif %}" href="/dashboard/kurumsal-bilgilendirme/test"><i class="fa-solid fa-paper-plane"></i><span>Test Merkezi</span></a>
  <a class="{% if active == 'logs' %}active{% endif %}" href="/dashboard/kurumsal-bilgilendirme/loglar"><i class="fa-solid fa-clock-rotate-left"></i><span>Gönderim Geçmişi</span></a>
  <a class="{% if active == 'system' %}active{% endif %}" href="/dashboard/kurumsal-bilgilendirme/sistem"><i class="fa-solid fa-server"></i><span>Sistem</span></a>
</nav>
{%- endmacro %}

{% macro user_full_name(user) -%}
{{ ((user.ad or '') ~ ' ' ~ (user.soyad or ''))|trim or user.full_name_cache or user.email or ('Kullanıcı #' ~ user.id) }}
{%- endmacro %}

{% block content %}
{% set _active_tab = active_tab|default('overview', true) %}
{% set _ready_score = readiness_score|default(uat_score|default(100, true), true) %}
{% set _success_rate = success_rate|default(100, true) %}
{% set _failed_count = failed_count|default(0, true) %}
{% set _release_label = release_status|default('Hazır', true) %}

<div class="cic-shell cicp-shell" data-bys360-phase="{{ 'BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_9_BASE_REAL_NEWLINES_FIX' }}">
  <section class="cicp-command-header" aria-label="Kurumsal Bilgilendirme Merkezi özet alanı">
    <div class="cicp-command-main">
      <div class="cicp-eyebrow"><i class="fa-solid fa-bullhorn"></i><span>Kurumsal Bilgilendirme Merkezi</span></div>
      <h1>Gönderim kontrol merkezi</h1>
      <p>Bilgilendirme mailleri; alıcı, şablon, kuru çalışma, pilot test ve gönderim geçmişi kontrolleriyle tek merkezden güvenli şekilde yönetilir.</p>
      <div class="cicp-command-actions">
        <a class="cic-btn" href="/dashboard/kurumsal-bilgilendirme/test"><i class="fa-solid fa-paper-plane"></i> Pilot test yap</a>
        <a class="cic-btn secondary" href="/dashboard/kurumsal-bilgilendirme/loglar"><i class="fa-solid fa-clock-rotate-left"></i> Geçmişi incele</a>
        <a class="cic-btn ghost" href="/dashboard/kurumsal-bilgilendirme/sistem#release"><i class="fa-solid fa-shield-halved"></i> Canlı geçiş</a>
      </div>
    </div>
    <aside class="cicp-readiness-card" aria-label="Canlı hazırlık özeti">
      <div class="cicp-score-ring"><strong>{{ _ready_score }}</strong><span>/100</span></div>
      <div class="cicp-score-copy">
        <div class="cicp-score-title">Gönderime hazırlık</div>
        <div class="cicp-score-sub">Pilot test, CSRF, log ve canlı geçiş kontrolleri</div>
        <span class="cic-badge ok"><i class="fa-solid fa-circle-check"></i> {{ _release_label }}</span>
      </div>
    </aside>
  </section>

  <section class="cicp-metrics" aria-label="Kısa durum özeti">
    <article class="cicp-metric"><span>Başarı oranı</span><strong>%{{ _success_rate }}</strong></article>
    <article class="cicp-metric"><span>Hatalı kayıt</span><strong>{{ _failed_count }}</strong></article>
    <article class="cicp-metric"><span>Canlı kontrol</span><strong>{{ _release_label }}</strong></article>
    <article class="cicp-metric"><span>Çalışma şekli</span><strong>Pilot önce</strong></article>
  </section>

  {{ tabs(_active_tab) }}

  <main class="cicp-content">
    {% block cic_content %}{% endblock %}
  </main>
</div>
{% endblock %}
'''

CSS_TEMPLATE = r'''
/* BYS360 Corporate Information Center V3.0 Phase 7.9 - clean base header */
.cic-shell.cicp-shell{
  --cic-red:#8B0000;
  --cic-red-dark:#650000;
  --cic-ink:#0f172a;
  --cic-muted:#64748b;
  --cic-line:rgba(139,0,0,.16);
  --cic-soft:#fff7f7;
  width:100%;
  max-width:1540px;
  margin:0 auto;
  padding:18px 16px 36px;
  color:var(--cic-ink);
}
.cicp-command-header{
  display:grid;
  grid-template-columns:minmax(0,1fr) 330px;
  gap:18px;
  align-items:stretch;
  background:linear-gradient(135deg,#fff 0%,#fff8f8 48%,#f7eeee 100%);
  border:1px solid var(--cic-line);
  border-radius:28px;
  padding:28px 30px;
  box-shadow:0 18px 48px rgba(15,23,42,.08);
  position:relative;
  overflow:hidden;
}
.cicp-command-header:before{
  content:"";
  position:absolute;
  inset:0 auto 0 0;
  width:7px;
  background:linear-gradient(180deg,var(--cic-red),#c9a227);
}
.cicp-command-main{position:relative; z-index:1;}
.cicp-eyebrow{
  display:inline-flex;
  align-items:center;
  gap:9px;
  padding:8px 13px;
  border:1px solid rgba(139,0,0,.14);
  border-radius:999px;
  background:#fff;
  color:var(--cic-red);
  font-weight:800;
  font-size:13px;
  letter-spacing:.02em;
}
.cicp-command-main h1{
  margin:18px 0 10px;
  font-size:clamp(31px,3.3vw,52px);
  line-height:1.03;
  letter-spacing:-.055em;
  color:#071124;
  font-weight:900;
}
.cicp-command-main p{
  margin:0;
  max-width:980px;
  color:#334155;
  font-size:16px;
  line-height:1.65;
}
.cicp-command-actions{
  display:flex;
  flex-wrap:wrap;
  gap:12px;
  margin-top:24px;
}
.cic-btn,
.cic-btn:visited{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  gap:9px;
  min-height:44px;
  padding:0 18px;
  border-radius:14px;
  border:1px solid var(--cic-red);
  background:linear-gradient(135deg,var(--cic-red),var(--cic-red-dark));
  color:#fff !important;
  text-decoration:none !important;
  font-weight:850;
  box-shadow:0 12px 24px rgba(139,0,0,.20);
}
.cic-btn.secondary,
.cic-btn.secondary:visited{
  background:#fff;
  color:var(--cic-red) !important;
  border-color:rgba(139,0,0,.20);
  box-shadow:none;
}
.cic-btn.ghost,
.cic-btn.ghost:visited{
  background:#fff;
  color:#1f2937 !important;
  border-color:#e5e7eb;
  box-shadow:none;
}
.cicp-readiness-card{
  position:relative;
  z-index:1;
  display:flex;
  align-items:center;
  gap:18px;
  padding:22px;
  background:rgba(255,255,255,.86);
  border:1px solid rgba(255,255,255,.75);
  border-radius:24px;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.9), 0 18px 40px rgba(15,23,42,.08);
}
.cicp-score-ring{
  width:94px;
  height:94px;
  flex:0 0 94px;
  border-radius:50%;
  display:flex;
  align-items:center;
  justify-content:center;
  flex-direction:column;
  background:conic-gradient(var(--cic-red) 0 100%, #f2e5e5 0 100%);
  color:#fff;
  box-shadow:0 16px 28px rgba(139,0,0,.22);
}
.cicp-score-ring strong{font-size:30px;line-height:1;font-weight:900;}
.cicp-score-ring span{font-size:12px;font-weight:800;opacity:.9;}
.cicp-score-title{font-size:18px;font-weight:900;color:#0f172a;margin-bottom:4px;}
.cicp-score-sub{font-size:13px;line-height:1.45;color:var(--cic-muted);margin-bottom:12px;}
.cic-badge{
  display:inline-flex;
  align-items:center;
  gap:7px;
  padding:7px 10px;
  border-radius:999px;
  font-size:12px;
  font-weight:850;
  border:1px solid #e5e7eb;
  color:#334155;
  background:#fff;
}
.cic-badge.ok{background:#ecfdf5;border-color:#bbf7d0;color:#047857;}
.cicp-metrics{
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:12px;
  margin:16px 0;
}
.cicp-metric{
  background:#fff;
  border:1px solid #edf0f4;
  border-radius:20px;
  padding:16px 18px;
  box-shadow:0 10px 26px rgba(15,23,42,.05);
}
.cicp-metric span{display:block;color:var(--cic-muted);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;margin-bottom:7px;}
.cicp-metric strong{font-size:25px;color:#101827;font-weight:900;letter-spacing:-.03em;}
.cic-tabs{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin:16px 0 18px;
  padding:10px;
  background:#fff;
  border:1px solid #edf0f4;
  border-radius:22px;
  box-shadow:0 10px 24px rgba(15,23,42,.05);
}
.cic-tabs a,
.cic-tabs a:visited{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding:11px 14px;
  border-radius:15px;
  color:#475569 !important;
  text-decoration:none !important;
  font-weight:800;
  border:1px solid transparent;
}
.cic-tabs a:hover{background:#fff7f7;color:var(--cic-red) !important;border-color:rgba(139,0,0,.12);}
.cic-tabs a.active{background:linear-gradient(135deg,var(--cic-red),var(--cic-red-dark));color:#fff !important;box-shadow:0 10px 18px rgba(139,0,0,.18);}
.cicp-content{margin-top:14px;}
@media (max-width:1100px){
  .cicp-command-header{grid-template-columns:1fr;}
  .cicp-metrics{grid-template-columns:repeat(2,minmax(0,1fr));}
}
@media (max-width:640px){
  .cic-shell.cicp-shell{padding:12px 10px 26px;}
  .cicp-command-header{padding:22px 20px;border-radius:22px;}
  .cicp-metrics{grid-template-columns:1fr;}
  .cic-tabs{overflow:auto;flex-wrap:nowrap;}
  .cic-tabs a{white-space:nowrap;}
}
'''

CHECK_SCRIPT = r'''# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from pathlib import Path
from jinja2 import Environment

PHASE = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_9_BASE_REAL_NEWLINES_FIX"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-ProjectRoot", default="C:/bys360/project")
    args = p.parse_args()
    root = Path(args.ProjectRoot)
    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    css = root / "app" / "static" / "css" / "corporate_information_center_v3_0_phase7_9_base_clean.css"
    text = base.read_text(encoding="utf-8")
    errors = []
    if PHASE not in text:
        errors.append("base.html içinde Faz 7.9 imzası yok")
    if "\\n" in text[:2000]:
        errors.append("base.html içinde literal \\n kalıntısı var")
    if "\\'" in text:
        errors.append("base.html içinde kaçışlı tırnak kalıntısı var")
    if "url_for('static', filename='css/corporate_information_center_v3_0_phase7_9_base_clean.css')" not in text:
        errors.append("Faz 7.9 CSS linki yok")
    if not css.exists():
        errors.append("Faz 7.9 CSS dosyası yok")
    try:
        Environment().parse(text)
    except Exception as exc:
        errors.append(f"Jinja parse hatası: {exc}")
    if errors:
        print(f"{PHASE}_GATE_FAIL")
        for e in errors:
            print("HATA:", e)
        return 2
    print(f"{PHASE}_GATE_OK")
    print(f"{PHASE}_FINAL_OK")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
'''


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8")


def backup_file(path: Path) -> None:
    if path.exists():
        stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = path.with_suffix(path.suffix + f".bak_phase7_9_{stamp}")
        backup.write_text(path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")


def apply(root: Path) -> int:
    print(f"{PHASE}_APPLY_START")
    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    css = root / "app" / "static" / "css" / "corporate_information_center_v3_0_phase7_9_base_clean.css"
    quality = root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_9_base_real_newlines_fix.py"

    backup_file(base)
    write_text(base, BASE_TEMPLATE)
    write_text(css, CSS_TEMPLATE)
    write_text(quality, CHECK_SCRIPT)

    print(f"{PHASE}_APPLY_OK")
    print("Güncellenen dosyalar:")
    print(" - app\\templates\\corporate_information_center\\base.html")
    print(" - app\\static\\css\\corporate_information_center_v3_0_phase7_9_base_clean.css")
    print(" - scripts\\quality\\check_corporate_information_center_v3_0_phase7_9_base_real_newlines_fix.py")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", default="C:/bys360/project")
    parser.add_argument("-Mode", default="all")
    args = parser.parse_args()
    root = Path(args.ProjectRoot)
    print(f"ProjectRoot={root}")
    apply(root)
    # run gate check immediately
    ns = {}
    exec(CHECK_SCRIPT, ns)
    check_main = ns["main"]
    # emulate args for embedded checker by directly checking files here to avoid argv issues
    import jinja2
    text = (root / "app" / "templates" / "corporate_information_center" / "base.html").read_text(encoding="utf-8")
    errors = []
    if PHASE not in text:
        errors.append("base.html içinde Faz 7.9 imzası yok")
    if "\\n" in text[:2000]:
        errors.append("base.html içinde literal \\n kalıntısı var")
    if "\\'" in text:
        errors.append("base.html içinde kaçışlı tırnak kalıntısı var")
    try:
        jinja2.Environment().parse(text)
    except Exception as exc:
        errors.append(f"Jinja parse hatası: {exc}")
    if errors:
        print(f"{PHASE}_GATE_FAIL")
        for e in errors:
            print("HATA:", e)
        return 2
    print(f"{PHASE}_GATE_OK")
    print(f"{PHASE}_FINAL_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
