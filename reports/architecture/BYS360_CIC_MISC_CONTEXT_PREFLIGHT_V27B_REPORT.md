# BYS360 CIC Misc Context Preflight V27B
- Generated at: 2026-06-25T20:22:45
- Status: READY_FOR_FACADE_SPLIT
- Ready for split: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: b242372
- Target: app/services/corporate_information_center.py
- Suggested module: app/services/cic/misc_context.py
- Closure function count: 23 / 23
- Closure total lines: 450
- Needed assignments: ['BASE_KEY', 'TASK_DEFINITIONS']
- Missing functions: []
- Missing assignments: []
- Outside calls: []
- Used imports: ['Any', 'User', '_has_settings_table', '_loads_json', 'current_app', 'ensure_defaults', 'get_config', 'get_setting', 'or_']
- Unknown external names: ['MailLog', 'add', 'send_email']

## Closure Functions
- list_users | line=247 | length=23 | inside=[] | outside=[]
- _users_by_ids | line=272 | length=6 | inside=[] | outside=[]
- _active_staff_users | line=280 | length=15 | inside=[] | outside=[]
- get_recipients | line=297 | length=8 | inside=['_active_staff_users', '_users_by_ids'] | outside=[]
- get_template | line=350 | length=6 | inside=[] | outside=[]
- get_recent_logs | line=437 | length=7 | inside=[] | outside=[]
- _cic_phase5_safe_int | line=455 | length=6 | inside=[] | outside=[]
- _cic_phase5_last_result | line=481 | length=7 | inside=[] | outside=[]
- _cic_phase5_audit_list | line=490 | length=7 | inside=[] | outside=[]
- _cic_phase5_mail_health | line=516 | length=26 | inside=[] | outside=[]
- _cic_phase5_log_metrics | line=544 | length=48 | inside=[] | outside=[]
- _cic_phase5_readiness | line=594 | length=33 | inside=['_cic_phase5_last_result', '_cic_phase5_mail_health'] | outside=[]
- _cic_phase5_task_preview | line=629 | length=18 | inside=['_cic_phase5_safe_int'] | outside=[]
- _context_base | line=648 | length=53 | inside=['_cic_phase5_audit_list', '_cic_phase5_last_result', '_cic_phase5_log_metrics', '_cic_phase5_mail_health', '_cic_phase5_readiness', '_cic_phase5_task_preview', 'get_recent_logs', 'get_recipients', 'get_template', 'list_users'] | outside=[]
- _cic_phase6_status | line=711 | length=4 | inside=[] | outside=[]
- _cic_phase6_item | line=717 | length=9 | inside=['_cic_phase6_status'] | outside=[]
- _cic_phase6_missing_email_count | line=728 | length=11 | inside=[] | outside=[]
- _cic_phase6_template_quality | line=741 | length=16 | inside=['_cic_phase6_item'] | outside=[]
- _cic_phase6_log_quality | line=759 | length=10 | inside=['_cic_phase6_item'] | outside=[]
- _cic_phase6_build | line=771 | length=90 | inside=['_cic_phase6_item', '_cic_phase6_log_quality', '_cic_phase6_missing_email_count', '_cic_phase6_template_quality'] | outside=[]
- _cic_auto_bool | line=1155 | length=7 | inside=[] | outside=[]
- get_auto_scheduler_config | line=1178 | length=18 | inside=['_cic_auto_bool'] | outside=[]
- context | line=1234 | length=22 | inside=['_cic_phase6_build', '_context_base', 'get_auto_scheduler_config'] | outside=[]

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
