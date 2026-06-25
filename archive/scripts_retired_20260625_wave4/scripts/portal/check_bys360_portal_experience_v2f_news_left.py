# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, py_compile
from pathlib import Path

PACKAGE = "BYS360_PORTAL_EXPERIENCE_V2F_NEWS_SHOWCASE_LEFT"

REQUIRED = {
    "app/templates/portal/_left_news_showcase_v2f.html": ["Duyurular ve İç Haberler", "BYS360_PORTAL_EXPERIENCE_V2F_LEFT_NEWS_SHOWCASE_TEMPLATE"],
    "app/static/css/bys360_portal_experience_v2f_news_left.css": ["BYS360_PORTAL_EXPERIENCE_V2F_NEWS_LEFT"],
    "app/templates/portal/feed.html": ["BYS360_PORTAL_EXPERIENCE_V2F_LEFT_NEWS_SHOWCASE", "BYS360_PORTAL_EXPERIENCE_V2F_NEWS_LEFT_CSS"],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    findings = []
    for rel, needles in REQUIRED.items():
        path = root / rel
        if not path.exists():
            findings.append({"type": "missing_file", "file": rel})
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in needles:
            if needle not in text:
                findings.append({"type": "missing_marker", "file": rel, "marker": needle})
    sidebar = root / "app/templates/portal/_feed_sidebar_v2b.html"
    if sidebar.exists():
        stext = sidebar.read_text(encoding="utf-8", errors="ignore")
        if "Öne Çıkan Duyurular" in stext and "portal-v2f-right-news-legacy" not in stext:
            findings.append({"type": "right_sidebar_news_not_moved", "file": str(sidebar)})
    for rel in ["scripts/portal/check_bys360_portal_experience_v2f_news_left.py"]:
        path = root / rel
        if path.exists():
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as exc:
                findings.append({"type": "compile_error", "file": rel, "error": str(exc)})
    result = {"package": PACKAGE, "ok": not findings, "finding_count": len(findings), "findings": findings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
