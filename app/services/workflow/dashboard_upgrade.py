"""BYS360 Workflow Engine Faz 9 - Yönetici Dashboard Upgrade.

Bu servis canlı performans haritası, en geciken amirler ve riskli personel
analizi için veri hazırlama katmanıdır. Veritabanı modelleri projede farklı
isimlerde olabileceği için servis güvenli fallback ile çalışır; canlı veri
bağlandığında route tarafında SQLAlchemy sorguları bu fonksiyonlara liste/dict
olarak verilebilir.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

LOW_SCORE_LIMIT = 70
HIGH_DELAY_DAYS = 5
WARNING_DELAY_DAYS = 3


@dataclass(frozen=True)
class PerformanceMapRow:
    unit_name: str
    total: int
    completed: int
    low_count: int
    average_score: float | None

    @property
    def completion_rate(self) -> float:
        if self.total <= 0:
            return 0.0
        return round((self.completed / self.total) * 100, 1)

    @property
    def risk_level(self) -> str:
        if self.low_count >= 5 or (self.average_score is not None and self.average_score < LOW_SCORE_LIMIT):
            return "critical"
        if self.low_count > 0 or self.completion_rate < 80:
            return "warning"
        return "normal"


@dataclass(frozen=True)
class DelayedManagerRow:
    manager_name: str
    unit_name: str
    pending_count: int
    max_wait_days: int

    @property
    def risk_level(self) -> str:
        if self.max_wait_days >= HIGH_DELAY_DAYS:
            return "critical"
        if self.max_wait_days >= WARNING_DELAY_DAYS:
            return "warning"
        return "normal"


@dataclass(frozen=True)
class RiskyPersonnelRow:
    personnel_name: str
    unit_name: str
    final_score: float | None
    low_score_count_this_year: int
    status: str

    @property
    def president_approval_required(self) -> bool:
        return self.final_score is not None and self.final_score < LOW_SCORE_LIMIT

    @property
    def risk_level(self) -> str:
        if self.low_score_count_this_year >= 2:
            return "critical"
        if self.president_approval_required:
            return "warning"
        return "normal"


def _get_value(item: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if isinstance(item, dict) and name in item:
            return item[name]
        if hasattr(item, name):
            return getattr(item, name)
    return default


def build_performance_map(rows: Iterable[Any]) -> list[PerformanceMapRow]:
    result: list[PerformanceMapRow] = []
    for row in rows:
        result.append(
            PerformanceMapRow(
                unit_name=str(_get_value(row, "unit_name", "unit", "organization_unit", default="Birim belirtilmemiş")),
                total=int(_get_value(row, "total", "total_count", default=0) or 0),
                completed=int(_get_value(row, "completed", "completed_count", default=0) or 0),
                low_count=int(_get_value(row, "low_count", "low_score_count", default=0) or 0),
                average_score=_safe_float(_get_value(row, "average_score", "avg_score", default=None)),
            )
        )
    return result


def build_delayed_managers(rows: Iterable[Any]) -> list[DelayedManagerRow]:
    result: list[DelayedManagerRow] = []
    for row in rows:
        result.append(
            DelayedManagerRow(
                manager_name=str(_get_value(row, "manager_name", "assigned_user_name", "name", default="Sorumlu belirtilmemiş")),
                unit_name=str(_get_value(row, "unit_name", "unit", default="Birim belirtilmemiş")),
                pending_count=int(_get_value(row, "pending_count", "count", default=0) or 0),
                max_wait_days=int(_get_value(row, "max_wait_days", "wait_days", default=0) or 0),
            )
        )
    return sorted(result, key=lambda x: (x.max_wait_days, x.pending_count), reverse=True)


def build_risky_personnel(rows: Iterable[Any]) -> list[RiskyPersonnelRow]:
    result: list[RiskyPersonnelRow] = []
    for row in rows:
        result.append(
            RiskyPersonnelRow(
                personnel_name=str(_get_value(row, "personnel_name", "user_name", "name", default="Personel belirtilmemiş")),
                unit_name=str(_get_value(row, "unit_name", "unit", default="Birim belirtilmemiş")),
                final_score=_safe_float(_get_value(row, "final_score", "score", default=None)),
                low_score_count_this_year=int(_get_value(row, "low_score_count_this_year", "low_count_year", default=0) or 0),
                status=str(_get_value(row, "status", default="İnceleme Bekliyor")),
            )
        )
    return sorted(result, key=lambda x: ((x.final_score if x.final_score is not None else 999), -x.low_score_count_this_year))


def demo_dashboard_data() -> dict[str, list[Any]]:
    """Boş veritabanı/dev ortamında ekranın kırılmaması için güvenli örnek veri."""
    return {
        "performance_map": build_performance_map([
            {"unit_name": "Personel ve İdari İşler", "total": 42, "completed": 38, "low_count": 2, "average_score": 78.4},
            {"unit_name": "Alan Yönetimi", "total": 35, "completed": 21, "low_count": 5, "average_score": 68.9},
            {"unit_name": "Kurumsal Hizmetler", "total": 28, "completed": 27, "low_count": 0, "average_score": 86.2},
        ]),
        "delayed_managers": build_delayed_managers([
            {"manager_name": "Bekleyen Amir", "unit_name": "Alan Yönetimi", "pending_count": 7, "max_wait_days": 6},
            {"manager_name": "Süreç Sorumlusu", "unit_name": "Personel ve İdari İşler", "pending_count": 3, "max_wait_days": 4},
        ]),
        "risky_personnel": build_risky_personnel([
            {"personnel_name": "Başkan Onayı Bekleyen Kayıt", "unit_name": "Alan Yönetimi", "final_score": 64.5, "low_score_count_this_year": 1, "status": "Başkan Onayı Bekliyor"},
            {"personnel_name": "Tekrar Düşük Performans", "unit_name": "Destek Hizmetleri", "final_score": 61.0, "low_score_count_this_year": 2, "status": "Kritik İnceleme"},
        ]),
    }


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None
