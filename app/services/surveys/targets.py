"""Anket hedef kitle ve erişim yardımcıları.

Faz 6 amacı:
- Canlı anket modülünde hedef kitle/erişim okuma mantığını route dışına almak.
- Yanıt kaydetme, yayınlama, kapatma, arşivleme ve silme akışlarına dokunmamak.
- Eski template/JSON sözleşmelerini korumak.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from .contracts import SurveyTargetDraft
from .normalizers import clean_target_values, normalize_choice, safe_text, SURVEY_ALLOWED_TARGET_TYPES, SURVEY_TARGET_TYPES
import logging
logger = logging.getLogger(__name__)

LogCallback = Callable[[str, BaseException], None]
ResetCallback = Callable[[], None]


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/targets.py | line=24")
        return default


def _reset(reset_callback: ResetCallback | None = None) -> None:
    if reset_callback is not None:
        try:
            reset_callback()
            return
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/surveys/targets.py")
    try:
        from app.extensions import db

        db.session.rollback()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/surveys/targets.py")
def _log(label: str, exc: BaseException, log_callback: LogCallback | None = None) -> None:
    if log_callback is not None:
        try:
            log_callback(label, exc)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/surveys/targets.py")
def user_item(user: Any) -> dict[str, Any]:
    """Canlı route/template sözleşmesiyle uyumlu kullanıcı etiketi üretir."""
    full_name = safe_text(getattr(user, "full_name", None))
    if not full_name:
        full_name = f"{safe_text(getattr(user, 'ad', ''))} {safe_text(getattr(user, 'soyad', ''))}".strip()
    full_name = full_name or f"Kullanıcı #{safe_text(getattr(user, 'id', ''))}"

    meta_parts: list[str] = []
    for value in (getattr(user, "sicil_no", None), getattr(user, "unvan", None), getattr(user, "birim", None)):
        cleaned = safe_text(value)
        if cleaned:
            meta_parts.append(cleaned)

    return {
        "id": _safe_int(getattr(user, "id", 0)),
        "label": full_name,
        "meta": " • ".join(meta_parts[:3]),
    }


def selected_user_items(users: Iterable[Any] | None) -> list[dict[str, Any]]:
    """Model nesnelerinden canlı template uyumlu kullanıcı listesi üretir."""
    return [item for item in (user_item(user) for user in (users or [])) if item.get("id")]


def selected_user_items_by_ids(
    raw_user_ids: Iterable[Any] | None,
    *,
    reset_callback: ResetCallback | None = None,
    log_callback: LogCallback | None = None,
) -> list[dict[str, Any]]:
    """Formdan gelen kullanıcı id listesini mevcut seçim etiketi listesine çevirir."""
    ids: list[int] = []
    for value in raw_user_ids or []:
        try:
            user_id = int(str(value).strip())
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/surveys/targets.py:84)")
            continue
        if user_id > 0 and user_id not in ids:
            ids.append(user_id)
    if not ids:
        return []

    try:
        from app.models import User

        rows = User.query.filter(User.id.in_(ids)).all()
        lookup = {_safe_int(getattr(row, "id", 0)): user_item(row) for row in rows}
        return [lookup[user_id] for user_id in ids if user_id in lookup]
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/targets.py | line=100")
        _reset(reset_callback)
        _log("survey_selected_user_items", exc, log_callback)
        return []


def distinct_user_values(
    column: Any,
    *,
    reset_callback: ResetCallback | None = None,
    log_callback: LogCallback | None = None,
) -> list[str]:
    """Aktif kullanıcılardaki benzersiz rol/birim gibi metin değerlerini döndürür."""
    try:
        from sqlalchemy import func
        from app.extensions import db
        from app.models import User

        rows = (
            db.session.query(column.label("value"))
            .filter(User.is_active.is_(True), column.isnot(None))
            .filter(func.length(func.trim(column)) > 0)
            .group_by(column)
            .order_by(func.lower(column), column)
            .all()
        )
        values: list[str] = []
        for row in rows:
            cleaned = safe_text(getattr(row, "value", None))
            if cleaned:
                values.append(cleaned)
        return values
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/targets.py | line=132")
        _reset(reset_callback)
        _log("survey_distinct_user_values", exc, log_callback)
        return []


def active_user_count(
    *,
    reset_callback: ResetCallback | None = None,
    log_callback: LogCallback | None = None,
) -> int:
    """Aktif kullanıcı sayısını savunmacı biçimde döndürür."""
    try:
        from app.models import User

        return int(User.query.filter(User.is_active.is_(True)).count())
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/targets.py | line=148")
        _reset(reset_callback)
        _log("survey_active_user_count", exc, log_callback)
        return 0


def resolve_target_user_ids(target_type: str, raw_values: Iterable[Any] | None) -> list[int]:
    """Hedef tip/değerlerinden aktif kullanıcı id listesi üretir.

    Canlı route davranışı korunur: all/user/role/unit desteklenir, bilinmeyen tip
    boş liste döndürür.
    """
    normalized_type = safe_text(target_type) or "all"
    cleaned_values = [safe_text(value) for value in (raw_values or []) if safe_text(value)]

    try:
        from sqlalchemy import func
        from app.extensions import db
        from app.models import User

        if normalized_type == "all":
            rows = db.session.query(User.id).filter(User.is_active.is_(True)).all()
            return [_safe_int(row[0]) for row in rows]

        if normalized_type == "user":
            user_ids: list[int] = []
            for value in cleaned_values:
                if value.isdigit():
                    parsed = int(value)
                    if parsed not in user_ids:
                        user_ids.append(parsed)
            if not user_ids:
                return []
            rows = db.session.query(User.id).filter(User.is_active.is_(True), User.id.in_(user_ids)).all()
            return [_safe_int(row[0]) for row in rows]

        lowered = [value.lower() for value in cleaned_values]
        if not lowered:
            return []

        if normalized_type == "role":
            rows = (
                db.session.query(User.id)
                .filter(User.is_active.is_(True))
                .filter(func.lower(func.coalesce(User.role, "")).in_(lowered))
                .all()
            )
            return [_safe_int(row[0]) for row in rows]

        if normalized_type == "unit":
            rows = (
                db.session.query(User.id)
                .filter(User.is_active.is_(True))
                .filter(func.lower(func.coalesce(User.birim, "")).in_(lowered))
                .all()
            )
            return [_safe_int(row[0]) for row in rows]

        return []
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/targets.py | line=207")
        # Eski route fonksiyonu burada özel log üretmüyordu. Davranışı sade tutmak
        # için hata halinde boş hedef listesi döndürülür.
        return []


def estimate_survey_target_user_ids(survey: Any) -> set[int]:
    """Mevcut SurveyAssignment kayıtlarından tahmini hedef kullanıcı kümesi üretir."""
    try:
        from app.models import User

        users = User.query.filter_by(is_active=True).all()
        target_user_ids: set[int] = set()
        assignments = getattr(survey, "assignments", None)
        assignment_rows = assignments.all() if hasattr(assignments, "all") else list(assignments or [])
        for assignment in assignment_rows:
            target_type = safe_text(getattr(assignment, "target_type", "")).lower()
            target_value = safe_text(getattr(assignment, "target_value", ""))
            if target_type == "all":
                target_user_ids.update(_safe_int(getattr(user, "id", 0)) for user in users)
            elif target_type == "user" and target_value.isdigit():
                target_user_ids.add(int(target_value))
            elif target_type == "role":
                target_user_ids.update(
                    _safe_int(getattr(user, "id", 0))
                    for user in users
                    if safe_text(getattr(user, "role", "")).lower() == target_value.lower()
                )
            elif target_type == "unit":
                target_user_ids.update(
                    _safe_int(getattr(user, "id", 0))
                    for user in users
                    if safe_text(getattr(user, "birim", "")).lower() == target_value.lower()
                )
        return {user_id for user_id in target_user_ids if user_id > 0}
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/targets.py | line=242")
        return set()


def assignment_matches_user_filter(user: Any):
    """SurveyAssignment hedefini kullaniciya gore SQL filtresine cevirir.

    Eski Python dongusu su hedefleri destekliyordu: all, user, role, unit.
    Bu yardimci ayni kurali SQLAlchemy WHERE/OR katmanina indirir.
    """
    from sqlalchemy import and_, func, or_
    from app.models import SurveyAssignment

    target_type = func.lower(func.trim(func.coalesce(SurveyAssignment.target_type, "")))
    target_value_text = func.trim(func.coalesce(SurveyAssignment.target_value, ""))
    target_value_lower = func.lower(target_value_text)

    conditions = [target_type == "all"]

    user_id_text = safe_text(getattr(user, "id", ""))
    if user_id_text:
        conditions.append(and_(target_type == "user", target_value_text == user_id_text))

    role_text = safe_text(getattr(user, "role", "")).lower()
    if role_text:
        conditions.append(and_(target_type == "role", target_value_lower == role_text))

    unit_text = safe_text(getattr(user, "birim", "")).lower()
    if unit_text:
        conditions.append(and_(target_type == "unit", target_value_lower == unit_text))

    return or_(*conditions)


def matching_assignment_for_user(survey_id: int, user: Any) -> Any | None:
    """Belirli anket icin kullaniciya uyan ilk assignment kaydini SQL ile bulur."""
    try:
        from app.models import SurveyAssignment

        return (
            SurveyAssignment.query
            .filter(SurveyAssignment.survey_id == int(survey_id))
            .filter(assignment_matches_user_filter(user))
            .order_by(SurveyAssignment.id.asc())
            .first()
        )
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/targets.py | line=288")
        _reset()
        return None


def assigned_survey_assignment_rows_for_user(user: Any, *, active_window: bool = False, now: Any | None = None) -> list[tuple[Any, Any]]:
    """Kullaniciya uyan yayinlanmis anketleri assignment ile birlikte SQL'den getirir."""
    try:
        from sqlalchemy import or_
        from app.models import Survey, SurveyAssignment

        query = (
            Survey.query
            .with_entities(Survey, SurveyAssignment)
            .join(SurveyAssignment, SurveyAssignment.survey_id == Survey.id)
            .filter(Survey.status == "published")
            .filter(assignment_matches_user_filter(user))
        )
        if active_window:
            if now is None:
                from app.core.datetime_utils import utc_now

                now = utc_now()
            query = query.filter(or_(Survey.start_at.is_(None), Survey.start_at <= now))
            query = query.filter(or_(Survey.end_at.is_(None), Survey.end_at >= now))

        return query.order_by(Survey.created_at.desc(), Survey.id.desc(), SurveyAssignment.id.asc()).all()
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/targets.py | line=315")
        _reset()
        return []


def target_user_search_items(query_text: str, *, limit: int = 20) -> list[dict[str, Any]]:
    """Kişi hedefleme autocomplete sonuçlarını üretir."""
    query = safe_text(query_text)
    try:
        limit_i = int(limit or 20)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/targets.py | line=325")
        limit_i = 20
    limit_i = max(5, min(limit_i, 50))
    if len(query) < 2:
        return []

    try:
        from sqlalchemy import func, or_
        from app.models import User

        like = f"%{query}%"
        rows = (
            User.query
            .filter(User.is_active.is_(True))
            .filter(
                or_(
                    User.full_name_cache.ilike(like),
                    User.ad.ilike(like),
                    User.soyad.ilike(like),
                    User.sicil_no.ilike(like),
                    User.unvan.ilike(like),
                    User.birim.ilike(like),
                    User.role.ilike(like),
                    User.email.ilike(like),
                )
            )
            .order_by(func.lower(func.coalesce(User.full_name_cache, User.ad, "")), func.lower(func.coalesce(User.soyad, "")), User.id.asc())
            .limit(limit_i)
            .all()
        )
        return [user_item(row) for row in rows]
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/targets.py | line=356")
        return []


def build_target_draft(
    *,
    target_type: str,
    raw_values: Iterable[Any] | None,
    roles: Iterable[str] | None = None,
    birimler: Iterable[str] | None = None,
) -> SurveyTargetDraft:
    normalized_type = normalize_choice(target_type, SURVEY_ALLOWED_TARGET_TYPES or SURVEY_TARGET_TYPES, "all")
    values = clean_target_values(normalized_type, raw_values, roles=roles, birimler=birimler)
    user_ids = resolve_target_user_ids(normalized_type, values)
    return SurveyTargetDraft(target_type=normalized_type, target_values=values, user_ids=user_ids)
