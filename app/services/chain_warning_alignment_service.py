from __future__ import annotations

from app.core.datetime_utils import utc_now
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set


try:
    import app.models as models
except Exception:  # pragma: no cover
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/chain_warning_alignment_service.py:14")
    models = None


User = getattr(models, "User", None) if models else None
PerformancePeriod = getattr(models, "PerformancePeriod", None) if models else None
EvaluationAssignment = getattr(models, "EvaluationAssignment", None) if models else None


SPECIAL_PRESIDENCY_UNITS: set[str] = {
    "BAŞKANLIK",
    "HUKUK MÜŞAVİRLİĞİ",
    "İÇ DENETİM",
    "DANIŞMANLIK",
}


@dataclass
class ChainWarningRecord:
    employee_id: int | None
    sicil_no: str
    full_name: str
    birim: str
    ust_birim: str
    raw_warning: str
    severity: str
    reason: str
    resolved_by_assignment: bool = False
    manager_levels_present: list[int] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "sicil_no": self.sicil_no,
            "full_name": self.full_name,
            "birim": self.birim,
            "ust_birim": self.ust_birim,
            "raw_warning": self.raw_warning,
            "severity": self.severity,
            "reason": self.reason,
            "resolved_by_assignment": self.resolved_by_assignment,
            "manager_levels_present": self.manager_levels_present or [],
        }


def _safe_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _full_name(user: Any) -> str:
    if not user:
        return ""
    full_name = _safe_str(getattr(user, "full_name", ""))
    if full_name:
        return full_name
    ad = _safe_str(getattr(user, "ad", ""))
    soyad = _safe_str(getattr(user, "soyad", ""))
    return f"{ad} {soyad}".strip()


def get_active_period() -> Any | None:
    if not PerformancePeriod:
        return None
    return (
        PerformancePeriod.query.filter_by(is_active=True)
        .order_by(PerformancePeriod.id.desc())
        .first()
    )


def get_users_by_name() -> dict[str, Any]:
    if not User:
        return {}
    users = User.query.filter_by(is_active=True).all() if hasattr(User, "is_active") else User.query.all()
    mapping: dict[str, Any] = {}
    for user in users:
        mapping[_full_name(user).casefold()] = user
    return mapping


def get_assignment_levels_by_employee(period_id: int) -> dict[int, set[int]]:
    levels: dict[int, set[int]] = {}
    if not EvaluationAssignment:
        return levels
    rows = EvaluationAssignment.query.filter_by(period_id=period_id).all()
    for row in rows:
        levels.setdefault(int(row.employee_id), set()).add(int(row.manager_level))
    return levels


def parse_hidden_warning_log(raw_message: str) -> list[str]:
    marker = "Otomatik zincir ham uyarıları gizlendi:"
    payload = raw_message.split(marker, 1)[-1].strip() if marker in raw_message else raw_message.strip()
    if not payload:
        return []
    return [part.strip() for part in payload.split("|") if part.strip()]


def classify_hidden_chain_warning(entry: str, users_by_name: dict[str, Any], assignment_levels: dict[int, set[int]]) -> ChainWarningRecord:
    name, sep, warning_text = entry.partition(":")
    person_name = name.strip()
    warning_text = warning_text.strip() if sep else entry.strip()

    user = users_by_name.get(person_name.casefold())
    levels_present = sorted(assignment_levels.get(int(user.id), set())) if user else []

    birim = _safe_str(getattr(user, "birim", "")) if user else ""
    ust_birim = _safe_str(getattr(user, "ust_birim", "")) if user else ""
    sicil_no = _safe_str(getattr(user, "sicil_no", "")) if user else ""

    resolved = False
    severity = "warning"
    reason = "Ham zincir uyarısı gerçek kullanıcı zinciriyle kontrol edilmelidir."

    if user and levels_present:
        if "Grup Başkanı bulunamadı" in warning_text and 2 in set(levels_present):
            resolved = True
            severity = "info"
            reason = "Görev/assignment gerçeğinde 1. amir seviyesi mevcut; ham uyarı eski ters slotlu zincir motorundan geliyor."
        elif "Koordinatör bulunamadı" in warning_text and 1 in set(levels_present):
            resolved = True
            severity = "info"
            reason = "Görev/assignment gerçeğinde 2. amir seviyesi mevcut; ham uyarı eski ters slotlu zincir motorundan geliyor."

    if birim in SPECIAL_PRESIDENCY_UNITS or ust_birim == "BAŞKANLIK":
        if "Grup Başkanı bulunamadı" in warning_text or "Koordinatör bulunamadı" in warning_text:
            severity = "info"
            resolved = True
            reason = "Başkanlığa bağlı özel birimde standart çalışma grubu zinciri birebir uygulanmayabilir; bu kayıt manuel kritik değil, istisna/information olarak ele alınmalıdır."

    return ChainWarningRecord(
        employee_id=int(user.id) if user else None,
        sicil_no=sicil_no,
        full_name=person_name,
        birim=birim,
        ust_birim=ust_birim,
        raw_warning=warning_text,
        severity=severity,
        reason=reason,
        resolved_by_assignment=resolved,
        manager_levels_present=levels_present,
    )


def audit_hidden_chain_warning_log(raw_message: str) -> dict[str, Any]:
    period = get_active_period()
    users_by_name = get_users_by_name()
    assignment_levels = get_assignment_levels_by_employee(int(period.id)) if period else {}

    entries = parse_hidden_warning_log(raw_message)
    records = [classify_hidden_chain_warning(entry, users_by_name, assignment_levels) for entry in entries]

    info_count = sum(1 for record in records if record.severity == "info")
    warning_count = sum(1 for record in records if record.severity == "warning")
    unresolved = [record.as_dict() for record in records if record.severity == "warning"]

    return {
        "ok": warning_count == 0,
        "generated_at": utc_now().isoformat(timespec="seconds"),
        "period_id": int(period.id) if period else None,
        "entry_count": len(records),
        "info_count": info_count,
        "warning_count": warning_count,
        "records": [record.as_dict() for record in records],
        "notes": [
            "Bu rapor ham zincir uyarılarını aktif görev/assignment gerçeğiyle karşılaştırır.",
            "Çalışma grubu personelinde esas slot kuralı 1. amir = Grup Başkanı, 2. amir = Koordinatördür; eski ters slot logları kritik sayılmamalıdır.",
            "3. amir / birim amiri seviyesi opsiyoneldir; bu seviye eksikliği varsayılanda bilgi notu olmalıdır.",
        ],
        "unresolved": unresolved,
    }
