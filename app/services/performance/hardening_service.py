from __future__ import annotations

import re
from typing import Any

TR_FILENAME_MAP = str.maketrans({
    "ç": "c", "Ç": "c",
    "ğ": "g", "Ğ": "g",
    "ı": "i", "I": "i", "İ": "i",
    "ö": "o", "Ö": "o",
    "ş": "s", "Ş": "s",
    "ü": "u", "Ü": "u",
})


def slugify_filename_part(value: Any, default: str = "dosya") -> str:
    text = str(value or "").strip()
    if not text:
        text = default
    text = text.translate(TR_FILENAME_MAP)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or default

def build_period_download_name(prefix: str, period: Any | None = None, extension: str = "xlsx") -> str:
    prefix_part = slugify_filename_part(prefix, default="bys360")
    period_label = getattr(period, "title", None) or getattr(period, "name", None) or "donem"
    period_part = slugify_filename_part(period_label, default="donem")
    ext = slugify_filename_part(extension, default="xlsx")
    return f"{prefix_part}_{period_part}.{ext}"

def humanize_export_exception(exc: Exception) -> str:
    raw = str(exc).strip() or exc.__class__.__name__
    lowered = raw.lower()

    if "permission" in lowered or "yetki" in lowered:
        return "Dışa aktarma dosyası hazırlanırken yetki veya erişim kısıtı algılandı."
    if "openpyxl" in lowered or "workbook" in lowered or "worksheet" in lowered:
        return "Excel dosyası hazırlanırken çalışma kitabı oluşturulamadı."
    if "bytesio" in lowered or "stream" in lowered:
        return "Dışa aktarma akışı hazırlanırken geçici dosya belleği kurulamadı."
    if "none" in lowered or "attributeerror" in lowered:
        return "Eksik veri nedeniyle dışa aktarma dosyası hazırlanamadı."
    return raw