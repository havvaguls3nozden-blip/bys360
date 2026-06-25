# BYS360 CIC Component Design V26D
- Generated at: 2026-06-25T20:11:45
- Status: NEEDS_IMPORT_OR_CONSTANT_REVIEW
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 0259a41
- Target: app/services/corporate_information_center.py
- V26C status: NEEDS_MANUAL_COMPONENT_DESIGN
- V26C ready for facade split: False
- Closure function count: 14
- Recommended module: app/services/cic/config_context.py

## Closure Functions
- _now | line=159 | length=2
- _has_settings_table | line=163 | length=7
- get_setting | line=172 | length=7
- set_setting | line=181 | length=15
- _loads_json | line=198 | length=9
- _dumps_json | line=209 | length=2
- _ensure_defaults_base | line=220 | length=44
- get_config | line=266 | length=11
- _clean_ids | line=279 | length=11
- _weather | line=397 | length=23
- _format_weather | line=422 | length=12
- _clothing | line=436 | length=13
- _tomorrow_note | line=451 | length=4
- ensure_defaults | line=1686 | length=27

## Assignment Sources

### line 24 names=['GROUP_KEY']
```python
GROUP_KEY = "corporate_information_center"
```

### line 25 names=['BASE_KEY']
```python
BASE_KEY = "corporate_information_center"
```

### line 28 names=['TASK_DEFINITIONS']
```python
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
```

### line 1517 names=['_CIC_V40_SPECIAL_DAY_DEFAULTS']
```python
_CIC_V40_SPECIAL_DAY_DEFAULTS = [
    {"date": "03-18", "name": "18 Mart Çanakkale Zaferi ve Şehitleri Anma Günü", "enabled": True, "target": "all_staff"},
    {"date": "04-23", "name": "23 Nisan Ulusal Egemenlik ve Çocuk Bayramı", "enabled": True, "target": "all_staff"},
    {"date": "05-19", "name": "19 Mayıs Atatürk'ü Anma, Gençlik ve Spor Bayramı", "enabled": True, "target": "all_staff"},
    {"date": "08-30", "name": "30 Ağustos Zafer Bayramı", "enabled": True, "target": "all_staff"},
    {"date": "10-29", "name": "29 Ekim Cumhuriyet Bayramı", "enabled": True, "target": "all_staff"},
    {"date": "12-01", "name": "Seyit Onbaşı Anma Günü", "enabled": True, "target": "all_staff"},
]
```

## Import Sources

### line 3 names=['json']
```python
import json
```

### line 4 names=['ssl']
```python
import ssl
```

### line 6 names=['datetime']
```python
from datetime import datetime
```

### line 7 names=['Any']
```python
from typing import Any
```

### line 8 names=['urlopen']
```python
from urllib.request import urlopen
```

### line 13 names=['db']
```python
from app.extensions import db
```

### line 14 names=['SystemSetting']
```python
from app.models import SystemSetting, User
```

## Missing
- missing_assignments: []
- missing_imports: ['sa_inspect']

## sa_inspect Context
- line 165: `        from sqlalchemy import inspect as sa_inspect`
- line 166: `        return bool(sa_inspect(db.engine).has_table("system_settings"))`
- line 1658: `        from sqlalchemy import inspect as _sa_inspect, text as _sa_text`
- line 1659: `        inspector = _sa_inspect(db.engine)`
- line 2186: `        from sqlalchemy import inspect as _sa_inspect, text as _sa_text`
- line 2187: `        inspector = _sa_inspect(db.engine)`
- line 2204: `    from sqlalchemy import inspect as _sa_inspect, text as _sa_text`
- line 2205: `    inspector = _sa_inspect(db.engine)`

## exc Context Top 30
- line 18: `except Exception:  # pragma: no cover`
- line 19: `    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/corporate_information_center.py:20")`
- line 167: `    except Exception:`
- line 168: `        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/corporate_information_center.py:168")`
- line 204: `    except Exception:`
- line 205: `        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/corporate_information_center.py:204")`
- line 286: `        except Exception:`
- line 287: `            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:288")`
- line 300: `        except Exception:`
- line 301: `            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:301")`
- line 305: `        except Exception:`
- line 306: `            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:305")`
- line 342: `        except Exception:`
- line 343: `            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:354")`
- line 357: `    except Exception:`
- line 358: `        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/corporate_information_center.py:365")`
- line 375: `        except Exception:`
- line 376: `            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:386")`
- line 382: `    except Exception:`
- line 383: `        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/corporate_information_center.py:388")`
- line 416: `    except Exception as exc:`
- line 417: `        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:426")`
- line 418: `        msg = f"Güncel hava durumu verisi şu anda alınamadı. Kontrol notu: {exc}"`
- line 439: `    except Exception:`
- line 440: `        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:448")`
- line 460: `    except Exception:`
- line 461: `        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:468")`
- line 536: `    except Exception:`
- line 537: `        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:628")`
- line 546: `    except Exception:`

## Implementation Steps
- app/services/cic klasoru yoksa olustur ve __init__.py ekle.
- Closure fonksiyonlari ve gerekli sabitler yeni app/services/cic/config_context.py dosyasina tasinacak sekilde planla.
- corporate_information_center.py facade dosyasi olarak kalacak.
- Facade icinde yeni modülden ayni fonksiyon adlari import edilerek dis import uyumlulugu korunacak.
- Ilk uygulamada sadece 14 fonksiyonluk closure hedeflenecek; baska fonksiyonlara dokunulmayacak.
- Uygulama sonrasi python compile, hedef modül import smoke ve mimari audit calistirilacak.

## Risk Notes
- Sabitleri eski dosyadan yeni modüle import etmek circular import riski yaratabilir.
- Bu nedenle closure fonksiyonlariyla birlikte ilgili sabitlerin de yeni modüle tasinmasi daha guvenli olabilir.
- SystemSetting/db kullanimi veri tabanina bagli oldugu icin testler import seviyesinde tutulmali, DB yazma yapilmamali.
- sa_inspect yerel import veya eksik global import olabilir; V26E uygulama oncesi bu satir netlestirilmeli.

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
