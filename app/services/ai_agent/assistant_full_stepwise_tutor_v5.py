from __future__ import annotations

# BYS360_ASSISTANT_FULL_STEPWISE_TUTOR_V5

from dataclasses import dataclass, field
from typing import Any, Callable
import re

ASSISTANT_NAME = "BYS360 Asistanı"
VERSION = "BYS360 Asistanı Tam Öğretici Rehber Motoru V5"
MODE = "ChatGPT benzeri doğal dil anlama; yalnızca BYS360 sınırlarında adım adım güvenli yönlendirme"
SAFETY_NOTICE = (
    "BYS360 Asistanı idari karar üretmez, performans puanı belirlemez, onay/ret işlemi yapmaz, "
    "mesaj/anket/amir görüşü gibi hassas içerikleri dökmez ve yetki dışı veri göstermez."
)
TR_TABLE = str.maketrans({
    "ı": "i", "İ": "i", "I": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
    "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
    "â": "a", "î": "i", "û": "u",
})


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower().translate(TR_TABLE)
    text = re.sub(r"[^a-z0-9%]+", " ", text)
    return " ".join(text.split())


def _has(q: str, *phrases: str) -> bool:
    return any(_norm(p) in q for p in phrases if p)


def _has_all(q: str, *words: str) -> bool:
    return all(_norm(w) in q for w in words if w)


def _tokens(value: str) -> set[str]:
    stop = {"ve", "ile", "icin", "nasil", "nereden", "ne", "bir", "ben", "bana", "mi", "mu", "mı", "mü", "da", "de", "bu", "su", "şu"}
    return {t for t in _norm(value).split() if len(t) > 1 and t not in stop}


def _role_from_user(user: Any) -> str:
    values: list[str] = []
    for attr in ("role", "role_name", "role_key", "user_role", "authority_role", "position", "title", "unvan", "job_title", "display_role"):
        try:
            val = getattr(user, attr, None)
            if val:
                values.append(str(val))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/ai_agent/assistant_full_stepwise_tutor_v5.py)")
    try:
        if bool(getattr(user, "is_admin", False)) or bool(getattr(user, "is_superuser", False)):
            return "admin"
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/ai_agent/assistant_full_stepwise_tutor_v5.py)")
    joined = _norm(" ".join(values))
    if _has(joined, "sistem", "admin", "yonetici", "superuser"):
        return "admin"
    if _has(joined, "personel ve destek", "insan kaynak", "ik", "performans yetkilisi"):
        return "hr_performance"
    if _has(joined, "baskan yardimcisi", "ust yonetim"):
        return "upper_management"
    if _has(joined, "baskan"):
        return "president"
    if _has(joined, "grup baskani"):
        return "group_head"
    if _has(joined, "koordinator", "koordinat"):
        return "coordinator"
    if _has(joined, "amir", "degerlendirici"):
        return "supervisor"
    return "personnel"


def _role_label(role: str) -> str:
    return {
        "admin": "Sistem Yöneticisi / Admin",
        "president": "Başkan / Üst Yönetim",
        "upper_management": "Üst Yönetim",
        "hr_performance": "Personel veya Performans Yetkilisi",
        "group_head": "Grup Başkanı",
        "coordinator": "Koordinatör",
        "supervisor": "Amir / Değerlendirici",
        "personnel": "Standart Kullanıcı / Personel",
    }.get(role, "Kullanıcı")


def _scope_note(role: str) -> str:
    notes = {
        "admin": "Admin/Sistem Yöneticisi geniş ayar yapabilir; yine de her işlem audit ve rol-yetki mantığıyla izlenmelidir.",
        "president": "Başkan/Üst Yönetim kurumsal özet ve onay ekranlarına yetki dahilinde erişir; asistan onay/ret yapmaz.",
        "upper_management": "Üst Yönetim yalnızca yetkili olduğu kurumsal kapsam ve raporlara yönlendirilmelidir.",
        "hr_performance": "Personel/Performans yetkilisi dönem, görev, yayın ve personel süreçlerini rol matrisi izinleri kadar yönetebilir.",
        "group_head": "Grup Başkanı kendi grup/üst birim kapsamındaki kayıt ve ortalamalara yönlendirilmelidir.",
        "coordinator": "Koordinatör kendi çalışma grubu veya koordinasyon kapsamındaki işlemlerle sınırlıdır.",
        "supervisor": "Amir yalnızca kendisine atanmış değerlendirme görevleri ve yetkili personel kapsamını görmelidir.",
        "personnel": "Personel yalnızca kendi hesabı, kendi talepleri, kendi bildirimleri ve yayınlanmış kendi sonuçlarını görmelidir.",
    }
    return notes.get(role, "Yetki kapsamı rol matrisi ve kişi/birim bazlı ayarlara göre belirlenir.")


def _a(label: str, route: str, desc: str = "") -> dict[str, str]:
    return {
        "label": label,
        "title": label,
        "route": route,
        "url": route,
        "description": desc,
        "safety_level": "rehber_yonlendirme",
    }


@dataclass(frozen=True)
class Guide:
    key: str
    title: str
    module: str
    who: list[str]
    patterns: list[str]
    steps: list[str]
    attention: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)
    actions: list[dict[str, str]] = field(default_factory=list)
    next_questions: list[str] = field(default_factory=list)
    priority: int = 50


GUIDES: list[Guide] = [
    Guide(
        key="all_modules_overview",
        title="BYS360 tüm modüller nasıl kullanılır?",
        module="Genel Kullanım",
        who=["Tüm kullanıcılar"],
        patterns=["tum ozellik", "tum moduller", "her seyi ogret", "hic bilmiyorum", "nasil kullanirim", "bana sistemi ogret", "bütün özellik", "bana ogret", "baslangic", "nereden baslayayim", "chatgpt gibi"],
        steps=[
            "Ana sayfaya girin ve size açık olan menüleri kontrol edin.",
            "Yapmak istediğiniz işlemi normal cümleyle yazın: 'personel ekleyeceğim', 'performans dönemi açacağım', 'menü görünmüyor' gibi.",
            "Asistan önce niyetinizi anlar, sonra ilgili modülü seçer.",
            "Size işlem için gereken yetkiyi, ekran yolunu ve adımları sırayla verir.",
            "İşlem hassas veri veya idari karar içeriyorsa içerik göstermez; sizi yetkili ekrana yönlendirir.",
            "Takıldığınız yerde aynı konuşmada 'sonra ne yapacağım?' diye sorabilirsiniz.",
        ],
        attention=[
            "BYS360 Asistanı ChatGPT gibi doğal dili anlar; ancak yalnızca BYS360 işlemlerinde rehberlik eder.",
            "İdari karar, performans puanı, onay/ret, mesaj içeriği ve anket cevabı üretmez/göstermez.",
        ],
        checks=["Ana sayfada rolünüze uygun menüler görünmelidir.", "Görünmeyen menüler için rol matrisi ve kişi/birim bazlı yetkiler kontrol edilmelidir."],
        actions=[_a("Ana Sayfa", "/home"), _a("Yardım/Destek", "/support"), _a("BYS360 Asistanı Paneli", "/ai-agent/panel")],
        next_questions=["Personel nasıl eklenir?", "Performans dönemi nasıl oluşturulur?", "Menü görünmüyor ne yapmalıyım?", "Destek talebi nasıl açılır?"],
        priority=100,
    ),
    Guide(
        key="personnel_add",
        title="Personel nasıl eklenir?",
        module="Personel Yönetimi",
        who=["Admin", "Sistem Yöneticisi", "Personel Yönetimi Yetkilisi", "İK/Personel yetkilisi"],
        patterns=["personel ekle", "yeni personel", "personel kaydet", "calisan ekle", "sicil no", "personel olustur", "personel kaydi ac"],
        steps=[
            "Sol menüden Personel Yönetimi bölümüne girin.",
            "Personel Listesi veya Personel Ekle ekranını açın.",
            "Yeni Personel Ekle butonuna basın.",
            "Sicil No, ad, soyad, unvan/görev, birim, üst birim ve yönetici/amir alanlarını doldurun.",
            "Gerekiyorsa rol, menü görünürlüğü ve profil fotoğrafı alanlarını tamamlayın.",
            "Kaydet butonuna basın.",
            "Kayıt sonrası personelin listede göründüğünü ve birim/amir ilişkisinin doğru olduğunu kontrol edin.",
        ],
        attention=["TC yerine Sicil No mantığı kullanılmalıdır.", "Birim, üst birim ve yönetici alanı yanlışsa performans amir zinciri de yanlış üretilebilir."],
        checks=["Personel listede görünmeli.", "Personelin rol/menü görünürlüğü doğru olmalı.", "Performans görev üretiminde doğru amir zinciri oluşmalı."],
        actions=[_a("Personel Yönetimi", "/personnel"), _a("Yeni Personel", "/personnel/create"), _a("Rol Matrisi", "/admin/role-matrix")],
        next_questions=["Toplu personel yükleme nasıl yapılır?", "Birim ve yönetici ilişkisi nasıl kurulur?", "Rol matrisi nasıl çalışır?"],
        priority=92,
    ),
    Guide(
        key="personnel_import",
        title="Toplu personel yükleme nasıl yapılır?",
        module="Personel Yönetimi",
        who=["Admin", "Personel Yönetimi Yetkilisi"],
        patterns=["toplu personel", "excel yukle", "personel import", "personel listesi yukle", "excelden aktar", "toplu yukle"],
        steps=[
            "Personel Yönetimi içinde Toplu Yükleme / Import ekranını açın.",
            "Örnek formatı indirin veya mevcut Excel listesini BYS360 formatına uyarlayın.",
            "Sicil No, ad soyad, unvan, birim, üst birim, yönetici ve varsa kategori alanlarını kontrol edin.",
            "Dosyayı yükleyin ve ön izleme/validasyon sonucunu inceleyin.",
            "Hata veren satırları düzeltmeden kesin aktarım yapmayın.",
            "Aktarım sonrası personel sayısı, birim dağılımı ve amir zincirini kontrol edin.",
        ],
        attention=["Amir sicilleri boş veya hatalıysa performans görevleri yanlış üretilebilir."],
        checks=["Import raporunda hata kalmamalı.", "Personel listesi doğru sayıda oluşmalı.", "Görev üretimi öncesi organizasyon verisi temiz olmalı."],
        actions=[_a("Personel Import", "/personnel/import"), _a("Personel Yönetimi", "/personnel")],
        next_questions=["Personel kategorisi nedir?", "Görev üretimi nasıl yapılır?"],
        priority=82,
    ),
    Guide(
        key="org_unit_management",
        title="Birim, üst birim ve yönetici ilişkisi nasıl kurulur?",
        module="Personel Yönetimi / Sistem Ayarları",
        who=["Admin", "Sistem Yöneticisi", "Personel Yetkilisi"],
        patterns=["birim ekle", "ust birim", "organizasyon", "yonetici ata", "birim yoneticisi", "calisma grubu", "koordinator", "grup baskanligi"],
        steps=[
            "Sistem Ayarları veya Personel Yönetimi içindeki Organizasyon/Birimler ekranını açın.",
            "Yeni birim ekliyorsanız birim adı, üst birim ve birim türünü girin.",
            "Çalışma grubu, koordinatörlük ve grup başkanlığı ilişkilerini doğru hiyerarşiyle bağlayın.",
            "Birim yöneticisi/koordinatör alanlarını doldurun.",
            "Personeli ilgili birime bağlayın.",
            "Değişiklikten sonra personel organizasyon geçmişini ve performans amir zincirini kontrol edin.",
        ],
        attention=["Organizasyon değişikliği geçmiş kayıt ve performans görünürlüğünü etkileyebilir."],
        checks=["Birim listesinde üst-alt ilişki doğru görünmeli.", "Personelin birim ve yönetici bilgisi doğru olmalı."],
        actions=[_a("Organizasyon Birimleri", "/admin/organization-units"), _a("Personel Yönetimi", "/personnel")],
        next_questions=["Performans amir zinciri nasıl oluşur?", "Rol matrisi nasıl uygulanır?"],
        priority=80,
    ),
    Guide(
        key="leave_request",
        title="İzin talebi veya izin kaydı nasıl oluşturulur?",
        module="Personel Yönetimi / İzin Yönetimi",
        who=["Personel", "Amir", "Personel Yetkilisi"],
        patterns=["izin talebi", "izin gir", "izin kaydi", "izin olustur", "izin almak", "izin sureci", "personel izin"],
        steps=[
            "Personel Yönetimi veya İzin Yönetimi bölümüne girin.",
            "İzin Talebi / İzin Kaydı ekranını açın.",
            "Personeli ve izin türünü seçin.",
            "Başlangıç ve bitiş tarihlerini girin.",
            "Gerekli açıklama veya belge varsa ekleyin.",
            "Kaydet / Onaya Gönder butonuna basın.",
            "Onay süreci varsa ilgili amire veya yetkili birime düştüğünü kontrol edin.",
        ],
        attention=["İzinli amir varsa vekâlet ve performans görev akışı etkilenebilir."],
        checks=["İzin kaydı personel geçmişinde görünmeli.", "Onay bekleyen kayıt doğru kişiye düşmeli."],
        actions=[_a("İzin Yönetimi", "/personnel/leaves"), _a("Personel Yönetimi", "/personnel")],
        next_questions=["Vekâlet nasıl tanımlanır?", "İzin performans görevlerini etkiler mi?"],
        priority=75,
    ),
    Guide(
        key="delegation_assignment",
        title="Vekâlet nasıl tanımlanır?",
        module="Personel Yönetimi / Vekâlet",
        who=["Admin", "Personel Yetkilisi", "Yetkili Yönetici"],
        patterns=["vekalet", "vekâlet", "vekil ata", "yerine bakacak", "gorev devri", "görev devri", "amir izinli"],
        steps=[
            "Personel Yönetimi içinde Vekâlet Yönetimi ekranını açın.",
            "Asıl kişiyi seçin.",
            "Vekil olacak kişiyi seçin.",
            "Başlangıç ve bitiş tarihlerini girin.",
            "Vekâlet kapsamını belirleyin.",
            "Kaydedin ve ilgili süreçlerde vekilin görünüp görünmediğini kontrol edin.",
        ],
        attention=["Vekâlet yetki dışı veri açmamalı; yalnızca tanımlı kapsamda işlem yapılmalıdır."],
        checks=["Vekâlet listesinde aktif kayıt görünmeli.", "Performans/izin onaylarında doğru vekil devreye girmeli."],
        actions=[_a("Vekâlet Yönetimi", "/personnel/delegations")],
        next_questions=["İzinli amir varsa görevler ne olur?", "Rol matrisiyle vekâlet farkı nedir?"],
        priority=74,
    ),
    Guide(
        key="performance_period_create",
        title="Performans dönemi nasıl oluşturulur?",
        module="Performans Yönetimi",
        who=["Admin", "Sistem Yöneticisi", "Performans Yetkilisi", "Yetki verilmiş Personel/İK kullanıcısı"],
        patterns=[
            "performans donemi", "performans dönemi", "donem olustur", "dönem oluştur", "donem ac", "dönem aç", "degerlendirme donemi", "değerlendirme dönemi",
            "yeni donem", "yeni dönem", "2026 performans", "yillik performans", "yıllık performans", "guvenlik personeline ozel donem", "kategoriye ozel donem",
            "performans baslat", "performans başlat", "donem baslat", "dönem başlat", "performans donemi olusturmayi", "performans dönemi oluşturmayı"
        ],
        steps=[
            "Sol menüden Performans Yönetimi bölümüne girin.",
            "Dönem Yönetimi / Performans Dönemleri sekmesini açın.",
            "Yeni Dönem Oluştur butonuna basın.",
            "Dönem adını yazın. Örnek: 2026 Yıllık Performans Dönemi.",
            "Dönem türünü seçin: Yıllık, 6 aylık, 3 aylık, aylık veya özel dönem.",
            "Başlangıç ve bitiş tarihlerini girin.",
            "Kapsam tipini seçin: tüm kurum, birim, üst birim, kategori/grup veya seçili personel.",
            "Kapsam seçimine göre ilgili birim, kategori veya personelleri seçin.",
            "Aktiflik/durum bilgisini belirleyin ve Kaydet/Oluştur butonuna basın.",
            "Dönem listede göründükten sonra kriter, ağırlık ve görev üretimi adımlarına geçin.",
        ],
        attention=[
            "Dönem oluşturmak tek başına değerlendirmeyi başlatmaz; kriter, ağırlık ve görev üretimi de tamamlanmalıdır.",
            "Aynı personel için aynı tarih aralığında çakışan dönem varsa sistem uyarı vermelidir.",
            "Güvenlik/Temizlik gibi kategoriye özel dönem açılırsa görevler sadece o kapsamdaki personele üretilmelidir.",
        ],
        checks=["Dönem listede görünmeli.", "Kapsam etiketi doğru olmalı.", "Görev üretimi ekranında doğru personel kapsamı gelmeli."],
        actions=[_a("Performans Dönemleri", "/performance/periods"), _a("Yeni Dönem", "/performance/periods/create"), _a("Görev Üretimi", "/performance/assignments")],
        next_questions=["Performans kriteri nasıl eklenir?", "Ağırlık nasıl tanımlanır?", "Görev üretimi nasıl yapılır?"],
        priority=99,
    ),
    Guide(
        key="performance_criteria",
        title="Performans değerlendirme kriteri nasıl eklenir?",
        module="Performans Yönetimi",
        who=["Admin", "Performans Yetkilisi"],
        patterns=["kriter ekle", "degerlendirme kriter", "değerlendirme kriter", "performans kriter", "yetkinlik yerine", "kriter tanimla"],
        steps=[
            "Performans Yönetimi > Değerlendirme Kriterleri ekranına girin.",
            "Yeni Kriter Ekle butonuna basın.",
            "Kriter adını ve açıklamasını yazın.",
            "Aktiflik durumunu belirleyin.",
            "Gerekirse dönem, kategori veya rol bağlantısını seçin.",
            "Kaydedin ve ilgili dönem puanlama ekranında görünüp görünmediğini kontrol edin.",
        ],
        attention=["Ekran ana dili 'Değerlendirme Kriterleri' olmalı; 'Yetkinlik' ana terim olarak kullanılmamalıdır."],
        checks=["Kriter aktif listede görünmeli.", "Puanlama ekranında doğru sırada çıkmalı."],
        actions=[_a("Değerlendirme Kriterleri", "/performance/criteria")],
        next_questions=["Ağırlık nasıl tanımlanır?", "1 ve 5 puanda açıklama zorunlu mu?"],
        priority=84,
    ),
    Guide(
        key="performance_weights",
        title="Performans ağırlıkları nasıl tanımlanır?",
        module="Performans Yönetimi",
        who=["Admin", "Performans Yetkilisi"],
        patterns=["agirlik", "ağırlık", "puan agirligi", "amir agirligi", "yuzde", "1 amir 2 amir", "puan dagilimi"],
        steps=[
            "Performans Yönetimi > Ağırlık Ayarları ekranına girin.",
            "Dönem, rol grubu veya kapsam tipini seçin.",
            "1. amir, 2. amir ve varsa 3. amir ağırlıklarını girin.",
            "Toplamın %100 olduğundan emin olun.",
            "3. amir yorum modundaysa puan ağırlığını %0 kabul edin.",
            "Kaydedin ve deneme hesaplamasında nihai puanın doğru üretildiğini kontrol edin.",
        ],
        attention=["3. amir puan modundaysa toplam ağırlık yine %100 olmalıdır."],
        checks=["Ağırlık toplamı %100 olmalı.", "Yorum modundaki 3. amir puana dahil olmamalı."],
        actions=[_a("Ağırlık Ayarları", "/performance/weights")],
        next_questions=["3. amir kuralı nedir?", "Görev üretimi nasıl yapılır?"],
        priority=82,
    ),
    Guide(
        key="performance_task_generation",
        title="Performans görev üretimi nasıl yapılır?",
        module="Performans Yönetimi",
        who=["Admin", "Performans Yetkilisi"],
        patterns=["gorev uret", "görev üret", "degerlendirme gorevi", "değerlendirme görevi", "amir gorevi", "gorevleri olustur", "görevleri oluştur"],
        steps=[
            "Performans Yönetimi > Görev Üretimi ekranına girin.",
            "Dönemi seçin.",
            "Dönemin kapsamını kontrol edin: tüm kurum, birim, kategori veya seçili personel.",
            "Personel, birim, kategori, amir, izin ve vekâlet verilerinin temiz olduğundan emin olun.",
            "Görevleri Oluştur butonuna basın.",
            "Oluşan görevlerde eksik amir, yanlış amir veya sahte 3. amir beklemesi var mı kontrol edin.",
            "Hata varsa personel/organizasyon kaydını düzeltip görevleri yeniden üretin.",
        ],
        attention=["Sistem yalnızca gerçek görev akışını üretmeli; olmayan 2./3. amir için sahte bekleme göstermemelidir."],
        checks=["Her personel için doğru amir zinciri oluşmalı.", "Hukuk ve özel rol istisnaları doğru uygulanmalı."],
        actions=[_a("Görev Üretimi", "/performance/assignments"), _a("Süreç Takibi", "/performance/process-tracking")],
        next_questions=["Amir değerlendirmesi nasıl yapılır?", "3. amir kuralı nedir?"],
        priority=88,
    ),
    Guide(
        key="supervisor_scoring",
        title="Amir değerlendirmesi / puanlama nasıl yapılır?",
        module="Performans Yönetimi",
        who=["Amir", "Koordinatör", "Grup Başkanı", "Yetkili Değerlendirici"],
        patterns=["puanlama", "puan ver", "amir degerlendirme", "amir değerlendirme", "degerlendirme yap", "gorevlerim", "görevlerim", "bekleyen gorev", "bekleyen görev"],
        steps=[
            "Performans Yönetimi > Değerlendirme Görevlerim ekranına girin.",
            "Size atanmış personel/değerlendirme görevini seçin.",
            "Kriter bazlı 1–5 arası puanları girin.",
            "Gerekli açıklama alanlarını doldurun.",
            "Genel görüş/kanaat alanını tamamlayın.",
            "Kaydet veya Değerlendirmeyi Tamamla butonuna basın.",
            "Görevin tamamlandı durumuna geçtiğini kontrol edin.",
        ],
        attention=["BYS360 kör değerlendirme yapmaz; sonraki amir önceki amirin puan ve görüşünü görebilir.", "1 ve 5 puan açıklama kuralı sistem ayarına bağlıdır; 70 altı ve 90 üstünde ayrıntılı genel görüş gerekir."],
        checks=["Görev listesinde durum tamamlandı olmalı.", "Eksik açıklama varsa sistem uyarı vermeli."],
        actions=[_a("Değerlendirme Görevlerim", "/performance/tasks"), _a("Performans Paneli", "/performance/dashboard")],
        next_questions=["70 altı olursa ne olur?", "Karne ne zaman görünür?"],
        priority=90,
    ),
    Guide(
        key="third_supervisor",
        title="3. amir kuralı nasıl çalışır?",
        module="Performans Yönetimi",
        who=["Admin", "Performans Yetkilisi", "Yönetici"],
        patterns=["3 amir", "3. amir", "ucuncu amir", "üçüncü amir", "yorumcu amir", "puan modu", "yorum modu"],
        steps=[
            "Önce sistem ayarlarında 3. amir kullanım modunu kontrol edin.",
            "Yorum modu seçiliyse 3. amir yalnızca görüş yazar; puana etkisi olmaz.",
            "Puan modu seçiliyse 3. amir puana katkı verir ve ağırlık hesabına dahil olur.",
            "Personel organizasyonunda gerçekten 3. amir var mı kontrol edin.",
            "Görev üretiminde olmayan 3. amir için görev oluşmadığından emin olun.",
            "Ekranlarda yorum modundaki 3. amir için 'puan bekliyor' değil 'yorum/görüş bekliyor' dili kullanılmalıdır.",
        ],
        attention=["3. amir zorunlu değildir. Her personelde olmak zorunda değildir."],
        checks=["3. amir yoksa boş sütun/görev görünmemeli.", "Puan modunda toplam ağırlık %100 olmalı."],
        actions=[_a("Performans Ayarları", "/settings#module-foundation"), _a("Görev Üretimi", "/performance/assignments")],
        next_questions=["Amir zinciri nasıl oluşur?", "Ağırlık nasıl tanımlanır?"],
        priority=86,
    ),
    Guide(
        key="below_70_process",
        title="70 altı performans sonucu ne olur?",
        module="Performans Yönetimi / Başkan Onayları",
        who=["Başkan/Üst Yönetim", "Admin", "Performans Yetkilisi", "Personel ve Destek Hizmetleri Grup Başkanı"],
        patterns=["70 alti", "70 altı", "yetmis alti", "düşük performans", "dusuk performans", "basarisiz", "başarısız", "baskan onay", "başkan onay", "ust onay", "üst onay"],
        steps=[
            "Değerlendirme tamamlanır ve sistem nihai puanı hesaplar.",
            "Nihai puan 70’in altındaysa sonuç doğrudan kesinleşmez.",
            "Kayıt Başkan/Üst Onay sürecine alınır ve yayın kilidi oluşur.",
            "Başkan/Üst Onay tamamlanmadan karne personele açılmaz.",
            "Onay sonrası personel süreç kaydı oluşur.",
            "Aynı yıl ilk 70 altı ise düşük performans uyarısı kaydı oluşur.",
            "Aynı yıl ikinci kez 70 altı ise tekrarlayan düşük performans süreci başlatılır.",
            "Sistem otomatik idari işlem yapmazma yapmaz; yalnızca idari süreç statüsü üretir.",
        ],
        attention=["Asistan Başkan yerine onay/ret yapamaz ve idari karar veremez."],
        checks=["Başkan Onayları ekranında yalnızca gerçek 70 altı kayıt görünmeli.", "Yayın kilidi kalkmadan personel karneyi görmemeli."],
        actions=[_a("Başkan Onayları", "/performance/president-approvals"), _a("Süreç Takibi", "/performance/process-tracking")],
        next_questions=["Karne neden görünmüyor?", "Yayın ön onayı nasıl yapılır?"],
        priority=95,
    ),
    Guide(
        key="publication_preapproval",
        title="Yayın ön onayı ve final yayın nasıl yapılır?",
        module="Performans Yönetimi",
        who=["Personel ve Destek Hizmetleri Grup Başkanı", "Admin/İK Yetkilisi"],
        patterns=["yayin on onay", "yayın ön onay", "final yayin", "final yayın", "karne yayinla", "karne yayınla", "sonuclari yayinla", "sonuçları yayınla"],
        steps=[
            "Tüm değerlendirme görevlerinin tamamlandığını kontrol edin.",
            "70 altı kayıt varsa Başkan/Üst Onay tamamlanmış olmalıdır.",
            "Sonuçlar Personel ve Destek Hizmetleri Grup Başkanı yayın ön onayına düşer.",
            "Yayın ön onayı verildikten sonra Admin/İK final yayın ekranına girer.",
            "İlgili dönemi seçer ve final yayın işlemini yapar.",
            "Yayın log kaydı oluşur ve personel kendi karnesini görebilir.",
        ],
        attention=["Yayın ön onayı olmadan final yayın yapılmamalıdır."],
        checks=["Yayın log kaydı oluşmalı.", "Personel sadece kendi karnesini görmeli."],
        actions=[_a("Yayın Ön Onayı", "/performance/personnel-support-publish-approvals"), _a("Final Yayın", "/performance/publish")],
        next_questions=["Karne neden görünmüyor?", "Başkan Onayları nedir?"],
        priority=86,
    ),
    Guide(
        key="scorecard_not_visible",
        title="Karne neden görünmüyor?",
        module="Performans Yönetimi",
        who=["Personel", "Admin", "Performans Yetkilisi", "Yönetici"],
        patterns=["karne gorunmuyor", "karne görünmüyor", "karnem yok", "karnemi goremiyorum", "puanimi goremiyorum", "sonuc gorunmuyor", "sonuç görünmüyor", "karne acilmiyor"],
        steps=[
            "Performans Yönetimi > Süreç Takibi ekranına girin.",
            "İlgili dönemi seçin ve değerlendirme görevleri tamamlandı mı kontrol edin.",
            "70 altı kayıt varsa Başkan/Üst Onay tamamlandı mı bakın.",
            "Yayın ön onayı gerekiyorsa Personel ve Destek Hizmetleri Grup Başkanı onayı tamamlandı mı kontrol edin.",
            "Admin/İK final yayını yaptı mı kontrol edin.",
            "Kullanıcının karne menü yetkisi ve kişi/birim görünürlüğü açık mı bakın.",
            "Dönem aktif/yayınlanmış değilse personel karneyi göremez.",
        ],
        attention=["Personel süreç tamamlanmadan kendi sonucunu göremez; bu doğru güvenlik davranışıdır."],
        checks=["Yayın durumu tamamlandı olmalı.", "Menü ve backend yetkisi birlikte açık olmalı."],
        actions=[_a("Süreç Takibi", "/performance/process-tracking"), _a("Karnem", "/performance/scorecard"), _a("Rol Matrisi", "/admin/role-matrix")],
        next_questions=["Final yayın nasıl yapılır?", "Başkan onayı nasıl tamamlanır?"],
        priority=90,
    ),
    Guide(
        key="scorecard_archive",
        title="Geçmiş karne / puan arşivi nasıl kullanılır?",
        module="Performans Yönetimi",
        who=["Personel", "Yönetici", "Admin", "Performans Yetkilisi"],
        patterns=["gecmis karne", "geçmiş karne", "karne arsiv", "karne arşiv", "eski puan", "2024 puan", "2025 puan", "gecmis performans"],
        steps=[
            "Performans Yönetimi > Geçmiş Karne Arşivi ekranına girin.",
            "Yıl veya dönem filtresi seçin.",
            "Yetkinize göre personel, birim veya kategori filtresini kullanın.",
            "Kendi geçmiş karneniz yayınlandıysa detayını açın.",
            "Eski puan import edilecekse kaynak belge, yıl, dönem ve puan alanlarını doldurun.",
        ],
        attention=["Personel yalnızca kendi geçmişini görmelidir. Yönetici görünürlüğü yetki kapsamına bağlıdır."],
        checks=["Yıl/dönem filtresi doğru çalışmalı.", "Yetkisiz kişi başka personel detayını görmemeli."],
        actions=[_a("Geçmiş Karne Arşivi", "/performance/archive")],
        next_questions=["Karne neden görünmüyor?", "Rapor nasıl alınır?"],
        priority=78,
    ),
    Guide(
        key="in_period_notes",
        title="Dönem içi not nasıl eklenir?",
        module="Performans Yönetimi",
        who=["Amir", "Yönetici", "Performans Yetkilisi"],
        patterns=["donem ici not", "dönem içi not", "ara geri bildirim", "olumlu not", "olumsuz not", "gozlem notu", "gözlem notu"],
        steps=[
            "Performans Yönetimi > Dönem İçi Notlar ekranına girin.",
            "Dönem ve personel seçin.",
            "Not türünü seçin: olumlu olay, olumsuz olay, başarı, gelişim ihtiyacı veya genel gözlem.",
            "Açıklama alanını doldurun.",
            "Kaydedin.",
            "Puanlama döneminde bu notun destek bilgi olarak görünüp görünmediğini kontrol edin.",
        ],
        attention=["Dönem içi not otomatik puan üretmez; yalnızca değerlendirmeye yardımcı kayıt sağlar."],
        checks=["Not ilgili dönem/personel altında görünmeli.", "Yetkisiz kişi not içeriğini görmemeli."],
        actions=[_a("Dönem İçi Notlar", "/performance/in-period-notes")],
        next_questions=["Gelişim önerisi nasıl yazılır?", "Amir puanlaması nasıl yapılır?"],
        priority=78,
    ),
    Guide(
        key="development_suggestion",
        title="Gelişim önerisi nasıl yazılır?",
        module="Performans Yönetimi",
        who=["Amir", "Performans Yetkilisi", "Yönetici"],
        patterns=["gelisim onerisi", "gelişim önerisi", "guculu yon", "güçlü yön", "gelisim alani", "gelişim alanı", "rehber not", "egitim onerisi"],
        steps=[
            "Performans Yönetimi > Gelişim Önerileri ekranına girin.",
            "Personeli ve dönemi seçin.",
            "Güçlü yön, gelişim alanı ve önerilen takip notunu yazın.",
            "Kaydedin.",
            "Karne veya gelişim ekranında görünürlüğün sistem ayarlarına uygun olduğunu kontrol edin.",
        ],
        attention=["Gelişim önerisi idari yaptırım kararı değildir; rehber ve takip notudur."],
        checks=["Öneri doğru personel/dönem altında görünmeli.", "Yayın görünürlüğü yetkiye bağlı olmalı."],
        actions=[_a("Gelişim Önerileri", "/performance/development-suggestions")],
        next_questions=["Dönem içi not nasıl eklenir?", "70 altı süreç nasıl ilerler?"],
        priority=75,
    ),
    Guide(
        key="performance_reports_dashboard",
        title="Performans dashboard ve raporları nasıl kullanılır?",
        module="Performans Yönetimi / Raporlar",
        who=["Başkan", "Admin", "Yönetici", "Performans Yetkilisi"],
        patterns=["performans rapor", "dashboard", "grafik", "canli performans haritasi", "riskli personel", "aksatan amir", "geciken amir", "kategori ortalamasi"],
        steps=[
            "Performans Yönetimi > Dashboard veya Raporlar ekranına girin.",
            "Dönem, birim, kategori veya personel filtresi seçin.",
            "Tamamlanma oranı, düşük performans, riskli personel, aksatan amir ve kategori ortalaması kartlarını inceleyin.",
            "Detay görmek istediğiniz kartın ilgili raporuna geçin.",
            "Dışa aktarım gerekiyorsa yetki dahilinde rapor oluşturun.",
        ],
        attention=["Personel detayları rol ve kapsam yetkisine göre görünmelidir; kategori ortalaması kişi detayı olmadan sunulabilir."],
        checks=["Teknik ifadeler kullanıcıya görünmemeli.", "Yetkisiz kullanıcı detay rapora erişememeli."],
        actions=[_a("Performans Dashboard", "/performance/dashboard"), _a("Performans Raporları", "/performance/reports")],
        next_questions=["Rol matrisi nasıl çalışır?", "KPI hedefleri nasıl takip edilir?"],
        priority=78,
    ),
    Guide(
        key="role_matrix",
        title="Rol matrisi ve menü görünürlüğü nasıl çalışır?",
        module="Sistem Ayarları ve Yetkilendirme",
        who=["Admin", "Sistem Yöneticisi", "Yetkilendirme Yetkilisi"],
        patterns=["rol matrisi", "yetki ver", "yetki kaldir", "menü aç", "menu ac", "menü kapat", "menu kapat", "modul bazli", "performans rol matrisi"],
        steps=[
            "Sistem Ayarları bölümüne girin.",
            "Rol Matrisi / Menü Yetkileri ekranını açın.",
            "Düzenlemek istediğiniz rolü seçin.",
            "Modül ve alt sekme görünürlüklerini açın veya kapatın.",
            "Gerekirse kişi bazlı ve birim bazlı menü profillerini ayrıca kontrol edin.",
            "Kaydedin.",
            "İlgili kullanıcıyla çıkış-giriş yaparak menü görünürlüğünü test edin.",
        ],
        attention=["Kapalı menü kullanıcıya hiç görünmemelidir; sadece tıklayınca erişim engeli vermek yeterli değildir.", "Backend route yetkisi de korunmalıdır."],
        checks=["Menü UI’da doğru görünmeli/gizlenmeli.", "URL elle yazılsa bile yetkisiz veri dönmemeli."],
        actions=[_a("Rol Matrisi", "/admin/role-matrix"), _a("Sistem Ayarları", "/settings")],
        next_questions=["Menü görünmüyor ne yapmalıyım?", "Kişi bazlı yetki nasıl verilir?"],
        priority=88,
    ),
    Guide(
        key="menu_not_visible",
        title="Menü görünmüyorsa ne yapılır?",
        module="Sistem Ayarları ve Yetkilendirme",
        who=["Admin", "Sistem Yöneticisi", "İlgili kullanıcı"],
        patterns=["menü görünmüyor", "menu gorunmuyor", "sekme yok", "özellik yok", "ozellik yok", "goremiyorum", "göremiyorum", "menü yok", "menu yok"],
        steps=[
            "Önce kullanıcının rolünü kontrol edin.",
            "Sistem Ayarları > Rol Matrisi ekranında ilgili modül/sekme açık mı bakın.",
            "Kişi bazlı menü izni varsa kapalı olup olmadığını kontrol edin.",
            "Birim bazlı menü profili uygulanıyorsa ilgili birim profilini kontrol edin.",
            "Modül ayarı genel olarak kapalı mı bakın.",
            "Kaydedip kullanıcıyla çıkış-giriş yaptırın.",
            "Hâlâ görünmüyorsa audit/yetki loglarını ve backend route yetkisini kontrol edin.",
        ],
        attention=["Yetkisi olmayan kullanıcının menüyü görmemesi doğru davranıştır."],
        checks=["Menü açık kullanıcıda görünmeli, kapalı kullanıcıda hiç görünmemeli.", "Beyaz sayfa yerine kurumsal erişim engeli ekranı çıkmalı."],
        actions=[_a("Rol Matrisi", "/admin/role-matrix"), _a("Kullanıcı Yetkileri", "/admin/users")],
        next_questions=["Rol matrisi nasıl çalışır?", "Kişi bazlı yetki nedir?"],
        priority=90,
    ),
    Guide(
        key="system_security",
        title="Güvenlik, CAPTCHA ve audit log nasıl çalışır?",
        module="Sistem Ayarları ve Güvenlik",
        who=["Admin", "Sistem Yöneticisi"],
        patterns=["captcha", "guvenlik", "güvenlik", "audit", "log", "hatali giris", "hatalı giriş", "oturum", "parola politikasi"],
        steps=[
            "Sistem Ayarları > Güvenlik Ayarları ekranına girin.",
            "Hatalı giriş limitini kontrol edin; 3 hatalı girişten sonra CAPTCHA aktif olmalıdır.",
            "Oturum süresi, parola politikası ve güvenli çıkış ayarlarını kontrol edin.",
            "Kritik ayar değişikliklerinin audit log’a düştüğünü doğrulayın.",
            "Yetki, rol ve menü değişikliklerinde kim/ne zaman/ne değiştirdi bilgisi izlenmelidir.",
        ],
        attention=["Asistan güvenlik ayarı değiştirmez; sadece doğru kontrol ekranına yönlendirir."],
        checks=["CAPTCHA davranışı test edilmeli.", "Audit log kayıtları oluşmalı."],
        actions=[_a("Güvenlik Ayarları", "/admin/security"), _a("Audit Log", "/admin/audit-logs")],
        next_questions=["Rol matrisi nasıl çalışır?", "Canlı operasyon kontrolü nedir?"],
        priority=72,
    ),
    Guide(
        key="support_ticket",
        title="Destek talebi nasıl açılır ve takip edilir?",
        module="Yardım Merkezi / Destek",
        who=["Tüm kullanıcılar"],
        patterns=["destek talebi", "yardim talebi", "yardım talebi", "ariza", "arıza", "sorun bildir", "ticket", "talep ac", "talep aç"],
        steps=[
            "Yardım Merkezi / Destek Talepleri ekranına girin.",
            "Yeni Destek Talebi butonuna basın.",
            "Kategori seçin ve konu başlığını yazın.",
            "Açıklamayı girin; gerekiyorsa ekran görüntüsü veya dosya ekleyin.",
            "Kaydedin.",
            "Talep numarası, durum ve cevapları Destek Taleplerim ekranından takip edin.",
            "Talep kapanınca geri bildirim puanı verin.",
        ],
        attention=["Asistan talep içeriğini veya ek dosyaları doğrudan göstermez; sadece ekran yönlendirmesi yapar."],
        checks=["Talep açık/bekleyen/cevaplandı/kapandı durumlarından biriyle görünmeli."],
        actions=[_a("Destek Talebi Oluştur", "/support/new"), _a("Destek Taleplerim", "/support")],
        next_questions=["Menü görünmüyor ne yapmalıyım?", "Bildirimler nerede?"],
        priority=80,
    ),
    Guide(
        key="messages_announcements",
        title="Mesaj, duyuru ve bildirimler nasıl kullanılır?",
        module="İletişim Yönetimi",
        who=["Tüm kullanıcılar", "Yönetici", "Yetkili Birimler"],
        patterns=["mesaj", "duyuru", "bildirim", "okunmamis", "okunmamış", "mesaj gonder", "duyuru olustur", "bildirimler"],
        steps=[
            "Mesaj için İletişim/Mesajlar ekranına girin ve yeni konuşma oluşturun.",
            "Alıcıyı seçin, mesajı yazın ve gerekiyorsa dosya ekleyin.",
            "Duyuru için Duyurular ekranına girin, başlık/içerik ve hedef kitleyi belirleyin.",
            "Bildirimler ekranından size gelen sistem uyarılarını takip edin.",
            "Kritik duyurularda hedef kitle ve yayın tarihi kontrol edilmelidir.",
        ],
        attention=["Asistan mesaj metinlerini ve özel içerikleri dökmez; yalnızca ilgili ekrana yönlendirir."],
        checks=["Duyuru hedef kullanıcıda görünmeli.", "Mesaj/ek dosya yetki sınırına göre erişilebilir olmalı."],
        actions=[_a("Mesajlar", "/messages"), _a("Duyurular", "/announcements"), _a("Bildirimler", "/notifications")],
        next_questions=["Anket nasıl oluşturulur?", "Destek talebi nasıl açılır?"],
        priority=76,
    ),
    Guide(
        key="survey_feedback",
        title="Anket ve geri bildirim nasıl oluşturulur / yanıtlanır?",
        module="İletişim ve Anket Yönetimi",
        who=["Personel", "Yönetici", "Anket/Geri Bildirim Yetkilisi"],
        patterns=["anket", "anket olustur", "anket yanitla", "geri bildirim", "nabiz", "nabız", "kampanya", "soru ekle"],
        steps=[
            "Anket oluşturmak için İletişim ve Anket Yönetimi > Anketler ekranına girin.",
            "Yeni anket oluşturun; başlık, açıklama ve soru türlerini ekleyin.",
            "Hedef kitle, başlangıç ve bitiş tarihini belirleyin.",
            "Yayınlayın ve katılım durumunu rapordan takip edin.",
            "Anket yanıtlamak için size açık anketi açın, cevapları doldurun ve gönderin.",
            "Geri bildirim kampanyası için hedef grup ve soruları belirleyip yayınlayın.",
        ],
        attention=["Asistan kişisel anket cevaplarını göstermez; sadece yanıt bekleyen anket veya katılım özeti düzeyinde yönlendirir."],
        checks=["Katılım oranı raporda görünmeli.", "Yetkisiz kişi kişisel cevap detayını görmemeli."],
        actions=[_a("Anketler", "/surveys"), _a("Geri Bildirim", "/communication/feedback")],
        next_questions=["Duyuru nasıl oluşturulur?", "AI Karar Destek anketi yorumlar mı?"],
        priority=78,
    ),
    Guide(
        key="ai_decision_support",
        title="AI Karar Destek ne yapar, ne yapmaz?",
        module="AI Karar Destek Merkezi",
        who=["Başkan/Üst Yönetim", "Admin", "Yetkili Yöneticiler"],
        patterns=["ai karar", "yapay zeka", "karar destek", "ai karar verir mi", "analiz", "ozetleme", "özetleme", "risk farkindaligi", "risk farkındalığı"],
        steps=[
            "AI Karar Destek Merkezi ekranına girin.",
            "Yetkili olduğunuz analiz başlığını seçin: performans, anket, destek, KPI veya rapor özeti.",
            "Sistem verileri özetler, önceliklendirir ve dikkat alanlarını gösterir.",
            "Üretilen çıktıyı yönetici/yetkili kullanıcı değerlendirir.",
            "Nihai idari karar insan tarafından verilir.",
        ],
        attention=["AI Karar Destek karar vermez, puan belirlemez, otomatik işlem yapmaz; yalnızca insan denetimli analiz desteği üretir."],
        checks=["Çıktılar loglanmalı.", "Hassas veri redaksiyonu ve yetki sınırı korunmalı."],
        actions=[_a("AI Karar Destek", "/ai/decision-support"), _a("AI Health", "/ai/decision-support/faz1/health")],
        next_questions=["BYS360 Asistanı ile AI Karar Destek farkı nedir?", "KPI analizi nasıl yapılır?"],
        priority=82,
    ),
    Guide(
        key="kpi_targets",
        title="KPI ve Hedef Yönetimi nasıl kullanılır?",
        module="KPI / Hedef Yönetimi",
        who=["Başkan/Üst Yönetim", "Admin", "Koordinatör", "Yetkili Yönetici"],
        patterns=["kpi", "hedef", "hedef karti", "hedef kartı", "hedef donemi", "hedef dönemi", "gerceklesme", "gerçekleşme", "riskli hedef", "stratejik hedef"],
        steps=[
            "KPI / Hedef Yönetimi ekranına girin.",
            "Hedef Dönemleri sekmesinden hedef dönemi oluşturun veya seçin.",
            "Hedef Kartları ekranında hedef adını, tipini, kategorisini, sahibi kişi/birimi, hedef değerini ve ağırlığını girin.",
            "KPI Ölçüm ekranında gerçekleşen değeri girin.",
            "Sistem başarı oranı ve risk durumunu hesaplar.",
            "Dashboard’da hedef gerçekleşme, riskli hedef ve kategori durumlarını takip edin.",
        ],
        attention=["Asistan hedef kapatmaz veya hedef değeri değiştirmez; sadece işlem yolunu öğretir."],
        checks=["Hedef kartı doğru dönem/kapsama bağlı olmalı.", "Dashboard’da gerçekleşme oranı görünmeli."],
        actions=[_a("KPI/Hedef Dashboard", "/performans/stratejik/kpi-dashboard"), _a("Hedef Kartları", "/performans/stratejik/targets"), _a("KPI Analiz", "/performans/stratejik/kpi-analiz")],
        next_questions=["Hedef dönemi nasıl oluşturulur?", "KPI gerçekleşmesi nasıl girilir?", "Dashboard nasıl kullanılır?"],
        priority=84,
    ),
    Guide(
        key="live_ops",
        title="Canlı operasyon kontrolü nasıl yapılır?",
        module="Canlı Operasyon / Teknik Kontrol",
        who=["Sistem Yöneticisi", "Geliştirici", "Canlı Operasyon Yetkilisi"],
        patterns=["canli kontrol", "canlı kontrol", "pilot yayin", "pilot yayın", "scheduled task", "waitress", "gate", "compileall", "white screen", "beyaz ekran", "restart"],
        steps=[
            "Overlay uygulamadan önce proje klasöründe olduğunuzdan emin olun.",
            "Repair scriptini çalıştırın ve beklenen OK çıktısını alın.",
            "Gate scriptini çalıştırın; hata varsa canlıyı yeniden başlatmayın.",
            "compileall ile Python sözdizimi kontrolü yapın.",
            "Pilot/canlı Scheduled Task yeniden başlatılacaksa önce doğru task adını kontrol edin.",
            "Yeniden başlatma sonrası /login, /home ve kritik modül ekranlarını test edin.",
        ],
        attention=["Asistan canlı sunucuda komut çalıştırmaz; sadece güvenli kontrol sırasını öğretir."],
        checks=["Gate OK olmalı.", "Beyaz ekran yoksa ve kritik sayfalar açılıyorsa işlem başarılıdır."],
        actions=[_a("Ana Sayfa", "/home"), _a("Login", "/login")],
        next_questions=["Gate hata verirse ne yapmalıyım?", "Son yüklediğim paketi nasıl geri alırım?"],
        priority=70,
    ),
]

# Extra phrase routing to avoid vague generic answers for common Turkish sentences.
def _hard_intent(q: str) -> str | None:
    if _has(q, "performans donemi", "degerlendirme donemi") and _has(q, "olustur", "ac", "baslat", "yeni", "nasil"):
        return "performance_period_create"
    if _has(q, "donem") and _has(q, "olustur", "ac", "baslat"):
        return "performance_period_create"
    if _has(q, "karnem", "karne", "sonuc", "puan") and _has(q, "gorunmuyor", "yok", "acilmiyor", "goremiyorum"):
        return "scorecard_not_visible"
    if _has(q, "menü", "menu", "sekme", "ozellik") and _has(q, "yok", "gorunmuyor", "goremiyorum", "gelmiyor"):
        return "menu_not_visible"
    if _has(q, "rol matrisi", "yetki") and _has(q, "ac", "kapat", "ver", "kaldir", "gorunurluk"):
        return "role_matrix"
    if _has(q, "70", "dusuk performans", "düşük performans"):
        return "below_70_process"
    if _has(q, "destek") and _has(q, "ac", "olustur", "talep", "yardim"):
        return "support_ticket"
    if _has(q, "anket") and _has(q, "olustur", "ac", "yayin", "soru"):
        return "survey_feedback"
    if _has(q, "personel") and _has(q, "ekle", "kaydet", "olustur", "yeni"):
        return "personnel_add"
    if _has(q, "gorev") and _has(q, "uret", "olustur"):
        return "performance_task_generation"
    if _has(q, "amir") and _has(q, "puan", "degerlendir", "gorev"):
        return "supervisor_scoring"
    if _has(q, "kpi", "hedef"):
        return "kpi_targets"
    if _has(q, "ai karar", "karar destek", "yapay zeka"):
        return "ai_decision_support"
    if _has(q, "chatgpt gibi", "her seyi", "tum modulleri", "tum ozellikleri", "hic bilmeyen"):
        return "all_modules_overview"
    return None


def _score_guide(q: str, guide: Guide) -> int:
    score = 0
    q_tokens = _tokens(q)
    for pattern in guide.patterns:
        p = _norm(pattern)
        if not p:
            continue
        if p in q:
            score += 100 + guide.priority
        else:
            p_tokens = _tokens(p)
            if p_tokens:
                overlap = len(q_tokens & p_tokens)
                if overlap:
                    score += overlap * 12
                if p_tokens and p_tokens.issubset(q_tokens):
                    score += 45
    # module hint boosts
    if "performans" in q and guide.module.startswith("Performans"):
        score += 18
    if "personel" in q and guide.module.startswith("Personel"):
        score += 18
    if ("yetki" in q or "rol" in q or "menu" in q) and "Ayar" in guide.module:
        score += 18
    if ("anket" in q or "mesaj" in q or "duyuru" in q) and "İletişim" in guide.module:
        score += 18
    return score


def _select_guide(question: str) -> tuple[Guide, int]:
    q = _norm(question)
    hard = _hard_intent(q)
    if hard:
        for g in GUIDES:
            if g.key == hard:
                return g, 999
    ranked = sorted(((g, _score_guide(q, g)) for g in GUIDES), key=lambda x: (x[1], x[0].priority), reverse=True)
    if ranked and ranked[0][1] >= 38:
        return ranked[0]
    return GUIDES[0], 0


def _format_answer(guide: Guide, role: str, confidence: int) -> str:
    lines: list[str] = []
    lines.append(f"Anladım. Bu konu **{guide.module}** içindedir: **{guide.title}**")
    if confidence < 38 and guide.key == "all_modules_overview":
        lines.append("Sorunuzu genel kullanım rehberi olarak ele aldım. İsterseniz işlem adını daha kısa yazabilirsiniz: ‘dönem açacağım’, ‘personel ekleyeceğim’, ‘menü görünmüyor’ gibi.")
    lines.append("")
    lines.append("**Kim yapabilir?**")
    for item in guide.who:
        lines.append(f"- {item}")
    lines.append(f"- Şu anki olası rol bağlamı: {_role_label(role)}")
    lines.append("")
    lines.append("**Adım adım işlem sırası:**")
    for i, step in enumerate(guide.steps, 1):
        lines.append(f"{i}. {step}")
    if guide.attention:
        lines.append("")
        lines.append("**Dikkat:**")
        for item in guide.attention:
            lines.append(f"- {item}")
    lines.append("")
    lines.append("**Yetki ve güvenlik sınırı:**")
    lines.append(f"- {_scope_note(role)}")
    lines.append(f"- {SAFETY_NOTICE}")
    if guide.checks:
        lines.append("")
        lines.append("**İşlemden sonra kontrol edin:**")
        for item in guide.checks:
            lines.append(f"- {item}")
    if guide.next_questions:
        lines.append("")
        lines.append("**Bundan sonra sorabileceğiniz örnekler:**")
        for item in guide.next_questions[:4]:
            lines.append(f"- {item}")
    return "\n".join(lines)


def _safe_legacy_counts(legacy_payload: dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(legacy_payload, dict):
        counts = legacy_payload.get("counts")
        if isinstance(counts, dict):
            return counts
    return {}


def build_bys360_assistant_full_tutor_reply_v5(
    user: Any,
    question: str,
    legacy_builder: Callable[[Any, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    raw_question = str(question or "").strip()
    if not raw_question:
        raw_question = "BYS360'ı nasıl kullanacağım?"
    legacy_payload: dict[str, Any] | None = None
    # Only use legacy payload for safe counts/summaries. Never let it override the V5 stepwise answer.
    if callable(legacy_builder):
        try:
            legacy_payload = legacy_builder(user, raw_question)
        except Exception:
            legacy_payload = None
    guide, confidence = _select_guide(raw_question)
    role = _role_from_user(user)
    answer = _format_answer(guide, role, confidence)
    return {
        "ok": True,
        "version": VERSION,
        "mode": MODE,
        "assistant_name": ASSISTANT_NAME,
        "intent": f"bys360_stepwise_v5:{guide.key}",
        "detected_module": guide.module,
        "confidence": confidence,
        "answer": answer,
        "actions": guide.actions,
        "suggested_actions": guide.actions,
        "quick_replies": guide.next_questions[:5] or [
            "Performans dönemi nasıl oluşturulur?",
            "Personel nasıl eklenir?",
            "Menü görünmüyor ne yapmalıyım?",
            "Destek talebi nasıl açılır?",
        ],
        "counts": _safe_legacy_counts(legacy_payload),
        "notice": SAFETY_NOTICE,
        "security_notice": SAFETY_NOTICE,
        "automation_notice": "Asistan otomatik işlem yapmaz; işlemi ilgili BYS360 ekranında yetkili kullanıcı tamamlar.",
        "learning_scope": "Tüm BYS360 modülleri için işlem öğretimi, ekran yönlendirme, yetki sınırı ve güvenli özet.",
    }


def get_bys360_assistant_full_tutor_v5_index() -> list[dict[str, Any]]:
    return [
        {
            "key": g.key,
            "title": g.title,
            "module": g.module,
            "patterns": g.patterns,
            "who": g.who,
            "actions": g.actions,
        }
        for g in GUIDES
    ]


# Backwards compatible aliases for possible imports/tests.
build_bys360_assistant_reply_v5 = build_bys360_assistant_full_tutor_reply_v5
get_bys360_stepwise_guide_index_v5 = get_bys360_assistant_full_tutor_v5_index
