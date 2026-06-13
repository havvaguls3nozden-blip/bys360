from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

REQUIRE_CRITERION_COMMENT_FOR_SCORE_1 = True
REQUIRE_CRITERION_COMMENT_FOR_SCORE_3 = False
REQUIRE_CRITERION_COMMENT_FOR_SCORE_5 = True


def _performance_module_setting_bool(setting_key: str, default: bool) -> bool:
    """ModuleSetting üzerinden canlı kural okur; tablo yoksa güvenli varsayılan döner."""
    try:
        from sqlalchemy import inspect, text
        from app.extensions import db
        if not inspect(db.engine).has_table("module_settings"):
            return bool(default)
        row = db.session.execute(
            text("""
                SELECT value_text
                FROM module_settings
                WHERE module_key = 'performance'
                  AND setting_key = :setting_key
                  AND is_active = true
                ORDER BY id DESC
                LIMIT 1
            """),
            {"setting_key": setting_key},
        ).first()
        if not row:
            return bool(default)
        raw = str(row[0] or "").strip().lower()
        if raw in {"1", "true", "on", "yes", "evet", "aktif", "active"}:
            return True
        if raw in {"0", "false", "off", "no", "hayir", "hayır", "pasif", "inactive"}:
            return False
        return bool(default)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return bool(default)


def normalize_raw_score(raw_score) -> int | None:
    try:
        if raw_score in (None, ""):
            return None
        return int(float(raw_score))
    except (TypeError, ValueError):
        return None


def score_requires_criterion_comment(raw_score) -> bool:
    normalized = normalize_raw_score(raw_score)
    require_edge_comment = _performance_module_setting_bool(
        "require_criterion_comment_for_score_1_5",
        True,
    )
    if normalized == 1:
        return bool(require_edge_comment and REQUIRE_CRITERION_COMMENT_FOR_SCORE_1)
    if normalized == 3:
        return REQUIRE_CRITERION_COMMENT_FOR_SCORE_3
    if normalized == 5:
        return bool(require_edge_comment and REQUIRE_CRITERION_COMMENT_FOR_SCORE_5)
    return False


def is_level_2_comment_required_when_level_1_score_is_three() -> bool:
    return False
