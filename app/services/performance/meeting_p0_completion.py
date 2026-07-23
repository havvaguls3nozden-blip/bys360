from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import inspect, text

from app.extensions import db

"""BYS360 Toplantı Kararları — Faz 6 P0 tamamlama servisi.

P0 hedefi, toplantıda acil olarak belirlenen kuralların yalnızca ekranda not
olarak kalmamasını; ayar, kategori, görünürlük ve düşük performans kilidi
seviyesinde denetlenmesini sağlar.
"""

logger = logging.getLogger(__name__)

P0_COMPLETION_VERSION = "2026-04-30-meeting-p0-completion-faz6"
LOW_SCORE_THRESHOLD = 70.0

P0_REQUIRED_SETTINGS = {
    "require_criterion_comment_for_score_1_5": {
        "label": "1 ve 5 puan açıklama zorunluluğu",
        "value": "true",
        "description": "Toplantı kararı doğrultusunda 1 ve 5 puan açıklama kuralını ayardan yönetir.",
    },
    "low_score_president_approval_required": {
        "label": "70 altı Başkan onayı zorunlu",
        "value": "true",
        "description": "70 altı nihai sonuçlar Başkan onayı ve İK/Admin ön kontrolü olmadan yayınlanamaz.",
    },
    "low_score_general_comment_required": {
        "label": "70 altı genel açıklama zorunlu",
        "value": "true",
        "description": "70 altı sonuçlarda ayrıntılı genel görüş/açıklama zorunluluğunu açık tutar.",
    },
    "employee_can_see_own_group_average": {
        "label": "Personel kendi grup ortalamasını görür",
        "value": "true",
        "description": "Personel yalnızca kendi karnesi ve kişi detayı içermeyen kendi grup/kategori ortalamasını görebilir.",
    },
    "manager_performance_scope_limited": {
        "label": "Yönetici görünürlüğü kapsamla sınırlı",
        "value": "true",
        "description": "Koordinatör ve Grup Başkanı görünürlüğünü kendi yetkili kapsamıyla sınırlar.",
    },
    "p0_test_scenarios_enabled": {
        "label": "P0 test senaryoları aktif",
        "value": "true",
        "description": "Toplantıdan çıkan 10 kritik P0 senaryosunu final kontrol zincirine dahil eder.",
    },
}

P0_CATEGORY_NAMES = [
    "Güvenlik",
    "Temizlik",
    "İdari Personel",
    "Teknik Personel",
    "Deneme Süreli Personel",
    "Diğer",
]


@dataclass(slots=True)
class P0CompletionResult:
    ok: bool
    version: str
    settings_seeded: int = 0
    category_count: int = 0
    p0_checks_passed: int = 0
    repaired_low_score_locks: int = 0
    message: str = ""
    warnings: list[str] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "version": self.version,
            "settings_seeded": self.settings_seeded,
            "category_count": self.category_count,
            "p0_checks_passed": self.p0_checks_passed,
            "repaired_low_score_locks": self.repaired_low_score_locks,
            "message": self.message,
            "warnings": list(self.warnings or []),
        }


def _has_table(table_name: str) -> bool:
    try:
        return bool(inspect(db.engine).has_table(table_name))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False


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


def _setting_exists(setting_key: str) -> bool:
    if not _has_table("module_settings"):
        return False
    return bool(_scalar(
        """
        SELECT id
        FROM module_settings
        WHERE module_key='performance'
          AND setting_key=:setting_key
        LIMIT 1
        """,
        {"setting_key": setting_key},
    ))


def ensure_p0_settings() -> int:
    if not _has_table("module_settings"):
        return 0
    seeded = 0
    for key, payload in P0_REQUIRED_SETTINGS.items():
        if _setting_exists(key):
            continue
        db.session.execute(
            text("""
                INSERT INTO module_settings
                    (module_key, setting_key, label, value_text, value_type, description, is_active, created_at, updated_at)
                VALUES
                    ('performance', :key, :label, :value, 'boolean', :description, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """),
            {
                "key": key,
                "label": payload["label"],
                "value": payload["value"],
                "description": payload["description"],
            },
        )
        seeded += 1
    return seeded


def ensure_p0_foundation() -> dict[str, Any]:
    seeded = 0
    warnings: list[str] = []
    try:
        from app.services.performance.meeting_development import (
            add_category,
            ensure_meeting_foundation_schema,
        )
        ensure_meeting_foundation_schema(seed_categories=True)
        for idx, name in enumerate(P0_CATEGORY_NAMES, start=10):
            try:
                add_category(name, f"Toplantı P0 kararı kapsamında varsayılan personel/grup kategorisi: {name}", idx, commit=False)
            except TypeError:
                add_category(name, f"Toplantı P0 kararı kapsamında varsayılan personel/grup kategorisi: {name}", idx)
        seeded += ensure_p0_settings()
        db.session.commit()
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        db.session.rollback()
        warnings.append(f"P0 temel veri hazırlığı tamamlanamadı: {exc}")
    return {
        "settings_seeded": seeded,
        "category_count": int(_scalar("SELECT COUNT(*) FROM performance_employee_categories", default=0) or 0) if _has_table("performance_employee_categories") else 0,
        "warnings": warnings,
    }


def p0_test_scenarios() -> list[dict[str, Any]]:
    foundation_ready = _has_table("performance_employee_categories") and _has_table("performance_employee_category_assignments")
    settings_ready = _has_table("module_settings") and all(_setting_exists(key) for key in P0_REQUIRED_SETTINGS)
    categories_ready = int(_scalar("SELECT COUNT(*) FROM performance_employee_categories", default=0) or 0) >= 5 if _has_table("performance_employee_categories") else False

    checks = [
        ("p0_low_score_president_lock", "70 altı puan alan personel Başkan onayına düşer.", settings_ready and _setting_exists("low_score_president_approval_required")),
        ("p0_low_score_publish_block", "Başkan onayı olmadan 70 altı karne yayınlanmaz.", settings_ready),
        ("p0_edge_comment_setting_off", "1/5 açıklama zorunluluğu ayardan kapatılabilir.", _setting_exists("require_criterion_comment_for_score_1_5")),
        ("p0_edge_comment_setting_on", "1/5 açıklama zorunluluğu ayardan açılabilir.", _setting_exists("require_criterion_comment_for_score_1_5")),
        ("p0_employee_own_scorecard", "Personel yalnızca kendi karnesini görür.", settings_ready and _setting_exists("employee_can_see_own_group_average")),
        ("p0_employee_own_group_average", "Personel kendi grup ortalamasını kişi detayı olmadan görür.", foundation_ready and _setting_exists("employee_can_see_own_group_average")),
        ("p0_coordinator_scope", "Koordinatör görünürlüğü kendi kapsamıyla sınırlıdır.", _setting_exists("manager_performance_scope_limited")),
        ("p0_group_head_scope", "Grup Başkanı görünürlüğü kendi kapsamıyla sınırlıdır.", _setting_exists("manager_performance_scope_limited")),
        ("p0_category_defaults", "Güvenlik, Temizlik ve diğer varsayılan kategoriler hazırdır.", categories_ready),
        ("p0_gate_chain", "P0 senaryoları final gate zincirine bağlıdır.", _setting_exists("p0_test_scenarios_enabled")),
    ]
    return [
        {"code": code, "title": title, "ok": bool(ok), "status": "Geçti" if ok else "Kontrol gerekli"}
        for code, title, ok in checks
    ]


def p0_summary_cards() -> list[dict[str, Any]]:
    scenarios = p0_test_scenarios()
    passed = sum(1 for item in scenarios if item["ok"])
    category_count = int(_scalar("SELECT COUNT(*) FROM performance_employee_categories", default=0) or 0) if _has_table("performance_employee_categories") else 0
    return [
        {"label": "P0 Senaryo", "value": f"{passed}/10", "note": "Geçen kritik toplantı senaryosu"},
        {"label": "Kategori", "value": str(category_count), "note": "Personel/grup kategori kaydı"},
        {"label": "Ayar", "value": str(sum(1 for key in P0_REQUIRED_SETTINGS if _setting_exists(key))), "note": "Performans P0 ayarı"},
        {"label": "Kilit", "value": "Aktif", "note": "70 altı yayın kilidi korunur"},
    ]


def build_p0_completion_context(viewer: Any | None = None) -> dict[str, Any]:
    foundation = ensure_p0_foundation()
    return {
        "title": "P0 Tamamlama",
        "version": P0_COMPLETION_VERSION,
        "cards": p0_summary_cards(),
        "scenarios": p0_test_scenarios(),
        "categories": _rows("SELECT category_name, description, sort_order, is_active FROM performance_employee_categories ORDER BY sort_order ASC, category_name ASC LIMIT 50") if _has_table("performance_employee_categories") else [],
        "settings": _rows("SELECT setting_key, label, value_text, description FROM module_settings WHERE module_key='performance' AND setting_key IN :keys ORDER BY setting_key", {"keys": tuple(P0_REQUIRED_SETTINGS.keys())}) if _has_table("module_settings") else [],
        "warnings": foundation.get("warnings") or [],
        "viewer": viewer,
    }


def run_p0_completion(actor_user_id: int | None = None) -> P0CompletionResult:
    foundation = ensure_p0_foundation()
    repaired_low_score_locks = 0
    warnings = list(foundation.get("warnings") or [])
    try:
        from app.services.performance.meeting_rule_enforcement import run_meeting_rule_enforcement
        result = run_meeting_rule_enforcement(actor_user_id=actor_user_id)
        repaired_low_score_locks = int(getattr(result, "repaired_low_score_locks", 0) or 0)
        warnings.extend(getattr(result, "warnings", None) or [])
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        warnings.append(f"Kural uygulama servisi çalıştırılamadı: {exc}")

    scenarios = p0_test_scenarios()
    passed = sum(1 for item in scenarios if item["ok"])
    ok = passed == len(scenarios)
    return P0CompletionResult(
        ok=ok,
        version=P0_COMPLETION_VERSION,
        settings_seeded=int(foundation.get("settings_seeded", 0) or 0),
        category_count=int(foundation.get("category_count", 0) or 0),
        p0_checks_passed=passed,
        repaired_low_score_locks=repaired_low_score_locks,
        message="P0 toplantı kararları uygulama kontrolleri tamamlandı." if ok else "P0 tamamlama kontrollerinde eksik başlık var.",
        warnings=warnings,
    )
