from __future__ import annotations


import logging

"""BYS360 Performans V2.1.1 kalite kapısı."""

from typing import Any
logger = logging.getLogger(__name__)


def run_v2_1_1_quality_gate() -> dict[str, Any]:
    result: dict[str, Any] = {"ok": True, "checks": []}

    def add(name: str, ok: bool, message: str) -> None:
        result["checks"].append({"name": name, "ok": bool(ok), "message": message})
        if not ok:
            result["ok"] = False

    try:
        from app.services.performance.v2_1_rule_engine import build_rule_snapshot_dict, validate_score_comment_rules, status_label
        snapshot = build_rule_snapshot_dict()
        add("rule_engine_import", True, "Kural motoru import edildi.")
        add("settings_count", len(snapshot.get("settings", {})) >= 8, f"Ayar sayısı: {len(snapshot.get('settings', {}))}")
        add("score_1_comment", bool(validate_score_comment_rules(raw_score=1, criterion_comment="")), "1 puan açıklama kontrolü çalışıyor.")
        add("low_score_comment", bool(validate_score_comment_rules(score_100=69, general_comment="")), "70 altı genel görüş kontrolü çalışıyor.")
        add("status_label", status_label("president_pending") == "Başkan Onayı Bekliyor", "Teknik statü Türkçe etikete çevriliyor.")
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        add("rule_engine_import", False, f"Kural motoru hatası: {exc}")

    try:
        from sqlalchemy import inspect
        from app.extensions import db
        has_table = inspect(db.engine).has_table("module_settings")
        add("module_settings_table", has_table, "module_settings tablosu mevcut." if has_table else "module_settings tablosu bulunamadı.")
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        add("module_settings_table", False, f"module_settings kontrol hatası: {exc}")

    return result
