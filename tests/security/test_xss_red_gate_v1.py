from __future__ import annotations

from pathlib import Path

from flask import Flask, request


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_portal_post_body_template_escapes_html() -> None:
    text = _read("app/templates/portal/_post_card.html")
    assert "post.body|replace" not in text
    assert "post.body|safe" not in text
    assert "white-space: pre-wrap" in text
    assert "{{ post.body }}" in text


def test_unsafe_template_safes_removed_or_filtered() -> None:
    assert "{{ attrs|safe }}" not in _read("app/templates/base.html")
    assert "attrs|safe_nav_attrs" in _read("app/templates/base.html")
    assert "{{ attachment.stored_path|safe }}" not in _read("app/templates/portal/_post_card.html")
    assert "attachment.stored_path|safe_social_embed" in _read("app/templates/portal/_post_card.html")
    assert "problems|join('<br>')|safe" not in _read("app/templates/corporate_information_center/overview.html")


def test_safe_social_embed_removes_script_and_javascript_url() -> None:
    from app.security.html_sanitizer import safe_social_embed

    payload = '<blockquote onclick="alert(1)"><script>alert(1)</script><a href="javascript:alert(1)">x</a></blockquote>'
    rendered = str(safe_social_embed(payload)).lower()
    assert "<script" not in rendered
    assert "onclick" not in rendered
    assert "javascript:" not in rendered


def test_post_body_payload_is_escaped_with_test_client() -> None:
    test_app = Flask("bys360-xss-red-gate-v1-test")

    @test_app.post("/_test/bys360-xss-red-gate-v1")
    def _bys360_xss_red_gate_v1_echo():
        template = '<div class="portal-post-body" style="white-space: pre-wrap;">{{ body }}</div>'
        return test_app.jinja_env.from_string(template).render(
            body=request.form.get("body", "")
        )

    payload = '<script>alert("x")</script>\nMerhaba'
    client = test_app.test_client()
    response = client.post(
        "/_test/bys360-xss-red-gate-v1",
        data={"body": payload},
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "<script>" not in html
    assert "&lt;script&gt;" in html or "&lt;script" in html
    assert "white-space: pre-wrap" in html
