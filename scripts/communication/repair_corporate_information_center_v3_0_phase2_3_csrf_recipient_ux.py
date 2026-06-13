# -*- coding: utf-8 -*-
"""
BYS360 Corporate Information Center V3.0 Phase 2.3
- CSRF/login endpoint yönlendirme düzeltmesi
- Kurumsal Bilgilendirme > Alıcılar sayfası seçim araçları
- Türkçe kurumsal kullanıcı deneyimi iyileştirmesi
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from datetime import datetime

VERSION = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE2_3_CSRF_RECIPIENT_UX"

JS_CONTENT = r"""/* BYS360 Corporate Information Center - Recipient UX V2.3
   Kurumsal Bilgilendirme > Alıcılar sayfasında seçim araçlarını ekler.
   Dış sayfalarda çalışmaz. */
(function () {
  'use strict';

  var path = (window.location.pathname || '').toLocaleLowerCase('tr-TR');
  if (!(path.indexOf('kurumsal-bilgilendirme') >= 0 && path.indexOf('alicilar') >= 0)) {
    return;
  }

  function ready(fn) {
    if (document.readyState !== 'loading') { fn(); }
    else { document.addEventListener('DOMContentLoaded', fn); }
  }

  function norm(value) {
    return String(value || '')
      .toLocaleLowerCase('tr-TR')
      .replace(/\\s+/g, ' ')
      .trim();
  }

  function closestRow(el) {
    return el.closest('tr, .recipient-row, .user-row, .person-row, .employee-row, .list-group-item, .form-check, li, .card, .table-row, .row') || el.parentElement;
  }

  function textOf(row) {
    return row ? (row.innerText || row.textContent || '') : '';
  }

  function isVisible(row) {
    if (!row) { return false; }
    if (row.hidden) { return false; }
    if (row.style && row.style.display === 'none') { return false; }
    var rect = row.getBoundingClientRect();
    return rect.width > 0 || rect.height > 0 || row.offsetParent !== null;
  }

  function checkboxLabel(cb) {
    var row = closestRow(cb);
    var text = textOf(row).replace(/\\s+/g, ' ').trim();
    if (text) { return text.substring(0, 120); }
    return cb.getAttribute('aria-label') || cb.name || cb.value || 'Seçili alıcı';
  }

  function getUnit(row) {
    if (!row) { return ''; }
    var ds = row.dataset || {};
    var direct = ds.unit || ds.birim || ds.organizationUnit || ds.organization || ds.orgUnit || '';
    if (direct) { return direct.trim(); }

    var unitCell = row.querySelector('[data-unit], [data-birim], .unit, .birim, .org-unit, .organization-unit');
    if (unitCell) {
      return (unitCell.getAttribute('data-unit') || unitCell.getAttribute('data-birim') || unitCell.innerText || unitCell.textContent || '').trim();
    }

    var text = textOf(row);
    var m = text.match(/(?:Birim|Üst Birim|Unit)\\s*[:\\-]\\s*([^\\n\\r|•]+)/i);
    if (m && m[1]) { return m[1].trim(); }
    return '';
  }

  function getRoleText(row) {
    if (!row) { return ''; }
    var ds = row.dataset || {};
    return [ds.role, ds.rol, ds.title, ds.unvan, ds.gorev, textOf(row)].join(' ');
  }

  function collectCheckboxes() {
    return Array.prototype.slice.call(document.querySelectorAll('input[type="checkbox"]')).filter(function (cb) {
      if (cb.hasAttribute('data-bys360-recipient-control')) { return false; }
      if (cb.disabled) { return false; }
      var name = norm(cb.name + ' ' + cb.id + ' ' + cb.className);
      if (name.indexOf('csrf') >= 0) { return false; }
      if (name.indexOf('remember') >= 0) { return false; }
      if (name.indexOf('toggle-sidebar') >= 0) { return false; }
      var row = closestRow(cb);
      if (!row) { return false; }
      var rowText = norm(textOf(row));
      if (!rowText && !cb.value) { return false; }
      return true;
    });
  }

  function enhanceFormsWithCsrf() {
    // Aynı sayfadaki tokenı bulan formlara taşır; yeni butonlar form submit etmez ama mevcut formları güvenli tutar.
    var tokenInput = document.querySelector('input[name="csrf_token"][value], input[name="csrfmiddlewaretoken"][value]');
    var meta = document.querySelector('meta[name="csrf-token"], meta[name="csrf_token"]');
    var token = tokenInput ? tokenInput.value : (meta ? meta.getAttribute('content') : '');
    if (!token) { return; }

    Array.prototype.slice.call(document.querySelectorAll('form[method="post"], form[method="POST"]')).forEach(function (form) {
      if (form.querySelector('input[name="csrf_token"], input[name="csrfmiddlewaretoken"]')) { return; }
      var hidden = document.createElement('input');
      hidden.type = 'hidden';
      hidden.name = tokenInput && tokenInput.name ? tokenInput.name : 'csrf_token';
      hidden.value = token;
      form.appendChild(hidden);
    });
  }

  function buildToolbar() {
    var existing = document.querySelector('[data-bys360-recipient-toolbar="1"]');
    if (existing) { return existing; }

    var toolbar = document.createElement('section');
    toolbar.className = 'bys360-recipient-toolbar';
    toolbar.setAttribute('data-bys360-recipient-toolbar', '1');
    toolbar.innerHTML = [
      '<div class="bys360-rt-head">',
      '  <div>',
      '    <div class="bys360-rt-kicker">Kurumsal Bilgilendirme</div>',
      '    <h3>Alıcı seçim araçları</h3>',
      '    <p>Alıcıları hızlı seçmek, filtrelemek ve kontrol etmek için bu alanı kullanın.</p>',
      '  </div>',
      '  <div class="bys360-rt-count"><strong data-bys360-selected-count>0</strong><span>seçili alıcı</span></div>',
      '</div>',
      '<div class="bys360-rt-controls">',
      '  <label class="bys360-rt-field"><span>İsme / e-postaya göre ara</span><input data-bys360-recipient-control="1" data-bys360-search type="search" placeholder="Ad, soyad, e-posta, sicil no, birim veya unvan"></label>',
      '  <label class="bys360-rt-field"><span>Birime göre filtrele</span><input data-bys360-recipient-control="1" data-bys360-unit-filter type="search" list="bys360-recipient-units" placeholder="Birim adı yazın"></label>',
      '  <datalist id="bys360-recipient-units"></datalist>',
      '</div>',
      '<div class="bys360-rt-actions">',
      '  <button type="button" data-bys360-action="select-all">Tümünü seç</button>',
      '  <button type="button" data-bys360-action="select-visible">Görünenleri seç</button>',
      '  <button type="button" data-bys360-action="select-managers">Yönetici / amirleri seç</button>',
      '  <button type="button" data-bys360-action="select-staff">Personeli seç</button>',
      '  <button type="button" data-bys360-action="select-pilot">Pilot grup seç</button>',
      '  <button type="button" data-bys360-action="clear" class="ghost">Seçimleri temizle</button>',
      '</div>',
      '<div class="bys360-rt-selected" data-bys360-selected-panel>',
      '  <div class="bys360-rt-selected-title">Seçili alıcılar</div>',
      '  <div class="bys360-rt-selected-list" data-bys360-selected-list>Henüz alıcı seçilmedi.</div>',
      '</div>'
    ].join('');

    var anchor = document.querySelector('main, .main-content, .content, .container, .container-fluid, body');
    var table = document.querySelector('table');
    var form = document.querySelector('form');
    var target = table || form || anchor.firstElementChild || anchor;
    if (target && target.parentNode) {
      target.parentNode.insertBefore(toolbar, target);
    } else {
      document.body.insertBefore(toolbar, document.body.firstChild);
    }
    return toolbar;
  }

  ready(function () {
    enhanceFormsWithCsrf();

    var boxes = collectCheckboxes();
    if (!boxes.length) {
      // Sayfa verisi geç yüklenirse tekrar dene.
      setTimeout(function () {
        boxes = collectCheckboxes();
        if (boxes.length) { init(boxes); }
      }, 700);
      return;
    }
    init(boxes);
  });

  function init(boxes) {
    var toolbar = buildToolbar();
    var search = toolbar.querySelector('[data-bys360-search]');
    var unitFilter = toolbar.querySelector('[data-bys360-unit-filter]');
    var unitsList = toolbar.querySelector('#bys360-recipient-units');
    var countEl = toolbar.querySelector('[data-bys360-selected-count]');
    var selectedList = toolbar.querySelector('[data-bys360-selected-list]');

    function rows() {
      boxes = collectCheckboxes();
      return boxes.map(function (cb) { return { cb: cb, row: closestRow(cb) }; });
    }

    function refreshUnits() {
      var units = {};
      rows().forEach(function (item) {
        var unit = getUnit(item.row);
        if (unit) { units[unit] = true; }
      });
      unitsList.innerHTML = Object.keys(units).sort(function (a, b) { return a.localeCompare(b, 'tr'); }).map(function (u) {
        return '<option value="' + u.replace(/"/g, '&quot;') + '"></option>';
      }).join('');
    }

    function applyFilter() {
      var q = norm(search && search.value);
      var u = norm(unitFilter && unitFilter.value);
      rows().forEach(function (item) {
        var rowText = norm(textOf(item.row));
        var unitText = norm(getUnit(item.row));
        var matchQ = !q || rowText.indexOf(q) >= 0 || norm(item.cb.value).indexOf(q) >= 0;
        var matchU = !u || unitText.indexOf(u) >= 0 || rowText.indexOf(u) >= 0;
        if (item.row) {
          item.row.style.display = (matchQ && matchU) ? '' : 'none';
        }
      });
      updateSummary();
    }

    function visibleItems() {
      return rows().filter(function (item) { return isVisible(item.row); });
    }

    function setChecked(items, checked) {
      items.forEach(function (item) {
        item.cb.checked = checked;
        item.cb.dispatchEvent(new Event('change', { bubbles: true }));
      });
      updateSummary();
    }

    function updateSummary() {
      var selected = rows().filter(function (item) { return item.cb.checked; });
      countEl.textContent = String(selected.length);
      if (!selected.length) {
        selectedList.textContent = 'Henüz alıcı seçilmedi.';
        selectedList.classList.add('is-empty');
        return;
      }
      selectedList.classList.remove('is-empty');
      selectedList.innerHTML = selected.slice(0, 40).map(function (item) {
        return '<span>' + checkboxLabel(item.cb).replace(/[<>&]/g, function (s) {
          return ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' })[s];
        }) + '</span>';
      }).join('');
      if (selected.length > 40) {
        selectedList.innerHTML += '<em>+' + (selected.length - 40) + ' alıcı daha</em>';
      }
    }

    function selectByRole(kind) {
      var managerWords = ['başkan', 'baskan', 'amir', 'yönetici', 'yonetici', 'koordinatör', 'koordinator', 'müdür', 'mudur', 'şef', 'sef', 'grup başkanı', 'grup baskani'];
      var staffWords = ['personel', 'memur', 'işçi', 'isci', 'çalışan', 'calisan'];
      var words = kind === 'manager' ? managerWords : staffWords;
      var matched = visibleItems().filter(function (item) {
        var txt = norm(getRoleText(item.row));
        return words.some(function (w) { return txt.indexOf(w) >= 0; });
      });
      if (!matched.length && kind === 'staff') {
        matched = visibleItems();
      }
      setChecked(matched, true);
    }

    toolbar.addEventListener('click', function (ev) {
      var btn = ev.target.closest('button[data-bys360-action]');
      if (!btn) { return; }
      var action = btn.getAttribute('data-bys360-action');
      if (action === 'select-all') { setChecked(rows(), true); }
      if (action === 'select-visible') { setChecked(visibleItems(), true); }
      if (action === 'clear') { setChecked(rows(), false); }
      if (action === 'select-managers') { selectByRole('manager'); }
      if (action === 'select-staff') { selectByRole('staff'); }
      if (action === 'select-pilot') {
        var pilot = visibleItems().filter(function (item) {
          return norm(textOf(item.row)).indexOf('pilot') >= 0 || (item.row.dataset && item.row.dataset.pilot === '1');
        });
        if (!pilot.length) { pilot = visibleItems().slice(0, Math.min(5, visibleItems().length)); }
        setChecked(pilot, true);
      }
    });

    if (search) { search.addEventListener('input', applyFilter); }
    if (unitFilter) { unitFilter.addEventListener('input', applyFilter); }
    document.addEventListener('change', function (ev) {
      if (ev.target && ev.target.matches('input[type="checkbox"]')) { updateSummary(); }
    });

    refreshUnits();
    applyFilter();
    updateSummary();
  }
})();
"""

CSS_CONTENT = r"""/* BYS360 Corporate Information Center - Recipient UX V2.3 */
.bys360-recipient-toolbar {
  border: 1px solid rgba(139, 0, 0, 0.16);
  background: rgba(255, 255, 255, 0.92);
  border-radius: 22px;
  padding: 20px;
  margin: 0 0 22px 0;
  box-shadow: 0 18px 42px rgba(24, 24, 24, 0.08);
  backdrop-filter: blur(10px);
  color: #202124;
}
.bys360-rt-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid rgba(139, 0, 0, 0.10);
  padding-bottom: 14px;
  margin-bottom: 16px;
}
.bys360-rt-kicker {
  color: #8B0000;
  font-weight: 700;
  letter-spacing: .04em;
  font-size: .76rem;
  text-transform: uppercase;
}
.bys360-recipient-toolbar h3 {
  margin: 3px 0 5px;
  font-size: 1.2rem;
  color: #111827;
}
.bys360-recipient-toolbar p {
  margin: 0;
  color: #59606b;
  font-size: .92rem;
}
.bys360-rt-count {
  min-width: 120px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(139, 0, 0, 0.10), rgba(139, 0, 0, 0.04));
  border: 1px solid rgba(139, 0, 0, 0.15);
  padding: 12px 14px;
  text-align: center;
}
.bys360-rt-count strong {
  display: block;
  font-size: 1.7rem;
  line-height: 1;
  color: #8B0000;
}
.bys360-rt-count span {
  display: block;
  margin-top: 4px;
  color: #5f6368;
  font-size: .78rem;
}
.bys360-rt-controls {
  display: grid;
  grid-template-columns: minmax(220px, 1.4fr) minmax(180px, .8fr);
  gap: 14px;
  margin-bottom: 14px;
}
.bys360-rt-field span {
  display: block;
  font-size: .78rem;
  color: #4b5563;
  margin-bottom: 6px;
  font-weight: 700;
}
.bys360-rt-field input {
  width: 100%;
  border: 1px solid rgba(31, 41, 55, 0.18);
  border-radius: 14px;
  padding: 12px 14px;
  outline: none;
  background: #fff;
  color: #111827;
  transition: border-color .2s ease, box-shadow .2s ease;
}
.bys360-rt-field input:focus {
  border-color: rgba(139, 0, 0, .55);
  box-shadow: 0 0 0 4px rgba(139, 0, 0, .08);
}
.bys360-rt-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
  margin-bottom: 14px;
}
.bys360-rt-actions button {
  border: 0;
  background: #8B0000;
  color: white;
  padding: 10px 13px;
  border-radius: 999px;
  cursor: pointer;
  font-weight: 700;
  font-size: .86rem;
  box-shadow: 0 8px 18px rgba(139, 0, 0, .16);
}
.bys360-rt-actions button:hover {
  filter: brightness(.96);
}
.bys360-rt-actions button.ghost {
  background: #f3f4f6;
  color: #374151;
  box-shadow: none;
}
.bys360-rt-selected {
  border: 1px dashed rgba(139, 0, 0, .22);
  border-radius: 16px;
  padding: 12px;
  background: rgba(139, 0, 0, .035);
}
.bys360-rt-selected-title {
  font-weight: 800;
  color: #8B0000;
  margin-bottom: 8px;
  font-size: .86rem;
}
.bys360-rt-selected-list {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  color: #5f6368;
  font-size: .86rem;
}
.bys360-rt-selected-list span,
.bys360-rt-selected-list em {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background: #fff;
  border: 1px solid rgba(139, 0, 0, .12);
  padding: 6px 9px;
  font-style: normal;
}
.bys360-rt-selected-list.is-empty {
  display: block;
}
@media (max-width: 760px) {
  .bys360-rt-head {
    flex-direction: column;
  }
  .bys360-rt-count {
    width: 100%;
  }
  .bys360-rt-controls {
    grid-template-columns: 1fr;
  }
  .bys360-rt-actions button {
    width: 100%;
  }
}
"""

ASSET_MARKER = "BYS360_PHASE2_3_RECIPIENT_UX_ASSETS"
ASSET_BLOCK = """<!-- BYS360_PHASE2_3_RECIPIENT_UX_ASSETS_BEGIN -->
{% if request and request.path and ('kurumsal-bilgilendirme/alicilar' in request.path or 'kurumsal-bilgilendirme/alicilar' in request.path|lower) %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/bys360_recipient_ux_v2_3.css') }}">
<script src="{{ url_for('static', filename='js/bys360_recipient_ux_v2_3.js') }}" defer></script>
{% endif %}
<!-- BYS360_PHASE2_3_RECIPIENT_UX_ASSETS_END -->
"""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = path.parent / "_bys360_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"{path.name}.{VERSION}.{stamp}.bak"
    target.write_text(read_text(path), encoding="utf-8", newline="")
    return target


def ensure_assets(root: Path) -> list[str]:
    changed = []
    js_path = root / "app" / "static" / "js" / "bys360_recipient_ux_v2_3.js"
    css_path = root / "app" / "static" / "css" / "bys360_recipient_ux_v2_3.css"

    if not js_path.exists() or read_text(js_path) != JS_CONTENT:
        backup(js_path)
        write_text(js_path, JS_CONTENT)
        changed.append(str(js_path.relative_to(root)))

    if not css_path.exists() or read_text(css_path) != CSS_CONTENT:
        backup(css_path)
        write_text(css_path, CSS_CONTENT)
        changed.append(str(css_path.relative_to(root)))

    return changed


def patch_csrf_login_endpoint(root: Path) -> dict:
    candidates = [
        root / "app" / "__init__.py",
        root / "app" / "security.py",
        root / "app" / "auth.py",
        root / "app" / "routes.py",
    ]
    result = {"patched": [], "missing": []}
    replacements = [
        ("url_for('auth.login')", "url_for('main.login')"),
        ('url_for("auth.login")', 'url_for("main.login")'),
        ("url_for('login')", "url_for('main.login')"),
        ('url_for("login")', 'url_for("main.login")'),
        ("url_for('auth_bp.login')", "url_for('main.login')"),
        ('url_for("auth_bp.login")', 'url_for("main.login")'),
    ]

    for path in candidates:
        if not path.exists():
            result["missing"].append(str(path.relative_to(root)))
            continue
        text = read_text(path)
        new_text = text
        for old, new in replacements:
            new_text = new_text.replace(old, new)

        # Bazı dosyalarda endpoint değişken olarak tutulmuş olabilir.
        new_text = new_text.replace("LOGIN_ENDPOINT = 'auth.login'", "LOGIN_ENDPOINT = 'main.login'")
        new_text = new_text.replace('LOGIN_ENDPOINT = "auth.login"', 'LOGIN_ENDPOINT = "main.login"')
        new_text = new_text.replace("login_endpoint = 'auth.login'", "login_endpoint = 'main.login'")
        new_text = new_text.replace('login_endpoint = "auth.login"', 'login_endpoint = "main.login"')

        if new_text != text:
            backup(path)
            write_text(path, new_text)
            result["patched"].append(str(path.relative_to(root)))

    return result


def likely_base_templates(root: Path) -> list[Path]:
    template_root = root / "app" / "templates"
    if not template_root.exists():
        return []

    preferred_names = {
        "base.html", "layout.html", "layouts.html", "dashboard_base.html",
        "admin_base.html", "main_base.html", "portal_base.html"
    }

    htmls = list(template_root.rglob("*.html"))
    preferred = []
    others = []

    for path in htmls:
        name = path.name.lower()
        text = read_text(path)
        if "</body>" not in text.lower():
            continue
        if name in preferred_names or "base" in name or "layout" in name:
            preferred.append(path)
        elif "kurumsal" in text.lower() or "dashboard" in text.lower():
            others.append(path)

    # Önce base/layout adayları. Hiç yoksa kurumsal sayfa adaylarına düş.
    return preferred[:8] if preferred else others[:5]


def patch_template_assets(root: Path) -> dict:
    result = {"patched": [], "already": [], "candidates": []}
    for path in likely_base_templates(root):
        result["candidates"].append(str(path.relative_to(root)))
        text = read_text(path)
        if ASSET_MARKER in text:
            result["already"].append(str(path.relative_to(root)))
            continue

        lower = text.lower()
        idx = lower.rfind("</body>")
        if idx == -1:
            continue

        new_text = text[:idx] + "\n" + ASSET_BLOCK + "\n" + text[idx:]
        backup(path)
        write_text(path, new_text)
        result["patched"].append(str(path.relative_to(root)))

    return result


def write_marker(root: Path, payload: dict) -> None:
    out = root / "logs" / "bys360_corporate_information_center_v3_0_phase2_3_repair.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def repair(root: Path) -> dict:
    payload = {
        "version": VERSION,
        "project_root": str(root),
        "assets": ensure_assets(root),
        "csrf_endpoint": patch_csrf_login_endpoint(root),
        "template_assets": patch_template_assets(root),
    }
    write_marker(root, payload)
    return payload


def check(root: Path) -> dict:
    js_path = root / "app" / "static" / "js" / "bys360_recipient_ux_v2_3.js"
    css_path = root / "app" / "static" / "css" / "bys360_recipient_ux_v2_3.css"
    init_path = root / "app" / "__init__.py"
    template_root = root / "app" / "templates"

    init_text = read_text(init_path) if init_path.exists() else ""
    base_has_marker = False
    marker_files = []
    if template_root.exists():
        for path in template_root.rglob("*.html"):
            text = read_text(path)
            if ASSET_MARKER in text:
                base_has_marker = True
                marker_files.append(str(path.relative_to(root)))

    auth_login_left = "url_for('auth.login')" in init_text or 'url_for("auth.login")' in init_text
    login_endpoint_ok = (not init_path.exists()) or ("url_for('main.login')" in init_text or 'url_for("main.login")' in init_text or not auth_login_left)

    ok = js_path.exists() and css_path.exists() and base_has_marker and login_endpoint_ok
    return {
        "version": VERSION,
        "ok": bool(ok),
        "js_exists": js_path.exists(),
        "css_exists": css_path.exists(),
        "template_marker": base_has_marker,
        "template_marker_files": marker_files,
        "csrf_login_endpoint_ok": login_endpoint_ok,
        "auth_login_reference_left_in_app_init": auth_login_left,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=os.getcwd())
    parser.add_argument("--mode", choices=["repair", "check", "all"], default="all")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not root.exists():
        raise SystemExit(f"Project root bulunamadı: {root}")

    if args.mode in ("repair", "all"):
        print(json.dumps(repair(root), ensure_ascii=False, indent=2))

    if args.mode in ("check", "all"):
        result = check(root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result["ok"]:
            raise SystemExit(2)

    print(f"{VERSION}_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
