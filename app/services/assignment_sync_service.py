from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

# --- BYS360 third-manager Excel import compatibility patch ---
THIRD_MANAGER_STANDARD_KEY = "ucuncu_yonetici_sicil"
THIRD_MANAGER_HEADER_ALIASES = [
    "ucuncu_yonetici_sicil",
    "üçüncü yönetici sicil",
    "ucuncu yonetici sicil",
    "3. amir sicil",
    "3 amir sicil",
    "new_y3",
]


"""BYS360 Faz 2.5 - Gorev uyarilarini gorunur yapan ve assignment senkronunu onaran servis.

Amac:
- Aktif donem icin islenecek evaluator zincirini seffaf sekilde gormek
- Ozel baskanlik birimlerini warning yerine info gibi ele almak
- Mevcut acik gorevlerle cakismadan eksik assignment kayitlarini olusturmak
- Var olan / atlanan / warning / info sonuclarini detayli raporlamak

Bu servis hicbir sekilde kafasina gore yeni amir uretmez.
Sadece kullanici kartinda mevcut olan yonetici sicil alanlarini kullanir.
"""

from dataclasses import dataclass, field
from typing import Any

from app.extensions import db
import app.models as models


User = getattr(models, "User", None)
PerformancePeriod = getattr(models, "PerformancePeriod", None)
EvaluationAssignment = getattr(models, "EvaluationAssignment", None)
PerformanceEvaluation = getattr(models, "PerformanceEvaluation", None)

from app.services.performance.hierarchy import build_manager_chain_for_user


SPECIAL_UNIT_NAMES = {
    "HUKUK MÜŞAVİRLİĞİ",
    "HUKUK MUSAVIRLIGI",
    "HUKUK MUSA VIRLIGI",
    "İÇ DENETİM",
    "IC DENETIM",
    "DANIŞMANLIK",
    "DANISMANLIK",
}
TOP_MANAGEMENT_UNITS = {
    "BAŞKANLIK",
    "BASKANLIK",
}
SYSTEM_UNIT_NAMES = {
    "BYS360",
}


@dataclass(slots=True)
class AssignmentDetail:
    employee_id: int | None
    sicil_no: str
    full_name: str
    birim: str
    ust_birim: str
    manager_level: int | None
    evaluator_id: int | None
    evaluator_sicil: str
    evaluator_name: str
    action: str
    severity: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "sicil_no": self.sicil_no,
            "full_name": self.full_name,
            "birim": self.birim,
            "ust_birim": self.ust_birim,
            "manager_level": self.manager_level,
            "evaluator_id": self.evaluator_id,
            "evaluator_sicil": self.evaluator_sicil,
            "evaluator_name": self.evaluator_name,
            "action": self.action,
            "severity": self.severity,
            "reason": self.reason,
        }


@dataclass(slots=True)
class AssignmentSyncSummary:
    ok: bool
    period_id: int | None
    scope_user_count: int
    created_count: int
    existing_count: int
    skipped_count: int
    warning_count: int
    info_count: int
    details: list[AssignmentDetail] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info_notes: list[str] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "period_id": self.period_id,
            "scope_user_count": self.scope_user_count,
            "created": self.created_count,
            "existing": self.existing_count,
            "skipped": self.skipped_count,
            "warnings": list(self.warnings or []),
            "info_notes": list(self.info_notes or []),
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "details": [item.to_dict() for item in self.details],
            "message": self.message,
        }


def _safe(value: Any) -> str:
    return str(value or "").strip()


def _norm(value: Any) -> str:
    return _safe(value).upper()


def _full_name(user: Any) -> str:
    if not user:
        return ""
    full_name = _safe(getattr(user, "full_name", ""))
    if full_name:
        return full_name
    return f"{_safe(getattr(user, 'ad', ''))} {_safe(getattr(user, 'soyad', ''))}".strip()


def _sicil(user: Any) -> str:
    return _safe(getattr(user, "sicil_no", ""))


def _is_system_user(user: Any) -> bool:
    if not user:
        return True
    role = _safe(getattr(user, "role", "")).lower()
    if role == "admin":
        return True
    if _norm(getattr(user, "birim", "")) in SYSTEM_UNIT_NAMES:
        return True
    if _norm(getattr(user, "ust_birim", "")) in SYSTEM_UNIT_NAMES:
        return True
    return False


def _is_special_unit(user: Any) -> bool:
    birim = _norm(getattr(user, "birim", ""))
    ust_birim = _norm(getattr(user, "ust_birim", ""))
    return birim in SPECIAL_UNIT_NAMES or ust_birim in SPECIAL_UNIT_NAMES


def _is_top_management(user: Any) -> bool:
    role = _safe(getattr(user, "role", "")).lower()
    birim = _norm(getattr(user, "birim", ""))
    ust_birim = _norm(getattr(user, "ust_birim", ""))
    return role in {"baskan", "baskan_yardimcisi"} or birim in TOP_MANAGEMENT_UNITS or ust_birim in TOP_MANAGEMENT_UNITS


def _fetch_scope_users(sicils: list[str] | None = None) -> list[Any]:
    if not User:
        return []
    query = User.query
    if hasattr(User, "is_active"):
        query = query.filter(User.is_active == True)  # noqa: E712
    rows = query.order_by(User.id.asc()).all()
    users = [row for row in rows if not _is_system_user(row)]
    if sicils:
        normalized = {_safe(item) for item in sicils if _safe(item)}
        users = [row for row in users if _sicil(row) in normalized]
    return users


def _active_period_id(explicit_period_id: int | None = None) -> int | None:
    if explicit_period_id:
        return explicit_period_id
    if not PerformancePeriod:
        return None
    row = (
        PerformancePeriod.query
        .filter_by(is_active=True)
        .order_by(PerformancePeriod.id.desc())
        .first()
    )
    return getattr(row, "id", None) if row else None


def _build_user_maps(users: list[Any]) -> tuple[dict[str, Any], dict[int, Any]]:
    by_sicil: dict[str, Any] = {}
    by_id: dict[int, Any] = {}
    for user in users:
        s = _sicil(user)
        if s:
            by_sicil[s] = user
        if getattr(user, "id", None) is not None:
            by_id[int(user.id)] = user
    return by_sicil, by_id


def _resolve_manager(user: Any, by_sicil: dict[str, Any], attr_name: str) -> Any | None:
    sicil = _safe(getattr(user, attr_name, ""))
    if not sicil:
        return None
    return by_sicil.get(sicil)


def _desired_levels(user: Any, by_sicil: dict[str, Any], period: Any | None = None) -> tuple[dict[int, Any], list[AssignmentDetail]]:
    """Tek doğru kaynak: authoritative chain resolver.

    Eski sürüm burada ham user kartı alanlarını okuyordu. Bu yüzden Excel'de
    3. amir dolu olsa bile bazı ekranlar/akışlar authoritative resolver yerine
    eski alanlardan beslendiğinde seviye 3 sessizce kaybolabiliyordu.

    Bundan sonra assignment sync tarafı da doğrudan build_manager_chain_for_user
    sonucunu kullanır. Böylece personel listesi, hiyerarşi ekranı, görev üretimi
    ve evaluation linkleri aynı zincirden beslenir.
    """
    details: list[AssignmentDetail] = []

    chain = build_manager_chain_for_user(user=user, users_by_sicil=by_sicil, period=period)

    m1 = by_sicil.get(_safe(getattr(chain, 'manager_1_sicil', ''))) if getattr(chain, 'manager_1_sicil', None) else None
    m2 = by_sicil.get(_safe(getattr(chain, 'manager_2_sicil', ''))) if getattr(chain, 'manager_2_sicil', None) else None
    m3 = by_sicil.get(_safe(getattr(chain, 'manager_3_sicil', ''))) if getattr(chain, 'manager_3_sicil', None) else None

    levels: dict[int, Any] = {}
    if m1:
        levels[1] = m1
    if m2:
        levels[2] = m2
    if m3 and bool(getattr(chain, 'level_3_enabled', True)):
        levels[3] = m3

    base = {
        "employee_id": getattr(user, "id", None),
        "sicil_no": _sicil(user),
        "full_name": _full_name(user),
        "birim": _safe(getattr(user, "birim", "")),
        "ust_birim": _safe(getattr(user, "ust_birim", "")),
    }

    if bool(getattr(chain, 'is_single_manager_case', False)) and m1 and not m2:
        details.append(AssignmentDetail(
            manager_level=2,
            evaluator_id=None,
            evaluator_sicil="",
            evaluator_name="",
            action="skipped",
            severity="info",
            reason="Tek amir kuralı bilgi olarak uygulandı.",
            **base,
        ))
        return levels, details

    if not m1:
        details.append(AssignmentDetail(
            manager_level=1,
            evaluator_id=None,
            evaluator_sicil="",
            evaluator_name="",
            action="skipped",
            severity="warning",
            reason="1. amir bulunamadi.",
            **base,
        ))
    if not m2 and not bool(getattr(chain, 'is_single_manager_case', False)) and not _is_top_management(user):
        details.append(AssignmentDetail(
            manager_level=2,
            evaluator_id=None,
            evaluator_sicil="",
            evaluator_name="",
            action="skipped",
            severity="warning",
            reason="2. amir bulunamadi.",
            **base,
        ))

    explicit_third = _safe(getattr(user, 'ucuncu_yonetici_sicil', ''))
    if explicit_third and not m3:
        details.append(AssignmentDetail(
            manager_level=3,
            evaluator_id=None,
            evaluator_sicil=explicit_third,
            evaluator_name="",
            action="skipped",
            severity="warning",
            reason="Excel veya kartta seçili 3. amir çözümlenemedi.",
            **base,
        ))

    return levels, details


def _ensure_evaluation(period_id: int, employee: Any, levels: dict[int, Any]) -> tuple[Any | None, str]:
    if not PerformanceEvaluation:
        return None, "PerformanceEvaluation modeli bulunamadi."
    row = (
        PerformanceEvaluation.query
        .filter_by(period_id=period_id, employee_id=employee.id)
        .first()
    )
    if not row:
        row = PerformanceEvaluation(
            period_id=period_id,
            employee_id=employee.id,
            level_1_evaluator_id=getattr(levels.get(1), "id", None),
            level_2_evaluator_id=getattr(levels.get(2), "id", None),
            level_3_evaluator_id=getattr(levels.get(3), "id", None),
            status="bekliyor",
        )
        db.session.add(row)
        db.session.flush()
        return row, "created"
    changed = False
    for level, attr in ((1, "level_1_evaluator_id"), (2, "level_2_evaluator_id"), (3, "level_3_evaluator_id")):
        desired_id = getattr(levels.get(level), "id", None)
        if hasattr(row, attr) and getattr(row, attr) != desired_id:
            setattr(row, attr, desired_id)
            changed = True
    if changed:
        db.session.add(row)
        db.session.flush()
        return row, "updated"
    return row, "existing"


def _existing_assignments(period_id: int, employee_id: int) -> list[Any]:
    if not EvaluationAssignment:
        return []
    return list(
        EvaluationAssignment.query
        .filter_by(period_id=period_id, employee_id=employee_id)
        .all()
    )


def _find_existing_exact(existing_rows: list[Any], evaluator_id: int | None, manager_level: int) -> Any | None:
    if not evaluator_id:
        return None
    for row in existing_rows:
        if int(getattr(row, "manager_level", 0) or 0) == int(manager_level) and int(getattr(row, "evaluator_id", 0) or 0) == int(evaluator_id):
            return row
    return None


def _find_existing_same_level(existing_rows: list[Any], manager_level: int) -> Any | None:
    for row in existing_rows:
        if int(getattr(row, "manager_level", 0) or 0) == int(manager_level):
            return row
    return None


def _status_allows_retarget(row: Any) -> bool:
    status = _safe(getattr(row, "status", "")).lower()
    return status in {"", "bekliyor", "taslak", "draft", "pending"}


def _create_assignment(period_id: int, employee_id: int, evaluator_id: int, manager_level: int) -> Any:
    row = EvaluationAssignment(
        period_id=period_id,
        employee_id=employee_id,
        evaluator_id=evaluator_id,
        manager_level=manager_level,
        status="bekliyor",
    )
    db.session.add(row)
    db.session.flush()
    return row


def sync_assignments_for_active_period(
    *,
    period_id: int | None = None,
    sicils: list[str] | None = None,
    commit: bool = True,
) -> AssignmentSyncSummary:
    users = _fetch_scope_users(sicils=sicils)
    active_period_id = _active_period_id(period_id)

    if not active_period_id:
        return AssignmentSyncSummary(
            ok=False,
            period_id=None,
            scope_user_count=len(users),
            created_count=0,
            existing_count=0,
            skipped_count=0,
            warning_count=1,
            info_count=0,
            warnings=["Aktif donem bulunamadi."],
            message="Aktif donem olmadigi icin gorev senkronu calismadi.",
        )

    by_sicil, _ = _build_user_maps(users)

    created = 0
    existing = 0
    skipped = 0
    warning_count = 0
    info_count = 0
    warnings: list[str] = []
    info_notes: list[str] = []
    details: list[AssignmentDetail] = []

    try:
        for user in users:
            period_row = db.session.get(PerformancePeriod, active_period_id) if PerformancePeriod else None
            levels, level_details = _desired_levels(user, by_sicil, period=period_row)
            details.extend(level_details)

            for item in level_details:
                if item.severity == "warning":
                    warning_count += 1
                    warnings.append(f"{item.full_name}: {item.reason}")
                elif item.severity == "info":
                    info_count += 1
                    info_notes.append(f"{item.full_name}: {item.reason}")

            _ensure_evaluation(active_period_id, user, levels)

            existing_rows = _existing_assignments(active_period_id, user.id)

            for manager_level in (1, 2, 3):
                evaluator = levels.get(manager_level)
                if not evaluator:
                    continue

                base = {
                    "employee_id": getattr(user, "id", None),
                    "sicil_no": _sicil(user),
                    "full_name": _full_name(user),
                    "birim": _safe(getattr(user, "birim", "")),
                    "ust_birim": _safe(getattr(user, "ust_birim", "")),
                    "manager_level": manager_level,
                    "evaluator_id": getattr(evaluator, "id", None),
                    "evaluator_sicil": _sicil(evaluator),
                    "evaluator_name": _full_name(evaluator),
                }

                exact = _find_existing_exact(existing_rows, getattr(evaluator, "id", None), manager_level)
                if exact:
                    existing += 1
                    details.append(AssignmentDetail(action="existing", severity="info", reason="Ayni gorev zaten mevcut.", **base))
                    info_count += 1
                    continue

                same_level = _find_existing_same_level(existing_rows, manager_level)
                if same_level and _status_allows_retarget(same_level):
                    same_level.evaluator_id = getattr(evaluator, "id", None)
                    db.session.add(same_level)
                    db.session.flush()
                    existing += 1
                    details.append(AssignmentDetail(action="retargeted", severity="info", reason="Ayni seviyedeki acik gorev yeni evaluator ile guncellendi.", **base))
                    info_count += 1
                    continue
                if same_level and not _status_allows_retarget(same_level):
                    skipped += 1
                    warning_count += 1
                    msg = "Ayni seviyede tamamlanmis/kapali gorev var; evaluator degistirilmedi."
                    warnings.append(f"{_full_name(user)} L{manager_level}: {msg}")
                    details.append(AssignmentDetail(action="skipped", severity="warning", reason=msg, **base))
                    continue

                _create_assignment(active_period_id, user.id, evaluator.id, manager_level)
                created += 1
                details.append(AssignmentDetail(action="created", severity="info", reason="Eksik gorev olusturuldu.", **base))
                info_count += 1

        if commit:
            db.session.commit()
        else:
            db.session.flush()

        return AssignmentSyncSummary(
            ok=True,
            period_id=active_period_id,
            scope_user_count=len(users),
            created_count=created,
            existing_count=existing,
            skipped_count=skipped,
            warning_count=warning_count,
            info_count=info_count,
            details=details,
            warnings=warnings,
            info_notes=info_notes,
            message="Gorev senkronu tamamlandi.",
        )
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        db.session.rollback()
        warnings.append(f"Gorev senkronu hatasi: {exc}")
        return AssignmentSyncSummary(
            ok=False,
            period_id=active_period_id,
            scope_user_count=len(users),
            created_count=created,
            existing_count=existing,
            skipped_count=skipped,
            warning_count=warning_count + 1,
            info_count=info_count,
            details=details,
            warnings=warnings,
            info_notes=info_notes,
            message="Gorev senkronu hata ile sonlandi.",
        )