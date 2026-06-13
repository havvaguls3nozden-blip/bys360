# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

EFFECTIVE_MENU_MARKER = "BYS360_PERFORMANCE_COMPLETION_PHASE3_EFFECTIVE_MENU_BRIDGE"
ROUTE_SUPPORT_MARKER = "BYS360_PERFORMANCE_COMPLETION_PHASE3_ROUTE_SUPPORT_BRIDGE"

EFFECTIVE_MENU_BRIDGE = r'''

# BYS360_PERFORMANCE_COMPLETION_PHASE3_EFFECTIVE_MENU_BRIDGE_BEGIN
# Faz 3 %100 kapanış: performans menü görünürlüğü, merkezi görünürlük sözleşmesine son katman olarak bağlanır.
try:
    _BYS360_PHASE3_COMPLETION_ORIGINAL_BUILD_MENU_VISIBILITY_MAP = build_menu_visibility_map

    def build_menu_visibility_map(user, *args, **kwargs):  # type: ignore[no-redef]
        visibility = dict(_BYS360_PHASE3_COMPLETION_ORIGINAL_BUILD_MENU_VISIBILITY_MAP(user, *args, **kwargs) or {})
        try:
            from app.services.performance.completion_phase3_visibility_scope import apply_phase3_menu_visibility
            return apply_phase3_menu_visibility(visibility, user)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_PERFORMANCE_COMPLETION_PHASE3_EFFECTIVE_MENU_BRIDGE_FALLBACK")
            return visibility
except Exception:
    import logging
    logging.getLogger(__name__).exception("BYS360_PERFORMANCE_COMPLETION_PHASE3_EFFECTIVE_MENU_BRIDGE_SETUP_FAILED")
# BYS360_PERFORMANCE_COMPLETION_PHASE3_EFFECTIVE_MENU_BRIDGE_END
'''

ROUTE_SUPPORT_BRIDGE = r'''

# BYS360_PERFORMANCE_COMPLETION_PHASE3_ROUTE_SUPPORT_BRIDGE_BEGIN
# Faz 3 %100 kapanış: yetkisiz erişimde kurumsal 403 ve menu_key_required backend kilidi.
try:
    _BYS360_PHASE3_COMPLETION_ORIGINAL_RENDER_ACCESS_DENIED = render_access_denied
except Exception:
    _BYS360_PHASE3_COMPLETION_ORIGINAL_RENDER_ACCESS_DENIED = None


def render_access_denied(message: str | None = None, *, status_code: int = 403):  # type: ignore[no-redef]
    try:
        from app.services.performance.completion_phase3_visibility_scope import phase3_denied_response
        return phase3_denied_response(message, status_code=status_code)
    except Exception:
        if _BYS360_PHASE3_COMPLETION_ORIGINAL_RENDER_ACCESS_DENIED is not None:
            return _BYS360_PHASE3_COMPLETION_ORIGINAL_RENDER_ACCESS_DENIED(message, status_code=status_code)
        return (message or "Bu sayfaya erişim yetkiniz bulunmamaktadır.", status_code)


def menu_key_required(menu_key: str):  # type: ignore[no-redef]
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("main.login"))
            if not can_access_menu(current_user, menu_key):
                return render_access_denied("Bu sayfaya erişim yetkiniz bulunmamaktadır.", status_code=403)
            return view_func(*args, **kwargs)
        return wrapper
    return decorator
# BYS360_PERFORMANCE_COMPLETION_PHASE3_ROUTE_SUPPORT_BRIDGE_END
'''


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def append_once(path: Path, marker: str, block: str) -> bool:
    text = read_text(path)
    if marker in text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n" + block.strip() + "\n", encoding="utf-8")
    return True


def patch_files(root: Path) -> dict[str, object]:
    changed = []
    effective_menu = root / "app" / "services" / "settings" / "effective_menu.py"
    route_support = root / "app" / "route_support.py"
    if effective_menu.exists() and append_once(effective_menu, EFFECTIVE_MENU_MARKER, EFFECTIVE_MENU_BRIDGE):
        changed.append(str(effective_menu.relative_to(root)))
    if route_support.exists() and append_once(route_support, ROUTE_SUPPORT_MARKER, ROUTE_SUPPORT_BRIDGE):
        changed.append(str(route_support.relative_to(root)))
    return {"ok": True, "changed": changed}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "seed", "patch", "all"], default="all")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    result = {
        "package": "performance_completion_phase3_visibility_center",
        "version": "V1",
        "project_root": str(root),
        "mode": args.mode,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    sys.path.insert(0, str(root))

    if args.mode in {"patch", "all"}:
        result["patch"] = patch_files(root)
    else:
        result["patch"] = {"ok": True, "skipped": True}

    if args.mode in {"seed", "all"}:
        try:
            from app import create_app
            from app.services.performance.completion_phase3_visibility_scope import seed_phase3_visibility_center

            app = create_app()
            with app.app_context():
                result["seed"] = seed_phase3_visibility_center(commit=True)
        except Exception as exc:
            result["seed"] = {"ok": False, "error": str(exc)}
    else:
        result["seed"] = {"ok": True, "skipped": True}

    check_script = root / "scripts" / "performance" / "check_bys360_performance_completion_phase3_visibility_center.py"
    cmd = [sys.executable, str(check_script), "--project-root", str(root)]
    if args.mode in {"seed", "all"}:
        cmd.append("--app-check")
    proc = subprocess.run(cmd, text=True, capture_output=True)
    result["check_exit_code"] = proc.returncode
    result["check_stdout"] = proc.stdout
    result["check_stderr"] = proc.stderr
    result["ok"] = bool(result.get("patch", {}).get("ok")) and bool(result.get("seed", {}).get("ok")) and proc.returncode == 0

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["ok"]:
        print("BYS360_PERFORMANCE_COMPLETION_PHASE3_VISIBILITY_CENTER_APPLY_OK")
        return 0
    print("BYS360_PERFORMANCE_COMPLETION_PHASE3_VISIBILITY_CENTER_APPLY_FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
