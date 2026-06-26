# BYS360 Phase UX-1 — Sade Ekran ve Kullanıcı Mantığı Temizliği

Bu paket, BYS360 ekranlarındaki “çok fazla yazı var, mantığını anlamıyoruz” eleştirisini karşılamak için hazırlanmıştır.

## Amaç

Kullanıcı ilk bakışta şunları görmelidir:

- Bu ekran ne işe yarar?
- Şimdi hangi işlemi yapmalıyım?
- Hangi adımları takip etmeliyim?
- Kritik uyarı nedir?
- Detay gerekiyorsa nereden açılır?

## Uygulanan standart

Her sayfaya otomatik bir **Kısa ekran mantığı** kartı eklenir.

Kart şunları gösterir:

1. Sayfanın kısa amacı
2. 3 adımlı işlem akışı
3. Kritik güvenlik/yetki/onay uyarısı
4. Detayları göster/gizle butonu
5. Ekran rehberine sor butonu

## Uzun metin politikası

Uzun açıklamalar tamamen silinmez. Varsayılan olarak kısaltılır, kullanıcı isterse **Detayı göster** ile tamamını açar.

Bu yaklaşım bilgi kaybı oluşturmaz; yalnızca ilk ekran yükünü azaltır.

## Başarı kriteri

- Kullanıcı ekran amacını 5 saniyede anlamalıdır.
- Ana işlem akışını 10 saniyede görebilmelidir.
- Uzun proje/metin açıklamaları varsayılan görünümü boğmamalıdır.
- Teknik kelimeler kullanıcı karşısında öne çıkmamalıdır.

## Dosyalar

- `app/static/js/bys360_ux1_simple_screen_guide.js`
- `app/static/css/bys360_ux1_simple_screen_guide.css`
- `scripts/windows/repair_bys360_ux1_simple_screen_guide_v1.ps1`
- `tests/quality/test_ux1_simple_screen_guide_contract.py`
