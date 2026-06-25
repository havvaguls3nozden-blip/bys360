# BYS360 CIC Send Context Preflight V28B
- Generated at: 2026-06-25T20:43:19
- Status: READY_FOR_FACADE_SPLIT
- Ready for split: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 72459fb
- Target: app/services/corporate_information_center.py
- Suggested module: app/services/cic/send_context.py
- Closure function count: 26 / 26
- Closure total lines: 421
- Needed assignments: ['BASE_KEY', 'TASK_DEFINITIONS', '_CIC_V40_SPECIAL_DAY_DEFAULTS']
- Missing functions: []
- Missing assignments: []
- Outside calls: []
- Used imports: ['User', '_active_staff_users', '_cic_v40_date', '_cic_v40_datetime', '_dumps_json', '_loads_json', '_now', '_weather', 'context', 'current_app', 'db', 'ensure_defaults', 'get_config', 'get_recipients', 'get_setting', 'get_template', 'set_setting', 'time']
- Unknown external names: ['MIMEMultipart', 'MIMEText', '_ca', 'create_mail_log', 'exc', 'log_exc', 'smtplib']

## Closure Functions
- _user_name | line=238 | length=7 | inside=[] | outside=[]
- _dashboard_counts | line=290 | length=12 | inside=[] | outside=[]
- _render_template_text_base | line=304 | length=19 | inside=['_dashboard_counts', '_user_name'] | outside=[]
- _recipients_for_task_base | line=327 | length=6 | inside=[] | outside=[]
- _cic_v11_bool | line=492 | length=11 | inside=[] | outside=[]
- _cic_v11_get_setting_value | line=505 | length=35 | inside=[] | outside=[]
- _cic_v11_clean_header | line=542 | length=2 | inside=[] | outside=[]
- _cic_v11_normalize_email | line=546 | length=5 | inside=['_cic_v11_clean_header'] | outside=[]
- _cic_v11_mail_settings | line=553 | length=24 | inside=['_cic_v11_bool', '_cic_v11_get_setting_value'] | outside=[]
- _cic_v11_send_email_direct | line=579 | length=52 | inside=['_cic_v11_clean_header', '_cic_v11_mail_settings', '_cic_v11_normalize_email'] | outside=[]
- _send_task_base | line=633 | length=99 | inside=['_cic_v11_mail_settings', '_cic_v11_normalize_email', '_cic_v11_send_email_direct', '_recipients_for_task', '_render_template_text'] | outside=[]
- _cic_v40_bool | line=1015 | length=7 | inside=[] | outside=[]
- _cic_v40_parse_date | line=1024 | length=17 | inside=[] | outside=[]
- _cic_v40_user_date | line=1043 | length=11 | inside=['_cic_v40_parse_date'] | outside=[]
- _cic_v40_today | line=1056 | length=10 | inside=[] | outside=[]
- _cic_v40_mmdd | line=1068 | length=2 | inside=[] | outside=[]
- _cic_v40_setting_bool | line=1085 | length=2 | inside=['_cic_v40_bool'] | outside=[]
- _cic_v40_special_days | line=1123 | length=19 | inside=['_cic_v40_bool'] | outside=[]
- _cic_v40_special_days_today | line=1144 | length=3 | inside=['_cic_v40_mmdd', '_cic_v40_special_days', '_cic_v40_today'] | outside=[]
- _cic_v40_active_staff_candidates | line=1149 | length=12 | inside=[] | outside=[]
- _cic_v40_birthday_users | line=1163 | length=10 | inside=['_cic_v40_active_staff_candidates', '_cic_v40_mmdd', '_cic_v40_setting_bool', '_cic_v40_today', '_cic_v40_user_date'] | outside=[]
- _cic_v40_service_year | line=1175 | length=9 | inside=['_cic_v40_today', '_cic_v40_user_date'] | outside=[]
- _cic_v40_anniversary_users | line=1186 | length=10 | inside=['_cic_v40_active_staff_candidates', '_cic_v40_mmdd', '_cic_v40_service_year', '_cic_v40_setting_bool', '_cic_v40_today', '_cic_v40_user_date'] | outside=[]
- _cic_v40_special_day_users | line=1198 | length=13 | inside=['_cic_v40_active_staff_candidates', '_cic_v40_setting_bool', '_cic_v40_special_days_today'] | outside=[]
- _recipients_for_task | line=1213 | length=11 | inside=['_cic_v40_anniversary_users', '_cic_v40_birthday_users', '_cic_v40_special_day_users', '_recipients_for_task_base'] | outside=[]
- _render_template_text | line=1226 | length=13 | inside=['_cic_v40_service_year', '_cic_v40_special_days_today', '_render_template_text_base'] | outside=[]

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

### line 952 names=['_CIC_V40_SPECIAL_DAY_DEFAULTS']
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

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
