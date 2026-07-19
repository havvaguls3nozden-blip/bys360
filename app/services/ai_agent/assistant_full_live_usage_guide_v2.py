from __future__ import annotations

# BYS360_ASSISTANT_FULL_LIVE_USAGE_GUIDE_V2
from dataclasses import dataclass
from typing import Any

VERSION = "BYS360 Asistanı Tam Canlı Kullanım Rehberi V2"
MODE = "Ekran, rol ve süreç bazlı adım adım canlı kullanım rehberi"
ASSISTANT_NAME = "BYS360 Asistanı"
NOTICE = "BYS360 Asistanı idari karar vermez, performans puanı üretmez, onay/ret işlemi yapmaz ve yetki dışı hassas veri göstermez."
SECURITY_NOTICE = "Bu yanıt kullanım rehberi ve güvenli yönlendirme amaçlıdır. Gerçek işlem ilgili ekranda yetkili kullanıcı tarafından yapılır."

INTRO_TITLE = "Merhaba, ben BYS360 Asistanı"
INTRO_TEXT = (
    "BYS360 içinde hangi işlemi nereden yapacağınızı adım adım anlatırım. "
    "Personel, performans, izin, vekâlet, rol matrisi, destek, anket, KPI/Hedef ve AI Karar Destek ekranlarında size güvenli kullanım yolu gösteririm."
)
INTRO_SECURITY_TEXT = "İdari karar vermem, performans puanı belirlemem ve yetkiniz dışındaki hassas verileri göstermem."

EXAMPLE_QUESTIONS = (
    "Personel nasıl eklenir?",
    "Performans dönemi nasıl açılır?",
    "Puanlama ekranı nasıl kullanılır?",
    "Başkan onayları nasıl kullanılır?",
    "70 altı performans süreci nasıl ilerler?",
    "Rol matrisinden menü nasıl açılır?",
    "İzin ve vekâlet işlemleri nasıl yapılır?",
    "KPI hedefleri nereden takip edilir?",
)

ROLE_EXAMPLES = {
    "personnel": ("Karnemi nereden görürüm?", "İzin talebi nasıl oluşturulur?", "Destek talebi nasıl açılır?", "Anketi nasıl cevaplarım?"),
    "supervisor": ("Puanlama görevlerim nerede?", "Önceki amir görüşünü nerede görürüm?", "Dönem içi not nasıl incelenir?", "Karne yayınlandı mı?"),
    "coordinator": ("Koordinatör hangi performans kayıtlarını görür?", "Ekip ortalamasını nereden takip ederim?", "Aksatan amir raporu nerede?", "Gelişim önerisi nasıl yazılır?"),
    "group_head": ("Grup Başkanı hangi raporları görür?", "Yayın öncesi kontrol nasıl yapılır?", "Düşük performansları nereden takip ederim?", "Kategori ortalaması nerede?"),
    "president": ("Başkan onayı bekleyenler nerede?", "70 altı karne nasıl incelenir?", "Riskli personel analizi nerede?", "KPI dashboardu nasıl okunur?"),
    "admin": ("Rol matrisi nasıl güncellenir?", "Menü görünürlüğü neden değişmedi?", "Sistem ayarları nasıl kontrol edilir?", "Gate kontrolü nasıl çalıştırılır?"),
    "hr_performance": ("Dönem nasıl açılır?", "Görev üretimi nasıl yapılır?", "Karne nasıl yayınlanır?", "Geçmiş puan arşivi nasıl yüklenir?"),
}

@dataclass(frozen=True)
class GuideTopic:
    key: str
    title: str
    keywords: tuple[str, ...]
    answer: str
    actions: tuple[tuple[str, str, str], ...] = ()
    allowed_roles: tuple[str, ...] = ("all",)
    quick_replies: tuple[str, ...] = ()
    section: str = "Genel"


def _norm(value: Any) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
        .replace("İ", "i")
        .replace("I", "i")
        .replace("ı", "i")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ö", "o")
        .replace("ç", "c")
    )


def _role_from_user(user: Any) -> str:
    candidates: list[str] = []
    for attr in (
        "role", "role_name", "role_key", "user_role", "authority_role", "position", "title", "unvan", "job_title",
        "permission_role", "display_role", "primary_role",
    ):
        try:
            value = getattr(user, attr, None)
            if value:
                candidates.append(str(value))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/ai_agent/assistant_full_live_usage_guide_v2.py)")
    try:
        if bool(getattr(user, "is_admin", False)) or bool(getattr(user, "is_superuser", False)):
            return "admin"
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/ai_agent/assistant_full_live_usage_guide_v2.py)")
    joined = _norm(" ".join(candidates))
    if any(x in joined for x in ("sistem", "admin", "yonetici", "superuser", "system")):
        return "admin"
    if any(x in joined for x in ("personel ve destek", "insan kaynak", "ik", "performans yetkilisi", "hr")):
        return "hr_performance"
    if any(x in joined for x in ("baskan yardimcisi", "ust yonetim", "üst yonetim")):
        return "upper_management"
    if "baskan" in joined or "başkan" in joined:
        return "president"
    if any(x in joined for x in ("grup baskani", "grup başkani", "grup başkanı")):
        return "group_head"
    if "koordinator" in joined or "koordinat" in joined:
        return "coordinator"
    if any(x in joined for x in ("amir", "degerlendirici", "değerlendirici")):
        return "supervisor"
    return "personnel"


def _role_label(role: str) -> str:
    return {
        "admin": "Sistem Yöneticisi/Admin",
        "president": "Başkan/Üst Yönetim",
        "upper_management": "Üst Yönetim",
        "group_head": "Grup Başkanı",
        "coordinator": "Koordinatör",
        "supervisor": "Amir/Değerlendirici",
        "hr_performance": "Personel/Performans Yetkilisi",
        "personnel": "Standart Kullanıcı/Personel",
    }.get(role, "Kullanıcı")


def _role_scope_note(role: str) -> str:
    if role in ("admin", "president", "upper_management"):
        return "Genel görünüm veya yönetim ekranları yalnızca sistemde tanımlı yetkiniz kadar açılır; hassas veri yine rol ve menü yetkisine bağlıdır."
    if role == "group_head":
        return "Grup Başkanı olarak kendi grup/üst birim kapsamınız dışındaki personel detaylarına yönlendirme yapılmamalıdır."
    if role == "coordinator":
        return "Koordinatör olarak yalnızca kendi çalışma grubu veya koordinasyon kapsamınızdaki kayıtları görmelisiniz."
    if role == "supervisor":
        return "Amir olarak yalnızca size atanmış değerlendirme görevleri ve yetkili olduğunuz personel görünmelidir."
    if role == "hr_performance":
        return "Personel/Performans yetkilisi işlemleri rol matrisi, menü görünürlüğü ve görev kapsamıyla sınırlıdır."
    return "Standart kullanıcı olarak yalnızca kendi hesabınıza, kendi bildirimlerinize, kendi taleplerinize ve yayınlanmış kendi karnenize erişirsiniz."


def _action(label: str, route: str, description: str = "") -> dict[str, str]:
    return {
        "label": label,
        "title": label,
        "route": route,
        "url": route,
        "description": description or "BYS360 içinde güvenli yönlendirme",
        "safety_level": "rehber_yonlendirme",
    }


def _topic_actions(topic: GuideTopic) -> list[dict[str, str]]:
    return [_action(label, route, description) for label, route, description in topic.actions]


def _role_quick_replies(role: str) -> list[str]:
    role_specific = list(ROLE_EXAMPLES.get(role, ()))
    base = [q for q in EXAMPLE_QUESTIONS]
    result: list[str] = []
    for item in role_specific + base:
        if item not in result:
            result.append(item)
    return result[:8]


def get_bys360_assistant_intro_payload(user: Any = None) -> dict[str, Any]:
    role = _role_from_user(user)
    return {
        "assistant_name": ASSISTANT_NAME,
        "title": INTRO_TITLE,
        "subtitle": INTRO_TEXT,
        "security_text": INTRO_SECURITY_TEXT,
        "version": VERSION,
        "mode": MODE,
        "detected_role": role,
        "detected_role_label": _role_label(role),
        "role_note": _role_scope_note(role),
        "example_questions": _role_quick_replies(role),
        "sections": ["Genel Kullanım", "Personel", "İzin/Vekâlet", "Performans", "İletişim/Anket/Destek", "Ayarlar", "AI/KPI"],
    }


def _reply(topic: GuideTopic, user: Any, question: str) -> dict[str, Any]:
    role = _role_from_user(user)
    answer = topic.answer.strip().replace("{{ROLE_NOTE}}", _role_scope_note(role))
    quick_replies = list(topic.quick_replies) if topic.quick_replies else _role_quick_replies(role)
    return {
        "ok": True,
        "version": VERSION,
        "mode": MODE,
        "assistant_name": ASSISTANT_NAME,
        "intent": topic.key,
        "topic_title": topic.title,
        "section": topic.section,
        "detected_role": role,
        "detected_role_label": _role_label(role),
        "question": str(question or ""),
        "answer": answer,
        "actions": _topic_actions(topic),
        "quick_replies": quick_replies,
        "notice": NOTICE,
        "security_notice": SECURITY_NOTICE,
        "automation_notice": "BYS360 Asistanı işlem yapmaz; kullanıcıyı doğru ekrana ve doğru adıma yönlendirir.",
        "assistant_panel_notice": INTRO_TEXT,
        "intro": get_bys360_assistant_intro_payload(user),
    }


def _topic(key: str, title: str, keywords: tuple[str, ...], answer: str, actions: tuple[tuple[str, str, str], ...] = (), quick: tuple[str, ...] = (), section: str = "Genel") -> GuideTopic:
    return GuideTopic(key=key, title=title, keywords=keywords, answer=answer, actions=actions, quick_replies=quick, section=section)


TOPICS: tuple[GuideTopic, ...] = (
    _topic("assistant_identity", "BYS360 Asistanı ne yapar?", ("sen kimsin", "adın ne", "adin ne", "ne yapabilirsin", "asistan", "yardım", "yardim", "kullanım rehberi", "kullanim rehberi", "örnek soru", "ornek soru"), """
Ben BYS360 Asistanı. Amacım BYS360’da hangi işlemi nereden ve hangi sırayla yapacağınızı adım adım anlatmaktır.

Kullanım mantığım:
1. Önce yapmak istediğiniz işlemi anlarım.
2. İlgili modülü ve ekranı söylerim.
3. İşlem adımlarını sıralarım.
4. Yetki gerekiyorsa bunu açıkça belirtirim.
5. İdari karar, puanlama kararı, onay/ret veya hassas veri gösterimi yapmam.

Açıldığımda örnek sorularım da bu mantığa göre güncellenir: personel ekleme, dönem açma, puanlama, Başkan onayı, rol matrisi, izin/vekâlet, destek, anket ve KPI/Hedef kullanımı.

Yetki notu: {{ROLE_NOTE}}
    """, (("BYS360 Asistanı Paneli", "/ai-agent/panel", "Asistan panelini açar"), ("Asistan Bilgi Bankası", "/ai-agent/knowledge", "Kullanım rehberlerini gösterir")), section="Genel Kullanım"),

    _topic("home_navigation", "Ana sayfa, sol menü ve genel gezinme", ("ana ekran", "anasayfa", "home", "sol menü", "sol menu", "menü nerede", "menu nerede", "modül nerede", "modul nerede", "ekran nerede"), """
Ana sayfa ve sol menüyü kullanmak için:
1. Giriş yaptıktan sonra ana sayfadaki modül kartlarını ve bildirim alanını kontrol edin.
2. Sol menüden işlem yapmak istediğiniz ana modülü açın.
3. Alt sekmeler rol matrisindeki yetkinize göre görünür; görünmeyen sekmeler için yetki kontrolü gerekir.
4. Görev, anket, destek, performans veya mesaj uyarıları bildirim alanında takip edilir.
5. Bir bağlantı beyaz ekran veya erişim engeli verirse önce menü görünürlüğü ve backend route yetkisi kontrol edilmelidir.

Yetki notu: {{ROLE_NOTE}}
    """, (("Ana Sayfa", "/home", "BYS360 ana sayfası"), ("Bildirimler", "/notifications", "Kullanıcı bildirimleri")), section="Genel Kullanım"),

    _topic("profile_account", "Profil ve hesap kullanımı", ("profil", "hesabım", "hesabim", "gizli erişim bilgisi", "gizli erişim bilgisi", "parola", "çıkış", "cikis", "oturum", "fotoğraf", "fotograf"), """
Profil ve hesap işlemleri için:
1. Sağ üst kullanıcı alanından profil veya hesap ekranına girin.
2. Kendi profil bilgilerinizi, görev/unvan görünümünüzü ve varsa fotoğraf alanınızı kontrol edin.
3. gizli erişim bilgisi/parola değişikliği varsa güvenlik kurallarına uygun yeni parola girin.
4. İşiniz bittiğinde güvenli çıkış yapın.
5. Profilde birim, görev, unvan veya yönetici bilgisi hatalıysa bunu personel yetkilisi düzeltmelidir.

Asistan parola göstermez, parola sıfırlamaz ve kullanıcı adına işlem yapmaz.

Yetki notu: {{ROLE_NOTE}}
    """, (("Profil", "/profile", "Kullanıcı profil ekranı"),), section="Genel Kullanım"),

    _topic("notifications", "Bildirimler ve bekleyen işler", ("bildirim", "bildirimler", "bekleyen iş", "bekleyen is", "uyarı", "uyari", "görev geldi", "gorev geldi", "okunmamış", "okunmamis"), """
Bildirimleri takip etmek için:
1. Ana sayfa veya üst menüdeki bildirim alanını açın.
2. Okunmamış bildirimleri ve size atanmış görevleri kontrol edin.
3. Performans görevi, anket, destek cevabı veya sistem duyurusu gibi bildirimleri ilgili ekrana giderek tamamlayın.
4. Bildirim görünmüyorsa ilgili modülün rol matrisi ve menü görünürlüğü kontrol edilmelidir.
5. Süresi yaklaşan performans görevleri ve aksatan amir uyarıları burada takip edilebilir.

Yetki notu: {{ROLE_NOTE}}
    """, (("Bildirimler", "/notifications", "Bildirim listesi"),), section="Genel Kullanım"),

    _topic("personnel_list", "Personel listesi ve personel arama", ("personel listesi", "personel ara", "personel nerede", "personel bul", "sicil ara", "personel kartı", "personel karti"), """
Personel listesi kullanımı:
1. Sol menüden Personel Yönetimi bölümüne girin.
2. Personel Listesi veya Personel Özlük Dosyaları ekranını açın.
3. Sicil No, ad soyad, birim, üst birim, unvan veya durum filtreleriyle arama yapın.
4. Personel kartına girerek temel bilgileri, birim ilişkisini, izin/vekâlet durumunu ve performans bağlantısını kontrol edin.
5. Yetkiniz yoksa kişi detayları görünmemelidir.

Yetki notu: {{ROLE_NOTE}}
    """, (("Personel Yönetimi", "/personnel", "Personel ana ekranı"),), section="Personel"),

    _topic("personnel_create", "Personel ekleme", ("personel ekle", "personel nasıl", "personel nasil", "yeni personel", "personel oluştur", "personel olustur", "personel kaydı", "personel kaydi", "sicil no", "sicil", "özlük", "ozluk"), """
Personel eklemek için:
1. Personel Yönetimi bölümünü açın.
2. Personel Listesi veya Personel Özlük Dosyaları ekranında Yeni Personel / Personel Ekle butonuna basın.
3. Sicil No, ad soyad, unvan, birim, üst birim ve yönetici alanlarını doldurun.
4. Varsa profil fotoğrafı, iletişim bilgisi, görev durumu ve başlangıç bilgilerini ekleyin.
5. Personel kategori/grup alanında doğru sınıfı seçin: Güvenlik, Temizlik, İdari Personel, Teknik Personel, Deneme Süreli Personel veya Diğer.
6. Kaydedin ve personelin rol/menü görünürlüğünü ayrıca kontrol edin.
7. Performans zinciri bu personel verisinden beslendiği için birim, yönetici ve kategori alanları boş bırakılmamalıdır.

BYS360’da TC yerine Sicil No esas alınır.

Yetki notu: {{ROLE_NOTE}}
    """, (("Personel Yönetimi", "/personnel", "Personel kayıt ekranı"), ("Rol Matrisi", "/admin/role-matrix", "Rol ve menü görünürlüğü")), ("Personel kategorisi nasıl seçilir?", "Rol matrisi nasıl ayarlanır?", "İzin ve vekâlet nasıl bağlanır?"), "Personel"),

    _topic("personnel_edit", "Personel bilgisi düzenleme", ("personel düzenle", "personel duzenle", "bilgi güncelle", "bilgi guncelle", "birim değişti", "birim degisti", "unvan değişti", "yönetici değişti", "yonetici degisti"), """
Personel bilgisi düzenleme adımları:
1. Personel Yönetimi > Personel Listesi ekranında ilgili personeli bulun.
2. Personel kartını açın ve düzenleme yetkiniz varsa güncelle butonuna basın.
3. Sicil No gibi temel alanları dikkatli kontrol edin; mükerrer kayıt oluşturmamaya dikkat edin.
4. Birim, üst birim, unvan, yönetici ve kategori değişiklikleri performans zincirini etkileyebilir.
5. Değişiklikten sonra organizasyon geçmişi ve amir zinciri/görev üretimi kontrol edilmelidir.
6. Gerekirse rol matrisi veya kişi bazlı menü görünürlüğü yeniden düzenlenir.

Yetki notu: {{ROLE_NOTE}}
    """, (("Personel Yönetimi", "/personnel", "Personel listesi"), ("Organizasyon Birimleri", "/org-units", "Birim yapısı")), section="Personel"),

    _topic("personnel_category", "Personel kategori/grup seçimi", ("kategori", "personel kategori", "grup ortalaması", "grup ortalamasi", "güvenlik", "guvenlik", "temizlik", "idari personel", "teknik personel", "deneme süreli", "deneme sureli"), """
Personel kategori/grup kullanımı:
1. Personel kartında kategori alanını bulun.
2. Personelin görev niteliğine göre Güvenlik, Temizlik, İdari Personel, Teknik Personel, Deneme Süreli Personel veya Diğer seçin.
3. Bu kategori performans dönem kapsamı, kategori ortalaması ve rapor filtrelerinde kullanılır.
4. Personel kendi kategori/grup ortalamasını kişi detayı olmadan görebilir.
5. Koordinatör ve Grup Başkanı yalnızca yetkili olduğu organizasyon/kategori kapsamını görmelidir.

Yetki notu: {{ROLE_NOTE}}
    """, (("Personel Yönetimi", "/personnel", "Personel kategori seçimi"), ("Performans Raporları", "/performance/reports", "Kategori filtreli performans raporları")), section="Personel"),

    _topic("org_units", "Organizasyon ve birim yönetimi", ("birim", "üst birim", "ust birim", "organizasyon", "çalışma grubu", "calisma grubu", "koordinatörlük", "koordinatorluk", "grup başkanlığı", "grup baskanligi"), """
Organizasyon/birim yönetimi için:
1. Personel Yönetimi veya yönetim menüsünden Organizasyon/Birim ekranına girin.
2. Birim, üst birim, çalışma grubu, koordinatörlük ve grup başkanlığı ilişkilerini kontrol edin.
3. Birim değişikliklerinde personelin bağlı olduğu yönetici ve performans amir zinciri etkilenir.
4. Geçmiş organizasyon kayıtları korunmalı, canlı zincir doğru atanmalıdır.
5. Risk/eksik veri uyarıları varsa personel ve birim bağlantıları tamamlanmalıdır.

Yetki notu: {{ROLE_NOTE}}
    """, (("Organizasyon Birimleri", "/org-units", "Birim ve üst birim yönetimi"),), section="Personel"),

    _topic("leave_request", "İzin işlemleri", ("izin", "izin talebi", "izin nasıl", "izin nasil", "izin kaydı", "izin kaydi", "leave", "izin bakiyesi", "izin onayı", "izin onayi"), """
İzin işlemleri için:
1. Personel Yönetimi altında İzinler / İzin Talepleri ekranını açın.
2. Yeni izin talebi oluşturun veya mevcut izin kayıtlarını inceleyin.
3. İzin türü, başlangıç-bitiş tarihi, açıklama ve varsa ek belge alanlarını doldurun.
4. Yetkili amir/onay akışına gönderin.
5. İzinli amir/personel bilgisi performans ve vekâlet süreçlerini etkileyebilir.
6. İzin onaylandıktan sonra devamsızlık, takvim ve vekâlet bilgileri kontrol edilmelidir.

Yetki notu: {{ROLE_NOTE}}
    """, (("İzin İşlemleri", "/personnel/leaves", "İzin kayıtları ve talepleri"),), section="İzin/Vekâlet"),

    _topic("delegation", "Vekâlet işlemleri", ("vekâlet", "vekalet", "vekil", "görev devri", "gorev devri", "amir izinli", "vekalet ata", "vekâlet ata"), """
Vekâlet işlemleri için:
1. Personel Yönetimi altında Vekâlet / Görev Devri ekranına girin.
2. Asıl kullanıcıyı, vekil kullanıcıyı, başlangıç ve bitiş tarihlerini seçin.
3. Hangi süreçlerde vekâlet geçerli olacaksa kapsamını belirleyin.
4. Kaydettikten sonra bildirim ve görev yönlendirmelerini kontrol edin.
5. Performans döneminde amir izinliyse vekâlet görev akışının boşa düşmesini engeller.
6. Süresi biten vekâletler otomatik pasifleşmeli veya yetkili kişi tarafından kapatılmalıdır.

Yetki notu: {{ROLE_NOTE}}
    """, (("Vekâlet İşlemleri", "/personnel/delegations", "Vekâlet kayıtları"),), section="İzin/Vekâlet"),

    _topic("attendance", "Devamsızlık ve istisna kayıtları", ("devamsızlık", "devamsizlik", "puantaj", "attendance", "istisna", "mazeret", "geç kalma", "gec kalma"), """
Devamsızlık/istisna kayıtları için:
1. Personel Yönetimi altında Devamsızlık veya İstisna kayıtları ekranını açın.
2. Personel, tarih, olay türü ve açıklama bilgilerini kontrol edin.
3. İzin kaydıyla ilişkili durumlarda mükerrer veya çelişkili kayıt oluşmamasına dikkat edin.
4. Bu kayıtlar raporlama ve yönetici görünürlüğünde analiz amaçlı kullanılabilir.
5. Hassas personel verisi yalnızca yetkili kapsamda görünmelidir.

Yetki notu: {{ROLE_NOTE}}
    """, (("Devamsızlık", "/personnel/attendance", "Devamsızlık ve istisna kayıtları"),), section="İzin/Vekâlet"),

    _topic("performance_overview", "Performans Yönetimi genel kullanım", ("performans", "performans yönetimi", "performans yonetimi", "performans ekranı", "performans ekrani", "performans nasıl", "performans nasil"), """
Performans Yönetimi genel akışı:
1. Dönem hazırlanır ve kapsamı belirlenir.
2. Değerlendirme kriterleri kontrol edilir.
3. Personel, kategori, birim, amir, izin ve vekâlet verileri doğrulanır.
4. Sistem gerçek amir zincirine göre değerlendirme görevleri üretir.
5. Amirler işlem sırasına göre puan ve görüş girişlerini tamamlar.
6. Sistem nihai puan, açıklama zorunluluğu, 70 altı/90 üstü kuralı ve onay ihtiyacını kontrol eder.
7. Gerekli Başkan/Üst Onay ve yayın ön onayı tamamlanır.
8. Admin/İK yetkilisi yayını yapınca personel karnesini görebilir.

Yetki notu: {{ROLE_NOTE}}
    """, (("Performans Yönetimi", "/performance", "Performans ana ekranı"),), section="Performans"),

    _topic("performance_period", "Performans dönemi açma", ("dönem aç", "donem ac", "performans dönemi", "performans donemi", "yeni dönem", "yeni donem", "dönem yönetimi", "donem yonetimi", "özel dönem", "ozel donem"), """
Performans dönemi açmak için:
1. Performans Yönetimi > Dönem Yönetimi ekranına girin.
2. Yeni dönem oluştur butonunu kullanın.
3. Dönem adını, türünü ve tarih aralığını girin. Örnek: yıllık, 6 aylık, 3 aylık, aylık veya özel dönem.
4. Kapsam tipini seçin: tüm kurum, birim, üst birim, kategori/grup veya seçili personel.
5. Dönem kapsamı özel ise ilgili birim/kategori/personel listesini seçin.
6. Çakışan dönem uyarısı varsa inceleyin.
7. Kaydettikten sonra kriterleri ve görev üretimini kontrol edin.

Yetki notu: {{ROLE_NOTE}}
    """, (("Dönem Yönetimi", "/performance/periods", "Performans dönemleri"),), ("Kriter nasıl tanımlanır?", "Görev üretimi nasıl yapılır?", "Kategoriye özel dönem nasıl açılır?"), "Performans"),

    _topic("performance_criteria", "Değerlendirme kriterleri", ("kriter", "değerlendirme kriterleri", "degerlendirme kriterleri", "yetkinlik değil", "yetkinlik degil", "puan kriteri", "kriter ekle"), """
Değerlendirme kriterleri için:
1. Performans Yönetimi > Kriter Yönetimi ekranına girin.
2. Yeni kriter ekleyin veya mevcut kriterleri düzenleyin.
3. Kriter adını, açıklamasını, aktif/pasif durumunu ve varsa ağırlığını kontrol edin.
4. Ekranlarda ana ifade “Değerlendirme Kriterleri” olmalıdır; “Yetkinlik” ana terim olarak kullanılmamalıdır.
5. Kriterler dönemle ilişkilendirilmeden görev üretimi sağlıklı çalışmaz.
6. Değişiklik sonrası puanlama ekranında kriterlerin görünüp görünmediğini kontrol edin.

Yetki notu: {{ROLE_NOTE}}
    """, (("Kriter Yönetimi", "/performance/criteria", "Değerlendirme kriterleri"),), section="Performans"),

    _topic("performance_assignments", "Amir zinciri ve görev üretimi", ("amir zinciri", "görev üret", "gorev uret", "değerlendirme görevi", "degerlendirme gorevi", "1. amir", "2. amir", "3. amir", "koordinatör", "grup başkanı"), """
Amir zinciri ve görev üretimi için:
1. Dönem ve kriterler hazır olduktan sonra Görev Üretimi / Amir Zinciri ekranını açın.
2. Personel birim, üst birim, yönetici, kategori, izin ve vekâlet verilerini kontrol edin.
3. Sistem gerçek hiyerarşiye göre görev üretmelidir; sahte bekleme veya boş 3. amir görevi oluşmamalıdır.
4. Çok seviyeli yapılarda işlem sırası genellikle varsa 3. amir, sonra 2. amir, en son 1. amirdir.
5. Sonraki amir önceki amirin puan ve kanaatini görebilmelidir; kör değerlendirme yoktur.
6. Hukuk Müşavirliği ve Başkanın tek puanladığı özel roller için istisna kuralları korunmalıdır.

Yetki notu: {{ROLE_NOTE}}
    """, (("Görev Üretimi", "/performance/assignments", "Değerlendirme görevleri"),), section="Performans"),

    _topic("third_supervisor", "3. amir opsiyonelliği", ("3. amir", "üçüncü amir", "ucuncu amir", "yorum modu", "puan modu", "3 amir sütunu", "3 amir sutunu"), """
3. amir kullanımı:
1. 3. amir her personel için zorunlu değildir.
2. Sistem ayarından 3. amir görünürlüğü ve modu kontrol edilir.
3. 3. amir yoksa tabloda boş sütun, boş görev veya “bekliyor” statüsü görünmemelidir.
4. Yorum modunda 3. amir sadece görüş yazar, puana etkisi olmaz.
5. Puan modunda 3. amir ağırlık hesabına dahil edilir ve toplam ağırlık %100 kalmalıdır.
6. Ekranda “puan bekliyor” yerine moda uygun “yorum/görüş bekliyor” veya “puanlama bekliyor” yazmalıdır.

Yetki notu: {{ROLE_NOTE}}
    """, (("Performans Ayarları", "/settings/performance", "3. amir modu ve görünürlük ayarları"),), section="Performans"),

    _topic("scoring", "Puanlama ekranı", ("puanlama", "puan ver", "değerlendir", "degerlendir", "puanlama ekranı", "puanlama ekrani", "1 puan", "5 puan", "açıklama zorunlu", "aciklama zorunlu"), """
Puanlama ekranı kullanımı:
1. Performans Yönetimi > Puanlama Görevlerim ekranına girin.
2. Size atanmış personel/değerlendirme görevini açın.
3. Her değerlendirme kriteri için 1-5 arası puan girin.
4. Sistem bu puanları 100’lük skala ve ağırlıklandırma ile nihai puana dönüştürür.
5. 1 veya 5 puanda açıklama zorunluluğu sistem ayarına bağlıdır; açıksa açıklama girmeden kaydedemezsiniz.
6. 70 altı veya 90 üstü sonuçlarda ayrıntılı genel görüş istenebilir.
7. Sonraki amir, önceki amirin puan ve kanaatini görerek değerlendirme yapar.
8. Kaydetmeden önce puan, açıklama ve genel görüş alanlarını kontrol edin.

Yetki notu: {{ROLE_NOTE}}
    """, (("Puanlama Görevlerim", "/performance/scoring", "Atanmış değerlendirme görevleri"),), section="Performans"),

    _topic("scorecard", "Karne görüntüleme", ("karne", "performans karnesi", "karnemi", "karne nerede", "sonucumu", "sonuç", "sonuc", "puanımı", "puanimi"), """
Karne görüntüleme:
1. Personel karnesi süreç tamamlanmadan ve yetkili yayın yapılmadan personele açılmaz.
2. Yayın sonrası Personel kendi karne ekranına girerek nihai puanı, kriter sonuçlarını ve açıklamaları görebilir.
3. Amirler ve yöneticiler yalnızca yetkili oldukları kapsamın karnelerini görmelidir.
4. 70 altı karneler gerekli Başkan/Üst Onay ve yayın ön onayı tamamlanmadan kesin/yayınlanmış sayılmaz.
5. Karne ekranında teknik ifadeler değil, Türkçe kurumsal durumlar gösterilmelidir.

Yetki notu: {{ROLE_NOTE}}
    """, (("Karne", "/performans/v2/faz5/scorecard", "Personel performans karnesi"), ("Geçmiş Karne Arşivi", "/performans/gecmis-karne-arsivi", "Geçmiş yıllar")), section="Performans"),

    _topic("low_score_approval", "70 altı düşük performans süreci", ("70 altı", "70 alti", "düşük performans", "dusuk performans", "başkan onayı", "baskan onayi", "üst onay", "ust onay", "başkan onayları", "baskan onaylari"), """
70 altı performans süreci:
1. Nihai performans başarı puanı 70’in altında kalırsa sonuç doğrudan kesinleşmez.
2. Kayıt Başkan/Üst Onay sürecine düşer.
3. Başkan/Üst Onay tamamlanmadan karne personele yayınlanmaz.
4. İlk 70 altı sonuçta düşük performans uyarısı ve personel süreç kaydı oluşur.
5. Aynı yıl ikinci 70 altı sonuçta tekrarlayan düşük performans süreci başlar.
6. Sistem otomatik idari işlem yapmazma yapmaz; yalnızca idari süreç başlatılacak statüsü üretir.
7. Ekranda teknik kodlar değil “Başkan Onayı Bekliyor”, “Başkan Onayı Yayın Kilidi”, “Düşük Performans Uyarısı Oluşturuldu” gibi Türkçe ifadeler görünmelidir.

Yetki notu: {{ROLE_NOTE}}
    """, (("Başkan Onayları", "/performance/president-approvals", "70 altı onay kayıtları"),), ("Başkan onayı nasıl kullanılır?", "Karne ne zaman yayınlanır?", "Yayın ön onayı nedir?"), "Performans"),

    _topic("president_approvals", "Başkan Onayları ekranı", ("başkan onayları", "baskan onaylari", "başkan onayı ekranı", "baskan onayi ekrani", "karne inceleme", "onayla", "iade et", "reddet"), """
Başkan Onayları ekranı kullanımı:
1. Performans Yönetimi > Başkan Onayları sekmesine girin.
2. Listede yalnızca gerçek 70 altı nihai performans kayıtları görünmelidir.
3. İlgili kaydın Karne İncelemesi sayfasını açın.
4. Personel bilgisi, dönem, nihai puan, kriter puanları, amir görüşleri, puanlama geçmişi ve süreç geçmişini inceleyin.
5. Uygun yetkiye sahipseniz onay veya iade/ret işlemini yapın.
6. Onaydan sonra süreç yayın ön onayı ve final yayın adımlarına ilerler.
7. Başkan Onayları sekmesi sadece Başkan ve Admin/Sistem Yöneticisi gibi yetkili rollerde görünmelidir.

Asistan onay/ret yapmaz; yalnızca ekranın kullanımını anlatır.

Yetki notu: {{ROLE_NOTE}}
    """, (("Başkan Onayları", "/performance/president-approvals", "Başkan/Üst Onay listesi"),), section="Performans"),

    _topic("publish_preapproval", "Personel ve Destek Hizmetleri Grup Başkanı yayın ön onayı", ("yayın ön onayı", "yayin on onayi", "personel ve destek", "final yayın", "final yayin", "karne yayın", "karne yayin", "yayınlama", "yayinlama"), """
Yayın ön onayı akışı:
1. Tüm değerlendirme/puanlama görevleri tamamlanır.
2. 70 altı kayıt varsa Başkan/Üst Onay tamamlanır.
3. Sonuçlar Admin/İK tarafından doğrudan yayınlanmadan önce Personel ve Destek Hizmetleri Grup Başkanı yayın ön onayına düşer.
4. Yayın ön onayı verilirse Admin/İK yetkilisi nihai yayını yapabilir.
5. Bu adım tamamlanmadan personel sonuçları kesin yayınlanmış kabul edilmemelidir.
6. Yayın ön onayı ekranında Türkçe, anlaşılır süreç durumu gösterilmelidir.

Yetki notu: {{ROLE_NOTE}}
    """, (("Yayın Ön Onayı", "/performance/publish-preapproval", "Final yayın ön kontrolü"),), section="Performans"),

    _topic("archive", "Geçmiş yıl karne/puan arşivi", ("geçmiş karne", "gecmis karne", "karne arşivi", "karne arsivi", "eski puan", "2024", "2025", "excel import", "geçmiş puan"), """
Geçmiş yıl karne/puan arşivi kullanımı:
1. Performans Yönetimi > Geçmiş Karne/Puan Arşivi ekranına girin.
2. Manuel eski puan ekleme veya Excel/import seçeneğini kullanın.
3. Yıl, dönem, puan, açıklama ve kaynak belge bilgilerini doldurun.
4. Personel yalnızca kendi geçmiş performansını görmelidir.
5. Koordinatör, Grup Başkanı ve yöneticiler yalnızca yetkili oldukları kapsamın geçmişini görmelidir.
6. Başkan/Admin genel geçmiş arşive erişebilir.

Yetki notu: {{ROLE_NOTE}}
    """, (("Geçmiş Karne Arşivi", "/performans/gecmis-karne-arsivi", "Geçmiş performans kayıtları"),), section="Performans"),

    _topic("interim_notes", "Dönem içi notlar / ara geri bildirim", ("dönem içi not", "donem ici not", "ara geri bildirim", "olumlu olay", "olumsuz olay", "başarı notu", "basari notu", "gözlem", "gozlem"), """
Dönem içi not kullanımı:
1. Performans Yönetimi > Dönem İçi Notlar ekranına girin.
2. Personel, dönem, not türü ve açıklama alanlarını doldurun.
3. Not türleri olumlu olay, olumsuz olay, başarı, gelişim ihtiyacı veya genel gözlem olabilir.
4. Bu notlar otomatik puan üretmez.
5. Puanlama döneminde amire hatırlatma ve bağlam bilgisi sağlar.
6. Yetkisiz kullanıcı başka personelin dönem içi not detayını görmemelidir.

Yetki notu: {{ROLE_NOTE}}
    """, (("Dönem İçi Notlar", "/performance/interim-notes", "Ara gözlem ve geri bildirim notları"),), section="Performans"),

    _topic("development_guidance", "Gelişim önerisi ve rehber alanı", ("gelişim önerisi", "gelisim onerisi", "gelişim rehberi", "gelisim rehberi", "eğitim önerisi", "egitim onerisi", "güçlü yön", "guclu yon"), """
Gelişim önerisi kullanımı:
1. Performans Yönetimi içinde Gelişim Rehberi / Gelişim Önerisi ekranını açın.
2. Personelin gelişim alanını, güçlü yönünü ve önerilen takip notunu yazın.
3. Düşük performans veya gelişim ihtiyacı durumlarında somut, ölçülebilir ve saygılı dil kullanın.
4. Gelişim önerisi performans puanı üretmez; karne sonrası rehberlik sağlar.
5. Personel tarafında hangi notların görüneceği yayın ve yetki ayarına bağlıdır.

Yetki notu: {{ROLE_NOTE}}
    """, (("Gelişim Rehberi", "/performance/meeting-development/faz10", "Gelişim önerileri"),), section="Performans"),

    _topic("performance_reports", "Performans raporları ve dashboard", ("performans raporu", "rapor", "dashboard", "canlı performans haritası", "canli performans haritasi", "riskli personel", "aksatan amir", "geciken amir", "kategori raporu"), """
Performans raporları kullanımı:
1. Performans Yönetimi > Raporlar veya Dashboard ekranına girin.
2. Dönem, birim, kategori, amir veya personel filtrelerini seçin.
3. Canlı performans haritası, en geciken amirler, riskli personel analizi, düşük performans yoğunluğu ve dönem tamamlanma oranlarını inceleyin.
4. Personel veya standart kullanıcı kişi detaylarını görmemelidir; yalnızca kendi verisi ve kişi detayı içermeyen ortalamalar görünür.
5. Yönetici raporları yetkili organizasyon kapsamına göre sınırlandırılmalıdır.

Yetki notu: {{ROLE_NOTE}}
    """, (("Performans Raporları", "/performance/reports", "Performans analizleri"), ("Dashboard", "/performance/dashboard", "Yönetici görünürlüğü")), section="Performans"),

    _topic("reminders_delayed_supervisor", "Otomatik hatırlatma ve aksatan amir", ("hatırlatma", "hatirlatma", "aksatan amir", "geciken amir", "son tarih", "deadline", "mail log", "e-posta hatırlatma"), """
Otomatik hatırlatma ve aksatan amir takibi:
1. Performans Yönetimi > Hatırlatma / Aksatan Amirler ekranını açın.
2. Bekleyen değerlendirme görevlerini ve son tarihlerini kontrol edin.
3. Son tarih yaklaşan amirlere sistem içi bildirim veya e-posta hatırlatması gönderilebilir.
4. Süresi geçen görevler aksatan amir raporunda görünür.
5. Mail log ve bildirim kayıtları denetim için saklanmalıdır.
6. Asistan hatırlatma göndermez; yalnızca ekran ve işlem yolunu tarif eder.

Yetki notu: {{ROLE_NOTE}}
    """, (("Hatırlatma ve Aksatan Amirler", "/performance/meeting-development/faz9", "Bekleyen görev ve gecikmeler"),), section="Performans"),

    _topic("messages", "Mesajlaşma", ("mesaj", "mesajlaşma", "mesajlasma", "sohbet", "konuşma", "konusma", "dosya gönder", "dosya gonder", "okunmamış mesaj"), """
Mesajlaşma kullanımı:
1. İletişim / Mesajlaşma ekranını açın.
2. Kişi veya grup konuşmasını seçin ya da yeni konuşma başlatın.
3. Mesajınızı yazın; gerekiyorsa dosya veya belge ekleyin.
4. Mesaj geçmişi, okunma durumu ve bildirimleri kontrol edin.
5. Kurum içi mesajlar kayıtlı ve yetki kontrollü olmalıdır.
6. Asistan mesaj içeriği göstermez ve sizin adınıza mesaj göndermez.

Yetki notu: {{ROLE_NOTE}}
    """, (("Mesajlaşma", "/messages", "Kurum içi mesajlaşma"),), section="İletişim/Anket/Destek"),

    _topic("announcements", "Duyurular", ("duyuru", "duyurular", "kurumsal duyuru", "bildiri", "ilan", "duyuru yayınla", "duyuru yayinla"), """
Duyuru kullanımı:
1. İletişim / Duyurular ekranına girin.
2. Size gelen duyuruları okuyun ve varsa onay/okundu bilgisini tamamlayın.
3. Yetkili kullanıcıysanız hedef kitle, başlık, içerik ve yayın tarihini belirleyerek duyuru oluşturabilirsiniz.
4. Kritik duyurularda kimlere ulaştığı ve okunma durumu takip edilmelidir.
5. Asistan duyuru yayınlamaz; yalnızca hangi ekranda yapılacağını gösterir.

Yetki notu: {{ROLE_NOTE}}
    """, (("Duyurular", "/announcements", "Kurumsal duyurular"),), section="İletişim/Anket/Destek"),

    _topic("surveys", "Anketler", ("anket", "anket cevapla", "anket oluştur", "anket olustur", "soru", "cevap", "katılım", "katilim"), """
Anket kullanımı:
1. İletişim / Anketler ekranına girin.
2. Size atanmış anketleri açın ve soruları cevaplayın.
3. Yetkili kullanıcıysanız anket başlığı, soru türleri, hedef kitle ve tarih aralığını belirleyerek anket oluşturabilirsiniz.
4. Anket sonuçları yetki sınırına göre raporlanır.
5. Açık uçlu cevaplar ve kişisel veriler hassasiyetle korunmalıdır.
6. Asistan anket cevabı göstermez ve kullanıcı adına cevap vermez.

Yetki notu: {{ROLE_NOTE}}
    """, (("Anketler", "/surveys", "Anket yönetimi"),), section="İletişim/Anket/Destek"),

    _topic("feedback", "Geri bildirim ve nabız", ("geri bildirim", "nabız", "nabiz", "kampanya", "aksiyon planı", "aksiyon plani", "memnuniyet"), """
Geri bildirim kullanımı:
1. Geri Bildirim / Nabız ekranına girin.
2. Size açık geri bildirim kampanyasını veya nabız ölçümünü seçin.
3. Görüşünüzü sade ve kurumsal dille yazın.
4. Yetkili kullanıcılar sonuçları kişi detayı ve gizlilik ayarlarına göre görebilir.
5. Geri bildirimlerden aksiyon planı oluşturulabilir.
6. Asistan geri bildirim içeriği göstermez; yalnızca kullanım yolunu anlatır.

Yetki notu: {{ROLE_NOTE}}
    """, (("Geri Bildirim", "/feedback", "Geri bildirim ve nabız"),), section="İletişim/Anket/Destek"),

    _topic("support_ticket", "Destek talebi oluşturma", ("destek", "destek talebi", "yardım talebi", "yardim talebi", "ticket", "sorun bildir", "hata bildir", "talep aç", "talep ac"), """
Destek talebi oluşturmak için:
1. Destek / Yardım Merkezi ekranına girin.
2. Yeni destek talebi oluştur butonunu seçin.
3. Kategori, başlık, açıklama ve varsa ekran görüntüsü/dosya ekini girin.
4. Talebi kaydedin ve durumunu takip edin.
5. Destek ekibi yanıt verdiğinde bildirim alırsınız.
6. Talep geçmişi kurumsal hafıza ve raporlama için saklanır.

Yetki notu: {{ROLE_NOTE}}
    """, (("Destek Talepleri", "/support/tickets", "Yardım ve destek talepleri"),), ("Destek talebime nereden bakarım?", "Bildirimler nerede?", "Mesaj nasıl gönderilir?"), "İletişim/Anket/Destek"),

    _topic("settings_overview", "Sistem ayarları genel kullanım", ("ayarlar", "sistem ayarları", "sistem ayarlari", "modül ayarları", "modul ayarlari", "konfigürasyon", "konfigurasyon"), """
Sistem Ayarları kullanımı:
1. Sistem Ayarları bölümüne yalnızca yetkili kullanıcılar erişmelidir.
2. Genel sistem ayarları, modül ayarları, güvenlik, e-posta, bildirim, zamanlanmış işler ve audit log buradan yönetilir.
3. Ayar değişiklikleri canlı sistemi etkileyebileceği için değişiklikten önce mevcut değer kontrol edilmelidir.
4. Değişiklik sonrası ilgili modül ve gate kontrolü çalıştırılmalıdır.
5. Kritik değişiklikler audit log’a düşmelidir.

Yetki notu: {{ROLE_NOTE}}
    """, (("Sistem Ayarları", "/settings", "Merkezi ayar ekranı"),), section="Ayarlar"),

    _topic("role_matrix_visibility", "Rol matrisi ve menü görünürlüğü", ("rol matrisi", "menü görünürlüğü", "menu gorunurlugu", "menü aç", "menu ac", "menü kapat", "menu kapat", "özellik görünmüyor", "ozellik gorunmuyor", "yetki", "erişim"), """
Rol matrisi ve menü görünürlüğü için:
1. Sistem Ayarları > Rol Matrisi ekranına girin.
2. İlgili rolü seçin: Personel, Amir, Koordinatör, Grup Başkanı, Başkan, Admin veya özel rol.
3. Açılacak/kapatılacak modül ve alt sekmeyi bulun.
4. Görünürlük ve erişim yetkisini birlikte düzenleyin.
5. Kaydettikten sonra kullanıcı oturumunu yenileyin veya canlı yetki katmanının güncellendiğini kontrol edin.
6. Menüde görünmemesi gereken ekran hiç görünmemelidir; sadece tıklayınca erişim engeli vermek yeterli değildir.
7. URL elle yazılırsa backend route yetki kontrolü yine veri sızdırmamalıdır.

Yetki notu: {{ROLE_NOTE}}
    """, (("Rol Matrisi", "/admin/role-matrix", "Rol ve menü görünürlüğü"),), ("Menü görünmüyorsa ne yapmalıyım?", "Yetkisiz erişim ekranı nedir?", "Asistan yetkiye göre cevap verir mi?"), "Ayarlar"),

    _topic("menu_not_visible", "Menü görünmüyor / özellik açılıp kapanmıyor", ("menü görünmüyor", "menu gorunmuyor", "açtım görünmüyor", "actim gorunmuyor", "kapattım hâlâ görünüyor", "hala görünüyor", "rol matrisi çalışmıyor", "calismiyor", "özellik eklenmiyor"), """
Menü görünürlüğü sorunu için kontrol sırası:
1. Rol Matrisi ekranında ilgili rol ve alt sekmenin açık/kapalı durumunu kontrol edin.
2. Kişi bazlı özel yetki varsa rol ayarının üstüne yazıp yazmadığını kontrol edin.
3. Birim bazlı menü profili varsa kullanıcının birimiyle çakışıp çakışmadığını kontrol edin.
4. Kullanıcının oturumunu yenileyin veya çıkış/giriş yaptırın.
5. Backend route yetkisi ile sol menü görünürlüğünün aynı kaynaktan beslendiğini kontrol edin.
6. Gate scripti menü görünürlüğü, effective_menu ve canlı yetki katmanı markerlarını doğrulamalıdır.

Yetki notu: {{ROLE_NOTE}}
    """, (("Rol Matrisi", "/admin/role-matrix", "Rol matrisi kontrolü"), ("Sistem Ayarları", "/settings", "Merkezi ayarlar")), section="Ayarlar"),

    _topic("security_settings", "Güvenlik, CAPTCHA ve audit", ("güvenlik", "guvenlik", "captcha", "3 hatalı giriş", "3 hatali giris", "audit", "log", "oturum güvenliği", "parola politikası"), """
Güvenlik ayarları:
1. Sistem Ayarları > Güvenlik bölümüne girin.
2. Oturum süresi, parola politikası, güvenli çıkış, dosya yükleme limiti ve CAPTCHA ayarlarını kontrol edin.
3. 3 hatalı girişten sonra CAPTCHA aktif olmalıdır.
4. Kritik ayar değişiklikleri audit log’a yazılmalıdır.
5. Canlı ortamda güvenlik ayarı değişikliklerinden sonra giriş, çıkış ve yetki senaryoları test edilmelidir.

Yetki notu: {{ROLE_NOTE}}
    """, (("Güvenlik Ayarları", "/settings/security", "Oturum ve güvenlik kontrolleri"), ("Audit Log", "/admin/audit-logs", "Denetim kayıtları")), section="Ayarlar"),

    _topic("access_denied", "Yetkisiz erişim ve güvenli yönlendirme", ("erişim engeli", "erisim engeli", "yetkim yok", "yetkisiz", "bu sayfaya erişim", "beyaz sayfa", "403", "izin yok"), """
Yetkisiz erişim durumunda:
1. Kullanıcı görmemesi gereken menüyü hiç görmemelidir.
2. URL elle yazılırsa sistem veri göstermeden kurumsal erişim engeli ekranı vermelidir.
3. Ekranda “Bu sayfaya erişim yetkiniz bulunmamaktadır.” gibi sade Türkçe ifade kullanılmalıdır.
4. Beyaz sayfa, teknik hata, tanılama veya traceback kullanıcıya gösterilmemelidir.
5. Yetki gerekiyorsa Admin/Sistem Yöneticisi rol matrisi ve kişi bazlı yetkiyi kontrol etmelidir.

Yetki notu: {{ROLE_NOTE}}
    """, (("Rol Matrisi", "/admin/role-matrix", "Yetki kontrolü"),), section="Ayarlar"),

    _topic("ai_decision_support", "AI Karar Destek Merkezi", ("ai karar destek", "karar destek", "yapay zeka karar", "özet", "ozet", "risk analizi", "ai öneri", "ai oneri"), """
AI Karar Destek Merkezi kullanımı:
1. AI Karar Destek Merkezi, yöneticilere özet, ön değerlendirme, risk farkındalığı ve rapor yorumu sağlar.
2. Modül nihai idari karar vermez.
3. Hassas veri maskeleme, loglama ve yetki kontrolüyle çalışmalıdır.
4. Performans, personel, anket, destek ve geri bildirim verileri yalnızca yetkili kapsamda analiz edilir.
5. AI çıktısı öneri/özet niteliğindedir; karar insana aittir.
6. BYS360 Asistanı ile farkı şudur: Asistan kullanım öğretir, AI Karar Destek veri analizi ve yönetici içgörüsü üretir.

Yetki notu: {{ROLE_NOTE}}
    """, (("AI Karar Destek", "/ai/decision-support", "Kontrollü karar destek merkezi"),), section="AI/KPI"),

    _topic("kpi_targets", "KPI ve Hedef Yönetimi", ("kpi", "hedef", "hedef kartı", "hedef karti", "hedef dönemi", "hedef donemi", "başarı oranı", "basari orani", "stratejik dashboard", "yetkinlik kütüphanesi"), """
KPI ve Hedef Yönetimi kullanımı:
1. KPI/Hedef Yönetimi ekranına girin.
2. Hedef dönemi seçin veya yetkiniz varsa yeni dönem oluşturun.
3. Hedef kartında hedef kodu, hedef adı, hedef tipi, kategori, sahip, ağırlık, hedef değer ve tarih aralığını kontrol edin.
4. Gerçekleşen değer girildiğinde sistem başarı oranı ve risk durumunu üretir.
5. Dashboard ekranında Başkan ve yöneticiler riskli KPI’ları, hedef gerçekleşme oranlarını ve kategori başarı haritasını takip edebilir.
6. KPI verisi performans, AI analiz ve stratejik görünürlük katmanını besler.

Yetki notu: {{ROLE_NOTE}}
    """, (("KPI / Hedef Yönetimi", "/kpi/targets", "Hedef kartları ve KPI ölçümleri"), ("Stratejik Dashboard", "/kpi/dashboard", "KPI dashboardu")), ("KPI hedefleri nereden takip edilir?", "Hedef kartı nasıl açılır?", "AI KPI analizi ne yapar?"), "AI/KPI"),

    _topic("assistant_opening_examples", "Asistan açılış tanıtımı ve örnek sorular", ("asistan açılınca", "asistan acilinca", "tanıtım", "tanitim", "örnek sorular", "ornek sorular", "açılış metni", "acilis metni", "karşılama", "karsilama"), """
BYS360 Asistanı açıldığında görünmesi gereken tanıtım:
1. Başlık: “Merhaba, ben BYS360 Asistanı” olmalıdır.
2. Açıklama: BYS360 içinde işlemlerin nereden ve hangi sırayla yapılacağını adım adım anlattığını söylemelidir.
3. Güvenlik notu: idari karar vermediği, puan belirlemediği ve yetki dışı hassas veri göstermediği belirtilmelidir.
4. Örnek sorular canlı kapsamı yansıtmalıdır: personel ekleme, dönem açma, puanlama, Başkan onayı, 70 altı süreç, rol matrisi, izin/vekâlet, KPI/Hedef.
5. Eski “AI Ajanı”, “Yapay Zekâ Ajanı” veya genel chatbot dili görünmemelidir.

Bu V2 overlay, açılış tanıtımını ve örnek soruları bu yeni yapıya göre günceller.

Yetki notu: {{ROLE_NOTE}}
    """, (), EXAMPLE_QUESTIONS, "Genel Kullanım"),

    _topic("mobile_usage", "Mobil kullanım", ("mobil", "telefon", "tablet", "responsive", "ekran sığmıyor", "ekran sigmiyor", "buton görünmüyor"), """
Mobil kullanım için:
1. Menü dar ekranda kapalı/akordeon olabilir; sol menüyü açma ikonunu kullanın.
2. Büyük tablolar yatay kaydırma veya kart görünümüyle sunulmalıdır.
3. Puanlama, karne, destek ve anket ekranlarında butonların görünürlüğünü kontrol edin.
4. Beyaz sayfa veya kayma varsa ilgili ekranın mobil CSS kontrolü gerekir.
5. Kritik onay ve puanlama işlemleri mobilde yapılacaksa kaydetmeden önce tüm alanların göründüğünden emin olun.

Yetki notu: {{ROLE_NOTE}}
    """, (), section="Genel Kullanım"),

    _topic("troubleshooting", "Canlı sorun giderme", ("açılmıyor", "acilmiyor", "beyaz ekran", "hata", "çalışmıyor", "calismiyor", "canlı", "canli", "gate", "overlay", "restart", "yeniden başlat"), """
Canlı sorun giderme kontrol sırası:
1. Son yüklenen overlay’in doğru klasöre açıldığını kontrol edin.
2. Repair scriptini çalıştırın.
3. Gate scriptini çalıştırın ve OK çıktısını bekleyin.
4. Python compileall ile değişen dosyaların sözdizimi hatası vermediğini kontrol edin.
5. Scheduled Task üzerinden canlı servisi yeniden başlatın.
6. Tarayıcı cache temizliği veya gizli sekme ile tekrar deneyin.
7. Hata devam ederse logs klasöründeki Waitress/app logları ve reports klasöründeki gate raporu incelenmelidir.

Yetki notu: {{ROLE_NOTE}}
    """, (), section="Genel Kullanım"),

    _topic("live_scope", "Canlı kapsamda kalan modüller", ("canlı kapsam", "canli kapsam", "hangi modüller", "hangi moduller", "kapsam dışı", "kapsam disi", "silinen modüller", "silinen moduller"), """
Canlı kapsam mantığı:
1. Kimlik, kullanıcı, yetki ve ayarlar omurgası canlıda kalır.
2. Personel, izin, devamsızlık ve vekâlet hattı canlı omurgadadır.
3. Performans Yönetimi ve güncel performans süreçleri canlı omurgadadır.
4. İletişim, anket, geri bildirim, destek ve bildirim yapıları canlı kapsamda değerlendirilir.
5. AI Karar Destek Merkezi ve BYS360 Asistanı ayrı ama ilişkili katmanlardır.
6. Eğitim/İSG, Strateji, İç Portal ve Belge-Medya Deposu gibi kapsam dışı bırakılan eski modüller bu rehberde canlı kullanım başlığı olarak anlatılmaz.

Yetki notu: {{ROLE_NOTE}}
    """, (), section="Genel Kullanım"),
)


def get_bys360_assistant_full_live_guide_index() -> list[dict[str, str]]:
    return [
        {"key": topic.key, "title": topic.title, "section": topic.section, "keywords": ", ".join(topic.keywords[:8])}
        for topic in TOPICS
    ]


def build_bys360_assistant_full_live_usage_reply(user: Any, question: str) -> dict[str, Any] | None:
    q = _norm(question)
    if not q:
        intro = get_bys360_assistant_intro_payload(user)
        topic = TOPICS[0]
        data = _reply(topic, user, question)
        data["intent"] = "assistant_opening"
        data["topic_title"] = "BYS360 Asistanı açılış rehberi"
        data["answer"] = f"{intro['title']}\n\n{intro['subtitle']}\n\n{intro['security_text']}\n\nÖrnek sorular:\n" + "\n".join(f"- {x}" for x in intro["example_questions"])
        data["quick_replies"] = intro["example_questions"]
        return data
    best: tuple[int, GuideTopic] | None = None
    for topic in TOPICS:
        score = 0
        for kw in topic.keywords:
            nkw = _norm(kw)
            if not nkw:
                continue
            if nkw == q:
                score += 25
            elif nkw in q:
                score += 10 + min(len(nkw), 20)
        # Small boost for title words
        for word in _norm(topic.title).split():
            if len(word) > 3 and word in q:
                score += 1
        if score and (best is None or score > best[0]):
            best = (score, topic)
    if best is not None and best[0] >= 10:
        return _reply(best[1], user, question)
    return _reply(GuideTopic(
        key="general_live_usage_help",
        title="BYS360 genel kullanım yardımı",
        keywords=(),
        section="Genel Kullanım",
        answer="""
BYS360 Asistanı size canlı sistemde işlem adımlarını anlatmak için hazır.

Sorunuzu şu biçimde yazarsanız daha net yönlendiririm:
1. “Personel nasıl eklenir?”
2. “Performans dönemi nasıl açılır?”
3. “Puanlama ekranı nasıl kullanılır?”
4. “Başkan onayları nasıl kullanılır?”
5. “Rol matrisinden menü nasıl açılır?”
6. “Destek talebi nasıl oluşturulur?”
7. “KPI hedefleri nereden takip edilir?”

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(
            ("BYS360 Asistanı Paneli", "/ai-agent/panel", "Asistan paneli"),
            ("Asistan Bilgi Bankası", "/ai-agent/knowledge", "Kullanım rehberi"),
        ),
    ), user, question)

# Geriye dönük uyumluluk için kısa adlar
build_bys360_assistant_knowledge_reply = build_bys360_assistant_full_live_usage_reply
get_bys360_assistant_knowledge_index = get_bys360_assistant_full_live_guide_index
