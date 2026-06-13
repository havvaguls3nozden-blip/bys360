# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    base = root / "app" / "templates" / "base.html"
    css = root / "app" / "static" / "css" / "bys360_ai_everywhere_v1.css"
    js = root / "app" / "static" / "js" / "bys360_ai_everywhere_v1.js"
    result = {
        "package": "BYS360_AI_EVERYWHERE_V1",
        "ok": True,
        "checks": {},
    }
    for label, path in [("base", base), ("css", css), ("js", js)]:
        exists = path.exists()
        result["checks"][f"{label}_exists"] = exists
        result["ok"] = result["ok"] and exists
    base_text = base.read_text(encoding="utf-8") if base.exists() else ""
    js_text = js.read_text(encoding="utf-8") if js.exists() else ""
    required = [
        "BYS360_AI_EVERYWHERE_V1_CSS",
        "BYS360_AI_EVERYWHERE_V1_JS",
        "performance-category-card",
        "performance-category-scope",
        "performance-category-period",
        "performance-category-integration",
        "performance-period-center",
        "performance-approvals",
        "performance-notes-guidance",
        "personnel",
        "communication",
        "settings",
        "ai-decision",
        "assistant",
        "kpi",
        "dashboard",
    ]
    for marker in required:
        found = marker in base_text or marker in js_text
        result["checks"][marker] = found
        result["ok"] = result["ok"] and found
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
