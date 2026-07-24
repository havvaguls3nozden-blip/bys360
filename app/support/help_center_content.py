from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from sqlalchemy import inspect

    from app.extensions import db
    from app.models import SupportHelpArticle
except Exception:  # pragma: no cover - application context not always ready during import checks
    logger.exception("BYS360 V6C guarded exception | file=app/support/help_center_content.py | line=12")
    inspect = None  # type: ignore[assignment]
    db = None  # type: ignore[assignment]
    SupportHelpArticle = None  # type: ignore[assignment,misc]


HELP_CATEGORIES = [
    {
        "slug": "baslarken",
        "title": "Başlarken",
        "icon": "fa-solid fa-door-open",
        "description": "İlk giriş, ekran düzeni, güvenli kullanım ve günlük takip alışkanlığı.",
        "learning_goal": "Kullanıcı sisteme güvenle girsin, ana menüyü tanısın ve ilk işlemlerini destek almadan yapabilsin.",
    },
    {
        "slug": "personel-organizasyon",
        "title": "Personel ve Organizasyon",
        "icon": "fa-solid fa-sitemap",
        "description": "Personel kayıtları, birim ilişkileri, üst birim yapısı ve sicil bazlı veri düzeni.",
        "learning_goal": "Personel bilgilerinin doğru tutulması ve hiyerarşinin hatasız okunması.",
    },
    {
        "slug": "performans",
        "title": "Performans Yönetimi",
        "icon": "fa-solid fa-chart-line",
        "description": "Dönem, kriter, görev üretimi, değerlendirme, karne, yayın ve geri bildirim akışı.",
        "learning_goal": "Performans sürecinin baştan sona kontrollü, şeffaf ve hatasız yürütülmesi.",
    },
    {
        "slug": "izin-vekalet",
        "title": "İzin ve Vekâlet",
        "icon": "fa-solid fa-user-clock",
        "description": "İzin talepleri, devamsızlık kayıtları, vekâlet devri ve görev sürekliliği.",
        "learning_goal": "Yokluk durumlarında iş akışının durmadan devam etmesi.",
    },
    {
        "slug": "iletisim-anket-geri-bildirim",
        "title": "İletişim, Anket ve Geri Bildirim",
        "icon": "fa-solid fa-comments",
        "description": "Mesajlar, duyurular, anketler, nabız ölçümü, geri bildirim talepleri ve yönetici görünürlüğü.",
        "learning_goal": "Kurumsal iletişimin kayıtlı, izlenebilir ve doğru kanaldan yapılması.",
    },
    {
        "slug": "raporlama-dashboard",
        "title": "Raporlama ve Dashboard",
        "icon": "fa-solid fa-chart-pie",
        "description": "Dashboard, personel raporları, performans raporları, filtreleme, dışa aktarma ve analiz ekranları.",
        "learning_goal": "Yöneticinin doğru veriyi doğru ekranda okuyup karar desteği olarak kullanması.",
    },
    {
        "slug": "ai-karar-destek",
        "title": "AI Karar Destek Katmanı",
        "icon": "fa-solid fa-wand-magic-sparkles",
        "description": "AI özetleri, risk sinyalleri, öneriler, nabız analizi ve kontrollü karar destek notları.",
        "learning_goal": "AI çıktılarının öneri niteliğinde okunması ve idari karar yerine geçirilmemesi.",
    },
    {
        "slug": "destek-talep",
        "title": "Destek ve Talep Yönetimi",
        "icon": "fa-solid fa-headset",
        "description": "Hata bildirimi, geliştirme talebi, kullanım desteği, önceliklendirme ve takip.",
        "learning_goal": "Sorunların sözlü kalmadan kayıtlı ve takip edilebilir hale gelmesi.",
    },
    {
        "slug": "guvenlik-yetki",
        "title": "Güvenlik, Yetki ve Hesap",
        "icon": "fa-solid fa-shield-halved",
        "description": "CAPTCHA, CSRF, parola, gizli soru, kişi bazlı menü görünürlüğü ve güvenli çıkış.",
        "learning_goal": "Kullanıcının yetki ve güvenlik kaynaklı durumları doğru yorumlaması.",
    },
]

HELP_ROLES = [
    {
        "slug": "personel",
        "title": "Personel",
        "icon": "fa-solid fa-user",
        "description": "Günlük kullanım, izin talebi, bildirim takibi, nabız formu, karne ve geri bildirim talebi.",
    },
    {
        "slug": "yonetici",
        "title": "Yönetici / Amir",
        "icon": "fa-solid fa-user-tie",
        "description": "Değerlendirme, ekip/personel analizi, onay, geri bildirim toplantısı, rapor ve aksiyon takibi.",
    },
    {
        "slug": "ik",
        "title": "Personel Birimi",
        "icon": "fa-solid fa-users-gear",
        "description": "Personel kayıtları, dönem, görev üretimi, sonuç yayını, personel raporları ve veri doğrulama.",
    },
    {
        "slug": "admin",
        "title": "Sistem Yöneticisi",
        "icon": "fa-solid fa-user-shield",
        "description": "Yetki, menü görünürlüğü, sistem ayarları, güvenlik, destek yönetimi ve teknik kontrol.",
    },
]


def _article(slug: str, title: str, summary: str, category_slug: str, role_slugs: list[str], tags: list[str], sections: list[dict[str, Any]], related: list[str] | None = None, featured: bool = False, troubleshooting: bool = False) -> dict[str, Any]:
    return {
        "slug": slug,
        "title": title,
        "summary": summary,
        "category_slug": category_slug,
        "role_slugs": role_slugs,
        "tags": tags,
        "sections": sections,
        "related": related or [],
        "is_featured": featured,
        "is_troubleshooting": troubleshooting,
    }


HELP_ARTICLES = [
    _article(
        "sisteme-ilk-giris-ve-gunluk-kontrol",
        "Sisteme ilk giriş ve günlük kontrol akışı",
        "İlk girişten sonra kullanıcının her gün kontrol etmesi gereken alanları anlatır.",
        "baslarken",
        ["personel", "yonetici", "ik", "admin"],
        ["ilk giriş", "dashboard", "profil", "bildirim"],
        [
            {"title": "Amaç", "body": "Bu rehber, BYS360’a giren kullanıcının ilk bakışta nereden başlayacağını, hangi bildirimleri kontrol edeceğini ve güvenli oturum alışkanlığını nasıl kuracağını açıklar."},
            {"title": "Adım adım", "bullet_items": ["Kurumsal kullanıcı bilgilerinizle oturum açın.", "Ana dashboard üzerinde bekleyen görev, bildirim ve duyuruları kontrol edin.", "Profil fotoğrafı, iletişim bilgisi ve gizli soru alanını tamamlayın.", "Size açılmış menülerin görevinizle uyumlu olup olmadığını kontrol edin.", "İşiniz bittiğinde Güvenli Çıkış bağlantısını kullanın."]},
            {"title": "Dikkat", "bullet_items": ["Ortak bilgisayarda oturum açık bırakılmamalıdır.", "Tarayıcıda eski sayfa açık kaldıysa işlem yapmadan önce sayfa yenilenmelidir.", "Menüde görmediğiniz ekranlar her zaman hata değildir; kişi bazlı görünürlük uygulanabilir."]},
        ],
        ["menude-bazi-alanlari-goremiyorum", "sifre-gizli-soru-ve-guvenli-cikis"],
        featured=True,
    ),
    _article(
        "modul-kartlari-ve-ekran-dili-nasil-okunur",
        "Modül kartları ve ekran dili nasıl okunur?",
        "Kart, rozet, durum etiketi, filtre ve tablo alanlarının ortak kullanım mantığını açıklar.",
        "baslarken",
        ["personel", "yonetici", "ik", "admin"],
        ["ekran", "kart", "filtre", "durum"],
        [
            {"title": "Ortak ekran mantığı", "body": "BYS360 ekranlarında üst özet kartları genel durumu, filtreler daraltılmış listeyi, tablolar ise işlem yapılacak kayıtları gösterir."},
            {"title": "Okuma sırası", "bullet_items": ["Önce üstteki dönem veya tarih bilgisini kontrol edin.", "Sonra özet kartlarını okuyun.", "Filtre varsa birim, dönem, durum veya kişi filtresini uygulayın.", "Tablodaki işlem butonlarını yalnızca ilgili kayıt için kullanın."]},
            {"title": "Yanlış yorumlamayı önleme", "bullet_items": ["Boş grafik her zaman hata anlamına gelmez; seçili dönemde veri olmayabilir.", "Pasif veya yayınlanmamış kayıtlar her kullanıcıya görünmeyebilir.", "Sayfa yenilemeden önce formu iki kez göndermeyin."]},
        ],
        ["rapor-filtreleri-nasil-kullanilir"],
    ),
    _article(
        "personel-kaydi-ve-zorunlu-alanlar",
        "Personel kaydı ve zorunlu alanlar",
        "Yeni personel eklerken sicil no, unvan, birim, üst birim ve yönetici bilgilerinin neden zorunlu olduğunu anlatır.",
        "personel-organizasyon",
        ["ik", "admin"],
        ["personel", "sicil no", "unvan", "birim", "üst birim"],
        [
            {"title": "Neden önemlidir?", "body": "Personel kaydı yalnızca isim listesi değildir. Performans, izin, vekâlet, bildirim ve raporlama ekranları bu kayıttan beslenir."},
            {"title": "Zorunlu alanlar", "bullet_items": ["Sicil No: Kullanıcının benzersiz kurum kimliğidir.", "Unvan: Yetki ve raporlama ayrımında kullanılır.", "Birim: Günlük görev ve bağlı çalışma grubu bilgisidir.", "Üst Birim: Grup başkanlığı veya üst organizasyon ilişkisidir.", "Yönetici bilgisi: Onay, değerlendirme ve vekâlet akışının temelidir."]},
            {"title": "Kontrol listesi", "bullet_items": ["Aynı sicil numarası ikinci kez girilmemeli.", "Aynı adlı fakat farklı üst birime bağlı birimler karıştırılmamalı.", "Pasif personel yanlışlıkla aktif görev zincirine dahil edilmemeli."]},
        ],
        ["personel-excel-aktarimi", "amir-zinciri-dogrulama"],
        featured=True,
    ),
    _article(
        "personel-excel-aktarimi",
        "Personel Excel aktarımı nasıl yapılır?",
        "Toplu personel aktarımında şablon, ön kontrol ve hata düzeltme mantığını öğretir.",
        "personel-organizasyon",
        ["ik", "admin"],
        ["excel", "toplu aktarım", "sicil no", "hata kontrol"],
        [
            {"title": "İşlem öncesi hazırlık", "bullet_items": ["Şablondaki sütun adlarını değiştirmeyin.", "Sicil no, ad soyad, unvan, birim, üst birim ve yönetici bilgilerini eksiksiz doldurun.", "Boş satır, birleştirilmiş hücre ve farklı tarih formatlarından kaçının."]},
            {"title": "Aktarım akışı", "bullet_items": ["Personel Yönetimi içinde toplu aktarım ekranını açın.", "Excel dosyasını seçin ve ön kontrol sonucunu bekleyin.", "Sistem uyarı verirse dosyayı düzeltip yeniden yükleyin.", "Aktarım sonrası personel listesi ve organizasyon görünümünü kontrol edin."]},
            {"title": "Sık hata nedenleri", "bullet_items": ["Sicil no alanının boş olması.", "Üst birim adının farklı yazılması.", "Yönetici sicil bilgisinin kullanıcı listesinde bulunmaması.", "Aynı kişinin iki satırda yer alması."]},
        ],
        ["amir-zinciri-dogrulama", "gorevler-bana-dusmedi"],
    ),
    _article(
        "amir-zinciri-dogrulama",
        "Amir zinciri nasıl doğrulanır?",
        "Koordinatör, grup başkanı, başkan yardımcısı ve özel istisna zincirlerinin nasıl kontrol edileceğini açıklar.",
        "personel-organizasyon",
        ["yonetici", "ik", "admin"],
        ["amir", "hiyerarşi", "koordinatör", "grup başkanı"],
        [
            {"title": "Temel mantık", "body": "Amir zinciri; performans görevlerinin, izin onaylarının ve raporlardaki yönetici görünürlüğünün temelidir."},
            {"title": "Kontrol edilecekler", "bullet_items": ["Çalışma grubu personelinde 1. amir Koordinatör, 2. amir Grup Başkanı olmalıdır.", "Koordinatör için 1. amir Grup Başkanı, 2. amir Başkan Yardımcısı olmalıdır.", "Tek amirli özel durumlarda gereksiz 2. amir bekliyor durumu oluşmamalıdır.", "3. amir varsa rolü yorum modu veya puan modu olarak doğru tanımlanmalıdır."]},
            {"title": "Uyarı gördüğünüzde", "bullet_items": ["Uyarıdaki sicil numarasını personel listesinde arayın.", "Birim/üst birim bilgisinin doğru yazıldığını kontrol edin.", "Zinciri düzeltmeden görev üretimi yapmayın."]},
        ],
        ["degerlendirme-gorevleri-nasil-uretilir", "gorevler-bana-dusmedi"],
        featured=True,
    ),
    _article(
        "performans-donemi-nasil-acilir",
        "Performans dönemi nasıl açılır?",
        "Dönem tanımı, aktif dönem, tarih aralığı ve yayın öncesi hazırlık adımlarını açıklar.",
        "performans",
        ["ik", "admin"],
        ["dönem", "aktif dönem", "performans"],
        [
            {"title": "İşlem öncesi", "bullet_items": ["Değerlendirme kriterleri hazır mı kontrol edin.", "Amir ağırlıkları ve 3. amir modu doğru mu kontrol edin.", "Personel ve amir zinciri doğrulamasını çalıştırın.", "Önceki dönemle çakışan aktif dönem olup olmadığını kontrol edin."]},
            {"title": "Adım adım", "bullet_items": ["Dönemler ekranına girin.", "Dönem adını, başlangıç ve bitiş tarihini tanımlayın.", "Dönem türünü seçin.", "Gerekli kontroller tamamlandıktan sonra dönemi aktif hale getirin."]},
            {"title": "Yayın mantığı", "body": "Dönem açılması sonuçların personele görüneceği anlamına gelmez. Sonuç görünürlüğü ayrı yayın/onay adımıyla yönetilir."},
        ],
        ["degerlendirme-kriterleri-nasil-tanimlanir", "degerlendirme-gorevleri-nasil-uretilir"],
        featured=True,
    ),
    _article(
        "degerlendirme-kriterleri-nasil-tanimlanir",
        "Değerlendirme kriterleri nasıl tanımlanır?",
        "Kriter başlığı, 1-5 puan dili, açıklama zorunluluğu ve toplam ağırlık kontrolünü öğretir.",
        "performans",
        ["ik", "admin"],
        ["kriter", "puan", "açıklama", "ağırlık"],
        [
            {"title": "Kriter yazım ilkesi", "bullet_items": ["Kriter başlığı kısa ve açık olmalıdır.", "Ölçülebilir davranış veya iş çıktısına bağlanmalıdır.", "Aynı anlamı taşıyan iki kriter tekrar edilmemelidir.", "Görünen metinlerde 'yetkinlik' yerine 'Değerlendirme Kriterleri' dili kullanılmalıdır."]},
            {"title": "Puanlama kuralı", "bullet_items": ["1 ve 5 puanlarda açıklama istenmelidir.", "70 altı ve 90 üstü sonuçlarda genel görüş ayrıntılı yazılmalıdır.", "Kriter ağırlıkları toplamı kontrol edilmelidir."]},
        ],
        ["performans-donemi-nasil-acilir", "degerlendirme-formu-nasil-doldurulur"],
    ),
    _article(
        "degerlendirme-gorevleri-nasil-uretilir",
        "Değerlendirme görevleri nasıl üretilir?",
        "Aktif dönem ve amir zincirinden görev üretme adımlarını anlatır.",
        "performans",
        ["ik", "admin"],
        ["görev üretimi", "atama", "aktif dönem"],
        [
            {"title": "Görev üretmeden önce", "bullet_items": ["Aktif dönem seçili olmalıdır.", "Personel listesi güncel olmalıdır.", "Amir zinciri uyarıları kapatılmış olmalıdır.", "Daha önce aynı dönem için görev üretilip üretilmediği kontrol edilmelidir."]},
            {"title": "Üretim sonrası kontrol", "bullet_items": ["Oluşturulan, atlanan ve mükerrer görev sayılarını inceleyin.", "Tek amirli kayıtlarda gereksiz 2. amir görevi oluşmadığını kontrol edin.", "3. amir yorum modundaysa puan görevi değil görüş görevi beklenmelidir."]},
        ],
        ["amir-zinciri-dogrulama", "gorevler-bana-dusmedi"],
    ),
    _article(
        "degerlendirme-formu-nasil-doldurulur",
        "Değerlendirme formu nasıl doldurulur?",
        "Amirlerin puan, açıklama ve genel görüş girişini doğru yapması için uygulamalı rehber.",
        "performans",
        ["yonetici"],
        ["değerlendirme", "puan", "yorum", "genel görüş"],
        [
            {"title": "Formu açmadan önce", "bullet_items": ["Görevlerim ekranında doğru dönem ve doğru personel seçili mi kontrol edin.", "Önceki amir görüşü görünüyorsa okuyun.", "Kriterleri hızlı geçmeden personelin dönem içi iş çıktısını dikkate alın."]},
            {"title": "Puanlama adımları", "bullet_items": ["Her kriter için 1-5 arası puan seçin.", "1 veya 5 verdiyseniz gerekçeyi yazın.", "Ortalama 70 altı veya 90 üstü olacaksa genel görüş alanını ayrıntılı doldurun.", "Kaydetmeden önce toplam ve eksik alan uyarılarını kontrol edin."]},
            {"title": "Şeffaf değerlendirme", "body": "Sistem kör değerlendirme mantığıyla çalışmaz. Sonraki amir, önceki amirin puanını ve kanaatini görerek nihai değerlendirme kalitesini artırır."},
        ],
        ["not-karnesi-ne-zaman-gorunur", "geri-bildirim-toplantisi-nasil-talep-edilir"],
        featured=True,
    ),
    _article(
        "personel-donem-analizi-nasil-okunur",
        "Personel Dönem Analizi nasıl okunur?",
        "Dönemler arası değişim, puan hareketi ve kişi bazlı analiz ekranının yorumlanmasını anlatır.",
        "performans",
        ["yonetici", "ik", "admin"],
        ["personel dönem analizi", "dönem", "karşılaştırma"],
        [
            {"title": "Bu ekran neyi gösterir?", "body": "Personelin dönemler arasındaki performans hareketini, artış/azalış yönünü ve dikkat gerektiren puan aralıklarını gösterir."},
            {"title": "Okuma sırası", "bullet_items": ["Önce seçili dönemleri kontrol edin.", "Puan değişim yönünü okuyun.", "70 altı veya 90 üstü sonuçları ayrıca inceleyin.", "Açıklama ve görüş alanlarıyla sayısal veriyi birlikte değerlendirin."]},
        ],
        ["rapor-filtreleri-nasil-kullanilir", "yonetici-ozetleri-nasil-okunur"],
    ),
    _article(
        "not-karnesi-ne-zaman-gorunur",
        "Not karnesi ne zaman görünür?",
        "Sonuçların personele ne zaman açılacağını ve yayın/onay mantığını açıklar.",
        "performans",
        ["personel", "yonetici", "ik", "admin"],
        ["karne", "yayın", "sonuç"],
        [
            {"title": "Temel kural", "body": "Değerlendirme sonuçları, yetkili yayın/onay işlemi yapılmadan personele açılmaz."},
            {"title": "Karne görünmüyorsa", "bullet_items": ["Dönem tamamlanmamış olabilir.", "İK/yetkili yayın işlemi henüz yapılmamış olabilir.", "Kişi bazlı görünürlük kapalı olabilir.", "Tarayıcı eski sayfayı gösteriyor olabilir; Ctrl+F5 ile yenileyin."]},
        ],
        ["geri-bildirim-toplantisi-nasil-talep-edilir"],
    ),
    _article(
        "geri-bildirim-toplantisi-nasil-talep-edilir",
        "Geri bildirim toplantısı nasıl talep edilir?",
        "Karne sonrası personel ve amir arasındaki görüşme talebi, randevu ve aksiyon mantığını açıklar.",
        "performans",
        ["personel", "yonetici"],
        ["geri bildirim", "toplantı", "randevu"],
        [
            {"title": "Personel için", "bullet_items": ["Karne ekranından geri bildirim talebini açın.", "Talep nedeninizi kısa ve net yazın.", "Bildirim veya toplantı ekranından yanıtı takip edin."]},
            {"title": "Yönetici için", "bullet_items": ["Talebi okuyun ve uygun toplantı zamanını belirleyin.", "Çakışan randevu var mı kontrol edin.", "Toplantı sonrası aksiyon planı gerekiyorsa kayıt altına alın."]},
        ],
        ["not-karnesi-ne-zaman-gorunur"],
    ),
    _article(
        "izin-talebi-nasil-olusturulur",
        "İzin talebi nasıl oluşturulur?",
        "İzin türü, tarih seçimi, açıklama ve onaya gönderme adımlarını öğretir.",
        "izin-vekalet",
        ["personel"],
        ["izin", "talep", "bakiye", "onay"],
        [
            {"title": "Adım adım", "bullet_items": ["İzin ekranında Yeni Talep seçeneğini açın.", "İzin türünü ve tarih aralığını seçin.", "Gerekli açıklamayı yazın.", "Çakışan kayıt veya bakiye uyarısı varsa düzeltin.", "Talebi gönderin ve durumunu takip edin."]},
            {"title": "Göndermeden önce", "bullet_items": ["Tarih aralığı doğru mu?", "İzin türü doğru mu?", "Vekil tanımı gerekiyorsa yapıldı mı?", "Ek belge gerekiyorsa eklendi mi?"]},
        ],
        ["vekil-nasil-tanimlanir", "izinli-amirin-gorevi-ne-olur"],
        featured=True,
    ),
    _article(
        "vekil-nasil-tanimlanir",
        "Vekil nasıl tanımlanır?",
        "İzinli veya görevde olmayan kullanıcı için vekâlet devri oluşturmayı açıklar.",
        "izin-vekalet",
        ["personel", "yonetici", "ik", "admin"],
        ["vekil", "vekâlet", "devir"],
        [
            {"title": "Ne zaman kullanılır?", "body": "Yöneticinin izinli olduğu veya işlem yapamayacağı dönemlerde onay ve değerlendirme görevlerinin boşa düşmemesi için kullanılır."},
            {"title": "Adım adım", "bullet_items": ["Vekâlet ekranını açın.", "Asıl kullanıcı ve vekil olacak kişiyi seçin.", "Başlangıç ve bitiş tarihini belirleyin.", "Devir kapsamını kontrol edin.", "Kaydı oluşturduktan sonra ilgili görev ekranında test edin."]},
        ],
        ["izinli-amirin-gorevi-ne-olur"],
    ),
    _article(
        "izinli-amirin-gorevi-ne-olur",
        "İzinli amirin görevi ne olur?",
        "Amirin izinli olduğu durumda görev devri ve süreç sürekliliğini anlatır.",
        "izin-vekalet",
        ["yonetici", "ik", "admin"],
        ["izinli amir", "görev devri", "vekâlet"],
        [
            {"title": "Temel ilke", "body": "İzinli amirin görevi boşa düşmez. Aynı seviyede tanımlı geçerli vekil varsa görev o kişiye yönlendirilir."},
            {"title": "Kontrol listesi", "bullet_items": ["Vekâlet tarihleri izin tarihleriyle uyumlu mu?", "Vekil aktif kullanıcı mı?", "Vekilin ilgili menü ve işlem yetkisi var mı?", "Görev geçmişinde devir izi oluşuyor mu?"]},
        ],
        ["vekil-nasil-tanimlanir", "degerlendirme-gorevleri-nasil-uretilir"],
    ),
    _article(
        "mesajlar-duyurular-ve-bildirimler",
        "Mesajlar, duyurular ve bildirimler nasıl takip edilir?",
        "Kurumsal iletişim akışının hangi ekranda nasıl takip edileceğini açıklar.",
        "iletisim-anket-geri-bildirim",
        ["personel", "yonetici", "ik", "admin"],
        ["mesaj", "duyuru", "bildirim"],
        [
            {"title": "Günlük takip", "bullet_items": ["Üst bildirim simgesini kontrol edin.", "Mesajlar ekranında okunmamış konuşmaları açın.", "Duyurularda tarih ve hedef kitle bilgisini okuyun.", "Aksiyon gerektiren bildirimleri ertelemeyin."]},
            {"title": "Kurumsal kullanım", "body": "Mesaj ve duyurular sözlü bilgi akışını kayıtlı hale getirir. Önemli işlem, tarih veya karar bilgileri mümkün olduğunca sistem üzerinden paylaşılmalıdır."},
        ],
        ["anket-nasil-yanitlanir", "destek-talebi-nasil-acilir"],
    ),
    _article(
        "anket-nasil-yanitlanir",
        "Anket nasıl yanıtlanır?",
        "Atanmış anketlerde soru türleri, kayıt ve gönderme adımlarını anlatır.",
        "iletisim-anket-geri-bildirim",
        ["personel", "yonetici"],
        ["anket", "soru", "yanıt"],
        [
            {"title": "Adım adım", "bullet_items": ["Anketler veya bildirimlerden ilgili anketi açın.", "Her soruyu dikkatle okuyun.", "Zorunlu soruları boş bırakmayın.", "Yanıtları kaydedip gönderin."]},
            {"title": "Dikkat", "bullet_items": ["Gönderilmiş anketin düzenlenebilirliği ayara bağlıdır.", "Boş veri dashboard analizlerinde yanlış izlenim oluşturabilir.", "Açık uçlu yanıtlar kurumsal dil ile yazılmalıdır."]},
        ],
        ["nabiz-formu-nasil-doldurulur"],
    ),
    _article(
        "nabiz-formu-nasil-doldurulur",
        "Nabız formu nasıl doldurulur?",
        "Kısa geri bildirim/nabız formunun amacı, doğru yanıt dili ve takip mantığını açıklar.",
        "iletisim-anket-geri-bildirim",
        ["personel"],
        ["nabız", "geri bildirim", "pulse"],
        [
            {"title": "Amaç", "body": "Nabız formu, kurumsal atmosferi ve çalışan geri bildirimlerini kısa, düzenli ve analiz edilebilir şekilde toplar."},
            {"title": "Nasıl doldurulur?", "bullet_items": ["Soruyu okuyun ve kendi gözleminize göre yanıtlayın.", "Serbest metin alanına kısa ama somut örnek yazın.", "Kişisel itham yerine süreç, ihtiyaç ve öneri dili kullanın.", "Gönderdikten sonra sonuçların genel analiz ekranlarında değerlendirileceğini bilin."]},
        ],
        ["nabiz-analitigi-nasil-okunur"],
        featured=True,
    ),
    _article(
        "nabiz-analitigi-nasil-okunur",
        "Nabız analitiği nasıl okunur?",
        "Yönetici için nabız skorları, duygu dağılımı, risk sinyali ve aksiyon önerilerini açıklar.",
        "iletisim-anket-geri-bildirim",
        ["yonetici", "ik", "admin"],
        ["nabız analitiği", "risk", "duygu", "aksiyon"],
        [
            {"title": "Okuma sırası", "bullet_items": ["Önce toplam katılım ve tarih aralığını kontrol edin.", "Duygu dağılımını tek başına değil, metin örnekleri ve birim bağlamıyla yorumlayın.", "Risk bayrağı olan başlıkları aksiyon notuna dönüştürün.", "AI önerilerini karar değil, ön değerlendirme olarak kullanın."]},
            {"title": "Yönetici aksiyonu", "bullet_items": ["Tekrarlayan sorun başlığını belirleyin.", "Sorumlu kişi veya birimi seçin.", "Kısa vadeli iyileştirme adımı oluşturun.", "Sonraki nabız döneminde değişimi tekrar izleyin."]},
        ],
        ["ai-ozeti-nasil-yorumlanir", "yonetici-ozetleri-nasil-okunur"],
    ),
    _article(
        "rapor-filtreleri-nasil-kullanilir",
        "Rapor filtreleri nasıl kullanılır?",
        "Dönem, birim, durum ve kişi filtreleriyle doğru rapor alma adımlarını açıklar.",
        "raporlama-dashboard",
        ["yonetici", "ik", "admin"],
        ["rapor", "filtre", "dashboard", "excel"],
        [
            {"title": "Filtreleme mantığı", "body": "Rapor ekranlarında görünen sonuçlar seçili filtrelere göre değişir. Yanlış dönem veya birim seçimi hatalı yorum yapılmasına neden olabilir."},
            {"title": "Adım adım", "bullet_items": ["Önce dönem filtresini seçin.", "Birim veya üst birim filtresini uygulayın.", "Durum filtresini açık, tamamlandı, yayınlandı gibi ihtiyaca göre daraltın.", "Tablo ve grafiklerin aynı filtreye göre güncellendiğini kontrol edin.", "Dışa aktarmadan önce ekrandaki satır sayısını doğrulayın."]},
        ],
        ["yonetici-ozetleri-nasil-okunur", "personel-raporlari-nasil-okunur"],
        featured=True,
    ),
    _article(
        "yonetici-ozetleri-nasil-okunur",
        "Yönetici özetleri nasıl okunur?",
        "Dashboard kartları, analiz notları ve karar destek uyarılarını yorumlamayı öğretir.",
        "raporlama-dashboard",
        ["yonetici", "ik", "admin"],
        ["yönetici özeti", "dashboard", "analiz"],
        [
            {"title": "Okuma sırası", "bullet_items": ["Önce verinin hangi dönemden geldiğini kontrol edin.", "Toplam sayı ve oranları birlikte okuyun.", "Kritik uyarıları tek başına değil, tablo detayıyla doğrulayın.", "AI notu varsa öneri olarak değerlendirin ve insan kontrolüyle karar verin."]},
            {"title": "Yanlış yorumlamayı önleme", "bullet_items": ["Boş veri hata değil, veri oluşmamış dönem olabilir.", "Yüzdeler küçük örneklemde yanıltıcı olabilir.", "Tek bir grafikle idari karar verilmemelidir."]},
        ],
        ["ai-ozeti-nasil-yorumlanir", "rapor-filtreleri-nasil-kullanilir"],
    ),
    _article(
        "personel-raporlari-nasil-okunur",
        "Personel Raporları nasıl okunur?",
        "Personel raporları ekranında aktif personel, birim dağılımı, hareket ve kayıt kalitesini yorumlama rehberi.",
        "raporlama-dashboard",
        ["ik", "admin", "yonetici"],
        ["personel raporları", "birim", "kayıt kalitesi"],
        [
            {"title": "Bu ekranın amacı", "body": "Personel Raporları, kullanıcı ve organizasyon verisinin güncel, tutarlı ve raporlanabilir olup olmadığını takip etmek için kullanılır."},
            {"title": "Kontrol edilecek alanlar", "bullet_items": ["Aktif/pasif kullanıcı sayısı.", "Birim ve üst birim dağılımı.", "Unvan ve sicil no eksikleri.", "Yönetici zinciri tamamlanmamış kayıtlar.", "Son güncelleme ve veri doğrulama durumu."]},
        ],
        ["personel-kaydi-ve-zorunlu-alanlar", "amir-zinciri-dogrulama"],
    ),
    _article(
        "ai-ozeti-nasil-yorumlanir",
        "AI özeti nasıl yorumlanır?",
        "AI karar destek alanlarının öneri niteliğinde nasıl kullanılacağını açıklar.",
        "ai-karar-destek",
        ["yonetici", "ik", "admin"],
        ["AI", "özet", "karar destek", "risk"],
        [
            {"title": "Temel ilke", "body": "AI çıktısı idari karar yerine geçmez. Özet, önceliklendirme, risk sinyali ve öneri üretir; nihai kontrol kullanıcıdadır."},
            {"title": "Nasıl okunur?", "bullet_items": ["Özetin hangi veri aralığından üretildiğini kontrol edin.", "Risk uyarısını tablo ve kaynak kayıtlarla karşılaştırın.", "Aksiyon önerisini doğrudan uygulamadan önce kurum iş kuralına göre değerlendirin.", "Hassas veri içeren çıktıları yetkisiz kişilerle paylaşmayın."]},
            {"title": "Güvenli kullanım", "bullet_items": ["AI metinleri kesin hüküm gibi yazılmamalıdır.", "Kişisel veri içeren serbest metinler gereksiz yere çoğaltılmamalıdır.", "Yönetici onayı gerektiren işlemlerde insan kontrolü korunmalıdır."]},
        ],
        ["yonetici-ozetleri-nasil-okunur", "nabiz-analitigi-nasil-okunur"],
        featured=True,
    ),
    _article(
        "ai-risk-ve-aksiyon-onerileri",
        "AI risk ve aksiyon önerileri nasıl kullanılır?",
        "Risk bayrağı, aksiyon önerisi ve yönetici takip adımlarını öğretir.",
        "ai-karar-destek",
        ["yonetici", "ik", "admin"],
        ["AI", "risk", "aksiyon", "öneri"],
        [
            {"title": "Risk bayrağı ne demektir?", "body": "Sistem, düşük puan, tekrar eden olumsuz geri bildirim, geciken görev veya olağandışı dağılım gibi sinyalleri öne çıkarabilir."},
            {"title": "Aksiyon üretme adımı", "bullet_items": ["Riskin hangi veriyle ilişkili olduğunu kontrol edin.", "Birim, dönem ve kişi bağlamını doğrulayın.", "Sorumlu rolü belirleyin.", "Kısa, ölçülebilir ve tarihli aksiyon notu oluşturun.", "Sonraki raporda aksiyonun etkisini kontrol edin."]},
        ],
        ["ai-ozeti-nasil-yorumlanir", "rapor-filtreleri-nasil-kullanilir"],
    ),
    _article(
        "destek-talebi-nasil-acilir",
        "Destek talebi nasıl açılır?",
        "Hata, kullanım desteği, yetki ve geliştirme taleplerinin nasıl kayıt altına alınacağını anlatır.",
        "destek-talep",
        ["personel", "yonetici", "ik", "admin"],
        ["destek", "talep", "hata", "geliştirme"],
        [
            {"title": "Ne zaman destek talebi açılır?", "bullet_items": ["Sayfa hata veriyorsa.", "Bir işlem beklediğiniz gibi çalışmıyorsa.", "Yetki veya menü görünürlüğü gerekiyorsa.", "Geliştirme öneriniz varsa.", "Kullanım adımını öğrenmeniz gerekiyorsa."]},
            {"title": "İyi talep nasıl yazılır?", "bullet_items": ["Ekran adresini yazın.", "Hangi adımda kaldığınızı belirtin.", "Varsa hata mesajını aynen ekleyin.", "Ekran görüntüsü veya belge ekleyin.", "Acil ise gerekçesini açıkça yazın."]},
            {"title": "Takip", "body": "Talebiniz oluşturulduktan sonra Taleplerim ekranından durumunu, yanıtları ve ek dosyaları takip edebilirsiniz."},
        ],
        ["talep-onceligi-nasil-secilir", "ekran-goruntusu-ve-dosya-ekleme"],
        featured=True,
    ),
    _article(
        "talep-onceligi-nasil-secilir",
        "Talep önceliği nasıl seçilir?",
        "Düşük, normal, yüksek ve kritik önceliklerin ne zaman kullanılacağını açıklar.",
        "destek-talep",
        ["personel", "yonetici", "ik", "admin"],
        ["öncelik", "kritik", "talep"],
        [
            {"title": "Öncelik rehberi", "bullet_items": ["Düşük: Kullanımı engellemeyen küçük öneri veya metin düzeltmesi.", "Normal: Günlük işi etkileyen ama alternatif yolu olan durum.", "Yüksek: Bir modülün önemli işleminde aksama.", "Kritik: Canlı kullanımda işlem yapılamaması, güvenlik veya veri kaybı riski."]},
            {"title": "Dikkat", "body": "Her talebin kritik seçilmesi takip kalitesini düşürür. Öncelik, iş etkisine göre seçilmelidir."},
        ],
        ["destek-talebi-nasil-acilir"],
    ),
    _article(
        "ekran-goruntusu-ve-dosya-ekleme",
        "Ekran görüntüsü ve dosya nasıl eklenir?",
        "Destek talebine kanıt, belge veya ekran görüntüsü ekleme kurallarını açıklar.",
        "destek-talep",
        ["personel", "yonetici", "ik", "admin"],
        ["dosya", "ek", "ekran görüntüsü"],
        [
            {"title": "Ek dosya ne işe yarar?", "body": "Talebin doğru anlaşılmasını sağlar ve hatanın tekrar üretilebilmesini kolaylaştırır."},
            {"title": "Dikkat edilecekler", "bullet_items": ["Gizli veya gereksiz kişisel veri içeren görselleri paylaşmayın.", "Hata mesajı görünür olsun.", "Dosya adı anlaşılır olsun.", "Aynı dosyayı gereksiz yere tekrar yüklemeyin."]},
        ],
        ["destek-talebi-nasil-acilir"],
    ),
    _article(
        "menude-bazi-alanlari-goremiyorum",
        "Menüde bazı alanları neden göremiyorum?",
        "Rol, kişi bazlı menü görünürlüğü ve doğrudan URL erişim mantığını açıklar.",
        "guvenlik-yetki",
        ["personel", "yonetici", "ik", "admin"],
        ["menü", "yetki", "görünürlük"],
        [
            {"title": "Temel mantık", "body": "BYS360’ta her kullanıcı aynı menüyü görmez. Görünürlük; rol, kişi bazlı yetki ve kurum içi görevlere göre ayarlanabilir."},
            {"title": "Kontrol listesi", "bullet_items": ["Doğru kullanıcıyla giriş yaptınız mı?", "Yetki yeni verildiyse oturumu kapatıp açtınız mı?", "Doğrudan URL ile erişilen sayfa yetki istiyor olabilir mi?", "Menü görünürlüğü kişi bazlı kapalı olabilir mi?"]},
        ],
        ["sifre-gizli-soru-ve-guvenli-cikis", "destek-talebi-nasil-acilir"],
        troubleshooting=True,
    ),
    _article(
        "sifre-gizli-soru-ve-guvenli-cikis",
        "Şifre, gizli soru ve güvenli çıkış",
        "Hesap güvenliği için parola, gizli soru ve oturum kapatma alışkanlığını anlatır.",
        "guvenlik-yetki",
        ["personel", "yonetici", "ik", "admin"],
        ["şifre", "gizli soru", "çıkış", "güvenlik"],
        [
            {"title": "Güvenli hesap kullanımı", "bullet_items": ["Şifrenizi başkalarıyla paylaşmayın.", "Gizli soru cevabını kolay tahmin edilecek şekilde seçmeyin.", "Ortak bilgisayarda işi bitirince Güvenli Çıkış yapın.", "Şüpheli durumda şifrenizi yenileyin."]},
            {"title": "İlk girişte", "body": "Sistem parola değişikliği veya gizli soru tanımı isterse bu adımı tamamlamadan bazı işlemleri yapamayabilirsiniz."},
        ],
        ["sisteme-ilk-giris-ve-gunluk-kontrol"],
    ),
    _article(
        "csrf-ve-oturum-hatalari",
        "CSRF ve oturum hatalarında ne yapılır?",
        "Form gönderirken görülen güvenlik doğrulama hatalarının kullanıcı tarafındaki çözüm adımlarını anlatır.",
        "guvenlik-yetki",
        ["personel", "yonetici", "ik", "admin"],
        ["csrf", "oturum", "güvenlik", "hata"],
        [
            {"title": "Neden olur?", "bullet_items": ["Sayfa uzun süre açık kalmış olabilir.", "Oturum yenilenmiş veya çerez geçersizleşmiş olabilir.", "Aynı form birden fazla sekmede açık kalmış olabilir.", "Ağ veya cihaz değişikliği yapılmış olabilir."]},
            {"title": "Çözüm", "bullet_items": ["Sayfayı Ctrl+F5 ile yenileyin.", "Gerekirse çıkış yapıp tekrar giriş yapın.", "Formu tek sekmeden gönderin.", "Sorun devam ederse ekran adresi ve hata mesajıyla destek talebi açın."]},
        ],
        ["destek-talebi-nasil-acilir", "sisteme-ilk-giris-ve-gunluk-kontrol"],
        troubleshooting=True,
    ),
    _article(
        "captcha-neden-acildi",
        "CAPTCHA neden açıldı?",
        "Başarısız giriş denemelerinden sonra görülen güvenlik doğrulama ekranını açıklar.",
        "guvenlik-yetki",
        ["personel", "yonetici", "ik", "admin"],
        ["captcha", "giriş", "güvenlik"],
        [
            {"title": "Neden görünür?", "body": "Kısa sürede tekrarlanan başarısız giriş denemeleri hesap güvenliği için ek doğrulama gerektirebilir."},
            {"title": "Ne yapılmalı?", "bullet_items": ["Kullanıcı adı ve şifrenizi dikkatle kontrol edin.", "CAPTCHA doğrulamasını tamamlayın.", "Şifrenizi hatırlamıyorsanız yetkili destek kanalına başvurun.", "Kendi hesabınız dışında deneme yapmayın."]},
        ],
        ["sifre-gizli-soru-ve-guvenli-cikis"],
        troubleshooting=True,
    ),
    _article(
        "yardim-merkezi-nasil-kullanilir",
        "Yardım Merkezi nasıl kullanılır?",
        "Rehber arama, rol bazlı öğrenme yolu, destek talebi ve takip ekranlarının birlikte nasıl kullanılacağını anlatır.",
        "destek-talep",
        ["personel", "yonetici", "ik", "admin"],
        ["yardım merkezi", "rehber", "arama", "destek", "öğrenme yolu"],
        [
            {"title": "Merkezin amacı", "body": "Yardım Merkezi, kullanıcının doğru bilgiye, doğru ekrana ve doğru destek kanalına hızlı ulaşması için tasarlanmıştır. Önce rehber okunur, konu rehberle çözülmüyorsa kayıtlı destek talebi açılır."},
            {"title": "Önerilen kullanım sırası", "bullet_items": ["Ana sayfadaki arama kutusuna işlem adını, modül adını veya gördüğünüz hata ifadesini yazın.", "Modül Bazlı Rehber Paketleri alanından ilgili modülün rehberlerini açın.", "Rol Bazlı Öğrenme Yolları alanından kendi görevinize uygun başlangıç sırasını takip edin.", "Sorun devam ediyorsa Yeni Talep Aç ekranından kayıt oluşturun.", "Talebinizin yanıtını ve durum geçmişini Taleplerim ekranından izleyin."]},
            {"title": "Dikkat edilmesi gerekenler", "bullet_items": ["Yardım rehberleri idari karar veya onay yerine geçmez; işlem adımlarını açıklar.", "Yetkiniz olmayan ekranları menüde görmemeniz hata olmayabilir.", "Kişisel veya hassas veri içeren ekran görüntülerini gereksiz paylaşmayın."]},
        ],
        ["destek-talebi-nasil-acilir", "talep-durumlari-nasil-takip-edilir", "menude-bazi-alanlari-goremiyorum"],
        featured=True,
    ),
    _article(
        "talep-durumlari-nasil-takip-edilir",
        "Talep durumları nasıl takip edilir?",
        "Açıldı, inceleniyor, bilgi bekleniyor, atandı, planlandı, çözüldü ve kapatıldı durumlarının anlamını açıklar.",
        "destek-talep",
        ["personel", "yonetici", "ik", "admin"],
        ["talep durumu", "durum geçmişi", "çözüm", "takip"],
        [
            {"title": "Durumların anlamı", "bullet_items": ["Açıldı: Talep sisteme kaydedildi ve ilk incelemeyi bekliyor.", "İnceleniyor: Yetkili kişi talebi değerlendiriyor.", "Bilgi Bekleniyor: Talebin ilerlemesi için kullanıcıdan ek açıklama veya dosya bekleniyor.", "Atandı: Talep ilgili sorumlu kullanıcıya yönlendirildi.", "Geliştirme Planına Alındı: Talep bir iyileştirme işi olarak planlandı.", "Çözüldü: Çözüm uygulanmış veya kullanıcıya çözüm yolu bildirilmiştir.", "Kapatıldı: Talep süreci tamamlanmıştır."]},
            {"title": "Nasıl kontrol edilir?", "bullet_items": ["Taleplerim ekranından başvuru numarasını açın.", "Talep özeti bölümünde öncelik, atanan kişi, alt durum ve çözüm özetini okuyun.", "Yorumlar ve işlem notları bölümünde yapılan açıklamaları takip edin.", "Durum geçmişi bölümünde talebin hangi aşamalardan geçtiğini görün."]},
            {"title": "İyi takip alışkanlığı", "body": "Bilgi beklenen taleplerde açıklama eklemek süreci hızlandırır. Aynı konu için tekrar tekrar yeni kayıt açmak yerine mevcut talebe yorum eklemek daha doğru takip sağlar."},
        ],
        ["destek-talebi-nasil-acilir", "talep-onceligi-nasil-secilir"],
        troubleshooting=True,
    ),
    _article(
        "yardim-makalesi-nasil-guncellenir",
        "Yardım makalesi nasıl güncellenir?",
        "Yetkili kullanıcıların Yardım Merkezi içeriğini kurumsal dille nasıl güncelleyeceğini açıklar.",
        "destek-talep",
        ["admin", "ik"],
        ["rehber yönetimi", "makale", "içerik", "kurumsal dil"],
        [
            {"title": "Kim güncelleyebilir?", "body": "Rehber Yönetimi alanı yalnızca yetkili kullanıcılara açıktır. Bu alan, canlı yardım içeriklerinin kod değişmeden güncellenebilmesi için kullanılır."},
            {"title": "Makale yazım ilkeleri", "bullet_items": ["Başlık kısa, açık ve kullanıcı sorusuna cevap veren yapıda olmalıdır.", "Özet alanı makalenin neyi çözdüğünü tek cümlede anlatmalıdır.", "Adım adım bölümünde işlem sırası numarasız karmaşık metin yerine sade maddelerle verilmelidir.", "Notlar bölümünde güvenlik, yetki, gizlilik ve dikkat edilmesi gereken durumlar yer almalıdır.", "Ekranda teknik kod, geliştirici dili veya geçici test ifadesi kullanılmamalıdır."]},
            {"title": "Yayın kontrolü", "bullet_items": ["Makale yayınlanmadan önce doğru kategoriye bağlı mı kontrol edin.", "Rol seçimi doğru yapılmalı; personelin görmemesi gereken yönetici içeriği personel rolüne açılmamalıdır.", "Güncel olmayan içerikler yayından kaldırılmalı veya güncellenmelidir."]},
        ],
        ["yardim-merkezi-nasil-kullanilir", "menude-bazi-alanlari-goremiyorum"],
    ),
    _article(
        "destek-talebinde-guvenli-veri-paylasimi",
        "Destek talebinde güvenli veri paylaşımı",
        "Ekran görüntüsü, belge ve açıklama eklerken kişisel veri ve kurum içi bilginin nasıl korunacağını anlatır.",
        "guvenlik-yetki",
        ["personel", "yonetici", "ik", "admin"],
        ["güvenlik", "kvkk", "dosya", "ekran görüntüsü", "destek"],
        [
            {"title": "Temel ilke", "body": "Destek talebi, sorunu çözmeye yetecek kadar bilgi içermelidir. Gereksiz kişisel veri, özel açıklama veya yetkisiz kişinin görmemesi gereken belge paylaşılmamalıdır."},
            {"title": "Ekran görüntüsü eklerken", "bullet_items": ["Hata mesajı ve ilgili alan görünür olmalıdır.", "Gereksiz kişi listeleri, iletişim bilgileri veya özel açıklamalar kırpılmalıdır.", "Performans puanı, amir görüşü veya hassas personel bilgisi içeren görüntüler yalnızca gerçekten gerekliyse ve yetkili kapsamda paylaşılmalıdır.", "Dosya adı açıklayıcı olmalı; aynı dosya birden fazla kez yüklenmemelidir."]},
            {"title": "Talep gizliliği", "body": "Talep yalnızca yetkili kullanıcılar tarafından görülmesi gerekiyorsa Yeni Talep Aç ekranındaki gizlilik seçeneği kullanılmalıdır."},
        ],
        ["ekran-goruntusu-ve-dosya-ekleme", "csrf-ve-oturum-hatalari"],
        troubleshooting=True,
    ),
    _article(
        "destek-talebinden-ogrenme-icerigi-uretme",
        "Destek talebinden öğrenme içeriği üretme",
        "Tekrar eden destek taleplerinin yeni yardım rehberlerine nasıl dönüştürüleceğini açıklar.",
        "destek-talep",
        ["admin", "ik", "yonetici"],
        ["talep analizi", "öğrenme", "rehber", "iyileştirme"],
        [
            {"title": "Ne zaman makaleye dönüşür?", "bullet_items": ["Aynı konuda çok sayıda destek talebi oluşuyorsa.", "Kullanıcılar bir işlem adımında sık takılıyorsa.", "Yeni eklenen bir ekran için açıklama ihtiyacı doğuyorsa.", "Yetki, görünürlük veya güvenlik uyarısı yanlış yorumlanıyorsa."]},
            {"title": "Dönüştürme adımları", "bullet_items": ["Talep başlıklarını ve açıklamalarını inceleyin.", "Kullanıcıların ortak sorusunu tek cümleye indirin.", "Çözüm adımlarını kısa ve uygulanabilir maddeler halinde yazın.", "Gerekirse ilgili modül rehberiyle bağlantı kurun.", "Makale yayınlandıktan sonra yeni taleplerde kullanıcıyı ilgili rehbere yönlendirin."]},
            {"title": "Kurumsal fayda", "body": "Bu yöntem destek yükünü azaltır, aynı hatanın tekrar sorulmasını engeller ve BYS360’ın kurumsal hafızasını güçlendirir."},
        ],
        ["yardim-makalesi-nasil-guncellenir", "talep-durumlari-nasil-takip-edilir"],
    ),

]

FEATURED_PRIORITY_SLUGS = [
    "yardim-merkezi-nasil-kullanilir",
    "destek-talebi-nasil-acilir",
    "talep-durumlari-nasil-takip-edilir",
    "destek-talebinde-guvenli-veri-paylasimi",
    "sisteme-ilk-giris-ve-gunluk-kontrol",
    "performans-donemi-nasil-acilir",
    "not-karnesi-ne-zaman-gorunur",
    "menude-bazi-alanlari-goremiyorum",
]
FEATURED_ARTICLE_SLUGS = list(dict.fromkeys(FEATURED_PRIORITY_SLUGS + [article["slug"] for article in HELP_ARTICLES if article.get("is_featured")]))
TROUBLESHOOTING_SLUGS = [article["slug"] for article in HELP_ARTICLES if article.get("is_troubleshooting")]
POPULAR_ARTICLE_SLUGS = [
    "yardim-merkezi-nasil-kullanilir",
    "destek-talebi-nasil-acilir",
    "talep-durumlari-nasil-takip-edilir",
    "destek-talebinde-guvenli-veri-paylasimi",
    "performans-donemi-nasil-acilir",
    "rapor-filtreleri-nasil-kullanilir",
    "menude-bazi-alanlari-goremiyorum",
]

SEARCH_ALIASES = {
    "ik": ["personel", "personel raporları", "insan kaynakları"],
    "hr": ["personel", "personel raporları"],
    "dashboard": ["rapor", "özet", "analiz", "grafik"],
    "analiz": ["rapor", "dashboard", "personel dönem analizi", "nabız analitiği"],
    "ai": ["yapay zeka", "karar destek", "özet", "risk", "aksiyon"],
    "nabız": ["pulse", "geri bildirim", "duygu", "risk"],
    "pulse": ["nabız", "geri bildirim"],
    "vekalet": ["vekâlet", "vekil", "izinli amir"],
    "menu": ["menü", "yetki", "görünürlük"],
    "csrf": ["oturum", "güvenlik doğrulaması"],
    "yardım": ["rehber", "destek", "talep", "makale"],
    "yardim": ["rehber", "destek", "talep", "makale"],
    "talep": ["destek", "başvuru", "durum", "çözüm"],
    "kvkk": ["güvenli veri", "kişisel veri", "dosya", "ekran görüntüsü"],
}

CATEGORY_MAP = {item["slug"]: item for item in HELP_CATEGORIES}
ROLE_MAP = {item["slug"]: item for item in HELP_ROLES}
ARTICLE_MAP = {item["slug"]: item for item in HELP_ARTICLES}


def _help_tables_ready() -> bool:
    if not db or not inspect or not SupportHelpArticle:  # type: ignore[truthy-function]
        return False
    try:
        existing = set(inspect(db.engine).get_table_names())
        return "support_help_articles" in existing
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/support/help_center_content.py)")
        return False


def _as_text(value: Any) -> str:
    return str(value or "").strip()


def _split_lines(raw: str | None) -> list[str]:
    return [line.strip(" -•\t") for line in (raw or "").splitlines() if line.strip(" -•\t")]


def _normalize_static_article(article: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(article)
    normalized.setdefault("sections", [])
    normalized.setdefault("tags", [])
    normalized.setdefault("role_slugs", [])
    normalized.setdefault("related", [])
    normalized["source_type"] = "static"
    return normalized


def _normalize_db_article(article: Any) -> dict[str, Any]:
    role_slugs: list[Any] = []
    tags: list[Any] = []
    related: list[Any] = []
    for attr, target in (("get_role_slugs", role_slugs), ("get_tags", tags), ("get_related_slugs", related)):
        try:
            target.extend(getattr(article, attr)() or [])
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/support/help_center_content.py)")
    sections: list[dict[str, Any]] = []
    content_text = _as_text(getattr(article, "content_text", ""))
    steps = _split_lines(getattr(article, "steps_text", ""))
    notes = _split_lines(getattr(article, "notes_text", ""))
    if content_text:
        sections.append({"title": "Açıklama", "body": content_text})
    if steps:
        sections.append({"title": "Adım adım", "bullet_items": steps})
    if notes:
        sections.append({"title": "Notlar", "bullet_items": notes})
    return {
        "slug": _as_text(getattr(article, "slug", "")),
        "title": _as_text(getattr(article, "title", "")),
        "summary": _as_text(getattr(article, "summary", "")),
        "category_slug": _as_text(getattr(article, "category_slug", "baslarken")) or "baslarken",
        "role_slugs": role_slugs,
        "tags": tags,
        "related": related,
        "sections": sections,
        "source_type": "database",
        "is_featured": bool(getattr(article, "is_featured", False)),
    }


def _flatten_static_article(article: dict[str, Any]) -> dict[str, Any]:
    article = _normalize_static_article(article)
    content_blocks: list[str] = []
    step_lines: list[str] = []
    note_lines: list[str] = []
    for section in article.get("sections", []):
        title = _as_text(section.get("title"))
        body = _as_text(section.get("body"))
        items = section.get("bullet_items") or []
        if body:
            content_blocks.append(f"{title}\n{body}" if title else body)
        if items:
            target = note_lines if any(key in title.lower() for key in ["dikkat", "not", "uyarı"]) else step_lines
            if title:
                target.append(title)
            target.extend([_as_text(item) for item in items if _as_text(item)])
    return {
        "slug": article["slug"],
        "title": article["title"],
        "summary": article["summary"],
        "category_slug": article["category_slug"],
        "role_slugs": article.get("role_slugs", []),
        "tags": article.get("tags", []),
        "related_slugs": article.get("related", []),
        "content_text": "\n\n".join(content_blocks),
        "steps_text": "\n".join(step_lines),
        "notes_text": "\n".join(note_lines),
    }


def default_help_articles_payload() -> list[dict[str, Any]]:
    return [_flatten_static_article(article) for article in HELP_ARTICLES]


def _db_article_query(published_only: bool = True):
    if not _help_tables_ready():
        return None
    query = SupportHelpArticle.query
    if published_only and hasattr(SupportHelpArticle, "is_published"):
        query = query.filter(SupportHelpArticle.is_published.is_(True))
    return query.order_by(SupportHelpArticle.sort_order.asc(), SupportHelpArticle.title.asc())


def get_db_articles(published_only: bool = True) -> list[dict[str, Any]]:
    query = _db_article_query(published_only=published_only)
    if query is None:
        return []
    try:
        return [_normalize_db_article(row) for row in query.all()]
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/support/help_center_content.py)")
        return []


def get_all_articles(published_only: bool = True) -> list[dict[str, Any]]:
    merged = {article["slug"]: _normalize_static_article(article) for article in HELP_ARTICLES}
    for article in get_db_articles(published_only=published_only):
        if article.get("category_slug") in CATEGORY_MAP:
            merged[article["slug"]] = article
    return list(merged.values())


def _ordered_by_slugs(slugs: list[str]) -> list[dict[str, Any]]:
    articles = {article["slug"]: article for article in get_all_articles()}
    return [articles[slug] for slug in slugs if slug in articles]


def get_featured_articles() -> list[dict[str, Any]]:
    priority = _ordered_by_slugs(FEATURED_ARTICLE_SLUGS)
    seen = {a["slug"] for a in priority}
    priority.extend([article for article in get_all_articles() if article.get("is_featured") and article["slug"] not in seen])
    return priority[:8]


def get_troubleshooting_articles() -> list[dict[str, Any]]:
    articles = [article for article in get_all_articles() if article.get("is_troubleshooting")]
    seen = {a["slug"] for a in articles}
    articles.extend([a for a in _ordered_by_slugs(TROUBLESHOOTING_SLUGS) if a["slug"] not in seen])
    return articles[:8]


def get_popular_articles() -> list[dict[str, Any]]:
    popular = _ordered_by_slugs(POPULAR_ARTICLE_SLUGS)
    if popular:
        return popular
    return get_all_articles()[:6]


def get_articles_for_category(category_slug: str) -> list[dict[str, Any]]:
    return [article for article in get_all_articles() if article.get("category_slug") == category_slug]


def get_articles_for_role(role_slug: str) -> list[dict[str, Any]]:
    return [article for article in get_all_articles() if role_slug in (article.get("role_slugs") or [])]


def get_related_articles(article: dict[str, Any]) -> list[dict[str, Any]]:
    related_slugs = article.get("related") or article.get("related_slugs") or []
    all_map = {item["slug"]: item for item in get_all_articles()}
    return [all_map[slug] for slug in related_slugs if slug in all_map]


def _normalize_search_text(value: str | None) -> str:
    text = (value or "").lower()
    replacements = {"ç": "c", "ğ": "g", "ı": "i", "i̇": "i", "ö": "o", "ş": "s", "ü": "u", "â": "a", "î": "i", "û": "u"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _expand_search_terms(query: str | None) -> list[str]:
    base = _normalize_search_text(query)
    terms = [part for part in base.split() if part]
    expanded = list(terms)
    for term in terms:
        for alias in SEARCH_ALIASES.get(term, []):
            expanded.extend(_normalize_search_text(alias).split())
    return list(dict.fromkeys(expanded))


def _build_article_haystack(article: dict[str, Any]) -> str:
    chunks = [article.get("title"), article.get("summary"), article.get("category_slug"), " ".join(article.get("tags") or []), " ".join(article.get("role_slugs") or [])]
    for section in article.get("sections") or []:
        chunks.append(section.get("title"))
        chunks.append(section.get("body"))
        chunks.extend(section.get("bullet_items") or [])
    return _normalize_search_text(" ".join(_as_text(chunk) for chunk in chunks))


def search_articles(query: str | None) -> list[dict[str, Any]]:
    terms = _expand_search_terms(query)
    if not terms:
        return get_popular_articles()
    scored: list[tuple[int, dict[str, Any]]] = []
    for article in get_all_articles():
        haystack = _build_article_haystack(article)
        score = sum(3 if term in _normalize_search_text(article.get("title")) else 1 for term in terms if term in haystack)
        if score:
            scored.append((score, article))
    scored.sort(key=lambda item: (-item[0], item[1].get("title", "")))
    return [article for _, article in scored]


def _coverage_level(article_count: int) -> str:
    if article_count >= 6:
        return "Kapsamlı"
    if article_count >= 3:
        return "Yeterli"
    if article_count >= 1:
        return "Temel"
    return "Hazırlanıyor"


def build_category_cards() -> list[dict[str, Any]]:
    cards = []
    for category in HELP_CATEGORIES:
        articles = get_articles_for_category(category["slug"])
        cards.append({**category, "article_count": len(articles), "coverage_level": _coverage_level(len(articles))})
    return cards


def build_role_cards() -> list[dict[str, Any]]:
    cards = []
    for role in HELP_ROLES:
        articles = get_articles_for_role(role["slug"])
        cards.append({**role, "article_count": len(articles), "coverage_level": _coverage_level(len(articles))})
    return cards


def build_module_guide_groups() -> list[dict[str, Any]]:
    preferred = [
        "performans",
        "raporlama-dashboard",
        "personel-organizasyon",
        "izin-vekalet",
        "iletisim-anket-geri-bildirim",
        "ai-karar-destek",
        "destek-talep",
        "guvenlik-yetki",
        "baslarken",
    ]
    groups = []
    for slug in preferred:
        category = CATEGORY_MAP.get(slug)
        if not category:
            continue
        articles = get_articles_for_category(slug)
        groups.append({
            "slug": slug,
            "title": category["title"],
            "description": category["description"],
            "learning_goal": category.get("learning_goal", ""),
            "icon": category["icon"],
            "article_count": len(articles),
            "coverage_level": _coverage_level(len(articles)),
            "articles": articles[:5],
        })
    return groups


def build_learning_paths() -> list[dict[str, Any]]:
    all_map = {article["slug"]: article for article in get_all_articles()}
    rows = [
        ("Personel hızlı başlangıç", "fa-solid fa-user", "Personel", ["sisteme-ilk-giris-ve-gunluk-kontrol", "izin-talebi-nasil-olusturulur", "nabiz-formu-nasil-doldurulur", "not-karnesi-ne-zaman-gorunur", "destek-talebi-nasil-acilir"]),
        ("Yönetici günlük akış", "fa-solid fa-user-tie", "Yönetici", ["degerlendirme-formu-nasil-doldurulur", "personel-donem-analizi-nasil-okunur", "nabiz-analitigi-nasil-okunur", "yonetici-ozetleri-nasil-okunur", "ai-ozeti-nasil-yorumlanir"]),
        ("Personel birimi kontrol akışı", "fa-solid fa-users-gear", "Personel Birimi", ["personel-kaydi-ve-zorunlu-alanlar", "personel-excel-aktarimi", "amir-zinciri-dogrulama", "performans-donemi-nasil-acilir", "degerlendirme-gorevleri-nasil-uretilir"]),
        ("Sistem yöneticisi güvenli işletim", "fa-solid fa-user-shield", "Sistem Yöneticisi", ["menude-bazi-alanlari-goremiyorum", "csrf-ve-oturum-hatalari", "captcha-neden-acildi", "destek-talebi-nasil-acilir", "ai-risk-ve-aksiyon-onerileri"]),
    ]
    paths = []
    for title, icon, role, slugs in rows:
        steps = [all_map[slug] for slug in slugs if slug in all_map]
        paths.append({"title": title, "icon": icon, "role": role, "steps": steps})
    return paths


def build_suggested_queries() -> list[str]:
    return [
        "Yardım merkezi nasıl kullanılır",
        "Destek talebi nasıl açılır",
        "Talep durumları",
        "Güvenli veri paylaşımı",
        "Personel raporları",
        "Personel dönem analizi",
        "Nabız analitiği",
        "AI karar destek",
        "Menü görünürlüğü",
        "CSRF hatası",
    ]


def build_support_process_steps() -> list[dict[str, str]]:
    return [
        {"icon": "fa-solid fa-magnifying-glass", "title": "1. Rehberi ara", "text": "İşlem adı, ekran başlığı veya hata ifadesiyle önce yardım içeriğini tarayın."},
        {"icon": "fa-solid fa-layer-group", "title": "2. Modül paketini aç", "text": "Performans, personel, iletişim, anket, destek veya güvenlik paketinden ilgili rehberi okuyun."},
        {"icon": "fa-solid fa-route", "title": "3. Rol yolunu izle", "text": "Personel, yönetici, personel birimi veya sistem yöneticisi için önerilen sırayı takip edin."},
        {"icon": "fa-solid fa-ticket", "title": "4. Talep oluştur", "text": "Rehber yeterli olmazsa ekran adresi, işlem adımı ve varsa dosyayla kayıtlı destek talebi açın."},
        {"icon": "fa-solid fa-clock-rotate-left", "title": "5. Durumu takip et", "text": "Talep yanıtlarını, atama bilgisini, çözüm notunu ve durum geçmişini Taleplerim ekranından izleyin."},
    ]


def build_help_quality_cards() -> list[dict[str, str]]:
    return [
        {"icon": "fa-solid fa-language", "title": "Kurumsal dil", "text": "Ekranlarda teknik kod, geçici test ifadesi ve geliştirici dili yerine sade Türkçe açıklama kullanılır."},
        {"icon": "fa-solid fa-shield-halved", "title": "Güvenli paylaşım", "text": "Destek talebinde yalnızca sorunu çözmeye yetecek bilgi paylaşılır; gereksiz kişisel veri eklenmez."},
        {"icon": "fa-solid fa-user-lock", "title": "Yetki sınırı", "text": "Kullanıcı yalnızca rolü ve menü yetkisi kapsamındaki rehber, talep ve yönlendirmelere erişir."},
        {"icon": "fa-solid fa-chart-simple", "title": "Ölçülebilir destek", "text": "Talep yoğunluğu, çözüm süresi, tekrar eden konu ve memnuniyet verisi yönetsel takibe dönüşür."},
    ]


def build_support_status_flow() -> list[dict[str, str]]:
    return [
        {"status": "Açıldı", "text": "Talep kaydedildi ve ilk incelemeyi bekliyor."},
        {"status": "İnceleniyor", "text": "Yetkili kişi talebi değerlendiriyor."},
        {"status": "Bilgi Bekleniyor", "text": "Kullanıcıdan ek açıklama veya dosya bekleniyor."},
        {"status": "Atandı", "text": "Talep ilgili sorumlu kullanıcıya yönlendirildi."},
        {"status": "Geliştirme Planına Alındı", "text": "Talep iyileştirme işi olarak planlandı."},
        {"status": "Çözüldü / Kapatıldı", "text": "Çözüm uygulanmış veya süreç tamamlanmıştır."},
    ]


def build_support_intake_examples() -> list[dict[str, str]]:
    return [
        {"title": "Hata bildirimi", "text": "Sayfa açılmıyor, kayıt kaydedilmiyor veya beklenmeyen sonuç üretiyorsa kullanılır."},
        {"title": "Kullanım desteği", "text": "Hangi işlemin nereden yapılacağı bilinmiyorsa veya rehber ihtiyacı varsa kullanılır."},
        {"title": "Yetki talebi", "text": "Kullanıcı görevine uygun menüyü göremiyor ya da ilgili ekrana erişemiyorsa kullanılır."},
        {"title": "Geliştirme talebi", "text": "Yeni ekran, yeni rapor, metin düzeltmesi veya süreç iyileştirmesi isteniyorsa kullanılır."},
    ]


def build_home_context() -> dict[str, Any]:
    all_articles = get_all_articles()
    category_cards = build_category_cards()
    role_cards = build_role_cards()
    return {
        "category_cards": category_cards,
        "role_cards": role_cards,
        "featured_articles": get_featured_articles(),
        "troubleshooting_articles": get_troubleshooting_articles(),
        "popular_articles": get_popular_articles(),
        "quick_start_articles": get_featured_articles()[:6],
        "module_groups": build_module_guide_groups(),
        "learning_paths": build_learning_paths(),
        "suggested_queries": build_suggested_queries(),
        "support_process_steps": build_support_process_steps(),
        "help_quality_cards": build_help_quality_cards(),
        "support_status_flow": build_support_status_flow(),
        "support_intake_examples": build_support_intake_examples(),
        "total_article_count": len(all_articles),
        "total_category_count": len(category_cards),
        "total_role_count": len(role_cards),
        "db_help_articles_enabled": _help_tables_ready(),
        "db_help_article_count": len(get_db_articles()) if _help_tables_ready() else 0,
    }


def get_category(slug: str) -> dict[str, Any] | None:
    category = CATEGORY_MAP.get(slug)
    if not category:
        return None
    articles = get_articles_for_category(slug)
    return {**category, "articles": articles, "article_count": len(articles), "coverage_level": _coverage_level(len(articles))}


def get_role(slug: str) -> dict[str, Any] | None:
    role = ROLE_MAP.get(slug)
    if not role:
        return None
    articles = get_articles_for_role(slug)
    return {**role, "articles": articles, "article_count": len(articles), "coverage_level": _coverage_level(len(articles))}


def get_article(slug: str, include_unpublished: bool = False) -> dict[str, Any] | None:
    for article in get_all_articles(published_only=not include_unpublished):
        if article.get("slug") == slug:
            category = CATEGORY_MAP.get(article.get("category_slug") or "", {})
            roles = [ROLE_MAP[r] for r in article.get("role_slugs", []) if r in ROLE_MAP]
            return {**article, "category": category, "roles": roles, "related_articles": get_related_articles(article)}
    return None
