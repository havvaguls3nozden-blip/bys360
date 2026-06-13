from __future__ import annotations

import argparse
import py_compile
from pathlib import Path

VERSION = "BYS360_GERI_BILDIRIM_MERKEZI_V2_13_0"


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{VERSION} kontrol scripti")
    parser.add_argument("--project-root", default=".", help="BYS360 proje kökü")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    files = [
        root / "app" / "communication" / "user_feedback_routes.py",
        root / "app" / "templates" / "feedback" / "quick_feedback.html",
        root / "app" / "templates" / "feedback" / "quick_feedback_success.html",
        root / "app" / "routes.py",
        root / "app" / "templates" / "feedback" / "dashboard.html",
    ]
    missing = [str(path) for path in files if not path.exists()]
    if missing:
        raise SystemExit("Eksik dosya var:\n" + "\n".join(missing))

    py_compile.compile(str(root / "app" / "communication" / "user_feedback_routes.py"), doraise=True)
    routes_text = (root / "app" / "routes.py").read_text(encoding="utf-8", errors="replace")
    dash_text = (root / "app" / "templates" / "feedback" / "dashboard.html").read_text(encoding="utf-8", errors="replace")
    quick_text = (root / "app" / "templates" / "feedback" / "quick_feedback.html").read_text(encoding="utf-8", errors="replace")
    route_text = (root / "app" / "communication" / "user_feedback_routes.py").read_text(encoding="utf-8", errors="replace")

    checks = {
        "route_import": "user_feedback_routes" in routes_text,
        "dashboard_button": "main.bys360_feedback_new" in dash_text,
        "quick_route_url": "/feedback/gonder" in route_text,
        "feedback_categories": "Ekran Hatası" in route_text and "Tebrik" in route_text and "Teşekkür" in route_text,
        "no_debug_terms": not any(term in quick_text.lower() for term in ["debug", "traceback", "exception", "phase sync"]),
    }
    failed = [key for key, ok in checks.items() if not ok]
    if failed:
        raise SystemExit("Başarısız kontroller: " + ", ".join(failed))

    print(f"{VERSION}_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
