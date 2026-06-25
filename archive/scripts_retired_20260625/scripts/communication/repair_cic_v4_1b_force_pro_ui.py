from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path

MARKER = "BYS360_CIC_V4_1B_FORCE_PRO_UI"
CSS_HREF = "corporate_information_center_v4_1b_force_pro.css"
JS_SRC = "corporate_information_center_v4_1b_force_pro.js"

CSS_CONTENT = r'''
/* BYS360_CIC_V4_1B_FORCE_PRO_UI */
body.bys360-cic-pro-v41b .cic-v41b-topbar,
body.bys360-cic-pro-v41b .cic-v41b-card {
  border: 1px solid rgba(139, 0, 0, 0.12);
  background: rgba(255, 255, 255, 0.86);
  border-radius: 22px;
  box-shadow: 0 18px 45px rgba(23, 23, 23, 0.08);
  backdrop-filter: blur(14px);
}
body.bys360-cic-pro-v41b .cic-v41b-topbar {
  padding: 20px 22px;
  margin: 0 0 18px 0;
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
  position: relative;
  overflow: hidden;
}
body.bys360-cic-pro-v41b .cic-v41b-topbar::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 7px;
  background: linear-gradient(180deg, #8B0000, #b31b1b);
}
body.bys360-cic-pro-v41b .cic-v41b-title {
  margin: 0;
  font-size: 1.32rem;
  font-weight: 800;
  color: #241c1c;
  letter-spacing: -0.01em;
}
body.bys360-cic-pro-v41b .cic-v41b-subtitle {
  margin: 5px 0 0 0;
  color: #6b5f5f;
  font-size: .94rem;
  line-height: 1.45;
}
body.bys360-cic-pro-v41b .cic-v41b-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-radius: 999px;
  padding: 9px 13px;
  background: rgba(139, 0, 0, 0.08);
  color: #8B0000;
  font-weight: 700;
  white-space: nowrap;
}
body.bys360-cic-pro-v41b .cic-v41b-tabs {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin: 0 0 18px 0;
  padding: 12px;
  border: 1px solid rgba(139,0,0,.10);
  background: rgba(255,255,255,.72);
  border-radius: 18px;
  box-shadow: 0 12px 28px rgba(0,0,0,.05);
}
body.bys360-cic-pro-v41b .cic-v41b-tabs a {
  text-decoration: none !important;
  color: #3b3030;
  border: 1px solid rgba(139,0,0,.10);
  background: rgba(255,255,255,.78);
  border-radius: 999px;
  padding: 9px 13px;
  font-weight: 700;
  transition: transform .16s ease, box-shadow .16s ease, background .16s ease;
}
body.bys360-cic-pro-v41b .cic-v41b-tabs a:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(139,0,0,.10);
}
body.bys360-cic-pro-v41b .cic-v41b-tabs a.active,
body.bys360-cic-pro-v41b .cic-v41b-tabs a[aria-current="page"] {
  background: linear-gradient(135deg, #8B0000, #b21d1d);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 10px 22px rgba(139,0,0,.22);
}
body.bys360-cic-pro-v41b .cic-v41b-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin: 16px 0 18px;
}
body.bys360-cic-pro-v41b .cic-v41b-card {
  padding: 18px;
}
body.bys360-cic-pro-v41b .cic-v41b-metric-label {
  color: #6d6262;
  font-size: .82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .04em;
}
body.bys360-cic-pro-v41b .cic-v41b-metric-value {
  color: #241c1c;
  font-size: 1.8rem;
  font-weight: 850;
  margin-top: 6px;
}
body.bys360-cic-pro-v41b table {
  border-collapse: separate !important;
  border-spacing: 0 !important;
  width: 100%;
  overflow: hidden;
}
body.bys360-cic-pro-v41b table th {
  background: rgba(139,0,0,.055) !important;
  color: #4a3636 !important;
  font-weight: 800 !important;
  border-bottom: 1px solid rgba(139,0,0,.12) !important;
}
body.bys360-cic-pro-v41b table td,
body.bys360-cic-pro-v41b table th {
  padding: 12px 14px !important;
  vertical-align: middle !important;
}
body.bys360-cic-pro-v41b .btn,
body.bys360-cic-pro-v41b button,
body.bys360-cic-pro-v41b input[type="submit"] {
  border-radius: 12px !important;
}
body.bys360-cic-pro-v41b .btn-primary,
body.bys360-cic-pro-v41b button[type="submit"] {
  background: linear-gradient(135deg, #8B0000, #b21d1d) !important;
  border-color: transparent !important;
  box-shadow: 0 10px 22px rgba(139,0,0,.18) !important;
}
body.bys360-cic-pro-v41b input,
body.bys360-cic-pro-v41b select,
body.bys360-cic-pro-v41b textarea {
  border-radius: 14px !important;
  border-color: rgba(139,0,0,.16) !important;
}
body.bys360-cic-pro-v41b .pilot,
body.bys360-cic-pro-v41b [data-label*="pilot" i],
body.bys360-cic-pro-v41b [class*="pilot" i] {
  display: none !important;
}
@media (max-width: 1100px) {
  body.bys360-cic-pro-v41b .cic-v41b-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 640px) {
  body.bys360-cic-pro-v41b .cic-v41b-topbar { align-items: flex-start; flex-direction: column; }
  body.bys360-cic-pro-v41b .cic-v41b-grid { grid-template-columns: 1fr; }
  body.bys360-cic-pro-v41b .cic-v41b-tabs { overflow-x: auto; flex-wrap: nowrap; }
  body.bys360-cic-pro-v41b .cic-v41b-tabs a { white-space: nowrap; }
}
'''.strip() + "\n"

JS_CONTENT = r'''
// BYS360_CIC_V4_1B_FORCE_PRO_UI
(function () {
  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }
  function isCicPage() {
    return window.location.pathname.indexOf('/dashboard/kurumsal-bilgilendirme') === 0;
  }
  function cleanVisiblePilotText(root) {
    var walker = document.createTreeWalker(root || document.body, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        if (!node.nodeValue || !/pilot/i.test(node.nodeValue)) return NodeFilter.FILTER_REJECT;
        var p = node.parentElement;
        if (!p) return NodeFilter.FILTER_REJECT;
        var tag = p.tagName ? p.tagName.toLowerCase() : '';
        if (['script','style','textarea','input'].indexOf(tag) >= 0) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function (node) {
      node.nodeValue = node.nodeValue
        .replace(/\bpilot\b/ig, '')
        .replace(/\s{2,}/g, ' ')
        .replace(/\(\s*\)/g, '')
        .trimStart();
    });
  }
  function ensureTopbar() {
    var main = document.querySelector('main') || document.querySelector('.content') || document.querySelector('.main-content') || document.body;
    if (document.querySelector('.cic-v41b-topbar')) return;
    var topbar = document.createElement('section');
    topbar.className = 'cic-v41b-topbar';
    topbar.innerHTML = '<div><h1 class="cic-v41b-title">Kurumsal Bilgilendirme Merkezi</h1><p class="cic-v41b-subtitle">Duyuru, alıcı yönetimi, otomatik kutlamalar ve gönderim süreçleri tek merkezden yönetilir.</p></div><span class="cic-v41b-chip">Canlıya hazır kurumsal görünüm</span>';
    main.insertBefore(topbar, main.firstChild);
  }
  function makeTabs() {
    var current = window.location.pathname;
    var links = [
      ['/dashboard/kurumsal-bilgilendirme', 'Genel Bakış'],
      ['/dashboard/kurumsal-bilgilendirme/alicilar', 'Alıcılar'],
      ['/dashboard/kurumsal-bilgilendirme/kutlamalar', 'Kutlamalar'],
      ['/dashboard/kurumsal-bilgilendirme/sistem', 'Sistem'],
      ['/dashboard/kurumsal-bilgilendirme/test', 'Test Gönderimi']
    ];
    var tabs = document.querySelector('.cic-v41b-tabs');
    if (!tabs) {
      tabs = document.createElement('nav');
      tabs.className = 'cic-v41b-tabs';
      tabs.setAttribute('aria-label', 'Kurumsal Bilgilendirme sekmeleri');
      var anchor = document.querySelector('.cic-v41b-topbar');
      if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(tabs, anchor.nextSibling);
      else (document.querySelector('main') || document.body).insertBefore(tabs, (document.querySelector('main') || document.body).firstChild);
    }
    links.forEach(function (item) {
      var href = item[0], label = item[1];
      var found = tabs.querySelector('a[href="' + href + '"]') || document.querySelector('a[href="' + href + '"]');
      if (!found || found.parentElement !== tabs) {
        var a = document.createElement('a');
        a.href = href;
        a.textContent = label;
        tabs.appendChild(a);
        found = a;
      }
      if (current === href || (href !== '/dashboard/kurumsal-bilgilendirme' && current.indexOf(href) === 0)) {
        found.classList.add('active');
        found.setAttribute('aria-current', 'page');
      }
    });
  }
  function enhanceCards() {
    var tables = document.querySelectorAll('table');
    tables.forEach(function (table) {
      var wrapper = table.closest('.cic-v41b-card, .card, .panel, .box');
      if (!wrapper) {
        wrapper = document.createElement('div');
        wrapper.className = 'cic-v41b-card';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
      } else {
        wrapper.classList.add('cic-v41b-card');
      }
    });
    document.querySelectorAll('.card, .panel, .box, .glass-card').forEach(function (el) {
      el.classList.add('cic-v41b-card');
    });
  }
  function ensureSidebarCelebrationsLink() {
    var href = '/dashboard/kurumsal-bilgilendirme/kutlamalar';
    if (document.querySelector('a[href="' + href + '"]')) return;
    var candidates = Array.prototype.slice.call(document.querySelectorAll('a')).filter(function (a) {
      return /kurumsal bilgilendirme/i.test(a.textContent || '') || (a.getAttribute('href') || '').indexOf('/dashboard/kurumsal-bilgilendirme') === 0;
    });
    var base = candidates[0];
    if (!base || !base.parentNode) return;
    var clone = base.cloneNode(true);
    clone.href = href;
    clone.textContent = 'Kutlamalar';
    clone.classList.remove('active');
    base.parentNode.appendChild(clone);
  }
  ready(function () {
    if (!isCicPage()) return;
    document.body.classList.add('bys360-cic-pro-v41b');
    ensureTopbar();
    makeTabs();
    enhanceCards();
    ensureSidebarCelebrationsLink();
    cleanVisiblePilotText(document.body);
    setTimeout(function(){ cleanVisiblePilotText(document.body); }, 500);
  });
})();
'''.strip() + "\n"


def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def backup(path: Path, backup_root: Path) -> None:
    if path.exists():
        rel = path.drive.replace(":", "") + str(path).replace(":", "").replace("\\", "_").replace("/", "_")
        dest = backup_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)


def strip_pilot_text(text: str) -> str:
    # Do not touch technical filenames or Python identifiers, only visible-template text segments approximately.
    text = re.sub(r"(?i)\bpilot\s*çalışma\b", "önizleme", text)
    text = re.sub(r"(?i)\bpilot\s*mod\b", "önizleme modu", text)
    text = re.sub(r"(?i)>\s*pilot\s*<", "><", text)
    text = re.sub(r"(?i)\bpilot\b", "", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text


def inject_assets_into_html(path: Path) -> bool:
    text = read_text(path)
    original = text
    css_tag = "{{ url_for('static', filename='css/" + CSS_HREF + "') }}"
    js_tag = "{{ url_for('static', filename='js/" + JS_SRC + "') }}"
    if css_tag not in text:
        link = f"\n    <!-- {MARKER} -->\n    <link rel=\"stylesheet\" href=\"{{{{ url_for('static', filename='css/{CSS_HREF}') }}}}?v=4_1b_force\">\n"
        if "</head>" in text:
            text = text.replace("</head>", link + "</head>", 1)
        else:
            text = link + text
    if js_tag not in text:
        script = f"\n    <!-- {MARKER} -->\n    <script src=\"{{{{ url_for('static', filename='js/{JS_SRC}') }}}}?v=4_1b_force\" defer></script>\n"
        if "</body>" in text:
            text = text.replace("</body>", script + "</body>", 1)
        else:
            text = text + script
    if text != original:
        write_text(path, text)
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not root.exists():
        raise SystemExit(f"ProjectRoot bulunamadi: {root}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = root / "backups" / f"cic_v4_1b_force_pro_ui_{stamp}"
    backup_root.mkdir(parents=True, exist_ok=True)

    css_path = root / "app" / "static" / "css" / CSS_HREF
    js_path = root / "app" / "static" / "js" / JS_SRC
    backup(css_path, backup_root)
    backup(js_path, backup_root)
    write_text(css_path, CSS_CONTENT)
    write_text(js_path, JS_CONTENT)

    template_root = root / "app" / "templates"
    if not template_root.exists():
        raise SystemExit(f"Template klasoru bulunamadi: {template_root}")

    patched_templates = []
    # Clean visible pilot wording in CIC templates.
    cic_templates = list((template_root / "corporate_information_center").glob("*.html")) if (template_root / "corporate_information_center").exists() else []
    for path in cic_templates:
        text = read_text(path)
        new_text = strip_pilot_text(text)
        if new_text != text:
            backup(path, backup_root)
            write_text(path, new_text)
            patched_templates.append(str(path.relative_to(root)))

    # Inject assets into global base and CIC base when available.
    candidates = [template_root / "base.html", template_root / "layout.html", template_root / "corporate_information_center" / "base.html"]
    injected = []
    for path in candidates:
        if path.exists():
            backup(path, backup_root)
            if inject_assets_into_html(path):
                injected.append(str(path.relative_to(root)))

    # If no known base found, inject into all CIC templates so the UI still loads.
    if not injected:
        for path in cic_templates:
            backup(path, backup_root)
            if inject_assets_into_html(path):
                injected.append(str(path.relative_to(root)))

    # Try a direct server-side tab insertion in CIC base if it has obvious nav/tabs.
    cic_base = template_root / "corporate_information_center" / "base.html"
    if cic_base.exists():
        text = read_text(cic_base)
        if "/dashboard/kurumsal-bilgilendirme/kutlamalar" not in text and "Kutlamalar" not in text:
            add = "\n<a class=\"cic-v41b-server-tab\" href=\"/dashboard/kurumsal-bilgilendirme/kutlamalar\">Kutlamalar</a>\n"
            inserted = False
            for pat in (r"(</nav>)", r"(</ul>)", r"(</div>)"):
                if re.search(pat, text, flags=re.I):
                    text = re.sub(pat, add + r"\1", text, count=1, flags=re.I)
                    inserted = True
                    break
            if inserted:
                backup(cic_base, backup_root)
                write_text(cic_base, text)
                patched_templates.append(str(cic_base.relative_to(root)))

    print("BYS360_CIC_V4_1B_FORCE_PRO_UI_FILES_WRITTEN")
    print("CSS=", css_path)
    print("JS=", js_path)
    print("INJECTED=", ", ".join(injected) if injected else "NONE")
    print("PATCHED_TEMPLATES=", ", ".join(sorted(set(patched_templates))) if patched_templates else "NONE")
    print("BACKUP=", backup_root)
    print("BYS360_CIC_V4_1B_FORCE_PRO_UI_APPLY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
