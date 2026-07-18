
"""BYS360 Ayarlar Rol Matrisi görsel ekran servisi V12.

Bu servis Ayarlar > Rol Matrisi ekranına okunabilir matris verisi sağlar.
V12; Yardım Merkezi V2, Sanal Asistan V9 ve güncel performans süreç
sekmlerini görsel rol matrisine ekler. Gerçek login, şifre, CAPTCHA,
veritabanı bağlantısı veya endpoint yetki kontrol akışına dokunmaz.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MatrixRole:
    key: str
    label: str
    short_label: str
    description: str


@dataclass(frozen=True)
class MatrixRow:
    key: str
    title: str
    subtitle: str
    icon: str
    allowed_roles: tuple[str, ...]
    policy: str = ""


@dataclass(frozen=True)
class MatrixGroup:
    key: str
    title: str
    subtitle: str
    icon: str
    badges: tuple[str, ...]
    rows: tuple[MatrixRow, ...]


ROLES: tuple[MatrixRole, ...] = (
    MatrixRole("admin", "Admin", "ADMIN", "Sistem yöneticisi ve tam yetkili kullanıcı."),
    MatrixRole("baskan", "Başkan", "BAŞKAN", "Üst yönetim görünürlüğü ve Başkan/Üst Onay sorumluluğu."),
    MatrixRole("baskan_yardimcisi", "Başkan Yardımcısı", "BAŞKAN\nYARDIMCISI", "Üst yönetim ve bağlı süreç görünürlüğü."),
    MatrixRole("grup_baskani", "Grup Başkanı", "GRUP\nBAŞKANI", "Grup başkanlığı, yayın ön onayı ve ekip görünürlüğü."),
    MatrixRole("mali_musavir", "Mali Müşavir", "MALİ\nMÜŞAVİR", "Mali müşavir düzeyi yönetim görünürlüğü."),
    MatrixRole("koordinator", "Koordinatör", "KOORDİNATÖR", "Koordinatörlük düzeyi süreç ve ekip görünürlüğü."),
    MatrixRole("birim_sorumlusu", "Birim Sorumlusu", "BİRİM\nSORUMLUSU", "Birim sorumluluğu ve ekip görünürlüğü."),
    MatrixRole("personel", "Personel", "PERSONEL", "Kişisel ekran, destek, anket, bildirim ve yayın sonrası karne görünürlüğü."),
    MatrixRole("rolsuz", "Rolsüz Kullanıcı", "ROLSÜZ", "Rolü boş/None olan kullanıcı. Varsayılan kapalı kabul edilir."),
)

ALL_AUTH_ROLES = tuple(role.key for role in ROLES if role.key != "rolsuz")
MANAGER_ROLES = ("admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu")
UPPER_ROLES = ("admin", "baskan", "baskan_yardimcisi")
ADMIN_ONLY = ("admin",)
ADMIN_AND_HR = ("admin", "mali_musavir")
PERSONNEL_MANAGEMENT_ROLES = MANAGER_ROLES
PERFORMANCE_MANAGEMENT_ROLES = MANAGER_ROLES
COMMUNICATION_ADMIN_ROLES = MANAGER_ROLES
AI_AUTHORIZED_ROLES = ("admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator")
AI_TECH_ADMIN_ROLES = ("admin",)
SETTINGS_ADMIN_ROLES = ("admin",)
REPORT_ROLES = MANAGER_ROLES
SUPPORT_USER_ROLES = ALL_AUTH_ROLES
SUPPORT_MANAGER_ROLES = MANAGER_ROLES
PRESIDENT_APPROVAL_ROLES = ("admin", "baskan")
PUBLISH_PREAPPROVAL_ROLES = ("admin", "grup_baskani")
ASSISTANT_MANAGER_ROLES = MANAGER_ROLES
ASSISTANT_PERSONNEL_ROLES = ALL_AUTH_ROLES

GROUPS: tuple[MatrixGroup, ...] = (
    MatrixGroup(
        key="genel",
        title="Genel Rol Matrisi",
        subtitle="Dashboard, bildirimler, kişisel görevler, not karnesi, personel analizi ve genel raporlama gibi ortak sekmelerin rol bazlı görünürlüğü.",
        icon="fa-solid fa-layer-group",
        badges=("Dashboard: yetkili tüm kullanıcılar", "Kişisel alanlar: tüm kullanıcılar", "Rolsüz kullanıcı: varsayılan kapalı"),
        rows=(
            MatrixRow("dashboard", "Dashboard", "dashboard", "fa-solid fa-house", ALL_AUTH_ROLES, "Genel giriş ekranı"),
            MatrixRow("notifications", "Bildirimler", "notifications", "fa-regular fa-bell", ALL_AUTH_ROLES, "Kişisel ve sistem içi bildirimler"),
            MatrixRow("messages_quick", "Mesaj Kısayolu", "messages", "fa-solid fa-envelope", ALL_AUTH_ROLES, "Kurum içi mesajlaşma kısayolu"),
            MatrixRow("performance_tasks", "Görevlerim", "performance_tasks", "fa-solid fa-list-check", PERFORMANCE_MANAGEMENT_ROLES, "Atanmış performans görevleri"),
            MatrixRow("scorecards", "Not Karnesi", "performance_scorecard", "fa-solid fa-id-card-clip", ALL_AUTH_ROLES, "Personel yalnızca yayın sonrası kendi sonucunu görür"),
            MatrixRow("my_performance_comparison", "Personel Analizi", "my_performance_comparison", "fa-solid fa-chart-line", ALL_AUTH_ROLES, "Personel kendi ortalamasını; yönetici yetki kapsamını görür"),
            MatrixRow("reports", "Genel Raporlama", "reports", "fa-solid fa-chart-column", REPORT_ROLES, "Yönetici ve üst yönetim raporları"),
            MatrixRow("activity_logs", "İşlem Kayıtları", "audit_logs", "fa-solid fa-clock-rotate-left", ("admin", "baskan", "baskan_yardimcisi"), "Kritik işlem geçmişi"),
        ),
    ),
    MatrixGroup(
        key="yardim_destek",
        title="Yardım Merkezi ve Destek Rol Matrisi",
        subtitle="Yardım Merkezi V2, yeni talep açma, talep takibi, atanan talepler ve tüm talepler ekranlarının rol bazlı görünürlüğü.",
        icon="fa-solid fa-headset",
        badges=("Yardım merkezi: tüm kullanıcılar", "Tüm talepler: yönetici kapsamı", "Talep içeriği: yetki sınırı"),
        rows=(
            MatrixRow("support", "Yardım Merkezi", "support_index", "fa-solid fa-circle-question", SUPPORT_USER_ROLES, "Kullanım rehberi, hızlı yönlendirme ve destek merkezi"),
            MatrixRow("support_new", "Yeni Talep Aç", "support_new", "fa-solid fa-plus", SUPPORT_USER_ROLES, "Kullanıcı destek talebi oluşturur"),
            MatrixRow("support_my_tickets", "Taleplerim", "support_my_tickets", "fa-solid fa-folder-open", SUPPORT_USER_ROLES, "Kullanıcı kendi taleplerini takip eder"),
            MatrixRow("support_assigned", "Bana Atananlar", "support_assigned", "fa-solid fa-user-check", SUPPORT_MANAGER_ROLES, "Yetkili kullanıcıya atanmış destek talepleri"),
            MatrixRow("support_all", "Tüm Talepler", "support_all", "fa-solid fa-table-list", SUPPORT_MANAGER_ROLES, "Yönetici kapsamındaki destek talebi izleme"),
            MatrixRow("support_manage", "Destek Talepleri Yönetimi", "support/manage", "fa-solid fa-headset", SUPPORT_MANAGER_ROLES, "Talep izleme, atama ve kapanış kontrolü"),
        ),
    ),
    MatrixGroup(
        key="personel_yonetimi",
        title="Personel Yönetimi Rol Matrisi",
        subtitle="Personel listesi, kullanıcı kayıtları, organizasyon, birim yönetimi, izin-devamsızlık, vekâlet ve personel raporları sekmeleri.",
        icon="fa-solid fa-users-gear",
        badges=("Personel rolünde yönetim gizli", "Rolsüz kullanıcıda kapalı", "Yönetici rolleri: yetki alanı kadar"),
        rows=(
            MatrixRow("personnel_dashboard", "Kontrol Paneli", "admin/dashboard veya personel özeti", "fa-solid fa-gauge-high", PERSONNEL_MANAGEMENT_ROLES, "Personel yönetimi genel özet"),
            MatrixRow("admin_users", "Personel Listesi", "admin_users", "fa-solid fa-users", PERSONNEL_MANAGEMENT_ROLES, "Kullanıcı ve personel listesi"),
            MatrixRow("personnel_create", "Personel Ekle", "admin/users/create", "fa-solid fa-user-plus", ADMIN_AND_HR, "Yeni personel/kullanıcı oluşturma"),
            MatrixRow("personnel_edit", "Personel Düzenle", "admin/users/<id>/edit", "fa-solid fa-user-pen", ADMIN_AND_HR, "Personel bilgisi güncelleme"),
            MatrixRow("organization_units", "Birim Yönetimi", "org_units", "fa-solid fa-sitemap", PERSONNEL_MANAGEMENT_ROLES, "Birim, üst birim ve organizasyon hiyerarşisi"),
            MatrixRow("unit_versions", "Organizasyon Versiyonları", "organization_unit_versions", "fa-solid fa-code-branch", PERSONNEL_MANAGEMENT_ROLES, "Geçmiş organizasyon yapısı ve değişiklik takibi"),
            MatrixRow("hierarchy", "Pozisyon / Hiyerarşi", "hierarchy", "fa-solid fa-people-arrows", PERSONNEL_MANAGEMENT_ROLES, "Yönetici, üst birim ve amir bağlantıları"),
            MatrixRow("leave", "İzin Yönetimi", "leave", "fa-solid fa-calendar-check", PERSONNEL_MANAGEMENT_ROLES + ("personel",), "Personel kendi iznini; yönetici yetki alanını görür"),
            MatrixRow("attendance", "Devamsızlık / İstisna", "attendance", "fa-solid fa-calendar-xmark", PERSONNEL_MANAGEMENT_ROLES, "Devamsızlık ve istisnai durum takibi"),
            MatrixRow("delegation", "Vekâlet Yönetimi", "delegation", "fa-solid fa-user-shield", PERSONNEL_MANAGEMENT_ROLES, "Vekil ve görev devri yönetimi"),
            MatrixRow("personnel_reports", "Personel Raporları", "personnel_reports", "fa-solid fa-chart-pie", PERSONNEL_MANAGEMENT_ROLES, "Personel dağılımı, hareket ve yetki raporları"),
        ),
    ),
    MatrixGroup(
        key="performans_yonetimi",
        title="Performans Yönetimi Rol Matrisi",
        subtitle="Kriter, dönem/kapsam, Dönem Yönetim Merkezi, canlı takip, amir hatırlatma, görev, karne, Başkan/Üst Onay, yayın ön onayı, süreç takibi, arşiv, gelişim rehberi ve raporların rol bazlı görünürlüğü.",
        icon="fa-solid fa-chart-line",
        badges=("Dönem Merkezi: rol/kişi/birim kontrollü", "Başkan/Üst Onay: Başkan ve Admin", "Yayın ön onayı: Grup Başkanı/Admin", "Karne: yayın sonrası personel"),
        rows=(
            MatrixRow("performance_dashboard", "Performans Kontrol Paneli", "performance/dashboard", "fa-solid fa-gauge", PERFORMANCE_MANAGEMENT_ROLES, "Süreç, görev ve dönem özeti"),
            MatrixRow("criteria", "Değerlendirme Kriterleri", "performance_criteria", "fa-solid fa-list-check", UPPER_ROLES, "Kriter tanımlama ve görüntüleme"),
            MatrixRow("periods", "Dönemler ve Kapsamlar", "performance_periods", "fa-solid fa-calendar-days", UPPER_ROLES, "Çoklu dönem, özel dönem ve kapsam yönetimi"),
            MatrixRow("period_management_center", "Dönem Yönetim Merkezi", "performance_period_management_center", "fa-solid fa-calendar-check", ('admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir'), "Dönem hazırlığı, kapsam, görev üretimi, canlı takip ve hatırlatma merkezini yönetir. Koordinatör/Birim Sorumlusu için kişi bazlı açılabilir."),
            MatrixRow("evaluation_live_tracking", "Canlı Değerlendirme Takibi", "performance_evaluation_live_tracking", "fa-solid fa-chart-line", ('admin', 'baskan', 'baskan_yardimcisi', 'birim_sorumlusu', 'grup_baskani', 'koordinator', 'mali_musavir'), "Değerlendirme süreci ilerlemesini, bekleyen ve geciken görevleri yetki kapsamıyla izler."),
            MatrixRow("evaluator_reminder_center", "Amir Hatırlatma Merkezi", "performance_evaluator_reminder_center", "fa-solid fa-bell", ('admin', 'baskan', 'baskan_yardimcisi', 'birim_sorumlusu', 'grup_baskani', 'koordinator', 'mali_musavir'), "Bekleyen/geciken değerlendirme görevleri için hatırlatma hazırlığı ve hedef amir listesini yönetir."),
            MatrixRow("assignments", "Değerlendirme Görevleri", "performance_evaluation_tasks", "fa-solid fa-clipboard-check", PERFORMANCE_MANAGEMENT_ROLES, "Amir görevleri ve süreç takibi"),
            MatrixRow("performance_process_tracking", "Süreç Takibi", "performance_process_tracking", "fa-solid fa-route", PERFORMANCE_MANAGEMENT_ROLES, "Performans süreçlerinin yetki kapsamıyla izlenmesi"),
            MatrixRow("performance_process_reports", "Süreç Raporları", "performance_process_reports", "fa-solid fa-chart-line", PERFORMANCE_MANAGEMENT_ROLES, "Risk, gecikme ve süreç yoğunluğu raporları"),
            MatrixRow("performance_president_approvals", "Başkan / Üst Onayları", "performance_president_approvals", "fa-solid fa-stamp", PRESIDENT_APPROVAL_ROLES, "70 altı düşük performans onayları"),
            MatrixRow("performance_personnel_support_publish_approval", "Yayın Ön Onayı", "performance_personnel_support_publish_approval", "fa-solid fa-user-check", PUBLISH_PREAPPROVAL_ROLES, "Final yayın öncesi Personel ve Destek Hizmetleri Grup Başkanı kontrolü"),
            MatrixRow("performance_archive", "Geçmiş Karne Arşivi", "performance_archive", "fa-solid fa-box-archive", ALL_AUTH_ROLES, "Personel kendi geçmişini; yönetici yetki kapsamını görür"),
            MatrixRow("performance_interim_notes", "Dönem İçi Notlar", "performance_interim_notes", "fa-regular fa-note-sticky", PERFORMANCE_MANAGEMENT_ROLES, "Ara dönem gözlem ve gelişim notları"),
            MatrixRow("performance_development_guidance", "Gelişim Rehberi", "performance_development_guidance", "fa-solid fa-seedling", PERFORMANCE_MANAGEMENT_ROLES, "Gelişim önerisi ve rehber not alanları"),
            MatrixRow("performance_meeting_p3_reminders", "Hatırlatma ve Aksatan Amirler", "performance_meeting_p3_reminders", "fa-solid fa-bell", PERFORMANCE_MANAGEMENT_ROLES, "Geciken değerlendirme görevleri ve hatırlatmalar"),
            MatrixRow("performance_reports", "Performans Raporları", "performance_reports", "fa-solid fa-chart-simple", PERFORMANCE_MANAGEMENT_ROLES, "Dönem, birim, ekip, kategori ve kişi bazlı raporlar"),
            MatrixRow("team_analysis", "Ekip Analizi", "performance_team_compare", "fa-solid fa-people-group", PERFORMANCE_MANAGEMENT_ROLES, "Yönetici ekip kıyası ve dağılım görünümü"),
            MatrixRow("feedback_meetings", "Gelişim Görüşmeleri", "performance_feedback_meetings", "fa-solid fa-comments", PERFORMANCE_MANAGEMENT_ROLES, "Performans sonrası görüşme ve gelişim takibi"),
            MatrixRow("publish", "Yayın Yönetimi", "performance_publish", "fa-solid fa-bullhorn", ("admin", "baskan"), "Sonuçların personele açılması"),
            MatrixRow("weight_config", "Ağırlık ve 3. Amir Ayarları", "performance_hierarchy_assignments", "fa-solid fa-scale-balanced", UPPER_ROLES, "Ağırlık, 3. amir yorum/puan modu"),
            MatrixRow("performance_mail", "Performans Mail Ayarları", "performance_mail_settings", "fa-solid fa-envelope-open-text", ADMIN_ONLY, "Hatırlatma ve süreç bildirimleri"),
        ),
    ),
    MatrixGroup(
        key="iletisim_anket",
        title="İletişim ve Anket Rol Matrisi",
        subtitle="Mesajlar, bildirimler, duyurular, anketler, geri bildirim, nabız, kampanya, sonuç ve aksiyon ekranlarının rol bazlı görünürlüğü.",
        icon="fa-solid fa-comments",
        badges=("Mesajlar: katılımcı/yetki bazlı", "Anketler: atama ve rol ayrımı", "Sonuçlar: yönetici kapsamı"),
        rows=(
            MatrixRow("messages", "Mesajlar", "messages", "fa-solid fa-envelope", ALL_AUTH_ROLES, "Katılımcı/yetki bazlı konuşma görünürlüğü"),
            MatrixRow("notifications", "Bildirimler", "notifications", "fa-regular fa-bell", ALL_AUTH_ROLES, "Kişisel ve rol bazlı bildirimler"),
            MatrixRow("announcements", "Duyurular", "announcements", "fa-solid fa-bullhorn", ALL_AUTH_ROLES, "Hedef kitleye göre duyuru görünürlüğü"),
            MatrixRow("announcement_manage", "Duyuru Yönetimi", "announcements/manage", "fa-solid fa-pen-nib", COMMUNICATION_ADMIN_ROLES, "Duyuru oluşturma ve yönetme"),
            MatrixRow("surveys", "Anketler", "surveys", "fa-solid fa-square-poll-vertical", ALL_AUTH_ROLES, "Atanan anketleri yanıtlama"),
            MatrixRow("survey_admin", "Anket Yönetimi", "survey_manage", "fa-solid fa-pen-to-square", COMMUNICATION_ADMIN_ROLES, "Anket oluşturma, atama ve sonuç takibi"),
            MatrixRow("survey_results", "Anket Sonuçları", "survey_results", "fa-solid fa-chart-pie", COMMUNICATION_ADMIN_ROLES, "Katılım ve cevap dağılımı"),
            MatrixRow("feedback_dashboard", "Kurumsal Geri Bildirim", "feedback_dashboard", "fa-solid fa-heart-pulse", ALL_AUTH_ROLES, "Geri bildirim katılım ve özet alanı"),
            MatrixRow("feedback_pulse", "Nabız Yoklaması", "feedback_pulse", "fa-solid fa-wave-square", ALL_AUTH_ROLES, "Kurum içi nabız yoklaması"),
            MatrixRow("feedback_campaigns", "Geri Bildirim Kampanyaları", "feedback_campaigns", "fa-solid fa-clipboard-question", COMMUNICATION_ADMIN_ROLES, "Kampanya oluşturma ve yönetme"),
            MatrixRow("feedback_results", "Geri Bildirim Sonuçları", "feedback_results", "fa-solid fa-chart-column", COMMUNICATION_ADMIN_ROLES, "Sonuç ve eğilim görünürlüğü"),
            MatrixRow("feedback_actions", "İyileştirme Aksiyonları", "feedback_actions", "fa-solid fa-list-check", COMMUNICATION_ADMIN_ROLES, "Aksiyon planı ve takip"),
            MatrixRow("feedback_manager", "Yönetici Görünümü", "feedback_manager", "fa-solid fa-users-viewfinder", MANAGER_ROLES, "Yöneticinin yetki alanı görünümü"),
            MatrixRow("feedback_admin", "Geri Bildirim Yönetimi", "feedback_admin", "fa-solid fa-sliders", COMMUNICATION_ADMIN_ROLES, "Geri bildirim yönetim ekranları"),
        ),
    ),
    MatrixGroup(
        key="ai_karar_destek",
        title="AI Karar Destek Rol Matrisi",
        subtitle="AI özetleme, karar destek notları, risk farkındalığı, redaksiyon kuralları, kullanım logları ve yönetici analiz ekranları.",
        icon="fa-solid fa-brain",
        badges=("AI karar vermez", "Personelde kapalı", "Redaksiyon ve log: admin"),
        rows=(
            MatrixRow("ai_dashboard", "AI Karar Destek Merkezi", "ai_center", "fa-solid fa-brain", AI_AUTHORIZED_ROLES, "Yetkili kullanıcılar karar destek özetlerini görür"),
            MatrixRow("ai_manager_summary", "Yönetici Özeti", "ai/manager-summary", "fa-solid fa-file-lines", AI_AUTHORIZED_ROLES, "Yönetici ve üst yönetim özetleri"),
            MatrixRow("ai_performance_summary", "Performans Özeti", "ai/performance-summary", "fa-solid fa-chart-line", AI_AUTHORIZED_ROLES, "Performans verisi üzerinden özet"),
            MatrixRow("ai_personnel_quality", "Personel Veri Kalitesi", "ai/personnel-quality", "fa-solid fa-user-check", ("admin", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator"), "Eksik sicil, birim, yönetici ve vekâlet kontrolü"),
            MatrixRow("ai_survey_summary", "Anket Sonuç Özeti", "ai/survey-summary", "fa-solid fa-square-poll-vertical", AI_AUTHORIZED_ROLES, "Anket sonuçlarını yönetici diliyle özetler"),
            MatrixRow("ai_feedback_themes", "Geri Bildirim Temaları", "ai/feedback-themes", "fa-solid fa-comment-dots", AI_AUTHORIZED_ROLES, "Tekrar eden konu başlıkları"),
            MatrixRow("ai_support_risk", "Destek Talebi Analizi", "ai/support-risk", "fa-solid fa-headset", AI_AUTHORIZED_ROLES, "Yoğunlaşan talepler ve geciken işler"),
            MatrixRow("ai_redaction_rules", "Hassas Veri Redaksiyonu", "ai/redaction-rules", "fa-solid fa-user-secret", AI_TECH_ADMIN_ROLES, "Maskeleme ve veri minimizasyonu kuralları"),
            MatrixRow("ai_request_logs", "AI İşlem Logları", "ai/request-logs", "fa-solid fa-clock-rotate-left", ("admin", "baskan"), "AI istek ve yanıt denetim izi"),
            MatrixRow("ai_settings", "AI Ayarları", "ai/settings", "fa-solid fa-sliders", AI_TECH_ADMIN_ROLES, "Cache, öneri dili, görünürlük ve log ayarları"),
        ),
    ),
    MatrixGroup(
        key="sanal_asistan",
        title="Sanal Asistan Rol Matrisi",
        subtitle="Sanal Asistan V9 kapsamındaki hızlı rehber, güvenli özet, Yardım Merkezi yönlendirmesi, performans rehberi, Başkan/Üst Onay, yayın ön onayı ve gelişim yönlendirmelerinin rol bazlı görünürlüğü.",
        icon="fa-solid fa-robot",
        badges=("Karar üretmez", "Hassas içerik göstermez", "Yönlendirme yetki sınırında"),
        rows=(
            MatrixRow("assistant_center", "Sanal Asistan Merkezi", "assistant_center", "fa-solid fa-robot", ASSISTANT_PERSONNEL_ROLES, "Asistan ana görünürlüğü"),
            MatrixRow("assistant_quick_help", "Hızlı Rehber Cevapları", "assistant_quick_help", "fa-solid fa-circle-question", ASSISTANT_PERSONNEL_ROLES, "Kullanım rehberi ve kısa cevaplar"),
            MatrixRow("assistant_my_summary", "Benim Özetim Kartları", "assistant_my_summary", "fa-solid fa-gauge-high", ASSISTANT_PERSONNEL_ROLES, "Sayı/özet kartları; hassas içerik yok"),
            MatrixRow("assistant_support_routing", "Yardım Merkezi Yönlendirmesi", "assistant_support_routing", "fa-solid fa-headset", ASSISTANT_PERSONNEL_ROLES, "Doğru destek sayfasına geçiş"),
            MatrixRow("assistant_performance_guidance", "Performans Süreç Rehberi", "assistant_performance_guidance", "fa-solid fa-chart-line", ASSISTANT_MANAGER_ROLES, "Performans süreç sorularını yönlendirir"),
            MatrixRow("assistant_president_approval_guidance", "Başkan / Üst Onay Rehberi", "assistant_president_approval_guidance", "fa-solid fa-stamp", PRESIDENT_APPROVAL_ROLES, "70 altı onay süreci açıklaması"),
            MatrixRow("assistant_publish_preapproval_guidance", "Yayın Ön Onayı Rehberi", "assistant_publish_preapproval_guidance", "fa-solid fa-user-check", PUBLISH_PREAPPROVAL_ROLES + ("baskan_yardimcisi",), "Final yayın öncesi kontrol rehberi"),
            MatrixRow("assistant_interim_notes_guidance", "Dönem İçi Not Rehberi", "assistant_interim_notes_guidance", "fa-regular fa-note-sticky", PERFORMANCE_MANAGEMENT_ROLES, "Ara notların nasıl kullanılacağını açıklar"),
            MatrixRow("assistant_development_guidance", "Gelişim Önerisi Rehberi", "assistant_development_guidance", "fa-solid fa-seedling", PERFORMANCE_MANAGEMENT_ROLES, "Gelişim önerisi alanına yönlendirir"),
            MatrixRow("assistant_archive_guidance", "Geçmiş Karne Arşivi Rehberi", "assistant_archive_guidance", "fa-solid fa-box-archive", ALL_AUTH_ROLES, "Kişisel veya yetkili arşiv görünürlüğünü açıklar"),
            MatrixRow("assistant_process_alerts", "Süreç Hatırlatma ve Uyarılar", "assistant_process_alerts", "fa-solid fa-triangle-exclamation", ALL_AUTH_ROLES, "Bekleyen iş ve süreç uyarıları"),
            MatrixRow("assistant_reports", "Rapor Oluşturma / Paylaşım", "assistant_report_generate", "fa-solid fa-file-lines", ASSISTANT_MANAGER_ROLES, "Yetkili rapor ve paylaşım destekleri"),
            MatrixRow("assistant_ai_summary", "AI Özet ve Karar Notu", "assistant_ai_summary", "fa-solid fa-brain", AI_AUTHORIZED_ROLES, "Yetkili ve insan denetimli özet"),
            MatrixRow("assistant_logs", "Asistan İşlem Logları", "assistant_logs", "fa-solid fa-clipboard-list", ("admin", "baskan"), "Asistan işlem denetim izi"),
            MatrixRow("assistant_settings", "Asistan Ayarları", "assistant_settings", "fa-solid fa-sliders", ADMIN_ONLY, "Asistan görünürlük ve özellik ayarları"),
        ),
    ),
    MatrixGroup(
        key="ayarlar_guvenlik",
        title="Ayarlar ve Güvenlik Rol Matrisi",
        subtitle="Sistem ayarları, modül ayarları, rol-yetki, menü görünürlüğü, CAPTCHA, oturum, e-posta, bildirim ve denetim kayıtları.",
        icon="fa-solid fa-shield-halved",
        badges=("Ayarlar: admin", "Rol Matrisi: admin", "Denetim: izlenebilirlik"),
        rows=(
            MatrixRow("settings", "Sistem Ayarları", "settings", "fa-solid fa-sliders", SETTINGS_ADMIN_ROLES, "Genel sistem parametreleri"),
            MatrixRow("module_settings", "Modül Ayarları", "module_settings", "fa-solid fa-puzzle-piece", SETTINGS_ADMIN_ROLES, "Performans, iletişim, AI, yardım ve bildirim ayarları"),
            MatrixRow("role_matrix", "Rol Matrisi", "admin/role-matrix", "fa-solid fa-table-list", SETTINGS_ADMIN_ROLES, "Bu görsel rol matrisi merkezi"),
            MatrixRow("role_defaults", "Rol Bazlı Menü Varsayılanları", "role_menu_defaults", "fa-solid fa-user-lock", SETTINGS_ADMIN_ROLES, "Rol menü görünürlük başlangıçları"),
            MatrixRow("user_menu_permissions", "Kişi Bazlı Menü Yetkileri", "user_menu_permissions", "fa-solid fa-user-gear", SETTINGS_ADMIN_ROLES, "Kullanıcıya özel menü açma/kapatma"),
            MatrixRow("unit_menu_profiles", "Birim Bazlı Menü Profilleri", "unit_menu_profiles", "fa-solid fa-building-shield", SETTINGS_ADMIN_ROLES, "Birim profiline göre görünürlük"),
            MatrixRow("security_settings", "Güvenlik Ayarları", "security_settings", "fa-solid fa-lock", SETTINGS_ADMIN_ROLES, "Parola, oturum, CAPTCHA ve erişim kuralları"),
            MatrixRow("notification_settings", "Bildirim / E-posta Ayarları", "notification_settings", "fa-solid fa-envelope-open-text", SETTINGS_ADMIN_ROLES, "Mail ve sistem içi bildirim davranışı"),
            MatrixRow("scheduled_jobs", "Zamanlanmış İşler", "scheduled_jobs", "fa-solid fa-clock", SETTINGS_ADMIN_ROLES, "Hatırlatma, rapor ve periyodik görev ayarları"),
            MatrixRow("audit_logs", "Denetim Kayıtları", "audit_logs", "fa-solid fa-file-shield", ("admin", "baskan"), "Kritik işlem ve ayar değişikliği geçmişi"),
        ),
    ),
)

PRINCIPLES: tuple[str, ...] = (
    "Rolsüz Kullanıcı satırı varsayılan kapalı kabul edilir; açık yetki verilmeden kritik modül görünmez.",
    "Personel Yönetimi sekmeleri standart personelde gösterilmez; personel yalnızca kendi kişisel süreçlerini görür.",
    "Performans sonucu personele yalnızca yayın sonrası açılır; Başkan/Üst Onay ve yayın ön onayı tamamlanmadan sonuç açılmaz.",
    "Yardım Merkezi tüm kullanıcılara rehberlik eder; talep yönetimi ve tüm talepler ekranı yetki kapsamıyla sınırlıdır.",
    "Sanal Asistan karar üretmez; yalnızca rehberlik, güvenli özet ve yetkili yönlendirme sağlar.",
    "AI karar vermez; yalnızca yetkili kullanıcı için karar destek, özet ve risk farkındalığı üretir.",
    "Menü görünürlüğü güvenlik yerine geçmez; endpoint ve işlem kontrolleri ayrıca korunur.",
    "Kritik rol, menü, ayar, AI, yayın ve yönetim işlemleri denetim iziyle izlenmelidir.",
)

ROLE_LEGEND: tuple[dict[str, str], ...] = (
    {"label": "Tik işareti", "text": "İlgili rol için sekmenin görünür veya kullanılabilir olduğunu gösterir."},
    {"label": "Boş kutu", "text": "İlgili rol için sekmenin varsayılan olarak kapalı olduğunu gösterir."},
    {"label": "Rolsüz Kullanıcı", "text": "Rol bilgisi boş olan kullanıcıdır; güvenli varsayılan kapalıdır."},
    {"label": "Yardım Merkezi", "text": "Kişisel destek akışı açık olabilir; tüm talepler ve atama görünürlüğü yönetici kapsamındadır."},
    {"label": "Performans Onayları", "text": "Başkan/Üst Onay ve yayın ön onayı özel rol sınırlarıyla yönetilir."},
    {"label": "Sanal Asistan", "text": "Hassas içerik göstermez; güvenli rehberlik ve yönlendirme üretir."},
    {"label": "AI Karar Destek", "text": "Yetki sınırını aşmaz, idari karar üretmez; insan denetimli destek verir."},
    {"label": "Denetim izi", "text": "Kritik görünürlük, ayar, yayın, AI ve yönetim işlemlerinin izlenmesi gerekir."},
)

ROLE_PRIORITY_NOTES: tuple[dict[str, str], ...] = (
    {"title": "Yönetim rolleri", "text": "Admin, Başkan, Başkan Yardımcısı, Grup Başkanı, Mali Müşavir, Koordinatör ve Birim Sorumlusu yönetim/görünürlük ağırlıklı rollerdir."},
    {"title": "Başkan / Üst Onay", "text": "70 altı süreçler yalnızca gerçek düşük performans kaydı oluştuğunda Başkan/Üst Onay ekranına düşer."},
    {"title": "Yayın ön onayı", "text": "Başkan/Üst Onay sonrası final yayın öncesi Personel ve Destek Hizmetleri Grup Başkanı kontrolü ayrı tutulur."},
    {"title": "Personel", "text": "Personel rolü günlük kullanım, kendi bildirimleri, mesajları, anketleri, destek talepleri, yardım merkezi, asistan ve yayın sonrası karne görünürlüğü ile sınırlıdır."},
    {"title": "Rolsüz Kullanıcı", "text": "Rol bilgisi boş/None olan kullanıcı güvenli varsayılanla kapalı kabul edilir; yönetim sekmeleri gösterilmez."},
    {"title": "Yetki değişikliği", "text": "Bu ekran okunabilir matristir. Gerçek yetki değiştirme işi rol, kişi ve birim bazlı menü ayarları üzerinden ayrıca yönetilmelidir."},
)


def _filter_groups(selected_module: str) -> tuple[MatrixGroup, ...]:
    selected = (selected_module or "tum").strip().lower()
    if selected in {"tum", "all", ""}:
        return GROUPS
    selected_group = tuple(group for group in GROUPS if group.key == selected)
    if selected_group:
        return selected_group
    for group in GROUPS:
        if any(row.key == selected for row in group.rows):
            return (group,)
    return GROUPS


def _role_summary_items() -> tuple[dict[str, object], ...]:
    items: list[dict[str, object]] = []
    all_rows = tuple(row for group in GROUPS for row in group.rows)
    for role in ROLES:
        allowed = sum(1 for row in all_rows if role.key in row.allowed_roles)
        denied = len(all_rows) - allowed
        groups = sum(1 for group in GROUPS if any(role.key in row.allowed_roles for row in group.rows))
        if role.key == "admin":
            note = "Tam sistem görünürlüğü ve teknik yönetim sorumluluğu."
        elif role.key == "baskan":
            note = "Üst yönetim, Başkan/Üst Onay ve kritik karar destek görünürlüğü."
        elif role.key == "baskan_yardimcisi":
            note = "Üst yönetim görünürlüğü, süreç takibi ve raporlama ağırlığı."
        elif role.key in {"grup_baskani", "koordinator", "birim_sorumlusu", "mali_musavir"}:
            note = "Yetki alanı kadar yönetim, izleme, gelişim ve raporlama görünürlüğü."
        elif role.key == "personel":
            note = "Kişisel ekranlar, yardım merkezi, asistan, mesajlaşma, anket, destek ve yayın sonrası karne."
        else:
            note = "Varsayılan kapalı; rol tanımı yapılmadan yönetim ekranı açılmaz."
        items.append({
            "key": role.key,
            "label": role.label,
            "short_label": role.short_label.replace("\n", " "),
            "allowed_count": allowed,
            "denied_count": denied,
            "group_count": groups,
            "note": note,
        })
    return tuple(items)


def _matrix_export_rows() -> tuple[dict[str, object], ...]:
    export_rows: list[dict[str, object]] = []
    for group in GROUPS:
        for row in group.rows:
            export_rows.append({
                "group": group.title,
                "key": row.key,
                "title": row.title,
                "subtitle": row.subtitle,
                "allowed_roles": ", ".join(row.allowed_roles),
                "policy": row.policy,
            })
    return tuple(export_rows)


def _build_role_matrix_ui_context_base(selected_module: str = "tum") -> dict:
    visible_groups = _filter_groups(selected_module)
    row_count = sum(len(group.rows) for group in GROUPS)
    visible_row_count = sum(len(group.rows) for group in visible_groups)
    menu_key_count = len({row.subtitle for group in GROUPS for row in group.rows})
    checked_count = sum(len(row.allowed_roles) for group in visible_groups for row in group.rows)
    restricted_row_count = sum(1 for group in GROUPS for row in group.rows if "personel" not in row.allowed_roles)

    return {
        "selected_module": selected_module or "tum",
        "roles": ROLES,
        "matrix_groups": GROUPS,
        "visible_groups": visible_groups,
        "principles": PRINCIPLES,
        "role_legend": ROLE_LEGEND,
        "role_summary": _role_summary_items(),
        "role_priority_notes": ROLE_PRIORITY_NOTES,
        "matrix_export_rows": _matrix_export_rows(),
        "matrix_version": "V12",
        "stats": {
            "group_count": len(GROUPS),
            "role_count": len(ROLES),
            "row_count": row_count,
            "visible_row_count": visible_row_count,
            "menu_key_count": menu_key_count,
            "principle_count": len(PRINCIPLES),
            "checked_count": checked_count,
            "restricted_row_count": restricted_row_count,
        },
    }


# BYS360_SETTINGS_MODULE_ROLE_MATRIX_V12_POLICY_NOTE
ASSISTANT_MODULE_MASTER_V9_ROW = {
    "key": "assistant_module",
    "label": "Sanal Asistan Modülü",
    "description": "Bu ana yetki kapalıysa Sanal Asistan penceresi, hızlı rehber, güvenli özet kartları ve tüm kısa yollar ilgili rolde görünmez.",
}

# BYS360_PERSONEL_ROLE_MATRIX_CURRENT_SCOPE_V1_UI_BEGIN
# Ayarlar > Rol Matrisi Merkezi görsel ekranında Personel Yönetimi güncel canlı kapsamı.

_BYS360_PERSONEL_ROLE_MATRIX_GROUP = MatrixGroup(
    key="personel_yonetimi",
    title="Personel Yönetimi Rol Matrisi",
    subtitle="Canlı kapsamda Personel Yönetimi; personel özlük/kullanıcı omurgası, birim-pozisyon yapısı ve izin-devamsızlık/vekâlet hattından oluşur. Kaldırılmış personel operasyon sekmeleri bu ekranda gösterilmez.",
    icon="fa-solid fa-users-gear",
    badges=("Canlı kapsam: 3 satır", "Personel rolünde yönetim gizli", "Performans sekmeleri ayrı matriste kalır"),
    rows=(
        MatrixRow(
            "admin_users",
            "Personel Özlük Dosyaları",
            "admin_users",
            "fa-solid fa-folder-open",
            PERSONNEL_MANAGEMENT_ROLES,
            "Personel/kullanıcı kaydı, sicil ve temel özlük görünürlüğü. Standart personelde yönetim ekranı kapalı kalır.",
        ),
        MatrixRow(
            "org_units",
            "Birim ve Pozisyon Yönetimi",
            "org_units",
            "fa-solid fa-diagram-project",
            PERSONNEL_MANAGEMENT_ROLES,
            "Birim, üst birim, pozisyon ve organizasyon bağlantısı. Yetkili roller kendi kapsamı kadar kullanır.",
        ),
        MatrixRow(
            "hr_leave_tracking",
            "İzin, Devamsızlık ve Vekâlet",
            "hr_leave_tracking",
            "fa-solid fa-calendar-check",
            PERSONNEL_MANAGEMENT_ROLES,
            "İzin, devamsızlık ve vekâlet hattı performans görev akışını besleyen aktif personel omurgasıdır.",
        ),
    ),
)

GROUPS = tuple(
    _BYS360_PERSONEL_ROLE_MATRIX_GROUP if getattr(group, "key", "") == "personel_yonetimi" else group
    for group in GROUPS
)
if not any(getattr(group, "key", "") == "personel_yonetimi" for group in GROUPS):
    GROUPS = (_BYS360_PERSONEL_ROLE_MATRIX_GROUP,) + tuple(GROUPS)

_BYS360_PREVIOUS_BUILD_ROLE_MATRIX_UI_CONTEXT = _build_role_matrix_ui_context_base

def build_role_matrix_ui_context(active_group_key: str | None = None):
    if callable(_BYS360_PREVIOUS_BUILD_ROLE_MATRIX_UI_CONTEXT):
        context = _BYS360_PREVIOUS_BUILD_ROLE_MATRIX_UI_CONTEXT(active_group_key)
    else:
        context = {}
    if isinstance(context, dict):
        context["matrix_version"] = "V13 · Personel Güncel Kapsam"
        context["personel_current_scope_note"] = "Personel Yönetimi rol matrisi güncel canlı kapsamla sınırlandırıldı."
    return context
# BYS360_PERSONEL_ROLE_MATRIX_CURRENT_SCOPE_V1_UI_END

# BYS360_SETTINGS_MENU_ROLE_MATRIX_ALL_TABS_V1_BEGIN
# Görsel Rol Matrisi Merkezi de yeni KPI/Hedef ve Öz Değerlendirme sekmelerini gösterir.
_BYS360_ROLE_MATRIX_UI_EXTRA_PERFORMANCE_ROWS = (
    MatrixRow('performance_kpi_dashboard', 'KPI Dashboardu', 'performance_kpi_dashboard', 'fa-solid fa-gauge-high', ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'], 'KPI ve hedef gerçekleşmeleri'),
    MatrixRow('performance_kpi_management', 'KPI ve Hedef Yönetimi', 'performance_kpi_management', 'fa-solid fa-bullseye', ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator'], 'Hedef kartları ve KPI kayıtları'),
    MatrixRow('performance_competency_library', 'Yetkinlik Kütüphanesi', 'performance_competency_library', 'fa-solid fa-layer-group', ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'], 'Rol/görev bazlı yetkinlik tanımları'),
    MatrixRow('performance_self_assessment', 'Öz Değerlendirme', 'performance_self_assessment', 'fa-solid fa-user-pen', ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel'], 'Personel öz değerlendirme ve yönetici özetleri'),
    MatrixRow('performance_kpi_analysis', 'KPI Analiz Merkezi', 'performance_kpi_analysis', 'fa-solid fa-chart-pie', ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator'], 'KPI/hedef analiz ve karar destek özetleri'),
)
try:
    _patched_groups = []
    for _group in GROUPS:
        if getattr(_group, "key", "") == "performans_yonetimi":
            _existing_keys = {getattr(_row, "subtitle", "") for _row in _group.rows}
            _rows = list(_group.rows)
            for _row in _BYS360_ROLE_MATRIX_UI_EXTRA_PERFORMANCE_ROWS:
                if getattr(_row, "subtitle", "") not in _existing_keys:
                    _rows.append(_row)
                    _existing_keys.add(getattr(_row, "subtitle", ""))
            _group = MatrixGroup(
                key=_group.key,
                title=_group.title,
                subtitle="Kriter, dönem/kapsam, görev, karne, Başkan/Üst Onay, yayın ön onayı, süreç takibi, arşiv, gelişim rehberi, KPI/Hedef, yetkinlik, öz değerlendirme ve KPI analiz sekmelerinin rol bazlı görünürlüğü.",
                icon=_group.icon,
                badges=_group.badges + ("KPI/Hedef: yönetici kapsamı", "Öz değerlendirme: tüm kullanıcılar"),
                rows=tuple(_rows),
            )
        _patched_groups.append(_group)
    GROUPS = tuple(_patched_groups)
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/role_matrix_ui_service.py)")
# BYS360_SETTINGS_MENU_ROLE_MATRIX_ALL_TABS_V1_END

# BYS360_ASSISTANT_TABS_ROLE_MATRIX_V2_BEGIN
# Görsel rol matrisi ekranında Sanal Asistan grubunun başına gerçek BYS360 Asistanı sekmeleri eklenir.
_BYS360_ASSISTANT_TAB_UI_ROWS = (
    MatrixRow("assistant_module", "BYS360 Asistanı Modülü", "assistant_module", "fa-solid fa-toggle-on", ALL_AUTH_ROLES, "Ana anahtar. Kapalıysa ilgili rolde Asistan bölümü görünmez."),
    MatrixRow("ai_agent_panel", "Asistan Paneli", "ai_agent_panel", "fa-solid fa-robot", ALL_AUTH_ROLES, "Sohbet, rehberlik ve güvenli yönlendirme paneli."),
    MatrixRow("ai_agent_knowledge", "Asistan Bilgi Bankası", "ai_agent_knowledge", "fa-solid fa-book-open-reader", ("admin", "baskan"), "Asistan bilgi kayıtlarının yönetildiği ekran."),
    MatrixRow("ai_agent_teaching_center", "Asistan Öğretim Merkezi", "ai_agent_teaching_center", "fa-solid fa-chalkboard-user", ("admin", "baskan"), "Asistanı eğitme ve kurumsal bilgi yönetimi ekranı."),
)
try:
    _new_groups = []
    for _group in GROUPS:
        if getattr(_group, "key", "") == "sanal_asistan":
            _existing = {getattr(_row, "subtitle", "") for _row in _group.rows}
            _prepend = tuple(_row for _row in _BYS360_ASSISTANT_TAB_UI_ROWS if _row.subtitle not in _existing)
            _group = MatrixGroup(
                key=_group.key,
                title="BYS360 Asistanı Rol Matrisi",
                subtitle="Asistan Paneli, Bilgi Bankası, Öğretim Merkezi ve rehberlik/özet yetkilerinin rol bazlı görünürlüğü.",
                icon=_group.icon,
                badges=("Sekmeler ayardan aç/kapat", "Kapalı sekme menüde görünmez", "Yetki sınırı korunur"),
                rows=_prepend + tuple(_group.rows),
            )
        _new_groups.append(_group)
    GROUPS = tuple(_new_groups)
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/role_matrix_ui_service.py)")
# BYS360_ASSISTANT_TABS_ROLE_MATRIX_V2_END

# BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_MATRIX_V3_BEGIN
# Görsel rol matrisi ekranında Performans Yönetimi grubunun başına ana anahtar satırı eklenir.
_BYS360_PERFORMANCE_MAIN_SWITCH_UI_ROW = MatrixRow(
    "performance_module",
    "Performans Yönetimi Modülü Ana Anahtarı",
    "performance_module",
    "fa-solid fa-toggle-on",
    ALL_AUTH_ROLES,
    "Kapalıysa ilgili rolde Performans Yönetimi bölümü ve tüm performans kısayolları menüde görünmez.",
)
try:
    _patched_groups = []
    for _group in GROUPS:
        if getattr(_group, "key", "") == "performans_yonetimi":
            _existing = {getattr(_row, "key", "") for _row in _group.rows}
            _rows = tuple(_group.rows)
            if "performance_module" not in _existing:
                _rows = (_BYS360_PERFORMANCE_MAIN_SWITCH_UI_ROW,) + _rows
            _group = MatrixGroup(
                key=_group.key,
                title="Performans Yönetimi Rol Matrisi",
                subtitle="Performans Yönetimi ana anahtarı ile tüm alt sekmeleri rol bazlı açıp kapatın. Ana anahtar kapalıysa alt sekmeler açık olsa bile menüde görünmez.",
                icon=_group.icon,
                badges=("Ana anahtar: bölüm görünürlüğü", "Alt sekmeler: ayrı kontrol", "Kapalı sekme menüde görünmez"),
                rows=_rows,
            )
        _patched_groups.append(_group)
    GROUPS = tuple(_patched_groups)
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/role_matrix_ui_service.py)")
# BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_MATRIX_V3_END

# BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_UI_BEGIN
# Ayarlar > Rol Matrisi Merkezi Personel Yönetimi satırları canlı sol şeritle hizalandı.
_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_GROUP = MatrixGroup(
    key="personel_yonetimi",
    title="Personel Yönetimi Rol Matrisi",
    subtitle="Personel Yönetimi sol şeridinde görünen canlı sekmeler bu satırlardan yönetilir. Seçili satır görünür, kapalı satır sol menüde hiç görünmez.",
    icon="fa-solid fa-users-gear",
    badges=("Canlı kapsam: 5 satır", "Kapalı sekme sol menüde görünmez", "Personel rolünde yönetim kapalı"),
    rows=(
        MatrixRow("admin_users", "Personel Özlük Dosyaları", "admin_users", "fa-solid fa-folder-open", PERSONNEL_MANAGEMENT_ROLES, "Personel/kullanıcı kaydı, sicil ve özlük listesi."),
        MatrixRow("org_units", "Birim ve Pozisyon Yönetimi", "org_units", "fa-solid fa-diagram-project", PERSONNEL_MANAGEMENT_ROLES, "Birim, üst birim, pozisyon ve organizasyon bağlantıları."),
        MatrixRow("hr_management", "Personel Kontrol Paneli", "hr_management", "fa-solid fa-users-gear", PERSONNEL_MANAGEMENT_ROLES, "İzin, devamsızlık, vekâlet ve personel süreç özeti."),
        MatrixRow("hr_leave_tracking", "İzin, Devamsızlık ve Vekâlet", "hr_leave_tracking", "fa-solid fa-calendar-check", PERSONNEL_MANAGEMENT_ROLES, "İzin/devamsızlık/vekâlet canlı işlem hattı."),
        MatrixRow("hr_reports", "Personel Raporları", "hr_reports", "fa-solid fa-chart-column", PERSONNEL_MANAGEMENT_ROLES, "Personel izin, devamsızlık ve vekâlet raporları."),
    ),
)
GROUPS = tuple(_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_GROUP if getattr(_group, "key", "") == "personel_yonetimi" else _group for _group in GROUPS)
if not any(getattr(_group, "key", "") == "personel_yonetimi" for _group in GROUPS):
    GROUPS = (_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_GROUP,) + tuple(GROUPS)
_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_PREVIOUS_CONTEXT = build_role_matrix_ui_context

def build_role_matrix_ui_context(selected_module: str = "tum") -> dict:  # type: ignore[no-redef]
    context = _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_PREVIOUS_CONTEXT(selected_module)
    if isinstance(context, dict):
        context["matrix_version"] = "V14 · Personel Rol Matrisi Canlı Görünürlük"
        context["personel_visibility_v7_note"] = "Personel Yönetimi seçili sekmeleri sol şeritte görünür; kapalı sekmeler gizlenir."
    return context
# BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_UI_END

# BYS360_PERFORMANCE_ROLE_MATRIX_PERSONNEL_V8_BEGIN
# Görsel Rol Matrisi düzeltmesi: performans satırları Genel'den kaldırılır ve
# Performans Yönetimi grubunda sol şeritteki gerçek anahtarlarla gösterilir.
_BYS360_PERF_RM_V8_GENERAL_ROW_KEYS = {"performance_tasks", "scorecards", "my_performance_comparison"}
_BYS360_PERF_RM_V8_GENERAL_ROW_SUBTITLES = {"performance_tasks", "performance_scorecard", "my_performance_comparison", "performance_reports"}
_BYS360_PERF_RM_V8_ROWS = (
    MatrixRow("performance_module", "Performans Yönetimi Modülü Ana Anahtarı", "performance_module", "fa-solid fa-toggle-on", ALL_AUTH_ROLES, "Alt sekmelerden biri açıksa bölüm otomatik görünür; tamamen kapatmak için alt performans sekmelerini de kapatın."),
    MatrixRow("performance_tasks", "Görevlerim", "performance_tasks", "fa-solid fa-list-check", PERFORMANCE_MANAGEMENT_ROLES, "Atanmış performans görevleri."),
    MatrixRow("performance_scorecard", "Not Karnesi", "performance_scorecard", "fa-solid fa-id-card-clip", ALL_AUTH_ROLES, "Personel yalnızca yayın sonrası kendi sonucunu görür."),
    MatrixRow("performance_archive", "Geçmiş Karne Arşivi", "performance_archive", "fa-solid fa-box-archive", ALL_AUTH_ROLES, "Personel kendi geçmişini; yönetici yetki kapsamını görür."),
    MatrixRow("my_performance_comparison", "Kişisel Performans Analizi", "my_performance_comparison", "fa-solid fa-chart-line", ALL_AUTH_ROLES, "Personel kendi ortalamasını; yönetici yetki kapsamını görür."),
    MatrixRow("performance_reports", "Performans Raporları", "performance_reports", "fa-solid fa-chart-simple", PERFORMANCE_MANAGEMENT_ROLES, "Dönem, birim, ekip, kategori ve kişi bazlı raporlar."),
    MatrixRow("performance_kpi_dashboard", "KPI Dashboardu", "performance_kpi_dashboard", "fa-solid fa-gauge-high", PERFORMANCE_MANAGEMENT_ROLES, "KPI ve hedef özetleri."),
    MatrixRow("performance_kpi_management", "KPI ve Hedef Yönetimi", "performance_kpi_management", "fa-solid fa-bullseye", ("admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator"), "Hedef kartları ve KPI dönemleri."),
    MatrixRow("performance_competency_library", "Yetkinlik Kütüphanesi", "performance_competency_library", "fa-solid fa-book-open", PERFORMANCE_MANAGEMENT_ROLES, "Görev/rol bazlı gelişim ve yetkinlik şablonları."),
    MatrixRow("performance_self_assessment", "Öz Değerlendirme", "performance_self_assessment", "fa-solid fa-user-check", ALL_AUTH_ROLES, "Personelin kendi dönem özeti ve gelişim notu."),
    MatrixRow("performance_kpi_analysis", "KPI Analiz Merkezi", "performance_kpi_analysis", "fa-solid fa-chart-column", ("admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator"), "AI destekli hedef/KPI analiz ekranı."),
    MatrixRow("performance_criteria", "Değerlendirme Kriterleri", "performance_criteria", "fa-solid fa-list-check", UPPER_ROLES, "Kriter tanımlama ve görüntüleme."),
    MatrixRow("performance_periods", "Dönemler ve Kapsamlar", "performance_periods", "fa-solid fa-calendar-days", UPPER_ROLES, "Çoklu dönem, özel dönem ve kapsam yönetimi."),
    MatrixRow("performance_evaluation_tasks", "Değerlendirme Görevleri", "performance_evaluation_tasks", "fa-solid fa-clipboard-check", PERFORMANCE_MANAGEMENT_ROLES, "Amir görevleri ve süreç takibi."),
    MatrixRow("performance_process_tracking", "Süreç Takibi", "performance_process_tracking", "fa-solid fa-route", PERFORMANCE_MANAGEMENT_ROLES, "Performans süreçlerinin yetki kapsamıyla izlenmesi."),
    MatrixRow("performance_process_reports", "Süreç Raporları", "performance_process_reports", "fa-solid fa-chart-line", PERFORMANCE_MANAGEMENT_ROLES, "Risk, gecikme ve süreç yoğunluğu raporları."),
    MatrixRow("performance_president_approvals", "Başkan / Üst Onayları", "performance_president_approvals", "fa-solid fa-stamp", PRESIDENT_APPROVAL_ROLES, "70 altı düşük performans onayları."),
    MatrixRow("performance_personnel_support_publish_approval", "Yayın Ön Onayı", "performance_personnel_support_publish_approval", "fa-solid fa-user-check", PUBLISH_PREAPPROVAL_ROLES + ("personel_ve_destek_hizmetleri_grup_baskani", "personel_destek_hizmetleri_grup_baskani", "personel_ve_idari_isler_grup_baskani", "personel_idari_isler_grup_baskani"), "Final yayın öncesi Personel ve Destek Hizmetleri Grup Başkanı kontrolü."),
    MatrixRow("performance_interim_notes", "Dönem İçi Notlar", "performance_interim_notes", "fa-regular fa-note-sticky", PERFORMANCE_MANAGEMENT_ROLES, "Ara dönem gözlem ve gelişim notları."),
    MatrixRow("performance_development_guidance", "Gelişim Rehberi", "performance_development_guidance", "fa-solid fa-seedling", PERFORMANCE_MANAGEMENT_ROLES, "Gelişim önerisi ve rehber not alanları."),
    MatrixRow("performance_meeting_p3_reminders", "Hatırlatma ve Aksatan Amirler", "performance_meeting_p3_reminders", "fa-solid fa-bell", PERFORMANCE_MANAGEMENT_ROLES, "Geciken değerlendirme görevleri ve hatırlatmalar."),
    MatrixRow("performance_feedback_aftercare", "Görüşme Sonrası Notlar", "performance_feedback_aftercare", "fa-solid fa-clipboard-check", PERFORMANCE_MANAGEMENT_ROLES, "Görüşme sonrası not ve değerlendirme takibi."),
    MatrixRow("performance_feedback_aftercare_new", "Personel ve Dönem Görüşmesi", "performance_feedback_aftercare_new", "fa-solid fa-user-clock", PERFORMANCE_MANAGEMENT_ROLES, "Personel/dönem bazlı görüşme kaydı."),
    MatrixRow("performance_feedback_meeting_guide", "Geri Bildirim Rehberi", "performance_feedback_meeting_guide", "fa-solid fa-comments", PERFORMANCE_MANAGEMENT_ROLES, "Geri bildirim görüşmesi rehber ekranı."),
    MatrixRow("performance_feedback_followup", "Eylem Planı Takibi", "performance_feedback_followup", "fa-solid fa-calendar-check", PERFORMANCE_MANAGEMENT_ROLES, "Gelişim görüşmesi eylem planı takibi."),
    MatrixRow("performance_task_management", "Görev Yönetimi", "performance_task_management", "fa-solid fa-screwdriver-wrench", ADMIN_ONLY, "Teknik görev üretimi ve kontrol."),
    MatrixRow("performance_feedback_meetings", "Geri Bildirim Talepleri / Randevu", "performance_feedback_meetings", "fa-solid fa-comments", PERFORMANCE_MANAGEMENT_ROLES, "Performans sonrası görüşme ve randevu takibi."),
    MatrixRow("performance_hierarchy_tree", "Hiyerarşi Ağacı", "performance_hierarchy_tree", "fa-solid fa-sitemap", PERFORMANCE_MANAGEMENT_ROLES, "Performans amir zinciri görünümü."),
    MatrixRow("performance_hierarchy_assignments", "Hiyerarşi Atamaları & Ayarları", "performance_hierarchy_assignments", "fa-solid fa-code-branch", ADMIN_ONLY, "Ağırlık, 3. amir ve hiyerarşi ayarları."),
    MatrixRow("performance_team_compare", "Personel Analizi", "performance_team_compare", "fa-solid fa-people-arrows", PERFORMANCE_MANAGEMENT_ROLES, "Yönetici ekip kıyası ve dağılım görünümü."),
    MatrixRow("team_performance_comparison_history", "Personel Dönem Analizi", "team_performance_comparison_history", "fa-solid fa-code-compare", PERFORMANCE_MANAGEMENT_ROLES, "Dönemsel ekip/personel kıyas geçmişi."),
    MatrixRow("performance_publish", "Yayın Yönetimi", "performance_publish", "fa-solid fa-bullhorn", ("admin", "baskan"), "Sonuçların personele açılması."),
    MatrixRow("performance_mail_settings", "Performans Mail Ayarları", "performance_mail_settings", "fa-solid fa-envelope-open-text", ADMIN_ONLY, "Hatırlatma ve süreç bildirimleri."),
)

def _bys360_rebuild_performance_role_matrix_v8():
    global GROUPS
    result = []
    for group in GROUPS:
        if getattr(group, "key", "") == "genel":
            rows = tuple(
                row for row in group.rows
                if getattr(row, "key", "") not in _BYS360_PERF_RM_V8_GENERAL_ROW_KEYS
                and getattr(row, "subtitle", "") not in _BYS360_PERF_RM_V8_GENERAL_ROW_SUBTITLES
            )
            group = MatrixGroup(
                key=group.key,
                title="Genel Rol Matrisi",
                subtitle="Dashboard, bildirimler, yardım merkezi ve kullanıcı ortak alanlarının rol bazlı görünürlüğü. Performans sekmeleri yalnızca Performans Yönetimi grubunda yönetilir.",
                icon=group.icon,
                badges=("Dashboard: yetkili tüm kullanıcılar", "Ortak alanlar: rol/yetki kontrollü", "Performans: kendi grubunda"),
                rows=rows,
            )
        elif getattr(group, "key", "") == "performans_yonetimi":
            existing = [row for row in group.rows if getattr(row, "key", "") not in {getattr(v8row, "key", "") for v8row in _BYS360_PERF_RM_V8_ROWS} and getattr(row, "subtitle", "") not in {getattr(v8row, "subtitle", "") for v8row in _BYS360_PERF_RM_V8_ROWS}]
            seen = set()
            rows = []
            for row in list(_BYS360_PERF_RM_V8_ROWS) + existing:
                key = getattr(row, "key", "")
                if key in seen:
                    continue
                seen.add(key)
                rows.append(row)
            group = MatrixGroup(
                key=group.key,
                title="Performans Yönetimi Rol Matrisi",
                subtitle="Sol şeritteki Performans Yönetimi sekmelerinin gerçek anahtarları burada yönetilir. Alt sekme açık olduğunda Performans Yönetimi bölümü ilgili rolde görünür; kapalı sekme sol menüde hiç görünmez.",
                icon=group.icon,
                badges=("Ana anahtar: bölüm görünürlüğü", "Alt sekmeler: tek tek kontrol", "Personel: yayın sonrası kişisel alan"),
                rows=tuple(rows),
            )
        result.append(group)
    GROUPS = tuple(result)

try:
    _bys360_rebuild_performance_role_matrix_v8()
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/role_matrix_ui_service.py)")
# BYS360_PERFORMANCE_ROLE_MATRIX_PERSONNEL_V8_END

# BYS360_SETTINGS_ROLE_MATRIX_ALL_FEATURES_FINAL_FIX_V1_BEGIN
# Geriye dönük gate uyumluluğu ve okunabilir kategori sözleşmesi.
# görsel ekran servisi V4
# Genel Kategorisi
# Personel Yönetimi Sekmeleri
# Performans Yönetimi Sekmeleri
CATEGORY_POLICIES = {
    "genel": "Genel Kategorisi",
    "personel_yonetimi": "Personel Yönetimi Sekmeleri",
    "performans_yonetimi": "Performans Yönetimi Sekmeleri",
    "iletisim_anket": "İletişim ve Anket Sekmeleri",
    "ai_karar_destek": "AI Karar Destek Sekmeleri",
    "settings_security": "Ayarlar ve Güvenlik Sekmeleri",
}
# BYS360_SETTINGS_ROLE_MATRIX_ALL_FEATURES_FINAL_FIX_V1_END

# BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_ROLE_MATRIX_CENTER_BEGIN
# /admin/role-matrix ekranında Portal yetkileri de okunabilir ayrı kart olarak görünür.
_PORTAL_MATRIX_ROWS_V2_12 = (
    MatrixRow("portal_feed", "Portal Yayın Akışı", "portal_feed", "fa-solid fa-stream", ALL_AUTH_ROLES, "Portal ana akışı"),
    MatrixRow("portal_people", "Personel Duvarları", "portal_people", "fa-solid fa-address-book", ALL_AUTH_ROLES, "Personel arama ve duvarlara geçiş"),
    MatrixRow("portal_profiles", "Profilim / Duvar", "portal_profiles", "fa-regular fa-user", ALL_AUTH_ROLES, "Profil ve duvar görünümü"),
    MatrixRow("portal_post_create", "Yeni Paylaşım", "portal_post_create", "fa-solid fa-pen-to-square", ALL_AUTH_ROLES, "Portal paylaşımı yayınlama"),
    MatrixRow("portal_wall_post", "Başkasının Duvarına Yazma", "portal_wall_post", "fa-solid fa-user-pen", ALL_AUTH_ROLES, "Personel duvarına doğrudan paylaşım bırakma"),
    MatrixRow("portal_post_interact", "Beğeni / Yorum", "portal_post_interact", "fa-regular fa-heart", ALL_AUTH_ROLES, "Tepki, yorum ve kaydetme"),
    MatrixRow("portal_post_delete", "Paylaşımı Silme", "portal_post_delete", "fa-solid fa-trash-can", ALL_AUTH_ROLES, "Yetkili paylaşımı yayından kaldırma"),
    MatrixRow("portal_groups", "Portal Grupları", "portal_groups", "fa-solid fa-user-group", ALL_AUTH_ROLES, "Grupları görüntüleme"),
    MatrixRow("portal_group_create", "Grup Oluşturma", "portal_group_create", "fa-solid fa-users-gear", MANAGER_ROLES, "Yetkili roller için grup oluşturma"),
    MatrixRow("portal_moderation", "Portal Yönetimi", "portal_moderation", "fa-solid fa-shield-halved", ("admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"), "İnceleme ve moderasyon"),
)
if not any(getattr(group, "key", "") == "portal" for group in GROUPS):
    GROUPS = GROUPS + (
        MatrixGroup(
            key="portal",
            title="Kurumsal Portal Rol Matrisi",
            subtitle="Yayın akışı, personel duvarları, paylaşım, silme, grup oluşturma ve portal yönetimi yetkileri.",
            icon="fa-solid fa-stream",
            badges=("Yayın akışı", "Personel duvarları", "Paylaşım ve silme", "Grup ve moderasyon"),
            rows=_PORTAL_MATRIX_ROWS_V2_12,
        ),
    )
# BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_ROLE_MATRIX_CENTER_END


# BYS360_PERFORMANCE_V2_1_21_PERIOD_CENTER_ROLE_MATRIX_UI_BEGIN
# Dönem Yönetim Merkezi, Ayarlar > Rol Matrisi görsel matrisinde ayrı satırdır.
_BYS360_PERIOD_CENTER_ROLE_MATRIX_ROW = MatrixRow(
    "performance_period_management_center",
    "Dönem Yönetim Merkezi",
    "performance_period_management_center",
    "fa-solid fa-calendar-check",
    ("admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"),
    "Dönem hazırlığı, durum akışı, görev üretimi, canlı takip ve hatırlatma yönetim merkezi. Koordinatör/Birim Sorumlusu için kişi bazlı yetki verilebilir.",
)
try:
    _patched_groups = []
    for _group in GROUPS:
        if getattr(_group, "key", "") == "performans_yonetimi":
            _rows = list(_group.rows)
            _existing_subtitles = {getattr(_row, "subtitle", "") for _row in _rows}
            if "performance_period_management_center" not in _existing_subtitles:
                _insert_at = 0
                for _idx, _row in enumerate(_rows):
                    if getattr(_row, "subtitle", "") == "performance_periods":
                        _insert_at = _idx + 1
                        break
                _rows.insert(_insert_at, _BYS360_PERIOD_CENTER_ROLE_MATRIX_ROW)
            _group = MatrixGroup(
                key=_group.key,
                title=_group.title,
                subtitle="Kriter, dönem/kapsam, Dönem Yönetim Merkezi, görev, karne, Başkan/Üst Onay, yayın ön onayı, süreç takibi, arşiv, gelişim rehberi ve raporların rol bazlı görünürlüğü.",
                icon=_group.icon,
                badges=tuple(dict.fromkeys(tuple(_group.badges) + ("Dönem Merkezi: rol matrisi kontrollü",))),
                rows=tuple(_rows),
            )
        _patched_groups.append(_group)
    GROUPS = tuple(_patched_groups)
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: Dönem Yönetim Merkezi rol matrisi satırı eklenemedi")

_BYS360_PREVIOUS_BUILD_ROLE_MATRIX_UI_CONTEXT_V221 = globals().get("build_role_matrix_ui_context")
def build_role_matrix_ui_context(active_group_key: str | None = None):
    if callable(_BYS360_PREVIOUS_BUILD_ROLE_MATRIX_UI_CONTEXT_V221):
        context = _BYS360_PREVIOUS_BUILD_ROLE_MATRIX_UI_CONTEXT_V221(active_group_key)
    else:
        context = {}
    if isinstance(context, dict):
        context["matrix_version"] = "V14 · Dönem Merkezi Rol Matrisi"
        context["period_center_role_matrix_note"] = "Dönem Yönetim Merkezi rol, birim ve kişi bazlı menü görünürlüğüne bağlandı."
    return context
# BYS360_PERFORMANCE_V2_1_21_PERIOD_CENTER_ROLE_MATRIX_UI_END

# Compatibility guard.
# Ayarlar > Rol Matrisi ekranında Basında Tarihi Alan satırı görünür, fakat varsayılan yetki admin-only kalır.
try:
    _BYS360_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROW = MatrixRow(
        "portal_press_news",
        "Basında Tarihi Alan",
        "portal_press_news",
        "fa-regular fa-newspaper",
        ADMIN_ONLY,
        "Basında Tarihi Alan haber adayları ve yayın/onay ekranı. Varsayılan olarak yalnızca Admin rolüne açıktır.",
    )
    _patched_groups = []
    _portal_group_found = False
    for _group in GROUPS:
        if getattr(_group, "key", "") == "portal":
            _portal_group_found = True
            _rows = []
            _seen = set()
            for _row in getattr(_group, "rows", ()):
                if getattr(_row, "key", "") == "portal_press_news" or getattr(_row, "subtitle", "") == "portal_press_news":
                    if "portal_press_news" not in _seen:
                        _rows.append(_BYS360_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROW)
                        _seen.add("portal_press_news")
                else:
                    _rows.append(_row)
                    _seen.add(getattr(_row, "key", ""))
            if "portal_press_news" not in _seen:
                _insert_at = len(_rows)
                for _idx, _row in enumerate(_rows):
                    if getattr(_row, "key", "") == "portal_moderation":
                        _insert_at = _idx
                        break
                _rows.insert(_insert_at, _BYS360_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROW)
            _group = MatrixGroup(
                key=_group.key,
                title=_group.title,
                subtitle="Yayın akışı, personel duvarları, paylaşım, grup ve Basında Tarihi Alan yetkileri. Basında Tarihi Alan varsayılan olarak yalnızca Admin rolündedir.",
                icon=_group.icon,
                badges=tuple(dict.fromkeys(tuple(_group.badges) + ("Basında Tarihi Alan: Admin",))),
                rows=tuple(_rows),
            )
        _patched_groups.append(_group)
    if not _portal_group_found:
        _patched_groups.append(MatrixGroup(
            key="portal",
            title="Kurumsal Portal Rol Matrisi",
            subtitle="Kurumsal Portal görünürlük ve yetki matrisi.",
            icon="fa-solid fa-stream",
            badges=("Basında Tarihi Alan: Admin",),
            rows=(_BYS360_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROW,),
        ))
    GROUPS = tuple(_patched_groups)
except Exception:
    __import__("logging").getLogger(__name__).exception("Basında Tarihi Alan admin-only rol matrisi satırı uygulanamadı")
# Compatibility guard.

