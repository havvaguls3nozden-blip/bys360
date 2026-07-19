from __future__ import annotations

# BYS360_ASSISTANT_KNOWLEDGE_BANK_V1

from dataclasses import dataclass
from typing import Any

VERSION = "BYS360 Asistanı Bilgi Bankası V1"
MODE = "Rol bazlı adım adım kullanım rehberi"
NOTICE = "BYS360 Asistanı idari karar vermez, performans puanı üretmez, onay/ret işlemi yapmaz ve yetki dışı hassas veri göstermez."
SECURITY_NOTICE = "Bu cevap yalnızca kullanım rehberi ve güvenli yönlendirme amaçlıdır; gerçek işlem ilgili ekranda yetkili kullanıcı tarafından yapılır."


@dataclass(frozen=True)
class GuideTopic:
    key: str
    title: str
    keywords: tuple[str, ...]
    answer: str
    actions: tuple[tuple[str, str, str], ...] = ()
    allowed_roles: tuple[str, ...] = ("all",)
    quick_replies: tuple[str, ...] = ()


def _norm(value: Any) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
        .replace("İ", "i")
        .replace("ı", "i")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ö", "o")
        .replace("ç", "c")
    )


def _role_from_user(user: Any) -> str:
    """Kullanıcı nesnesinden en güvenli rol ipucunu alır. Bulamazsa standart kullanıcı döner."""
    candidates: list[str] = []
    for attr in (
        "role",
        "role_name",
        "role_key",
        "user_role",
        "authority_role",
        "position",
        "title",
        "unvan",
        "job_title",
    ):
        try:
            value = getattr(user, attr, None)
            if value:
                candidates.append(str(value))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/ai_agent/assistant_knowledge_bank_v1.py)")
    try:
        if bool(getattr(user, "is_admin", False)) or bool(getattr(user, "is_superuser", False)):
            return "admin"
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/ai_agent/assistant_knowledge_bank_v1.py)")
    joined = _norm(" ".join(candidates))
    if any(x in joined for x in ("sistem", "admin", "yonetici", "superuser")):
        return "admin"
    if any(x in joined for x in ("baskan yardimcisi", "başkan yardimcisi", "ust yonetim", "üst yonetim")):
        return "upper_management"
    if "baskan" in joined or "başkan" in joined:
        return "president"
    if any(x in joined for x in ("grup baskani", "grup başkani", "grup başkanı")):
        return "group_head"
    if "koordinator" in joined or "koordinat" in joined:
        return "coordinator"
    if any(x in joined for x in ("amir", "degerlendirici", "değerlendirici")):
        return "supervisor"
    if any(x in joined for x in ("ik", "insan kaynak", "personel ve destek", "performans yetkilisi")):
        return "hr_performance"
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
        return "Rolünüz üst yönetim/yönetim kapsamındaysa genel özet ve kontrol ekranları görünebilir; yine de her veri sistem yetkisiyle sınırlıdır."
    if role == "group_head":
        return "Grup Başkanı rolünde yalnızca yetkili olduğunuz grup/üst birim kapsamındaki kayıtlar görünmelidir."
    if role == "coordinator":
        return "Koordinatör rolünde yalnızca kendi çalışma grubu veya koordinasyon kapsamınızdaki kayıtlar görünmelidir."
    if role == "supervisor":
        return "Amir rolünde yalnızca size atanmış değerlendirme görevleri ve yetkili olduğunuz personel görünmelidir."
    if role == "hr_performance":
        return "Personel/Performans yetkilisi rolünde işlem kapsamı menü ve rol matrisindeki yetkilere bağlıdır."
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


def _default_quick_replies(role: str) -> list[str]:
    base = [
        "Personel nasıl eklenir?",
        "Performans dönemi nasıl açılır?",
        "Puanlama nasıl yapılır?",
        "Karnemi nereden görürüm?",
        "Rol matrisinden menü nasıl açılır?",
        "Destek talebi nasıl oluşturulur?",
    ]
    if role in ("admin", "hr_performance", "president", "group_head"):
        base.extend([
            "Başkan onayları nasıl kullanılır?",
            "70 altı süreç nasıl ilerler?",
            "KPI/Hedef ekranları nasıl kullanılır?",
        ])
    return base[:8]


def _reply(topic: GuideTopic, user: Any, question: str) -> dict[str, Any]:
    role = _role_from_user(user)
    role_note = _role_scope_note(role)
    answer = topic.answer.strip()
    if "{{ROLE_NOTE}}" in answer:
        answer = answer.replace("{{ROLE_NOTE}}", role_note)
    else:
        answer = f"{answer}\n\nYetki notu: {role_note}"

    quick_replies = list(topic.quick_replies) if topic.quick_replies else _default_quick_replies(role)
    return {
        "ok": True,
        "version": VERSION,
        "mode": MODE,
        "assistant_name": "BYS360 Asistanı",
        "intent": topic.key,
        "topic_title": topic.title,
        "detected_role": role,
        "detected_role_label": _role_label(role),
        "question": str(question or ""),
        "answer": answer,
        "actions": _topic_actions(topic),
        "quick_replies": quick_replies,
        "notice": NOTICE,
        "security_notice": SECURITY_NOTICE,
        "automation_notice": "BYS360 Asistanı işlem yapmaz; kullanıcıyı doğru ekrana ve doğru adıma yönlendirir.",
        "assistant_panel_notice": "Merhaba, ben BYS360 Asistanı. BYS360 kullanımında size adım adım yardımcı olurum.",
    }


TOPICS: tuple[GuideTopic, ...] = (
    GuideTopic(
        key="assistant_identity",
        title="BYS360 Asistanı ne yapar?",
        keywords=("adın ne", "adin ne", "sen kimsin", "ne yapabilirsin", "asistan", "yardım", "yardim", "kullanım rehberi", "kullanim rehberi"),
        answer="""
Ben BYS360 Asistanı. BYS360 içinde kullanıcıya ekranları, işlem adımlarını ve süreç mantığını sade biçimde anlatırım.

Adım adım yardımcı olabileceğim ana alanlar:
1. Personel Yönetimi: personel kaydı, sicil, birim, yönetici, izin ve vekâlet yönlendirmeleri.
2. Performans Yönetimi: dönem, kriter, amir zinciri, puanlama, karne, 70 altı süreç ve yayın adımları.
3. İletişim / Anket / Destek: mesaj, duyuru, bildirim, anket ve destek talebi ekranları.
4. Sistem Ayarları: rol matrisi, menü görünürlüğü, modül ayarları ve güvenlik ayarları.
5. KPI / Hedef: hedef kartları, KPI dashboardu ve analiz ekranları.

Ben idari karar vermem, performans puanı üretmem, onay/ret işlemi yapmam ve yetki dışı veri göstermem.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(
            ("BYS360 Asistanı Paneli", "/ai-agent/panel", "Asistan panelini açar"),
            ("Asistan Bilgi Bankası", "/ai-agent/knowledge", "Kullanım rehberlerini gösterir"),
        ),
        quick_replies=("Personel nasıl eklenir?", "Performans dönemi nasıl açılır?", "Rol matrisi nasıl çalışır?", "KPI hedefleri nerede?"),
    ),
    GuideTopic(
        key="home_navigation",
        title="Ana ekran ve menü kullanımı",
        keywords=("ana ekran", "anasayfa", "home", "sol menü", "sol menu", "menü nerede", "menu nerede", "modül nerede", "modul nerede"),
        answer="""
Ana ekran ve sol menü kullanımı için adımlar:
1. Sisteme giriş yaptıktan sonra ana sayfada size açık modül kartlarını kontrol edin.
2. Sol menüden işlem yapmak istediğiniz ana modülü açın.
3. Alt sekmeler yalnızca yetkiniz varsa görünür; görünmeyen sekmeler için rol matrisi kontrol edilmelidir.
4. Bildirim alanından size gelen görev, anket, destek veya performans uyarılarını takip edin.
5. Sayfa açılmazsa ya yetkiniz yoktur ya da ilgili modül rol matrisinde kapalıdır.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Ana Sayfa", "/home", "BYS360 ana sayfası"), ("Bildirimler", "/notifications", "Kullanıcı bildirimleri")),
    ),
    GuideTopic(
        key="personnel_create",
        title="Personel ekleme",
        keywords=("personel ekle", "personel nasıl", "personel nasil", "personel nereden", "personel oluştur", "personel olustur", "yeni personel", "personel kaydı", "personel kaydi", "sicil", "sicil no", "personel özlük", "personel ozluk"),
        answer="""
Personel eklemek için adımlar:
1. Sol menüden Personel Yönetimi bölümünü açın.
2. Personel Özlük Dosyaları veya Personel Listesi ekranına girin.
3. Yeni personel ekleme butonunu kullanın.
4. Sicil No, ad soyad, unvan, birim, üst birim ve yönetici alanlarını doldurun.
5. Varsa profil fotoğrafı ve iletişim bilgilerini ekleyin.
6. Personel kategori/grup alanı varsa doğru kategoriyi seçin: Güvenlik, Temizlik, İdari Personel, Teknik Personel, Deneme Süreli Personel veya Diğer.
7. Kaydettikten sonra organizasyon bağlantısını ve performans zincirine etkisini kontrol edin.
8. Rol veya menü görünürlüğü gerekiyorsa Sistem Ayarları / Rol Matrisi ekranından ayrıca düzenleyin.

Not: BYS360’da TC yerine Sicil No esas alınır. Asistan personel kaydı oluşturmaz; yalnızca adımları gösterir.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Personel Yönetimi", "/personnel", "Personel kayıt ekranı"), ("Rol Matrisi", "/admin/role-matrix", "Menü ve rol görünürlüğü")),
        quick_replies=("Personel kategorisi nasıl seçilir?", "Rol matrisi nasıl ayarlanır?", "İzin ve vekâlet nasıl girilir?"),
    ),
    GuideTopic(
        key="personnel_edit_org",
        title="Personel bilgisi ve organizasyon ilişkisi düzenleme",
        keywords=("personel düzenle", "personel duzenle", "birim değiş", "birim degis", "üst birim", "ust birim", "yönetici değiş", "yonetici degis", "organizasyon"),
        answer="""
Personel bilgisi veya organizasyon ilişkisi düzenlemek için adımlar:
1. Personel Yönetimi ekranından ilgili personeli bulun.
2. Personel detay veya düzenleme ekranını açın.
3. Birim, üst birim, unvan, görev ve yönetici alanlarını kontrol edin.
4. Değişiklik performans amir zincirini etkileyebilir; dönem başlamadan önce doğru olduğundan emin olun.
5. Organizasyon geçmişi tutulan alanlarda eski kayıtların kaybolmaması gerekir.
6. Değişiklik sonrası performans görev üretimi veya menü görünürlüğü etkileniyorsa ilgili kontrol ekranlarını tekrar çalıştırın.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Personel Yönetimi", "/personnel", "Personel kayıtları"), ("Organizasyon Birimleri", "/org-units", "Birim ve üst birim ilişkileri")),
    ),
    GuideTopic(
        key="leave_delegation",
        title="İzin, devamsızlık ve vekâlet kullanımı",
        keywords=("izin", "devamsızlık", "devamsizlik", "vekâlet", "vekalet", "izin kaydı", "izin kaydi", "amir izinli", "görev devri", "gorev devri"),
        answer="""
İzin, devamsızlık veya vekâlet işlemleri için adımlar:
1. Sol menüden Personel Yönetimi bölümünü açın.
2. İzin / Devamsızlık / Vekâlet ekranına girin.
3. İlgili personeli ve tarih aralığını seçin.
4. İzin veya devamsızlık türünü belirleyin.
5. Vekâlet varsa vekil kişiyi ve geçerlilik süresini tanımlayın.
6. Amir izinliyse performans görevinin boşa düşmemesi için vekâlet ilişkisinin doğru kurulduğunu kontrol edin.
7. Kaydetmeden önce tarih çakışması ve yetki kapsamını gözden geçirin.

Asistan izin onaylamaz veya vekâlet atamaz; yalnızca işlem yolunu gösterir.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("İzin ve Devamsızlık", "/hr-management/leave", "İzin/devamsızlık ekranı"), ("Devamsızlık ve Vekâlet", "/hr-management/attendance", "Vekâlet ve devam ekranı")),
    ),
    GuideTopic(
        key="performance_period",
        title="Performans dönemi açma",
        keywords=("performans dönemi", "performans donemi", "dönem aç", "donem ac", "yeni dönem", "yeni donem", "özel dönem", "ozel donem", "kapsam tipi"),
        answer="""
Performans dönemi açmak için adımlar:
1. Sol menüden Performans Yönetimi bölümünü açın.
2. Dönem Yönetimi ekranına girin.
3. Yeni dönem oluştur butonunu seçin.
4. Dönem adını, dönem türünü ve başlangıç/bitiş tarihlerini girin.
5. Kapsam tipini seçin: tüm kurum, birim, üst birim, kategori/grup veya seçili personel.
6. Kriter ve ağırlıkların bu dönem için hazır olduğundan emin olun.
7. Personel kategori ve amir zinciri verilerini kontrol edin.
8. Kaydettikten sonra görev üretimi / değerlendirme görevleri ekranından oluşan zinciri kontrol edin.

Dönem açma işlemi rol yetkisine bağlıdır. Asistan dönem oluşturmaz; sadece adımları anlatır.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Dönem Yönetimi", "/performance/periods", "Performans dönemleri"), ("Performans Paneli", "/performance/dashboard", "Süreç izleme paneli")),
        quick_replies=("Kapsam tipi nedir?", "Görev üretimi nasıl yapılır?", "3. amir nasıl çalışır?"),
    ),
    GuideTopic(
        key="performance_criteria",
        title="Değerlendirme kriterleri",
        keywords=("kriter", "değerlendirme kriter", "degerlendirme kriter", "yetkinlik", "ağırlık", "agirlik", "puan aralığı", "puan araligi"),
        answer="""
Değerlendirme kriterleri için adımlar:
1. Performans Yönetimi bölümünden Değerlendirme Kriterleri ekranını açın.
2. Aktif dönemde kullanılacak kriterlerin açık olduğundan emin olun.
3. Kriter adları kullanıcı ekranında sade ve kurumsal dilde görünmelidir.
4. BYS360’da ana terim “Değerlendirme Kriterleri” olmalıdır; kullanıcı ekranında teknik ifade kullanılmamalıdır.
5. Kriter ağırlıkları veya puan etkileri varsa toplam kurala uygun olmalıdır.
6. Değişiklik yaptıktan sonra dönem, görev üretimi ve karne ekranındaki etkisini kontrol edin.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Değerlendirme Kriterleri", "/performance/criteria", "Kriter yönetimi"), ("Sistem Ayarları", "/settings", "Modül ayarları")),
    ),
    GuideTopic(
        key="assignment_generation",
        title="Değerlendirme görev üretimi",
        keywords=("görev üret", "gorev uret", "değerlendirme görevi", "degerlendirme gorevi", "amir zinciri", "görevler oluşmadı", "gorevler olusmadi"),
        answer="""
Performans değerlendirme görevi üretmek için adımlar:
1. Aktif performans döneminin açık olduğundan emin olun.
2. Personel kayıtlarında birim, üst birim, yönetici, kategori ve rol bilgilerinin doğru olduğunu kontrol edin.
3. Dönem kapsamına giren personeli kontrol edin.
4. Görev üretimi ekranından değerlendirme görevlerini oluşturun.
5. Oluşan görevlerde 1. amir, 2. amir ve varsa 3. amir ilişkisini kontrol edin.
6. 3. amir yoksa boş görev veya boş bekleme statüsü oluşmamalıdır.
7. Hukuk Müşavirliği ve Başkanın tek puanladığı özel roller gibi istisnalarda sahte 2./3. amir görevi üretilmemelidir.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Performans Görevleri", "/performance/tasks", "Değerlendirme görevleri"), ("Dönem Yönetimi", "/performance/periods", "Dönem ve kapsam kontrolü")),
    ),
    GuideTopic(
        key="scoring_steps",
        title="Puanlama yapma",
        keywords=("puanlama", "puan ver", "değerlendir", "degerlendir", "amir puan", "1 puan", "5 puan", "genel görüş", "genel gorus"),
        answer="""
Amir puanlama işlemi için adımlar:
1. Performans Yönetimi bölümünden Görevlerim / Performans Görevleri ekranına girin.
2. Size atanmış değerlendirme görevini seçin.
3. Personel ve dönem bilgisini kontrol edin.
4. Her değerlendirme kriteri için 1-5 arası puan girin.
5. Sistem ayarına göre 1 ve 5 puanlarda açıklama zorunlu olabilir.
6. Nihai sonuç 70 altı veya 90 üstü ise ayrıntılı genel görüş gerekebilir.
7. Kör değerlendirme yoktur; sonraki amir önceki amirin puan ve kanaatini görebilir.
8. Kaydetmeden önce tüm zorunlu açıklama alanlarını kontrol edin.

Asistan puan vermez, puan önermez ve amir görüşü yazmaz; yalnızca işlem yolunu açıklar.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Performans Görevlerim", "/performance/tasks", "Atanmış değerlendirme görevleri"), ("Puanlama Ekranı", "/performance/tasks", "Görev seçerek puanlama")),
        quick_replies=("70 altı olursa ne olur?", "Karne ne zaman yayınlanır?", "3. amir nasıl çalışır?"),
    ),
    GuideTopic(
        key="third_supervisor",
        title="3. amir kullanımı",
        keywords=("3. amir", "3 amir", "üçüncü amir", "ucuncu amir", "yorum modu", "puan modu", "üçüncü sütun", "ucuncu sutun"),
        answer="""
3. amir kuralı için temel kullanım:
1. 3. amir her personel için zorunlu değildir.
2. Yapıda gerçek 3. amir yoksa sistem boş görev veya boş sütun göstermemelidir.
3. 3. amir yorum modundaysa yalnızca görüş yazar, puana etkisi olmaz.
4. 3. amir puan modundaysa sistem ayarındaki ağırlık hesabına dahil edilir.
5. Çok seviyeli yapılarda işlem sırası genellikle varsa 3. amir, sonra 2. amir, en son 1. amir şeklindedir.
6. Kör değerlendirme yoktur; sonraki amir önceki değerlendirmeyi görür.
7. 3. amir ayarları Sistem Ayarları ve Performans Yönetimi yetkileriyle kontrol edilir.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Sistem Ayarları", "/settings", "3. amir modu ve görünürlük"), ("Performans Görevleri", "/performance/tasks", "Görev akışı kontrolü")),
    ),
    GuideTopic(
        key="scorecard_publish",
        title="Karne ve yayın süreci",
        keywords=("karne", "karnem", "not karnesi", "sonucumu", "sonucum", "yayın", "yayin", "görünmüyor", "gorunmuyor", "yayınlanmadı", "yayinlanmadi"),
        answer="""
Karne görüntüleme ve yayın mantığı:
1. Personel kendi karnesini ancak yayın/onay süreci tamamlandıktan sonra görebilir.
2. Karneniz görünmüyorsa değerlendirme henüz tamamlanmamış olabilir.
3. 70 altı sonuç varsa Başkan/Üst Onay süreci bekleniyor olabilir.
4. Yayın öncesi Personel ve Destek Hizmetleri Grup Başkanı ön onayı gerekiyorsa süreç tamamlanmadan karne açılmaz.
5. Admin/İK yetkili kişi nihai yayını yaptıktan sonra personel kendi karne ekranından sonucu görebilir.
6. Geçmiş dönemler için Geçmiş Karne/Puan Arşivi kullanılmalıdır.

Asistan puan, amir görüşü veya hassas karne detayı göstermez; ilgili ekrana yönlendirir.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Not Karnesi", "/performance/scorecard", "Yayınlanmış karne görünümü"), ("Geçmiş Karne Arşivi", "/performans/gecmis-karne-arsivi", "Geçmiş puan ve karne kayıtları")),
    ),
    GuideTopic(
        key="low_score_approval",
        title="70 altı düşük performans ve Başkan/Üst Onay",
        keywords=("70 altı", "70 alti", "düşük performans", "dusuk performans", "başkan onay", "baskan onay", "üst onay", "ust onay", "uyarı", "uyari", "ikinci 70"),
        answer="""
70 altı performans sonucunda süreç şöyle ilerler:
1. Değerlendirme tamamlanır ve nihai puan hesaplanır.
2. Nihai puan 70’in altındaysa sonuç doğrudan kesinleşmez.
3. Kayıt Başkan/Üst Onay sürecine düşer.
4. Onay tamamlanmadan karne personele kesin sonuç olarak yayınlanmaz.
5. İlk 70 altı sonuçta uyarı/süreç kaydı oluşturulur.
6. Aynı yıl ikinci 70 altı sonuçta tekrarlayan düşük performans süreci başlatılır.
7. Sistem otomatik idari işlem yapmazma yapmaz; yalnızca yetkili idari sürece kayıt üretir.
8. Başkan/Üst Onay tamamlandıktan sonra yayın ön onayı ve nihai yayın adımları işletilir.

Asistan onay/ret işlemi yapmaz; yalnızca Başkan Onayları ve Süreç Takibi ekranına yönlendirir.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Başkan Onayları", "/performance/president-approvals", "Düşük performans onay kayıtları"), ("Süreç Takibi", "/performance/process-tracking", "Personel süreç zinciri")),
        quick_replies=("Karne ne zaman yayınlanır?", "Başkan onayı olmadan görünür mü?", "Süreç takibi nerede?"),
    ),
    GuideTopic(
        key="final_publish_preapproval",
        title="Yayın ön onayı ve nihai yayın",
        keywords=("yayın ön onayı", "yayin on onayi", "personel ve destek", "nihai yayın", "nihai yayin", "final yayın", "final yayin", "yayın kilidi", "yayin kilidi"),
        answer="""
Yayın ön onayı ve nihai yayın akışı:
1. Tüm değerlendirme görevleri tamamlanır.
2. Açıklama zorunlulukları ve düşük/yüksek performans kontrolleri yapılır.
3. 70 altı kayıt varsa Başkan/Üst Onay tamamlanır.
4. Ardından sonuçlar Personel ve Destek Hizmetleri Grup Başkanı yayın ön onayına düşer.
5. Yayın ön onayı verildikten sonra Admin/İK yetkili kişi nihai yayını yapabilir.
6. Nihai yayın yapılmadan personel sonucu kesin/yayınlanmış karne olarak görmez.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Yayın Kontrolü", "/performance/publish", "Nihai yayın kontrolü"), ("Başkan Onayları", "/performance/president-approvals", "Düşük performans onayı")),
    ),
    GuideTopic(
        key="archive_history",
        title="Geçmiş yıl karne/puan arşivi",
        keywords=("geçmiş karne", "gecmis karne", "karne arşivi", "karne arsivi", "eski puan", "2024", "2025", "excel import", "geçmiş yıl", "gecmis yil"),
        answer="""
Geçmiş yıl karne/puan arşivi için adımlar:
1. Performans Yönetimi içinde Geçmiş Karne/Puan Arşivi ekranına girin.
2. Yetkiniz varsa manuel geçmiş puan ekleme veya Excel/import alanını kullanın.
3. Yıl, dönem, puan, açıklama ve kaynak belge bilgilerini eksiksiz girin.
4. Personel yalnızca kendi geçmiş puanlarını görebilmelidir.
5. Yönetici yalnızca yetkili olduğu kapsamın geçmiş kayıtlarını görmelidir.
6. Başkan/Admin genel arşiv görünürlüğüne sahip olabilir.

Asistan eski puan eklemez veya değiştirmez; yalnızca arşiv ekranına yönlendirir.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Geçmiş Karne Arşivi", "/performans/gecmis-karne-arsivi", "Geçmiş performans kayıtları"), ("Performans Raporları", "/performance/reports", "Dönemsel raporlar")),
    ),
    GuideTopic(
        key="interim_notes",
        title="Dönem içi notlar ve ara geri bildirim",
        keywords=("dönem içi not", "donem ici not", "ara geri bildirim", "olumlu olay", "olumsuz olay", "gelişim ihtiyacı", "gelisim ihtiyaci", "genel gözlem", "genel gozlem"),
        answer="""
Dönem içi notlar için adımlar:
1. Performans Yönetimi bölümünden Dönem İçi Notlar / Ara Geri Bildirim ekranına girin.
2. İlgili personeli ve dönemi seçin.
3. Not türünü belirleyin: Olumlu Olay, Olumsuz Olay, Başarı, Gelişim İhtiyacı veya Genel Gözlem.
4. Kısa, somut ve kurumsal bir açıklama yazın.
5. Bu notlar otomatik puan üretmez; puanlama döneminde amire hatırlatma ve bağlam sağlar.
6. Yetkisiz kullanıcı başka personelin not detayını görmemelidir.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Dönem İçi Notlar", "/performance/interim-notes", "Ara gözlem ve not ekranı"), ("Gelişim Rehberi", "/performance/meeting-development/faz10", "Gelişim önerileri")),
    ),
    GuideTopic(
        key="development_guidance",
        title="Gelişim önerisi ve rehber alanı",
        keywords=("gelişim önerisi", "gelisim onerisi", "gelişim rehberi", "gelisim rehberi", "öneri yaz", "oneri yaz", "eğitim önerisi", "egitim onerisi"),
        answer="""
Gelişim önerisi kullanımı için adımlar:
1. Performans Yönetimi içinde ilgili karne veya Gelişim Rehberi ekranını açın.
2. Personelin güçlü yönleri, gelişim alanları ve takip önerileri ayrı ayrı yazılmalıdır.
3. Öneri dili cezalandırıcı değil, geliştirici ve kurumsal olmalıdır.
4. Düşük performans durumunda gelişim önerisi süreç kaydıyla uyumlu olmalıdır.
5. Asistan öneri metni yazdırmaz; nasıl yazılması gerektiğini ve hangi ekrana gidileceğini anlatır.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Gelişim Rehberi", "/performance/meeting-development/faz10", "Gelişim önerisi ekranı"), ("Karne", "/performance/scorecard", "Karne detayları")),
    ),
    GuideTopic(
        key="role_matrix_visibility",
        title="Rol Matrisi ve menü görünürlüğü",
        keywords=("rol matrisi", "menü görünürlüğü", "menu gorunurlugu", "menü aç", "menu ac", "menü kapat", "menu kapat", "yetki", "erişim", "erisim", "görünmüyor", "gorunmuyor", "sekme yok", "sekme görünmüyor"),
        answer="""
Rol Matrisi ve menü görünürlüğü için adımlar:
1. Sistem Ayarları bölümünden Rol Matrisi / Menü Görünürlüğü ekranına girin.
2. İlgili rolü veya kullanıcıyı seçin.
3. Açılacak modül ve alt sekmeyi işaretleyin; kapatılacak sekmeyi kaldırın.
4. Kişi bazlı özel yetki varsa rol ayarından ayrı kontrol edin.
5. Ayarı kaydettikten sonra kullanıcının menüsü yeniden hesaplanmalıdır.
6. Menü görünürlüğü ile backend route yetkisi birlikte çalışmalıdır; sadece tıklayınca erişim engeli vermek yeterli değildir.
7. Yetkisiz kullanıcı menüyü hiç görmemeli; URL yazarsa kurumsal erişim engeli ekranı görmelidir.

Asistan yetki vermez veya kaldırmaz; yalnızca doğru ayar ekranına yönlendirir.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Rol Matrisi", "/admin/role-matrix", "Rol ve menü ayarları"), ("Sistem Ayarları", "/settings", "Genel ayarlar")),
        quick_replies=("Menü kapalı ama görünüyor ne yapmalıyım?", "Yetkisiz erişim ekranı nasıl olmalı?", "Asistan menüsü kimlere görünür?"),
    ),
    GuideTopic(
        key="access_denied",
        title="Yetkisiz erişim ve beyaz sayfa kontrolü",
        keywords=("erişim engeli", "erisim engeli", "yetkisiz", "beyaz sayfa", "white screen", "404", "403", "sayfa açılmıyor", "sayfa acilmiyor"),
        answer="""
Yetkisiz erişim veya beyaz sayfa durumunda kontrol adımları:
1. Kullanıcının ilgili menüyü görme yetkisi var mı Rol Matrisi üzerinden kontrol edin.
2. Backend route yetkisi menü görünürlüğüyle uyumlu mu kontrol edin.
3. Yetkisiz kullanıcı beyaz sayfaya düşmemeli; kurumsal “Bu sayfaya erişim yetkiniz bulunmamaktadır.” ekranı görmelidir.
4. Sayfa beyaz kalıyorsa template/render hatası, route hatası veya eksik include olabilir.
5. Hata teknik logda incelenmeli; kullanıcı ekranına teknik traceback gösterilmemelidir.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Rol Matrisi", "/admin/role-matrix", "Yetki kontrolü"), ("Sistem Ayarları", "/settings", "Güvenlik ve görünürlük ayarları")),
    ),
    GuideTopic(
        key="support_ticket",
        title="Destek talebi oluşturma",
        keywords=("destek", "talep", "yardım", "yardim", "arıza", "ariza", "destek talebi", "yardım merkezi", "yardim merkezi"),
        answer="""
Destek talebi oluşturmak için adımlar:
1. Sol menüden Destek / Yardım Merkezi ekranına girin.
2. Yeni destek talebi oluştur butonunu seçin.
3. Kategori, konu başlığı ve açıklama alanlarını doldurun.
4. Gerekirse ekran görüntüsü veya belge ekleyin.
5. Talebi kaydedin ve durumunu Destek Taleplerim ekranından takip edin.
6. Asistan destek talebini sizin adınıza kapatmaz veya içerik dökmez; sadece doğru ekrana yönlendirir.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Destek Talebi Oluştur", "/support/new", "Yeni destek kaydı"), ("Destek Taleplerim", "/support", "Açık ve kapanan talepler")),
    ),
    GuideTopic(
        key="survey_feedback",
        title="Anket ve geri bildirim kullanımı",
        keywords=("anket", "anketler", "anket cevapla", "geri bildirim", "nabız", "nabiz", "kampanya", "anket sonucu"),
        answer="""
Anket ve geri bildirim kullanımı için adımlar:
1. Sol menüden İletişim / Anket veya Anketlerim ekranına girin.
2. Size atanmış açık anketleri kontrol edin.
3. Anket sorularını yanıtlayın ve kaydedin.
4. Geri bildirim veya nabız kampanyası varsa ilgili ekrandan görüşünüzü iletin.
5. Anket cevapları kişisel ve hassas olabilir; Asistan cevap içeriğini göstermez.
6. Yöneticiler yalnızca yetkileri dahilindeki sonuç özetlerini görmelidir; kişi bazlı hassas veri dökülmemelidir.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Anketler", "/surveys", "Anket listesi"), ("Geri Bildirim", "/communication/feedback", "Geri bildirim alanı")),
    ),
    GuideTopic(
        key="communication_messages",
        title="Mesaj, duyuru ve bildirimler",
        keywords=("mesaj", "duyuru", "bildirim", "okunmamış", "okunmamis", "mail", "e-posta", "iletişim", "iletisim"),
        answer="""
Mesaj, duyuru ve bildirimleri takip etmek için adımlar:
1. Bildirimler alanından size gelen sistem uyarılarını kontrol edin.
2. Mesajlar ekranından kurum içi yazışmalarınızı takip edin.
3. Duyurular ekranından size açık kurumsal duyuruları okuyun.
4. Kritik süreçlerde e-posta bildirimi gelebilir; sistem içi kayıt esas alınmalıdır.
5. Asistan mesaj, duyuru veya anket cevabı içeriğini dökmez; yalnızca ilgili ekrana yönlendirir.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Bildirimler", "/notifications", "Sistem bildirimleri"), ("Mesajlar", "/messages", "Kurum içi mesajlaşma"), ("Duyurular", "/announcements", "Duyuru ekranı")),
    ),
    GuideTopic(
        key="kpi_targets",
        title="KPI/Hedef Yönetimi kullanımı",
        keywords=("kpi", "hedef", "stratejik", "hedef kartı", "hedef karti", "hedef dönemi", "hedef donemi", "gerçekleşme", "gerceklesme", "riskli hedef", "dashboard"),
        answer="""
KPI/Hedef Yönetimi kullanımı için adımlar:
1. KPI/Hedef veya Stratejik Performans ekranına girin.
2. Önce hedef dönemini seçin: yıllık, çeyreklik, birim veya kategori bazlı dönem olabilir.
3. Hedef kartında hedef adı, hedef tipi, sahip, ağırlık, hedef değer, gerçekleşen değer ve durum alanlarını kontrol edin.
4. Dashboard ekranında gerçekleşme oranı, riskli hedefler ve genel ilerleme izlenir.
5. KPI verileri performans, dashboard ve AI Karar Destek katmanlarına güvenli özet üretir.
6. Asistan hedef kapatmaz, hedef değeri değiştirmez ve yönetici kararı vermez; yalnızca ekran kullanımını anlatır.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("KPI/Hedef Paneli", "/performans/stratejik/kpi-dashboard", "KPI ve hedef dashboardu"), ("KPI Analiz", "/performans/stratejik/kpi-analiz", "Hedef analiz ekranı")),
        quick_replies=("Hedef kartı nasıl açılır?", "Riskli hedef ne demek?", "Dashboard nerede?"),
    ),
    GuideTopic(
        key="reports_dashboard",
        title="Raporlar ve yönetici görünürlüğü",
        keywords=("rapor", "raporlama", "analiz", "yönetici görünürlüğü", "yonetici gorunurlugu", "riskli personel", "canlı performans haritası", "canli performans haritasi", "aksatan amir"),
        answer="""
Raporlar ve yönetici görünürlüğü için adımlar:
1. Performans Yönetimi veya Dashboard bölümünden rapor ekranını açın.
2. Dönem, birim, kategori, grup veya personel kapsamına göre filtreleme yapın.
3. Riskli personel, düşük performans yoğunluğu, aksatan amirler ve tamamlanma oranlarını kontrol edin.
4. Personel detayları rol ve yetki kapsamına göre görünmelidir.
5. Standart personel yalnızca kendi karne ve kendi kategori/grup ortalamasını kişi detayı olmadan görebilir.
6. Teknik statüler kullanıcı ekranında görünmemeli; Türkçe kurumsal ifadeler kullanılmalıdır.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Performans Raporları", "/performance/reports", "Performans analizleri"), ("Yönetici Dashboard", "/performance/dashboard", "Yönetici görünürlüğü")),
    ),
    GuideTopic(
        key="assistant_settings",
        title="BYS360 Asistanı görünürlüğü ve bilgi bankası",
        keywords=("asistan görünmüyor", "asistan gorunmuyor", "asistan açılmıyor", "asistan acilmiyor", "bilgi bankası", "bilgi bankasi", "öğretim merkezi", "ogretim merkezi", "asistan bilgisi"),
        answer="""
BYS360 Asistanı görünürlüğü ve bilgi bankası için adımlar:
1. Asistan sağ alt panelde görünmüyorsa Rol Matrisi / Menü Görünürlüğü ayarını kontrol edin.
2. Asistan paneli tıklanınca açılmıyorsa JS/CSS include sayısı ve base.html include alanı kontrol edilmelidir.
3. Asistan adı kullanıcı tarafında “BYS360 Asistanı” olarak görünmelidir.
4. Bilgi Bankası ekranı kullanım rehberi mantığıyla çalışmalı; teknik “AI Ajanı” dili kullanıcıya gösterilmemelidir.
5. Asistan genel sohbet botu gibi değil; BYS360 ekranlarını adım adım öğreten kurumsal rehber gibi cevap vermelidir.
6. AI Karar Destek Merkezi ayrı kalır; BYS360 Asistanı idari karar veya puan üretmez.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("BYS360 Asistanı Paneli", "/ai-agent/panel", "Asistan paneli"), ("Asistan Bilgi Bankası", "/ai-agent/knowledge", "Kullanım rehberleri"), ("Rol Matrisi", "/admin/role-matrix", "Asistan görünürlüğü")),
    ),
    GuideTopic(
        key="security_settings",
        title="Güvenlik, oturum ve CAPTCHA",
        keywords=("güvenlik", "guvenlik", "captcha", "oturum", "gizli erişim bilgisi", "gizli erişim bilgisi", "kvkk", "audit", "log", "hassas veri"),
        answer="""
Güvenlik ve oturum ayarları için adımlar:
1. Sistem Ayarları bölümünden Güvenlik Ayarları ekranını açın.
2. Oturum süresi, parola politikası, CAPTCHA ve güvenli çıkış kurallarını kontrol edin.
3. 3 hatalı girişten sonra CAPTCHA aktif olmalıdır.
4. Hassas veriler yetki dışında görünmemeli; asistan kişisel içerik dökmemelidir.
5. Kritik ayar ve yetki değişiklikleri audit log ile izlenmelidir.
6. Canlı ortamda teknik hata mesajı kullanıcıya gösterilmemeli; kurumsal hata ekranı kullanılmalıdır.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Sistem Ayarları", "/settings", "Güvenlik ayarları"), ("Audit Log", "/admin/audit-logs", "Değişiklik geçmişi")),
    ),
    GuideTopic(
        key="live_operation",
        title="Canlı yayın ve servis kontrolü",
        keywords=("canlı", "canli", "pilot yayın", "pilot yayin", "waitress", "scheduled task", "servis", "restart", "yeniden başlat", "yeniden baslat"),
        answer="""
Canlı yayın ve servis kontrolü için genel adımlar:
1. Overlay kurulduktan sonra ilgili repair ve gate scriptlerini çalıştırın.
2. Gate sonucu OK olmadan canlı servisi yeniden başlatmayın.
3. Python compileall ile değişen dosyaların sözdizimini kontrol edin.
4. Canlı görev adı kullanılıyorsa Scheduled Task üzerinden durdur/başlat yapılmalıdır.
5. Yeniden başlatma sonrası ana sayfa, asistan paneli, rol matrisi ve kritik performans ekranları kontrol edilmelidir.
6. Kullanıcıya görünen ekranda teknik traceback veya beyaz sayfa kalmamalıdır.

Bu konu teknik/operasyon yetkisi gerektirir.

Yetki notu: {{ROLE_NOTE}}
        """,
        actions=(("Ana Sayfa", "/home", "Canlı ana sayfa kontrolü"), ("BYS360 Asistanı Paneli", "/ai-agent/panel", "Asistan panel kontrolü")),
        allowed_roles=("admin", "hr_performance", "all"),
    ),
)


def _score_topic(topic: GuideTopic, text: str) -> int:
    score = 0
    for keyword in topic.keywords:
        k = _norm(keyword)
        if not k:
            continue
        if k == text:
            score += 10
        elif k in text:
            score += 4 + min(len(k) // 6, 4)
    return score


def find_bys360_guide_topic(question: str) -> GuideTopic | None:
    text = _norm(question)
    if not text:
        return None
    best: tuple[int, GuideTopic] | None = None
    for topic in TOPICS:
        score = _score_topic(topic, text)
        if score <= 0:
            continue
        if best is None or score > best[0]:
            best = (score, topic)
    if best and best[0] >= 4:
        return best[1]
    return None


def build_bys360_assistant_knowledge_reply(user: Any, question: str) -> dict[str, Any] | None:
    """BYS360 Asistanı için rol bazlı, sabit ve güvenli kullanım rehberi üretir."""
    topic = find_bys360_guide_topic(question or "")
    if not topic:
        return None
    return _reply(topic, user, question or "")


def get_bys360_assistant_knowledge_index() -> list[dict[str, Any]]:
    """Bilgi bankası indeksini UI veya testlerde kullanılabilecek güvenli sözlük listesi olarak döndürür."""
    return [
        {
            "key": topic.key,
            "title": topic.title,
            "keywords": list(topic.keywords),
            "actions": [
                {"label": label, "route": route, "description": desc}
                for label, route, desc in topic.actions
            ],
            "allowed_roles": list(topic.allowed_roles),
        }
        for topic in TOPICS
    ]


__all__ = [
    "VERSION",
    "MODE",
    "NOTICE",
    "build_bys360_assistant_knowledge_reply",
    "find_bys360_guide_topic",
    "get_bys360_assistant_knowledge_index",
]
