
from pathlib import Path
import sys

REQUIRED_CSS = [
    "BYS360_PORTAL_IPHONE_RESPONSIVE_V2_11_BEGIN",
    "@supports (-webkit-touch-callout: none)",
    "env(safe-area-inset-left)",
    "font-size: 16px",
    ".portal-video-frame",
    ".portal-tabs::-webkit-scrollbar",
]

FORBIDDEN_PEOPLE = [
    "main.portal_profile_me",
]


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    errors = []
    css = root / "app/static/css/bys360_portal.css"
    if not css.exists():
        errors.append("bys360_portal.css bulunamadı")
    else:
        text = css.read_text(encoding="utf-8", errors="ignore")
        for marker in REQUIRED_CSS:
            if marker not in text:
                errors.append(f"CSS içinde eksik iPhone responsive izi: {marker}")
    people = root / "app/templates/portal/people.html"
    if people.exists():
        ptext = people.read_text(encoding="utf-8", errors="ignore")
        for bad in FORBIDDEN_PEOPLE:
            if bad in ptext:
                errors.append(f"people.html içinde eski endpoint kaldı: {bad}")
    template_names = ["feed.html", "profile.html", "groups.html", "people.html"]
    for name in template_names:
        p = root / "app/templates/portal" / name
        if p.exists():
            t = p.read_text(encoding="utf-8", errors="ignore")
            if "bys360_portal.css" not in t:
                errors.append(f"{name} içinde portal CSS bağlantısı yok")
    if errors:
        print("BYS360_PORTAL_IPHONE_RESPONSIVE_V2_11_GATE_FAIL")
        for e in errors:
            print(" - " + e)
        return 1
    print("BYS360_PORTAL_IPHONE_RESPONSIVE_V2_11_GATE_OK")
    print("BYS360_PORTAL_IPHONE_RESPONSIVE_V2_11_QUALITY_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
