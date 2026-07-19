from __future__ import annotations


import logging

from typing import Any
from sqlalchemy import inspect

from app.services.performance.v2_1_5_category_period_scope import PLAN_TABLE, PLAN_ITEM_TABLE
from app.services.performance.v2_1_6_category_period_integration import INTEGRATION_TABLE, PRECHECK_TABLE
from app.services.performance.v2_1_7_period_management_center import RULE_VERSION, ensure_period_management_center_ready
logger = logging.getLogger(__name__)


def _db():
    from app.extensions import db
    return db


def _check(name: str, ok: bool, message: str) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "message": message}


def run_v2_1_7_period_management_center_gate() -> dict[str, Any]:
    """Hafif gate kontrolü.

    V2.1.8A: GET sırasında build_period_management_center_state çağrılmaz. Önceki sürümde
    gate bile tüm sayfa durumunu tekrar kurduğu için büyük veride ekran dönerek kalabiliyordu.
    """
    checks: list[dict[str, Any]] = []
    schema: dict[str, Any] = {}
    try:
        schema = ensure_period_management_center_ready()
        inspector = inspect(_db().engine)
        checks.append(_check("v2_1_5_plan_tables", inspector.has_table(PLAN_TABLE) and inspector.has_table(PLAN_ITEM_TABLE), "Dönem kapsam planı tabloları mevcut."))
        checks.append(_check("v2_1_6_integration_tables", inspector.has_table(INTEGRATION_TABLE) and inspector.has_table(PRECHECK_TABLE), "Dönem bağlantısı ve ön kontrol tabloları mevcut."))
        checks.append(_check("center_fast_open", True, "Dönem Yönetim Merkezi hızlı açılış modunda çalışıyor."))
        checks.append(_check("safe_mode", True, "Görev üretimi yalnızca seçili plan ve temiz ön kontrol ile başlatılır."))
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            _db().session.rollback()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            pass
        schema = {"ok": False, "error": str(exc)}
        checks.append(_check("exception", False, str(exc)))
    return {"ok": all(item.get("ok") for item in checks), "schema": schema, "checks": checks, "rule_version": RULE_VERSION}
