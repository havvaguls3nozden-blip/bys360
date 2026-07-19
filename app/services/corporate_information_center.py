from __future__ import annotations

import json
import ssl
import time
from datetime import datetime
from typing import Any
from urllib.request import urlopen

from flask import current_app
from sqlalchemy import or_

from app.extensions import db
from app.models import SystemSetting, User

try:
    from app.services.mail_core import send_email, create_mail_log
except Exception:  # pragma: no cover
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/corporate_information_center.py:20")
    send_email = None
    create_mail_log = None

VERSION = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE1"
GROUP_KEY = "corporate_information_center"
BASE_KEY = "corporate_information_center"
ADMIN_ROLES = {"admin", "administrator", "super_admin", "system_admin", "sistem_yoneticisi"}

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


# Phase4J V26E CIC config_context facade imports
from app.services.cic.config_context import (
    _clean_ids,
    _clothing,
    _dumps_json,
    _ensure_defaults_base,
    _format_weather,
    _has_settings_table,
    _loads_json,
    _now,
    _tomorrow_note,
    _weather,
    ensure_defaults,
    get_config,
    get_setting,
    set_setting,
)













def can_manage(user: Any) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    role = str(getattr(user, "role", "") or "").lower()
    return role in ADMIN_ROLES








# Phase4J V30C CIC save_context facade imports
from app.services.cic.save_context import (
    _save_system_base,
    ensure_celebration_schema,
    save_celebration_settings,
    save_recipients,
    save_system,
    save_tasks,
    save_templates,
    set_auto_scheduler_config,
)






# Phase4J V28C CIC send_context facade imports
from app.services.cic.send_context import (
    _cic_v11_bool,
    _cic_v11_clean_header,
    _cic_v11_get_setting_value,
    _cic_v11_mail_settings,
    _cic_v11_normalize_email,
    _cic_v11_send_email_direct,
    _cic_v40_active_staff_candidates,
    _cic_v40_anniversary_users,
    _cic_v40_birthday_users,
    _cic_v40_bool,
    _cic_v40_mmdd,
    _cic_v40_parse_date,
    _cic_v40_service_year,
    _cic_v40_setting_bool,
    _cic_v40_special_day_users,
    _cic_v40_special_days,
    _cic_v40_special_days_today,
    _cic_v40_today,
    _cic_v40_user_date,
    _dashboard_counts,
    _recipients_for_task,
    _recipients_for_task_base,
    _render_template_text,
    _render_template_text_base,
    _send_task_base,
    _user_name,
)



# Phase4J V27C CIC misc_context facade imports
from app.services.cic.misc_context import (
    _active_staff_users,
    _cic_auto_bool,
    _cic_phase5_audit_list,
    _cic_phase5_last_result,
    _cic_phase5_log_metrics,
    _cic_phase5_mail_health,
    _cic_phase5_readiness,
    _cic_phase5_safe_int,
    _cic_phase5_task_preview,
    _cic_phase6_build,
    _cic_phase6_item,
    _cic_phase6_log_quality,
    _cic_phase6_missing_email_count,
    _cic_phase6_status,
    _cic_phase6_template_quality,
    _context_base,
    _users_by_ids,
    context,
    get_auto_scheduler_config,
    get_recent_logs,
    get_recipients,
    get_template,
    list_users,
)
























# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE3_DISPATCH_BEGIN


# Phase4J V29C CIC cic_context facade imports
from app.services.cic.cic_context import (
    _cic_auto_last_run_key,
    _cic_is_weekend,
    _cic_phase3_actor_label,
    _cic_phase3_last_result,
    _cic_phase3_make_result,
    _cic_phase3_public_error,
    _cic_phase3_store_result,
    _cic_phase3_task_label,
    _cic_phase5_actor,
    _cic_phase5_now_label,
    _cic_phase5_store_audit,
    _cic_phase6_bool,
    _cic_v40_create_system_notifications,
    _cic_v40_date_input,
    _cic_v40_days_until,
    _cic_v40_run_weekend_celebrations,
    _cic_v40_upcoming_special_days,
    _cic_v40_upcoming_users,
    _cic_v45_bool,
    _cic_v45_build_user_indexes,
    _cic_v45_ensure_schema,
    _cic_v45_existing_user_rows,
    _cic_v45_header_key,
    _cic_v45_norm,
    _cic_v45_norm_name,
    _cic_v45_parse_date,
    _cic_v45_text,
    _cic_weekday_name_tr,
    send_task,
)













# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE3_DISPATCH_END

# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_CONTROL_PANEL_BEGIN






















# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_CONTROL_PANEL_END

# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_FINAL_UAT_LIVE_READY_BEGIN















# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_FINAL_UAT_LIVE_READY_END

# BYS360_CIC_V3_0_MAIL_ENGINE_SYSTEM_SENDER_V1_1_BEGIN
# Kurumsal Bilgilendirme mail gönderiminde sistem MAIL/SMTP ayarları kullanılır.
# Bu blok bilerek dosyanın sonunda yer alır; varsa eski send_task tanımlarını güvenli biçimde ezer.













# BYS360_CIC_V3_0_MAIL_ENGINE_SYSTEM_SENDER_V1_1_END

# BYS360_CIC_V3_0_RECIPIENTS_SAVE_PERSISTENCE_V2
# Final robust recipient persistence override. Last definition wins at import time.


# BYS360_CIC_V3_0_SYSTEM_AUTO_MAIL_SCHEDULER_V1
# Sistem uzerinden aktif/pasif ve saat kontrollu otomatik mail zamanlayici.

# BYS360_CIC_V3_0_AUTO_MAIL_WEEKDAY_ONLY_V1
# Otomatik mail zamanlayicisi hafta sonu guvenlik kilidi.
# Cumartesi ve pazar gunleri otomatik mail gonderimi yapilmaz.











# PHASE3A_CIC_EXPLICIT_SAVE_SYSTEM_BEGIN
# PHASE3A_CIC_EXPLICIT_SAVE_SYSTEM_END

# PHASE3A_CIC_EXPLICIT_CONTEXT_BEGIN
# PHASE3A_CIC_EXPLICIT_CONTEXT_END



# Phase4J V31C CIC run_context facade imports
from app.services.cic.run_context import (
    _run_due_tasks_base,
    run_due_tasks,
)


# BYS360_CIC_V4_0_SMART_CELEBRATIONS_BEGIN
# Akilli Kutlama ve Otomatik Ozel Gun Bilgilendirme Motoru.
# Bu blok mevcut Kurumsal Bilgilendirme motorunu bozmadan genisletir.

from typing import Any as _cic_v40_Any

_CIC_V40_CELEBRATION_TASKS = {"staff_birthday", "work_anniversary", "special_day"}
_CIC_V40_SPECIAL_DAY_DEFAULTS = [
    {"date": "03-18", "name": "18 Mart Çanakkale Zaferi ve Şehitleri Anma Günü", "enabled": True, "target": "all_staff"},
    {"date": "04-23", "name": "23 Nisan Ulusal Egemenlik ve Çocuk Bayramı", "enabled": True, "target": "all_staff"},
    {"date": "05-19", "name": "19 Mayıs Atatürk'ü Anma, Gençlik ve Spor Bayramı", "enabled": True, "target": "all_staff"},
    {"date": "08-30", "name": "30 Ağustos Zafer Bayramı", "enabled": True, "target": "all_staff"},
    {"date": "10-29", "name": "29 Ekim Cumhuriyet Bayramı", "enabled": True, "target": "all_staff"},
    {"date": "12-01", "name": "Seyit Onbaşı Anma Günü", "enabled": True, "target": "all_staff"},
]

TASK_DEFINITIONS.update({
    "staff_birthday": {
        "category": "kutlama",
        "label": "Doğum Günü Kutlaması",
        "short_label": "Doğum Günü",
        "default_hour": 9,
        "default_minute": 0,
        "icon": "fa-cake-candles",
        "description": "Doğum günü olan aktif personele yaş bilgisi göstermeden kurumsal kutlama gönderir.",
        "recipient_group": "celebration_birthday",
        "subject": "Doğum Gününüz Kutlu Olsun",
        "body": """Sayın {ad_soyad},

Doğum gününüzü kutlar; sağlıklı, mutlu ve başarılı bir yaş dileriz.

Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı""",
    },
    "work_anniversary": {
        "category": "kutlama",
        "label": "Göreve Başlama Yıl Dönümü",
        "short_label": "Hizmet Yılı",
        "default_hour": 9,
        "default_minute": 15,
        "icon": "fa-award",
        "description": "Göreve başlama yıl dönümü olan personele kurumsal teşekkür ve kutlama gönderir.",
        "recipient_group": "celebration_anniversary",
        "subject": "Kurum Hizmet Yıl Dönümünüz Kutlu Olsun",
        "body": """Sayın {ad_soyad},

Kurumumuzdaki {hizmet_yili}. hizmet yılınızı kutlar; emekleriniz ve katkılarınız için teşekkür ederiz.

Nice başarılı yıllar dileriz.

Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı""",
    },
    "special_day": {
        "category": "kutlama",
        "label": "Özel Gün Kutlaması",
        "short_label": "Özel Gün",
        "default_hour": 10,
        "default_minute": 0,
        "icon": "fa-flag",
        "description": "Tanımlı resmi/kurumsal özel günlerde hedef kitleye kutlama veya anma mesajı gönderir.",
        "recipient_group": "celebration_special_day",
        "subject": "{ozel_gun_adi}",
        "body": """Sayın {ad_soyad},

{ozel_gun_adi} vesilesiyle iyi dileklerimizi sunarız.

Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı""",
    },
})

















# PHASE3A_CIC_EXPLICIT_ENSURE_DEFAULTS_BEGIN
# PHASE3A_CIC_EXPLICIT_ENSURE_DEFAULTS_END














# PHASE3A_CIC_EXPLICIT_RECIPIENT_RENDER_BEGIN


# PHASE3A_CIC_EXPLICIT_RECIPIENT_RENDER_END



# PHASE3A_CIC_EXPLICIT_SEND_TASK_BEGIN
# PHASE3A_CIC_EXPLICIT_SEND_TASK_END







def celebration_context(search: str | None = None) -> dict[str, _cic_v40_Any]:
    ensure_defaults()
    schema = ensure_celebration_schema()
    data = context(search)
    users = list_users(search=search, limit=1000)
    today_birthdays = _cic_v40_birthday_users()
    today_anniversaries = _cic_v40_anniversary_users()
    today_specials = _cic_v40_special_days_today()
    data.update({
        "active_tab": "celebrations",
        "celebration": {
            "schema": schema,
            "settings": {
                "celebrations_enabled": _cic_v40_setting_bool("celebrations_enabled", True),
                "birthday_enabled": _cic_v40_setting_bool("birthday_enabled", True),
                "work_anniversary_enabled": _cic_v40_setting_bool("work_anniversary_enabled", True),
                "special_day_enabled": _cic_v40_setting_bool("special_day_enabled", True),
                "system_notifications_enabled": _cic_v40_setting_bool("celebration_system_notifications_enabled", True),
                "include_weekend": _cic_v40_setting_bool("celebrations_include_weekend", False),
                "special_day_recipient_mode": get_setting(f"{BASE_KEY}.special_day_recipient_mode", "all_active") or "all_active",
            },
            "special_days": _cic_v40_special_days(),
            "special_days_json": _dumps_json(_cic_v40_special_days()),
            "today_birthdays": today_birthdays,
            "today_anniversaries": today_anniversaries,
            "today_specials": today_specials,
            "upcoming_birthdays": _cic_v40_upcoming_users("birthday", 30),
            "upcoming_anniversaries": _cic_v40_upcoming_users("anniversary", 30),
            "upcoming_special_days": _cic_v40_upcoming_special_days(45),
            "users": users,
            "stats": {
                "today_total": len(today_birthdays) + len(today_anniversaries) + len(today_specials),
                "birthday_count": len(today_birthdays),
                "anniversary_count": len(today_anniversaries),
                "special_day_count": len(today_specials),
                "upcoming_total": len(_cic_v40_upcoming_users("birthday", 30)) + len(_cic_v40_upcoming_users("anniversary", 30)) + len(_cic_v40_upcoming_special_days(45)),
            },
        },
    })
    return data




# PHASE3A_CIC_EXPLICIT_RUN_DUE_TASKS_BEGIN
# PHASE3A_CIC_EXPLICIT_RUN_DUE_TASKS_END


# BYS360_CIC_V4_0_SMART_CELEBRATIONS_END

# BYS360_CIC_V4_5_CELEBRATION_EXCEL_IMPORT_BEGIN
# Kutlama tarihleri için güvenli Excel ön kontrol ve uygulama motoru.




















def import_celebration_dates_from_excel(file_storage: object, *, apply: bool = False, actor_user_id: int | None = None) -> dict[str, object]:
    _cic_v45_ensure_schema()
    result: dict[str, object] = {"ok": True, "mode": "apply" if apply else "preview", "total_rows": 0, "matched": 0, "updated": 0, "unmatched": 0, "skipped": 0, "errors": [], "warnings": [], "preview_rows": []}
    if file_storage is None or not getattr(file_storage, "filename", ""):
        result["ok"] = False
        result["errors"].append("Excel dosyası seçilmedi.")
        return result
    filename = str(getattr(file_storage, "filename", ""))
    if not filename.lower().endswith((".xlsx", ".xlsm")):
        result["ok"] = False
        result["errors"].append("Sadece .xlsx veya .xlsm dosyası yüklenebilir.")
        return result
    try:
        from openpyxl import load_workbook as _cic_v45_load_workbook
    except Exception:
        result["ok"] = False
        result["errors"].append("Excel okuma kütüphanesi bulunamadı. openpyxl kurulumu gerekiyor.")
        return result
    try:
        stream = getattr(file_storage, "stream", file_storage)
        try:
            stream.seek(0)
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2682")
            pass
        wb = _cic_v45_load_workbook(stream, data_only=True, read_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        headers = next(rows_iter, None)
    except Exception as exc:
        result["ok"] = False
        result["errors"].append("Excel dosyası okunamadı: " + str(exc))
        return result
    if not headers:
        result["ok"] = False
        result["errors"].append("Excel dosyasında başlık satırı bulunamadı.")
        return result
    header_map: dict[int, str] = {}
    for idx, h in enumerate(headers):
        key = _cic_v45_header_key(h)
        if key and key not in header_map.values():
            header_map[idx] = key
    if "sicil_no" not in header_map.values() and "email" not in header_map.values() and "ad_soyad" not in header_map.values():
        result["ok"] = False
        result["errors"].append("Eşleştirme için Sicil No, E-posta veya Ad Soyad başlığı bulunmalı.")
        return result
    if "birth_date" not in header_map.values() and "hire_date" not in header_map.values() and "celebration_opt_out" not in header_map.values():
        result["ok"] = False
        result["errors"].append("Güncellenecek alan bulunamadı. Doğum Tarihi, İşe Başlama Tarihi veya Kutlama Dışı başlığı gerekli.")
        return result
    indexes = _cic_v45_build_user_indexes(_cic_v45_existing_user_rows())
    updates: list[dict[str, object]] = []
    from sqlalchemy import text as _sa_text
    for excel_row_no, row in enumerate(rows_iter, start=2):
        values = {key: row[idx] if idx < len(row) else None for idx, key in header_map.items()}
        if not any(_cic_v45_text(v) for v in values.values()):
            continue
        result["total_rows"] = int(result["total_rows"]) + 1
        sicil = _cic_v45_text(values.get("sicil_no"))
        email = _cic_v45_text(values.get("email")).lower()
        name = _cic_v45_text(values.get("ad_soyad")) or (_cic_v45_text(values.get("ad")) + " " + _cic_v45_text(values.get("soyad"))).strip()
        user = None
        match_by = ""
        if sicil and sicil in indexes["sicil"]:
            user = indexes["sicil"][sicil]; match_by = "Sicil No"
        elif email and email in indexes["email"]:
            user = indexes["email"][email]; match_by = "E-posta"
        else:
            n = _cic_v45_norm_name(name)
            if n and n in indexes["name"]:
                user = indexes["name"][n]; match_by = "Ad Soyad"
        if not user:
            result["unmatched"] = int(result["unmatched"]) + 1
            if len(result["warnings"]) < 25:
                result["warnings"].append(f"Satır {excel_row_no}: Personel eşleşmedi ({sicil or email or name or 'tanımsız'}).")
            continue
        birth_date = _cic_v45_parse_date(values.get("birth_date")) if "birth_date" in values else None
        hire_date = _cic_v45_parse_date(values.get("hire_date")) if "hire_date" in values else None
        opt_raw = values.get("celebration_opt_out") if "celebration_opt_out" in values else None
        opt_out = _cic_v45_bool(opt_raw)
        fields: dict[str, object] = {}
        if "birth_date" in values and values.get("birth_date") not in (None, ""):
            if birth_date:
                fields["birth_date"] = birth_date
            else:
                result["warnings"].append(f"Satır {excel_row_no}: Doğum tarihi okunamadı.")
        if "hire_date" in values and values.get("hire_date") not in (None, ""):
            if hire_date:
                fields["hire_date"] = hire_date
            else:
                result["warnings"].append(f"Satır {excel_row_no}: İşe başlama tarihi okunamadı.")
        if opt_raw not in (None, "") and opt_out is not None:
            fields["celebration_opt_out"] = bool(opt_out)
        if not fields:
            result["skipped"] = int(result["skipped"]) + 1
            continue
        result["matched"] = int(result["matched"]) + 1
        preview = {"row": excel_row_no, "user_id": user.get("id"), "match_by": match_by, "sicil_no": sicil or _cic_v45_text(user.get("sicil_no")), "ad_soyad": name or ((_cic_v45_text(user.get("ad")) + " " + _cic_v45_text(user.get("soyad"))).strip()), "birth_date": str(fields.get("birth_date") or ""), "hire_date": str(fields.get("hire_date") or ""), "celebration_opt_out": fields.get("celebration_opt_out") if "celebration_opt_out" in fields else ""}
        if len(result["preview_rows"]) < 30:
            result["preview_rows"].append(preview)
        if apply:
            updates.append({"id": int(user["id"]), "fields": fields})
    if apply and updates:
        with db.engine.begin() as conn:
            for item in updates:
                fields = item["fields"]
                set_sql = []
                params: dict[str, object] = {"id": item["id"]}
                for col, val in fields.items():
                    set_sql.append(f"{col} = :{col}")
                    params[col] = val
                if set_sql:
                    conn.execute(_sa_text("UPDATE users SET " + ", ".join(set_sql) + " WHERE id = :id"), params)
                    result["updated"] = int(result["updated"]) + 1
    if not apply:
        result["warnings"].insert(0, "Ön kontrol yapıldı; veritabanına kayıt yazılmadı.")
    else:
        result["warnings"].insert(0, f"Uygulama tamamlandı; {result['updated']} personel kaydı güncellendi.")
    return result
# BYS360_CIC_V4_5_CELEBRATION_EXCEL_IMPORT_END
