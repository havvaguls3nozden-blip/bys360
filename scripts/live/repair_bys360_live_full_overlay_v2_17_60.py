from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

VERSION = "V2.17.60"
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
    parent = root.parent
    if root.name.lower() == "project":
        return parent / "backups" / f"BYS360_LIVE_FULL_{VERSION}_{stamp}"
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


def backup_file(root: Path, backup_root: Path, rel: Path, changed: list[str]) -> None:
    src = root / rel
    if not src.exists() or src.is_dir():
        return
    dst = backup_root / rel
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    rel_s = str(rel).replace("\\", "/")
    if rel_s not in changed:
        changed.append(rel_s)


def normalize_bom(root: Path, backup_root: Path, changed: list[str]) -> list[str]:
    fixed: list[str] = []
    candidates = list(KNOWN_BOM_FILES)
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
            fixed.append(str(rel).replace("\\", "/"))
    return fixed


def ensure_head_assets(root: Path, backup_root: Path, changed: list[str]) -> bool:
    rel = Path("app/templates/base.html")
    path = root / rel
    if not path.exists():
        return False
    text = read_text(path)
    original = text
    head_injection = """<!-- BYS360_LIVE_FULL_OVERLAY_V2_17_60_HEAD_BEGIN -->
{% if csrf_token is defined %}<meta name="csrf-token" content="{{ csrf_token() }}">{% endif %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/bys360_live_full_v2_17_60.css') }}?v=2_17_60">
{% if request and request.path and ('kurumsal-bilgilendirme/alicilar' in request.path or 'kurumsal-bilgilendirme/alicilar' in request.path|lower) %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/bys360_recipient_ux_v2_3.css') }}?v=2_17_60">
{% endif %}
<!-- BYS360_LIVE_FULL_OVERLAY_V2_17_60_HEAD_END -->"""
    if "BYS360_LIVE_FULL_OVERLAY_V2_17_60_HEAD_BEGIN" not in text:
        text = text.replace("</head>", head_injection + "\n</head>", 1)

    clean_tail = """{% block extra_scripts %}{% endblock %}

<!-- BYS360_LIVE_FULL_OVERLAY_V2_17_60_BODY_BEGIN -->
<div id="bys360-assistant-module-root" data-bys360-assistant-module="assistant-deep-knowledge-context-v27"></div>

<script src="{{ url_for('static', filename='js/bys360_screen_title_fix_v18_8.js') }}?v=2_17_60" defer></script>
<script src="{{ url_for('static', filename='js/bys360_form_csrf_guard_v2_17_60.js') }}?v=2_17_60" defer></script>
<script src="{{ url_for('static', filename='js/bys360_mobile_webview_scroll_fix_v12.js') }}" defer></script>
<script src="{{ url_for('static', filename='js/bys360_ios_pwa_v2.js') }}?v=ios-pwa-v2-2_17_60" defer></script>
<script src="{{ url_for('static', filename='pwa/ios_pwa_performance_mobile_v3_1.js') }}?v=2_17_60" defer></script>
<script src="{{ url_for('static', filename='pwa/ios_pwa_premium.js') }}?v=2_17_60" defer></script>
<script src="{{ url_for('static', filename='js/bys360_assistant_module.js') }}?v=assistant-2_17_60" defer></script>
<script src="{{ url_for('static', filename='js/bys360_assistant_closed_label_v2.js') }}?v=2_17_60" defer></script>
{% if request and request.path and ('kurumsal-bilgilendirme/alicilar' in request.path or 'kurumsal-bilgilendirme/alicilar' in request.path|lower) %}
<script src="{{ url_for('static', filename='js/bys360_recipient_ux_v2_3.js') }}?v=2_17_60" defer></script>
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
<!-- BYS360_LIVE_FULL_OVERLAY_V2_17_60_BODY_END -->
</body>
</html>
"""
    marker = "{% block extra_scripts %}{% endblock %}"
    if marker in text:
        text = re.sub(re.escape(marker) + r"(?s:.*)\Z", clean_tail, text, count=1)
    else:
        text = re.sub(r"</body>\s*</html>\s*\Z", clean_tail, text, count=1, flags=re.S | re.I)
    if text != original:
        backup_file(root, backup_root, rel, changed)
        write_text(path, text)
        return True
    return False


def write_assets(root: Path, backup_root: Path, changed: list[str]) -> list[str]:
    outputs = []
    css_rel = Path("app/static/css/bys360_live_full_v2_17_60.css")
    css_text = """/* BYS360_LIVE_FULL_OVERLAY_V2_17_60 */
:root { --bys360-live-red:#8B0000; --bys360-live-border:rgba(15,23,42,.10); }
.bys360-live-safe-note{border:1px solid rgba(139,0,0,.12);border-left:5px solid var(--bys360-live-red);background:#fff;border-radius:16px;padding:14px 16px;box-shadow:0 12px 26px rgba(15,23,42,.06)}
.table-responsive, .role-matrix-wrap, .settings-table-wrap, .cic-table-wrap { max-width:100%; overflow-x:auto; -webkit-overflow-scrolling:touch; }
.content-block img, .content-block iframe, .content-block video, .portal-card img { max-width:100%; height:auto; }
.alert, .flash-alert { border-radius:14px; }
input[name="csrf_token"] { display:none !important; }
@media (max-width: 768px){
  .content-wrap, #contentWrap { padding:14px !important; }
  .quick-link span, .user-role { display:none !important; }
  .page-title { max-width:58vw !important; font-size:1rem !important; }
  .table { min-width:680px; }
}
"""
    js_rel = Path("app/static/js/bys360_form_csrf_guard_v2_17_60.js")
    js_text = """/* BYS360_LIVE_FULL_OVERLAY_V2_17_60 */
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
      if(!input){ input=document.createElement('input'); input.type='hidden'; input.name='csrf_token'; form.prepend(input); }
      if(!input.value) input.value=token;
    });
  }
  function refresh(){
    if(!window.fetch) { syncForms(); return Promise.resolve(); }
    return fetch('/pwa/csrf-refresh', {headers:{'X-Requested-With':'XMLHttpRequest'}, cache:'no-store', credentials:'same-origin'})
      .then(function(res){ return res.ok ? res.json() : null; })
      .then(function(data){ if(data && data.csrf_token){ setMetaToken(data.csrf_token); syncForms(data.csrf_token); } else { syncForms(); } })
      .catch(function(){ syncForms(); });
  }
  document.addEventListener('DOMContentLoaded', function(){ refresh(); });
  window.addEventListener('pageshow', function(){ refresh(); });
  document.addEventListener('submit', function(event){
    var form=event.target;
    if(!form || !form.matches || !form.matches('form')) return;
    if((form.getAttribute('method')||'').toLowerCase() !== 'post') return;
    syncForms();
  }, true);
  window.bys360RefreshCsrf = refresh;
})();
"""
    for rel, text in [(css_rel, css_text), (js_rel, js_text)]:
        path = root / rel
        if path.exists() and read_text(path) == text:
            continue
        backup_file(root, backup_root, rel, changed)
        write_text(path, text)
        outputs.append(str(rel).replace("\\", "/"))
    return outputs


def patch_error_handlers(root: Path, backup_root: Path, changed: list[str]) -> bool:
    rel = Path("app/error_handlers.py")
    path = root / rel
    if not path.exists():
        return False
    text = read_text(path)
    original = text
    text = text.replace(
        "from flask import Flask, current_app, flash, g, redirect, render_template, request, session, url_for",
        "from flask import Flask, current_app, flash, g, jsonify, redirect, render_template, request, session, url_for",
        1,
    )
    helper = '''# BYS360_LIVE_FULL_OVERLAY_V2_17_60_CSRF_RECOVERY_BEGIN
def _safe_csrf_referer_target() -> str:
    """CSRF suresi dolan formlarda ayni kurum icinde guvenli geri donus adresi uretir."""
    try:
        candidate = request.headers.get("Referer") or request.referrer or ""
        if candidate:
            from urllib.parse import urlparse
            current_host = (request.host or "").lower()
            parsed = urlparse(candidate)
            if not parsed.netloc or parsed.netloc.lower() == current_host:
                path = parsed.path or "/"
                query = ("?" + parsed.query) if parsed.query else ""
                if not path.startswith("//"):
                    return path + query
    except Exception:
        current_app.logger.debug("CSRF guvenli geri donus adresi hesaplanamadi", exc_info=True)
    try:
        return url_for("main.dashboard")
    except Exception:
        try:
            return url_for("main.login")
        except Exception:
            return "/"


def _handle_expired_csrf_response(error: CSRFError):
    """CSRF korumasini gevsetmeden kullaniciyi temiz GET ekranina dondurur."""
    message = "Güvenlik doğrulaması yenilendi. Lütfen işlemi tekrar deneyin."
    try:
        current_app.logger.warning("CSRF yenileme gerektiren istek | hata=%s | detay=%s", getattr(error, "description", "-"), request_log_context())
    except Exception:
        pass
    wants_json = False
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
        response.headers["X-BYS360-CSRF-Recover"] = "V2.17.60"
    except Exception:
        pass
    return response
# BYS360_LIVE_FULL_OVERLAY_V2_17_60_CSRF_RECOVERY_END'''
    if "BYS360_LIVE_FULL_OVERLAY_V2_17_60_CSRF_RECOVERY_BEGIN" not in text:
        text = text.replace("def register_service_unavailable_handler(app: Flask) -> None:", helper + "\n\n\ndef register_service_unavailable_handler(app: Flask) -> None:", 1)
    old = '        return render_error_page(400, "Güvenlik Doğrulaması Başarısız", str(error.description))'
    if old in text:
        text = text.replace(old, '        return _handle_expired_csrf_response(error)', 1)
    if text != original:
        backup_file(root, backup_root, rel, changed)
        write_text(path, text)
        return True
    return False


def write_docs(root: Path, backup_root: Path, changed: list[str]) -> None:
    rel = Path("docs/BYS360_LIVE_FULL_OVERLAY_V2_17_60_README.md")
    text = """# BYS360 LIVE FULL OVERLAY V2.17.60

Bu overlay, yüklenen son BYS360 proje paketi üzerinde görülen canlı kritiklerini tek pakette toparlamak için hazırlanmıştır.

## Kapsam

- `base.html` kuyruk yapısını temizler: bölünmüş `</body>` etiketi, `</html>` sonrası kalan script/link parçaları ve mükerrer canlı blokları toparlanır.
- POST formları için CSRF meta + form senkronizasyon katmanı ekler.
- CSRF süresi dolduğunda korumayı kapatmadan kullanıcıyı geldiği ekrana güvenli şekilde döndürür.
- Logout akışında istemci cache/session temizleme davranışını korur.
- Syntax probe raporunda görülen UTF-8 BOM kaynaklı Python dosyalarını temizler.
- Canlı UI için küçük responsive/taşma koruma CSS katmanı ekler.
- Kontrol scripti raporu `reports/quality/bys360_live_full_overlay_v2_17_60_report.*` olarak üretir.

## Uygulama

```powershell
cd C:\\bys360\\project
Expand-Archive -LiteralPath "$env:USERPROFILE\\Downloads\\BYS360_LIVE_FULL_OVERLAY_V2_17_60.zip" -DestinationPath "C:\\bys360\\project" -Force
powershell -ExecutionPolicy Bypass -File .\\scripts\\windows\\repair_bys360_live_full_overlay_v2_17_60.ps1 -ProjectRoot "C:\\bys360\\project" -Mode all
```

## Kontrol

```powershell
powershell -ExecutionPolicy Bypass -File .\\scripts\\windows\\check_bys360_live_full_overlay_v2_17_60.ps1 -ProjectRoot "C:\\bys360\\project"
```

## Geri alma

Uygulama çıktısında yedek klasörü yazılır.

```powershell
powershell -ExecutionPolicy Bypass -File .\\scripts\\windows\\rollback_bys360_live_full_overlay_v2_17_60.ps1 -ProjectRoot "C:\\bys360\\project" -BackupRoot "C:\\bys360\\backups\\BYS360_LIVE_FULL_V2.17.60_YYYYMMDD_HHMMSS"
```

## Not

Bu paket `.env`, şifre, canlı veritabanı bağlantısı veya kullanıcı verisi içermez. Mevcut iş kurallarını gevşetmez; CSRF ve yetki kontrolleri korunur.
"""
    backup_file(root, backup_root, rel, changed)
    write_text(root / rel, text)


def check_project(root: Path) -> dict:
    result: dict = {"version": VERSION, "ok": True, "checks": []}
    def add(name: str, ok: bool, detail: str = ""):
        result["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            result["ok"] = False
    base = root / "app/templates/base.html"
    if base.exists():
        text = read_text(base)
        add("base_exists", True, "app/templates/base.html bulundu")
        add("base_no_split_body", "</bo" not in text and re.search(r"^\s*dy>\s*$", text, re.M) is None, "Bölünmüş body etiketi yok")
        add("base_has_clean_marker", "BYS360_LIVE_FULL_OVERLAY_V2_17_60_BODY_BEGIN" in text, "Temiz kuyruk marker var")
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
            import py_compile
            py_compile.compile(str(eh), doraise=True)
            add("error_handlers_compile", True, "error_handlers.py compile OK")
        except Exception as exc:
            add("error_handlers_compile", False, str(exc))
    else:
        add("error_handlers_exists", False, "app/error_handlers.py bulunamadı")
    for rel in KNOWN_BOM_FILES:
        path = root / rel
        if path.exists():
            data = path.read_bytes()
            add("bom_clean:" + str(rel).replace("\\", "/"), not data.startswith(b"\xef\xbb\xbf"), "UTF-8 BOM kontrolü")
    for rel in [Path("app/static/css/bys360_live_full_v2_17_60.css"), Path("app/static/js/bys360_form_csrf_guard_v2_17_60.js")]:
        add("asset_exists:" + str(rel).replace("\\", "/"), (root / rel).exists(), "Canlı asset kontrolü")
    return result


def write_report(root: Path, report: dict) -> None:
    out_dir = root / "reports/quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "bys360_live_full_overlay_v2_17_60_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = ["# BYS360 Live Full Overlay V2.17.60 Kontrol Raporu", "", f"overall_ok: `{report.get('ok')}`", "", "| Kontrol | Sonuç | Detay |", "|---|---:|---|"]
    for item in report.get("checks", []):
        detail = str(item.get("detail", "")).replace("|", "/")
        rows.append(f"| `{item['name']}` | `{item['ok']}` | {detail} |")
    (out_dir / "bys360_live_full_overlay_v2_17_60_report.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


def apply(root: Path) -> dict:
    stamp = now_stamp()
    backup_root = project_backup_root(root, stamp)
    backup_root.mkdir(parents=True, exist_ok=True)
    changed: list[str] = []
    result = {"version": VERSION, "applied_at": stamp, "backup_root": str(backup_root), "changed_files": changed, "actions": []}
    result["actions"].append({"name": "normalize_bom", "fixed": normalize_bom(root, backup_root, changed)})
    result["actions"].append({"name": "patch_base_html", "changed": ensure_head_assets(root, backup_root, changed)})
    result["actions"].append({"name": "write_assets", "changed": write_assets(root, backup_root, changed)})
    result["actions"].append({"name": "patch_error_handlers", "changed": patch_error_handlers(root, backup_root, changed)})
    write_docs(root, backup_root, changed)
    report = check_project(root)
    result["check"] = report
    write_report(root, report)
    return result


def rollback(root: Path, backup_root: Path) -> dict:
    restored = []
    if not backup_root.exists():
        raise SystemExit(f"BackupRoot bulunamadı: {backup_root}")
    for src in backup_root.rglob("*"):
        if src.is_file():
            rel = src.relative_to(backup_root)
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            restored.append(str(rel).replace("\\", "/"))
    return {"version": VERSION, "rollback_from": str(backup_root), "restored": restored, "ok": True}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=f"BYS360 Live Full Overlay {VERSION}")
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
