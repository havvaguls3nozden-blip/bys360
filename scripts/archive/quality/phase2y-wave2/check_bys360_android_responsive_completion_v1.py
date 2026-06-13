from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PACKAGE = "BYS360_ANDROID_RESPONSIVE_COMPLETION_V1"
CSS_MARKER = "BYS360_ANDROID_RESPONSIVE_COMPLETION_V1_CSS"
JS_MARKER = "BYS360_ANDROID_RESPONSIVE_COMPLETION_V1_JS"


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    base = root / "app" / "templates" / "base.html"
    css = root / "app" / "static" / "css" / "bys360_android_responsive_completion_v1.css"
    js = root / "app" / "static" / "js" / "bys360_android_responsive_completion_v1.js"

    checks: dict[str, object] = {
        "base_exists": base.exists(),
        "css_exists": css.exists(),
        "js_exists": js.exists(),
    }

    base_text = base.read_text(encoding="utf-8", errors="replace") if base.exists() else ""
    css_text = css.read_text(encoding="utf-8", errors="replace") if css.exists() else ""
    js_text = js.read_text(encoding="utf-8", errors="replace") if js.exists() else ""

    compact_css = css_text.replace(" ", "")
    checks.update({
        "base_css_include": "bys360_android_responsive_completion_v1.css" in base_text and CSS_MARKER in base_text,
        "base_js_include": "bys360_android_responsive_completion_v1.js" in base_text and JS_MARKER in base_text,
        "css_marker": CSS_MARKER in css_text,
        "js_marker": JS_MARKER in js_text,
        "android_ua_detection": "/Android/i" in js_text and "bys360-android-responsive-v1" in js_text,
        "android_webview_detection": "bys360-android-webview-v1" in js_text and "wv" in js_text,
        "viewport_vh_fix": "--bys360-android-vh" in css_text and "visualViewport" in js_text,
        "mobile_table_cards": "bys360-android-mobile-card-table" in css_text and "data-bys-android-label" in js_text,
        "single_column_grids": "grid-template-columns:1fr" in compact_css,
        "overflow_guard": "overflow-x:hidden" in css_text and "bys360-android-overflow-managed" in css_text,
        "modal_form_support": ".modal" in css_text and ".form-grid" in css_text,
        "assistant_panel_support": "bys360-ai" in css_text and "assistant" in css_text,
    })

    advisories = []
    tpl_root = root / "app" / "templates"
    if tpl_root.exists():
        pattern = re.compile(r"(?:min-width|width)\s*:\s*(\d{3,4})px", re.I)
        for path in tpl_root.rglob("*.html"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            hits = []
            for m in pattern.finditer(text):
                try:
                    value = int(m.group(1))
                except ValueError:
                    continue
                if value >= 760:
                    line = text[:m.start()].count("\n") + 1
                    hits.append({"line": line, "value": value})
            if hits:
                advisories.append({"file": str(path.relative_to(root)), "hits": hits[:5]})
            if len(advisories) >= 25:
                break
    checks["fixed_width_advisory_count"] = len(advisories)
    checks["fixed_width_advisories_sample"] = advisories[:8]

    ok = all(bool(v) for k, v in checks.items() if not k.startswith("fixed_width_advis"))
    print(json.dumps({"package": PACKAGE, "ok": ok, "checks": checks}, ensure_ascii=False, indent=2))
    if ok:
        print(f"{PACKAGE}_OK")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
