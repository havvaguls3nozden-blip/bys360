from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

"""BYS360 Performans Aşama 10 — gelişim önerisi ve rehberlik servisi.

Bu servis performans sonucunu yalnızca puanla kapatmamak için kullanılır:
- 70 altı sonuçlarda gelişim önerisi zorunlu/öncelikli kayıt haline gelir.
- 90 üstü sonuçlarda güçlü yön notu tutulabilir.
- Kullanıcıya kısa rehber alanı sunulur.
- Sanal asistan yalnızca rehberlik/yönlendirme sınırında kalır.
- AI karar destek kesin karar vermez; yalnızca dikkat notu üretir.
- Eğitim modülü canlıya açılmaz; ileride ayrı modül olarak genişletilebilir.
"""

logger = logging.getLogger(__name__)

P4_DEVELOPMENT_GUIDANCE_VERSION = "2026-05-01-phase10-development-guidance-binding-v2"
P4_RECOMMENDATION_TABLE = "performance_development_recommendations"

LOW_SCORE_THRESHOLD = 70.0
HIGH_SCORE_THRESHOLD = 90.0

P4_REQUIRED_SETTINGS = {
    "performance_development_recommendations_enabled": {
        "label": "Performans gelişim önerileri aktif",
        "value": "true",
        "description": "Performans sonucundan sonra gelişim önerisi ve güçlü yön notu altyapısını etkinleştirir.",
    },
    "performance_development_recommendation_required_below_70": {
        "label": "70 altı gelişim önerisi zorunlu",
        "value": "true",
        "description": "70 altı sonuçlarda gelişim önerisi oluşturulmasını yayın öncesi kontrol başlığı yapar.",
    },
    "performance_strength_note_enabled_above_90": {
        "label": "90 üstü güçlü yön notu aktif",
        "value": "true",
        "description": "90 üstü sonuçlarda güçlü yön ve iyi uygulama notu tutulmasını destekler.",
    },
    "performance_user_guidance_enabled": {
        "label": "Kullanıcı performans rehberi aktif",
        "value": "true",
        "description": "Personel ve amirler için sade performans kullanım rehberini açar.",
    },
    "performance_virtual_assistant_guidance_enabled": {
        "label": "Sanal asistan rehber yönlendirmesi aktif",
        "value": "true",
        "description": "Sanal asistanın performans ekranlarına yalnızca rehberlik ve yönlendirme yapmasını sağlar.",
    },
    "performance_ai_development_notes_enabled": {
        "label": "AI gelişim dikkat notu aktif",
        "value": "false",
        "description": "AI karar destek notları varsayılan kapalı gelir; açılırsa yalnızca insan denetimli dikkat notu üretir.",
    },
    "performance_ai_no_final_decision": {
        "label": "AI nihai karar vermez",
        "value": "true",
        "description": "AI çıktılarının puan, disiplin veya idari karar yerine geçmeyeceğini sabitler.",
    },
    "performance_development_no_auto_score": {
        "label": "Gelişim önerisi otomatik puan üretmez",
        "value": "true",
        "description": "Gelişim önerisi, ara not veya rehber çıktısı hiçbir şekilde otomatik performans puanı üretmez.",
    },
    "performance_development_no_disciplinary_action": {
        "label": "Gelişim önerisi idari yaptırım üretmez",
        "value": "true",
        "description": "Gelişim önerileri tek başına idari yaptırım, disiplin veya işten çıkarma kararı oluşturmaz.",
    },
    "performance_development_sensitive_data_minimized": {
        "label": "Gelişim önerilerinde hassas veri azaltılır",
        "value": "true",
        "description": "Gelişim ve rehber çıktılarında gereksiz kişisel/hassas içerik gösterilmemesini sağlar.",
    },
}

P4_RECOMMENDATION_COLUMNS: dict[str, str] = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "evaluation_id": "INTEGER",
    "period_id": "INTEGER",
    "employee_user_id": "INTEGER",
    "source": "VARCHAR(80) NOT NULL DEFAULT 'manual'",
    "recommendation_type": "VARCHAR(80) NOT NULL",
    "title": "VARCHAR(255) NOT NULL",
    "recommendation_text": "TEXT NOT NULL",
    "visibility_scope": "VARCHAR(80) NOT NULL DEFAULT 'authorized_scope'",
    "is_required": "BOOLEAN DEFAULT false",
    "status": "VARCHAR(40) NOT NULL DEFAULT 'draft'",
    "created_by": "INTEGER",
    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "updated_at": "TIMESTAMP",
    "approved_by": "INTEGER",
    "approved_at": "TIMESTAMP",
}
P4_RECOMMENDATION_REQUIRED_COLUMNS = set(P4_RECOMMENDATION_COLUMNS)

P4_RECOMMENDATION_TYPES = [
    {"value": "below_70_development", "label": "70 Altı Gelişim Önerisi", "description": "Düşük performans sonucunda gelişim alanını ve takip önerisini kayda alır."},
    {"value": "above_90_strength", "label": "90 Üstü Güçlü Yön Notu", "description": "Çok başarılı sonuçlarda güçlü yön ve iyi uygulama alanını görünür kılar."},
    {"value": "skill_gap", "label": "Gelişim İhtiyacı", "description": "Kriter veya gözlem bazlı gelişim ihtiyacını sade dille belirtir."},
    {"value": "guidance_note", "label": "Rehber Notu", "description": "Personel veya amire süreç kullanımı için karar içermeyen yönlendirme sunar."},
    {"value": "assistant_guidance", "label": "Sanal Asistan Yönlendirmesi", "description": "Asistanın doğru ekrana güvenli geçiş kartı üretmesine temel olur."},
    {"value": "ai_attention_note", "label": "AI Dikkat Notu", "description": "AI açık olduğunda yalnızca insan denetimli dikkat/özet notu niteliğindedir."},
]
P4_TYPE_LABELS = {item["value"]: item["label"] for item in P4_RECOMMENDATION_TYPES}

P4_VISIBILITY_LABELS = {
    "authorized_scope": "Yetkili kişiler görebilir",
    "employee_visible": "Personel karnesinde göster",
    "manager_only": "Sadece yönetici/İK",
}

P4_STATUS_LABELS = {
    "draft": "Taslak",
    "approved": "Onaylandı",
    "archived": "Arşivlendi",
}

P4_VISIBILITY_OPTIONS = [
    {"value": key, "label": label}
    for key, label in P4_VISIBILITY_LABELS.items()
]


P4_GUIDANCE_CARDS = [
    {"title": "70 altı sonuç", "text": "Gelişim önerisi ve Başkan onayı süreci birlikte izlenir; sonuç tek başına kesinleşmiş sayılmaz."},
    {"title": "90 üstü sonuç", "text": "Güçlü yön notu ve iyi uygulama görünürlüğü desteklenir; otomatik ödül/işlem üretmez."},
    {"title": "Personel rehberi", "text": "Personel yayın sonrası kendi karne sonucunu, varsa gelişim önerisini ve güçlü yön notunu görebilir."},
    {"title": "Sanal asistan", "text": "Asistan puan, görüş veya hassas içerik göstermez; yalnızca rehberlik ve güvenli yönlendirme sağlar."},
    {"title": "AI karar destek", "text": "AI karar vermez; yalnızca yöneticinin değerlendirmesine yardımcı olacak dikkat notu üretir."},
]

MANAGER_GUIDANCE_ROLES = {
    "admin",
    "super_admin",
    "system_admin",
    "sistem_yoneticisi",
    "baskan",
    "baskan_yardimcisi",
    "grup_baskani",
    "mali_musavir",
    "koordinator",
    "birim_sorumlusu",
}


@dataclass(slots=True)
class P4DevelopmentGuidanceResult:
    ok: bool
    version: str
    settings_seeded: int = 0
    tables_ready: int = 0
    checks_passed: int = 0
    message: str = ""
    warnings: list[str] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "version": self.version,
            "settings_seeded": self.settings_seeded,
            "tables_ready": self.tables_ready,
            "checks_passed": self.checks_passed,
            "message": self.message,
            "warnings": list(self.warnings or []),
        }


def _dialect() -> str:
    try:
        return db.engine.dialect.name
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return "unknown"


def _has_table(table_name: str) -> bool:
    try:
        return bool(inspect(db.engine).has_table(table_name))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False


def _columns(table_name: str) -> set[str]:
    try:
        return {col["name"] for col in inspect(db.engine).get_columns(table_name)}
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return set()


def _scalar(sql: str, params: dict[str, Any] | None = None, default: Any = None) -> Any:
    try:
        return db.session.execute(text(sql), params or {}).scalar()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in db.session.execute(text(sql), params or {}).mappings().all()]
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return []


def _safe_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _setting_exists(setting_key: str) -> bool:
    if not _has_table("module_settings"):
        return False
    return bool(_scalar("""SELECT id FROM module_settings WHERE module_key='performance' AND setting_key=:setting_key LIMIT 1""", {"setting_key": setting_key}))


def _setting_bool(setting_key: str, default: bool = False) -> bool:
    if not _has_table("module_settings"):
        return default
    raw = _scalar("""SELECT value_text FROM module_settings WHERE module_key='performance' AND setting_key=:setting_key LIMIT 1""", {"setting_key": setting_key})
    if raw is None:
        return default
    return str(raw).strip().lower() in {"true", "1", "on", "evet", "aktif", "yes"}


def _id_column_sql() -> str:
    if _dialect() == "postgresql":
        return "id SERIAL PRIMARY KEY"
    return "id INTEGER PRIMARY KEY AUTOINCREMENT"


def _column_sql(column_name: str) -> str:
    if column_name == "id":
        return _id_column_sql()
    return P4_RECOMMENDATION_COLUMNS[column_name]


def _insert_module_setting(key: str, payload: dict[str, str]) -> bool:
    cols = _columns("module_settings")
    if not {"module_key", "setting_key"}.issubset(cols):
        return False
    values: dict[str, Any] = {"module_key": "performance", "setting_key": key}
    optional_values = {
        "label": payload.get("label"),
        "value_text": payload.get("value", "true"),
        "value_type": "boolean",
        "description": payload.get("description"),
        "is_active": True,
    }
    for name, value in optional_values.items():
        if name in cols:
            values[name] = value
    names = list(values)
    placeholders = [f":{name}" for name in names]
    if "created_at" in cols:
        names.append("created_at")
        placeholders.append("CURRENT_TIMESTAMP")
    if "updated_at" in cols:
        names.append("updated_at")
        placeholders.append("CURRENT_TIMESTAMP")
    db.session.execute(text(f"INSERT INTO module_settings ({', '.join(names)}) VALUES ({', '.join(placeholders)})"), values)
    return True


def ensure_p4_settings() -> int:
    if not _has_table("module_settings"):
        return 0
    seeded = 0
    for key, payload in P4_REQUIRED_SETTINGS.items():
        if _setting_exists(key):
            continue
        if _insert_module_setting(key, payload):
            seeded += 1
    return seeded


def ensure_recommendation_table() -> tuple[bool, list[str]]:
    warnings: list[str] = []
    if not _has_table(P4_RECOMMENDATION_TABLE):
        try:
            column_defs = [f"{name} {_column_sql(name)}" for name in P4_RECOMMENDATION_COLUMNS]
            db.session.execute(text(f"CREATE TABLE {P4_RECOMMENDATION_TABLE} ({', '.join(column_defs)})"))
            db.session.commit()
        except SQLAlchemyError as exc:
            db.session.rollback()
            warnings.append(f"Gelişim önerisi tablosu oluşturulamadı: {exc.__class__.__name__}")
        except Exception as exc:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            db.session.rollback()
            warnings.append(f"Gelişim önerisi tablosu oluşturulamadı: {exc}")

    if _has_table(P4_RECOMMENDATION_TABLE):
        existing = _columns(P4_RECOMMENDATION_TABLE)
        for name in P4_RECOMMENDATION_REQUIRED_COLUMNS - existing:
            if name == "id":
                continue
            try:
                db.session.execute(text(f"ALTER TABLE {P4_RECOMMENDATION_TABLE} ADD COLUMN {name} {_column_sql(name)}"))
                db.session.commit()
            except Exception as exc:
                logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
                db.session.rollback()
                warnings.append(f"Gelişim önerisi alanı eklenemedi ({name}): {exc.__class__.__name__}")
    return _has_table(P4_RECOMMENDATION_TABLE), warnings


def seed_demo_recommendation(actor_user_id: int | None = None) -> int:
    if not _has_table(P4_RECOMMENDATION_TABLE):
        return 0
    title = "Aşama 10 gelişim önerisi altyapısı hazır"
    existing = _scalar(f"SELECT id FROM {P4_RECOMMENDATION_TABLE} WHERE recommendation_type='guidance_note' AND title=:title LIMIT 1", {"title": title})
    if existing:
        return 0
    db.session.execute(text(f"""
        INSERT INTO {P4_RECOMMENDATION_TABLE}
            (source, recommendation_type, title, recommendation_text, visibility_scope, is_required, status, created_by, created_at)
        VALUES
            ('system', 'guidance_note', :title, :text, 'authorized_scope', false, 'draft', :created_by, CURRENT_TIMESTAMP)
    """), {"title": title, "text": "Bu kayıt, performans içinde gelişim önerisi ve rehber alanının hazır olduğunu gösterir. Otomatik puan veya idari karar üretmez.", "created_by": actor_user_id})
    return 1


def _recommendation_filter_sql(alias: str = "") -> str:
    prefix = f"{alias}." if alias else ""
    return f"({prefix}evaluation_id=:evaluation_id OR ({prefix}period_id=:period_id AND {prefix}employee_user_id=:employee_user_id))"


def _evaluation_identity(evaluation: Any) -> dict[str, Any]:
    return {
        "evaluation_id": getattr(evaluation, "id", None),
        "period_id": getattr(evaluation, "period_id", None),
        "employee_user_id": getattr(evaluation, "employee_id", None),
    }


def _recommendation_rows_for_evaluation(evaluation: Any, limit: int = 20) -> list[dict[str, Any]]:
    if not evaluation or not _has_table(P4_RECOMMENDATION_TABLE):
        return []
    params = _evaluation_identity(evaluation) | {"limit": limit}
    rows = _rows(f"""
        SELECT id, source, recommendation_type, title, recommendation_text, visibility_scope, is_required, status, created_by, created_at, approved_by, approved_at
        FROM {P4_RECOMMENDATION_TABLE}
        WHERE {_recommendation_filter_sql()}
        ORDER BY is_required DESC, id DESC
        LIMIT :limit
    """, params)
    for row in rows:
        recommendation_type = str(row.get("recommendation_type") or "")
        visibility_scope = str(row.get("visibility_scope") or "")
        status = str(row.get("status") or "")
        row["type_label"] = P4_TYPE_LABELS.get(recommendation_type, recommendation_type or "Gelişim Önerisi")
        row["visibility_label"] = P4_VISIBILITY_LABELS.get(visibility_scope, "Yetkili görünürlük")
        row["status_label"] = P4_STATUS_LABELS.get(status, "Kontrol Bekliyor")
        row["created_display"] = _safe_text(row.get("created_at"))[:16].replace("T", " ") or "-"
    return rows


def has_required_development_recommendation(evaluation: Any) -> bool:
    if not evaluation:
        return True
    final_score = _safe_float(getattr(evaluation, "final_total_100", None), default=0.0)
    if final_score >= LOW_SCORE_THRESHOLD:
        return True
    if not _setting_bool("performance_development_recommendation_required_below_70", default=False):
        return True
    if not _has_table(P4_RECOMMENDATION_TABLE):
        return False
    count = _scalar(f"""
        SELECT COUNT(*) FROM {P4_RECOMMENDATION_TABLE}
        WHERE {_recommendation_filter_sql()}
          AND (is_required=true OR recommendation_type IN ('below_70_development', 'skill_gap'))
    """, _evaluation_identity(evaluation), default=0)
    try:
        return int(count or 0) > 0
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False


def get_development_recommendation_publish_block_reason(evaluation: Any) -> str:
    """Yayın ön kontrolü için 70 altı gelişim önerisi eksikliği mesajını döndürür."""
    if not evaluation:
        return ""
    final_score = _safe_float(getattr(evaluation, "final_total_100", None), default=0.0)
    if final_score >= LOW_SCORE_THRESHOLD:
        return ""
    if not _setting_bool("performance_development_recommendation_required_below_70", default=False):
        return ""
    if has_required_development_recommendation(evaluation):
        return ""
    return "70 altı sonuçlarda gelişim önerisi kaydı oluşturulmadan personele yayın açılamaz."


def can_manage_development_guidance(viewer: Any | None) -> bool:
    if viewer is None:
        return False
    role = _safe_text(getattr(viewer, "role", "")).lower()
    return bool(role in MANAGER_GUIDANCE_ROLES or getattr(viewer, "is_admin", False) or getattr(viewer, "is_superuser", False))


def build_scorecard_development_guidance_context(evaluation: Any, viewer: Any | None = None) -> dict[str, Any]:
    final_score = _safe_float(getattr(evaluation, "final_total_100", None), default=0.0) if evaluation else 0.0
    is_low = final_score < LOW_SCORE_THRESHOLD
    is_high = final_score > HIGH_SCORE_THRESHOLD
    rows = _recommendation_rows_for_evaluation(evaluation)
    has_required = has_required_development_recommendation(evaluation)
    block_reason = get_development_recommendation_publish_block_reason(evaluation)

    if is_low:
        status_label = "Gelişim önerisi gerekli"
        status_detail = "70 altı sonuç, Başkan onayı sürecinin yanında gelişim önerisiyle desteklenmelidir."
        default_type = "below_70_development"
        default_title = "70 altı sonuç için gelişim önerisi"
        default_required = True
    elif is_high:
        status_label = "Güçlü yön notu eklenebilir"
        status_detail = "90 üstü sonuçlarda güçlü yön, iyi uygulama ve örnek davranış notu tutulabilir."
        default_type = "above_90_strength"
        default_title = "90 üstü sonuç için güçlü yön notu"
        default_required = False
    else:
        status_label = "Rehberlik alanı"
        status_detail = "Bu sonuç bandında gelişim/güçlü yön notu isteğe bağlıdır; puanı otomatik değiştirmez."
        default_type = "guidance_note"
        default_title = "Performans rehber notu"
        default_required = False

    return {
        "version": P4_DEVELOPMENT_GUIDANCE_VERSION,
        "enabled": _setting_bool("performance_development_recommendations_enabled", default=True),
        "final_score": final_score,
        "is_low_score": is_low,
        "is_high_score": is_high,
        "status_label": status_label,
        "status_detail": status_detail,
        "default_type": default_type,
        "default_title": default_title,
        "default_required": default_required,
        "recommendation_types": P4_RECOMMENDATION_TYPES,
        "guidance_cards": P4_GUIDANCE_CARDS,
        "visibility_options": P4_VISIBILITY_OPTIONS,
        "recommendations": rows,
        "count": len(rows),
        "has_required_recommendation": has_required,
        "publish_block_reason": block_reason,
        "can_add_note": can_manage_development_guidance(viewer),
        "ai_note_enabled": _setting_bool("performance_ai_development_notes_enabled", default=False),
        "no_auto_score": _setting_bool("performance_development_no_auto_score", default=True),
        "assistant_guidance_enabled": _setting_bool("performance_virtual_assistant_guidance_enabled", default=True),
    }


def save_development_recommendation(
    *,
    evaluation: Any,
    created_by: int | None,
    recommendation_type: str,
    title: str,
    recommendation_text: str,
    visibility_scope: str = "authorized_scope",
    is_required: bool = False,
    source: str = "manual",
    status: str = "draft",
) -> int | None:
    if not evaluation:
        return None
    ensure_recommendation_table()
    if not _has_table(P4_RECOMMENDATION_TABLE):
        return None
    rec_type = recommendation_type if recommendation_type in P4_TYPE_LABELS else "guidance_note"
    scope = visibility_scope if visibility_scope in {"authorized_scope", "employee_visible", "manager_only"} else "authorized_scope"
    clean_title = _safe_text(title)[:255] or P4_TYPE_LABELS.get(rec_type, "Gelişim Önerisi")
    clean_text = _safe_text(recommendation_text)
    if not clean_text:
        return None
    params = {
        "evaluation_id": getattr(evaluation, "id", None),
        "period_id": getattr(evaluation, "period_id", None),
        "employee_user_id": getattr(evaluation, "employee_id", None),
        "source": source,
        "recommendation_type": rec_type,
        "title": clean_title,
        "recommendation_text": clean_text,
        "visibility_scope": scope,
        "is_required": bool(is_required),
        "status": status if status in {"draft", "approved", "archived"} else "draft",
        "created_by": created_by,
    }
    db.session.execute(text(f"""
        INSERT INTO {P4_RECOMMENDATION_TABLE}
            (evaluation_id, period_id, employee_user_id, source, recommendation_type, title, recommendation_text, visibility_scope, is_required, status, created_by, created_at, updated_at)
        VALUES
            (:evaluation_id, :period_id, :employee_user_id, :source, :recommendation_type, :title, :recommendation_text, :visibility_scope, :is_required, :status, :created_by, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """), params)
    inserted_id = _scalar("SELECT lastval()", default=None) if _dialect() == "postgresql" else _scalar("SELECT last_insert_rowid()", default=None)
    return inserted_id


def p4_status_checks() -> list[dict[str, Any]]:
    rec_cols = _columns(P4_RECOMMENDATION_TABLE) if _has_table(P4_RECOMMENDATION_TABLE) else set()
    p8_ready = _setting_exists("performance_interim_notes_enabled") and _has_table("performance_interim_notes")
    live_ai_tables = _has_table("ai_request_logs") or _has_table("ai_recommendations") or _has_table("ai_summary_cache")
    checks = [
        ("p4_development_enabled", "Gelişim önerileri ayarı hazır.", _setting_exists("performance_development_recommendations_enabled")),
        ("p4_recommendation_table", "Gelişim önerisi tablosu hazır.", _has_table(P4_RECOMMENDATION_TABLE)),
        ("p4_recommendation_columns", "Gelişim önerisi tablosunda değerlendirme, personel, görünürlük ve onay alanları var.", P4_RECOMMENDATION_REQUIRED_COLUMNS.issubset(rec_cols)),
        ("p4_below_70_required", "70 altı sonuçlarda gelişim önerisi zorunlu/öncelikli kontrol başlığıdır.", _setting_exists("performance_development_recommendation_required_below_70")),
        ("p4_above_90_strength", "90 üstü sonuçlarda güçlü yön notu desteklenir.", _setting_exists("performance_strength_note_enabled_above_90")),
        ("p4_user_guidance", "Kullanıcı rehber alanı ayara bağlandı.", _setting_exists("performance_user_guidance_enabled")),
        ("p4_assistant_guidance", "Sanal asistan yalnızca rehberlik ve yönlendirme için bağlandı.", _setting_exists("performance_virtual_assistant_guidance_enabled")),
        ("p4_ai_human_review", "AI çıktı sınırı insan denetimli karar destek olarak işaretlendi.", _setting_exists("performance_ai_no_final_decision")),
        ("p4_no_auto_score", "Gelişim/rehber notları otomatik puan üretmez.", _setting_exists("performance_development_no_auto_score")),
        ("p4_no_disciplinary_action", "Gelişim önerileri tek başına idari yaptırım üretmez.", _setting_exists("performance_development_no_disciplinary_action")),
        ("p4_sensitive_data_minimized", "Gelişim önerilerinde hassas veri azaltma ilkesi hazır.", _setting_exists("performance_development_sensitive_data_minimized")),
        ("p4_p8_dependency", "Dönem içi notlarla gelişim önerisi bağı korunuyor.", p8_ready),
        ("p4_ai_tables_optional", "AI karar destek canlı omurgası varsa güvenli sınırlarla ilişkilendirilebilir.", bool(live_ai_tables or _setting_exists("performance_ai_development_notes_enabled"))),
    ]
    return [{"code": code, "title": title, "ok": bool(ok), "status": "Hazır" if ok else "Kontrol gerekli"} for code, title, ok in checks]


def p4_summary_cards() -> list[dict[str, Any]]:
    checks = p4_status_checks()
    rec_count = _scalar(f"SELECT COUNT(*) FROM {P4_RECOMMENDATION_TABLE}", default=0) if _has_table(P4_RECOMMENDATION_TABLE) else 0
    draft_count = _scalar(f"SELECT COUNT(*) FROM {P4_RECOMMENDATION_TABLE} WHERE status='draft'", default=0) if _has_table(P4_RECOMMENDATION_TABLE) else 0
    required_count = _scalar(f"SELECT COUNT(*) FROM {P4_RECOMMENDATION_TABLE} WHERE is_required=true", default=0) if _has_table(P4_RECOMMENDATION_TABLE) else 0
    return [
        {"label": "Aşama 10 Kontrol", "value": f"{sum(1 for item in checks if item['ok'])}/{len(checks)}", "note": "Hazır olan gelişim/rehberlik başlığı"},
        {"label": "Gelişim Önerisi", "value": str(rec_count or 0), "note": "Toplam öneri/rehber kaydı"},
        {"label": "Taslak Kayıt", "value": str(draft_count or 0), "note": "Kontrol bekleyen öneri"},
        {"label": "Zorunlu Öneri", "value": str(required_count or 0), "note": "70 altı vb. zorunlu işaretlenen kayıt"},
    ]


def build_p4_development_guidance_context(viewer: Any | None = None) -> dict[str, Any]:
    rows = _rows(f"""
        SELECT source, recommendation_type, title, visibility_scope, is_required, status, created_at
        FROM {P4_RECOMMENDATION_TABLE}
        ORDER BY id DESC LIMIT 10
    """) if _has_table(P4_RECOMMENDATION_TABLE) else []
    for row in rows:
        recommendation_type = str(row.get("recommendation_type") or "")
        visibility_scope = str(row.get("visibility_scope") or "")
        status = str(row.get("status") or "")
        row["type_label"] = P4_TYPE_LABELS.get(recommendation_type, recommendation_type or "Gelişim Önerisi")
        row["visibility_label"] = P4_VISIBILITY_LABELS.get(visibility_scope, "Yetkili görünürlük")
        row["status_label"] = P4_STATUS_LABELS.get(status, "Kontrol Bekliyor")
    return {
        "title": "Aşama 10 Gelişim Önerisi ve Rehberlik",
        "version": P4_DEVELOPMENT_GUIDANCE_VERSION,
        "cards": p4_summary_cards(),
        "checks": p4_status_checks(),
        "recommendation_types": P4_RECOMMENDATION_TYPES,
        "guidance_cards": P4_GUIDANCE_CARDS,
        "visibility_options": P4_VISIBILITY_OPTIONS,
        "recommendation_rows": rows,
        "settings": _rows("SELECT setting_key, label, value_text, description FROM module_settings WHERE module_key='performance' ORDER BY setting_key") if _has_table("module_settings") else [],
        "viewer": viewer,
    }


def run_p4_development_guidance(actor_user_id: int | None = None) -> P4DevelopmentGuidanceResult:
    warnings: list[str] = []
    seeded = 0
    try:
        seeded = ensure_p4_settings()
        _, rec_warnings = ensure_recommendation_table()
        warnings.extend(rec_warnings)
        seed_demo_recommendation(actor_user_id=actor_user_id)
        db.session.commit()
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        db.session.rollback()
        warnings.append(f"Aşama 10 gelişim/rehberlik hazırlığı tamamlanamadı: {exc}")
    checks = p4_status_checks()
    passed = sum(1 for item in checks if item["ok"])
    tables_ready = int(_has_table(P4_RECOMMENDATION_TABLE))
    ok = passed == len(checks)
    return P4DevelopmentGuidanceResult(
        ok=ok,
        version=P4_DEVELOPMENT_GUIDANCE_VERSION,
        settings_seeded=seeded,
        tables_ready=tables_ready,
        checks_passed=passed,
        message="Aşama 10 gelişim önerisi, kullanıcı rehberi, sanal asistan ve AI karar destek sınırları hazır." if ok else "Aşama 10 gelişim/rehberlik kontrollerinde eksik başlık var.",
        warnings=warnings,
    )


__all__ = [
    "P4_DEVELOPMENT_GUIDANCE_VERSION",
    "P4_RECOMMENDATION_TABLE",
    "build_p4_development_guidance_context",
    "build_scorecard_development_guidance_context",
    "can_manage_development_guidance",
    "ensure_p4_settings",
    "ensure_recommendation_table",
    "get_development_recommendation_publish_block_reason",
    "has_required_development_recommendation",
    "run_p4_development_guidance",
    "save_development_recommendation",
]
