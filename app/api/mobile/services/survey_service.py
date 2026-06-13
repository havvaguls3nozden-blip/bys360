# -*- coding: utf-8 -*-
"""BYS360 mobile survey service delegates.

Bu dosya mobil survey handler delegasyonu için güvenli shim katmanıdır.
Route/endpoint isimleri değişmez; gerçek eski gövdeler routes.py içindeki
_bys360_legacy_* fonksiyonlarında korunur.
"""
from __future__ import annotations

from typing import Any


def _call_legacy(name: str, *args: Any, **kwargs: Any) -> Any:
    from app.api.mobile import routes as mobile_routes
    legacy = getattr(mobile_routes, f"_bys360_legacy_{name}", None)
    if legacy is None:
        raise RuntimeError(f"Mobil survey legacy fonksiyonu bulunamadı: {name}")
    return legacy(*args, **kwargs)


def _mobile_survey_detail_payload(*args: Any, **kwargs: Any) -> Any:
    return _call_legacy("_mobile_survey_detail_payload", *args, **kwargs)


def _mobile_survey_validate_answers(*args: Any, **kwargs: Any) -> Any:
    return _call_legacy("_mobile_survey_validate_answers", *args, **kwargs)


def mobile_survey_submit(*args: Any, **kwargs: Any) -> Any:
    return _call_legacy("mobile_survey_submit", *args, **kwargs)
