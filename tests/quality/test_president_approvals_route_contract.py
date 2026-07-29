"""Phase 12A — Başkan Onayları (President Approvals) route sözleşmesi.

Bu dosya `/performans/baskan-onaylari`, `/performance/president-approvals` ve
`/workflow/president-approvals` ailesindeki route'ların GERÇEK runtime davranışını
kilitler. Hiçbir route kaydı DEĞİŞTİRİLMEDİ — bu testler yalnızca mevcut, doğrulanmış
davranışı sabitler ve gelecekte bir import-sırası refactor'ünün handler'ı sessizce
değiştirmesini (silent flip) CI'da yakalar.

Önemli düzeltme (Phase 12A koordinatör + 3 ajan bağımsız doğrulaması):
`/workflow/president-approvals` başlangıç hipotezinde "aktif legacy akış" olarak
anılmıştı. Bu YANLIŞTIR: `app/workflow/routes.py` hiçbir yerden import edilmiyor,
dolayısıyla bu route runtime'da hiç kayıtlı değil (bkz. test_workflow_president_
approvals_confirmed_dead_at_runtime). Bu dosyadaki testler VARSAYIMI değil,
KANITLANMIŞ GERÇEK DURUMU kilitler.

Hiçbir gerçek POST/onayla/iade/sil çalıştırılmaz; POST testleri yalnızca Werkzeug
matcher (`url_map.bind().match()`) seviyesindedir, handler invoke edilmez.

Not (dead-route testi izolasyonu): `app.workflow.routes`'daki `@main_bp.route(...)`
decorator'ları IMPORT anında çalışır ve paylaşılan `main_bp` Blueprint nesnesine
kalıcı olarak yazılır. `tests/workflow/test_phase5w_workflow_schema_readiness.py`
bu modülü izole birim testi amacıyla doğrudan import ediyor; tam test paketi
içinde bu import session-scope `app` fixture'ından ÖNCE tetiklenirse, sonraki
`create_app()` çağrıları da (aynı process içinde modül zaten cache'lendiği için)
kirlenmiş `main_bp`'yi görür. Bu, ürünün kendisinde bir hata DEĞİL, yalnızca test
suite'inin aynı process'i paylaşmasından kaynaklanan bir gözlem artefaktıdır.
Bu yüzden `test_workflow_president_approvals_confirmed_dead_at_runtime` bilerek
TAMAMEN İZOLE bir alt-process'te `create_app()` çalıştırır (3 ajanın da yaptığı
gibi) — session `app` fixture'ına güvenmez.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.ci_safe

# Bildirim / AI-asistan katmanında hardcoded (url_for değil, düz string) kullanılan
# iki farklı deep-link URL'i (Phase 12A Agent 2/3 grep taraması, 2026-07-29):
#   app/services/performance/process_engine_phase5_notifications.py:575
#   app/services/performance/process_engine_phase6_president_approvals.py:142
#   app/services/performance/president_menu_card_access.py:220
#   app/services/performance/process_engine_phase7_president_rule.py:507
#   app/services/ai_agent/assistant_project_master_knowledge_v3.py:276
#   app/services/ai_agent/performance_bridge.py:174, action_queue_bridge.py:30, +18 diğer
DEEP_LINK_URLS = ["/performans/baskan-onaylari", "/performance/president-approvals"]


@pytest.fixture(autouse=True)
def _isolated_login_and_csrf(app):
    original_login_disabled = app.config.get("LOGIN_DISABLED")
    original_csrf = app.config.get("WTF_CSRF_ENABLED")
    app.config["LOGIN_DISABLED"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    yield
    if original_login_disabled is None:
        app.config.pop("LOGIN_DISABLED", None)
    else:
        app.config["LOGIN_DISABLED"] = original_login_disabled
    if original_csrf is None:
        app.config.pop("WTF_CSRF_ENABLED", None)
    else:
        app.config["WTF_CSRF_ENABLED"] = original_csrf


def _adapter(app):
    return app.url_map.bind("localhost", url_scheme="http")


def test_workflow_president_approvals_confirmed_dead_at_runtime():
    repo_root = Path(__file__).resolve().parents[2]
    probe_script = (
        "from app import create_app\n"
        "app = create_app()\n"
        "endpoints = {r.endpoint for r in app.url_map.iter_rules()}\n"
        "print('workflow_endpoint_present=%s' % ('main.workflow_president_approvals' in endpoints))\n"
        "print('workflow_decide_present=%s' % ('main.workflow_president_decide' in endpoints))\n"
        "adapter = app.url_map.bind('localhost', url_scheme='http')\n"
        "try:\n"
        "    adapter.match('/workflow/president-approvals', method='GET')\n"
        "    print('match_result=FOUND')\n"
        "except Exception as exc:\n"
        "    print('match_result=%s' % type(exc).__name__)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe_script],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, {"stdout": result.stdout, "stderr": result.stderr}
    output_lines = result.stdout.strip().splitlines()
    assert "workflow_endpoint_present=False" in output_lines, result.stdout
    assert "workflow_decide_present=False" in output_lines, result.stdout
    assert "match_result=NotFound" in output_lines, result.stdout


def test_base_list_url_variants_resolve_to_winning_endpoint(app):
    adapter = _adapter(app)
    for path in ("/performans/baskan-onaylari", "/performance/president-approvals"):
        endpoint, _args = adapter.match(path, method="GET")
        assert endpoint == "main.performance_president_approvals"


def test_karne_scorecard_url_variants_resolve_to_expected_endpoints(app):
    adapter = _adapter(app)

    endpoint, _args = adapter.match("/performans/baskan-onaylari/1/karne", method="GET")
    assert endpoint == "main.performance_president_approval_scorecard"

    endpoint, _args = adapter.match("/performance/president-approvals/1/scorecard", method="GET")
    assert endpoint == "main.performance_president_approval_scorecard"

    # Bu alias çakışmasız kaldı (main.performance_president_card_review'ın 3 alias'ından
    # tek canlısı) — hâlâ 70-altı skor gate'ini içeren "zengin" handler'a gidiyor.
    endpoint, _args = adapter.match("/performance/president-approvals/1/card", method="GET")
    assert endpoint == "main.performance_president_card_review"


def test_post_decision_endpoints_resolve_without_ambiguity(app):
    adapter = _adapter(app)
    pairs = [
        ("/performans/baskan-onaylari/1/onayla", "/performance/president-approvals/1/approve", "main.performance_president_approval_approve"),
        ("/performans/baskan-onaylari/1/iade", "/performance/president-approvals/1/return", "main.performance_president_approval_return"),
        ("/performans/baskan-onaylari/1/sil", "/performance/president-approvals/1/delete", "main.performance_president_approval_delete"),
    ]
    for tr_path, en_path, expected_endpoint in pairs:
        tr_endpoint, _args = adapter.match(tr_path, method="POST")
        en_endpoint, _args = adapter.match(en_path, method="POST")
        assert tr_endpoint == expected_endpoint
        assert en_endpoint == expected_endpoint


def test_unauthorized_user_receives_backend_403_not_just_hidden_menu(client, monkeypatch):
    import app.performance.president_approval_card_routes as scorecard_routes
    import app.performance.process_engine_phase6_president_approvals_routes as list_routes

    monkeypatch.setattr(list_routes, "can_view_president_approvals", lambda user: False)
    monkeypatch.setattr(scorecard_routes, "can_view_president_approvals", lambda user: False)

    list_response = client.get("/performance/president-approvals")
    assert list_response.status_code == 403

    scorecard_response = client.get("/performance/president-approvals/1/scorecard")
    assert scorecard_response.status_code == 403


def test_hardcoded_deep_link_urls_resolve_without_404(client):
    for url in DEEP_LINK_URLS:
        response = client.get(url)
        assert response.status_code != 404, f"{url} 404 üretti — deep-link kırık"


def test_url_for_stability_for_winning_endpoints(app):
    with app.test_request_context():
        from flask import url_for

        list_url = url_for("main.performance_president_approvals")
        assert list_url in ("/performans/baskan-onaylari", "/performance/president-approvals")

        scorecard_url = url_for("main.performance_president_approval_scorecard", approval_id=1)
        assert scorecard_url in (
            "/performans/baskan-onaylari/1/karne",
            "/performance/president-approvals/1/scorecard",
        )

        card_review_url = url_for("main.performance_president_card_review", approval_id=1)
        assert card_review_url in (
            "/performance/president-approvals/1/card",
            "/performans/baskan-onaylari/1/karne",
            "/performance/president-approvals/1/scorecard",
        )
