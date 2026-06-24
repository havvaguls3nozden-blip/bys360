"""BYS360 KPI ortak hesaplama yardımcıları.

Maintenance 10E yol haritası kapsamında ``calculate_completion_rate`` tekrarı tek
merkezde toplandı. Servisler Decimal tabanlı bu yardımcıyı kullanır; ekran
servisleri gerekirse 100 üstünü kart görünümü için sınırlayabilir.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

# BYS360_MAINTENANCE_10E_KPI_UTILS

TWO_PLACES = Decimal("0.01")


def to_decimal(value: Any, default: Decimal | None = None) -> Decimal | None:
    """Değeri güvenli Decimal'e çevirir.

    Boş, None veya geçersiz değerlerde ``default`` döner. Float doğrudan Decimal'e
    verilmez; string üzerinden alınır ki yuvarlama sürprizi oluşmasın.
    """
    if value is None or value == "":
        return default
    try:
        return Decimal(str(value).replace(",", ".").strip())
    except (InvalidOperation, ValueError, TypeError, AttributeError):
        return default


def quantize_rate(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_completion_rate(
    target_value: Any,
    current_value: Any,
    *,
    cap_at_100: bool = False,
) -> Decimal:
    """Hedef ve gerçekleşen değere göre yüzde tamamlanma oranı hesaplar.

    Kurallar:
    - hedef boş, geçersiz veya 0/negatif ise 0.00 döner,
    - gerçekleşen boş/geçersiz veya negatif ise 0.00 döner,
    - varsayılan olarak 100 üstü başarı korunur,
    - dashboard kartlarında istenirse ``cap_at_100=True`` ile 100'e sınırlandırılır.
    """
    target = to_decimal(target_value)
    current = to_decimal(current_value)
    if target is None or current is None or target <= 0 or current < 0:
        return Decimal("0.00")

    rate = (current / target) * Decimal("100")
    if cap_at_100 and rate > Decimal("100"):
        rate = Decimal("100")
    return quantize_rate(rate)


def classify_kpi_status(completion_rate: Any) -> dict[str, str]:
    """Başarı oranına göre kurumsal durum ve risk etiketi üretir."""
    rate = to_decimal(completion_rate, Decimal("0")) or Decimal("0")
    if rate >= Decimal("90"):
        return {
            "status": "completed",
            "status_label": "Tamamlandı",
            "risk_level": "low",
            "risk_label": "Düşük",
        }
    if rate >= Decimal("70"):
        return {
            "status": "ongoing",
            "status_label": "Devam Ediyor",
            "risk_level": "normal",
            "risk_label": "Normal",
        }
    if rate >= Decimal("50"):
        return {
            "status": "at_risk",
            "status_label": "Riskli",
            "risk_level": "high",
            "risk_label": "Yüksek",
        }
    return {
        "status": "critical",
        "status_label": "Kritik",
        "risk_level": "critical",
        "risk_label": "Kritik",
    }


def completion_rate_float(target_value: Any, current_value: Any, *, cap_at_100: bool = False) -> float:
    """Dashboard ve JSON çıktıları için float karşılık döndürür."""
    return float(calculate_completion_rate(target_value, current_value, cap_at_100=cap_at_100))
