
"""Ortak hata ve rollback yardimcilari.

Personel – saat 10:35.
Burayi ayri tuttum cunku route'larda her seferinde ayni rollback + log tekrarini gormek can sikiyordu.
Hala mucize degil ama en azindan hata turu biraz daha okunur.
"""
from __future__ import annotations

from typing import Any

from flask import current_app
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.extensions import db


def safe_rollback() -> None:
    try:
        db.session.rollback()
    except Exception:  # pragma: no cover - rollback'in de patlamasi zor ama can sıkıcı.
        current_app.logger.exception("Rollback da takildi. Oturum biraz dagilmis olabilir.")


def classify_exception(error: Exception) -> str:
    if isinstance(error, IntegrityError):
        return "integrity"
    if isinstance(error, SQLAlchemyError):
        return "database"
    if isinstance(error, ValueError):
        return "validation"
    if isinstance(error, PermissionError):
        return "permission"
    return "unexpected"


def log_route_exception(label: str, error: Exception, *, rollback: bool = True, extra: dict[str, Any] | None = None) -> str:
    if rollback:
        safe_rollback()
    kind = classify_exception(error)
    payload = {"kind": kind, "label": label}
    if extra:
        payload.update(extra)
    current_app.logger.exception("Route hatasi [%s] (%s): %s | extra=%s", label, kind, error, payload)
    return kind


def humanize_exception(error: Exception, *, default: str = "İşlem sırasında beklenmeyen bir hata oluştu.") -> str:
    kind = classify_exception(error)
    if kind == "integrity":
        return "Kayıt bütünlüğü kontrolü takıldı. Aynı veri ikinci kez girilmiş ya da zorunlu bir alan eksik olabilir."
    if kind == "database":
        return "Veritabanı işlemi sırasında bir sorun oluştu. İşlem geri alındı."
    if kind == "validation":
        return str(error) or default
    if kind == "permission":
        return str(error) or "Bu işlem için yetkiniz uygun görünmüyor."
    return default