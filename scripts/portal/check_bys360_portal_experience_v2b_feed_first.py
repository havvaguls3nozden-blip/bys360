# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, py_compile
from pathlib import Path

PACKAGE = "BYS360_PORTAL_EXPERIENCE_V2B_FEED_FIRST"
REQUIRED_FILES = [
    "app/templates/portal/_feed_sidebar_v2b.html",
    "app/static/css/bys360_portal_experience_v2b_feed_first.css",
]
PATCH_MARKERS = {
    "app/templates/portal/feed.html": [
        "BYS360_PORTAL_EXPERIENCE_V2B_FEED_FIRST_CSS",
        "portal-layout-feed-first",
        "portal/_feed_sidebar_v2b.html",
    ],
}
FORBIDDEN_TOP_MARKERS = [
    "BYS360_PORTAL_EXPERIENCE_V2_FEED_INCLUDE",
    "BYS360_PORTAL_EXPERIENCE_V1_FEED_INCLUDE",
]

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    findings = []
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            findings.append({"type":"missing_file", "file":rel})
    for rel, markers in PATCH_MARKERS.items():
        path = root / rel
        if not path.exists():
            findings.append({"type":"missing_patch_target", "file":rel}); continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                findings.append({"type":"missing_marker", "file":rel, "marker":marker})
        # Sadece akış üstündeki eski büyük include markerlarının temizlendiğini kontrol eder.
        before_layout = text.split('<div class="portal-layout', 1)[0]
        for marker in FORBIDDEN_TOP_MARKERS:
            if marker in before_layout:
                findings.append({"type":"feed_top_still_crowded", "file":rel, "marker":marker})
    try:
        py_compile.compile(str(root / "scripts/portal/check_bys360_portal_experience_v2b_feed_first.py"), doraise=True)
    except Exception as exc:
        findings.append({"type":"compile_error", "file":"scripts/portal/check_bys360_portal_experience_v2b_feed_first.py", "error":str(exc)})
    result = {"package": PACKAGE, "ok": not findings, "finding_count": len(findings), "findings": findings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
