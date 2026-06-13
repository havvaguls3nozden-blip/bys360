from __future__ import annotations



from copy import deepcopy
from typing import Any

# BYS360 CIC task contract extracted from legacy corporate_information_center.py.
# This module is intentionally data-only; it must not send mail, query recipients,
# or import facade/mail_scheduler_service. P19A keeps runtime behavior unchanged.

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

# Legacy TASK_DEFINITIONS extension block preserved verbatim.
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

def get_base_key() -> str:
    """Return the CIC settings namespace key."""
    return str(BASE_KEY)


def get_task_definitions() -> dict[str, dict[str, Any]]:
    """Return a defensive copy of task definitions for read-only callers."""
    return deepcopy(TASK_DEFINITIONS)


def get_task_definition(task_key: str) -> dict[str, Any] | None:
    """Return a defensive copy of a single task definition."""
    meta = TASK_DEFINITIONS.get(task_key)
    return deepcopy(meta) if isinstance(meta, dict) else None


def task_keys() -> tuple[str, ...]:
    """Return task keys in definition order."""
    return tuple(TASK_DEFINITIONS.keys())


def contract_snapshot() -> dict[str, Any]:
    """Small smoke-test friendly summary of the contract."""
    return {
        "base_key": get_base_key(),
        "task_count": len(TASK_DEFINITIONS),
        "task_keys": list(TASK_DEFINITIONS.keys()),
    }


__all__ = [
    "BASE_KEY",
    "TASK_DEFINITIONS",
    "get_base_key",
    "get_task_definitions",
    "get_task_definition",
    "task_keys",
    "contract_snapshot",
]
