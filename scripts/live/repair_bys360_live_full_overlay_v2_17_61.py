from __future__ import annotations

import argparse
import json
import py_compile
import re
import shutil
from datetime import datetime
from pathlib import Path

VERSION = "V2.17.61"
PREV = "V2.17.60"
KNOWN_BOM_FILES = [
    Path("app/communication/daily_weather_mail_routes.py"),
    Path("app/services/executive_mail_center_v2.py"),
    Path("scripts/executive/seed_executive_summary_menu_v2_14_8.py"),
    Path("scripts/performance_mail_automation_runner.py"),
    Path("scripts/scheduled/run_cic_staff_noon.py"),
]


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def project_backup_root(root: Path, stamp: str) -> Path:
    if root.name.lower() == "project":
        return root.parent / "backups" / f"BYS360_LIVE_FULL_{VERSION}_{stamp}"
    return root / "_backups" / f"BYS360_LIVE_FULL_{VERSION}_{stamp}"


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1254", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def rel_s(rel: Path) -> str:
    return str(rel).replace("\\", "/")


def backup_file(root: Path, backup_root: Path, rel: Path, changed: list[str]) -> None:
    src = root / rel
    if not src.exists() or src.is_dir():
        return
    dst = backup_root / rel
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    s = rel_s(rel)
    if s not in changed:
        changed.append(s)


def normalize_bom(root: Path, backup_root: Path, changed: list[str]) -> list[str]:
    fixed: list[str] = []
    candidates: list[Path] = list(KNOWN_BOM_FILES)
    for folder in (root / "app", root / "scripts"):
        if folder.exists():
            for path in folder.rglob("*.py"):
                try:
                    data = path.read_bytes()
                except OSError:
                    continue
                if data.startswith(b"\xef\xbb\xbf"):
                    rel = path.relative_to(root)
                    if rel not in candidates:
                        candidates.append(rel)
    for rel in candidates:
        path = root / rel
        if not path.exists():
            continue
        data = path.read_bytes()
        if data.startswith(b"\xef\xbb\xbf") or read_text(path).startswith("\ufeff"):
            backup_file(root, backup_root, rel, changed)
            write_text(path, read_text(path).lstrip("\ufeff"))
            fixed.append(rel_s(rel))
    return fixed


def strip_previous_live_blocks(text: str) -> str:
    # Aynı canlı bloklarının tekrar tekrar eklenmesini engeller.
    for ver in ("V2_17_60", "V2_17_61"):
        text = re.sub(rf"\n?<!-- BYS360_LIVE_FULL_OVERLAY_{ver}_HEAD_BEGIN -->.*?<!-- BYS360_LIVE_FULL_OVERLAY_{ver}_HEAD_END -->\n?", "\n", text, flags=re.S)
        text = re.sub(rf"\n?<!-- BYS360_LIVE_FULL_OVERLAY_{ver}_BODY_BEGIN -->.*?<!-- BYS360_LIVE_FULL_OVERLAY_{ver}_BODY_END -->\n?", "\n", text, flags=re.S)
    # Daha önce bozulmuş kapanıştan kalan çıplak script/link kuyruklarını kesmek için
    # {% block extra_scripts %} bloğundan sonraki alan yeniden kurulacaktır.
    return text


def patch_base_html(root: Path, backup_root: Path, changed: list[str]) -> bool:
    rel = Path("app/templates/base.html")
    path = root / rel
    if not path.exists():
        return False
    original = read_text(path)
    text = strip_previous_live_blocks(original)
    # Bölünmüş body kapanışını toparla.
    text = text.replace("</bo\n", "</bo")
    text = re.sub(r"</bo\s*\n\s*dy>", "</body>", text, flags=re.I)
    text = re.sub(r"^\s*dy>\s*$", "</body>", text, flags=re.M | re.I)

    head_injection = """<!-- BYS360_LIVE_FULL_OVERLAY_V2_17_61_HEAD_BEGIN -->
{% if csrf_token is defined %}<meta name="csrf-token" content="{{ csrf_token() }}">{% endif %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/bys360_live_full_v2_17_61.css') }}?v=2_17_61">
{% if request and request.path and ('kurumsal-bilgilendirme/alicilar' in request.path or 'kurumsal-bilgilendirme/alicilar' in request.path|lower) %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/bys360_recipient_ux_v2_3.css') }}?v=2_17_61">
{% endif %}
<!-- BYS360_LIVE_FULL_OVERLAY_V2_17_61_HEAD_END -->"""
    if "BYS360_LIVE_FULL_OVERLAY_V2_17_61_HEAD_BEGIN" not in text:
        if re.search(r"</head>", text, flags=re.I):
            text = re.sub(r"</head>", head_injection + "\n</head>", text, count=1, flags=re.I)
        else:
            text = head_injection + "\n" + text

    clean_tail = """{% block extra_scripts %}{% endblock %}

<!-- BYS360_LIVE_FULL_OVERLAY_V2_17_61_BODY_BEGIN -->
<div id="bys360-assistant-module-root" data-bys360-assistant-module="assistant-deep-knowledge-context-v27"></div>

<script src="{{ url_for('static', filename='js/bys360_screen_title_fix_v18_8.js') }}?v=2_17_61" defer></script>
<script src="{{ url_for('static', filename='js/bys360_form_csrf_guard_v2_17_61.js') }}?v=2_17_61" defer></script>
<script src="{{ url_for('static', filename='js/bys360_mobile_webview_scroll_fix_v12.js') }}" defer></script>
<script src="{{ url_for('static', filename='js/bys360_ios_pwa_v2.js') }}?v=ios-pwa-v2-2_17_61" defer></script>
<script src="{{ url_for('static', filename='pwa/ios_pwa_performance_mobile_v3_1.js') }}?v=2_17_61" defer></script>
<script src="{{ url_for('static', filename='pwa/ios_pwa_premium.js') }}?v=2_17_61" defer></script>
<script src="{{ url_for('static', filename='js/bys360_assistant_module.js') }}?v=assistant-2_17_61" defer></script>
<script src="{{ url_for('static', filename='js/bys360_assistant_closed_label_v2.js') }}?v=2_17_61" defer></script>
{% if request and request.path and ('kurumsal-bilgilendirme/alicilar' in request.path or 'kurumsal-bilgilendirme/alicilar' in request.path|lower) %}
<script src="{{ url_for('static', filename='js/bys360_recipient_ux_v2_3.js') }}?v=2_17_61" defer></script>
{% endif %}

<form id="bys360LogoutForceClearForm" action="/logout" method="post" style="display:none;" aria-hidden="true">
    {% if csrf_token is defined %}<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">{% endif %}
</form>
<script>
(function () {
    "use strict";
    var formId = "bys360LogoutForceClearForm";
    function isLogoutUrl(value) {
        if (!value) return false;
        try { var url = new URL(value, window.location.origin); return url.pathname.replace(/\\/+$/, "") === "/logout"; }
        catch (error) { return value === "/logout" || /\\/logout\\/?$/.test(String(value)); }
    }
    function clearLightClientState() {
        try { window.sessionStorage && window.sessionStorage.clear(); } catch (error) {}
        try {
            if (window.caches && window.caches.keys) {
                window.caches.keys().then(function (keys) {
                    keys.forEach(function (key) { if (/bys360/i.test(key)) window.caches.delete(key); });
                }).catch(function () {});
            }
        } catch (error) {}
    }
    function postLogout(event) {
        if (event && typeof event.preventDefault === "function") event.preventDefault();
        clearLightClientState();
        var form = document.getElementById(formId) || document.getElementById("logoutForm") || document.getElementById("bys360LogoutPostForm");
        if (form) { try { form.submit(); return false; } catch (error) {} }
        window.location.assign("/logout");
        return false;
    }
    window.bys360ForceLogout = postLogout;
    window.submitLogoutForm = postLogout;
    document.addEventListener("click", function (event) {
        var target = event.target && event.target.closest ? event.target.closest("a[href],button[data-logout]") : null;
        if (!target) return;
        var href = target.getAttribute("href") || target.getAttribute("data-logout") || "";
        if (!isLogoutUrl(href)) return;
        postLogout(event);
    }, true);
    window.addEventListener("pageshow", function (event) {
        if (event && event.persisted && /\\/logout\\/?$/.test(window.location.pathname)) window.location.replace("/login");
    });
})();
</script>
<!-- BYS360_LIVE_FULL_OVERLAY_V2_17_61_BODY_END -->
</body>
</html>
"""
    marker_re = re.compile(r"\{%\s*block\s+extra_scripts\s*%\}\s*\{%\s*endblock\s*%\}", re.I)
    match = marker_re.search(text)
    if match:
        text = text[: match.start()] + clean_tail
    else:
        # Son body kapanışından itibaren kuyruk yeniden yazılır. Hiç yoksa sona eklenir.
        body_matches = list(re.finditer(r"</body>", text, flags=re.I))
        if body_matches:
            text = text[: body_matches[-1].start()] + clean_tail
        else:
            text = text.rstrip() + "\n" + clean_tail
    if text != original:
        backup_file(root, backup_root, rel, changed)
        write_text(path, text)
        return True
    return False


def write_assets(root: Path, backup_root: Path, changed: list[str]) -> list[str]:
    written: list[str] = []
    css_rel = Path("app/static/css/bys360_live_full_v2_17_61.css")
    css = """/* BYS360_LIVE_FULL_OVERLAY_V2_17_61 */
:root { --bys360-live-red:#8B0000; --bys360-live-border:rgba(15,23,42,.10); }
.bys360-live-safe-note{border:1px solid rgba(139,0,0,.12);border-left:5px solid var(--bys360-live-red);background:#fff;border-radius:16px;padding:14px 16px;box-shadow:0 12px 26px rgba(15,23,42,.06)}
.table-responsive,.role-matrix-wrap,.settings-table-wrap,.cic-table-wrap{max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;}
.content-block img,.content-block iframe,.content-block video,.portal-card img{max-width:100%;height:auto;}
.alert,.flash-alert{border-radius:14px;}
input[name="csrf_token"]{display:none!important;}
@media (max-width:768px){
  .content-wrap,#contentWrap{padding:14px!important;}
  .quick-link span,.user-role{display:none!important;}
  .page-title{max-width:58vw!important;font-size:1rem!important;}
  .table{min-width:680px;}
}
"""
    js_rel = Path("app/static/js/bys360_form_csrf_guard_v2_17_61.js")
    js = """/* BYS360_LIVE_FULL_OVERLAY_V2_17_61 */
(function(){
  'use strict';
  function metaToken(){
    var meta=document.querySelector('meta[name="csrf-token"],meta[name="csrf_token"]');
    return meta && meta.getAttribute('content') ? meta.getAttribute('content') : '';
  }
  function setMetaToken(token){
    if(!token) return;
    var meta=document.querySelector('meta[name="csrf-token"]');
    if(!meta){ meta=document.createElement('meta'); meta.setAttribute('name','csrf-token'); document.head.appendChild(meta); }
    meta.setAttribute('content', token);
  }
  function syncForms(token){
    token = token || metaToken();
    if(!token) return;
    document.querySelectorAll('form').forEach(function(form){
      var method=(form.getAttribute('method')||'').toLowerCase();
      if(method !== 'post') return;
      var input=form.querySelector('input[name="csrf_token"]');
      if(!input){ input=document.createElement('input'); input.type='hidden'; input.name='csrf_token'; form.appendChild(input); }
      if(!input.value) input.value=token;
    });
  }
  function refreshToken(){
    return fetch('/pwa/csrf-refresh',{credentials:'same-origin',headers:{'Accept':'application/json'}})
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(data){
        var token = data && (data.csrf_token || data.token || data.csrf);
        if(token){ setMetaToken(token); syncForms(token); }
        return token || '';
      }).catch(function(){ return ''; });
  }
  document.addEventListener('DOMContentLoaded', function(){ syncForms(); refreshToken(); });
  document.addEventListener('submit', function(event){
    var form=event.target;
    if(!form || !form.matches || !form.matches('form')) return;
    if((form.getAttribute('method')||'').toLowerCase() !== 'post') return;
    syncForms();
  }, true);
  window.addEventListener('pageshow', function(){ refreshToken(); });
})();
"""
    for rel, text in [(css_rel, css), (js_rel, js)]:
        backup_file(root, backup_root, rel, changed)
        write_text(root / rel, text)
        written.append(rel_s(rel))
    return written


def ensure_flask_import(text: str, name: str) -> str:
    # from flask import ... satırında eksik importu ekler.
    m = re.search(r"^from flask import (?P<items>.+)$", text, flags=re.M)
    if not m:
        return f"from flask import {name}\n" + text
    items = [item.strip() for item in m.group("items").split(",")]
    if name not in items:
        items.append(name)
        items = sorted(set(items), key=lambda x: x.lower())
        text = text[: m.start()] + "from flask import " + ", ".join(items) + text[m.end():]
    return text


def patch_error_handlers(root: Path, backup_root: Path, changed: list[str]) -> bool:
    rel = Path("app/error_handlers.py")
    path = root / rel
    if not path.exists():
        return False
    original = read_text(path)
    text = original.lstrip("\ufeff")
    text = ensure_flask_import(text, "jsonify")

    helper = r'''
# BYS360_LIVE_FULL_OVERLAY_V2_17_61_CSRF_RECOVERY_BEGIN
def _safe_csrf_referer_target() -> str:
    """Ayni site icinde guvenli geri donus adresi uretir."""
    try:
        referer = request.headers.get("Referer") or ""
        host_url = request.host_url or "/"
        if referer.startswith(host_url):
            target = referer[len(host_url) - 1:]
            if target and not target.startswith("//"):
                return target
        if referer.startswith("/") and not referer.startswith("//"):
            return referer
    except Exception:
        try:
            current_app.logger.debug("CSRF guvenli geri donus adresi hesaplanamadi", exc_info=True)
        except Exception:
            pass
    for endpoint in ("main.dashboard", "dashboard.index", "main.login"):
        try:
            return url_for(endpoint)
        except Exception:
            continue
    return "/"


def _handle_expired_csrf_response(error: CSRFError):
    """CSRF korumasini gevsetmeden kullaniciyi temiz GET ekranina dondurur."""
    message = "Güvenlik doğrulaması yenilendi. Lütfen işlemi tekrar deneyin."
    try:
        current_app.logger.warning(
            "CSRF yenileme gerektiren istek | hata=%s | detay=%s",
            getattr(error, "description", "-"),
            request_log_context(),
        )
    except Exception:
        pass
    try:
        wants_json = request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in (request.headers.get("Accept") or "")
    except Exception:
        wants_json = False
    if wants_json:
        response = jsonify({"ok": False, "message": message, "csrf_refresh_url": "/pwa/csrf-refresh"})
        response.status_code = 400
    else:
        try:
            flash(message, "warning")
        except Exception:
            pass
        response = redirect(_safe_csrf_referer_target())
    try:
        response.headers["Cache-Control"] = "no-store, no-cache, max-age=0, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-BYS360-CSRF-Recover"] = "V2.17.61"
    except Exception:
        pass
    return response
# BYS360_LIVE_FULL_OVERLAY_V2_17_61_CSRF_RECOVERY_END
'''
    if "BYS360_LIVE_FULL_OVERLAY_V2_17_61_CSRF_RECOVERY_BEGIN" not in text:
        # Eski V2.17.60 helper varsa kaldırıp güncel helper koy.
        text = re.sub(r"\n?# BYS360_LIVE_FULL_OVERLAY_V2_17_60_CSRF_RECOVERY_BEGIN.*?# BYS360_LIVE_FULL_OVERLAY_V2_17_60_CSRF_RECOVERY_END\n?", "\n", text, flags=re.S)
        insert_at = None
        m = re.search(r"^def register_service_unavailable_handler\(", text, flags=re.M)
        if m:
            insert_at = m.start()
        else:
            m = re.search(r"^def register_error_handlers\(", text, flags=re.M)
            if m:
                insert_at = m.start()
        if insert_at is not None:
            text = text[:insert_at] + helper + "\n" + text[insert_at:]
        else:
            text = text.rstrip() + "\n\n" + helper + "\n"

    # CSRF handler içinde logout özel durumu korunur; sadece genel hata sayfası recovery'e döner.
    text = re.sub(
        r"return\s+render_error_page\(\s*400\s*,\s*[\"']Güvenlik Doğrulaması Başarısız[\"']\s*,\s*str\(error\.description\)\s*\)",
        "return _handle_expired_csrf_response(error)",
        text,
        count=1,
        flags=re.S,
    )
    if text != original:
        backup_file(root, backup_root, rel, changed)
        write_text(path, text)
        return True
    return False


def write_docs(root: Path, backup_root: Path, changed: list[str]) -> None:
    rel = Path("docs/BYS360_LIVE_FULL_OVERLAY_V2_17_61_README.md")
    text = """# BYS360 LIVE FULL OVERLAY V2.17.61 HOTFIX

Bu hotfix, V2.17.60 kontrolünde `ExitCode=2` alınması ihtimaline karşı daha dayanıklı canlı toparlama ve daha açıklayıcı check raporu üretir.

## Uygulama

```powershell
cd C:\\bys360\\project
Expand-Archive -LiteralPath "$env:USERPROFILE\\Downloads\\BYS360_LIVE_FULL_OVERLAY_V2_17_61_HOTFIX.zip" -DestinationPath "C:\\bys360\\project" -Force
powershell -ExecutionPolicy Bypass -File .\\scripts\\windows\\repair_bys360_live_full_overlay_v2_17_61.ps1 -ProjectRoot "C:\\bys360\\project" -Mode all
```

## Kontrol

```powershell
powershell -ExecutionPolicy Bypass -File .\\scripts\\windows\\check_bys360_live_full_overlay_v2_17_61.ps1 -ProjectRoot "C:\\bys360\\project"
```

Rapor yolu:

`reports\\quality\\bys360_live_full_overlay_v2_17_61_report.md`

Bu paket `.env`, şifre veya canlı veri içermez.
"""
    backup_file(root, backup_root, rel, changed)
    write_text(root / rel, text)


def check_project(root: Path) -> dict:
    report: dict = {"version": VERSION, "ok": True, "checks": []}

    def add(name: str, ok: bool, detail: str = "") -> None:
        report["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            report["ok"] = False

    base = root / "app/templates/base.html"
    if base.exists():
        text = read_text(base)
        add("base_exists", True, "app/templates/base.html bulundu")
        add("base_no_split_body", "</bo" not in text and re.search(r"^\s*dy>\s*$", text, re.M | re.I) is None, "Bölünmüş body etiketi yok")
        add("base_has_hotfix_marker", "BYS360_LIVE_FULL_OVERLAY_V2_17_61_BODY_BEGIN" in text, "V2.17.61 temiz kuyruk marker var")
        add("base_single_final_html", re.search(r"</body>\s*</html>\s*\Z", text, re.S | re.I) is not None, "Temiz </body></html> kapanışı")
        add("base_no_after_html", re.search(r"</html>\s*\S", text, re.S | re.I) is None, "</html> sonrası içerik yok")
        add("base_has_csrf_meta", "meta name=\"csrf-token\"" in text, "CSRF meta token var")
    else:
        add("base_exists", False, "app/templates/base.html bulunamadı")

    eh = root / "app/error_handlers.py"
    if eh.exists():
        et = read_text(eh)
        add("csrf_recovery_handler", "_handle_expired_csrf_response" in et and "X-BYS360-CSRF-Recover" in et, "CSRF recovery handler var")
        try:
            py_compile.compile(str(eh), doraise=True)
            add("error_handlers_compile", True, "error_handlers.py compile OK")
        except Exception as exc:
            add("error_handlers_compile", False, str(exc))
    else:
        add("error_handlers_exists", False, "app/error_handlers.py bulunamadı")

    for rel in KNOWN_BOM_FILES:
        path = root / rel
        if path.exists():
            add("bom_clean:" + rel_s(rel), not path.read_bytes().startswith(b"\xef\xbb\xbf"), "UTF-8 BOM kontrolü")

    for rel in [Path("app/static/css/bys360_live_full_v2_17_61.css"), Path("app/static/js/bys360_form_csrf_guard_v2_17_61.js")]:
        add("asset_exists:" + rel_s(rel), (root / rel).exists(), "Canlı asset kontrolü")

    # Check scriptleri de parse edilebilir olsun.
    for rel in [Path("scripts/live/repair_bys360_live_full_overlay_v2_17_61.py"), Path("scripts/quality/check_bys360_live_full_overlay_v2_17_61.py")]:
        path = root / rel
        if path.exists():
            try:
                py_compile.compile(str(path), doraise=True)
                add("script_compile:" + rel_s(rel), True, "script compile OK")
            except Exception as exc:
                add("script_compile:" + rel_s(rel), False, str(exc))
    return report


def write_report(root: Path, report: dict) -> None:
    out = root / "reports/quality"
    out.mkdir(parents=True, exist_ok=True)
    (out / "bys360_live_full_overlay_v2_17_61_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = [
        "# BYS360 Live Full Overlay V2.17.61 Hotfix Kontrol Raporu",
        "",
        f"overall_ok: `{report.get('ok')}`",
        "",
        "| Kontrol | Sonuç | Detay |",
        "|---|---:|---|",
    ]
    for item in report.get("checks", []):
        detail = str(item.get("detail", "")).replace("|", "/")
        rows.append(f"| `{item.get('name')}` | `{item.get('ok')}` | {detail} |")
    (out / "bys360_live_full_overlay_v2_17_61_report.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


def apply(root: Path) -> dict:
    stamp = now_stamp()
    backup_root = project_backup_root(root, stamp)
    backup_root.mkdir(parents=True, exist_ok=True)
    changed: list[str] = []
    result = {"version": VERSION, "applied_at": stamp, "backup_root": str(backup_root), "changed_files": changed, "actions": []}
    result["actions"].append({"name": "normalize_bom", "fixed": normalize_bom(root, backup_root, changed)})
    result["actions"].append({"name": "patch_base_html", "changed": patch_base_html(root, backup_root, changed)})
    result["actions"].append({"name": "write_assets", "written": write_assets(root, backup_root, changed)})
    result["actions"].append({"name": "patch_error_handlers", "changed": patch_error_handlers(root, backup_root, changed)})
    write_docs(root, backup_root, changed)
    report = check_project(root)
    write_report(root, report)
    result["check"] = report
    return result


def rollback(root: Path, backup_root: Path) -> dict:
    if not backup_root.exists():
        raise SystemExit(f"BackupRoot bulunamadı: {backup_root}")
    restored: list[str] = []
    for src in backup_root.rglob("*"):
        if src.is_file():
            rel = src.relative_to(backup_root)
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            restored.append(rel_s(rel))
    return {"version": VERSION, "rollback_from": str(backup_root), "restored": restored, "ok": True}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=f"BYS360 Live Full Overlay {VERSION} Hotfix")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["apply", "check", "all", "rollback"], default="all")
    parser.add_argument("--backup-root", default="")
    args = parser.parse_args(argv)
    root = Path(args.project_root).resolve()
    if not root.exists():
        raise SystemExit(f"ProjectRoot bulunamadı: {root}")
    if args.mode == "rollback":
        if not args.backup_root:
            raise SystemExit("Rollback için --backup-root zorunlu")
        result = rollback(root, Path(args.backup_root).resolve())
    elif args.mode == "check":
        result = check_project(root)
        write_report(root, result)
    else:
        result = apply(root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.mode == "check" and not result.get("ok"):
        return 2
    if args.mode in {"apply", "all"} and not result.get("check", {}).get("ok", False):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
