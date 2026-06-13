from __future__ import annotations

import pytest


@pytest.mark.parametrize("path", [
    "/feedback",
    "/feedback/pulse",
    "/feedback/pulse/history",
    "/feedback/pulse/analytics",
    "/feedback/admin/pulse-analytics",
    "/feedback/campaigns",
    "/feedback/results",
])
def test_feedback_routes_exist_and_do_not_500(client, path):
    response = client.get(path)
    assert response.status_code in {200, 302, 401, 403}, f"{path} beklenmeyen durum: {response.status_code}"
    assert response.status_code < 500
    assert response.status_code != 404
