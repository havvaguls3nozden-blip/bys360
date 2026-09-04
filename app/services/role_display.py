"""BYS360 shared role display-label source (H1E-N1 display layer).

Tek doğru kaynak: uygulama genelinde birbirinden bağımsız olarak birden çok
yerde tekrar tanımlanmış aynı kapalı rol sözlüğünü (admin, baskan,
baskan_yardimcisi, grup_baskani, mali_musavir, birim_sorumlusu, koordinator,
hukuk_musaviri, personel) burada tek yerden Türkçe ekran etiketine çevirir.

Bu modül YALNIZCA görüntüleme (display/label) katmanı içindir: rol KOD
değerini, yetkilendirme/izin mantığını veya rol önceliğini asla değiştirmez.
Sadece ekranda gösterilecek Türkçe metni üretir.

Kapalı sözlükte bulunmayan (bilinmeyen/gelecekte eklenecek) dolu bir rol
değeri için ham İngilizce/machine değerini -- title-case edilmiş haliyle
bile -- asla ekrana yansıtmaz; güvenli, kurumsal "Bilinmiyor" karşılığını
döner. Boş/None girdi için özel bir iş kuralı olan çağıranlar (ör. boş rolü
"personel" varsayılan rolüne eşleyen ya da satırı tamamen atlayan kod)
kendi boş-girdi davranışını KORUR; bu modül yalnızca "dolu ama eşlenmemiş"
durumu güvenli hale getirmek için kullanılır.
"""
from __future__ import annotations

ROLE_DISPLAY_LABELS: dict[str, str] = {
    "admin": "Admin",
    "baskan": "Başkan",
    "baskan_yardimcisi": "Başkan Yardımcısı",
    "grup_baskani": "Grup Başkanı",
    "mali_musavir": "Mali Müşavir",
    "birim_sorumlusu": "Birim Sorumlusu",
    "koordinator": "Koordinatör",
    "hukuk_musaviri": "Hukuk Müşaviri",
    "personel": "Personel",
}

UNKNOWN_ROLE_DISPLAY_LABEL = "Bilinmiyor"


def role_display_label(role_value: str | None) -> str:
    """Bilinen bir rol koduna karşılık gelen Türkçe ekran etiketini döner.

    Kapalı sözlükte olmayan dolu bir değer için ham metni (title-case
    edilmiş haliyle dahi) asla yansıtmaz; güvenli "Bilinmiyor" karşılığını
    döner. Boş/None girdi de aynı güvenli karşılığı alır -- çağıranın
    kendine özgü bir boş-girdi varsayılanı varsa (ör. "personel" varsayılan
    rolü) bu fonksiyonu çağırmadan önce kendi kuralını uygulamalıdır.
    """
    text = str(role_value or "").strip()
    if not text:
        return UNKNOWN_ROLE_DISPLAY_LABEL
    return ROLE_DISPLAY_LABELS.get(text, UNKNOWN_ROLE_DISPLAY_LABEL)


__all__ = [
    "ROLE_DISPLAY_LABELS",
    "UNKNOWN_ROLE_DISPLAY_LABEL",
    "role_display_label",
]
