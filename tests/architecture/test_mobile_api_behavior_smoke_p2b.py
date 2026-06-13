from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "auth.py": [("POST", "/auth/login"), ("POST", "/auth/refresh"), ("GET", "/me")],
    "dashboard.py": [("GET", "/dashboard/summary")],
    "notifications.py": [("POST", "/notifications/<int:notification_id>/read"), ("POST", "/notifications/read-all")],
    "personnel_read.py": [("GET", "/personnel/list")],
    "personnel_write_all.py": [("GET", "/personnel/all"), ("POST", "/personnel/create"), ("POST", "/personnel/add")],
    "kpi_target_management.py": [("GET", "/kpi/target-management"), ("POST", "/kpi/target-management"), ("POST", "/kpi/target-management/<int:target_id>/progress")],
    "communication_v1_write.py": [("GET", "/communication/messages/threads/<int:thread_id>"), ("POST", "/communication/messages/threads/<int:thread_id>/send"), ("POST", "/communication/messages/create-thread")],
    "communication_v2_write.py": [("GET", "/communication/v2/threads/<int:thread_id>"), ("POST", "/communication/v2/threads/<int:thread_id>/send"), ("GET", "/communication/v2/users"), ("POST", "/communication/v2/create-thread")],
    "support_survey_write.py": [("POST", "/support/tickets"), ("POST", "/support/tickets/<int:ticket_id>/reply"), ("POST", "/surveys/<int:survey_id>/submit")],
    "assistant_chat.py": [("POST", "/assistant/v2/ask")],
}
DECORATOR_RE = re.compile(r"@mobile_api_bp\.(get|post|put|patch|delete)\(\s*(['\"])(.*?)\2")

def extract(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = DECORATOR_RE.search(line)
        if m:
            rows.append((m.group(1).upper(), m.group(3), str(path.relative_to(ROOT)).replace("\\", "/")))
    return rows

def test_mobile_domain_files_exist_and_compile():
    base = ROOT / "app" / "api" / "mobile" / "domains"
    assert base.exists()
    for filename in EXPECTED:
        path = base / filename
        assert path.exists(), filename
        ast.parse(path.read_text(encoding="utf-8"))

def test_mobile_route_contract_and_domain_ownership():
    base = ROOT / "app" / "api" / "mobile" / "domains"
    routes = []
    for filename in EXPECTED:
        routes.extend(extract(base / filename))
    assert len(routes) == 24
    assert len(set((m, r) for m, r, _ in routes)) == 24
    found = {(m, r): file for m, r, file in routes}
    for filename, pairs in EXPECTED.items():
        expected_file = f"app/api/mobile/domains/{filename}"
        for method, rule in pairs:
            assert (method, rule) in found, (method, rule)
            assert found[(method, rule)] == expected_file

def test_mobile_routes_py_is_facade_only():
    routes_py = ROOT / "app" / "api" / "mobile" / "routes.py"
    assert routes_py.exists()
    assert len(routes_py.read_text(encoding="utf-8", errors="replace").splitlines()) <= 300
    assert extract(routes_py) == []
