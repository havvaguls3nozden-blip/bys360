from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import inspect, text

from app.extensions import db
from app.services.performance.meeting_development import (
    build_meeting_development_summary,
    ensure_meeting_foundation_schema,
)

"""BYS360 toplantı geliştirme canlı kontrol ve senaryo omurgası."""

logger = logging.getLogger(__name__)

FORBIDDEN_UI_TERMS = [
    "Faz 3 senkronu",
    "phase sync",
    "workflow state",
    "scorecard_pending",
    "president_pending",
    "blocked_president_pending",
]

STATUS_LABELS = {
    "president_pending": "Başkan Onayı Bekliyor",
    "blocked_president_pending": "Başkan Onayı Yayın Kilidi",
    "hr_precheck": "İK/Admin Ön Kontrolünde",
    "first_low_warning": "Düşük Performans Uyarısı Oluşturuldu",
    "second_low_repeat": "Tekrarlayan Düşük Performans Süreci",
    "approved_by_president": "Başkan Tarafından Onaylandı",
    "rejected_by_president": "Başkan Tarafından İade Edildi",
    "published": "Personele Yayınlandı",
    "draft": "Taslak",
    "completed": "Tamamlandı",
}


@dataclass(frozen=True)
class Scenario:
    code: str
    title: str
    priority: str
    expected: str
    check_hint: str


TEST_SCENARIOS = [
    Scenario("LOW_SCORE_PRESIDENT_APPROVAL", "70 altı sonuç Başkan onayına düşmeli", "P0", "Nihai puan 70 altındaysa karne personele yayınlanmadan Başkan Onayı Bekliyor durumuna alınır.", "Düşük puanlı bir değerlendirme tamamlanır; Başkan Onayları ekranında gerçek kayıt oluştuğu kontrol edilir."),
    Scenario("LOW_SCORE_PUBLICATION_LOCK", "Başkan onayı olmadan yayın kilidi korunmalı", "P0", "70 altı sonuçta İK/Admin ön kontrolü ve Başkan onayı tamamlanmadan personel karnesi kesin görünmez.", "Personel hesabıyla giriş yapılarak karne görünürlüğü denenir."),
    Scenario("EDGE_COMMENT_SETTING", "1 ve 5 puan açıklama kuralı ayardan yönetilmeli", "P0", "Toplantı kararıyla esneklik istenirse kriter bazlı 1/5 açıklaması kapatılabilir; 70 altı genel açıklama ayrı zorunlu kalır.", "Toplantı Geliştirme ekranındaki ayar kapatılıp puanlama formu denenir."),
    Scenario("LEVEL3_OPTIONAL_COLUMN", "3. amir sütunu opsiyonel olmalı", "P1", "3. amir olmayan yapılarda sütun/alan kullanıcıyı yormaz; 3. amir olan kayıtta gerçek akış korunur.", "3. amirsiz ve 3. amirli iki personel kaydıyla hiyerarşi/görev ekranı kontrol edilir."),
    Scenario("GROUP_CATEGORY_SCOPE", "Güvenlik/temizlik gibi personel kategorileri tanımlanmalı", "P0", "Kategori ve dönem kapsamı tanımlanınca raporlar grup kırılımına hazırlanır.", "Toplantı Geliştirme ekranından kategori ve dönem kapsamı eklenir."),
    Scenario("CATEGORY_ASSIGNMENT", "Personel kategoriyle eşleştirilebilmeli", "P0", "Kategori tanımı yalnızca liste olarak kalmaz; personele bağlanır ve rapor kırılımına temel oluşturur.", "Toplantı Derinleştirme ekranında personel-kategori eşleştirme denenir."),
    Scenario("MANAGER_SCOPE_VISIBILITY", "Koordinatör ve grup başkanı kendi kapsamını görmeli", "P0", "Yönetici yalnızca yetkili olduğu grup/birim ortalamasını ve ilgili personel detaylarını görür.", "Koordinatör ve grup başkanı rolleriyle rapor/karne ekranları denenir."),
    Scenario("EMPLOYEE_OWN_CARD_VISIBILITY", "Personel yalnızca kendi karnesini ve grup ortalamasını görmeli", "P0", "Personel başka kişilerin detay puanını, amir görüşünü veya özel karne içeriğini göremez.", "Personel hesabıyla farklı URL denemeleri yapılır; erişim engeli kurumsal ekranla dönmelidir."),
    Scenario("HISTORY_IMPORT_ARCHIVE", "Geçmiş dönem puanları arşive aktarılabilmeli", "P1", "Pasif/geçmiş dönem için eski puanlar arşive eklenir; personel görünürlüğü kayıt bazında yönetilir.", "Toplantı Derinleştirme ekranında geçmiş karne kaydı oluşturulur."),
    Scenario("OBSERVATION_NOTE", "Ara dönem performans notu kaydedilebilmeli", "P2", "Olumlu/olumsuz olay, başarı veya gelişim notu dönem içinde kayıt altına alınır.", "Toplantı Geliştirme ekranında bir personel için not girilir ve yetki kapsamında göründüğü kontrol edilir."),
    Scenario("REMINDER_NOTIFICATIONS", "Aksatan amirlere hatırlatma akışı hazırlanmalı", "P1", "Bekleyen görevlerde sistem içi bildirim/e-posta altyapısı ile hatırlatma üretilebilir.", "Mail log, bildirim ve bekleyen görev ekranları birlikte kontrol edilir."),
]


def _has_table(name: str) -> bool:
    try:
        return inspect(db.engine).has_table(name)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False


def _scalar(sql: str, params: dict[str, Any] | None = None, default: Any = 0) -> Any:
    try:
        return db.session.execute(text(sql), params or {}).scalar() or default
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in db.session.execute(text(sql), params or {}).mappings().all()]
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return []


def label_status(raw_status: str | None) -> str:
    key = (raw_status or "").strip()
    return STATUS_LABELS.get(key, key.replace("_", " ").strip().title() if key else "Durum Yok")


def build_gate_summary() -> dict[str, Any]:
    ensure_meeting_foundation_schema(seed_categories=True)
    summary = build_meeting_development_summary()
    periods_count = _scalar("SELECT COUNT(*) FROM performance_periods", default=0) if _has_table("performance_periods") else 0
    low_score_pending = 0
    if _has_table("performance_evaluations"):
        low_score_pending = _scalar(
            """
            SELECT COUNT(*)
            FROM performance_evaluations
            WHERE COALESCE(final_total_100, 0) < 70
              AND COALESCE(is_published_to_employee, false) = false
            """,
            default=0,
        )
    settings = _rows(
        """
        SELECT setting_key, value_text
        FROM module_settings
        WHERE module_key='performance'
        ORDER BY setting_key
        """
    ) if _has_table("module_settings") else []
    summary.update({"periods_count": periods_count, "low_score_pending": low_score_pending, "settings": settings})
    return summary


def build_meeting_test_context() -> dict[str, Any]:
    return {
        "summary": build_gate_summary(),
        "scenarios": [scenario.__dict__ for scenario in TEST_SCENARIOS],
        "status_labels": STATUS_LABELS,
        "forbidden_terms": FORBIDDEN_UI_TERMS,
    }
