# -*- coding: utf-8 -*-
"""
BYS360 Live Full Overlay V2.13.0
Idempotent live overlay helper.

Bu script mevcut proje dosyalarını yedekler, canlı tasarım/geri bildirim/rol matrisi
iyileştirmelerini statik CSS + JS katmanı olarak ekler ve kritik şablonları bozmadan
kurumsal görünüm standardını güçlendirir.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Iterable, Optional

VERSION = "BYS360_LIVE_FULL_OVERLAY_V2_13_0"
MARKER = "BYS360_LIVE_FULL_OVERLAY_V2_13_0"

CSS_REL = Path("app/static/css/bys360_live_full_overlay_v2_13_0.css")
JS_REL = Path("app/static/js/bys360_live_full_overlay_v2_13_0.js")
MANIFEST_REL = Path("_overlay_logs/bys360_live_full_overlay_v2_13_0_manifest.json")

CSS_CONTENT = r'''
/* BYS360_LIVE_FULL_OVERLAY_V2_13_0 */
:root{
  --bys360-primary:#8B0000;
  --bys360-primary-dark:#650000;
  --bys360-primary-soft:#fff2f2;
  --bys360-border:rgba(139,0,0,.16);
  --bys360-card:#ffffff;
  --bys360-text:#202124;
  --bys360-muted:#667085;
  --bys360-bg:#f7f3f1;
  --bys360-shadow:0 18px 50px rgba(32,24,24,.10);
  --bys360-radius:22px;
}

.bys360-live-enhanced .bys360-live-panel,
.bys360-live-panel{
  margin:0 0 18px 0;
  padding:20px 22px;
  border:1px solid var(--bys360-border);
  border-left:6px solid var(--bys360-primary);
  border-radius:var(--bys360-radius);
  background:linear-gradient(135deg,rgba(255,255,255,.96),rgba(255,246,246,.90));
  box-shadow:var(--bys360-shadow);
  color:var(--bys360-text);
}
.bys360-live-panel h2,
.bys360-live-panel h3{
  margin:0 0 8px 0;
  color:var(--bys360-primary-dark);
  font-weight:800;
  letter-spacing:-.02em;
}
.bys360-live-panel p{margin:0;color:var(--bys360-muted);line-height:1.55;}
.bys360-live-panel .bys360-live-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px;}
.bys360-live-pill{
  display:inline-flex;align-items:center;gap:6px;
  padding:7px 11px;border-radius:999px;
  background:var(--bys360-primary-soft);
  border:1px solid var(--bys360-border);
  color:var(--bys360-primary-dark);font-weight:700;font-size:.86rem;
}
.bys360-live-note{
  border-radius:16px;
  padding:13px 15px;
  background:#fff8e8;
  border:1px solid rgba(176,120,0,.18);
  color:#6f4d00;
  line-height:1.48;
}
.bys360-live-muted{color:var(--bys360-muted)!important;}

/* Genel form/kart standardı */
.bys360-live-enhanced form,
.bys360-live-enhanced .card,
.bys360-live-enhanced .panel,
.bys360-live-enhanced .box,
.bys360-live-enhanced .content-card{
  border-radius:20px;
}
.bys360-live-enhanced input,
.bys360-live-enhanced select,
.bys360-live-enhanced textarea{
  border-radius:14px!important;
  border:1px solid rgba(139,0,0,.18)!important;
}
.bys360-live-enhanced input:focus,
.bys360-live-enhanced select:focus,
.bys360-live-enhanced textarea:focus{
  outline:0!important;
  border-color:var(--bys360-primary)!important;
  box-shadow:0 0 0 .20rem rgba(139,0,0,.12)!important;
}
.bys360-live-enhanced .btn,
.bys360-live-enhanced button,
.bys360-live-enhanced input[type="submit"]{
  border-radius:14px;
}
.bys360-live-enhanced .btn-primary,
.bys360-live-enhanced button[type="submit"],
.bys360-live-enhanced input[type="submit"]{
  background:linear-gradient(135deg,var(--bys360-primary),var(--bys360-primary-dark));
  border-color:var(--bys360-primary-dark);
  box-shadow:0 10px 24px rgba(139,0,0,.20);
}

/* Geri bildirim/kampanya sayfası */
body.bys360-feedback-page .container,
body.bys360-feedback-page main,
body.bys360-feedback-page .main-content{
  max-width:1180px;
}
body.bys360-feedback-page table,
body.bys360-role-matrix-page table{
  overflow:hidden;
  border-radius:18px;
  border:1px solid rgba(139,0,0,.12);
  background:#fff;
}
body.bys360-feedback-page th,
body.bys360-role-matrix-page th{
  background:linear-gradient(135deg,#8B0000,#6e0000)!important;
  color:#fff!important;
  border-color:rgba(255,255,255,.14)!important;
  font-weight:700;
}
body.bys360-feedback-page td,
body.bys360-role-matrix-page td{vertical-align:middle;}

/* Rol matrisi okunabilirliği */
body.bys360-role-matrix-page .table-responsive,
body.bys360-role-matrix-page table{
  width:100%;
}
body.bys360-role-matrix-page input[type="checkbox"]{
  width:18px;height:18px;accent-color:var(--bys360-primary);
}
body.bys360-role-matrix-page .matrix-help,
body.bys360-role-matrix-page .role-help{
  font-size:.92rem;color:var(--bys360-muted);
}

/* Portal/iPhone responsive düzeltmeleri */
body.bys360-portal-page{
  -webkit-text-size-adjust:100%;
}
body.bys360-portal-page .portal-grid,
body.bys360-portal-page .dashboard-grid,
body.bys360-portal-page .cards-grid,
body.bys360-portal-page .quick-access-grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
  gap:16px;
}
body.bys360-portal-page img,
body.bys360-portal-page video,
body.bys360-portal-page iframe{max-width:100%;height:auto;}
body.bys360-portal-page .card,
body.bys360-portal-page .portal-card,
body.bys360-portal-page .home-card{min-width:0;}
body.bys360-portal-page .instagram-feed,
body.bys360-portal-page [data-widget="instagram"],
body.bys360-portal-page .ig-feed-card,
body.bys360-portal-page .social-feed-card{display:none!important;}

/* Mobil ve küçük ekran */
@media (max-width: 768px){
  body.bys360-live-enhanced .container,
  body.bys360-live-enhanced main,
  body.bys360-live-enhanced .main-content{
    width:100%!important;
    max-width:100%!important;
    padding-left:14px!important;
    padding-right:14px!important;
  }
  .bys360-live-panel{padding:17px 16px;border-radius:18px;}
  .bys360-live-panel h2{font-size:1.12rem;}
  body.bys360-live-enhanced table{font-size:.88rem;}
  body.bys360-live-enhanced .table-responsive{overflow-x:auto;-webkit-overflow-scrolling:touch;}
  body.bys360-live-enhanced .btn,
  body.bys360-live-enhanced button{
    min-height:42px;
  }
  body.bys360-portal-page .portal-grid,
  body.bys360-portal-page .dashboard-grid,
  body.bys360-portal-page .cards-grid,
  body.bys360-portal-page .quick-access-grid{
    grid-template-columns:1fr!important;
  }
  body.bys360-portal-page .sidebar,
  body.bys360-portal-page .portal-sidebar{
    max-width:88vw;
  }
}

@media (max-width: 430px){
  .bys360-live-panel{margin:0 0 14px 0;}
  .bys360-live-panel .bys360-live-actions{display:grid;grid-template-columns:1fr;}
  body.bys360-live-enhanced h1{font-size:1.34rem;line-height:1.18;}
  body.bys360-live-enhanced h2{font-size:1.16rem;}
  body.bys360-live-enhanced .card,
  body.bys360-live-enhanced .panel,
  body.bys360-live-enhanced .box{border-radius:18px;}
}

/* Kullanıcıya teknik dil sızmasını azaltan küçük vurgu */
.bys360-live-tech-clean{
  font-family:inherit!important;
  color:var(--bys360-muted)!important;
}
'''.strip() + "\n"

JS_CONTENT = r'''
// BYS360_LIVE_FULL_OVERLAY_V2_13_0
(function(){
  "use strict";

  function ready(fn){
    if(document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  function path(){ return (window.location.pathname || "").toLowerCase(); }

  function addBodyClasses(){
    var p = path();
    document.body.classList.add("bys360-live-enhanced");
    if(p.indexOf("/feedback") === 0 || p.indexOf("/geri-bildirim") === 0) document.body.classList.add("bys360-feedback-page");
    if(p.indexOf("/settings") === 0 || p.indexOf("/ayar") === 0 || p.indexOf("role-matrix") >= 0 || p.indexOf("rol") >= 0) document.body.classList.add("bys360-role-matrix-page");
    if(p.indexOf("/portal") === 0) document.body.classList.add("bys360-portal-page");
    if(p.indexOf("/person") === 0 || p.indexOf("/personel") === 0) document.body.classList.add("bys360-personnel-page");
  }

  function firstContent(){
    return document.querySelector("main .container, .main-content, main, .content, .container-fluid, .container, body");
  }

  function panel(id, title, text, pills){
    if(document.getElementById(id)) return null;
    var wrap = document.createElement("section");
    wrap.className = "bys360-live-panel";
    wrap.id = id;
    var h = document.createElement("h2");
    h.textContent = title;
    var p = document.createElement("p");
    p.textContent = text;
    wrap.appendChild(h);
    wrap.appendChild(p);
    if(pills && pills.length){
      var actions = document.createElement("div");
      actions.className = "bys360-live-actions";
      pills.forEach(function(label){
        var s = document.createElement("span");
        s.className = "bys360-live-pill";
        s.textContent = label;
        actions.appendChild(s);
      });
      wrap.appendChild(actions);
    }
    return wrap;
  }

  function insertTop(el){
    var c = firstContent();
    if(!c || !el) return;
    var target = c.querySelector("h1, .page-title, .content-header") || c.firstElementChild;
    if(target && target.parentNode) target.parentNode.insertBefore(el, target.nextSibling);
    else c.insertBefore(el, c.firstChild);
  }

  function enhanceFeedback(){
    var p = path();
    if(!(p.indexOf("/feedback") === 0 || p.indexOf("/geri-bildirim") === 0)) return;
    var isCampaignNew = p.indexOf("campaign") >= 0 || p.indexOf("kampanya") >= 0;
    if(isCampaignNew){
      insertTop(panel(
        "bys360-feedback-campaign-guidance",
        "Geri Bildirim Kampanyası Oluşturma",
        "Bu ekran; ekran hatası, eksik bildirme, öneri, tebrik ve teşekkür gibi kurumsal geri bildirimleri belirli dönem veya hedef kitle için toplamak amacıyla kullanılır. Kampanya açıldıktan sonra sonuçlar yetkili kullanıcılar tarafından izlenebilir ve raporlanabilir.",
        ["Kolay kullanım", "Yetki kontrollü görünürlük", "Kurumsal raporlama", "Takip edilebilir süreç"]
      ));
    }else{
      insertTop(panel(
        "bys360-feedback-guidance",
        "BYS360 Geri Bildirim Merkezi",
        "Bu alan; ekran hataları, eksikler, öneriler, tebrikler ve teşekkürlerin kayıtlı şekilde alınması için düzenlenmiştir. Amaç yalnızca mesaj toplamak değil, kurumsal gelişim için izlenebilir geri bildirim hafızası oluşturmaktır.",
        ["Ekran hatası", "Eksik bildirme", "Öneri", "Tebrik / teşekkür"]
      ));
    }
  }

  function enhanceRoleMatrix(){
    var p = path();
    if(!(p.indexOf("/settings") === 0 || p.indexOf("/ayar") === 0 || p.indexOf("role-matrix") >= 0 || p.indexOf("rol") >= 0)) return;
    var title = "Rol ve Menü Görünürlüğü Matrisi";
    var desc = "Bu bölümde rol, kişi ve birim bazlı görünürlük birlikte düşünülmelidir. Menü görünürlüğü kullanıcı deneyimi kadar güvenlik kontrolünün de parçasıdır; bu nedenle değişikliklerden sonra yetkili/yetkisiz kullanıcı senaryosu mutlaka kontrol edilmelidir.";
    if(p.indexOf("person") >= 0 || p.indexOf("personel") >= 0) {
      title = "Personel Bazlı Rol Matrisi";
      desc = "Bu ekran belirli personelin rol, menü ve işlem görünürlüğünü kontrol etmek için kullanılmalıdır. Kişi bazlı istisnalar kalıcı role dönüşmemeli; yapılan değişiklikler izlenebilir olmalıdır.";
    }
    insertTop(panel("bys360-role-matrix-guidance", title, desc, ["Rol bazlı", "Kişi bazlı", "Birim bazlı", "Audit log"]));
  }

  function enhancePortal(){
    var p = path();
    if(p.indexOf("/portal") !== 0) return;
    insertTop(panel(
      "bys360-portal-mobile-guidance",
      "Kurumsal Portal Mobil Uyumluluk",
      "Portal ekranı iPhone ve dar ekranlarda tek kolon, okunur kartlar ve taşmayan içerik mantığıyla düzenlenir. Instagram akışı gibi canlı bağlantı gerektiren alanlar hazır olana kadar ana görünümden gizlenir.",
      ["iPhone uyumlu", "Tek kolon kartlar", "Taşma kontrolü", "Sade portal"]
    ));
  }

  function cleanTechnicalLanguage(){
    var replacements = [
      [/\bunauthorized_scope\b/gi, "Bu işlem için yetkiniz bulunmamaktadır"],
      [/\bworkflow state\b/gi, "Süreç durumu"],
      [/\bphase sync\b/gi, "Süreç eşitleme"],
      [/\bsync\b/gi, "eşitleme"],
      [/\bdebug\b/gi, "kontrol"],
      [/\bendpoint\b/gi, "bağlantı"],
      [/\bexception\b/gi, "işlem hatası"],
      [/\btraceback\b/gi, "hata ayrıntısı"],
      [/\bJSON\b/g, "veri"],
      [/\bAPI error\b/gi, "Veriler şu anda alınamadı"]
    ];
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode:function(node){
        if(!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        var parent = node.parentElement;
        if(!parent) return NodeFilter.FILTER_REJECT;
        var tag = parent.tagName ? parent.tagName.toLowerCase() : "";
        if(["script","style","code","pre","textarea"].indexOf(tag) >= 0) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var nodes = [];
    while(walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function(n){
      var text = n.nodeValue;
      var out = text;
      replacements.forEach(function(r){ out = out.replace(r[0], r[1]); });
      if(out !== text) {
        n.nodeValue = out;
        if(n.parentElement) n.parentElement.classList.add("bys360-live-tech-clean");
      }
    });
  }

  function ensureTablesResponsive(){
    document.querySelectorAll("table").forEach(function(tbl){
      if(tbl.parentElement && tbl.parentElement.classList.contains("table-responsive")) return;
      var wrap = document.createElement("div");
      wrap.className = "table-responsive";
      tbl.parentNode.insertBefore(wrap, tbl);
      wrap.appendChild(tbl);
    });
  }

  ready(function(){
    addBodyClasses();
    enhanceFeedback();
    enhanceRoleMatrix();
    enhancePortal();
    ensureTablesResponsive();
    cleanTechnicalLanguage();
  });
})();
'''.strip() + "\n"

CAMPAIGN_TEMPLATE = r'''{% extends "base.html" %}
{% block title %}Geri Bildirim Kampanyası Oluştur{% endblock %}
{% block content %}
<section class="bys360-live-panel">
  <h2>Geri Bildirim Kampanyası Oluştur</h2>
  <p>Bu ekran; ekran hatası, eksik bildirme, öneri, tebrik ve teşekkür gibi kurumsal geri bildirimleri belirli dönem veya hedef kitle için toplamak amacıyla kullanılır.</p>
  <div class="bys360-live-actions">
    <span class="bys360-live-pill">Kolay kullanım</span>
    <span class="bys360-live-pill">Yetki kontrollü</span>
    <span class="bys360-live-pill">Raporlanabilir</span>
    <span class="bys360-live-pill">Kurumsal takip</span>
  </div>
</section>

<div class="card shadow-sm border-0 rounded-4">
  <div class="card-body p-4">
    <form method="post">
      {% if csrf_token is defined %}<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">{% endif %}
      <div class="row g-3">
        <div class="col-12 col-lg-8">
          <label class="form-label fw-semibold">Kampanya adı</label>
          <input class="form-control" name="title" placeholder="Örn. BYS360 ekran geri bildirimleri" required>
        </div>
        <div class="col-12 col-lg-4">
          <label class="form-label fw-semibold">Durum</label>
          <select class="form-select" name="status">
            <option value="active">Aktif</option>
            <option value="draft">Taslak</option>
            <option value="closed">Kapalı</option>
          </select>
        </div>
        <div class="col-12">
          <label class="form-label fw-semibold">Açıklama</label>
          <textarea class="form-control" name="description" rows="4" placeholder="Kampanyanın amacını kısa ve anlaşılır yazın."></textarea>
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label fw-semibold">Başlangıç tarihi</label>
          <input class="form-control" type="date" name="start_date">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label fw-semibold">Bitiş tarihi</label>
          <input class="form-control" type="date" name="end_date">
        </div>
        <div class="col-12">
          <label class="form-label fw-semibold">Hedef kitle</label>
          <select class="form-select" name="audience_scope">
            <option value="all">Tüm kullanıcılar</option>
            <option value="unit">Birim bazlı</option>
            <option value="role">Rol bazlı</option>
            <option value="selected">Seçili personel</option>
          </select>
          <div class="form-text">Hedef kitle görünürlüğü mevcut rol ve menü yetkileriyle birlikte çalışmalıdır.</div>
        </div>
      </div>
      <div class="d-flex flex-wrap gap-2 mt-4">
        <button type="submit" class="btn btn-primary px-4">Kampanyayı Kaydet</button>
        <a href="{{ url_for('feedback.admin_campaigns') if false else '/feedback/admin/campaigns' }}" class="btn btn-outline-secondary">Listeye Dön</a>
      </div>
    </form>
  </div>
</div>
{% endblock %}
'''.strip() + "\n"

README_TEXT = rf'''
{VERSION}

Amaç:
- Canlı BYS360 üzerinde geri bildirim/kampanya ekranlarının kurumsal görünümünü güçlendirmek.
- Portal ve iPhone/dar ekran responsive davranışını iyileştirmek.
- Ayarlar, rol matrisi ve personel bazlı rol matrisi ekranlarında açıklayıcı kurumsal rehber paneli eklemek.
- Kullanıcı ekranına sızan teknik ifadeleri azaltmak.
- Instagram/harici akış kartlarını portal görünümünden güvenli şekilde gizlemek.

Bu overlay mevcut iş kurallarını silmez; öncelikle statik CSS + JS katmanı ve güvenli şablon desteği ekler.
Mevcut dosyalar değiştirilmeden önce _backups klasörüne yedeklenir.

Uygulama:
1) Zip dosyasını C:\bys360\project içine açın.
2) PowerShell'i proje kökünde çalıştırın.
3) Aşağıdaki komutu uygulayın:

powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_live_full_overlay_v2_13_0.ps1 -ProjectRoot "C:\bys360\project"

Kontrol:
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_live_full_overlay_v2_13_0.ps1 -ProjectRoot "C:\bys360\project"

Geri alma:
powershell -ExecutionPolicy Bypass -File .\scripts\windows\rollback_bys360_live_full_overlay_v2_13_0.ps1 -ProjectRoot "C:\bys360\project"
'''.strip() + "\n"


def now_stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def backup_file(root: Path, path: Path, backup_root: Path, manifest: list[dict]) -> None:
    if not path.exists() or not path.is_file():
        return
    rel = path.relative_to(root)
    dst = backup_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)
    manifest.append({"path": str(rel).replace("\\", "/"), "backup": str(dst.relative_to(root)).replace("\\", "/")})


def write_managed_file(root: Path, rel: Path, content: str, backup_root: Path, manifest: list[dict]) -> None:
    path = root / rel
    old = read_text(path) if path.exists() else None
    if old == content:
        return
    backup_file(root, path, backup_root, manifest)
    write_text(path, content)
    manifest.append({"path": str(rel).replace("\\", "/"), "action": "written"})


def find_base_templates(root: Path) -> list[Path]:
    candidates = [
        root / "app/templates/base.html",
        root / "templates/base.html",
        root / "app/templates/layout.html",
        root / "templates/layout.html",
    ]
    return [p for p in candidates if p.exists()]


def ensure_asset_links(root: Path, backup_root: Path, manifest: list[dict]) -> None:
    css_href = "{{ url_for('static', filename='css/bys360_live_full_overlay_v2_13_0.css') }}"
    js_src = "{{ url_for('static', filename='js/bys360_live_full_overlay_v2_13_0.js') }}"
    css_tag = f'<!-- {MARKER}:css --><link rel="stylesheet" href="{css_href}">'
    js_tag = f'<!-- {MARKER}:js --><script defer src="{js_src}"></script>'
    for base in find_base_templates(root):
        text = read_text(base)
        new = text
        if MARKER + ":css" not in new:
            if "</head>" in new:
                new = new.replace("</head>", f"    {css_tag}\n</head>", 1)
            else:
                new = css_tag + "\n" + new
        if MARKER + ":js" not in new:
            if "</body>" in new:
                new = new.replace("</body>", f"    {js_tag}\n</body>", 1)
            else:
                new = new + "\n" + js_tag + "\n"
        if new != text:
            backup_file(root, base, backup_root, manifest)
            write_text(base, new)
            manifest.append({"path": str(base.relative_to(root)).replace("\\", "/"), "action": "asset_links_added"})


def ensure_sidebar_feedback_link(root: Path, backup_root: Path, manifest: list[dict]) -> None:
    # Bu küçük menü enjeksiyonu sadece Geri Bildirim hiç yoksa yapılır.
    for base in find_base_templates(root):
        text = read_text(base)
        if "Geri Bildirim" in text or "/feedback" in text:
            continue
        link = f'''
        <!-- {MARKER}:feedback-menu -->
        <li class="nav-item bys360-live-feedback-menu">
          <a class="nav-link" href="/feedback">
            <span>Geri Bildirim</span>
          </a>
        </li>
'''
        patterns = ["</ul>", "</nav>"]
        new = text
        for pat in patterns:
            idx = new.lower().find(pat)
            if idx >= 0:
                new = new[:idx] + link + new[idx:]
                break
        if new != text:
            backup_file(root, base, backup_root, manifest)
            write_text(base, new)
            manifest.append({"path": str(base.relative_to(root)).replace("\\", "/"), "action": "feedback_menu_added"})
            break


def ensure_templates(root: Path, backup_root: Path, manifest: list[dict]) -> None:
    # Var olan route'u bozmayacak şekilde alternatif kurumsal şablon bırakılır.
    write_managed_file(root, Path("app/templates/feedback/admin_campaign_new_bys360_live.html"), CAMPAIGN_TEMPLATE, backup_root, manifest)
    write_managed_file(root, Path("docs/BYS360_LIVE_FULL_OVERLAY_V2_13_0_README.txt"), README_TEXT, backup_root, manifest)


def patch_feedback_route_hint(root: Path, backup_root: Path, manifest: list[dict]) -> None:
    # Route dosyasını otomatik olarak değiştirmek yerine, güvenli bir not bloğu ekler.
    # İstenirse geliştirici mevcut /feedback/admin/campaigns/new route'undaki render_template'i
    # admin_campaign_new_bys360_live.html şablonuna yönlendirebilir.
    candidates = [root / "app/feedback/routes.py", root / "app/feedback.py"]
    hint = f'''

# {MARKER}: optional campaign template hint
# /feedback/admin/campaigns/new ekranı eski şablonla açılıyorsa, ilgili render_template çağrısı
# "feedback/admin_campaign_new_bys360_live.html" şablonuna yönlendirilebilir.
# Bu overlay varsayılan olarak route davranışını değiştirmez; CSS/JS katmanı canlı ekranı iyileştirir.
'''
    for p in candidates:
        if p.exists():
            text = read_text(p)
            if MARKER + ": optional campaign template hint" not in text:
                backup_file(root, p, backup_root, manifest)
                write_text(p, text.rstrip() + hint)
                manifest.append({"path": str(p.relative_to(root)).replace("\\", "/"), "action": "feedback_route_hint_added"})
            break


def ensure_check_manifest(root: Path, backup_root: Path, manifest: list[dict]) -> None:
    out = {
        "version": VERSION,
        "applied_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "files": manifest,
        "checks": [
            "base template asset links",
            "static css/js files",
            "feedback guidance layer",
            "role matrix guidance layer",
            "portal responsive layer",
            "technical language cleanup layer",
        ],
    }
    write_text(root / MANIFEST_REL, json.dumps(out, ensure_ascii=False, indent=2))


def validate_project(root: Path) -> None:
    if not root.exists():
        raise SystemExit(f"ProjectRoot bulunamadı: {root}")
    if not (root / "app").exists() and not (root / "templates").exists():
        raise SystemExit("Bu klasör BYS360 proje kökü gibi görünmüyor. app veya templates klasörü bulunamadı.")


def apply(root: Path) -> None:
    root = root.resolve()
    validate_project(root)
    backup_root = root / "_backups" / f"{VERSION}_{now_stamp()}"
    manifest: list[dict] = []

    write_managed_file(root, CSS_REL, CSS_CONTENT, backup_root, manifest)
    write_managed_file(root, JS_REL, JS_CONTENT, backup_root, manifest)
    ensure_asset_links(root, backup_root, manifest)
    ensure_sidebar_feedback_link(root, backup_root, manifest)
    ensure_templates(root, backup_root, manifest)
    patch_feedback_route_hint(root, backup_root, manifest)
    ensure_check_manifest(root, backup_root, manifest)

    print(f"{VERSION}_APPLY_OK")
    print(f"Manifest: {root / MANIFEST_REL}")
    if backup_root.exists():
        print(f"Backup: {backup_root}")


def check(root: Path) -> int:
    root = root.resolve()
    errors: list[str] = []
    for rel in [CSS_REL, JS_REL, MANIFEST_REL]:
        if not (root / rel).exists():
            errors.append(f"Eksik dosya: {rel}")
    bases = find_base_templates(root)
    if not bases:
        errors.append("base.html/layout.html bulunamadı")
    else:
        if not any(MARKER + ":css" in read_text(p) and MARKER + ":js" in read_text(p) for p in bases):
            errors.append("Base template içinde overlay CSS/JS bağlantısı bulunamadı")
    if errors:
        print(f"{VERSION}_CHECK_FAIL")
        for e in errors:
            print("- " + e)
        return 1
    print(f"{VERSION}_CHECK_OK")
    print("Kontrol edilen başlıklar: CSS/JS, base bağlantıları, manifest.")
    return 0


def rollback(root: Path) -> int:
    root = root.resolve()
    backups_dir = root / "_backups"
    if not backups_dir.exists():
        print("Rollback için _backups klasörü bulunamadı.")
        return 1
    backups = sorted([p for p in backups_dir.iterdir() if p.is_dir() and p.name.startswith(VERSION)], reverse=True)
    if not backups:
        print(f"{VERSION} için backup bulunamadı.")
        return 1
    latest = backups[0]
    restored = 0
    for src in latest.rglob("*"):
        if src.is_file():
            rel = src.relative_to(latest)
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            restored += 1
    print(f"{VERSION}_ROLLBACK_OK")
    print(f"Geri yüklenen dosya sayısı: {restored}")
    print(f"Kullanılan backup: {latest}")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=VERSION)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["apply", "check", "rollback"], default="apply")
    args = parser.parse_args(argv)
    root = Path(args.project_root)
    if args.mode == "apply":
        apply(root)
        return 0
    if args.mode == "check":
        return check(root)
    if args.mode == "rollback":
        return rollback(root)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
