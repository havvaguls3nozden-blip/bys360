"""
BYS360 Asistanı Visible Tutor V6.1

Amaç:
- Kullanıcının doğal cümlesinden BYS360 niyetini anlamak.
- BYS360 sınırları içinde adım adım işlem yaptırmak.
- İdari karar, performans puanı veya hassas veri göstermemek.
- UI tarafındaki eski kısa/fallback cevabın yerine öğretici cevap üretmek.

Bu dosya bilinçli olarak dataclass vb. kullanmaz; Windows/importlib gate testlerinde
"NoneType __dict__" hatasına düşmemesi için sade fonksiyonel yapıdadır.
"""
from __future__ import annotations


import re
import unicodedata
from typing import Any
from collections.abc import Iterable


import logging
ops_logger = logging.getLogger(__name__)

BYS360_VISIBLE_TUTOR_V6_1_MARKER = "BYS360_VISIBLE_TUTOR_V6_1_ACTIVE"

OLD_GREETING = "Merhaba. Ben BYS360 Asistanı. BYS360 içinde performans dönemi oluşturma, personel ekleme, rol matrisi, anket, destek, KPI/Hedef ve karar destek işlemlerinde sizi adım adım yönlendiririm. İdari karar vermem, performans puanı belirlemem, hassas veri göstermem; doğru ekranı, gerekli yetkiyi ve işlem sırasını öğretirim."

WELCOME_TEXT = (
    "Merhaba. Ben BYS360 Asistanı. BYS360 içinde performans dönemi oluşturma, personel ekleme, rol matrisi, anket, destek, KPI/Hedef ve karar destek işlemlerinde sizi adım adım yönlendiririm. İdari karar vermem, performans puanı belirlemem, hassas veri göstermem; doğru ekranı, gerekli yetkiyi ve işlem sırasını öğretirim."
    "sizi adım adım yönlendiririm; performans dönemi oluşturma, personel, rol matrisi, "
    "anket, destek, KPI ve karar destek işlemlerinde doğru ekrana götürürüm. "
    "Hassas veri göstermem, idari karar vermem."
)


def _normalize(text: Any) -> str:
    value = "" if text is None else str(text)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = value.replace("ı", "i").replace("İ", "i")
    value = re.sub(r"[^a-z0-9çğıöşü\s/_-]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _has_any(normalized_text: str, keywords: Iterable[str]) -> bool:
    return any(_normalize(k) in normalized_text for k in keywords)


INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "PERFORMANS_DONEMI_OLUSTURMA": (
        "performans donemi", "dönem aç", "donem ac", "degerlendirme donemi",
        "yeni donem", "performans baslat", "donem olustur", "dönem oluştur",
        "performans dönemi oluşturmayı sordum", "2026 performans", "ozel donem",
        "guvenlik personeline ozel donem", "temizlik icin donem"
    ),
    "PERSONEL_EKLEME": (
        "personel ekle", "yeni personel", "personel kaydi", "sicil no",
        "calisan ekle", "kullanici ekle", "personeli sisteme"
    ),
    "ROL_MATRISI_MENU": (
        "rol matrisi", "menu yok", "menü yok", "menu gorunmuyor", "menü görünmüyor",
        "yetki ac", "yetki kapat", "sekme gorunmuyor", "rol yetki", "menu yetki"
    ),
    "YETKI_SINIRI": (
        "yetkim yok", "erisemiyorum", "erişim yok", "erisim engeli", "sayfa acilmiyor",
        "bu sayfaya erisim", "beyaz sayfa", "yetkisiz"
    ),
    "BASKAN_ONAYI_70_ALTI": (
        "70 alti", "70 altı", "dusuk performans", "düşük performans",
        "baskan onayi", "başkan onayı", "ust onay", "yayın kilidi", "yayin kilidi"
    ),
    "KARNE_GORUNMUYOR": (
        "karne gorunmuyor", "karne görünmüyor", "karnem yok", "karne neden yok",
        "sonuc gorunmuyor", "sonuç görünmüyor", "puanimi goremiyorum"
    ),
    "ANKET_OLUSTURMA": (
        "anket olustur", "anket oluştur", "yeni anket", "anket nasil", "anket nasıl",
        "geri bildirim kampanyasi", "nabiz"
    ),
    "DESTEK_TALEBI": (
        "destek talebi", "yardim merkezi", "yardım merkezi", "talep ac",
        "talep aç", "sorun bildirecegim", "ticket"
    ),
    "KPI_HEDEF": (
        "kpi", "hedef", "hedef karti", "hedef kartı", "hedef donemi",
        "gerceklesme", "gerçekleşme", "stratejik hedef"
    ),
    "AI_KARAR_DESTEK": (
        "ai karar", "yapay zeka karar", "karar destek", "ai karar verir mi",
        "ai ne yapar", "yapay zeka ne yapar"
    ),
    "GENEL_REHBER": (
        "chatgpt gibi", "beni yonlendir", "beni yönlendir", "nasil kullanacagim",
        "nasıl kullanacağım", "hic bilmiyorum", "hiç bilmiyorum", "ne yapacagim",
        "ne yapacağım", "yardim et", "yardım et"
    ),
}


def detect_intent(message: Any) -> str:
    t = _normalize(message)
    if not t:
        return "WELCOME"
    # Öncelik: daha özel niyetler önce.
    ordered = [
        "PERFORMANS_DONEMI_OLUSTURMA",
        "BASKAN_ONAYI_70_ALTI",
        "KARNE_GORUNMUYOR",
        "ROL_MATRISI_MENU",
        "PERSONEL_EKLEME",
        "ANKET_OLUSTURMA",
        "DESTEK_TALEBI",
        "KPI_HEDEF",
        "AI_KARAR_DESTEK",
        "YETKI_SINIRI",
        "GENEL_REHBER",
    ]
    for intent in ordered:
        if _has_any(t, INTENT_KEYWORDS.get(intent, ())):
            return intent
    return "GENEL_REHBER"


def _format_response(title: str, module: str, who: list[str], steps: list[str], notes: list[str], checks: list[str]) -> str:
    who_text = "\n".join(f"- {x}" for x in who) if who else "- Yetki, kurum rol matrisindeki tanıma göre değişir."
    steps_text = "\n".join(f"{i}. {x}" for i, x in enumerate(steps, 1))
    notes_text = "\n".join(f"- {x}" for x in notes) if notes else "- Bu işlemde rol ve menü görünürlüğü kontrol edilmelidir."
    checks_text = "\n".join(f"- {x}" for x in checks) if checks else "- İşlemden sonra ilgili listede kaydın göründüğünü kontrol edin."
    return (
        f"Anladım. {title}\n\n"
        f"Bu konu hangi modülde?\n- {module}\n\n"
        f"Kim yapabilir?\n{who_text}\n\n"
        f"Adım adım işlem sırası:\n{steps_text}\n\n"
        f"Dikkat edilmesi gerekenler:\n{notes_text}\n\n"
        f"İşlemden sonra kontrol:\n{checks_text}\n\n"
        "Güvenlik sınırı:\n"
        "- Ben BYS360 içinde rehberlik ederim; idari karar vermem, performans puanı belirlemem, hassas veri veya yetkisiz içerik göstermem."
    )


def _performance_period_answer() -> str:
    return _format_response(
        "Performans dönemi oluşturmak istiyorsunuz.",
        "Performans Yönetimi > Dönem Yönetimi / Performans Dönemleri",
        ["Admin", "Sistem Yöneticisi", "Performans Yetkilisi", "Yetki verilmiş İK/Personel yetkilisi"],
        [
            "Sol menüden Performans Yönetimi bölümüne girin.",
            "Dönem Yönetimi veya Performans Dönemleri sekmesini açın.",
            "Yeni Dönem Oluştur butonuna basın.",
            "Dönem adını yazın. Örnek: 2026 Yıllık Performans Dönemi.",
            "Dönem türünü seçin: yıllık, 6 aylık, 3 aylık, aylık veya özel dönem.",
            "Başlangıç ve bitiş tarihlerini girin.",
            "Kapsam tipini seçin: tüm kurum, birim, üst birim, kategori/grup veya seçili personel.",
            "Kapsama göre ilgili birimi, kategoriyi ya da personelleri seçin.",
            "Aktiflik ve yayın/işlem durumunu kontrol edin.",
            "Kaydet veya Oluştur butonuna basın.",
            "Sonra Değerlendirme Kriterleri, Ağırlık Ayarları ve Görev Üretimi adımlarına geçin.",
        ],
        [
            "Dönem oluşturmak tek başına değerlendirmeyi başlatmaz; kriter, ağırlık ve görev üretimi de tamamlanmalıdır.",
            "Aynı personel için aynı tarih aralığında çakışan dönem varsa sistem uyarı vermelidir.",
            "Güvenlik veya Temizlik gibi kategoriye özel dönem açıldıysa görevler sadece o kapsamdaki personele üretilmelidir.",
            "Menü görünmüyorsa Rol Matrisi, kişi bazlı izin ve birim bazlı menü profili kontrol edilmelidir.",
        ],
        [
            "Oluşturulan dönem Performans Dönemleri listesinde görünmelidir.",
            "Dönem kapsamındaki personel sayısı beklenen sayıyla uyumlu olmalıdır.",
            "Görev üretiminden sonra eksik amir, sahte 3. amir görevi veya yanlış bekleme statüsü kalmamalıdır.",
        ],
    )


def _personnel_answer() -> str:
    return _format_response(
        "Yeni personel kaydı oluşturmak istiyorsunuz.",
        "Personel Yönetimi > Personel Listesi / Personel Ekle",
        ["Admin", "Sistem Yöneticisi", "Personel Yönetimi Yetkilisi", "Yetki verilmiş İK/Personel kullanıcısı"],
        [
            "Sol menüden Personel Yönetimi bölümüne girin.",
            "Personel Listesi veya Personel Ekle ekranını açın.",
            "Yeni Personel Ekle butonuna basın.",
            "Sicil No, ad, soyad, unvan ve görev bilgilerini girin.",
            "Birim, üst birim ve yönetici alanlarını doldurun.",
            "Gerekliyse kategori seçin: Güvenlik, Temizlik, İdari Personel, Teknik Personel, Deneme Süreli Personel veya Diğer.",
            "Rol ve menü görünürlüğü gerekiyorsa ilgili rolü seçin.",
            "Kaydet butonuna basın.",
        ],
        [
            "BYS360’da TC yerine Sicil No kullanılmalıdır.",
            "Birim, üst birim ve yönetici bilgisi boş veya hatalıysa performans amir zinciri yanlış üretilebilir.",
            "Kullanıcı hesabı ve personel kaydı ilişkisi doğru kurulmalıdır.",
        ],
        [
            "Personel listesinde yeni kayıt görünmelidir.",
            "Personelin birimi, yöneticisi, rolü ve menü görünürlüğü doğru olmalıdır.",
            "Performans görev üretiminden önce personel organizasyon bilgisi kontrol edilmelidir.",
        ],
    )


def _role_matrix_answer() -> str:
    return _format_response(
        "Menü/yetki görünürlüğü veya rol matrisi sorununu çözmek istiyorsunuz.",
        "Sistem Ayarları > Rol Matrisi / Menü Yetkileri / Kullanıcı Bazlı Yetki",
        ["Admin", "Sistem Yöneticisi", "Yetkilendirme yönetimi verilmiş kullanıcı"],
        [
            "Sistem Ayarları bölümüne girin.",
            "Rol Matrisi veya Menü Yetkileri ekranını açın.",
            "İlgili rolü seçin.",
            "Açılacak modül ve alt sekmeleri işaretleyin; kapatılacakları kaldırın.",
            "Kullanıcı bazlı özel izin varsa ayrıca kontrol edin.",
            "Birim bazlı menü profili varsa ilgili birim profilini kontrol edin.",
            "Kaydet butonuna basın.",
            "İlgili kullanıcıyla çıkış-giriş yaparak menünün görünüp görünmediğini kontrol edin.",
        ],
        [
            "Bir menü kapalıysa kullanıcı o menüyü hiç görmemelidir; sadece tıklayınca erişim engeli vermek yeterli değildir.",
            "Backend route yetkisi de korunmalıdır; URL elle yazılsa bile yetkisiz veri dönmemelidir.",
            "Eski oturum veya tarayıcı cache’i nedeniyle değişiklik geç görünebilir.",
        ],
        [
            "Yetki verilen kullanıcı menüyü görmelidir.",
            "Yetki kapatılan kullanıcı menüyü hiç görmemelidir.",
            "Yetkisiz URL denemesinde kurumsal erişim engeli ekranı görünmelidir.",
        ],
    )


def _low_performance_answer() -> str:
    return _format_response(
        "70 altı düşük performans sürecini öğrenmek istiyorsunuz.",
        "Performans Yönetimi > Başkan/Üst Onayları > Süreç Takibi > Karne/Yayın",
        ["Başkan/Üst Yönetim", "Admin/Sistem Yöneticisi", "Performans Yetkilisi", "Yetki verilen yayın/onay sorumlusu"],
        [
            "Değerlendirme görevleri tamamlanır.",
            "Sistem nihai puanı hesaplar.",
            "Nihai puan 70’in altındaysa sonuç doğrudan kesinleşmez.",
            "Kayıt Başkan/Üst Onay sürecine alınır ve yayın kilidi oluşur.",
            "Başkan/Üst Onay karne inceleme ekranından değerlendirme incelenir.",
            "Onay veya iade işlemi yapılır.",
            "Onay tamamlanmadan personel karnesi yayınlanmaz.",
            "Aynı yıl ilk 70 altı ise düşük performans uyarısı kaydı oluşur.",
            "Aynı yıl ikinci 70 altı ise tekrarlayan düşük performans süreci başlatılır.",
            "Sistem otomatik idari işlem yapmazma yapmaz; yalnızca idari süreci takip edilebilir hale getirir.",
        ],
        [
            "Başkan onayı olmayan 70 altı sonuç personele kesin/yayınlanmış sonuç gibi gösterilmemelidir.",
            "Teknik statüler kullanıcıya Türkçe kurumsal ifadelerle gösterilmelidir.",
            "Sahte Başkan onayı kaydı üretilmemelidir; yalnızca gerçek 70 altı kayıtlar listelenmelidir.",
        ],
        [
            "Başkan Onayları ekranında gerçek kayıt görünmelidir.",
            "Karne yayın kilidi Başkan/Üst Onay tamamlanana kadar devam etmelidir.",
            "Onay sonrası süreç geçmişi ve personel geçmişi doğru işlenmelidir.",
        ],
    )


def _scorecard_answer() -> str:
    return _format_response(
        "Karne görünmeme nedenini kontrol etmek istiyorsunuz.",
        "Performans Yönetimi > Süreç Takibi / Başkan Onayları / Yayın Ön Onayı / Karne",
        ["Personel kendi yayınlanmış karnesini görür", "Admin/İK/Performans Yetkilisi süreç ve yayın kontrollerini yapar"],
        [
            "Önce değerlendirme görevlerinin tamamlanıp tamamlanmadığını kontrol edin.",
            "70 altı sonuç varsa Başkan/Üst Onay tamamlandı mı bakın.",
            "Yayın ön onayı gerekiyorsa Personel ve Destek Hizmetleri Grup Başkanı onayı tamamlandı mı kontrol edin.",
            "Admin/İK final yayın yaptı mı kontrol edin.",
            "Dönemin aktif/yayınlanmış durumda olup olmadığına bakın.",
            "Personelin rol/menü görünürlüğünde karne ekranı açık mı kontrol edin.",
        ],
        [
            "Personel sonuçları süreç tamamlanmadan ve yetkili yayın yapılmadan göremez.",
            "70 altı sonuçlarda Başkan/Üst Onay olmadan karne açılmaz.",
            "Yetki kapalıysa karne menüsü kullanıcıya görünmemelidir.",
        ],
        [
            "Yayınlandıktan sonra personel yalnızca kendi karnesini görmelidir.",
            "Yönetici sadece yetkili olduğu kapsamı görmelidir.",
            "Teknik kodlar yerine Türkçe statüler görünmelidir.",
        ],
    )


def _survey_answer() -> str:
    return _format_response(
        "Anket oluşturmak istiyorsunuz.",
        "İletişim ve Anket Yönetimi > Anketler",
        ["Admin", "Sistem Yöneticisi", "İletişim/Anket Yetkilisi", "Yetki verilmiş birim sorumlusu"],
        [
            "İletişim ve Anket Yönetimi bölümüne girin.",
            "Anketler sekmesini açın.",
            "Yeni Anket Oluştur butonuna basın.",
            "Anket başlığı ve açıklamasını yazın.",
            "Soru türlerini seçerek soruları ekleyin: seçenekli, açık uçlu veya puanlamalı.",
            "Hedef kitleyi seçin: tüm kurum, birim, grup veya seçili kullanıcılar.",
            "Başlangıç ve bitiş tarihlerini girin.",
            "Gizlilik/anonimlik ayarlarını kontrol edin.",
            "Kaydet veya Yayınla butonuna basın.",
        ],
        [
            "Asistan kişisel anket cevaplarını göstermez.",
            "Yalnızca yanıt bekleyen anket sayısı veya katılım özeti gibi güvenli özetler verilebilir.",
            "Hedef kitle ve anonimlik ayarı canlıya almadan önce kontrol edilmelidir.",
        ],
        [
            "Anket hedef kullanıcıların ekranında görünmelidir.",
            "Katılım raporu yetkili kullanıcıya görünmelidir.",
            "Yetkisiz kullanıcı kişisel cevapları görememelidir.",
        ],
    )


def _support_answer() -> str:
    return _format_response(
        "Destek talebi açmak veya takip etmek istiyorsunuz.",
        "Yardım Merkezi / Destek Talepleri",
        ["Tüm kullanıcılar kendi talebini açabilir", "Destek yetkilileri yetkili olduğu talepleri yönetir"],
        [
            "Yardım Merkezi veya Destek Talepleri ekranına girin.",
            "Yeni Destek Talebi butonuna basın.",
            "Kategori seçin.",
            "Konu başlığını yazın.",
            "Açıklama alanına sorunu anlaşılır şekilde yazın.",
            "Gerekirse ekran görüntüsü veya dosya ekleyin.",
            "Kaydet butonuna basın.",
            "Talep durumunu Destek Taleplerim ekranından takip edin.",
        ],
        [
            "Asistan destek talebi içeriğini veya ek dosyaları doğrudan göstermez.",
            "Sadece açık/bekleyen/cevaplanan talep sayısı gibi güvenli özet verebilir.",
        ],
        [
            "Talep numarası oluşmalıdır.",
            "Talep durumu listede görünmelidir.",
            "Cevap geldiyse kullanıcıya bildirim düşmelidir.",
        ],
    )


def _kpi_answer() -> str:
    return _format_response(
        "KPI/Hedef Yönetimi kullanmak istiyorsunuz.",
        "KPI / Hedef Yönetimi > Hedef Dönemleri / Hedef Kartları / KPI Ölçümleri",
        ["Başkan/Üst Yönetim", "Admin/Sistem Yöneticisi", "KPI/Hedef yetkilisi", "Yetki verilmiş yönetici"],
        [
            "KPI / Hedef Yönetimi ekranına girin.",
            "Önce Hedef Dönemi oluşturun: ad, başlangıç, bitiş, kapsam tipi.",
            "Hedef Kartları sekmesine geçin.",
            "Yeni hedef kartı oluşturun.",
            "Hedef tipini seçin: kurumsal, birim veya personel.",
            "Kategori seçin: KPI, operasyon veya stratejik.",
            "Sahip kişi veya birimi seçin.",
            "Hedef değer, gerçekleşen değer, ağırlık ve tarihleri girin.",
            "Kaydedin.",
            "KPI Ölçüm ekranında gerçekleşme değerini güncelleyip başarı oranını takip edin.",
        ],
        [
            "KPI performans puanını otomatik belirlemek zorunda değildir; bağlantı kuralı ayrıca tanımlanmalıdır.",
            "Yönetici dashboardlarında sadece yetkili kapsam görünmelidir.",
            "Riskli hedefler karar destek notu üretebilir ama nihai karar insana aittir.",
        ],
        [
            "Hedef kartı listede görünmelidir.",
            "Başarı/gerçekleşme oranı hesaplanmalıdır.",
            "Dashboard kartlarında yetki kapsamına göre görünmelidir.",
        ],
    )


def _ai_decision_answer() -> str:
    return _format_response(
        "AI Karar Destek’in ne yaptığını öğrenmek istiyorsunuz.",
        "AI Karar Destek Merkezi",
        ["Başkan/Üst Yönetim", "Admin/Sistem Yöneticisi", "Yetki verilmiş karar destek kullanıcıları"],
        [
            "AI Karar Destek Merkezi ekranına girin.",
            "Yetkili olduğunuz analiz başlığını seçin.",
            "Performans, destek, anket, KPI veya rapor özetini seçin.",
            "Sistem size özet, dikkat notu veya risk farkındalığı sunar.",
            "Çıktıyı karar yerine değil, insan denetimli değerlendirme desteği olarak kullanın.",
        ],
        [
            "AI karar vermez; performans puanı belirlemez; idari işlem tesis etmez.",
            "Hassas veri maskeleme, loglama ve yetki kontrolü korunmalıdır.",
            "Asistan ve AI Karar Destek farklıdır: Asistan öğretir/yönlendirir, AI Karar Destek analiz/özet üretir.",
        ],
        [
            "Yetkisiz veri özeti görünmemelidir.",
            "AI istek/yanıt logları ve redaksiyon kuralları çalışmalıdır.",
            "Çıktı nihai karar gibi değil, destek notu gibi sunulmalıdır.",
        ],
    )


def _general_answer() -> str:
    return (
        f"{WELCOME_TEXT}\n\n"
        "Bana günlük dille yazabilirsiniz. Örneğin “dönem açacağım”, “menü yok”, "
        "“personel ekleyeceğim”, “karne görünmüyor”, “anket oluşturacağım” dediğinizde "
        "ne yapmak istediğinizi BYS360 sınırlarında anlar ve sizi adım adım yönlendiririm.\n\n"
        "En çok yardımcı olduğum başlıklar:\n"
        "1. Personel Yönetimi: personel ekleme, birim, yönetici, izin ve vekâlet.\n"
        "2. Performans Yönetimi: dönem, kriter, görev üretimi, puanlama, Başkan/Üst Onay, karne ve raporlar.\n"
        "3. Sistem Ayarları: rol matrisi, menü görünürlüğü, kullanıcı/birim bazlı yetki.\n"
        "4. İletişim ve Anket: mesaj, duyuru, anket, geri bildirim ve destek talebi.\n"
        "5. KPI/Hedef: hedef dönemi, hedef kartı, gerçekleşme ve dashboard.\n"
        "6. AI Karar Destek: güvenli özet, analiz ve risk farkındalığı.\n\n"
        "Güvenlik sınırım: İdari karar vermem, performans puanı belirlemem, hassas veri göstermem, yetki sınırını aşmam."
    )


ANSWER_BUILDERS = {
    "WELCOME": _general_answer,
    "GENEL_REHBER": _general_answer,
    "PERFORMANS_DONEMI_OLUSTURMA": _performance_period_answer,
    "PERSONEL_EKLEME": _personnel_answer,
    "ROL_MATRISI_MENU": _role_matrix_answer,
    "YETKI_SINIRI": _role_matrix_answer,
    "BASKAN_ONAYI_70_ALTI": _low_performance_answer,
    "KARNE_GORUNMUYOR": _scorecard_answer,
    "ANKET_OLUSTURMA": _survey_answer,
    "DESTEK_TALEBI": _support_answer,
    "KPI_HEDEF": _kpi_answer,
    "AI_KARAR_DESTEK": _ai_decision_answer,
}


def is_supported_visible_tutor_v6(message: Any) -> bool:
    intent = detect_intent(message)
    return intent in ANSWER_BUILDERS and intent not in {"GENEL_REHBER", "WELCOME"} or bool(_normalize(message))


def answer_visible_tutor_v6(message: Any = "") -> str:
    intent = detect_intent(message)
    builder = ANSWER_BUILDERS.get(intent, _general_answer)
    return builder()


def try_answer_visible_tutor_v6(message: Any = "") -> str:
    """Bilinen BYS360 niyetlerinde öğretici cevap döndürür; tamamen boşsa karşılama verir."""
    return answer_visible_tutor_v6(message)


# Farklı service.py sürümleriyle uyumluluk için alias fonksiyonları.
def answer(message: Any = "", *args: Any, **kwargs: Any) -> str:
    return answer_visible_tutor_v6(message)


def build_response(message: Any = "", *args: Any, **kwargs: Any) -> str:
    return answer_visible_tutor_v6(message)


def assistant_reply(message: Any = "", *args: Any, **kwargs: Any) -> str:
    return answer_visible_tutor_v6(message)


def generate_reply(message: Any = "", *args: Any, **kwargs: Any) -> str:
    return answer_visible_tutor_v6(message)


def get_answer(message: Any = "", *args: Any, **kwargs: Any) -> str:
    return answer_visible_tutor_v6(message)


def bys360_assistant_answer(message: Any = "", *args: Any, **kwargs: Any) -> str:
    return answer_visible_tutor_v6(message)


if __name__ == "__main__":
    for sample in [
        "performans dönemi oluşturmayı sordum",
        "dönem açacağım",
        "menü yok",
        "personel ekleyeceğim",
        "70 altı performans sonucu ne olur",
        "anket nasıl oluşturulur",
        "KPI hedefleri nereden takip edilir",
        "doğal ve anlaşılır şekilde yönlendir",
    ]:
        ops_logger.info(" ".join(str(x) for x in ("-----", sample)))
        ops_logger.info(str(answer_visible_tutor_v6(sample)[:700]))
