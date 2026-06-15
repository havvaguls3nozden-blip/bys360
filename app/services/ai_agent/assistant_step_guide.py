from __future__ import annotations

# BYS360_ASSISTANT_CANONICAL_STEP_GUIDE_V1

from typing import Any

VERSION = "BYS360 Asistanı Kullanım Rehberi V1"
MODE = "Adım adım kurumsal rehberlik"
NOTICE = "BYS360 Asistanı idari karar vermez, puan değiştirmez, onay vermez ve yetki dışı veri göstermez."


def _norm(value: Any) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
        .replace("ı", "i")
        .replace("İ", "i")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ö", "o")
        .replace("ç", "c")
    )


def _has(text: str, *terms: str) -> bool:
    return any(_norm(term) in text for term in terms)


def _action(label: str, route: str, description: str = "") -> dict[str, str]:
    return {
        "label": label,
        "title": label,
        "route": route,
        "url": route,
        "description": description or "BYS360 içinde güvenli yönlendirme",
        "safety_level": "rehber_yonlendirme",
    }


def _reply(intent: str, answer: str, actions: list[dict[str, str]] | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "mode": MODE,
        "intent": intent,
        "answer": answer.strip(),
        "actions": actions or [],
        "quick_replies": [
            "Personel nasıl eklenir?",
            "Performans dönemi nasıl açılır?",
            "Karnemi nereden görürüm?",
            "Rol matrisinden menü nasıl açılır?",
            "Destek talebi nasıl oluşturulur?",
        ],
        "notice": NOTICE,
        "automation_notice": "İşlem yapmak için ilgili ekrandaki yetkili butonları kullanıcı kullanır; asistan otomatik işlem yapmaz.",
        "security_notice": "Cevaplar yalnızca rehberlik ve güvenli yönlendirme amaçlıdır.",
        "assistant_panel_notice": "Merhaba, ben BYS360 Asistanı. BYS360 kullanımında size adım adım yardımcı olurum.",
    }


def build_bys360_assistant_step_reply(user: Any, question: str) -> dict[str, Any] | None:
    """BYS360 Asistanı için sabit, güvenli ve adım adım kullanım rehberi.

    Bu modül kişisel veri, puan, amir görüşü, mesaj içeriği veya anket cevabı döndürmez.
    Yalnızca kullanıcıyı ilgili ekrana ve işlem adımına yönlendirir.
    """
    q = _norm(question)
    if not q:
        return None

    # Kimlik / kabiliyet
    if _has(q, "adın ne", "adin ne", "sen kimsin", "ne yapabilirsin", "asistan ne yapar", "bys360 asistani", "bys360 asistanı"):
        return _reply(
            "assistant_identity",
            """
Ben BYS360 Asistanı. BYS360 içinde kullanıcıya ekranları, işlem adımlarını ve süreç mantığını sade biçimde anlatırım.

Adım adım yardımcı olabileceğim ana alanlar:
1. Personel Yönetimi: personel kaydı, sicil, birim, yönetici, izin ve vekâlet yönlendirmeleri.
2. Performans Yönetimi: dönem, kriter, amir zinciri, puanlama, karne, 70 altı süreç ve yayın adımları.
3. İletişim / Anket / Destek: mesaj, duyuru, bildirim, anket ve destek talebi ekranları.
4. Sistem Ayarları: rol matrisi, menü görünürlüğü, modül ayarları ve güvenlik ayarları.
5. KPI / Hedef: hedef kartları, KPI dashboardu ve analiz ekranları.

Ben idari karar vermem, performans puanı üretmem, onay/ret işlemi yapmam ve yetki dışı veri göstermem. Sizi doğru ekrana güvenli şekilde yönlendiririm.
            """,
            [_action("BYS360 Asistanı Paneli", "/ai-agent/panel"), _action("Asistan Bilgi Bankası", "/ai-agent/knowledge")],
        )

    # Personel ekleme
    if _has(q, "personel ekle", "personel kaydi", "personel kaydı", "yeni personel", "sicil no", "sicil numarasi"):
        return _reply(
            "personnel_create_steps",
            """
Personel eklemek için adımlar:
1. Sol menüden Personel Yönetimi bölümünü açın.
2. Personel Özlük Dosyaları ekranına girin.
3. Yeni personel ekleme butonunu kullanın.
4. Sicil No, ad soyad, unvan, birim, üst birim ve yönetici alanlarını doldurun.
5. Varsa profil fotoğrafı ve iletişim bilgilerini ekleyin.
6. Rol ve menü görünürlüğü gerekiyorsa Sistem Ayarları / Rol Matrisi üzerinden kontrol edin.
7. Kaydettikten sonra personelin organizasyon ve performans zincirinde doğru görünüp görünmediğini kontrol edin.

Not: BYS360’da TC yerine Sicil No esas alınır. Asistan personel kaydı oluşturmaz; yalnızca doğru adımı gösterir.
            """,
            [_action("Personel Özlük Dosyaları", "/personnel"), _action("Rol Matrisi", "/admin/role-matrix")],
        )

    # İzin / vekalet
    if _has(q, "izin", "vekalet", "vekâlet", "devamsizlik", "devamsızlık"):
        return _reply(
            "leave_delegation_steps",
            """
İzin, devamsızlık veya vekâlet işlemleri için adımlar:
1. Sol menüden Personel Yönetimi bölümünü açın.
2. İzin ve Devamsızlık Takibi veya Devamsızlık ve Vekâlet ekranına girin.
3. İlgili personeli ve tarih aralığını seçin.
4. İzin, devamsızlık veya vekâlet türünü belirleyin.
5. Vekâlet varsa vekil kişiyi ve geçerlilik süresini tanımlayın.
6. Kaydetmeden önce performans ve görev akışını etkileyebilecek tarihleri kontrol edin.

Asistan vekâlet atamaz veya izin onaylamaz; yalnızca işlem yolunu gösterir.
            """,
            [_action("İzin ve Devamsızlık Takibi", "/hr-management/leave"), _action("Devamsızlık ve Vekâlet", "/hr-management/attendance")],
        )

    # Performans dönemi
    if _has(q, "performans donemi", "performans dönemi", "donem ac", "dönem aç", "yeni dönem", "donem nasil"):
        return _reply(
            "performance_period_steps",
            """
Performans dönemi açmak için adımlar:
1. Sol menüden Performans Yönetimi bölümünü açın.
2. Dönem Yönetimi ekranına girin.
3. Yeni dönem oluştur butonunu seçin.
4. Dönem adını, dönem türünü ve tarih aralığını girin.
5. Kapsam tipini seçin: tüm kurum, birim, kategori veya seçili personel.
6. Kriter ve ağırlıkların bu dönem için hazır olduğundan emin olun.
7. Kaydettikten sonra görev üretimi / değerlendirme görevleri ekranından zinciri kontrol edin.

Dönem açma işlemi rol yetkisine bağlıdır. Asistan dönem oluşturmaz; sadece adımları anlatır.
            """,
            [_action("Dönem Yönetimi", "/performance/periods"), _action("Performans Paneli", "/performance/dashboard")],
        )

    # Kriter / puanlama
    if _has(q, "kriter", "degerlendirme kriter", "değerlendirme kriter", "puanlama", "puan ver", "amir puan"):
        return _reply(
            "performance_scoring_steps",
            """
Performans kriteri ve puanlama süreci için adımlar:
1. Performans Yönetimi bölümünden Değerlendirme Kriterleri ekranını kontrol edin.
2. Aktif dönem için kullanılacak kriterlerin açık olduğundan emin olun.
3. Amir olarak Görevlerim / Performans Görevleri ekranına girin.
4. Değerlendirilecek personeli seçin.
5. Her kriter için 1-5 arası puan ve gerekiyorsa açıklama girin.
6. 1 ve 5 puan açıklama zorunluluğu sistem ayarına bağlıdır.
7. Nihai sonuç 70 altı veya 90 üstü ise ayrıntılı genel görüş gerekebilir.
8. Kaydetmeden önce önceki amir görüşü ve süreç uyarılarını kontrol edin.

Asistan puan vermez, puan önermez ve amir görüşü yazmaz; yalnızca ekran yolunu açıklar.
            """,
            [_action("Performans Görevlerim", "/performance/tasks"), _action("Değerlendirme Kriterleri", "/performance/criteria")],
        )

    # Karne / yayın
    if _has(q, "karne", "karnem", "not karnesi", "sonucumu", "sonucum", "yayın", "yayin", "goremiyorum", "görünmüyor"):
        return _reply(
            "scorecard_publish_steps",
            """
Karne görüntüleme ve yayın mantığı:
1. Personel kendi karnesini ancak yayın/onay süreci tamamlandıktan sonra görebilir.
2. Karneniz görünmüyorsa değerlendirme henüz tamamlanmamış olabilir.
3. 70 altı sonuç varsa Başkan/Üst Onay süreci bekleniyor olabilir.
4. Yayın öncesi Personel ve Destek Hizmetleri Grup Başkanı ön onayı gerekiyorsa süreç tamamlanmadan karne açılmaz.
5. Yayınlandıktan sonra Not Karnesi ekranından güncel sonucu, Geçmiş Karne Arşivi ekranından eski dönemleri görebilirsiniz.

Asistan puan, amir görüşü veya hassas karne detayı göstermez; sizi ilgili ekrana yönlendirir.
            """,
            [_action("Not Karnesi", "/performance/scorecard"), _action("Geçmiş Karne Arşivi", "/performans/gecmis-karne-arsivi")],
        )

    # 70 altı / başkan onayı
    if _has(q, "70 alti", "70 altı", "dusuk performans", "düşük performans", "baskan onay", "başkan onay", "ust onay", "üst onay"):
        return _reply(
            "low_score_approval_steps",
            """
70 altı performans sonucunda süreç şöyle ilerler:
1. Değerlendirme tamamlanır ve nihai puan hesaplanır.
2. Nihai puan 70’in altındaysa sonuç doğrudan kesinleşmez.
3. Kayıt Başkan/Üst Onay sürecine düşer.
4. Onay tamamlanmadan karne personele kesin sonuç olarak yayınlanmaz.
5. İlk 70 altı sonuçta uyarı/süreç kaydı oluşturulur.
6. Aynı yıl ikinci 70 altı sonuçta tekrarlayan düşük performans süreci başlatılır.
7. Sistem otomatik idari işlem yapmazma yapmaz; yalnızca yetkili idari sürece kayıt üretir.

Asistan onay/ret işlemi yapmaz; yalnızca Başkan Onayları ve Süreç Takibi ekranına yönlendirir.
            """,
            [_action("Başkan Onayları", "/performance/president-approvals"), _action("Süreç Takibi", "/performance/process-tracking")],
        )

    # 3. amir
    if _has(q, "3. amir", "ucuncu amir", "üçüncü amir", "3 amir"):
        return _reply(
            "third_supervisor_steps",
            """
3. amir kuralı için temel kullanım:
1. 3. amir her personel için zorunlu değildir.
2. Yapıda gerçek 3. amir yoksa sistem boş görev veya boş sütun göstermemelidir.
3. 3. amir yorum modundaysa yalnızca görüş yazar, puana etkisi olmaz.
4. 3. amir puan modundaysa sistem ayarındaki ağırlık hesabına dahil edilir.
5. İşlem sırası çok seviyeli yapılarda varsa 3. amir, sonra 2. amir, en son 1. amir şeklindedir.
6. Kör değerlendirme yoktur; sonraki amir önceki değerlendirmeyi görür.

Bu ayarlar Sistem Ayarları ve Performans Yönetimi yetkileriyle kontrol edilir.
            """,
            [_action("Sistem Ayarları", "/settings"), _action("Performans Görevleri", "/performance/tasks")],
        )

    # Rol matrisi / menü
    if _has(q, "rol matrisi", "menu", "menü", "gizle", "goster", "göster", "yetki", "ekrani ac", "ekranı aç", "sekme"):
        return _reply(
            "role_matrix_steps",
            """
Rol matrisi ve menü görünürlüğü için adımlar:
1. Sistem Ayarları bölümüne girin.
2. Rol Matrisi / Menü Görünürlüğü ekranını açın.
3. Düzenlenecek rolü, kullanıcıyı veya birim profilini seçin.
4. Görünmesi istenen menüleri açık, görünmemesi gerekenleri kapalı yapın.
5. Kaydettikten sonra aynı yetkinin backend erişim kontrolünde de çalıştığını kontrol edin.
6. Kullanıcı yetkisizse menüyü hiç görmemeli; URL yazarsa kurumsal erişim engeli ekranı görmelidir.

Asistan yetki vermez veya kaldırmaz; yalnızca doğru ayar ekranına yönlendirir.
            """,
            [_action("Rol Matrisi", "/admin/role-matrix"), _action("Sistem Ayarları", "/settings")],
        )

    # Destek
    if _has(q, "destek talebi", "yardim talebi", "yardım talebi", "ariza", "arıza", "talep ac", "talep aç"):
        return _reply(
            "support_ticket_steps",
            """
Destek talebi oluşturmak için adımlar:
1. Sol menüden Yardım Merkezi veya Destek Talebi Aç ekranına girin.
2. Talep konusunu kısa ve anlaşılır yazın.
3. Kategori ve öncelik alanlarını seçin.
4. Açıklama bölümüne yaşadığınız sorunu ekleyin.
5. Gerekirse ekran görüntüsü veya belge ekleyin.
6. Talebi kaydedin ve Taleplerim ekranından durumunu takip edin.

Asistan destek talebinin içeriğini herkese göstermez; yalnızca sizi ilgili ekrana yönlendirir.
            """,
            [_action("Destek Talebi Aç", "/support/new"), _action("Taleplerim", "/support")],
        )

    # Anket / bildirim / iletişim
    if _has(q, "anket", "duyuru", "bildirim", "mesaj", "geri bildirim", "nabiz", "nabız"):
        return _reply(
            "communication_steps",
            """
İletişim, anket ve bildirim kullanımı:
1. Bildirimler ekranından size gelen sistem bildirimlerini kontrol edin.
2. Duyurular ekranından kurum içi duyuruları takip edin.
3. Anketler ekranından size atanmış anketleri yanıtlayın.
4. Geri bildirim veya nabız ekranları açıksa ilgili formu doldurun.
5. Mesajlar ekranından yetkiniz dahilindeki konuşmaları takip edin.

Asistan mesaj içeriği, anket cevabı veya kişisel geri bildirim detayı göstermez.
            """,
            [_action("Bildirimler", "/notifications"), _action("Anketler", "/surveys"), _action("Mesajlar", "/messages")],
        )

    # KPI / hedef
    if _has(q, "kpi", "hedef", "stratejik", "riskli hedef", "hedef kart"):
        return _reply(
            "kpi_target_steps",
            """
KPI ve Hedef Yönetimi için adımlar:
1. Performans Yönetimi bölümünden KPI Dashboardu ekranını açın.
2. Hedef durumlarını, gerçekleşme oranlarını ve riskli hedefleri kontrol edin.
3. Hedef eklemek veya düzenlemek için KPI ve Hedef Yönetimi ekranına geçin.
4. Hedef kartında hedef adı, kapsam, sahip, ağırlık, hedef değer ve tarih aralığını kontrol edin.
5. KPI Analiz Merkezi ekranından riskli veya geciken hedefleri inceleyin.

Asistan hedef kapatmaz, hedef değeri değiştirmez ve karar vermez; yalnızca analiz ekranına yönlendirir.
            """,
            [_action("KPI Dashboardu", "/performans/stratejik/kpi-dashboard"), _action("KPI ve Hedef Yönetimi", "/performans/stratejik/hedefler")],
        )

    return None
