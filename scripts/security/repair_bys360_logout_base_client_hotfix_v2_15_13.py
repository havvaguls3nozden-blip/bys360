from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "BYS360_LOGOUT_BASE_CLIENT_HOTFIX_V2_15_13"
REQUIRED_MARKER = "BYS360_LOGOUT_FORCE_CLEAR_V2_15_12"

BASE_LOGOUT_BLOCK = r'''
<!-- BYS360_LOGOUT_FORCE_CLEAR_V2_15_12_BEGIN -->
<form id="bys360LogoutForceClearForm" action="/logout" method="post" style="display:none;" aria-hidden="true">
    {% if csrf_token is defined %}
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    {% endif %}
</form>
<script>
(function () {
    "use strict";
    var formId = "bys360LogoutForceClearForm";
    function isLogoutUrl(value) {
        if (!value) return false;
        try {
            var url = new URL(value, window.location.origin);
            return url.pathname.replace(/\/+$/, "") === "/logout";
        } catch (error) {
            return value === "/logout" || /\/logout\/?$/.test(String(value));
        }
    }
    function clearLightClientState() {
        try { window.sessionStorage && window.sessionStorage.clear(); } catch (error) {}
        try {
            if (window.caches && window.caches.keys) {
                window.caches.keys().then(function (keys) {
                    keys.forEach(function (key) {
                        if (/bys360/i.test(key)) window.caches.delete(key);
                    });
                }).catch(function () {});
            }
        } catch (error) {}
    }
    function postLogout(event) {
        if (event && typeof event.preventDefault === "function") event.preventDefault();
        clearLightClientState();
        var form = document.getElementById(formId) || document.getElementById("logoutForm") || document.getElementById("bys360LogoutPostForm");
        if (form) {
            try { form.submit(); return false; } catch (error) {}
        }
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
        if (event && event.persisted && /\/logout\/?$/.test(window.location.pathname)) {
            window.location.replace("/login");
        }
    });
})();
</script>
<!-- BYS360_LOGOUT_FORCE_CLEAR_V2_15_12_END -->
'''.strip()


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def backup(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".logout_base_client_v2_15_13.bak")
    if not bak.exists():
        shutil.copy2(path, bak)


def remove_html_block(text: str, marker: str) -> str:
    patterns = [
        rf"\n?<!--\s*{re.escape(marker)}_BEGIN\s*-->.*?<!--\s*{re.escape(marker)}_END\s*-->\n?",
        rf"\n?<!--\s*{re.escape(marker)}[^>]*BEGIN\s*-->.*?<!--\s*/?{re.escape(marker)}[^>]*END\s*-->\n?",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "\n", text, flags=re.IGNORECASE | re.DOTALL)
    return text


def remove_legacy_logout_blocks(text: str) -> str:
    # Eski istemci logout bloklarını tek noktaya indirir; backend tarafına dokunmaz.
    legacy_markers = [
        "BYS360_LOGOUT_FORCE_CLEAR_V2_15_12",
        "BYS360_LOGOUT_BASE_CLIENT_HOTFIX_V2_15_13",
        "BYS360_LOGOUT_POST_FIX_V2_4",
        "BYS360_LIVE_LOGOUT_FORCE_CLEAR_V2_13_3",
        "BYS360_LIVE_LOGOUT_FORCE_CLEAR_V2_13_4",
    ]
    for marker in legacy_markers:
        text = remove_html_block(text, marker)
    return text


def insert_before_body_or_append(text: str, block: str) -> str:
    matches = list(re.finditer(r"</body\s*>", text, flags=re.IGNORECASE))
    if matches:
        m = matches[-1]
        return text[:m.start()] + "\n" + block + "\n" + text[m.start():]
    matches = list(re.finditer(r"</html\s*>", text, flags=re.IGNORECASE))
    if matches:
        m = matches[-1]
        return text[:m.start()] + "\n" + block + "\n" + text[m.start():]
    return text.rstrip() + "\n" + block + "\n"


def patch_base_file(path: Path, project_root: Path) -> bool:
    original = read_text(path)
    text = remove_legacy_logout_blocks(original)
    text = insert_before_body_or_append(text, BASE_LOGOUT_BLOCK)
    required_tokens = [
        REQUIRED_MARKER,
        "bys360LogoutForceClearForm",
        "window.submitLogoutForm = postLogout",
        'window.location.assign("/logout")',
    ]
    missing = [token for token in required_tokens if token not in text]
    if missing:
        raise RuntimeError(f"{path.relative_to(project_root)} içine logout istemci bloğu yazılamadı: {', '.join(missing)}")
    if text != original:
        backup(path)
        write_text(path, text)
        return True
    return False


def candidate_base_files(project_root: Path) -> list[Path]:
    candidates = []
    primary = project_root / "app" / "templates" / "base.html"
    if primary.exists():
        candidates.append(primary)
    templates = project_root / "app" / "templates"
    if templates.exists():
        for p in templates.rglob("base.html"):
            if p not in candidates:
                candidates.append(p)
        admin_ai = templates / "admin_ai_base.html"
        if admin_ai.exists() and admin_ai not in candidates:
            candidates.append(admin_ai)
    return candidates


def quick_check(project_root: Path) -> list[str]:
    errors = []
    base = project_root / "app" / "templates" / "base.html"
    if not base.exists():
        return [f"Ana base.html bulunamadı: {base}"]
    text = read_text(base)
    for token in [
        REQUIRED_MARKER,
        "bys360LogoutForceClearForm",
        "window.submitLogoutForm = postLogout",
        'window.location.assign("/logout")',
    ]:
        if token not in text:
            errors.append(f"base.html logout istemci düzeltmesi eksiği: {token}")
    return errors


def run_existing_gate(project_root: Path) -> int | None:
    check = project_root / "scripts" / "security" / "check_bys360_logout_force_clear_v2_15_12.py"
    if not check.exists():
        return None
    py = project_root / ".venv" / "Scripts" / "python.exe"
    if not py.exists():
        py = Path(sys.executable)
    result = subprocess.run([str(py), str(check), str(project_root)], text=True)
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    project_root = Path(argv[0]).resolve() if argv else Path.cwd().resolve()
    if not (project_root / "app").exists():
        print(f"Proje kökü bulunamadı: {project_root}")
        return 2

    bases = candidate_base_files(project_root)
    if not bases:
        print("HATA: app/templates altında base.html bulunamadı.")
        return 2

    changed = []
    for path in bases:
        if patch_base_file(path, project_root):
            changed.append(str(path.relative_to(project_root)))

    errors = quick_check(project_root)
    if errors:
        print(f"{VERSION}_GATE_FAIL")
        for e in errors:
            print(f"HATA: {e}")
        return 1

    print(f"{VERSION}_APPLY_OK")
    if changed:
        print("Güncellenen dosyalar:")
        for item in changed:
            print(f" - {item}")
    else:
        print("base.html logout istemci düzeltmesi zaten uygulanmış görünüyor.")

    existing_gate = run_existing_gate(project_root)
    if existing_gate is None:
        print(f"{VERSION}_LOCAL_GATE_OK")
    elif existing_gate != 0:
        print(f"{VERSION}_EXISTING_GATE_STILL_FAIL")
        return existing_gate

    print(f"{VERSION}_FINAL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
