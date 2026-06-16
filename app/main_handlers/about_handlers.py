from __future__ import annotations

from flask import url_for

from app.models import (
    AIFeedbackLog,
    AIRecommendation,
    AIRequestLog,
    EvaluationAssignment,
    FeedbackCampaign,
    FeedbackRequest,
    MessageThread,
    OrganizationUnit,
    PerformanceCriteria,
    PerformancePeriod,
    Survey,
    SystemSetting,
    User,
)
from app.route_support import safe_render


def _safe_count(query_factory, default: int = 0) -> int:
    try:
        return int(query_factory())
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/main_handlers/about_handlers.py:28")
        return default


def _setting_value(setting_key: str, default: str = "") -> str:
    """Hakkımızda sayfasını Ayarlar > Hakkımızda Sayfası grubundan besler.

    Tablo henüz oluşmamışsa veya kayıt yoksa güvenli varsayılan döner; böylece
    canlı açılışta sayfa ayar altyapısına bağımlı şekilde patlamaz.
    """
    try:
        row = SystemSetting.query.filter_by(setting_key=setting_key, is_active=True).first()
        if row and row.value_text is not None and str(row.value_text).strip():
            return str(row.value_text).strip()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/main_handlers/about_handlers.py)")
    return default


def _split_badges(raw_text: str, fallback: list[str]) -> list[str]:
    source = (raw_text or "").replace("|", "\n").replace(",", "\n")
    values = [item.strip() for item in source.splitlines() if item.strip()]
    return values[:8] or fallback


def about_bys360():
    stats = {
        "personnel_count": _safe_count(lambda: User.query.filter(User.role != "admin").count()),
        "unit_count": _safe_count(lambda: OrganizationUnit.query.count()),
        "period_count": _safe_count(lambda: PerformancePeriod.query.count()),
        "criteria_count": _safe_count(lambda: PerformanceCriteria.query.count()),
        "assignment_count": _safe_count(lambda: EvaluationAssignment.query.count()),
        "message_thread_count": _safe_count(lambda: MessageThread.query.count()),
        "survey_count": _safe_count(lambda: Survey.query.count()),
        "feedback_count": _safe_count(lambda: FeedbackRequest.query.count() + FeedbackCampaign.query.count()),
        "ai_log_count": _safe_count(lambda: AIRequestLog.query.count() + AIRecommendation.query.count() + AIFeedbackLog.query.count()),
    }

    default_badges = [
        "Canlı omurga",
        "Rol bazlı erişim",
        "Şeffaf performans akışı",
        "AI destekli analiz",
    ]
    hero_badges = _split_badges(
        _setting_value("about.hero_badges", "\n".join(default_badges)),
        default_badges,
    )

    hero_metrics = [
        {"label": "Personel", "value": stats["personnel_count"], "icon": "fa-solid fa-users"},
        {"label": "Birim", "value": stats["unit_count"], "icon": "fa-solid fa-sitemap"},
        {"label": "Dönem", "value": stats["period_count"], "icon": "fa-solid fa-calendar-days"},
        {"label": "Kriter", "value": stats["criteria_count"], "icon": "fa-solid fa-list-check"},
    ]

    showcase_cards = [
        {
            "title": "Canlı yönetim panosu",
            "text": "Özet kartlar, süreç görünürlüğü ve grafik destekli genel bakış aynı yüzeyde toplanır.",
            "tags": ["Dashboard", "Görev görünümü", "Süreç özeti"],
        },
        {
            "title": "Kesintisiz süreç akışı",
            "text": "Personel, performans, izin-vekalet, destek ve bildirim hattı aynı canlı omurga içinde ilerler.",
            "tags": ["Personel", "Performans", "Vekâlet"],
        },
    ]

    value_blocks = [
        {
            "icon": "fa-solid fa-id-card-clip",
            "title": "Kimlik, kullanıcı ve yetki",
            "text": "Kullanıcı kayıtları, rol profilleri, kişi bazlı görünürlük ve ayar yönetimi tek merkezden kontrol edilir.",
        },
        {
            "icon": "fa-solid fa-chart-line",
            "title": "Performans ve raporlama",
            "text": "Dönem, değerlendirme kriterleri, amir akışı, yayın süreci ve analiz ekranları aynı işleyişte birleşir.",
        },
        {
            "icon": "fa-solid fa-comments",
            "title": "İletişim, anket ve geri bildirim",
            "text": "Mesajlaşma, duyuru, anket, nabız yoklaması ve geri bildirim kampanyaları canlı kullanıcı deneyimini destekler.",
        },
        {
            "icon": "fa-solid fa-brain",
            "title": "AI karar destek",
            "text": "Kontrollü özetleme, önceliklendirme, kayıtlı işlem izi ve yönetişim ayarları karar süreçlerini destekler.",
        },
    ]

    screen_groups = [
        {
            "eyebrow": "Yönetim görünümü",
            "title": "Dashboard ve genel özet",
            "text": "Süreç özeti, görev görünürlüğü, dönem risk görünümü ve kurumsal kapsam kartları tek ekranda toplanır.",
            "image_url": url_for("static", filename="img/about/dashboard-main.png"),
            "detail_image_url": url_for("static", filename="img/about/dashboard-main-detail.png"),
            "detail_title": "Yakın görünüm",
            "detail_text": "Grafik alanı, süreç özeti ve durum panelleri birlikte okunabilir bir yoğunluk üretir.",
            "tags": ["Dashboard", "Grafik", "Süreç özeti"],
        },
        {
            "eyebrow": "Performans",
            "title": "Değerlendirme kriterleri",
            "text": "Ağırlık, sıra, aktiflik durumu ve açıklama alanlarıyla değerlendirme kriterleri merkezi olarak yönetilir.",
            "image_url": url_for("static", filename="img/about/performance-criteria.png"),
            "detail_image_url": url_for("static", filename="img/about/performance-criteria-detail.png"),
            "detail_title": "Yakın görünüm",
            "detail_text": "Kriter kartları, işlem butonları ve sıralama alanları sade bir akışla aynı blokta ilerler.",
            "tags": ["Kriter listesi", "Ağırlık", "Sıralama"],
        },
        {
            "eyebrow": "Personel",
            "title": "Personel yönetimi",
            "text": "Personel havuzu, filtreler, toplu işlemler ve birim temelli görünüm tek sayfada bir araya gelir.",
            "image_url": url_for("static", filename="img/about/personnel-management.png"),
            "detail_image_url": url_for("static", filename="img/about/personnel-management-detail.png"),
            "detail_title": "Yakın görünüm",
            "detail_text": "Filtre alanı, toplu işlem yüzeyi ve kayıt listesi aynı akış mantığında konumlanır.",
            "tags": ["Personel havuzu", "Toplu işlem", "Filtreleme"],
        },
        {
            "eyebrow": "İzin ve vekâlet",
            "title": "Devamsızlık ve görev devamlılığı",
            "text": "Devamsızlık kayıtları, vekil atama seçenekleri ve kapsam etkileri aynı işlem panelinde yönetilir.",
            "image_url": url_for("static", filename="img/about/absence-delegation.png"),
            "detail_image_url": url_for("static", filename="img/about/absence-delegation-detail.png"),
            "detail_title": "Yakın görünüm",
            "detail_text": "Kayıt ve vekâlet blokları eş zamanlı işleyişi görünür kılan çift panel yapıda sunulur.",
            "tags": ["Devamsızlık", "Vekil", "Görev devri"],
        },
        {
            "eyebrow": "Organizasyon",
            "title": "Hiyerarşi ağacı",
            "text": "Üst birim, alt birim ve personel düzeyinde kurumsal zincir şeffaf biçimde görüntülenir.",
            "image_url": url_for("static", filename="img/about/hierarchy-tree.png"),
            "detail_image_url": url_for("static", filename="img/about/hierarchy-tree-detail.png"),
            "detail_title": "Yakın görünüm",
            "detail_text": "Amir zinciri ve personel kartları, geniş listelerde bile okunabilir yoğunluğu korur.",
            "tags": ["Birim yapısı", "1. amir", "2. amir"],
        },
        {
            "eyebrow": "İletişim",
            "title": "Mesaj, duyuru, anket ve geri bildirim",
            "text": "Canlı iletişim alanı mesajlaşma, duyuru, anket ve geri bildirim süreçlerini aynı kullanıcı diliyle destekler.",
            "image_url": url_for("static", filename="img/about/communication-network.png"),
            "detail_image_url": url_for("static", filename="img/about/communication-network-detail.png"),
            "detail_title": "Yakın görünüm",
            "detail_text": "İletişim kartları, bildirim mantığı ve aksiyon şeritleri sade kullanım deneyimi oluşturur.",
            "tags": ["Mesajlar", "Anket", "Geri bildirim"],
        },
    ]

    module_cards = [
        ("fa-solid fa-user-shield", "Kimlik, Kullanıcı ve Yetki", "Kullanıcı, rol, birim ve kişi bazlı menü görünürlüğünü merkezden yönetir."),
        ("fa-solid fa-headset", "Yardım ve Destek Merkezi", "Destek talebi, yanıt, ek ve memnuniyet kayıtlarını izlenebilir şekilde toplar."),
        ("fa-solid fa-users-gear", "Personel Yönetimi", "Sicil bazlı kayıt, unvan, birim ve organizasyon bağlantılarını canlı omurgada tutar."),
        ("fa-solid fa-chart-column", "Performans Yönetimi", "Dönem, kriter, görev, değerlendirme, yayın ve karne süreçlerini aynı omurgada toplar."),
        ("fa-solid fa-people-arrows-left-right", "İzin, Devamsızlık ve Vekâlet", "Yokluk halinde iş akışının durmamasını destekleyen devamlılık mantığını işletir."),
        ("fa-solid fa-comments", "İletişim ve Anket Yönetimi", "Mesajlar, duyurular, anketler ve geri bildirim akışıyla kurumsal etkileşimi güçlendirir."),
        ("fa-solid fa-heart-pulse", "Geri Bildirim ve Nabız", "Nabız yoklaması, kampanya, sonuç ve aksiyon planı alanlarını yönetilebilir kılar."),
        ("fa-solid fa-brain", "AI Karar Destek Merkezi", "Kontrollü özetleme, önceliklendirme, analiz ve işlem loglarıyla karar süreçlerini destekler."),
    ]

    security_points = [
        "Rol bazlı erişim ve kişi bazlı menü görünürlüğü",
        "Canlı kapsamla uyumlu sade ayar ve modül yönetimi",
        "Performans, anket, destek ve AI işlemlerinde izlenebilir kayıt mantığı",
        "Yayın öncesi kontrol, görünürlük ve denetlenebilir işlem akışı",
    ]

    return safe_render(
        "about_bys360.html",
        "<h3>BYS360 Hakkında</h3>",
        page_title="BYS360 Hakkında",
        hero_title=_setting_value(
            "about.hero_title",
            "Kurumsal Süreçleri Tek Dijital Omurgada Toplayan Bütünleşik Yönetim Sistemi",
        ),
        hero_subtitle=_setting_value(
            "about.hero_subtitle",
            "BYS360; kimlik, yetki, personel, performans, izin-vekalet, iletişim, anket, destek, raporlama ve AI karar destek alanlarını aynı kurumsal kullanım dili içinde bir araya getirir.",
        ),
        about_overview_title=_setting_value("about.overview_title", "Canlı kullanım için sadeleştirilmiş bütünlüklü yapı"),
        about_overview_text=_setting_value(
            "about.overview_text",
            "BYS360, modülleri ayrı ve kopuk ekranlar olarak değil; birbirini besleyen tek bir yönetim omurgası olarak kurgular. Kullanıcı, yetki, personel, performans, iletişim, anket, destek ve AI karar destek alanları aynı deneyim içinde devam eder.",
        ),
        about_callout_title=_setting_value("about.callout_title", "Kurumsal güven, yetki ve süreç görünürlüğü"),
        about_callout_text=_setting_value(
            "about.callout_text",
            "BYS360 yalnızca işlem ekranları sunmaz; aynı zamanda kurumsal kullanım için yetki sınırı, kapsam seçimi, görünürlük ve denetlenebilir süreç yaklaşımını korur.",
        ),
        about_footer_title=_setting_value(
            "about.footer_title",
            "BYS360, kurum içi süreçleri aynı dilde bir araya getiren yönetim altyapısıdır.",
        ),
        about_footer_text=_setting_value(
            "about.footer_text",
            "Personel yönetiminden performans akışına, iletişim ve anket yönetiminden AI karar destek alanına kadar canlı yüzeyler; sade, düzenli ve kurumsal bir kullanım deneyimi oluşturacak şekilde tasarlanmıştır.",
        ),
        hero_device_title="BYS360 Canlı Omurga",
        hero_device_image_url=url_for("static", filename="img/about/dashboard-main-hero.png"),
        hero_focus_image_url=url_for("static", filename="img/about/hero-summary.png"),
        hero_badges=hero_badges,
        hero_metrics=hero_metrics,
        showcase_cards=showcase_cards,
        value_blocks=value_blocks,
        screen_groups=screen_groups,
        module_cards=module_cards,
        security_points=security_points,
        live_summary={
            "message_thread_count": stats["message_thread_count"],
            "survey_count": stats["survey_count"],
            "feedback_count": stats["feedback_count"],
            "ai_log_count": stats["ai_log_count"],
        },
    )
