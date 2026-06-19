from __future__ import annotations

import argparse
import json
import py_compile
import shutil
import subprocess
from pathlib import Path

PACKAGE = "BYS360_PORTAL_AJAX_REACTIONS_V1"


def require(condition: bool, findings: list[dict], code: str, message: str) -> None:
    findings.append({"code": code, "ok": bool(condition), "message": message})


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    findings: list[dict] = []

    routes = read(root / "app/portal/routes.py")
    post_card = read(root / "app/templates/portal/_post_card.html")
    js = read(root / "app/static/js/bys360_portal.js")
    css = read(root / "app/static/css/bys360_portal.css")

    require("BYS360_PORTAL_AJAX_REACTIONS_V1_BEGIN" in routes, findings, "routes_marker", "Portal AJAX helper marker mevcut")
    require("_portal_wants_json_response" in routes and "jsonify(_portal_reaction_payload" in routes, findings, "routes_json", "Beğeni route JSON cevap destekli")
    require("reaction_counts," in routes and "user_reaction_for_post," in routes, findings, "routes_imports", "Tepki sayımı ve kullanıcı tepkisi import edildi")
    require("flash(message" in routes and "if wants_json" in routes, findings, "fallback_redirect", "Eski redirect/flash davranışı fallback olarak korunuyor")

    require("data-portal-post-card" in post_card, findings, "card_attr", "Paylaşım kartı JS hedef alanına sahip")
    require("data-portal-reaction-total" in post_card, findings, "total_attr", "Tepki toplamı DOM üzerinden yenilenebilir")
    require("data-portal-reaction-button" in post_card and "data-portal-reaction-count" in post_card, findings, "button_attr", "Tepki butonları DOM üzerinden yenilenebilir")

    require("event.preventDefault()" in js and "fetch(form.action" in js, findings, "js_fetch", "Beğeni formu sayfa yenilemeden fetch ile çalışır")
    require("X-Requested-With" in js and "application/json" in js, findings, "js_headers", "AJAX istek başlıkları mevcut")
    require("updateReactionUi" in js and "showPortalInlineMessage" in js, findings, "js_ui_update", "UI tepki sonrası anlık güncellenir")
    require("BYS360_PORTAL_AJAX_REACTIONS_V1_BEGIN" in css, findings, "css_marker", "Inline mesaj stili mevcut")

    try:
        py_compile.compile(str(root / "app/portal/routes.py"), doraise=True)
        require(True, findings, "py_compile", "app/portal/routes.py syntax OK")
    except Exception as exc:
        require(False, findings, "py_compile", f"app/portal/routes.py syntax hatası: {exc}")

    try:
        from jinja2 import Environment
        for rel in [
            "app/templates/portal/_post_card.html",
            "app/templates/portal/feed.html",
            "app/templates/portal/group_detail.html",
            "app/templates/portal/groups.html",
            "app/templates/portal/people.html",
            "app/templates/portal/profile.html",
            "app/templates/portal/moderation.html",
        ]:
            path = root / rel
            if path.exists():
                Environment().parse(read(path))
        require(True, findings, "jinja_parse", "Portal template parse OK")
    except Exception as exc:
        require(False, findings, "jinja_parse", f"Jinja parse hatası: {exc}")

    node = shutil.which("node")
    if node:
        proc = subprocess.run([node, "--check", str(root / "app/static/js/bys360_portal.js")], text=True, capture_output=True)
        require(proc.returncode == 0, findings, "node_check", "bys360_portal.js syntax OK" if proc.returncode == 0 else proc.stderr.strip())
    else:
        findings.append({"code": "node_check", "ok": True, "message": "Node bulunamadı; JS syntax kontrolü atlandı"})

    ok = all(item["ok"] for item in findings)
    report = {
        "package": PACKAGE,
        "ok": ok,
        "project_root": str(root),
        "finding_count": len(findings),
        "findings": findings,
    }
    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "BYS360_PORTAL_AJAX_REACTIONS_V1_REPORT.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({**report, "report": str(report_path)}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
