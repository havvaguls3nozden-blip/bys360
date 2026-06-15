from __future__ import annotations

from flask import render_template


def render_error_page(status_code: int, title: str, message: str):
    """Standart hata sayfasini guvenli fallback ile dondurur."""
    try:
        return render_template(
            f"errors/{status_code}.html",
            title=title,
            message=message,
        ), status_code
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/bootstrap/error_pages.py:16")
        return (
            f"""
            <html>
                <head><title>{status_code} - {title}</title></head>
                <body style="font-family: Arial, sans-serif; padding: 40px;">
                    <h2>{title}</h2>
                    <p>{message}</p>
                </body>
            </html>
            """,
            status_code,
        )
