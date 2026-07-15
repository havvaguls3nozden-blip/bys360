from __future__ import annotations

import json
import sys
from pathlib import Path

PACKAGE = "BYS360_ANDROID_RESPONSIVE_COMPLETION_V2"
CSS_MARKER = "BYS360_ANDROID_RESPONSIVE_COMPLETION_V2_CSS"
JS_MARKER = "BYS360_ANDROID_RESPONSIVE_COMPLETION_V2_JS"


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    base = root / "app" / "templates" / "base.html"
    css = root / "app" / "static" / "css" / "bys360_android_responsive_completion_v2.css"
    js = root / "app" / "static" / "js" / "bys360_android_responsive_completion_v2.js"
    base_text = base.read_text(encoding="utf-8", errors="replace") if base.exists() else ""
    css_text = css.read_text(encoding="utf-8", errors="replace") if css.exists() else ""
    js_text = js.read_text(encoding="utf-8", errors="replace") if js.exists() else ""
    checks = {
        "base_exists": base.exists(),
        "css_exists": css.exists(),
        "js_exists": js.exists(),
        "base_css_include": CSS_MARKER in base_text and "bys360_android_responsive_completion_v2.css" in base_text,
        "base_js_include": JS_MARKER in base_text and "bys360_android_responsive_completion_v2.js" in base_text,
        "css_marker": "BYS360_ANDROID_RESPONSIVE_COMPLETION_V2_CSS_BEGIN" in css_text,
        "js_marker": "BYS360_ANDROID_RESPONSIVE_COMPLETION_V2_JS_BEGIN" in js_text,
        "android_detection": "/Android/i" in js_text and "bys360-android-responsive-v2" in js_text,
        "webview_detection": "bys360-android-webview-v2" in js_text and "wv" in js_text,
        "classless_mobile_fallback": "JS sınıfı gelmeden" in css_text and "@media (max-width:760px)" in css_text,
        "viewport_vh_fix": "--bys360-android-v2-vh" in css_text and "visualViewport" in js_text,
        "wide_inline_scan": "fixWideInlineElements" in js_text and "[style*=\"min-width\"]" in css_text,
        "table_card_mode": "bys360-android-v2-card-table" in css_text and "data-bys360-android-v2-label" in js_text,
        "mutation_observer": "MutationObserver" in js_text,
        "forms_and_tabs": ".form-grid" in css_text and ".nav-tabs" in css_text,
        "sidebar_mobile": ".app-sidebar:not(.mobile-open)" in css_text,
        "assistant_panel_support": "data-ai-agent-panel" in css_text and "assistant" in css_text,
    }
    out = {"package": PACKAGE, "ok": all(bool(v) for v in checks.values()), "checks": checks}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if out["ok"]:
        print("BYS360_ANDROID_RESPONSIVE_COMPLETION_V2_OK")
        return 0
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
