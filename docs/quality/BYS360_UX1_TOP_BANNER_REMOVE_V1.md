# BYS360 UX-1 Top Banner Remove V1

Bu hotfix, UX-1 ile eklenen global üst bant rehberini kaldırır.

## Karar
- Sayfa en üstündeki geniş `Kısa ekran mantığı` paneli render edilmez.
- Üst banttaki `Detayları göster/gizle` ve `Ekran rehberine sor` butonları kaldırılır.
- Mevcut küçük AI destekli ekran rehberi kartı korunur.
- Uzun metin sadeleştirme ve ana işlem butonu odaklama davranışı korunur.

## Neden
Kullanıcı geri bildirimi: üst bant görsel olarak ağır, ekranı kalabalıklaştırıyor ve aç/kapat davranışı beklenen deneyimi vermiyor.

## Kontrat
- `bys360-ux1-quick-logic` JS tarafından enjekte edilmez.
- CSS güvenlik katmanı olarak `.bys360-ux1-quick-logic` alanını gizler.
- Cache bust değeri `ux1-top-banner-remove-v1` olarak güncellenir.
