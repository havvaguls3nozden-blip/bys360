# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

V31_MARKER = "BYS360_ASSISTANT_CHATGPT_LIKE_V31"
V31_2_HOME_DASHBOARD_SPLIT = "BYS360_ASSISTANT_HOME_DASHBOARD_SPLIT_V31_2"
V31_5_QUESTION_UNIVERSE = "BYS360_ASSISTANT_QUESTION_UNIVERSE_V31_5"
V31_4_REAL_SCREEN_NAMES = "BYS360_ASSISTANT_REAL_SCREEN_NAMES_V31_4"
V32_MARKER = "BYS360_ASSISTANT_ADVANCED_INTELLIGENCE_V32"


def _tr(text: str) -> str:
    text = text or ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU"))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _role_name(user: Any) -> str:
    for attr in ("role", "role_name", "user_role", "profile_role"):
        value = getattr(user, attr, None)
        if value:
            return str(value)
    return "Kullanıcı"


def _display_name(user: Any) -> str:
    for attr in ("full_name", "name", "display_name", "username"):
        value = getattr(user, attr, None)
        if value:
            return str(value).strip()
    return ""


CANONICAL_UI_REPLACEMENTS_V31_4: Tuple[Tuple[str, str], ...] = (
    ("Dönemler", "Dönemler"),
    ("Dönemler", "Dönemler"),
    ("Dönemler", "Dönemler"),
    ("Başkan Onayları", "Başkan Onayları"),
    ("Başkan Onayı", "Başkan Onayı"),
    ("Yayın Ön Onayı", "Yayın Ön Onayı"),
    ("Dönem İçi Notlar / Gelişim Rehberi", "Dönem İçi Notlar / Gelişim Rehberi"),
    ("Sorular / Kriterler ekranına", "Sorular / Kriterler ekranına"),
    ("Sorular / Kriterler sekmesini", "Sorular / Kriterler sekmesini"),
    ("Performans Yönetimi > Sorular / Kriterler", "Performans Yönetimi > Sorular / Kriterler"),
    ("Değerlendirme Görevleri ekranına", "Değerlendirme Görevleri ekranına"),
    ("Performans Yönetimi > Değerlendirme Görevleri", "Performans Yönetimi > Değerlendirme Görevleri"),
    ("Not Karnesi / Geçmiş Karne Arşivi", "Not Karnesi / Geçmiş Karne Arşivi"),
    ("Performans Yönetimi > Not Karnesi / Geçmiş Karne Arşivi", "Performans Yönetimi > Not Karnesi / Geçmiş Karne Arşivi"),
    ("KPI Dashboardu", "KPI Dashboardu"),
)


def _canonical_ui_text_v31_4(value: Any) -> str:
    text = "" if value is None else str(value)
    for old, new in CANONICAL_UI_REPLACEMENTS_V31_4:
        text = text.replace(old, new)
    return text


@dataclass(frozen=True)
class Topic:
    key: str
    module: str
    title: str
    keywords: Tuple[str, ...]
    menu_path: str
    roles: Tuple[str, ...]
    steps: Tuple[str, ...]
    warnings: Tuple[str, ...] = ()
    checks: Tuple[str, ...] = ()
    actions: Tuple[Tuple[str, str], ...] = ()
    aliases: Tuple[str, ...] = ()
    score_boost: int = 0


TOPICS: Tuple[Topic, ...] = (

    Topic(
        key="home_page",
        module="Genel",
        title="Ana Sayfa",
        keywords=("ana sayfa", "anasayfa", "baslangic", "başlangıç", "bugun ne var", "bugün ne var", "gunluk ozet", "günlük özet", "nereden baslayacagim", "nereden başlayacağım"),
        menu_path="Ana Sayfa",
        roles=("Tüm kullanıcılar",),
        steps=(
            "Ana Sayfa, BYS360 açılış ve günlük başlangıç ekranıdır.",
            "Kullanıcı burada kendisine açık kısa özetleri, bekleyen bildirim/görev/anket/destek kartlarını ve modül geçişlerini görür.",
            "İşlem yapmak için Ana Sayfa’dan ilgili gerçek modül ekranına geçilir.",
        ),
        warnings=("Ana Sayfa yönetici analiz ekranı değildir; grafik ve kurumsal gösterge için Dashboard kullanılır.",),
        checks=("/home yolunda Ana Sayfa cevabı; /dashboard yolunda Dashboard cevabı dönmelidir.",),
        actions=(("Ana Sayfa", "/home"), ("Dashboard", "/dashboard")),
        aliases=("home", "baslangic", "başlangıç"),
        score_boost=8,
    ),
    Topic(
        key="general_dashboard",
        module="Yönetici Dashboard",
        title="Dashboard",
        keywords=("dashboard", "genel dashboard", "yonetici dashboard", "yönetici dashboard", "gosterge paneli", "gösterge paneli", "yonetici gorunumu", "yönetici görünümü"),
        menu_path="Dashboard",
        roles=("Başkan", "Admin", "Yöneticiler", "Rol matrisinde yetki verilmiş kullanıcılar"),
        steps=(
            "Dashboard, Ana Sayfa’dan farklı olarak yönetici görünürlüğü ve analiz ekranıdır.",
            "Bu ekranda yetki kapsamındaki özet kartlar, grafikler, KPI/performans bağlantıları ve kurumsal durum göstergeleri izlenir.",
            "Ayrıntılı işlem için ilgili modül ekranına geçilir: Performans Dashboard, KPI Dashboardu, Raporlar, Destek veya Anket gibi.",
        ),
        warnings=("Dashboard günlük başlangıç ekranı olan Ana Sayfa ile karıştırılmamalıdır.", "Kart veya grafik görünmüyorsa rol matrisi, kişi bazlı menü izni ve modül ayarı kontrol edilmelidir."),
        checks=("/dashboard yolunda Dashboard; /home yolunda Ana Sayfa olarak tanınmalıdır.",),
        actions=(("Dashboard", "/dashboard"), ("Ana Sayfa", "/home"), ("Performans Dashboard", "/performance/dashboard")),
        aliases=("dashboard", "gosterge", "gösterge"),
        score_boost=9,
    ),
    Topic(
        key="person_add",
        module="Personel Yönetimi",
        title="Personel / kişi ekleme",
        keywords=("personel ekle", "kisi ekle", "kişi ekle", "kullanici ekle", "sicil", "yeni personel", "personel kaydi", "personel nasıl eklenir"),
        menu_path="Personel Yönetimi > Personel Listesi / Personel Ekle",
        roles=("Admin", "Sistem Yöneticisi", "Personel Yönetimi yetkilisi", "Yetki verilmiş İK/personel kullanıcısı"),
        steps=(
            "Sol menüden Personel Yönetimi bölümüne girin.",
            "Personel Listesi veya Personel Ekle ekranını açın.",
            "Yeni Personel Ekle butonuna basın.",
            "Sicil No, ad, soyad, unvan, görev, birim, üst birim ve yönetici alanlarını doldurun.",
            "Gerekirse profil fotoğrafı ve kullanıcı hesabı/rol bilgisini ekleyin.",
            "Kaydedin ve personelin listede göründüğünü kontrol edin.",
        ),
        warnings=("BYS360’da TC yerine Sicil No esas alınmalıdır.", "Unvan, birim, üst birim ve yönetici alanları boş kalırsa performans amir zinciri yanlış üretilebilir."),
        checks=("Kayıt sonrası personelin birimi, yöneticisi, rolü ve menü görünürlüğü doğru mu kontrol edin.",),
        actions=(("Personel Listesi", "/personnel"), ("Personel Ekle", "/personnel/create")),
        aliases=("personel", "kisi", "kişi", "sicil"),
        score_boost=5,
    ),
    Topic(
        key="leave",
        module="Personel Yönetimi",
        title="İzin kaydı / izin talebi",
        keywords=("izin", "izin gir", "izin talebi", "izin kaydi", "yillik izin", "yıllık izin"),
        menu_path="Personel Yönetimi > İzin Yönetimi",
        roles=("Personel", "Amir", "Personel Yönetimi yetkilisi", "Admin"),
        steps=(
            "Personel Yönetimi veya İzin Yönetimi ekranına girin.",
            "İzin Talebi / İzin Kaydı alanını açın.",
            "Personeli, izin türünü ve başlangıç-bitiş tarihlerini seçin.",
            "Gerekli açıklama veya belge varsa ekleyin.",
            "Kaydedin; onay süreci varsa ilgili amire düştüğünü kontrol edin.",
        ),
        warnings=("İzinli amir varsa performans görevleri vekâlet yapısından etkilenebilir.",),
        checks=("İzin kaydının takvimde, personel geçmişinde ve varsa vekâlet akışında göründüğünü kontrol edin.",),
        actions=(("İzin Yönetimi", "/personnel/leaves"),),
    ),
    Topic(
        key="delegation",
        module="Personel Yönetimi",
        title="Vekâlet tanımlama",
        keywords=("vekalet", "vekâlet", "vekil", "gorev devri", "görev devri", "amirim izinli"),
        menu_path="Personel Yönetimi > Vekâlet Yönetimi",
        roles=("Admin", "Personel Yönetimi yetkilisi", "Yetki verilmiş birim kullanıcısı"),
        steps=(
            "Personel Yönetimi > Vekâlet Yönetimi ekranına girin.",
            "Asıl kişiyi ve vekil olacak kişiyi seçin.",
            "Başlangıç ve bitiş tarihlerini belirleyin.",
            "Vekâlet kapsamını seçip kaydedin.",
            "Performans veya onay süreçlerinde vekilin devreye girip girmediğini kontrol edin.",
        ),
        warnings=("Vekâlet süresi ve kapsamı yanlış girilirse onay veya değerlendirme görevleri yanlış kişiye düşebilir.",),
        checks=("Vekâlet kaydı aktif mi, tarih aralığı doğru mu, ilgili süreçte görev devri çalışıyor mu kontrol edin.",),
        actions=(("Vekâlet Yönetimi", "/personnel/delegations"),),
    ),
    Topic(
        key="performance_overview",
        module="Performans Yönetimi",
        title="Performans Yönetimi genel akışı",
        keywords=("performans", "degerlendirme", "değerlendirme", "performans sureci", "performans süreci", "puanlama sureci", "puanlama süreci"),
        menu_path="Performans Yönetimi",
        roles=("Başkan / Üst Yönetim", "Admin", "Performans Yetkilisi", "Amir", "Personel"),
        steps=(
            "Dönem hazırlanır; tür, tarih ve kapsam belirlenir.",
            "Değerlendirme Kriterleri ve ağırlık ayarları kontrol edilir.",
            "Personel, birim, kategori, amir, izin ve vekâlet verisi doğrulanır.",
            "Görev üretimi yapılır ve amirlere değerlendirme görevleri düşer.",
            "Amirler puan/görüş girer; düşük veya yüksek eşiklerde açıklama kuralları çalışır.",
            "70 altı sonuçlar Başkan Onayı sürecine girer; gerekli onaylar tamamlanmadan personele yayınlanmaz.",
            "Yayın sonrası karne, geçmiş kayıt ve raporlar yetki sınırına göre görünür olur.",
        ),
        warnings=("Sistem kör değerlendirme yapmaz; sonraki amir önceki değerlendirmeyi görebilir.", "Personel sonucu süreç tamamlanmadan göremez."),
        checks=("Dönem, kriter, ağırlık, görev üretimi ve yayın/onay adımlarının tamamlandığını kontrol edin.",),
        actions=(("Performans Dashboard", "/performance/dashboard"), ("Performans Raporları", "/performance/reports")),
    ),
    Topic(
        key="period_create",
        module="Performans Yönetimi",
        title="Performans dönemi oluşturma",
        keywords=("donem ac", "dönem aç", "donem olustur", "dönem oluştur", "yeni donem", "yeni dönem", "performans donemi", "performans dönemi", "2026 performans", "guvenlik personeline ozel donem", "güvenlik personeline özel dönem", "temizlik donemi", "temizlik dönemi", "aylik donem", "aylık dönem", "uc aylik", "üç aylık", "6 aylik", "6 aylık"),
        menu_path="Performans Yönetimi > Dönemler",
        roles=("Admin", "Sistem Yöneticisi", "Performans Yetkilisi", "Yetki verilmiş İK/personel kullanıcısı"),
        steps=(
            "Performans Yönetimi bölümüne girin.",
            "Dönemler sekmesini açın.",
            "Yeni Dönem Oluştur butonuna basın.",
            "Dönem adını, dönem türünü ve tarih aralığını girin.",
            "Kapsam tipini seçin: tüm kurum, birim, üst birim, kategori/grup veya seçili personel.",
            "Kapsama göre birim, kategori ya da personelleri seçin.",
            "Kaydedin; ardından kriter, ağırlık ve görev üretimi adımlarına geçin.",
        ),
        warnings=("Aynı personel için aynı tarih aralığında çakışan dönem varsa sistem uyarı vermelidir.", "Kategoriye özel dönem açıldıysa görevler sadece o kapsamdaki personele üretilmelidir."),
        checks=("Dönem listede görünüyor mu, kapsam doğru mu, görev üretimi doğru personele mi yapılacak kontrol edin.",),
        actions=(("Dönemler", "/performance/periods"),),
        aliases=("donem", "dönem", "kapsam", "kategori donemi"),
        score_boost=7,
    ),
    Topic(
        key="criteria",
        module="Performans Yönetimi",
        title="Sorular / Kriterler",
        keywords=("kriter", "degerlendirme kriterleri", "değerlendirme kriterleri", "yetkinlik", "kriter ekle", "performans kriteri"),
        menu_path="Performans Yönetimi > Sorular / Kriterler",
        roles=("Admin", "Performans Yetkilisi"),
        steps=(
            "Performans Yönetimi > Sorular / Kriterler ekranına girin.",
            "Yeni kriter ekle butonunu kullanın.",
            "Kriter adı, açıklama, aktiflik ve varsa dönem/kategori bağlantısını girin.",
            "Kaydedin ve kriterin ilgili dönemde kullanılabilir olduğunu kontrol edin.",
        ),
        warnings=("Ekran dili olarak ana ifade Değerlendirme Kriterleri olmalıdır.",),
        checks=("Kriter aktif mi, döneme bağlı mı, puanlama ekranında görünüyor mu kontrol edin.",),
        actions=(("Sorular / Kriterler", "/performance/criteria"),),
    ),
    Topic(
        key="weights",
        module="Performans Yönetimi",
        title="Ağırlık ayarları",
        keywords=("agirlik", "ağırlık", "puan agirligi", "puan ağırlığı", "1 amir", "2 amir", "3 amir", "yuzde", "yüzde"),
        menu_path="Performans Yönetimi > Ağırlık Ayarları",
        roles=("Admin", "Performans Yetkilisi"),
        steps=(
            "Ağırlık Ayarları ekranını açın.",
            "Dönem, rol grubu veya amir yapısını seçin.",
            "1. amir, 2. amir ve varsa 3. amir ağırlıklarını girin.",
            "Toplamın her durumda %100 olduğunu kontrol edip kaydedin.",
        ),
        warnings=("3. amir yorum modundaysa puan ağırlığı %0 olmalıdır.", "3. amir puan modundaysa ağırlık hesabına dahil olur ama toplam yine %100 kalır."),
        checks=("Yanlış ağırlık tanımı nihai puanı etkiler; kayıttan sonra örnek hesaplama kontrolü yapılmalıdır.",),
        actions=(("Ağırlık Ayarları", "/performance/weights"),),
    ),
    Topic(
        key="task_generation",
        module="Performans Yönetimi",
        title="Değerlendirme görevlerini üretme",
        keywords=("gorev uret", "görev üret", "degerlendirme gorevi", "değerlendirme görevi", "amir gorevi", "amir görevi", "gorevler olustur", "görevler oluştur", "gorev dusmedi", "görev düşmedi"),
        menu_path="Performans Yönetimi > Değerlendirme Görevleri",
        roles=("Admin", "Performans Yetkilisi"),
        steps=(
            "Değerlendirme Görevleri ekranına girin.",
            "Dönemi ve kapsamı seçin.",
            "Personel, birim, kategori, amir, izin ve vekâlet verilerini kontrol edin.",
            "Görevleri Oluştur butonuna basın.",
            "Oluşan görevlerde eksik amir, yanlış kişi veya sahte bekleme var mı kontrol edin.",
            "Hata varsa personel/organizasyon kaydını düzeltip görevleri yeniden üretin.",
        ),
        warnings=("3. amir olmayan kişide boş 3. amir görevi oluşmamalıdır.", "Hukuk Müşavirliği ve özel roller gibi istisnalar dikkate alınmalıdır."),
        checks=("Görev listesi gerçek akışa uygun mu; yanlış bekleme durumu var mı kontrol edin.",),
        actions=(("Değerlendirme Görevleri", "/performance/assignments"),),
    ),
    Topic(
        key="scoring",
        module="Performans Yönetimi",
        title="Amir değerlendirmesi / puanlama",
        keywords=("puanla", "puanlama", "degerlendirme yap", "değerlendirme yap", "amir degerlendirmesi", "amir değerlendirmesi", "gorevlerim", "görevlerim", "puan girecegim", "puan gireceğim"),
        menu_path="Performans Yönetimi > Görevlerim",
        roles=("Amir", "Koordinatör", "Grup Başkanı", "Başkan Yardımcısı", "Başkan"),
        steps=(
            "Değerlendirme Görevlerim ekranına girin.",
            "Size atanmış personel kaydını seçin.",
            "Kriter bazlı 1–5 arası puanları girin.",
            "Gerekli açıklamaları ve genel görüşü yazın.",
            "Kaydet veya Tamamla butonuna basın.",
            "Görevin tamamlandı durumuna geçtiğini kontrol edin.",
        ),
        warnings=("1 ve 5 puan açıklama zorunluluğu sistem ayarına göre çalışır.", "70 altı ve 90 üstü sonuçlarda ayrıntılı genel görüş gerekir.", "Sonraki amir önceki amirin puan ve kanaatini görebilir; kör değerlendirme yoktur."),
        checks=("Eksik açıklama varsa sistem tamamlamaya izin vermemelidir.",),
        actions=(("Görevlerim", "/performance/my-evaluations"),),
    ),
    Topic(
        key="low_performance",
        module="Performans Yönetimi",
        title="70 altı performans sonucu / Başkan Onayı",
        keywords=("70 alti", "70 altı", "dusuk performans", "düşük performans", "baskan onayi", "başkan onayı", "ust onay", "üst onay", "basarisiz", "başarısız", "uyari", "uyarı", "ikinci kez 70", "yayin kilidi", "yayın kilidi"),
        menu_path="Performans Yönetimi > Başkan Onayları",
        roles=("Başkan", "Admin", "Sistem Yöneticisi", "Yetkili takip kullanıcıları"),
        steps=(
            "Değerlendirme tamamlanınca sistem nihai puanı hesaplar.",
            "Nihai puan 70’in altındaysa sonuç doğrudan kesinleşmez.",
            "Kayıt Başkan Onayı sürecine düşer ve yayın kilidi oluşur.",
            "Başkan Onayı ekranında karne, amir görüşleri, süreç geçmişi ve gerekçeler incelenir.",
            "Onay/ret işleminden sonra personel süreç zinciri ve yayın hazırlığı tamamlanır.",
            "Gerekli onaylar bitmeden personel karnesi yayınlanmaz.",
        ),
        warnings=("Sistem otomatik işten çıkarma yapmaz; sadece idari süreç statüsü üretir.", "70 üstü kayıt için sahte Başkan onayı oluşturulmamalıdır."),
        checks=("Başkan Onayı olmadan karne personele açılıyor mu özellikle test edilmelidir.",),
        actions=(("Başkan Onayları", "/performance/president-approvals"),),
        score_boost=6,
    ),
    Topic(
        key="publish_preapproval",
        module="Performans Yönetimi",
        title="Yayın ön onayı",
        keywords=("yayin on onayi", "yayın ön onayı", "personel ve destek", "nihai yayin", "nihai yayın", "sonuc yayinla", "sonuç yayınla", "karne yayinla", "karne yayınla"),
        menu_path="Performans Yönetimi > Yayın Ön Onayı",
        roles=("Personel ve Destek Hizmetleri Grup Başkanı", "Admin", "İK/Performans Yetkilisi"),
        steps=(
            "Tüm değerlendirme görevlerinin tamamlandığını kontrol edin.",
            "70 altı kayıt varsa Başkan Onayı sürecinin tamamlandığından emin olun.",
            "Sonuçlar Personel ve Destek Hizmetleri Grup Başkanı yayın ön onayına düşer.",
            "Ön onay verildikten sonra Admin/İK nihai yayını yapabilir.",
            "Yayın sonrası personel karneleri yetki sınırına göre açılır.",
        ),
        warnings=("Yayın ön onayı tamamlanmadan Admin/İK nihai yayın yapmamalıdır.",),
        checks=("Yayınlanan karneler yalnızca ilgili personele ve yetkili yöneticilere görünmelidir.",),
        actions=(("Yayın Ön Onayı", "/performance/personnel-support-publish-approvals"),),
    ),
    Topic(
        key="scorecard",
        module="Performans Yönetimi",
        title="Karne / geçmiş karne arşivi",
        keywords=("karne", "not karnesi", "gecmis karne", "geçmiş karne", "puan arsivi", "puan arşivi", "eski puan", "karnem", "performans sonucum"),
        menu_path="Performans Yönetimi > Not Karnesi / Geçmiş Karne Arşivi",
        roles=("Personel", "Amir", "Koordinatör", "Grup Başkanı", "Başkan", "Admin"),
        steps=(
            "Personel kendi karnesini yalnızca yayın sonrası görebilir.",
            "Yönetici sadece yetkili olduğu kapsamın karnelerini ve özetlerini görebilir.",
            "Geçmiş yıl karne/puan arşivinde yıl, dönem ve personel bazlı filtreleme yapılır.",
            "Karne içinde nihai puan, kriter özeti, amir görüşleri ve süreç bilgileri kurumsal dille gösterilmelidir.",
        ),
        warnings=("Yayınlanmamış karne personele açılmaz.", "Kişi detayı içeren performans bilgisi yetkisiz kullanıcıya gösterilmez."),
        checks=("Karne ekranında faz, sync, workflow state, draft gibi teknik ifadeler görünmemelidir.",),
        actions=(("Karne Arşivi", "/performance/scorecards/archive"),),
    ),
    Topic(
        key="performance_note",
        module="Performans Yönetimi",
        title="Performans notu verme / dönem içi gözlem",
        keywords=("performans notu", "not nasil verilir", "not nasıl verilir", "not ver", "not gir", "not ekle", "not dus", "not düş", "not düşmek", "olay notu", "gozlem notu", "gözlem notu", "ara not", "ara geri bildirim", "donem ici not", "dönem içi not", "olumlu not", "olumsuz not", "gelisim notu", "gelişim notu", "personel hakkinda not", "personel hakkında not"),
        menu_path="Performans Yönetimi > Dönem İçi Notlar",
        roles=("Amir", "Koordinatör", "Grup Başkanı", "Performans Yetkilisi", "Admin"),
        steps=(
            "Performans Yönetimi bölümüne girin.",
            "Dönem İçi Notlar sekmesini açın.",
            "Yeni Not / Not Ekle butonuna basın.",
            "İlgili dönem ve personeli seçin.",
            "Not türünü seçin: olumlu gözlem, olumsuz gözlem, başarı, gelişim ihtiyacı veya genel not.",
            "Açıklama alanına somut olayı, tarihi ve varsa kısa gelişim önerisini yazın.",
            "Kaydedin; notun ilgili personel ve dönem altında göründüğünü kontrol edin.",
        ),
        warnings=(
            "Bu ekran puan verme ekranı değildir; performans notu, dönem içindeki gözlem/ara geri bildirim kaydıdır.",
            "Notlar otomatik performans puanı üretmez; puanlama döneminde amire hatırlatma ve gelişim desteği sağlar.",
            "Performans puanı, amir kanaati veya hassas kişisel içerik asistan tarafından gösterilmez; yetkili kullanıcı ilgili ekranda işlem yapar.",
        ),
        checks=(
            "Not doğru dönem ve doğru personel altında görünüyor mu kontrol edin.",
            "Notun karneye yansıyıp yansımayacağı sistem ayarı ve yetki kuralına göre kontrol edilmelidir.",
        ),
        actions=(("Dönem İçi Notlar", "/performance/interim-notes"), ("Gelişim Rehberi", "/performance/meeting-development/faz10")),
        aliases=("not", "performans notu", "dönem içi not", "gözlem", "ara geri bildirim"),
        score_boost=14,
    ),
    Topic(
        key="notes_development",
        module="Performans Yönetimi",
        title="Dönem içi notlar ve gelişim önerisi",
        keywords=("donem ici not", "dönem içi not", "performans notu", "not nasil verilir", "not nasıl verilir", "not ver", "not gir", "not ekle", "ara geri bildirim", "gelisim onerisi", "gelişim önerisi", "olumlu olay", "olumsuz olay", "olay notu", "gozlem notu", "gözlem notu", "gelisim ihtiyaci", "gelişim ihtiyacı"),
        menu_path="Performans Yönetimi > Dönem İçi Notlar / Gelişim Rehberi",
        roles=("Amir", "Koordinatör", "Grup Başkanı", "Performans Yetkilisi", "Admin"),
        steps=(
            "Dönem içi not ekranına girin.",
            "Personeli ve ilgili dönemi seçin.",
            "Olumlu/olumsuz olay, başarı, gelişim ihtiyacı veya genel gözlem notunu ekleyin.",
            "Gelişim önerisi varsa rehber not olarak kaydedin.",
            "Puanlama döneminde bu notların amire hatırlatma olarak görünmesini kontrol edin.",
        ),
        warnings=("Bu notlar otomatik puan üretmez; sadece değerlendirme ve gelişim sürecine destek olur.",),
        checks=("Notun yetki sınırı doğru mu, karneye yansıyıp yansımayacağı ayarı açık mı kontrol edin.",),
        actions=(("Dönem İçi Notlar", "/performance/interim-notes"),),
    ),
    Topic(
        key="reports_dashboard",
        module="Raporlama / Dashboard",
        title="Raporlar ve yönetici dashboardları",
        keywords=("rapor", "performans dashboard", "performans raporu", "yonetici paneli", "yönetici paneli", "canli performans haritasi", "canlı performans haritası", "riskli personel", "geciken amir", "analiz", "grafik"),
        menu_path="Performans Yönetimi > Dashboard / Raporlar",
        roles=("Başkan", "Üst Yönetim", "Grup Başkanı", "Koordinatör", "Admin", "Performans Yetkilisi"),
        steps=(
            "Performans Dashboard veya Performans Raporları ekranına girin.",
            "Dönem, birim, üst birim, kategori veya amir filtresini seçin.",
            "Tamamlanma oranı, geciken amirler, riskli personel, düşük performans yoğunluğu ve kategori ortalamalarını inceleyin.",
            "Yetki kapsamınız dışında kalan kişi detayları görünmemelidir.",
        ),
        warnings=("Raporlar yöneticiye karar destek sağlar; otomatik idari karar üretmez.",),
        checks=("Başkan/Admin genel görünüm alırken koordinatör ve grup başkanı sadece kendi kapsamını görmelidir.",),
        actions=(("Performans Dashboard", "/performance/dashboard"), ("Raporlar", "/performance/reports")),
    ),
    Topic(
        key="role_matrix",
        module="Sistem Ayarları",
        title="Rol matrisi ve menü görünürlüğü",
        keywords=("rol matrisi", "menu gorunmuyor", "menü görünmüyor", "sekme gorunmuyor", "sekme görünmüyor", "yetki", "ayarlar", "ac kapat", "aç kapat", "personelde gorunmuyor", "personelde görünmüyor", "menu kapali", "menü kapalı"),
        menu_path="Sistem Ayarları > Rol Matrisi / Menü Görünürlüğü",
        roles=("Admin", "Sistem Yöneticisi", "Yetkilendirilmiş ayar kullanıcısı"),
        steps=(
            "Sistem Ayarları bölümüne girin.",
            "Modül Bazlı Rol Matrisi veya ilgili modülün rol matrisi ekranını açın.",
            "Rol, kişi veya birim bazlı görünürlük ayarını kontrol edin.",
            "Menü açık değilse ilgili sekmeyi role/kişiye/birime açın.",
            "Kaydedin ve kullanıcının oturumunu yenileyerek menünün gerçekten görünüp görünmediğini test edin.",
            "Backend route yetkisini de kontrol edin; sadece menüyü göstermek yeterli değildir.",
        ),
        warnings=("Kapalı sekmeler sol menüde hiç görünmemelidir; tıklayınca erişim engeli vermesi tek başına yeterli değildir.", "Kritik yetki değişiklikleri audit log’a düşmelidir."),
        checks=("Menü görünürlüğü, route erişimi ve veri yetkisi birlikte çalışıyor mu kontrol edin.",),
        actions=(("Sistem Ayarları", "/settings"), ("Rol Matrisi", "/admin/role-matrix")),
        aliases=("menu", "menü", "sekme", "yetki"),
        score_boost=7,
    ),
    Topic(
        key="assistant_training",
        module="BYS360 Asistanı Modülü",
        title="BYS360 Asistanı’nı eğitme / bilgi bankası",
        keywords=("asistani egit", "asistanı eğit", "bilgi bankasi", "bilgi bankası", "cevap veremiyor", "soru anlamiyor", "soru anlamıyor", "asistan bilgisi", "asistan ogretim", "asistan öğretim", "bunu ogren", "bunu öğren"),
        menu_path="BYS360 Asistanı Modülü > Öğretim Merkezi / Bilgi Bankası",
        roles=("Admin", "Sistem Yöneticisi", "Yetki verilmiş öğretim merkezi kullanıcısı"),
        steps=(
            "Asistan Öğretim Merkezi veya bilgi bankası ekranını açın.",
            "Kullanıcının yazabileceği doğal cümleleri örnek soru olarak ekleyin.",
            "Doğru modül, doğru ekran, adım adım işlem ve güvenlik sınırını cevap alanına yazın.",
            "Etiketleri ekleyin: personel, performans, rol matrisi, karne, başkan onayı gibi.",
            "Kaydedin ve aynı soruyu farklı cümlelerle test edin.",
        ),
        warnings=("Asistan idari karar, performans puanı veya hassas veri üretmeyi öğrenmemelidir.", "Öğretim merkezi rol matrisiyle kontrol edilmelidir."),
        checks=("Yeni bilgi kaydı hem kısa hem günlük dilde hem de BYS360 sınırlarına uygun cevap veriyor mu test edin.",),
        actions=(("Asistan Öğretim Merkezi", "/ai-agent/knowledge"),),
    ),
    Topic(
        key="communication_survey_support",
        module="İletişim ve Anket Yönetimi",
        title="Mesaj, duyuru, anket ve destek süreçleri",
        keywords=("mesaj", "duyuru", "bildirim", "anket", "destek", "yardim merkezi", "yardım merkezi", "talep", "okunmamis", "okunmamış", "geri bildirim"),
        menu_path="İletişim ve Anket Yönetimi / Destek Talepleri",
        roles=("Personel", "Yönetici", "Yetkili birim", "Admin"),
        steps=(
            "İlgili işlem için İletişim, Anket veya Destek ekranına girin.",
            "Mesaj için konuşma başlatın; duyuru için hedef kitleyi seçin; anket için soru ve atama bilgilerini girin.",
            "Destek talebi için kategori, konu ve açıklamayı doldurun.",
            "Kaydedin ve ilgili kullanıcılara bildirim gittiğini kontrol edin.",
        ),
        warnings=("Asistan mesaj metni, anket cevabı veya destek talebi içeriğini doğrudan göstermez; sadece sayı/özet ve yönlendirme verir.",),
        checks=("Yetkisiz kullanıcılar özel konuşma, açık uçlu anket cevabı veya destek eklerini görmemelidir.",),
        actions=(("Destek Talepleri", "/support"), ("Anketler", "/surveys"), ("Mesajlar", "/messages")),
    ),
    Topic(
        key="ai_decision",
        module="AI Karar Destek",
        title="AI Karar Destek Merkezi",
        keywords=("ai karar destek", "yapay zeka", "yapay zekâ", "analiz", "ozetle", "özetle", "risk farkindaligi", "risk farkındalığı", "oneriler", "öneriler", "ai"),
        menu_path="AI Karar Destek Merkezi",
        roles=("Başkan", "Üst Yönetim", "Yetkili yönetici", "Admin"),
        steps=(
            "AI Karar Destek Merkezi ekranına girin.",
            "Yetkili olduğunuz rapor, dönem, anket, destek veya performans verisini seçin.",
            "Sistem özet, dikkat notu veya önceliklendirme sunar.",
            "Çıktıyı karar gibi değil, yöneticinin değerlendirmesine yardımcı not olarak ele alın.",
        ),
        warnings=("AI karar vermez; nihai idari karar insana aittir.", "Hassas veri ve kişisel içerikler maskeleme/yetki sınırlarıyla korunmalıdır."),
        checks=("AI çıktısının hangi veri türüne dayandığı anlaşılır mı ve yetki sınırı korunuyor mu kontrol edin.",),
        actions=(("AI Karar Destek", "/ai/decision-support"),),
    ),
    Topic(
        key="kpi_targets",
        module="KPI / Hedef Yönetimi",
        title="KPI ve hedef yönetimi",
        keywords=("kpi dashboard", "kpi dashboardu", "hedef dashboard", "kpi panel", "kpi", "hedef", "hedef karti", "hedef kartı", "hedef donemi", "hedef dönemi", "stratejik hedef", "gerceklesme", "gerçekleşme", "riskli kpi"),
        menu_path="KPI / Hedef Yönetimi",
        roles=("Başkan", "Üst Yönetim", "Koordinatör", "Grup Başkanı", "Admin"),
        steps=(
            "Hedef dönemi oluşturun veya mevcut dönemi seçin.",
            "Hedef kartı için hedef adı, sahip, hedef değer, gerçekleşen değer, ağırlık ve tarih aralığını girin.",
            "KPI ölçüm mantığıyla gerçekleşme oranını takip edin.",
            "Dashboard üzerinden riskli veya geciken hedefleri izleyin.",
        ),
        warnings=("KPI hedefleri performans puanını otomatik belirlemez; karar destek ve ölçüm altyapısı sağlar.",),
        checks=("Hedefin sahibi, kapsamı, ağırlığı ve gerçekleşme değeri doğru mu kontrol edin.",),
        actions=(("KPI Dashboardu", "/performans/stratejik/kpi-dashboard"),),
        score_boost=10,
    ),
    Topic(
        key="access_problem",
        module="Sistem Ayarları",
        title="Erişim yok / menü kayboldu / beyaz sayfa",
        keywords=("erisemiyorum", "erişemiyorum", "erisim engeli", "erişim engeli", "beyaz sayfa", "menu kayboldu", "menü kayboldu", "sayfa acilmiyor", "sayfa açılmıyor", "sekme yok", "yetkim yok", "gorunmuyor", "görünmüyor"),
        menu_path="Sistem Ayarları > Rol Matrisi / Menü Görünürlüğü + log kontrolü",
        roles=("Admin", "Sistem Yöneticisi"),
        steps=(
            "Önce kullanıcının rolünü, kişi bazlı yetkisini ve birim bazlı menü profilini kontrol edin.",
            "İlgili modül anahtarı kapalı mı bakın.",
            "Sol menü görünürlüğü ile backend route yetkisi aynı mı kontrol edin.",
            "Yetkisiz kullanıcı için beyaz sayfa yerine kurumsal erişim engeli ekranı çalışmalı.",
            "500/beyaz sayfa varsa uygulama loglarında template, route veya import hatası arayın.",
        ),
        warnings=("Menünün görünmemesi bazen doğru davranıştır; ancak yetkili kullanıcıda görünmüyorsa rol matrisi veya ayar katmanı bozulmuş olabilir.",),
        checks=("Aynı kullanıcıyla oturumu yenileyip menü ve URL erişimini birlikte test edin.",),
        actions=(("Rol Matrisi", "/admin/role-matrix"), ("Sistem Ayarları", "/settings")),
        score_boost=6,
    ),
    Topic(
        key="security_kvkk",
        module="Güvenlik ve Uyum",
        title="Güvenlik, KVKK ve hassas veri sınırları",
        keywords=("kvkk", "guvenlik", "güvenlik", "hassas veri", "captcha", "audit", "log", "sifre", "şifre", "oturum", "yetkisiz veri"),
        menu_path="Sistem Ayarları > Güvenlik Ayarları / Audit Log",
        roles=("Admin", "Sistem Yöneticisi", "Güvenlik yetkilisi"),
        steps=(
            "Güvenlik Ayarları ekranında oturum, parola, CAPTCHA ve dosya yükleme sınırlarını kontrol edin.",
            "Kritik ayar ve yetki değişikliklerinin audit log’a düştüğünü doğrulayın.",
            "AI ve Asistan görünürlüğünün rol/yetki sınırına bağlı olduğundan emin olun.",
        ),
        warnings=("Asistan kişisel veri, performans puanı, amir kanaati, mesaj içeriği, anket cevabı veya destek talebi metni göstermez.",),
        checks=("Yetkisiz erişim, menü görünürlüğü ve log kayıtları birlikte test edilmelidir.",),
        actions=(("Güvenlik Ayarları", "/admin/security"), ("Audit Log", "/admin/audit-logs")),
    ),
)

SENSITIVE_PATTERNS = (
    # BYS360_ASSISTANT_V32_2_SENSITIVE_CONTENT_GUARD
    # Doğrudan veri gösterme/okuma/listeleme isteği + hassas içerik terimi birlikte yakalanır.
    r"(?=.*\b(goster|göster|gostermek|göstermek|ver|ac|aç|goruntule|görüntüle|goruntulemek|görüntülemek|gormek|görmek|bak|listele|paylas|paylaş|oku|indir|kopyala)\b)(?=.*\b(performans\s+puan\w*|performans\s+sonuc\w*|puan\w*|notun\w*|notunu\w*|karnesin\w*|karne\w*|amir\s+gorus\w*|amir\s+görüş\w*|yonetici\s+gorus\w*|yönetici\s+görüş\w*|anket\s+cevab\w*|anket\s+cevap\w*|anket\s+yanit\w*|anket\s+yanıt\w*|mesaj\s+icerig\w*|mesaj\s+içerig\w*|mesaj\s+içeriğ\w*|mesaj\s+metn\w*|mesaj\s+yazism\w*|mesaj\s+yazışm\w*|mesajlar\w*|ozel\s+mesaj\w*|özel\s+mesaj\w*|tc\b|kimlik\s+no\w*|telefon\w*|adres\w*|maas\w*|maaş\w*|dogum\s+tarih\w*|doğum\s+tarih\w*)\b).*",
    r"\b(performans puani belirle|performans puanı belirle|isimi sonlandir|işimi sonlandır|isten cikar|işten çıkar|idari karar ver)\b",
    r"\b(kim ne yazmis|kim ne yazmış|ozel mesaj|özel mesaj)\b",
)
OUT_OF_SCOPE_HINTS = ("hava durumu", "borsa", "dolar", "euro", "haber", "film", "yemek tarifi", "siyaset", "futbol", "magazin")


def _contains_sensitive_request(normalized: str) -> bool:
    return any(re.search(pattern, normalized) for pattern in SENSITIVE_PATTERNS)


def _is_out_of_scope(normalized: str) -> bool:
    return any(hint in normalized for hint in OUT_OF_SCOPE_HINTS)

def _question_universe_answer_v31_5() -> str:
    return (
        "BYS360 sınırları içinde bana günlük dille soru sorabilirsiniz. Ben gerçek ekran adını, işlem sırasını, yetki ihtimalini ve güvenlik sınırını anlatırım.\n\n"
        "**Genel:** BYS360 nedir, Ana Sayfa ne işe yarar, Dashboard ne işe yarar, bu sayfada ne yapılır, nereden başlayacağım?\n"
        "**Personel:** kişi nasıl eklenir, sicil no neden önemli, personelin birimi/yöneticisi nasıl güncellenir, personel neden görünmüyor?\n"
        "**İzin–Vekâlet:** izin nasıl girilir, devamsızlık nasıl kaydedilir, vekâlet nasıl tanımlanır, amir izinliyse görev ne olur?\n"
        "**Performans:** dönem nasıl açılır, Dönemler nerede, Sorular / Kriterler nasıl eklenir, Değerlendirme Görevleri nasıl oluşturulur, Görevlerim ekranında ne yapılır, puanlama nasıl yapılır, performans notu nasıl verilir, Dönem İçi Notlar nasıl kullanılır, Gelişim Rehberi ne işe yarar, 70 altı sonuç ne olur, Başkan Onayları nerede, Yayın Ön Onayı nedir, Not Karnesi neden görünmüyor, Geçmiş Karne Arşivi nasıl kullanılır?\n"
        "**Ayarlar:** menü görünmüyor, sekme açılmıyor, Rol Matrisi nasıl çalışır, kişi bazlı yetki nasıl verilir, kapalı sekmeler neden görünmemeli?\n"
        "**İletişim–Anket–Destek:** mesaj nasıl gönderilir, duyuru nasıl oluşturulur, anket nasıl yanıtlanır, destek talebi nasıl açılır, bildirimler nerede?\n"
        "**AI/KPI:** AI Karar Destek ne işe yarar, AI karar verir mi, KPI Dashboardu nerede, hedef kartı nasıl takip edilir?\n\n"
        "Sınırım şudur: performans puanı, amir görüşü, mesaj metni, anket cevabı veya yetkisiz kişisel veri göstermem; sizi ilgili yetkili ekrana yönlendiririm."
    )

def _smalltalk(normalized: str, name: str) -> Optional[str]:
    if re.search(r"\b(hangi sorular|hangi sorulari|hangi soruları|ne sorabilirim|neler sorabilirim|soru listesi|ornek sorular|örnek sorular|insan ne sorar|hangi konular|soru havuzu|bys360da ne sorulur|bys360 da ne sorulur)\b", normalized):
        return _question_universe_answer_v31_5()
    if not normalized:
        return "Buradayım. BYS360 içinde yapmak istediğiniz işlemi yazın; sizi doğru ekrana ve adımlara yönlendireyim."
    if re.search(r"\b(selam|merhaba|gunaydin|günaydın|iyi aksamlar|iyi akşamlar|iyi gunler|iyi günler)\b", normalized):
        suffix = f" {name}" if name else ""
        return f"Merhaba{suffix}. BYS360 içinde hangi işlemde yardımcı olayım? Örneğin personel ekleme, performans dönemi açma, rol matrisi, karne, Başkan Onayı, anket veya destek talebi diyebilirsiniz."
    if re.search(r"\b(nasilsin|nasılsın|iyi misin|naber|ne haber)\b", normalized):
        return "İyiyim, teşekkür ederim. BYS360’da takıldığınız işlemi yazın; günlük dille anlatsanız da ne yapmak istediğinizi anlayıp adım adım yönlendireceğim."
    if re.search(r"\b(seni kim|kim gelistirdi|kim geliştirdi|kim yaptı|kim yapti|gelistiren kim|geliştiren kim)\b", normalized):
        return "Ben BYS360 Asistanı Modülü olarak, BYS360 projesi kapsamında kurum içi kullanım rehberliği vermek için tasarlandım. Amacım kullanıcıyı doğru ekrana, doğru işlem sırasına ve yetki sınırları içinde güvenli bilgiye yönlendirmek."
    if re.search(r"\b(neler yapabilirsin|ne yaparsin|ne yaparsın|ne işe yararsın|ne ise yararsin)\b", normalized):
        return "BYS360 içinde personel, izin, vekâlet, performans, karne, Başkan Onayı, rol matrisi, menü görünürlüğü, anket, destek, bildirim, AI Karar Destek ve KPI/Hedef süreçlerinde size adım adım rehberlik edebilirim. Hassas veri göstermem, idari karar vermem ve performans puanı belirlemem."
    return None


def _score_topic(topic: Topic, normalized: str) -> int:
    if not normalized:
        return 0
    score = topic.score_boost
    for kw in topic.keywords + topic.aliases:
        nkw = _tr(kw)
        if not nkw:
            continue
        if nkw in normalized:
            score += 8 + len(nkw.split())
        else:
            parts = [p for p in nkw.split() if len(p) > 2]
            hits = sum(1 for p in parts if p in normalized)
            if hits:
                score += hits
    for token in normalized.split():
        if len(token) > 3 and any(token in _tr(k) for k in topic.keywords):
            score += 1
    return score


def _best_topics(normalized: str, limit: int = 3) -> List[Tuple[int, Topic]]:
    scored = [(_score_topic(topic, normalized), topic) for topic in TOPICS]
    scored = [(score, topic) for score, topic in scored if score > 0]
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[:limit]


def _format_topic_answer(topic: Topic, user: Any, question: str, alternates: List[Topic]) -> Dict[str, Any]:
    role = _role_name(user)
    topic_module = _canonical_ui_text_v31_4(topic.module)
    topic_title = _canonical_ui_text_v31_4(topic.title)
    topic_menu_path = _canonical_ui_text_v31_4(topic.menu_path)
    who = "\n".join(f"- {_canonical_ui_text_v31_4(r)}" for r in topic.roles)
    steps = "\n".join(f"{idx}. {_canonical_ui_text_v31_4(step)}" for idx, step in enumerate(topic.steps, 1))
    warnings = "\n".join(f"- {_canonical_ui_text_v31_4(w)}" for w in topic.warnings) if topic.warnings else "- Bu işlemde yetki ve görünürlük sınırı korunmalıdır."
    checks = "\n".join(f"- {_canonical_ui_text_v31_4(c)}" for c in topic.checks) if topic.checks else "- İşlem sonrası kaydın doğru ekranda göründüğünü kontrol edin."
    alt_text = ""
    if alternates:
        alt_names = ", ".join(f"{_canonical_ui_text_v31_4(alt.module)}: {_canonical_ui_text_v31_4(alt.title)}" for alt in alternates[:2])
        alt_text = f"\n\nBenzer olabilecek diğer başlıklar: {alt_names}. Yanlış anladıysam sadece yapmak istediğiniz işlemi bir cümleyle tekrar yazın."
    answer = (
        f"Anladım. Bu konu **{topic_module}** içindedir: **{topic_title}**.\n\n"
        f"**Nereden gidilir?**\n{topic_menu_path}\n\n"
        f"**Kim yapabilir?**\n{who}\n\n"
        f"**Adım adım:**\n{steps}\n\n"
        f"**Dikkat:**\n{warnings}\n\n"
        f"**Kontrol:**\n{checks}{alt_text}"
    )
    return {
        "ok": True,
        "marker": V31_MARKER,
        "engine": "bys360-assistant-chatgpt-like-v31",
        "mode": "guided_answer",
        "topic": topic.key,
        "module": topic_module,
        "title": topic_title,
        "role_scope": role,
        "answer": answer,
        "actions": [{"label": _canonical_ui_text_v31_4(label), "url": url} for label, url in topic.actions],
        "quick_replies": [_canonical_ui_text_v31_4(alt.title) for alt in alternates[:3]],
        "notice": "BYS360 sınırları içinde güvenli rehberlik sağlandı.",
    }


def _safe_block_answer(reason: str) -> Dict[str, Any]:
    if reason == "sensitive":
        answer = (
            "Bu bilgiyi doğrudan gösteremem. BYS360 Asistanı; performans puanı, amir görüşü, mesaj içeriği, anket cevabı, "
            "TC/telefon/adres gibi kişisel veya hassas verileri paylaşmaz.\n\n"
            "Yapabileceğim şey şu: yetkiniz varsa ilgili modül ekranına yönlendirebilirim. Performans sonucu için "
            "Performans Yönetimi > Not Karnesi / Geçmiş Karne Arşivi veya yetkili yönetici ekranı kullanılmalıdır. "
            "Yetki yoksa Rol Matrisi ve kişi bazlı menü izni kontrol edilmelidir."
        )
    else:
        answer = (
            "Bu soru BYS360 kapsamının dışında görünüyor. Ben kurum içi BYS360 kullanımı için; personel, performans, izin, vekâlet, "
            "rol matrisi, menü görünürlüğü, anket, destek, bildirim, AI Karar Destek ve KPI/Hedef süreçlerinde yardımcı olurum."
        )
    return {"ok": True, "marker": V31_MARKER, "engine": "bys360-assistant-chatgpt-like-v31", "mode": "safe_boundary", "answer": answer, "actions": [], "quick_replies": ["Personel ekleme", "Performans dönemi açma", "Rol matrisi", "Başkan Onayı"], "notice": "Güvenli sınır uygulandı."}

def _topic_by_key(key: str) -> Optional[Topic]:
    for topic in TOPICS:
        if topic.key == key:
            return topic
    return None


def _context_path(context: Optional[Dict[str, Any]]) -> str:
    if not isinstance(context, dict):
        return ""
    for key in ("path", "pathOnly", "pathname", "href", "url"):
        value = context.get(key)
        if value:
            return str(value).split("?")[0].split("#")[0].strip().lower()
    return ""


def _is_page_help_intent(normalized: str) -> bool:
    return bool(re.search(r"\b(bu sayfa|bu ekran|burada ne|ne yapilir|ne yapilir|ne yapılır|hangi ekran|neredeyim|sayfayi tanit|sayfayı tanıt)\b", normalized or ""))


def _contextual_page_topic(normalized: str, context: Optional[Dict[str, Any]]) -> Optional[Topic]:
    path = _context_path(context)
    if not _is_page_help_intent(normalized) and normalized not in ("ana sayfa", "anasayfa", "dashboard", "genel dashboard"):
        return None
    if path in ("/", "/home"):
        return _topic_by_key("home_page")
    if path == "/dashboard":
        return _topic_by_key("general_dashboard")
    for prefix, key in PAGE_TOPIC_PREFIXES_V32:
        if path == prefix or path.startswith(prefix + "/"):
            return _topic_by_key(key)
    return None


PAGE_TOPIC_PREFIXES_V32: Tuple[Tuple[str, str], ...] = (
    ("/performance/dashboard", "reports_dashboard"),
    ("/performans/dashboard", "reports_dashboard"),
    ("/performance/periods", "period_create"),
    ("/performance/period-management", "period_create"),
    ("/performance/criteria", "criteria"),
    ("/performance/questions", "criteria"),
    ("/performance/weights", "weights"),
    ("/performance/evaluation-tasks", "task_generation"),
    ("/performance/tasks", "task_generation"),
    ("/performance/my-evaluations", "scoring"),
    ("/performance/president-approvals", "low_performance"),
    ("/performance/personnel-support-publish-approvals", "publish_preapproval"),
    ("/performance/scorecard", "scorecard"),
    ("/performance/interim-notes", "performance_note"),
    ("/performance/development", "notes_development"),
    ("/performance/reports", "reports_dashboard"),
    ("/performans/stratejik/kpi-dashboard", "kpi_targets"),
    ("/performans/stratejik", "kpi_targets"),
    ("/personnel", "person_add"),
    ("/admin/users", "person_add"),
    ("/hr-management/leave", "leave"),
    ("/leave", "leave"),
    ("/delegation", "delegation"),
    ("/settings/role-matrix", "role_matrix"),
    ("/admin/role-matrix", "role_matrix"),
    ("/settings", "access_problem"),
    ("/support", "communication_survey_support"),
    ("/surveys", "communication_survey_support"),
    ("/messages", "communication_survey_support"),
    ("/ai/decision-support", "ai_decision"),
    ("/ai-agent/panel", "assistant_training"),
    ("/ai-agent/knowledge", "assistant_training"),
    ("/ai-agent/teaching-center", "assistant_training"),
)


def _normalize_actions_v32(actions: Any) -> List[Dict[str, str]]:
    safe: List[Dict[str, str]] = []
    if not isinstance(actions, list):
        return safe
    for item in actions[:4]:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("title") or "İlgili ekrana git").strip()
        url = str(item.get("url") or item.get("href") or item.get("route") or "").strip()
        if not url.startswith("/") or url.startswith("//"):
            continue
        safe.append({"label": _canonical_ui_text_v31_4(label), "url": url})
    return safe


def _knowledge_reply_v32(user: Any, raw: str) -> Optional[Dict[str, Any]]:
    if not raw or len(_tr(raw)) < 3:
        return None
    try:
        from app.services.ai_agent.knowledge import build_knowledge_reply
        result = build_knowledge_reply(user, raw)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return None
    if not isinstance(result, dict):
        return None
    answer = str(result.get("answer") or "").strip()
    if not answer:
        return None
    return {
        "ok": True,
        "marker": V32_MARKER,
        "engine": "bys360-assistant-advanced-intelligence-v32-knowledge-bridge",
        "mode": "knowledge_guided_answer",
        "answer": _canonical_ui_text_v31_4(answer),
        "actions": _normalize_actions_v32(result.get("actions") or result.get("suggested_actions") or []),
        "quick_replies": result.get("quick_replies") or ["Bu sayfada ne yapılır?", "Menü görünmüyor", "Performans dönemi nasıl açılır?"],
        "notice": "BYS360 bilgi bankası ve güvenli rehberlik katmanı kullanıldı.",
    }


def _fallback_answer(user: Any, question: str, legacy_builder: Optional[Callable[..., Any]] = None) -> Dict[str, Any]:
    if callable(legacy_builder):
        try:
            legacy = legacy_builder(user, question)
            if isinstance(legacy, dict) and str(legacy.get("answer", "")).strip():
                legacy["answer"] = _canonical_ui_text_v31_4(legacy.get("answer", ""))
                legacy.setdefault("marker", V31_MARKER)
                legacy.setdefault("engine", "bys360-assistant-chatgpt-like-v31-legacy-bridge")
                return legacy
            if isinstance(legacy, str) and legacy.strip():
                return {"ok": True, "marker": V31_MARKER, "engine": "bys360-assistant-chatgpt-like-v31-legacy-bridge", "answer": _canonical_ui_text_v31_4(legacy)}
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/ai_agent/assistant_chatgpt_like_v31.py)")
    return {
        "ok": True,
        "marker": V31_MARKER,
        "engine": "bys360-assistant-chatgpt-like-v31",
        "mode": "clarifying_fallback",
        "answer": (
            "Anladım, bunu BYS360 kapsamında yorumlamaya çalışıyorum. En yakın başlıklar şunlar olabilir: "
            "Personel işlemleri, Performans Yönetimi, Rol Matrisi, Menü Görünürlüğü, Anket/Destek, AI Karar Destek veya KPI/Hedef. "
            "Yapmak istediğiniz işlemi tek cümleyle yazarsanız sizi doğrudan doğru ekrana ve işlem sırasına yönlendireceğim."
        ),
        "actions": [],
        "quick_replies": ["Kişi nasıl eklenir?", "Performans dönemi nasıl açılır?", "Menü neden görünmüyor?", "70 altı sonuç ne olur?"],
    }


def build_bys360_assistant_chatgpt_like_reply_v31(
    user: Any,
    question: str,
    *,
    legacy_builder: Optional[Callable[..., Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    raw = (question or "").strip()
    normalized = _tr(raw)
    name = _display_name(user).split(" ")[0] if _display_name(user) else ""

    if _contains_sensitive_request(normalized):
        return _safe_block_answer("sensitive")
    if _is_out_of_scope(normalized):
        return _safe_block_answer("out_of_scope")

    contextual_topic = _contextual_page_topic(normalized, context)
    if contextual_topic:
        result = _format_topic_answer(contextual_topic, user, raw, [])
        result["marker"] = V32_MARKER
        result["engine"] = "bys360-assistant-advanced-intelligence-v32-page-context"
        result["mode"] = "page_context_guidance"
        return result

    talk = _smalltalk(normalized, name)
    if talk:
        return {"ok": True, "marker": V32_MARKER, "engine": "bys360-assistant-advanced-intelligence-v32", "mode": "smalltalk", "answer": talk, "actions": [], "quick_replies": ["Personel ekleme", "Performans dönemi açma", "Rol matrisi", "Başkan Onayı"]}

    knowledge = _knowledge_reply_v32(user, raw)
    if knowledge:
        return knowledge

    best = _best_topics(normalized, limit=4)
    if best and best[0][0] >= 4:
        return _format_topic_answer(best[0][1], user, raw, [t for _, t in best[1:]])

    return _fallback_answer(user, raw, legacy_builder)


def self_test() -> Dict[str, Any]:
    class U:
        role = "Admin"
        full_name = "Test Kullanıcı"

    samples = {
        "kişi nasıl eklenir": "Personel",
        "güvenlik personeline özel dönem açacağım": "Dönem",
        "personelde sekme görünmüyor rol matrisi çalışmıyor": "Rol matrisi",
        "70 altı performans sonucu ne olur": "Başkan",
        "personelin puanını göster": "gösteremem",
        "hangi sorular sorabilirim": "BYS360",
    }
    results = []
    ok = True
    for q, expected in samples.items():
        ans = build_bys360_assistant_chatgpt_like_reply_v31(U(), q)
        text = str(ans.get("answer", ""))
        passed = expected.lower() in text.lower()
        ok = ok and passed
        results.append({"question": q, "expected": expected, "passed": passed})
    return {"ok": ok, "marker": V31_MARKER, "results": results}
