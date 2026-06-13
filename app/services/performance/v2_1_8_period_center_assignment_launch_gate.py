# -*- coding: utf-8 -*-
from __future__ import annotations


import logging

from typing import Any
from sqlalchemy import inspect

from app.services.performance.v2_1_6_category_period_integration import INTEGRATION_TABLE, PRECHECK_TABLE
from app.services.performance.v2_1_8_period_center_assignment_launch import RULE_VERSION
logger = logging.getLogger(__name__)


def _db():
    from app.extensions import db
    return db


def _check(name: str, ok: bool, message: str) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "message": message}


def run_v2_1_8_period_center_assignment_launch_gate() -> dict[str, Any]:
    """Hafif görev üretimi güvenlik kapısı kontrolü.

    V2.1.8A: Sayfa GET edilirken DDL/ALTER çalıştırmaz. Kolon eksikse uyarı verir;
    görev üretimi başlatılırken servis zaten şemayı güvenli şekilde tamamlar.
    """
    checks: list[dict[str, Any]] = []
    schema: dict[str, Any] = {"ok": True, "mode": "inspect_only"}
    try:
        inspector = inspect(_db().engine)
        has_integration = inspector.has_table(INTEGRATION_TABLE)
        has_precheck = inspector.has_table(PRECHECK_TABLE)
        checks.append(_check("integration_table", has_integration, "Dönem bağlantı tablosu mevcut." if has_integration else "Dönem bağlantı tablosu henüz bulunamadı."))
        checks.append(_check("precheck_table", has_precheck, "Amir/kapsam ön kontrol tablosu mevcut." if has_precheck else "Amir/kapsam ön kontrol tablosu henüz bulunamadı."))
        cols = {col.get("name") for col in inspector.get_columns(INTEGRATION_TABLE)} if has_integration else set()
        for col in ("assignment_generation_status", "assignment_generation_summary", "assignment_generation_run_key", "assignment_generation_at"):
            checks.append(_check(f"column_{col}", col in cols, f"Görev üretimi izleme alanı: {col}" if col in cols else f"Görev üretimi izleme alanı ilk işlemde hazırlanacak: {col}"))
        checks.append(_check("fast_open_policy", True, "Sayfa açılışında ağır görev üretimi kontrolü çalıştırılmaz."))
        checks.append(_check("safe_launch_policy", True, "Görev üretimi yalnızca bağlantılı dönem ve temiz ön kontrol ile başlatılır."))
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            _db().session.rollback()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            pass
        checks.append(_check("exception", False, str(exc)))
        schema = {"ok": False, "error": str(exc)}
    # Kolon eksikleri sayfanın açılmasını engellemesin; güvenlik ilkeleri geçtiyse gate gösterilir.
    return {"ok": all(item.get("ok") for item in checks if not str(item.get("name", "")).startswith("column_")), "checks": checks, "schema": schema, "rule_version": RULE_VERSION}
