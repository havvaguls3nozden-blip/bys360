# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, py_compile, re
from pathlib import Path

PACKAGE = "BYS360_PORTAL_EXPERIENCE_V2C_POST_CARDS"
REQUIRED_FILES = [
    "app/static/css/bys360_portal_experience_v2c_post_cards.css",
]
PATCH_MARKERS = {
    "app/templates/portal/feed.html": [
        "BYS360_PORTAL_EXPERIENCE_V2C_POST_CARDS_CSS",
        "portal-v2c-feed",
    ],
    "app/templates/portal/_composer.html": [
        "portal-v2c-composer",
        "BYS360_PORTAL_EXPERIENCE_V2C_COMPOSER_CHIPS",
        "Ne paylaşmak istersiniz?",
    ],
    "app/templates/portal/_post_card.html": [
        "portal-v2c-post-card",
        "Yorum yazın; kişi etiketlemek için @ kullanabilirsiniz",
    ],
}
FORBIDDEN_VISIBLE_TERMS = [
    "deneyim katmanı",
    "Portal V2",
    "Kurumsal Portal V2",
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
    try:
        py_compile.compile(str(root / "scripts/portal/check_bys360_portal_experience_v2c_post_cards.py"), doraise=True)
    except Exception as exc:
        findings.append({"type": "compile_error", "file": "scripts/portal/check_bys360_portal_experience_v2c_post_cards.py", "error": str(exc)})
    result = {"package": PACKAGE, "ok": not findings, "finding_count": len(findings), "findings": findings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
