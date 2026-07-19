from __future__ import annotations

# BYS360_ASSISTANT_STEPWISE_TUTOR_V4
from typing import Any

VERSION = "BYS360 Asistanı Öğretici Rehber Motoru V4"
MODE = "Doğal dil anlama, adım adım kullanım öğretimi ve güvenli yönlendirme"
ASSISTANT_NAME = "BYS360 Asistanı"
NOTICE = "BYS360 Asistanı idari karar vermez, performans puanı belirlemez, onay/ret işlemi yapmaz ve yetki dışı hassas veri göstermez."
SECURITY_NOTICE = "Cevaplar işlem rehberi ve güvenli yönlendirme amaçlıdır. Gerçek işlem ilgili BYS360 ekranında yetkili kullanıcı tarafından yapılır."

TR_TABLE = str.maketrans({
    "ı": "i", "İ": "i", "I": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
    "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
    "â": "a", "î": "i", "û": "u"
})

ACTION_SAFETY = "rehber_yonlendirme"


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower().translate(TR_TABLE)
    for ch in "\n\r\t.,;:!?()[]{}<>/\\|+*=\"'`~_-":
        text = text.replace(ch, " ")
    return " ".join(text.split())


def _tokens(value: str) -> set[str]:
    return {p for p in _norm(value).split() if len(p) >= 2}


def _role_from_user(user: Any) -> str:
    values: list[str] = []
    for attr in ("role", "role_name", "role_key", "user_role", "authority_role", "position", "title", "unvan", "job_title", "display_role"):
        try:
            val = getattr(user, attr, None)
            if val:
                values.append(str(val))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/ai_agent/assistant_stepwise_tutor_v4.py)")
    try:
        if bool(getattr(user, "is_admin", False)) or bool(getattr(user, "is_superuser", False)):
            return "admin"
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/ai_agent/assistant_stepwise_tutor_v4.py)")
    joined = _norm(" ".join(values))
    if any(x in joined for x in ("sistem", "admin", "yonetici", "superuser")):
        return "admin"
    if any(x in joined for x in ("personel ve destek", "insan kaynak", "ik", "performans yetkilisi")):
        return "hr_performance"
    if "baskan yardimcisi" in joined or "ust yonetim" in joined:
        return "upper_management"
    if "baskan" in joined:
        return "president"
    if "grup baskani" in joined:
        return "group_head"
    if "koordinator" in joined or "koordinat" in joined:
        return "coordinator"
    if "amir" in joined or "degerlendirici" in joined:
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


def _scope_note(role: str) -> str:
    if role in ("admin", "president", "upper_management"):
        return "Üst yönetim veya admin görünümü bile sistemde tanımlı rol, kişi, birim ve menü yetkileriyle sınırlı çalışır."
    if role == "group_head":
        return "Grup Başkanı yalnızca kendi grup/üst birim kapsamındaki kayıt ve raporlara yönlendirilmelidir."
    if role == "coordinator":
        return "Koordinatör yalnızca kendi çalışma grubu veya koordinasyon kapsamındaki işlemlere yönlendirilmelidir."
    if role == "supervisor":
        return "Amir yalnızca kendisine atanmış değerlendirme görevleri ve yetkili olduğu personel kapsamına yönlendirilmelidir."
    if role == "hr_performance":
        return "Personel/Performans yetkilisinin görünürlüğü rol matrisi, kişi bazlı yetki ve menü ayarlarıyla belirlenir."
    return "Standart kullanıcı yalnızca kendi hesabı, kendi talepleri, kendi bildirimleri ve yayınlanmış kendi sonuçlarıyla sınırlıdır."


def _a(label: str, url: str, desc: str = "") -> dict[str, str]:
    return {"label": label, "title": label, "route": url, "url": url, "description": desc, "safety_level": ACTION_SAFETY}


def _guide(key: str, title: str, aliases: list[str], steps: list[str], actions: list[tuple[str, str, str]],
           intro: str = "", safety: str = "", quick: list[str] | None = None, roles: list[str] | None = None,
           priority: int = 50) -> dict[str, Any]:
    return {
        "key": key,
        "title": title,
        "aliases": aliases,
        "steps": steps,
        "actions": actions,
        "intro": intro,
        "safety": safety,
        "quick": quick or [],
        "roles": roles or [],
        "priority": priority,
    }


STEPWISE_GUIDES: list[dict[str, Any]] = [
    _guide(
        "new_user_start",
        "BYS360’a ilk kez giren kullanıcı nereden başlamalı?",
        ["hic bilmiyorum", "nereden baslayayim", "ilk kez", "yeni kullanici", "ne yapacagim", "bana ogret", "adim adim anlat", "tum ozellikleri nasil kullaniliyor", "sistemi nasil kullanirim"],
        [
            "Önce kullanıcı adınızla giriş yapın ve ana sayfada size açık menüleri kontrol edin.",
            "Sağ alt köşedeki BYS360 Asistanı’nı açın ve yapmak istediğiniz işlemi normal cümleyle yazın. Örnek: ‘izin talebi oluşturacağım’, ‘karne nerede’, ‘menü görünmüyor’. ",
            "Asistan size ilgili modülü, işlem sırasını ve güvenli ekran bağlantısını gösterir.",
            "Kişisel veya hassas veri gerekiyorsa asistan içeriği dökmez; sizi yetkili ekrana yönlendirir.",
            "Yetkiniz yoksa menüyü görememeniz normaldir. Bu durumda rol matrisi veya yetkili birim kontrolü gerekir.",
        ],
        [("Ana Sayfa", "/home", "Giriş sonrası genel başlangıç"), ("BYS360 Asistanı", "/ai-agent/panel", "Rehberlik paneli"), ("Yardım/Destek", "/support", "Destek talepleri")],
        intro="BYS360’ı hiç bilmeyen biri için en doğru başlangıç, önce menüleri tanımak ve yapmak istediği işi doğal cümleyle asistana sormaktır.",
        safety="Asistan işlem yapmaz; işlem adımını öğretir ve doğru ekrana götürür.",
        quick=["Personel nasıl eklenir?", "Performans görevi nasıl tamamlanır?", "Destek talebi nasıl açılır?", "Menü görünmüyor ne yapmalıyım?"],
        priority=95,
    ),
    _guide(
        "personnel_add",
        "Personel nasıl eklenir?",
        ["personel ekle", "personel kaydet", "yeni personel", "personel olustur", "sicil no", "personel kaydi", "calisan ekle"],
        [
            "Personel Yönetimi menüsüne girin.",
            "Personel listesi veya personel ekleme ekranını açın.",
            "Sicil No, ad soyad, unvan/görev, birim, üst birim ve yönetici/amir alanlarını doldurun.",
            "Rol ve menü görünürlüğü gerekiyorsa ilgili rol veya kişi bazlı yetkiyi kontrol edin.",
            "Profil fotoğrafı veya ek bilgi alanı varsa yükleyin; zorunlu alanları boş bırakmayın.",
            "Kaydetmeden önce birim, üst birim ve amir ilişkisinin doğru olduğundan emin olun.",
            "Kaydettikten sonra personelin performans, izin, vekâlet ve iletişim süreçlerine doğru yansıyıp yansımadığını kontrol edin.",
        ],
        [("Personel Yönetimi", "/personnel", "Personel listesi"), ("Yeni Personel", "/personnel/create", "Personel ekleme"), ("Rol Matrisi", "/admin/role-matrix", "Yetki kontrolü")],
        intro="Personel kaydı BYS360’ın ana veri omurgasıdır. Hatalı birim veya amir bilgisi performans zincirini de etkileyebilir.",
        safety="TC gibi hassas bilgiler yerine sistemde kurumsal tercih olarak Sicil No mantığı esas alınmalıdır.",
        quick=["Toplu personel yükleme nasıl yapılır?", "Amir bilgisi neden önemli?", "Rol matrisi nasıl çalışır?"],
        roles=["admin", "hr_performance"],
        priority=80,
    ),
    _guide(
        "personnel_import",
        "Toplu personel yükleme/import nasıl yapılır?",
        ["toplu personel", "excel yukle", "personel import", "liste yukle", "personel listesi", "excelden aktar", "amir listesi"],
        [
            "Önce örnek import formatını indirin veya mevcut personel listesini BYS360 formatına uyarlayın.",
            "Sicil No, ad soyad, unvan, birim, üst birim, rol, yönetici ve varsa kategori alanlarını kontrol edin.",
            "Amir sicilleri boş veya hatalıysa yüklemeden önce düzeltin.",
            "Import ekranından dosyayı yükleyin ve ön izleme/validasyon sonucunu kontrol edin.",
            "Hata veren satırları düzeltmeden kesin aktarım yapmayın.",
            "Aktarım sonrası personel sayısı, birim dağılımı ve amir zinciri üretimini kontrol edin.",
        ],
        [("Personel Import", "/personnel/import", "Toplu yükleme"), ("Personel Yönetimi", "/personnel", "Kontrol listesi"), ("Performans Görev Üretimi", "/performance/assignments", "Amir zinciri kontrolü")],
        intro="Toplu yüklemede amaç sadece kayıt oluşturmak değil, performans zincirinin doğru üretileceği temiz personel omurgasını kurmaktır.",
        safety="Yükleme öncesi birim, üst birim ve amir sicilleri mutlaka kontrol edilmelidir.",
        quick=["Personel kategorisi nedir?", "Amir zinciri nasıl oluşur?", "Yükleme hatası alırsam ne yapmalıyım?"],
        roles=["admin", "hr_performance"],
        priority=76,
    ),
    _guide(
        "org_units",
        "Birim, üst birim ve yönetici ilişkisi nasıl yönetilir?",
        ["birim ekle", "ust birim", "organizasyon", "yonetici ata", "birim yoneticisi", "calisma grubu", "koordinator", "grup baskanligi"],
        [
            "Sistem Ayarları veya Personel Yönetimi içindeki birim/organizasyon ekranını açın.",
            "Yeni birim ekliyorsanız ad, üst birim ve tür bilgisini belirleyin.",
            "Çalışma grubu, koordinatörlük ve grup başkanlığı ilişkilerini doğru hiyerarşiyle bağlayın.",
            "Birim yöneticisi veya koordinatör bilgisini ilgili alana girin.",
            "Değişiklik sonrası personel organizasyon geçmişinin güncellenip güncellenmediğini kontrol edin.",
            "Performans görev üretiminden önce birim ve yönetici ilişkilerinin temiz olduğundan emin olun.",
        ],
        [("Organizasyon/Birimler", "/admin/organization-units", "Birim yönetimi"), ("Personel Yönetimi", "/personnel", "Personel-birim ilişkisi"), ("Rol Matrisi", "/admin/role-matrix", "Görünürlük")],
        intro="BYS360’da organizasyon yapısı yalnızca liste değildir; yetki, performans, rapor ve bildirim kapsamını belirler.",
        quick=["Koordinatörün amiri kimdir?", "Çalışma grubu personelinde amir zinciri nedir?", "Menü görünürlüğü nasıl etkilenir?"],
        roles=["admin", "hr_performance"],
        priority=72,
    ),
    _guide(
        "leave_request",
        "İzin talebi nasıl oluşturulur?",
        ["izin talebi", "izin iste", "izin alacagim", "izin kaydi", "leave", "personel izni", "yillik izin"],
        [
            "Personel veya izin menüsünden İzin Talepleri ekranını açın.",
            "Yeni izin talebi seçeneğine girin.",
            "İzin türünü, başlangıç ve bitiş tarihini, açıklama alanını ve varsa ek belgeyi doldurun.",
            "Talebi kaydedin veya onaya gönderin.",
            "Talebin durumunu aynı ekrandan takip edin.",
            "İzin döneminde vekâlet gerekiyorsa vekâlet kaydının ayrıca oluşturulup oluşturulmadığını kontrol edin.",
        ],
        [("İzin Talepleri", "/personnel/leave-requests", "İzin süreci"), ("Vekâlet", "/personnel/delegations", "Vekâlet kaydı"), ("Bildirimler", "/notifications", "Süreç bildirimi")],
        intro="İzin süreci personel yönetiminin parçasıdır ve performans/vekalet akışını etkileyebilir.",
        safety="Asistan izin onaylamaz; yalnızca talebin nasıl oluşturulacağını anlatır.",
        quick=["Vekâlet nasıl verilir?", "İzin talebimin durumunu nereden görürüm?"],
        priority=70,
    ),
    _guide(
        "delegation",
        "Vekâlet nasıl tanımlanır?",
        ["vekalet", "vekil", "yerime kim bakacak", "gorev devri", "izinliyken", "amir izinli", "vekalet atama"],
        [
            "Personel Yönetimi altında Vekâlet ekranını açın.",
            "Vekâlet veren kişi, vekil kişi, tarih aralığı ve kapsam bilgisini seçin.",
            "Vekâletin performans, onay, destek veya bildirim süreçlerini etkileyip etkilemeyeceğini kontrol edin.",
            "Kaydedin ve ilgili kişilere bildirim gidip gitmediğini kontrol edin.",
            "Süre bitince vekâletin otomatik/pasif duruma dönüp dönmediğini izleyin.",
        ],
        [("Vekâlet Yönetimi", "/personnel/delegations", "Vekâlet kayıtları"), ("İzin Talepleri", "/personnel/leave-requests", "İzin bağlantısı"), ("Performans Görevleri", "/performance/tasks", "Görev etkisi")],
        intro="Vekâlet, izin veya görev devri sırasında süreçlerin aksamamasını sağlar.",
        safety="Asistan vekil ataması yapmaz; yetkili kullanıcıyı ilgili ekrana yönlendirir.",
        quick=["İzin talebi nasıl açılır?", "Performans görevi vekile düşer mi?"],
        roles=["admin", "hr_performance", "group_head", "coordinator"],
        priority=70,
    ),
    _guide(
        "performance_period",
        "Performans dönemi nasıl açılır?",
        ["performans donemi ac", "dönem aç", "donem ac", "degerlendirme donemi", "performans baslat", "yeni dönem", "ozel donem", "kategori donemi"],
        [
            "Performans Yönetimi menüsünden Dönemler ekranını açın.",
            "Yeni dönem oluştur seçeneğine girin.",
            "Dönem adını, dönem türünü, başlangıç ve bitiş tarihlerini belirleyin.",
            "Kapsam tipini seçin: tüm kurum, birim, üst birim, kategori/grup veya seçili personel.",
            "Kriter ve ağırlık ayarlarının hazır olduğundan emin olun.",
            "Personel, kategori, amir, izin ve vekâlet verilerini kontrol edin.",
            "Dönemi kaydedin ve görev üretimi adımına geçin.",
        ],
        [("Performans Dönemleri", "/performance/periods", "Dönem yönetimi"), ("Yeni Dönem", "/performance/periods/create", "Dönem oluşturma"), ("Kriterler", "/performance/criteria", "Kriter ayarı")],
        intro="Performans dönemi açmak, değerlendirme sürecinin başlangıç adımıdır. Kapsam yanlış seçilirse görevler yanlış personele üretilebilir.",
        safety="Dönem açma yetkisi rol matrisi ve performans yetkileriyle sınırlı olmalıdır.",
        quick=["Görev üretimi nasıl yapılır?", "Kriterler nasıl tanımlanır?", "Kategoriye özel dönem nedir?"],
        roles=["admin", "hr_performance"],
        priority=84,
    ),
    _guide(
        "performance_criteria",
        "Değerlendirme kriterleri ve ağırlıklar nasıl tanımlanır?",
        ["kriter ekle", "degerlendirme kriterleri", "yetkinlik", "agirlik", "puan kriteri", "1 5", "100 luk", "puanlama ayari"],
        [
            "Performans Yönetimi içinde Değerlendirme Kriterleri ekranını açın.",
            "Kriter adı, açıklaması, aktiflik durumu ve varsa kategori bilgisini girin.",
            "Puanlama ölçeğinin 1-5 ve 100’lük dönüşüm mantığıyla uyumlu olduğundan emin olun.",
            "Ağırlıklar toplamının %100 olacak şekilde tanımlandığını kontrol edin.",
            "1 ve 5 puan açıklama zorunluluğu ayarı gerekiyorsa Sistem Ayarları tarafındaki ilgili parametreyi kontrol edin.",
            "Kriterleri döneme bağlamadan önce test veya ön izleme yapın.",
        ],
        [("Değerlendirme Kriterleri", "/performance/criteria", "Kriter yönetimi"), ("Performans Ayarları", "/settings#module-foundation", "Ayar kontrolü"), ("Rol Matrisi", "/admin/role-matrix", "Yetki")],
        intro="BYS360 ekranlarında ana terim ‘Değerlendirme Kriterleri’ olmalıdır; kullanıcıya teknik/yabancı terimlerle karışık anlatılmamalıdır.",
        safety="Asistan puan veya ağırlık değiştirmez; yalnızca nasıl tanımlanacağını anlatır.",
        quick=["70 altı açıklama zorunlu mu?", "3. amir ağırlığı nasıl çalışır?", "Dönem nasıl açılır?"],
        roles=["admin", "hr_performance"],
        priority=78,
    ),
    _guide(
        "assignment_generation",
        "Performans görevleri nasıl üretilir?",
        ["gorev uret", "görev üret", "degerlendirme gorevi", "amir gorevi", "gorevler olusmadi", "performans gorevleri", "assignment"],
        [
            "Dönemin aktif ve kapsamının doğru olduğundan emin olun.",
            "Personel kayıtlarında birim, üst birim, kategori ve amir bilgilerinin dolu olduğunu kontrol edin.",
            "İzin ve vekâlet kayıtlarını kontrol edin; gerekirse vekil ilişkisini güncelleyin.",
            "Performans Yönetimi içinde görev üretimi/atama ekranını açın.",
            "Ön izleme varsa üretilecek görevleri kontrol edin.",
            "Gerçek dışı 2. amir/3. amir veya sahte bekleme görünüyorsa görev üretimini durdurup amir verisini düzeltin.",
            "Görevleri üretin ve aksatan/görev bekleyen amir listesini izleyin.",
        ],
        [("Görev Üretimi", "/performance/assignments", "Görev üretimi"), ("Personel Yönetimi", "/personnel", "Amir verisi"), ("Dönemler", "/performance/periods", "Dönem kontrolü")],
        intro="Görev üretimi, personel verisi ile performans motorunu birbirine bağlayan kritik adımdır.",
        safety="Asistan görev üretmez; yetkili kullanıcıyı üretim ekranına yönlendirir.",
        quick=["Amir zinciri nasıl çalışır?", "3. amir yoksa ne olur?", "Vekâlet görevleri etkiler mi?"],
        roles=["admin", "hr_performance"],
        priority=82,
    ),
    _guide(
        "supervisor_scoring",
        "Amir performans değerlendirmesini nasıl tamamlar?",
        ["puan ver", "degerlendirme yap", "amir puanlama", "gorevimi tamamla", "performans gorevim", "personeli puanla", "degerlendirme tamamla"],
        [
            "Performans görevlerim ekranını açın.",
            "Size atanmış değerlendirme görevini seçin.",
            "Her değerlendirme kriteri için 1-5 arası puan girin.",
            "1 veya 5 puanda açıklama zorunluysa açıklama alanını doldurun.",
            "70 altı veya 90 üstü nihai etki oluşuyorsa ayrıntılı genel görüş gerekebileceğini unutmayın.",
            "Önceki amir değerlendirmesi görünüyorsa bunu dikkate alarak kendi kanaatinizi yazın; BYS360 kör değerlendirme yapmaz.",
            "Kaydedin ve görevi tamamla/onaya gönder adımını bitirin.",
        ],
        [("Performans Görevlerim", "/performance/tasks", "Amir görevleri"), ("Performans Paneli", "/performance/dashboard", "Süreç özeti"), ("Yardım", "/support", "Sorun bildir")],
        intro="Amir puanlamasında amaç yalnızca sayı girmek değil; kriter bazlı, gerekçeli ve izlenebilir değerlendirme yapmaktır.",
        safety="Asistan puan önermez, puan vermez ve amir görüşü üretmez; işlem adımlarını açıklar.",
        quick=["1 ve 5 puanda açıklama zorunlu mu?", "70 altı olursa ne olur?", "Kör değerlendirme var mı?"],
        roles=["supervisor", "group_head", "coordinator", "president", "upper_management"],
        priority=86,
    ),
    _guide(
        "third_supervisor",
        "3. amir kuralı nasıl çalışır?",
        ["3 amir", "ucuncu amir", "üçüncü amir", "yorum modu", "puan modu", "birim sorumlusu", "3 amir yok", "opsiyonel amir"],
        [
            "Önce ilgili personelin yapısında gerçekten 3. amir gerekip gerekmediğini kontrol edin.",
            "Sistem ayarlarında 3. amirin yorum modu mu puan modu mu çalışacağını belirleyin.",
            "Yorum modunda 3. amir yalnızca görüş yazar; puana etkisi %0 olur.",
            "Puan modunda 3. amir ağırlığa dahil edilir ve toplam ağırlık yine %100 olmalıdır.",
            "3. amir olmayan personelde boş sütun, sahte görev veya yanlış bekleme statüsü gösterilmemelidir.",
            "Çok seviyeli yapılarda işlem sırası genellikle varsa 3 → 2 → 1 şeklinde ilerler.",
        ],
        [("Performans Ayarları", "/settings#module-foundation", "3. amir modu"), ("Görev Üretimi", "/performance/assignments", "Görev kontrolü"), ("Süreç Takibi", "/performance/process-tracking", "Akış durumu")],
        intro="3. amir BYS360’da zorunlu değildir; yalnızca kurum yapısında gerçekten gerekiyorsa kullanılır.",
        safety="Asistan 3. amir atamaz; kuralı anlatır ve ilgili ayar ekranına yönlendirir.",
        quick=["Amir zinciri nasıl çalışır?", "Görev üretimi nasıl yapılır?", "Ağırlık toplamı nasıl korunur?"],
        priority=82,
    ),
    _guide(
        "low_score_approval",
        "70 altı performans sonucu nasıl ilerler?",
        ["70 alti", "70 altı", "dusuk performans", "başkan onayı", "baskan onayi", "yetersiz", "uyari", "ikinci kez", "is akdi", "tekrarlayan dusuk"],
        [
            "Değerlendirme tamamlanır ve sistem nihai başarı puanını hesaplar.",
            "Nihai puan 70’in altındaysa sonuç doğrudan kesinleşmez.",
            "Kayıt Başkan/Üst Onay sürecine alınır ve yayın kilidi oluşur.",
            "Başkan/Üst Onay tamamlanmadan personel bu sonucu kesin/yayınlanmış karne olarak göremez.",
            "İlk 70 altı sonuçta düşük performans uyarısı ve personel süreç kaydı oluşturulur.",
            "Aynı takvim yılında ikinci 70 altı durumda tekrarlayan düşük performans süreci başlar; sistem otomatik idari işlem yapmazma yapmaz.",
            "Gerekli üst onaylar ve yayın ön onayı tamamlandıktan sonra Admin/İK nihai yayın adımını yürütür.",
        ],
        [("Başkan Onayları", "/performance/president-approvals", "70 altı onayları"), ("Süreç Takibi", "/performance/process-tracking", "Süreç akışı"), ("Performans Raporları", "/performance/reports", "Düşük performans raporları")],
        intro="70 altı sonuç BYS360’da yalnızca puan değildir; onay, uyarı, süreç zinciri ve yayın kilidiyle yönetilen resmi performans sürecidir.",
        safety="Asistan onay/ret vermez, idari karar üretmez ve personel hakkında işlem tesis etmez.",
        quick=["Karne ne zaman görünür?", "Başkan Onayı ekranında ne görünür?", "İkinci kez 70 altı ne olur?"],
        priority=94,
    ),
    _guide(
        "scorecard_publish",
        "Karne ne zaman ve nasıl personele yayınlanır?",
        ["karne yayin", "karne yayın", "karnem nerede", "sonucumu goremedim", "performans sonucum", "yayın kilidi", "yayin kilidi", "personel karne", "not karnesi"],
        [
            "Tüm amir değerlendirme görevlerinin tamamlandığını kontrol edin.",
            "Açıklama zorunluluklarının yerine getirilip getirilmediğini kontrol edin.",
            "70 altı kayıt varsa Başkan/Üst Onay sürecinin tamamlanmasını bekleyin.",
            "Personel ve Destek Hizmetleri Grup Başkanı yayın ön onayı gerekiyorsa bu adımı tamamlayın.",
            "Admin/İK yetkili kişi nihai yayın işlemini yapar.",
            "Yayın sonrası personel kendi karnesini ve yetki verilen genel/kategori özetini görebilir.",
            "Yayın öncesi personel kendi nihai sonucunu görmemelidir.",
        ],
        [("Yayın Kontrolü", "/performance/publish", "Karne yayın işlemi"), ("Başkan Onayları", "/performance/president-approvals", "Düşük performans onayı"), ("Karnem", "/performance/scorecard", "Personel karne")],
        intro="BYS360’da karne görünürlüğü süreç tamamlandıktan ve gerekli onaylar alındıktan sonra açılır.",
        safety="Asistan karneyi yayınlamaz ve puan/görüş içeriği göstermez; yalnızca doğru ekrana yönlendirir.",
        quick=["70 altı süreç nasıl ilerler?", "Personel neyi görebilir?", "Yayın kilidi ne demek?"],
        priority=90,
    ),
    _guide(
        "archive_scorecards",
        "Geçmiş yıl karne ve puan arşivi nasıl kullanılır?",
        ["gecmis karne", "geçmiş karne", "arsiv", "arşiv", "eski puan", "2024 puan", "2025 karne", "performans gecmisi"],
        [
            "Performans Yönetimi içinde Geçmiş Karne/Puan Arşivi ekranını açın.",
            "Yıl, dönem, personel, birim veya kategori filtresini seçin.",
            "Personel kendi yayınlanmış geçmiş karnelerini görebilir; başka kişilerin detaylarını göremez.",
            "Yönetici yalnızca yetkili olduğu kapsamın geçmişini görmelidir.",
            "Eski puan ekleme veya import işlemi varsa yetkili kullanıcı tarafından yapılmalıdır.",
            "Aktarım sonrası kayıtların personel geçmişi ve raporlara doğru yansıdığını kontrol edin.",
        ],
        [("Geçmiş Karne Arşivi", "/performance/archive", "Geçmiş karneler"), ("Performans Raporları", "/performance/reports", "Raporlar"), ("Personel Kartı", "/personnel", "Personel geçmişi")],
        intro="Geçmiş karne arşivi kurumsal hafızayı güçlendirir ve personelin dönemsel gelişimini izlenebilir hale getirir.",
        safety="Asistan geçmiş puan içeriği dökmez; yetkili arşiv ekranına yönlendirir.",
        quick=["Karne nasıl yayınlanır?", "Eski puan importu nasıl yapılır?"],
        priority=70,
    ),
    _guide(
        "in_period_notes",
        "Dönem içi not ve ara geri bildirim nasıl girilir?",
        ["donem ici not", "dönem içi not", "ara geri bildirim", "olumlu not", "olumsuz not", "gelisim ihtiyaci", "gözlem", "gozlem"],
        [
            "Performans Yönetimi içinde Dönem İçi Notlar veya Ara Geri Bildirim ekranını açın.",
            "Personel, dönem ve not türünü seçin: olumlu olay, gelişim ihtiyacı, genel gözlem veya takip notu.",
            "Kısa, somut ve kurumsal dille açıklama yazın.",
            "Varsa tarih, konu veya destekleyici bilgi alanlarını doldurun.",
            "Kaydedin ve notun ilgili dönem/personel kaydına bağlandığını kontrol edin.",
            "Bu notların otomatik puan üretmediğini; sadece değerlendirme sürecine hatırlatma/rehber bilgi sunduğunu unutmayın.",
        ],
        [("Dönem İçi Notlar", "/performance/in-period-notes", "Ara notlar"), ("Gelişim Önerileri", "/performance/development", "Gelişim alanı"), ("Performans Görevleri", "/performance/tasks", "Değerlendirme")],
        intro="Dönem içi notlar performans döneminin sonunda unutulan olayları kayıtlı ve izlenebilir hale getirir.",
        safety="Asistan not yazmaz veya puan oluşturmaz; notun nasıl girileceğini öğretir.",
        quick=["Gelişim önerisi nasıl yazılır?", "Bu not puanı etkiler mi?"],
        roles=["supervisor", "group_head", "coordinator", "hr_performance", "admin"],
        priority=72,
    ),
    _guide(
        "development_suggestion",
        "Gelişim önerisi nasıl yazılır?",
        ["gelisim onerisi", "gelişim önerisi", "egitim onerisi", "rehber not", "guclu yon", "gelisim alani", "performans sonrasi"],
        [
            "Performans veya karne ekranında Gelişim Önerisi/Rehber Alanı bölümünü açın.",
            "Personelin güçlü yönünü, gelişim alanını ve önerilen takip adımını ayrı ayrı yazın.",
            "Kişiyi hedef alan sert/etiketleyici dil yerine gelişim odaklı kurumsal dil kullanın.",
            "Öneriyi otomatik karar gibi değil, amir/kurum değerlendirmesine destek notu olarak kaydedin.",
            "Kaydın karne, süreç geçmişi veya gelişim ekranında nasıl görüneceğini kontrol edin.",
        ],
        [("Gelişim Önerileri", "/performance/development", "Gelişim notları"), ("Karne", "/performance/scorecard", "Karne görünümü"), ("Performans Raporları", "/performance/reports", "Gelişim raporu")],
        intro="Gelişim önerisi, performans sonucunu yalnızca puanla bırakmayıp takip edilebilir gelişim notuna dönüştürür.",
        safety="Asistan kişi hakkında öneri kararı üretmez; yazım mantığını ve ekran yolunu anlatır.",
        quick=["Dönem içi not nasıl girilir?", "70 altı süreçte gelişim notu gerekir mi?"],
        roles=["supervisor", "group_head", "coordinator", "hr_performance", "admin"],
        priority=70,
    ),
    _guide(
        "dashboard_reports",
        "Dashboard ve raporlar nasıl kullanılır?",
        ["dashboard", "rapor", "analiz", "canli performans haritasi", "riskli personel", "aksatan amir", "birim ortalamasi", "kategori ortalamasi", "yonetici paneli"],
        [
            "Performans Dashboard veya Raporlar ekranını açın.",
            "Dönem, birim, üst birim, kategori veya kapsam filtresini seçin.",
            "Tamamlanma oranı, geciken amirler, riskli personel ve düşük/yüksek performans alanlarını kontrol edin.",
            "Kişi detayı görmeniz gerekiyorsa bunun rol ve yetki kapsamınızda olduğundan emin olun.",
            "Raporu paylaşmadan önce hassas veri, puan ve görüş görünürlüğünü kontrol edin.",
            "AI Karar Destek özeti varsa nihai karar gibi değil, dikkat notu olarak değerlendirin.",
        ],
        [("Performans Dashboard", "/performance/dashboard", "Yönetici görünümü"), ("Performans Raporları", "/performance/reports", "Raporlama"), ("AI Karar Destek", "/ai/decision-support", "Özet ve analiz")],
        intro="Dashboardlar yöneticinin süreçleri hızlı görmesi içindir; kişi detayları her zaman yetki sınırıyla korunmalıdır.",
        safety="Asistan rapordaki hassas kişi verilerini doğrudan dökmez; yetkili ekrana yönlendirir.",
        quick=["Aksatan amir nasıl görülür?", "Kategori ortalaması nedir?", "AI Karar Destek karar verir mi?"],
        priority=80,
    ),
    _guide(
        "role_matrix",
        "Rol matrisi ve menü görünürlüğü nasıl kullanılır?",
        ["rol matrisi", "yetki", "menu gorunmuyor", "menü görünmüyor", "sekme yok", "erisim engeli", "kapat aç", "modul yetki", "kisi bazli", "birim bazli"],
        [
            "Sistem Ayarları veya Admin içindeki Rol Matrisi ekranını açın.",
            "Önce modül bazlı görünürlüğü kontrol edin: Personel, Performans, İletişim, Anket, Destek, AI, KPI.",
            "Sonra rol bazlı varsayılan yetkiyi kontrol edin.",
            "Gerekirse kişi bazlı özel görünürlük veya birim bazlı menü profilini kontrol edin.",
            "Menü kapalıysa kullanıcı sol menüde hiç görmemelidir; sadece erişim engeli vermesi yeterli değildir.",
            "Backend route yetkisi de ayrıca korunmalıdır; URL yazan kullanıcı yetkisiz veri alamamalıdır.",
            "Değişiklik sonrası çıkış/giriş veya cache yenileme gerekiyorsa bunu uygulayın.",
        ],
        [("Rol Matrisi", "/admin/role-matrix", "Rol bazlı görünürlük"), ("Sistem Ayarları", "/settings", "Genel ayarlar"), ("Audit Log", "/admin/audit-logs", "Değişiklik izleri")],
        intro="BYS360’da rol matrisi yalnızca menü düzeni değildir; güvenlik, süreç ve veri görünürlüğü kontrolüdür.",
        safety="Asistan yetki vermez veya kaldırmaz; sadece hangi ayarın kontrol edileceğini anlatır.",
        quick=["Menü kapalı ama görünüyor ne yapmalıyım?", "Kişi bazlı yetki nedir?", "Backend route yetkisi neden önemli?"],
        roles=["admin"],
        priority=90,
    ),
    _guide(
        "support_ticket",
        "Destek talebi nasıl açılır?",
        ["destek talebi", "yardim talebi", "yardım talebi", "sorun bildir", "hata bildir", "talep ac", "ariza", "çalışmıyor", "calismiyor"],
        [
            "Destek veya Yardım Merkezi ekranını açın.",
            "Yeni destek talebi oluştur seçeneğine girin.",
            "Kategori, konu başlığı ve açıklamayı sade şekilde yazın.",
            "Ekran görüntüsü veya belge gerekiyorsa güvenli dosya eki olarak ekleyin.",
            "Talebi gönderin ve oluşan durum bilgisini takip edin.",
            "Cevap geldikçe talep geçmişinden izleyin; çözüldüyse kapatma veya geri bildirim adımını tamamlayın.",
        ],
        [("Destek Talepleri", "/support", "Taleplerim"), ("Yeni Destek Talebi", "/support/new", "Talep oluştur"), ("Yardım Merkezi", "/help", "Kullanım yardımı")],
        intro="Destek talepleri kişisel yazışmalarda kaybolmaması için BYS360 içinde kayıtlı ve izlenebilir yürütülmelidir.",
        safety="Asistan talep içeriğini başkalarına göstermez; sadece talep açma yolunu anlatır.",
        quick=["Menü görünmüyor ne yapmalıyım?", "Asistana hata nasıl sorulur?"],
        priority=78,
    ),
    _guide(
        "communication",
        "Mesaj, duyuru ve bildirimler nasıl kullanılır?",
        ["mesaj", "duyuru", "bildirim", "okunmamis", "okunmamış", "mail", "kurum ici iletisim", "yazisma", "duyuru yap"],
        [
            "İletişim, Mesajlar, Duyurular veya Bildirimler ekranını açın.",
            "Mesajlaşmada kişi/grup veya konu bazlı konuşmayı seçin.",
            "Duyuru oluşturuyorsanız hedef kitleyi, tarih aralığını ve görünürlük kapsamını belirleyin.",
            "Dosya eki varsa güvenli dosya sınırlarına uygun ekleyin.",
            "Bildirim veya duyurunun doğru hedef kitleye gittiğini kontrol edin.",
            "Raporlama gerekiyorsa okunma/erişim durumunu ilgili ekrandan izleyin.",
        ],
        [("Mesajlar", "/messages", "Kurum içi mesajlaşma"), ("Duyurular", "/announcements", "Duyuru yönetimi"), ("Bildirimler", "/notifications", "Bildirimler")],
        intro="İletişim modülü mesaj, duyuru, bildirim ve dosya paylaşımını kayıtlı kurumsal hafızaya taşır.",
        safety="Asistan mesaj metni veya dosya içeriği göstermez; yalnızca ilgili ekrana yönlendirir.",
        quick=["Anket nasıl oluşturulur?", "Destek talebi nasıl açılır?", "Bildirimler nerede?"],
        priority=72,
    ),
    _guide(
        "survey_feedback",
        "Anket ve geri bildirim nasıl kullanılır?",
        ["anket", "anket olustur", "anket cevapla", "geri bildirim", "nabiz", "nabız", "kampanya", "memnuniyet", "anket sonucu"],
        [
            "Anket veya Geri Bildirim ekranını açın.",
            "Yeni anket oluşturuyorsanız başlık, açıklama, soru türleri ve hedef kitleyi belirleyin.",
            "Katılımcı atama ve tarih aralığını kontrol edin.",
            "Personel olarak size atanmış anket varsa cevaplama ekranına girin ve gönderin.",
            "Sonuç ekranında katılım oranı ve genel dağılımı izleyin.",
            "Açık uçlu cevaplar ve kişisel sonuçlar yalnızca yetkili kullanıcılarca görülmelidir.",
        ],
        [("Anketler", "/surveys", "Anket yönetimi"), ("Geri Bildirim", "/communication/feedback", "Geri bildirim/nabız"), ("Raporlar", "/communication/reports", "Katılım raporu")],
        intro="Anket ve geri bildirim modülü kurum içi katılımı ölçülebilir hale getirir.",
        safety="Asistan anket cevabı veya kişisel geri bildirim içeriği göstermez; yalnızca sayı/özet ve yönlendirme yapar.",
        quick=["Anket sonucunu kim görebilir?", "Geri bildirim kampanyası nedir?"],
        priority=74,
    ),
    _guide(
        "ai_decision_support",
        "AI Karar Destek Merkezi nasıl kullanılır?",
        ["ai karar destek", "yapay zeka karar", "özetle", "ozetle", "risk analizi", "ai analiz", "karar verir mi", "onerir mi", "yönetici özeti", "yonetici ozeti"],
        [
            "AI Karar Destek Merkezi ekranını açın.",
            "İlgili analiz başlığını seçin: performans, anket, destek, KPI veya yönetici özeti.",
            "Sistem yalnızca yetkili olduğunuz kapsamda özet ve dikkat notu üretmelidir.",
            "AI çıktısını nihai karar olarak değil, insan denetimli karar destek notu olarak değerlendirin.",
            "Hassas veri, kişisel detay, mesaj içeriği veya anket cevabı gerekiyorsa redaksiyon ve yetki sınırları korunmalıdır.",
            "Gerekirse çıktı hakkında geri bildirim verin veya ilgili rapor ekranına geçin.",
        ],
        [("AI Karar Destek", "/ai/decision-support", "AI özet ve analiz"), ("AI Health", "/ai/decision-support/faz1/health", "Durum kontrolü"), ("Raporlar", "/performance/reports", "Kaynak raporlar")],
        intro="AI Karar Destek, karar veren yapı değildir; veriyi anlamlandıran, özetleyen ve yöneticinin değerlendirmesini destekleyen katmandır.",
        safety="AI ve asistan idari karar üretmez; nihai karar insana ve yetkili kurumsal sürece aittir.",
        quick=["BYS360 Asistanı ile AI Karar Destek farkı nedir?", "Hassas veri gösterir mi?"],
        priority=88,
    ),
    _guide(
        "kpi_targets",
        "KPI ve Hedef Yönetimi nasıl kullanılır?",
        ["kpi", "hedef", "hedef karti", "stratejik hedef", "gerceklesme", "riskli hedef", "hedef donemi", "yetkinlik kutuphanesi", "oz degerlendirme"],
        [
            "KPI/Hedef Yönetimi veya stratejik dashboard ekranını açın.",
            "Önce hedef dönemini seçin: yıllık, 6 aylık, 3 aylık, aylık veya özel dönem.",
            "Hedef kartında hedef adı, hedef tipi, sahip, ağırlık, hedef değer ve gerçekleşen değer alanlarını kontrol edin.",
            "KPI ölçümünde başarı oranı, risk seviyesi ve durum bilgisini izleyin.",
            "Yetkinlik veya öz değerlendirme bağlantısı varsa ilgili alanları doldurun veya kontrol edin.",
            "Riskli hedefleri dashboard üzerinden izleyin; AI özetini karar değil dikkat notu olarak kullanın.",
        ],
        [("KPI Dashboard", "/performans/stratejik/kpi-dashboard", "KPI görünümü"), ("Hedef Yönetimi", "/performans/stratejik/hedefler", "Hedef kartları"), ("AI KPI Analiz", "/performans/stratejik/kpi-analiz", "AI destekli özet")],
        intro="KPI/Hedef Yönetimi BYS360’ın stratejik ölçüm motorudur; sistemin yalnızca işlem değil ölçüm ve yönetim platformu olmasını sağlar.",
        safety="Asistan hedef kapatmaz, değer değiştirmez ve hedef başarısını kesin hüküm olarak yorumlamaz.",
        quick=["Hedef kartı nedir?", "Riskli hedef ne demek?", "AI KPI analizi karar verir mi?"],
        priority=86,
    ),
    _guide(
        "assistant_boundaries",
        "BYS360 Asistanı ne yapar, ne yapmaz?",
        ["asistan ne yapar", "ne yapabilirsin", "neleri biliyorsun", "neyi gostermez", "hassas veri", "puan goster", "mesaj oku", "anket cevabi", "amir gorusu", "karar ver"],
        [
            "Asistan işlem adımlarını öğretir: hangi menü, hangi ekran, hangi sıra.",
            "Yetki kapsamındaki sayı/genel durum özetlerini gösterebilir.",
            "Güvenli yönlendirme kartlarıyla ilgili ekrana götürür.",
            "Performans puanı, amir kanaati, mesaj metni, anket cevabı, kişisel hassas kayıt veya yetki dışı detay göstermez.",
            "İdari karar, onay/ret, personel işlemi, puan verme veya veri değiştirme yapmaz.",
            "AI Karar Destek çıktısını karar gibi sunmaz; insan denetimli değerlendirme gerekir.",
        ],
        [("BYS360 Asistanı", "/ai-agent/panel", "Asistan paneli"), ("Asistan Bilgi Bankası", "/ai-agent/knowledge", "Rehber içerik"), ("AI Karar Destek", "/ai/decision-support", "Analiz katmanı")],
        intro="BYS360 Asistanı, kullanıcıya sistemi öğreten ve doğru ekrana götüren güvenli rehberlik katmanıdır.",
        safety=NOTICE,
        quick=["BYS360 nedir?", "Personel nasıl eklenir?", "70 altı süreç nasıl ilerler?"],
        priority=92,
    ),
    _guide(
        "security_settings",
        "Güvenlik, CAPTCHA ve oturum ayarları nasıl yönetilir?",
        ["guvenlik", "captcha", "oturum", "parola", "gizli erişim bilgisi", "giris denemesi", "audit log", "kvkk", "dosya yukleme", "bakim modu"],
        [
            "Sistem Ayarları içindeki Güvenlik Ayarları ekranını açın.",
            "Başarısız giriş denemesi, CAPTCHA aktivasyonu, oturum süresi ve parola politikası ayarlarını kontrol edin.",
            "Dosya yükleme limitleri ve güvenli dosya türlerini belirleyin.",
            "Kritik işlem, rol değişikliği ve ayar değişikliği audit loglarının çalıştığını kontrol edin.",
            "Bakım modu veya canlı ortam uyarılarını yalnızca yetkili kişi yönetmelidir.",
            "Şüpheli erişim veya yetki kaçağı şüphesinde log ve rol matrisi birlikte incelenmelidir.",
        ],
        [("Güvenlik Ayarları", "/settings#settings-security-role-policy", "Güvenlik"), ("Audit Log", "/admin/audit-logs", "Denetim izleri"), ("Rol Matrisi", "/admin/role-matrix", "Yetki kontrolü")],
        intro="BYS360’da güvenlik teknik ek değil, sistemin temel tasarım ilkesidir.",
        safety="Asistan güvenlik ayarı değiştirmez; yetkili ekranı ve kontrol sırasını gösterir.",
        quick=["Rol matrisi nasıl çalışır?", "Yetki kaçağı nasıl test edilir?"],
        roles=["admin"],
        priority=76,
    ),
]

FALLBACK_QUICK = [
    "Personel nasıl eklenir?",
    "Performans dönemi nasıl açılır?",
    "Amir değerlendirmesi nasıl yapılır?",
    "70 altı süreç nasıl ilerler?",
    "Rol matrisi nasıl çalışır?",
    "Destek talebi nasıl açılır?",
]


def _guide_text(guide: dict[str, Any], role: str) -> str:
    lines: list[str] = []
    intro = guide.get("intro") or "Bu işlem için adım adım rehber aşağıdadır."
    lines.append(intro)
    lines.append("")
    lines.append("İşlem sırası:")
    for i, step in enumerate(guide.get("steps") or [], 1):
        lines.append(f"{i}. {step}")
    safety = guide.get("safety") or SECURITY_NOTICE
    lines.append("")
    lines.append(f"Yetki ve güvenlik notu: {_scope_note(role)} {safety}")
    return "\n".join(lines)


def _guide_actions(guide: dict[str, Any]) -> list[dict[str, str]]:
    return [_a(label, url, desc) for label, url, desc in guide.get("actions", [])]


def _score_guide(guide: dict[str, Any], question_norm: str) -> int:
    if not question_norm:
        return 0
    score = 0
    q_tokens = set(question_norm.split())
    for alias in guide.get("aliases", []):
        an = _norm(alias)
        if not an:
            continue
        if an == question_norm:
            score += 120
        elif an in question_norm:
            score += 60 + min(20, len(an.split()) * 2)
        else:
            overlap = q_tokens & set(an.split())
            if overlap:
                score += len(overlap) * 7
    title_tokens = set(_norm(guide.get("title", "")).split())
    score += len(q_tokens & title_tokens) * 5
    if any(x in question_norm for x in ("nasil", "nerede", "nerden", "adim", "adim adim", "ogret", "yapacagim", "olustur", "ekle", "ac", "kullan")):
        score += 8
    score += int(guide.get("priority", 50)) // 10
    return score


def find_stepwise_guide(question: str) -> dict[str, Any] | None:
    qn = _norm(question)
    if not qn:
        return STEPWISE_GUIDES[0]
    scored = sorted(((_score_guide(g, qn), int(g.get("priority", 50)), g) for g in STEPWISE_GUIDES), key=lambda x: (x[0], x[1]), reverse=True)
    best_score, _, best = scored[0]
    return best if best_score >= 24 else None


def _maybe_route_general(question: str) -> dict[str, Any] | None:
    qn = _norm(question)
    if any(x in qn for x in ("tum ozellik", "butun ozellik", "her seyi ogret", "her şeyi öğret", "sistemin tamam", "modulleri anlat", "bys360 nasil kullanilir", "bys360 kullanmayi ogret")):
        return STEPWISE_GUIDES[0]
    return None


def build_bys360_assistant_stepwise_reply(user: Any, question: str) -> dict[str, Any] | None:
    q = question or ""
    role = _role_from_user(user)
    guide = _maybe_route_general(q) or find_stepwise_guide(q)
    if not guide:
        # Do not return None for broad human-like usage questions; provide a teaching fallback.
        qn = _norm(q)
        if any(x in qn for x in ("nasil", "nerede", "niye", "neden", "yapamiyorum", "bulamiyorum", "acilmiyor", "gorunmuyor", "ogret", "yardim")):
            guide = STEPWISE_GUIDES[0]
        else:
            return None
    return {
        "ok": True,
        "version": VERSION,
        "mode": MODE,
        "intent": f"stepwise_tutor:{guide['key']}",
        "assistant_name": ASSISTANT_NAME,
        "topic": guide.get("title"),
        "role_scope": _role_label(role),
        "answer": _guide_text(guide, role),
        "actions": _guide_actions(guide),
        "quick_replies": guide.get("quick") or FALLBACK_QUICK,
        "notice": NOTICE,
        "security_notice": SECURITY_NOTICE,
    }


def get_bys360_stepwise_guide_index() -> list[dict[str, Any]]:
    return [
        {
            "key": g["key"],
            "title": g["title"],
            "aliases": list(g.get("aliases", [])[:10]),
            "actions": [{"label": a[0], "url": a[1], "description": a[2]} for a in g.get("actions", [])],
            "quick_replies": g.get("quick") or FALLBACK_QUICK,
            "priority": g.get("priority", 50),
        }
        for g in STEPWISE_GUIDES
    ]


__all__ = [
    "VERSION",
    "MODE",
    "ASSISTANT_NAME",
    "build_bys360_assistant_stepwise_reply",
    "find_stepwise_guide",
    "get_bys360_stepwise_guide_index",
]
