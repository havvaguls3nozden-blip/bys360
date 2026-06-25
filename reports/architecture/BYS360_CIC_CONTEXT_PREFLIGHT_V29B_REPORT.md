# BYS360 CIC Context Preflight V29B
- Generated at: 2026-06-25T20:50:14
- Status: READY_FOR_FACADE_SPLIT
- Ready for split: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 5aaf414
- Target: app/services/corporate_information_center.py
- Suggested module: app/services/cic/cic_context.py
- Closure function count: 29 / 29
- Closure total lines: 356
- Needed assignments: ['BASE_KEY', 'TASK_DEFINITIONS', 'VERSION', '_CIC_V40_CELEBRATION_TASKS']
- Missing functions: []
- Missing assignments: []
- Outside calls: []
- Used imports: ['Any', 'User', '_cic_phase5_audit_list', '_cic_v40_Any', '_cic_v40_active_staff_candidates', '_cic_v40_date', '_cic_v40_mmdd', '_cic_v40_parse_date', '_cic_v40_service_year', '_cic_v40_setting_bool', '_cic_v40_special_days', '_cic_v40_today', '_cic_v40_user_date', '_cic_v45_date', '_cic_v45_datetime', '_cic_v45_re', '_cic_v45_timedelta', '_cic_v45_unicodedata', '_dumps_json', '_loads_json', '_now', '_recipients_for_task', '_render_template_text', '_send_task_base', '_user_name', 'datetime', 'db', 'get_auto_scheduler_config', 'get_config', 'get_setting', 'get_template', 'set_setting', 'time']
- Unknown external names: ['Notification', '_sa_inspect', '_sa_text']

## Closure Functions
- _cic_phase3_public_error | line=323 | length=14 | inside=[] | outside=[]
- _cic_phase3_task_label | line=339 | length=3 | inside=[] | outside=[]
- _cic_phase3_actor_label | line=344 | length=9 | inside=[] | outside=[]
- _cic_phase3_store_result | line=355 | length=7 | inside=['_cic_phase3_task_label'] | outside=[]
- _cic_phase3_make_result | line=364 | length=27 | inside=['_cic_phase3_actor_label', '_cic_phase3_task_label'] | outside=[]
- _cic_phase3_last_result | line=394 | length=3 | inside=[] | outside=[]
- _cic_phase5_now_label | line=405 | length=6 | inside=[] | outside=[]
- _cic_phase5_actor | line=413 | length=8 | inside=[] | outside=[]
- _cic_phase5_store_audit | line=427 | length=15 | inside=[] | outside=[]
- _cic_phase6_bool | line=457 | length=2 | inside=[] | outside=[]
- _cic_is_weekend | line=539 | length=3 | inside=[] | outside=[]
- _cic_weekday_name_tr | line=544 | length=7 | inside=[] | outside=[]
- _cic_auto_last_run_key | line=593 | length=2 | inside=[] | outside=[]
- _cic_v40_days_until | line=783 | length=11 | inside=[] | outside=[]
- _cic_v40_create_system_notifications | line=851 | length=45 | inside=[] | outside=[]
- send_task | line=898 | length=28 | inside=['_cic_v40_create_system_notifications'] | outside=[]
- _cic_v40_date_input | line=928 | length=3 | inside=[] | outside=[]
- _cic_v40_upcoming_users | line=933 | length=20 | inside=['_cic_v40_days_until'] | outside=[]
- _cic_v40_upcoming_special_days | line=955 | length=9 | inside=['_cic_v40_days_until'] | outside=[]
- _cic_v40_run_weekend_celebrations | line=1065 | length=29 | inside=['_cic_auto_last_run_key', 'send_task'] | outside=[]
- _cic_v45_text | line=1128 | length=2 | inside=[] | outside=[]
- _cic_v45_norm | line=1132 | length=7 | inside=['_cic_v45_text'] | outside=[]
- _cic_v45_norm_name | line=1141 | length=5 | inside=['_cic_v45_text'] | outside=[]
- _cic_v45_bool | line=1148 | length=10 | inside=['_cic_v45_norm', '_cic_v45_text'] | outside=[]
- _cic_v45_parse_date | line=1160 | length=25 | inside=['_cic_v45_text'] | outside=[]
- _cic_v45_header_key | line=1187 | length=12 | inside=['_cic_v45_norm'] | outside=[]
- _cic_v45_ensure_schema | line=1201 | length=17 | inside=[] | outside=[]
- _cic_v45_existing_user_rows | line=1220 | length=11 | inside=[] | outside=[]
- _cic_v45_build_user_indexes | line=1233 | length=16 | inside=['_cic_v45_norm_name', '_cic_v45_text'] | outside=[]

## Assignment Sources

### line 23 names=['VERSION']
```python
VERSION = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE1"
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

### line 709 names=['_CIC_V40_CELEBRATION_TASKS']
```python
_CIC_V40_CELEBRATION_TASKS = {"staff_birthday", "work_anniversary", "special_day"}
```

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
