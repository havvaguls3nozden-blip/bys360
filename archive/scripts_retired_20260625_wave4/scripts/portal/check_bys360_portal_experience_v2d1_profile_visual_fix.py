# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, py_compile
from pathlib import Path

PACKAGE = "BYS360_PORTAL_EXPERIENCE_V2D1_PROFILE_VISUAL_FIX"

REQUIRED_FILES = [
    "app/static/css/bys360_portal_experience_v2d1_profile_visual_fix.css",
]
PATCH_MARKERS = {
    "app/templates/portal/feed.html": [
        "BYS360_PORTAL_EXPERIENCE_V2D1_PROFILE_VISUAL_FIX_CSS",
        "portal-v2d1-profile-visual-fix",
        "bys360_portal_experience_v2d1_profile_visual_fix.css",
    ],
}
REQUIRED_CSS_TERMS = [
    ".portal-v2d1-profile-visual-fix .portal-v2d-profile-compact",
    "justify-items:center",
    "text-align:center",
    "portal-v2d-profile-info h2",
    "portal-v2d-avatar",
]
FORBIDDEN_VISIBLE_TERMS = [
    "visual fix",
    "görsel fix",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    findings = []

    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            findings.append({"type": "missing_file", "file": rel})

    for rel, markers in PATCH_MARKERS.items():
        path = root / rel
        if not path.exists():
            findings.append({"type": "missing_file", "file": rel})
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                findings.append({"type": "missing_marker", "file": rel, "marker": marker})

    css_path = root / "app/static/css/bys360_portal_experience_v2d1_profile_visual_fix.css"
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        for term in REQUIRED_CSS_TERMS:
            if term not in css:
                findings.append({"type": "missing_css_rule", "file": str(css_path.relative_to(root)), "term": term})

    # Kullanıcıya görünen şablonlarda geliştirme dili olmasın. CSS yorumları bu kontrole dahil edilmez.
    for rel in ["app/templates/portal/feed.html", "app/templates/portal/profile.html"]:
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for term in FORBIDDEN_VISIBLE_TERMS:
            if term in text:
                findings.append({"type": "forbidden_visible_term", "file": rel, "term": term})

    for rel in ["scripts/portal/check_bys360_portal_experience_v2d1_profile_visual_fix.py"]:
        path = root / rel
        if path.exists():
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as exc:
                findings.append({"type": "compile_error", "file": rel, "error": str(exc)})

    result = {"package": PACKAGE, "ok": not findings, "finding_count": len(findings), "findings": findings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
