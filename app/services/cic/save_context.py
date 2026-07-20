"""Canonical CIC settings persistence service."""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.services.cic.config_context import (
    _clean_ids,
    _dumps_json,
    _now,
    get_config,
    set_setting,
)
from app.services.cic.scheduler_service import set_auto_scheduler_config

BASE_KEY = "corporate_information_center"

TASK_DEFINITIONS: dict[str, dict[str, Any]] = {
    "staff_morning": {
        "category": "personel",
        "label": "Personel Sabah Bilgilendirmesi",
        "short_label": "Sabah Personel",
        "default_hour": 8,
        "default_minute": 0,
        "icon": "fa-sun",
        "description": "Günaydın mesajı, bugünkü hava durumu, kıyafet önerisi ve iyi dilek.",
        "recipient_group": "staff",
        "subject": "Günaydın | BYS360 Günlük Bilgilendirme",
        "body": """Sayın {ad_soyad},

Günaydın.

Bugün {konum} için hava durumu özeti:
{bugun_hava}

Kıyafet önerisi:
{kiyafet_onerisi}

Başarılı, verimli ve güzel bir gün geçirmenizi dileriz.

BYS360
Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı""",
    },
    # BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_1_STAFF_NOON_MESSAGE
    "staff_noon": {
        "category": "personel",
        "label": "Personel Öğlen Bilgilendirmesi",
        "short_label": "Öğlen Personel",
        "default_hour": 12,
        "default_minute": 30,
        "icon": "fa-mug-hot",
        "description": "Gün ortası iyi dilek, mesai kontrolü ve geri bildirim hatırlatması.",
        "recipient_group": "staff",
        "subject": "BYS360 Gün Ortası Destek Hatırlatması",
        "body": """Sayın {ad_soyad},

Gününüz nasıl geçiyor?

Sistemde destek ihtiyacı duyduğunuz bir konu var mı?

BYS360 kullanımı sırasında destek, öneri, hata bildirimi veya geliştirme ihtiyacı oluşursa Geri Bildirim Merkezi üzerinden bize iletebilirsiniz.

Geri bildirim bağlantısı:
{geri_bildirim_baglantisi}

İyi çalışmalar dileriz.

BYS360
Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı""",
    },
    "staff_evening": {
        "category": "personel",
        "label": "Personel Akşam Bilgilendirmesi",
        "short_label": "Akşam Personel",
        "default_hour": 17,
        "default_minute": 30,
        "icon": "fa-cloud-moon",
        "description": "İyi akşamlar mesajı, yarın hava durumu ve ertesi gün hazırlık notu.",
        "recipient_group": "staff",
        "subject": "İyi Akşamlar | BYS360 Yarın İçin Bilgilendirme",
        "body": """Sayın {ad_soyad},

İyi akşamlar.

Yarın {konum} için beklenen hava durumu:
{yarin_hava}

Yarın için öneri:
{yarin_oneri}

Bugünkü emekleriniz için teşekkür eder, güzel bir akşam dileriz.

BYS360""",
    },
    "manager_morning": {
        "category": "yonetici",
        "label": "Yönetici Sabah Özeti",
        "short_label": "Sabah Yönetici",
        "default_hour": 7,
        "default_minute": 45,
        "icon": "fa-chart-line",
        "description": "Yöneticiler için gün başlangıcı kısa kurum içi durum özeti.",
        "recipient_group": "managers",
        "subject": "BYS360 Yönetici Sabah Özeti",
        "body": """Sayın {ad_soyad},

BYS360 gün başlangıcı yönetici özeti aşağıdadır.

Tarih: {tarih}
Aktif personel sayısı: {aktif_personel_sayisi}
Son bilgilendirme durumu: {son_gonderim_durumu}
Bugün takip edilecek ana başlık: {gunun_notu}

Sistem bağlantısı:
{bys360_baglanti}

İyi çalışmalar dileriz.

BYS360""",
    },
    "manager_evening": {
        "category": "yonetici",
        "label": "Yönetici Akşam Özeti",
        "short_label": "Akşam Yönetici",
        "default_hour": 17,
        "default_minute": 45,
        "icon": "fa-clipboard-check",
        "description": "Yöneticiler için gün sonu kısa durum ve ertesi gün dikkat notu.",
        "recipient_group": "managers",
        "subject": "BYS360 Yönetici Akşam Özeti",
        "body": """Sayın {ad_soyad},

BYS360 gün sonu yönetici özeti aşağıdadır.

Tarih: {tarih}
Son gönderim durumu: {son_gonderim_durumu}
Yarın için dikkat notu: {yarin_yonetici_notu}

Sistem bağlantısı:
{bys360_baglanti}

İyi akşamlar dileriz.

BYS360""",
    },
}

def save_tasks(payload: dict[str, Any], actor_user_id: int | None = None) -> None:
    cfg = get_config()
    tasks = cfg["tasks"]
    for key, meta in TASK_DEFINITIONS.items():
        t = tasks.setdefault(key, {})
        t["enabled"] = str(payload.get(f"enabled_{key}", "")).lower() in {"1", "true", "on", "yes"}
        try:
            t["hour"] = max(0, min(23, int(payload.get(f"hour_{key}", meta["default_hour"]))))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:301")
            t["hour"] = meta["default_hour"]
        try:
            t["minute"] = max(0, min(59, int(payload.get(f"minute_{key}", meta["default_minute"]))))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:305")
            t["minute"] = meta["default_minute"]
        t["recipient_group"] = meta["recipient_group"]
    set_setting(f"{BASE_KEY}.tasks", _dumps_json(tasks), label="Kurumsal bilgilendirme görevleri", value_type="json", actor_user_id=actor_user_id)
    db.session.commit()


def _save_system_base(payload: dict[str, Any], actor_user_id: int | None = None) -> None:
    set_setting(f"{BASE_KEY}.location_name", (payload.get("location_name") or "Çanakkale").strip(), label="Hava durumu konumu", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.latitude", (payload.get("latitude") or "40.1553").strip(), label="Enlem", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.longitude", (payload.get("longitude") or "26.4142").strip(), label="Boylam", actor_user_id=actor_user_id)
    db.session.commit()

def save_recipients(payload: dict[str, Any], actor_user_id: int | None = None) -> None:  # noqa: F811
    def getlist_all(*names: str) -> list[Any]:
        values: list[Any] = []
        for name in names:
            try:
                if hasattr(payload, "getlist"):
                    part = payload.getlist(name)
                else:
                    raw = payload.get(name, []) if hasattr(payload, "get") else []
                    part = raw if isinstance(raw, list) else ([raw] if raw else [])
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1570")
                part = []
            for item in part or []:
                if item not in values:
                    values.append(item)
        return values

    manager_ids = _clean_ids(getlist_all("manager_ids", "manager_user_ids", "manager_recipient_ids", "selected_manager_ids"))
    staff_ids = _clean_ids(getlist_all("staff_ids", "staff_user_ids", "staff_recipient_ids", "selected_staff_ids"))
    mode = str(payload.get("staff_recipient_mode") or "manual").strip() if hasattr(payload, "get") else "manual"
    if mode not in {"manual", "all_active"}:
        mode = "manual"

    set_setting(f"{BASE_KEY}.manager_recipient_ids", _dumps_json(manager_ids), label="Yönetici alıcıları", value_type="json", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.staff_recipient_ids", _dumps_json(staff_ids), label="Personel alıcıları", value_type="json", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.staff_recipient_mode", mode, label="Personel alıcı modu", value_type="string", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.last_recipient_save_summary", _dumps_json({"manager_count": len(manager_ids), "staff_count": len(staff_ids), "mode": mode}), label="Son alıcı kayıt özeti", value_type="json", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.last_recipient_save_at", _now().isoformat(timespec="seconds"), label="Son alıcı kayıt zamanı", value_type="string", actor_user_id=actor_user_id)
    db.session.commit()

def save_system(payload: dict[str, object], actor_user_id: int | None = None) -> None:
    """Persist CIC system settings through one explicit public layer.

    Flattened legacy wrapper chain:
    - Base weather/location settings are saved by _save_system_base.
    - Auto scheduler settings are saved once by set_auto_scheduler_config.
    """
    _save_system_base(payload, actor_user_id=actor_user_id)
    set_auto_scheduler_config(payload, actor_user_id=actor_user_id)



__all__ = [
    "_save_system_base",
    "save_recipients",
    "save_system",
    "save_tasks",
]
