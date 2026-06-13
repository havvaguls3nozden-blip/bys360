from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

VERSION = "V2.17.8"
SLUG = "bys360_mobile_auth_service_delegate_p1_3_v2_17_8"
START_MARK = "# BYS360_P1_3_AUTH_SERVICE_DELEGATE_START"
END_MARK = "# BYS360_P1_3_AUTH_SERVICE_DELEGATE_END"
IMPORT_LINE = "from app.api.mobile.services.auth_service import mobile_login_response, mobile_refresh_response, mobile_me_response"

SERVICE_BLOCK = r'''# BYS360_P1_3_AUTH_SERVICE_DELEGATE_START
from __future__ import annotations

from typing import Any, Callable

from flask import jsonify, request
from sqlalchemy import or_

from app.models import User


def _user_payload(user: User, full_name: Callable[[Any], str]) -> dict[str, Any]:
    return {
        "id": getattr(user, "id", None),
        "full_name": full_name(user),
        "sicil_no": getattr(user, "sicil_no", "") or "",
        "role": getattr(user, "role_label", None) or getattr(user, "role", "") or "",
        "unit": getattr(user, "birim", None) or getattr(user, "ust_birim", "") or "",
    }


def mobile_login_response(
    issue_token: Callable[[User], str],
    issue_refresh_token: Callable[[User], str],
    full_name: Callable[[Any], str],
):
    """Mobil giriş yanıtını üretir; route URL/endpoint değişmeden servis delegasyonu sağlar."""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"message": "Kullanıcı adı/sicil ve şifre zorunludur."}), 400

    user = User.query.filter(or_(User.sicil_no == username, User.email == username)).first()
    if not user or not user.check_password(password) or not getattr(user, "is_active", True):
        return jsonify({"message": "Kullanıcı adı/sicil veya şifre hatalı."}), 401

    return jsonify({
        "access_token": issue_token(user),
        "refresh_token": issue_refresh_token(user),
        "token_type": "Bearer",
        "user": _user_payload(user, full_name),
    })


def mobile_refresh_response(
    refresh_token: str | None,
    load_refresh_token_user: Callable[[str | None], User | None],
    issue_token: Callable[[User], str],
    issue_refresh_token: Callable[[User], str],
    full_name: Callable[[Any], str],
):
    """Mobil token yenileme yanıtını üretir."""
    user = load_refresh_token_user(refresh_token)
    if not user:
        return jsonify({"message": "Mobil oturum yenilenemedi. Lütfen tekrar giriş yapın."}), 401
    return jsonify({
        "access_token": issue_token(user),
        "refresh_token": issue_refresh_token(user),
        "token_type": "Bearer",
        "user": _user_payload(user, full_name),
    })


def mobile_me_response(
    user: User,
    module_payload: Callable[..., Any],
    metric: Callable[..., dict[str, Any]],
    item: Callable[..., dict[str, Any]],
    full_name: Callable[[Any], str],
):
    """Mevcut /me formatını koruyarak profil özetini servis katmanından üretir."""
    return module_payload(
        metrics=[
            metric("Oturum", "Aktif", "Gerçek mobil API token", "red", "verified_user"),
            metric("Rol", getattr(user, "role_label", None) or getattr(user, "role", "-"), "Yetki kontrollü erişim", "red", "badge"),
            metric("Sicil", getattr(user, "sicil_no", "-"), "Kurum içi kullanıcı kimliği", "red", "person"),
        ],
        items=[
            item(
                getattr(user, "id", ""),
                full_name(user),
                getattr(user, "birim", "") or getattr(user, "ust_birim", ""),
                "Aktif",
                getattr(user, "role_label", None) or getattr(user, "role", ""),
                getattr(user, "sicil_no", ""),
                100,
            )
        ],
    )
# BYS360_P1_3_AUTH_SERVICE_DELEGATE_END
'''


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def backup(path: Path, root: Path, label: str) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rel = path.relative_to(root)
    dest = root / "_local_quarantine" / f"{SLUG}_{stamp}" / str(rel)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    return dest


def syntax_ok(path: Path) -> tuple[bool, str]:
    try:
        ast.parse(read_text(path), filename=str(path))
        return True, ""
    except SyntaxError as exc:
        return False, f"{exc.__class__.__name__}: {exc}"


def ensure_service_block(service_path: Path, root: Path, apply: bool) -> dict[str, Any]:
    info: dict[str, Any] = {"path": str(service_path.relative_to(root)), "exists_before": service_path.exists(), "changed": False}
    existing = read_text(service_path) if service_path.exists() else ""
    if START_MARK in existing and END_MARK in existing:
        new_text = re.sub(
            re.escape(START_MARK) + r".*?" + re.escape(END_MARK),
            SERVICE_BLOCK.strip(),
            existing,
            flags=re.S,
        )
    else:
        sep = "\n\n" if existing.strip() else ""
        new_text = existing.rstrip() + sep + SERVICE_BLOCK.strip() + "\n"
    info["changed"] = new_text != existing
    if apply and info["changed"]:
        backup(service_path, root, "auth_service_before")
        write_text(service_path, new_text)
    ok, err = syntax_ok(service_path) if (apply or service_path.exists()) else (True, "")
    info["syntax_ok_after"] = ok
    info["syntax_error"] = err
    return info


def ensure_import(routes_text: str) -> tuple[str, bool]:
    if IMPORT_LINE in routes_text:
        return routes_text, False
    marker = "from . import mobile_api_bp"
    if marker in routes_text:
        return routes_text.replace(marker, marker + "\n" + IMPORT_LINE, 1), True
    # Safe fallback: place after imports block.
    return IMPORT_LINE + "\n" + routes_text, True


def replace_block(text: str, start_regex: str, end_regex: str, body: str, name: str) -> tuple[str, bool, str]:
    pattern = re.compile(r"(" + start_regex + r"\n)(.*?)(?=\n\n" + end_regex + r")", re.S)
    match = pattern.search(text)
    if not match:
        return text, False, f"{name}: blok bulunamadi"
    new = match.group(1) + body.rstrip() + "\n"
    return text[:match.start()] + new + text[match.end():], (match.group(0) != new), ""


def delegate_routes(routes_path: Path, root: Path, apply: bool) -> dict[str, Any]:
    info: dict[str, Any] = {"path": str(routes_path.relative_to(root)), "changed": False, "errors": []}
    text = read_text(routes_path)
    before = text
    text, import_changed = ensure_import(text)
    info["import_added"] = import_changed

    login_body = '    return mobile_login_response(_issue_token, _issue_refresh_token, _full_name)\n'
    refresh_body = '''    data = request.get_json(silent=True) or {}
    refresh_token = data.get("refresh_token") or data.get("refreshToken")
    return mobile_refresh_response(refresh_token, _load_refresh_token_user, _issue_token, _issue_refresh_token, _full_name)
'''
    me_body = '    return mobile_me_response(user, _module_payload, _metric, _item, _full_name)\n'

    text, changed, err = replace_block(
        text,
        r'@mobile_api_bp\.post\("/auth/login"\)\s*def mobile_login\(\):',
        r'@mobile_api_bp\.post\("/auth/refresh"\)',
        login_body,
        "mobile_login",
    )
    info["mobile_login_delegated"] = changed
    if err:
        info["errors"].append(err)

    text, changed, err = replace_block(
        text,
        r'@mobile_api_bp\.post\("/auth/refresh"\)\s*def mobile_refresh\(\):',
        r'@mobile_api_bp\.get\("/me"\)',
        refresh_body,
        "mobile_refresh",
    )
    info["mobile_refresh_delegated"] = changed
    if err:
        info["errors"].append(err)

    text, changed, err = replace_block(
        text,
        r'@mobile_api_bp\.get\("/me"\)\s*@require_mobile_user\s*def mobile_me\(user: User\):',
        r'@mobile_api_bp\.get\("/dashboard/summary"\)',
        me_body,
        "mobile_me",
    )
    info["mobile_me_delegated"] = changed
    if err:
        info["errors"].append(err)

    info["changed"] = text != before
    if apply and info["changed"]:
        backup(routes_path, root, "routes_before")
        write_text(routes_path, text)

    if apply:
        ok, err = syntax_ok(routes_path)
    else:
        try:
            ast.parse(text, filename=str(routes_path))
            ok, err = True, ""
        except SyntaxError as exc:
            ok, err = False, f"{exc.__class__.__name__}: {exc}"
    info["syntax_ok_after"] = ok
    info["syntax_error"] = err
    return info


def run_cmd(root: Path, args: list[str], timeout: int = 120) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        cp = subprocess.run(
            args,
            cwd=str(root),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=env,
        )
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout_tail": cp.stdout[-4000:],
            "stderr_tail": cp.stderr[-4000:],
        }
    except Exception as exc:
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": repr(exc)}


def health(root: Path) -> dict[str, Any]:
    compile_res = run_cmd(root, [sys.executable, "-m", "compileall", "app", "config.py", "scripts"], timeout=180)
    factory_res = run_cmd(root, [sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"], timeout=120)
    return {
        "compileall_ok": bool(compile_res.get("ok")),
        "app_factory_ok": bool(factory_res.get("ok")) and "BYS360_APP_CREATE_OK" in str(factory_res.get("stdout_tail", "")),
        "overall_ok": bool(compile_res.get("ok")) and bool(factory_res.get("ok")) and "BYS360_APP_CREATE_OK" in str(factory_res.get("stdout_tail", "")),
        "compileall": compile_res,
        "app_factory": factory_res,
    }


def count_route_lines(path: Path) -> dict[str, Any]:
    text = read_text(path) if path.exists() else ""
    funcs = re.findall(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", text, flags=re.M)
    return {"kb": round(len(text.encode("utf-8"))/1024, 1), "lines": text.count("\n") + 1 if text else 0, "function_count": len(funcs)}


def write_reports(root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / f"{SLUG}_report.json"
    md_path = report_dir / f"{SLUG}_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    routes_info = report.get("routes_after", {})
    service_info = report.get("service", {})
    health_info = report.get("health_summary", {})
    lines = [
        "# BYS360 Mobile Auth Service Delegate P1.3 V2.17.8",
        "",
        "Bu rapor mobil auth/profile uçları için servis delegasyonu sonucunu gösterir. URL, endpoint ve blueprint adı değiştirilmez.",
        "",
        "## Durum",
        f"- mode: {report.get('mode')}",
        f"- service_changed: {service_info.get('changed')}",
        f"- routes_changed: {report.get('routes', {}).get('changed')}",
        f"- routes_syntax_ok_after: {report.get('routes', {}).get('syntax_ok_after')}",
        f"- service_syntax_ok_after: {service_info.get('syntax_ok_after')}",
        "",
        "## Delegasyon",
        f"- mobile_login_delegated: {report.get('routes', {}).get('mobile_login_delegated')}",
        f"- mobile_refresh_delegated: {report.get('routes', {}).get('mobile_refresh_delegated')}",
        f"- mobile_me_delegated: {report.get('routes', {}).get('mobile_me_delegated')}",
        "",
        "## routes.py Son Durum",
        f"- KB: {routes_info.get('kb')}",
        f"- Satır: {routes_info.get('lines')}",
        f"- Fonksiyon: {routes_info.get('function_count')}",
        "",
        "## Sağlık Kontrolü",
        f"- compileall_ok: {health_info.get('compileall_ok')}",
        f"- app_factory_ok: {health_info.get('app_factory_ok')}",
        f"- overall_ok: {health_info.get('overall_ok')}",
        "",
        "## Not",
        "Bu adım küçük tutulmuştur. Bir sonraki güvenli adım dashboard/profile veya support helper delegasyonu olabilir.",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", choices=["audit", "apply", "all"], default="audit")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    routes_path = root / "app" / "api" / "mobile" / "routes.py"
    service_path = root / "app" / "api" / "mobile" / "services" / "auth_service.py"
    apply = args.mode in {"apply", "all"}

    report: dict[str, Any] = {"version": VERSION, "mode": args.mode, "project_root": str(root)}
    report["routes_before"] = count_route_lines(routes_path)
    report["service"] = ensure_service_block(service_path, root, apply=apply)
    report["routes"] = delegate_routes(routes_path, root, apply=apply)
    report["routes_after"] = count_route_lines(routes_path)
    if args.mode in {"all"}:
        report["health_summary"] = health(root)
    else:
        report["health_summary"] = {}

    json_path, md_path = write_reports(root, report)
    report["json_report"] = str(json_path.relative_to(root))
    report["md_report"] = str(md_path.relative_to(root))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_AUTH_SERVICE_DELEGATE_P1_3_V2_17_8_REPORT_OK")
    if args.mode == "all":
        if not report["health_summary"].get("overall_ok"):
            print("BYS360_MOBILE_AUTH_SERVICE_DELEGATE_P1_3_V2_17_8_HEALTH_FAIL")
            return 1
        print("BYS360_MOBILE_AUTH_SERVICE_DELEGATE_P1_3_V2_17_8_HEALTH_OK")
    if apply:
        if report.get("routes", {}).get("errors"):
            print("BYS360_MOBILE_AUTH_SERVICE_DELEGATE_P1_3_V2_17_8_APPLY_WITH_WARNINGS")
        else:
            print("BYS360_MOBILE_AUTH_SERVICE_DELEGATE_P1_3_V2_17_8_APPLY_OK")
    print("BYS360_MOBILE_AUTH_SERVICE_DELEGATE_P1_3_V2_17_8_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
