# BYS360 CIC Save Context Preflight V30B
- Generated at: 2026-06-25T20:56:19
- Status: READY_FOR_FACADE_SPLIT
- Ready for split: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 37853bc
- Target: app/services/corporate_information_center.py
- Suggested module: app/services/cic/save_context.py
- Closure function count: 8 / 8
- Closure total lines: 178
- Needed assignments: ['BASE_KEY', 'TASK_DEFINITIONS']
- Missing functions: []
- Missing assignments: []
- Outside calls: []
- Used imports: ['Any', 'User', '_cic_auto_bool', '_cic_v40_bool', '_cic_v40_parse_date', '_clean_ids', '_dumps_json', '_now', 'db', 'get_config', 'get_setting', 'json', 'set_setting']
- Unknown external names: ['_sa_inspect', '_sa_text', 'exc', 'getlist_all']

## Closure Functions
- save_tasks | line=202 | length=19 | inside=[] | outside=[]
- save_templates | line=222 | length=7 | inside=[] | outside=[]
- _save_system_base | line=231 | length=5 | inside=[] | outside=[]
- save_recipients | line=433 | length=30 | inside=[] | outside=[]
- set_auto_scheduler_config | line=484 | length=22 | inside=[] | outside=[]
- save_system | line=508 | length=9 | inside=['_save_system_base', 'set_auto_scheduler_config'] | outside=[]
- ensure_celebration_schema | line=714 | length=30 | inside=[] | outside=[]
- save_celebration_settings | line=819 | length=56 | inside=['ensure_celebration_schema'] | outside=[]

## Assignment Sources

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

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
