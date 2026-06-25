# BYS360 CIC Run Context Preflight V31B
- Generated at: 2026-06-25T21:03:38
- Status: READY_FOR_FACADE_SPLIT
- Ready for split: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: f9b29cf
- Target: app/services/corporate_information_center.py
- Suggested module: app/services/cic/run_context.py
- Closure function count: 2 / 2
- Closure total lines: 124
- Projected target lines after split: 757
- Would go under 800: True
- Needed assignments: ['TASK_DEFINITIONS']
- Missing functions: []
- Missing assignments: []
- Outside calls: []
- Used imports: ['_cic_auto_last_run_key', '_cic_is_weekend', '_cic_typing_any', '_cic_v40_Any', '_cic_v40_run_weekend_celebrations', '_cic_weekday_name_tr', '_now', 'db', 'ensure_defaults', 'get_auto_scheduler_config', 'get_config', 'get_setting', 'send_task', 'set_setting']
- Unknown external names: []

## Closure Functions
- _run_due_tasks_base | line=444 | length=104 | inside=[] | outside=[]
- run_due_tasks | line=712 | length=20 | inside=['_run_due_tasks_base'] | outside=[]

## Assignment Sources

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
