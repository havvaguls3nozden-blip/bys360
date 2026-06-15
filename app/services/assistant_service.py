
"""BYS360 Asistan için kontrollü, yerel ve güvenli rehber cevap servisi.

V9 güncellemesi: Performans Yönetimi Modülü'ne eklenen Başkan/Üst Onay,
yayın ön onayı, çoklu dönem, kategori, dönem içi not, gelişim önerisi, geçmiş
karne arşivi, otomatik hatırlatma ve yardım merkezi akışlarını rehberliğe bağlar.

Asistan idari karar üretmez, dış AI servisine bağlanmaz. Canlı özetler ayrı
serviste yalnızca sayı/kart olarak üretilir; mesaj metni, puan, anket cevabı veya
kişisel açıklama gösterilmez.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class AssistantAction:
    label: str
    url: str


@dataclass(frozen=True)
class AssistantReply:
    answer: str
    actions: tuple[AssistantAction, ...] = ()
    topic: str = "genel"
    suggestions: tuple[str, ...] = ()


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    return re.sub(r"\s+", " ", text)


def _role_text(role: object | None) -> str:
    raw = getattr(role, "name", None) or getattr(role, "value", None) or role or ""
    return _normalize(str(raw))


def _is_privileged_role(role: object | None) -> bool:
    role_name = _role_text(role)
    privileged_markers = (
        "admin", "sistem", "super", "ust yonetim", "üst yönetim",
        "baskan", "başkan", "baskan yardimcisi", "başkan yardımcısı",
        "grup baskani", "grup başkanı", "koordinator", "koordinatör",
        "mali musavir", "mali müşavir", "ik", "insan kaynaklari", "insan kaynakları",
        "personel yonetimi", "personel yönetimi", "performans yetkilisi",
        "personel ve destek", "personel destek", "idari isler", "idari işler",
        "birim sorumlusu",
    )
    return any(marker in role_name for marker in privileged_markers)


def _is_president_like_role(role: object | None) -> bool:
    role_name = _role_text(role)
    return any(marker in role_name for marker in ("baskan", "başkan", "ust yonetim", "üst yönetim", "super", "admin", "sistem"))


def _is_personnel_support_role(role: object | None) -> bool:
    role_name = _role_text(role)
    return (
        "admin" in role_name
        or "sistem" in role_name
        or ("personel" in role_name and ("destek" in role_name or "idari" in role_name) and ("baskan" in role_name or "başkan" in role_name))
    )


def _has(text: str, *needles: str) -> bool:
    normalized_needles = tuple(_normalize(needle) for needle in needles)
    return any(needle in text for needle in normalized_needles)


def _actions(*items: tuple[str, str]) -> tuple[AssistantAction, ...]:
    allowed: list[AssistantAction] = []
    for label, url in items:
        clean_url = str(url or "")
        if not clean_url.startswith("/") or clean_url.startswith("//"):
            continue
        allowed.append(AssistantAction(str(label), clean_url))
    return tuple(allowed)


def get_assistant_topics(*, role: object | None = None) -> list[dict[str, str]]:
    privileged = _is_privileged_role(role)
    president_like = _is_president_like_role(role)
    personnel_support = _is_personnel_support_role(role)
    topics = [
        {"label": "Benim özetim", "question": "Bekleyen işlerimin özetini göster", "icon": "list-check"},
        {"label": "Öncelikli yönlendirme", "question": "Önce nereye bakmalıyım?", "icon": "route"},
        {"label": "Performans görevleri", "question": "Performans görevlerime nereden ulaşırım?", "icon": "clipboard-check"},
        {"label": "Karnem ve geçmişim", "question": "Karnemi ve geçmiş performansımı nereden görürüm?", "icon": "file-lines"},
        {"label": "Yardım Merkezi", "question": "Yardım merkezi ve kullanım kılavuzu nerede?", "icon": "circle-question"},
        {"label": "Destek talebi", "question": "Destek talebi nasıl açılır?", "icon": "life-ring"},
        {"label": "Duyurular", "question": "Duyuruları nereden görürüm?", "icon": "bullhorn"},
        {"label": "Anketler", "question": "Anketlerime nasıl ulaşırım?", "icon": "square-poll-vertical"},
        {"label": "Mesajlar", "question": "Mesajlarımı nereden görürüm?", "icon": "envelope"},
        {"label": "Şifre işlemleri", "question": "Şifremi nasıl değiştiririm?", "icon": "key"},
    ]
    if privileged:
        topics.extend([
            {"label": "Dönem ve kapsam", "question": "Çoklu dönem ve özel kapsam yönetimi nasıl kullanılır?", "icon": "calendar-days"},
            {"label": "Personel kategorileri", "question": "Personel kategori ve grup ortalaması nasıl çalışır?", "icon": "users-viewfinder"},
            {"label": "Dönem içi notlar", "question": "Dönem içi notlar nasıl kullanılır?", "icon": "note-sticky"},
            {"label": "Gelişim önerisi", "question": "Gelişim önerisi ve rehber alanı nasıl kullanılır?", "icon": "seedling"},
            {"label": "Geçmiş karne arşivi", "question": "Geçmiş karne ve puan arşivine nereden ulaşırım?", "icon": "box-archive"},
            {"label": "Aksatan amir", "question": "Aksatan amir ve otomatik hatırlatma nereden takip edilir?", "icon": "clock"},
            {"label": "Süreç takibi", "question": "Performans süreç takibi nereden izlenir?", "icon": "timeline"},
            {"label": "Raporlar", "question": "Raporlara ve canlı performans haritasına nereden ulaşırım?", "icon": "chart-line"},
            {"label": "Yetki ve menü", "question": "Yetki ve menü görünürlüğü nasıl yönetilir?", "icon": "user-shield"},
            {"label": "AI ilkesi", "question": "AI karar destek nasıl kullanılmalı?", "icon": "shield-halved"},
        ])
    if president_like:
        topics.append({"label": "Başkan/Üst Onay", "question": "Başkan onayları ve düşük performans süreci nereden takip edilir?", "icon": "stamp"})
    if personnel_support:
        topics.append({"label": "Yayın ön onayı", "question": "Personel ve Destek Hizmetleri yayın ön onayı nasıl çalışır?", "icon": "file-signature"})
    topics.extend([
        {"label": "Güvenlik/KVKK", "question": "Güvenlik ve KVKK açısından nelere dikkat etmeliyim?", "icon": "lock"},
        {"label": "Canlıya geçiş", "question": "Canlıya geçişte nelere dikkat etmeliyiz?", "icon": "rocket"},
    ])
    return topics


def build_assistant_reply(question: str, *, role: object | None = None) -> AssistantReply:
    q = _normalize((question or "")[:350])
    privileged = _is_privileged_role(role)
    president_like = _is_president_like_role(role)
    personnel_support = _is_personnel_support_role(role)

    if not q or _has(q, "komut", "ne sorabilirim", "neler yapabilirsin", "yardim et", "yardım et"):
        suggestions = [
            "Bekleyen işlerimin özetini göster",
            "Başkan onayları ve düşük performans süreci nereden takip edilir?" if president_like else "Performans görevlerime nereden ulaşırım?",
            "Yardım merkezi ve kullanım kılavuzu nerede?",
        ]
        return AssistantReply(
            topic="komutlar",
            answer=("BYS360 Asistan güncel canlı omurgaya göre çalışır. Performans görevleri, Başkan/Üst Onay, yayın ön onayı, dönem/kapsam yönetimi, personel kategorileri, dönem içi notlar, gelişim önerisi, geçmiş karne arşivi, aksatan amir takibi, duyuru, anket, mesaj, destek ve Yardım Merkezi konularında sizi doğru ekrana yönlendirir. Yalnızca sayı/özet ve güvenli bağlantı sunar; puan, kanaat, mesaj metni, anket cevabı veya hassas kişisel içerik göstermez."),
            actions=_actions(("Yardım Merkezi", "/support"), ("Benim özetim", "/assistant/my-summary"), ("Ana Sayfa", "/home")),
            suggestions=tuple(suggestions),
        )

    if _has(q, "nereye bak", "neye bak", "oncelik", "öncelik", "aksiyon", "yonlendirme", "yönlendirme", "hangi ekrana", "nereden baslay", "nereden başlay", "sırada ne", "sirada ne"):
        return AssistantReply(
            topic="guvenli_yonlendirme",
            answer=("Öncelikli yönlendirme kartları canlı içerik okumadan, yalnızca güvenli sayı/özet sonuçlarına göre hazırlanır. Asistan sizi ilgili ekrana götürür; detayları yalnızca o ekranda ve kendi yetkiniz kapsamında görürsünüz."),
            actions=_actions(("Benim özetim", "/assistant/my-summary"), ("Bildirimler", "/notifications"), ("Yardım Merkezi", "/support")),
            suggestions=("Bekleyen işlerimin özetini göster", "Performans süreç takibi nereden izlenir?"),
        )

    if _has(q, "baskan onay", "başkan onay", "ust onay", "üst onay", "70 alti", "70 altı", "dusuk performans", "düşük performans", "yayin kilidi", "yayın kilidi"):
        actions = [("Başkan Onayları", "/performance/president-approvals"), ("Süreç Takibi", "/performance/process-tracking"), ("Yardım Merkezi", "/support")]
        if not president_like:
            actions = [("Yardım Merkezi", "/support"), ("Performans görevleri", "/performance/tasks")]
        return AssistantReply(
            topic="baskan_ust_onay",
            answer=("70 altı performans sonucu doğrudan kesinleşmiş sayılmaz. Gerekli süreç Başkan/Üst Onay ekranında takip edilir; yayın kilidi ve süreç durumu ilgili yetkili ekranlarda görünür. Asistan bu kayıtlara ilişkin puan, kişi detayı veya kanaat göstermez; yalnızca doğru ekrana yönlendirir."),
            actions=_actions(*actions),
            suggestions=("Personel ve Destek Hizmetleri yayın ön onayı nasıl çalışır?", "Performans süreç takibi nereden izlenir?"),
        )

    if _has(q, "personel ve destek", "destek hizmetleri", "yayin on onay", "yayın ön onay", "on yayin", "ön yayın", "final yayin", "nihai yayin"):
        actions = [("Yayın Ön Onayları", "/performance/personnel-support-publish-approvals"), ("Yayın Kontrolü", "/performance/publish"), ("Yardım Merkezi", "/support")]
        if not personnel_support:
            actions = [("Yardım Merkezi", "/support"), ("Performans görevleri", "/performance/tasks")]
        return AssistantReply(
            topic="yayin_on_onayi",
            answer=("Tüm değerlendirme ve gerekli Başkan/Üst Onay adımları tamamlandıktan sonra sonuçlar Admin/İK final yayınına gitmeden önce Personel ve Destek Hizmetleri Grup Başkanı yayın ön onayına düşer. Bu adım Başkan onayının yerine geçmez; yayın öncesi kurumsal kontrol adımıdır."),
            actions=_actions(*actions),
            suggestions=("Başkan onayları ve düşük performans süreci nereden takip edilir?", "Yayın kontrolü nerede?"),
        )

    if _has(q, "donem", "dönem", "kapsam", "aylik", "aylık", "3 aylik", "3 aylık", "6 aylik", "6 aylık", "ozel donem", "özel dönem", "kategoriye ozel", "kategoriye özel", "guvenlik donemi", "güvenlik dönemi"):
        actions = [("Dönem Yönetimi", "/performance/periods"), ("Görev Üretimi", "/performance/assignments/generate"), ("Performans Raporları", "/performance/reports")]
        if not privileged:
            actions = [("Yardım Merkezi", "/support"), ("Karnem", "/performance/scorecard")]
        return AssistantReply(
            topic="donem_kapsam",
            answer=("Güncel performans yapısı yıllık dönemle sınırlı değildir. Aylık, 3 aylık, 6 aylık, yıllık veya özel dönem açılabilir; kapsam tüm kurum, birim, üst birim, kategori/grup veya seçili personel olarak belirlenebilir. Görev üretimi yalnızca dönem kapsamına giren gerçek personel için yapılmalıdır."),
            actions=_actions(*actions),
            suggestions=("Personel kategori ve grup ortalaması nasıl çalışır?", "Aksatan amir ve otomatik hatırlatma nereden takip edilir?"),
        )

    if _has(q, "kategori", "grup ortalama", "grup ortalaması", "guvenlik", "güvenlik", "temizlik", "idari personel", "teknik personel", "deneme sureli", "deneme süreli"):
        actions = [("Personel Listesi", "/admin/users"), ("Performans Raporları", "/performance/reports"), ("Dönem Yönetimi", "/performance/periods")]
        if not privileged:
            actions = [("Karnem", "/performance/scorecard"), ("Yardım Merkezi", "/support")]
        return AssistantReply(
            topic="personel_kategori",
            answer=("Personel kategori/grup altyapısı; Güvenlik, Temizlik, İdari Personel, Teknik Personel, Deneme Süreli Personel ve Diğer gibi kırılımlarla dönem, rapor ve ortalama takibini destekler. Personel kendi kişi detaysız grup/kategori ortalamasını görebilir; başka personel detayları yetki dışındaysa gösterilmez."),
            actions=_actions(*actions),
            suggestions=("Çoklu dönem ve özel kapsam yönetimi nasıl kullanılır?", "Raporlara ve canlı performans haritasına nereden ulaşırım?"),
        )

    if _has(q, "donem ici not", "dönem içi not", "ara not", "olumlu olay", "olumsuz olay", "gözlem", "gozlem", "ara geri bildirim"):
        actions = [("Dönem İçi Notlar", "/performance/interim-notes"), ("Gelişim Rehberi", "/performance/meeting-development/faz10"), ("Yardım Merkezi", "/support")]
        return AssistantReply(
            topic="donem_ici_not",
            answer=("Dönem içi notlar; olumlu olay, olumsuz olay, başarı, gelişim ihtiyacı ve genel gözlem gibi kayıtları puan döneminden önce kurumsal hafızaya alır. Bu notlar otomatik puan üretmez; değerlendirme sırasında yetkili amire hatırlatma ve bağlam desteği sağlar."),
            actions=_actions(*actions),
            suggestions=("Gelişim önerisi ve rehber alanı nasıl kullanılır?", "Karnemi ve geçmiş performansımı nereden görürüm?"),
        )

    if _has(q, "gelisim", "gelişim", "rehber", "egitim onerisi", "eğitim önerisi", "onerisi", "önerisi", "guclu yon", "güçlü yön"):
        actions = [("Gelişim Rehberi", "/performance/meeting-development/faz10"), ("Dönem İçi Notlar", "/performance/interim-notes"), ("Karne", "/performance/scorecard")]
        return AssistantReply(
            topic="gelisim_onerisi",
            answer=("Gelişim önerisi alanı, performans sonucunun yalnızca puanla kapanmaması için kullanılır. Yetkili kullanıcı; güçlü yön, gelişim alanı, takip notu ve rehber öneri ekleyebilir. Personel tarafında görünürlük yayın ve yetki kurallarına bağlıdır; asistan öneriyi kesin karar gibi sunmaz."),
            actions=_actions(*actions),
            suggestions=("Dönem içi notlar nasıl kullanılır?", "Yardım merkezi ve kullanım kılavuzu nerede?"),
        )

    if _has(q, "gecmis karne", "geçmiş karne", "karne arsiv", "karne arşiv", "puan arsiv", "puan arşiv", "eski puan", "2024", "2025", "import"):
        actions = [("Geçmiş Karne Arşivi", "/performance/archive"), ("Geçmiş Puan Import", "/performance/import/history"), ("Karne", "/performance/scorecard")]
        return AssistantReply(
            topic="gecmis_karne_arsivi",
            answer=("Geçmiş karne ve puan arşivi, önceki yıllara ait performans puanlarının yıl, dönem, puan, açıklama ve kaynak belge bilgisiyle saklanması için kullanılır. Personel kendi geçmişini; yönetici ise yalnızca yetkili olduğu kapsamın geçmişini görmelidir."),
            actions=_actions(*actions),
            suggestions=("Karnemi ve geçmiş performansımı nereden görürüm?", "Raporlara ve canlı performans haritasına nereden ulaşırım?"),
        )

    if _has(q, "aksatan", "geciken", "gecikmis", "gecikmiş", "hatirlatma", "hatırlatma", "son tarih", "mail log", "mail", "otomatik"):
        actions = [("Hatırlatma ve Aksatan Amirler", "/performance/meeting-development/faz9"), ("Mail Hatırlatmaları", "/performance/mail-reminders"), ("Performans Görevleri", "/performance/tasks")]
        if not privileged:
            actions = [("Performans Görevlerim", "/performance/tasks"), ("Bildirimler", "/notifications")]
        return AssistantReply(
            topic="hatirlatma_aksatan_amir",
            answer=("Otomatik hatırlatma ve aksatan amir takibi, değerlendirme sürecinin manuel takipte kaybolmaması için kullanılır. Son tarih yaklaşınca bildirim/e-posta üretilebilir; süre geçtiğinde aksatan amir raporlanır. Asistan yalnızca sayı ve yönlendirme verir, değerlendirme içeriği göstermez."),
            actions=_actions(*actions),
            suggestions=("Önce nereye bakmalıyım?", "Raporlara ve canlı performans haritasına nereden ulaşırım?"),
        )

    if _has(q, "surec takibi", "süreç takibi", "surec rapor", "süreç rapor", "akış", "akis", "process tracking", "process report"):
        actions = [("Süreç Takibi", "/performance/process-tracking"), ("Süreç Raporları", "/performance/process-reports"), ("Başkan Onayları", "/performance/president-approvals")]
        if not privileged:
            actions = [("Yardım Merkezi", "/support"), ("Performans Görevlerim", "/performance/tasks")]
        return AssistantReply(
            topic="surec_takibi",
            answer=("Süreç takibi; değerlendirme tamamlandı, düşük performans onayı, yayın ön onayı, final yayın ve personel görünürlüğü gibi adımların nerede olduğunu izlemek için kullanılır. Teknik durum kodları kullanıcıya gösterilmemeli; ekranda Türkçe kurumsal ifadeler kullanılmalıdır."),
            actions=_actions(*actions),
            suggestions=("Başkan onayları ve düşük performans süreci nereden takip edilir?", "Personel ve Destek Hizmetleri yayın ön onayı nasıl çalışır?"),
        )

    if _has(q, "performans", "degerlendirme", "değerlendirme", "karne", "gorev", "görev", "puan", "amir"):
        actions = [("Performans görevleri", "/performance/tasks"), ("Karne", "/performance/scorecard"), ("Performans kontrol paneli", "/performance/dashboard"), ("Yardım Merkezi", "/support")]
        if privileged:
            actions.insert(3, ("Performans raporları", "/performance/reports"))
        return AssistantReply(
            topic="performans",
            answer=("Performans işlemleri BYS360 içinde dönem, Değerlendirme Kriterleri, amir zinciri, görünürlük ve yayın/onay kurallarına göre yürütülür. Sonuçlar yetkili yayın ve gerekli onay süreçleri tamamlanmadan personele açılmaz. Asistan performans puanı, kanaat veya idari sonuç üretmez."),
            actions=_actions(*actions),
            suggestions=("Başkan onayları ve düşük performans süreci nereden takip edilir?", "Dönem içi notlar nasıl kullanılır?"),
        )

    if _has(q, "duyuru", "duyurular", "bildirim", "bildirimler", "popup", "pop up", "pop-up"):
        return AssistantReply(
            topic="duyuru_bildirim",
            answer=("Duyuru ve bildirimler kurum içi bilgilendirmelerin kayıtlı ve izlenebilir şekilde kullanıcılara ulaşması için kullanılır. Size atanmış bildirimleri Bildirimler alanından, duyuruları ise Duyurular ekranından görebilirsiniz. Kritik duyurularda okunma ve hedef kitle yönetimi yetkiye göre çalışır."),
            actions=_actions(("Bildirimler", "/notifications"), ("Duyurular", "/announcements")),
            suggestions=("Duyurular neden görünmüyor?", "Yardım merkezi nerede?"),
        )

    if _has(q, "anket", "anketler", "geri bildirim", "nabiz", "nabız", "form", "kampanya"):
        return AssistantReply(
            topic="anket",
            answer=("Anketler ve geri bildirimler kurum içi katılımı ölçmek için kullanılır. Size atanmış anketleri ilgili anket ekranından yanıtlayabilirsiniz. Sonuç görünürlüğü, anonim/kimlikli cevap mantığı ve raporlar yetki seviyesine göre açılır."),
            actions=_actions(("Anketler", "/surveys"), ("Yardım Merkezi", "/support")),
            suggestions=("Geri bildirim nasıl verilir?", "Destek talebi nasıl açılır?"),
        )

    if _has(q, "destek", "yardim", "yardım", "talep", "hata", "sorun", "ariza", "arıza"):
        return AssistantReply(
            topic="destek",
            answer=("Bir sorun veya ihtiyaç için destek talebi açabilirsiniz. Destek talepleri kişisel yazışmalarda kaybolmaz; kayıtlı, takip edilebilir ve gerektiğinde dosya ekli şekilde yönetilir. Ekran görüntüsü veya kısa açıklama eklemek çözümü hızlandırır."),
            actions=_actions(("Destek talebi aç", "/support/new"), ("Taleplerim", "/support/my-tickets"), ("Yardım Merkezi", "/support")),
            suggestions=("Yardım merkezi nerede?", "Mesajlarımı nereden görürüm?"),
        )

    if _has(q, "mesaj", "mesajlar", "sohbet", "konusma", "konuşma", "dosya yukle", "dosya yükle", "ek", "pdf"):
        return AssistantReply(
            topic="mesajlasma",
            answer=("Mesajlaşma alanında kurum içi yazışmaları ve konuşmaları takip edebilirsiniz. Dosya paylaşımı yetki, dosya türü ve boyut kurallarına bağlı çalışır. Hassas veya kişisel verileri yalnızca görev gereği ve yetki dahilinde paylaşmaya dikkat edin."),
            actions=_actions(("Mesajlar", "/messages"), ("Yeni mesaj", "/messages/new"), ("Yardım Merkezi", "/support")),
            suggestions=("Dosya yükleme neden görünmüyor?", "Güvenlik ve KVKK açısından nelere dikkat etmeliyim?"),
        )

    if _has(q, "sifre", "şifre", "parola", "hesap", "profil", "foto", "avatar", "oturum", "cikis", "çıkış"):
        return AssistantReply(
            topic="hesap",
            answer=("Hesap bilgilerinizi Hesabım alanından, şifre işlemlerinizi ise Şifre Değiştir ekranından yönetebilirsiniz. Güvenlik nedeniyle şifre, doğrulama cevabı veya hassas hesap bilgilerinizi asistan mesajına yazmayın."),
            actions=_actions(("Hesabım", "/account"), ("Şifre değiştir", "/account/change-password")),
            suggestions=("Güvenlik ve KVKK açısından nelere dikkat etmeliyim?", "Yardım merkezi nerede?"),
        )

    if _has(q, "ai", "yapay zeka", "yapay zekâ", "karar destek", "ozet", "özet", "analiz", "oneri", "öneri"):
        actions = [("Yardım Merkezi", "/support")]
        if privileged:
            actions.insert(0, ("AI Karar Destek", "/admin/ai-center"))
        return AssistantReply(
            topic="ai_karar_destek",
            answer=("BYS360 içinde AI karar vermez; yalnızca yetkili kullanıcıya özet, ön değerlendirme, dikkat notu ve karar destek çıktısı sunar. Sanal Asistan ise bu çıktıları karar gibi sunmadan, güvenli yönlendirme ve rehberlik katmanında kullanır."),
            actions=_actions(*actions),
            suggestions=("Raporlara ve canlı performans haritasına nereden ulaşırım?", "Güvenlik ve KVKK açısından nelere dikkat etmeliyim?"),
        )

    if _has(q, "personel", "sicil", "izin", "vekalet", "vekâlet", "birim", "unvan", "organizasyon", "yonetici", "yönetici"):
        actions = [("Yardım Merkezi", "/support")]
        if privileged:
            actions.insert(0, ("Personel listesi", "/admin/users"))
        return AssistantReply(
            topic="personel",
            answer=("Personel Yönetimi; sicil, birim, unvan, yönetici ilişkisi, izin, vekâlet ve kategori bilgilerinin merkezi omurgasıdır. Bu bilgiler performans, yetki, bildirim, raporlama ve karar destek süreçlerini etkilediği için güncel tutulmalıdır."),
            actions=_actions(*actions),
            suggestions=("Personel kategori ve grup ortalaması nasıl çalışır?", "Yetki ve menü görünürlüğü nasıl yönetilir?"),
        )

    if _has(q, "kvkk", "guvenlik", "güvenlik", "gizlilik", "yetki", "log", "kayit", "kayıt", "captcha"):
        return AssistantReply(
            topic="guvenlik_kvkk",
            answer=("BYS360’da kullanıcılar yalnızca yetkili oldukları alanlara erişmelidir. Asistana şifre, özel nitelikli veri veya gereksiz kişisel bilgi yazılmamalıdır. Kritik işlemler izlenebilirlik ve denetim amacıyla kayıt altına alınabilir."),
            actions=_actions(("Yardım Merkezi", "/support"), ("Hesabım", "/account")),
            suggestions=("Şifremi nasıl değiştiririm?", "AI karar destek nasıl kullanılmalı?"),
        )

    if _has(q, "yetki", "menu", "menü", "rol", "görünürlük", "gorunurluk", "ayar", "ayarlar"):
        actions = [("Yardım Merkezi", "/support")]
        if privileged:
            actions.insert(0, ("Ayarlar", "/settings"))
        return AssistantReply(
            topic="yetki_menu",
            answer=("BYS360’da menü görünürlüğü ve işlem yetkileri rol, kişi, birim ve sistem ayarlarına göre yönetilir. Kullanıcının görmemesi gereken menü ekranda kalmamalı; özel yetkiler kontrollü ve izlenebilir şekilde verilmelidir."),
            actions=_actions(*actions),
            suggestions=("Güvenlik ve KVKK açısından nelere dikkat etmeliyim?", "Personel bilgileri nereden yönetilir?"),
        )

    if _has(q, "rapor", "raporlar", "dashboard", "kontrol paneli", "canli harita", "canlı harita", "excel", "pdf", "cikti", "çıktı", "karsilastirma", "karşılaştırma"):
        actions = [("Yardım Merkezi", "/support")]
        if privileged:
            actions = [("Performans Dashboard", "/performance/dashboard"), ("Performans raporları", "/performance/reports"), ("Süreç raporları", "/performance/process-reports")]
        return AssistantReply(
            topic="raporlar_dashboard",
            answer=("Raporlar ve yönetici dashboard alanları yetki seviyesine göre açılır. Canlı performans haritası, riskli personel analizi, en geciken amirler, dönem bazlı tamamlanma ve kategori kırılımları gibi özetler yönetici görünürlüğü kapsamında değerlendirilir."),
            actions=_actions(*actions),
            suggestions=("Önce nereye bakmalıyım?", "AI karar destek nasıl kullanılmalı?"),
        )

    if _has(q, "canli", "canlı", "yukle", "yükle", "deploy", "sunucu", "yedek", "backup", "postgres", "waitress", "test"):
        return AssistantReply(
            topic="canliya_gecis",
            answer=("Canlıya geçişte önce yedek alınmalı, doğru PostgreSQL bağlantısı doğrulanmalı, overlay proje dosyasında test edilmeli, sonra Waitress yeniden başlatılmalıdır. Asistan overlay’i veritabanı migrasyonu yapmaz; bu yüzden canlı veri yapısını değiştirmez."),
            actions=_actions(("Yardım Merkezi", "/support"), ("Ana Sayfa", "/home")),
            suggestions=("Güvenlik ve KVKK açısından nelere dikkat etmeliyim?", "Raporlara ve canlı performans haritasına nereden ulaşırım?"),
        )

    if _has(q, "kilavuz", "kılavuz", "yardim merkezi", "yardım merkezi", "nasil kullanilir", "nasıl kullanılır"):
        return AssistantReply(
            topic="yardim_merkezi",
            answer=("BYS360 kullanımında ilk başvuru noktası Yardım Merkezi’dir. Kullanıcı rehberleri, destek talebi oluşturma, talep durumu takibi, sık sorulan konular ve yeni özelliklerin kullanım notları bu alanda toplanır. Asistan, ilgili başlığa hızlı ulaşmanız için yönlendirme yapar."),
            actions=_actions(("Yardım Merkezi", "/support"), ("Destek talebi aç", "/support/new"), ("Taleplerim", "/support/my-tickets")),
            suggestions=("Destek talebi nasıl açılır?", "Dönem içi notlar nasıl kullanılır?"),
        )

    return AssistantReply(
        topic="genel",
        answer=("Bu konuda size genel yönlendirme yapabilirim. BYS360’da en güvenli başlangıç Yardım Merkezi’nden ilgili başlığı açmak veya destek talebi oluşturmaktır. Asistan yalnızca bilgilendirme yapar; yetki dışı veri göstermez ve idari karar yerine geçmez."),
        actions=_actions(("Yardım Merkezi", "/support"), ("Destek talebi aç", "/support/new"), ("Ana Sayfa", "/home")),
        suggestions=("Ne sorabilirim?", "Önce nereye bakmalıyım?", "Yardım merkezi ve kullanım kılavuzu nerede?"),
    )
