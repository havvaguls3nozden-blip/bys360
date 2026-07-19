from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_PHASE2_AUTH_SMOKE_GATE_V1"
REPORT_REL = Path("reports/architecture/BYS360_PHASE2_AUTH_SMOKE_GATE_V1_REPORT.json")


AUTH_SMOKE_CASES: list[dict[str, Any]] = [
    {
        "name": "mobile_login_empty_payload",
        "method": "POST",
        "path": "/api/mobile/auth/login",
        "json": {},
        "forbidden_statuses": {404, 405, 500},
    },
    {
        "name": "mobile_refresh_empty_payload",
        "method": "POST",
        "path": "/api/mobile/auth/refresh",
        "json": {},
        "forbidden_statuses": {404, 405, 500},
    },
    {
        "name": "mobile_me_without_token",
        "method": "GET",
        "path": "/api/mobile/me",
        "json": None,
        "forbidden_statuses": {404, 405, 500},
    },
]


def _call(client: Any, case: dict[str, Any]) -> dict[str, Any]:
    method = case["method"]
    path = case["path"]

    if method == "GET":
        response = client.get(path)
    elif method == "POST":
        response = client.post(path, json=case.get("json"))
    else:
        raise ValueError(f"Desteklenmeyen method: {method}")

    status_code = int(response.status_code)
    forbidden = sorted(case["forbidden_statuses"])

    return {
        "name": case["name"],
        "method": method,
        "path": path,
        "status_code": status_code,
        "forbidden_statuses": forbidden,
        "ok": status_code not in case["forbidden_statuses"],
    }


def run_checks(root: Path, write_report: bool = True) -> dict[str, Any]:
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("BYS360_TESTING", "1")

    from app import create_app

    app = create_app()
    client = app.test_client()

    responses = [_call(client, case) for case in AUTH_SMOKE_CASES]

    auth_smoke_ok = all(item["ok"] for item in responses)

    result = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "auth_smoke_ok": auth_smoke_ok,
        "responses": responses,
        "next_actions": [
            "Faz 2C'de gerçek test kullanıcısı ile başarılı login/refresh/me akışı fixture üzerinden genişletilebilir.",
            "Faz 2D'de rol bazlı mobil endpoint erişim matrisi test_client ile kalıcı hale getirilebilir.",
        ],
    }

    if write_report:
        report = root / REPORT_REL
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        result["report"] = str(report)

    return result


def main() -> int:
    root = Path.cwd()
    result = run_checks(root, write_report=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["auth_smoke_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
