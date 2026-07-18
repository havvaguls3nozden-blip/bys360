
"""Rapor/PDF dışa aktarımında zaman aşımı riskini azaltan koruma."""
from __future__ import annotations


from flask import current_app


def max_inline_pdf_rows() -> int:
    try:
        return int(current_app.config.get("PDF_EXPORT_MAX_ROWS_INLINE", 250) or 250)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/pdf_export_guard.py:13")
        return 250


def validate_inline_pdf_export(row_count: int, *, label: str = "PDF") -> tuple[bool, str]:
    limit = max_inline_pdf_rows()
    if int(row_count or 0) <= limit:
        return True, "PDF dışa aktarımı inline çalışabilir."
    return False, (
        f"{label} çıktısı {row_count} kayıt içeriyor. Canlı sistemde zaman aşımı riskini önlemek için "
        f"tek seferde en fazla {limit} kayıt PDF olarak hazırlanabilir. Filtre kullanın veya Excel çıktısını alın."
    )
