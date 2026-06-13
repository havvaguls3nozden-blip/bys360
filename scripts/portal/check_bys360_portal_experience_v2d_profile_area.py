# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, py_compile, re
from pathlib import Path

PACKAGE = "BYS360_PORTAL_EXPERIENCE_V2D_PROFILE_AREA"
REQUIRED_FILES = [
    "app/templates/portal/_profile_summary_card_v2d.html",
    "app/static/css/bys360_portal_experience_v2d_profile_area.css",
]
PATCH_MARKERS = {
    "app/templates/portal/feed.html": [
        "BYS360_PORTAL_EXPERIENCE_V2D_PROFILE_AREA_CSS",
        "portal-v2d-feed",
        "BYS360_PORTAL_EXPERIENCE_V2D_LEFT_PROFILE_CARD",
        "portal/_profile_summary_card_v2d.html",
    ],
    "app/templates/portal/profile.html": [
        "BYS360_PORTAL_EXPERIENCE_V2D_PROFILE_AREA_CSS",
        "portal-v2d-profile-page",
        "BYS360_PORTAL_EXPERIENCE_V2D_PROFILE_HERO",
        "portal/_profile_summary_card_v2d.html",
    ],
}
FORBIDDEN_VISIBLE_TERMS = [
    "deneyim katmanı",
    "geliştirme sürümü",
]


def strip_jinja_comments(text: str) -> str:
    return re.sub(r"\{#.*?#\}", "", text, flags=re.S)


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
            # Bazı eski/özel paketlerde profil sayfası bulunmayabilir; varsa kontrol edilir.
            if rel.endswith("profile.html"):
                continue
            findings.append({"type": "missing_patch_target", "file": rel})
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                findings.append({"type": "missing_marker", "file": rel, "marker": marker})
        visible_text = strip_jinja_comments(text)
        for term in FORBIDDEN_VISIBLE_TERMS:
            if term in visible_text:
                findings.append({"type": "forbidden_visible_term", "file": rel, "term": term})
    profile_partial = root / "app/templates/portal/_profile_summary_card_v2d.html"
    if profile_partial.exists():
        text = profile_partial.read_text(encoding="utf-8")
        for marker in ["Kurumsal Profil", "Profil bilgisi", "Tamamlanma", "Görünür Paylaşım"]:
            if marker not in text:
                findings.append({"type": "missing_profile_marker", "file": str(profile_partial), "marker": marker})
    try:
        py_compile.compile(str(root / "scripts/portal/check_bys360_portal_experience_v2d_profile_area.py"), doraise=True)
    except Exception as exc:
        findings.append({"type": "compile_error", "file": "scripts/portal/check_bys360_portal_experience_v2d_profile_area.py", "error": str(exc)})
    result = {"package": PACKAGE, "ok": not findings, "finding_count": len(findings), "findings": findings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
