# BYS360 Android Responsive Visual UAT Checklist - P5E

Olusturma zamani: 2026-06-11T23:03:54

## Kaynak kanit

- P5D V2 release suite: `C:\bys360\project\reports\architecture\BYS360_ANDROID_RESPONSIVE_RELEASE_SUITE_GATE_P5D_V2_REPORT.json`
- Cihaz sayisi: 7
- Hedef yuzey sayisi: 0
- Responsive marker toplam: 2528

## Android cihaz matrisi

| Durum | Genislik | Yukseklik | Yon | Not |
|---|---:|---:|---|---|
| Android small | 360 | 640 | portrait | Kontrol edildi / edilecek |
| Android compact | 393 | 851 | portrait | Kontrol edildi / edilecek |
| Android standard | 412 | 915 | portrait | Kontrol edildi / edilecek |
| Android large phone | 480 | 960 | portrait | Kontrol edildi / edilecek |
| Android fold/tablet narrow | 600 | 960 | portrait | Kontrol edildi / edilecek |
| Android tablet | 768 | 1024 | portrait | Kontrol edildi / edilecek |
| Android landscape | 851 | 393 | landscape | Kontrol edildi / edilecek |

## Hedef ekran/yuzey kontrolleri

### Ana panel / dashboard

- Release suite kapsami: HAYIR
- [ ] kart taşması yok
- [ ] grid tek kolona düşer
- [ ] yatay kaydırma yalnız tabloda

### Ana sayfa

- Release suite kapsami: HAYIR
- [ ] hero/özet kartları taşmaz
- [ ] butonlar 44px dokunma alanını korur

### Performans değerlendirme formu

- Release suite kapsami: HAYIR
- [ ] puanlama alanları alt alta kırılır
- [ ] tablo/form taşması kontrollü scroll olur

### Admin AI / karar destek ekranları

- Release suite kapsami: HAYIR
- [ ] dar ekranlarda kartlar kırılır
- [ ] aksiyon butonları satır içinde sıkışmaz

### Geniş tablolar

- Release suite kapsami: HAYIR
- [ ] tablo dış container taşmaz
- [ ] scroll sadece tablo içinde kalır

### Geniş formlar

- Release suite kapsami: HAYIR
- [ ] input/select/textarea tam genişlik olur
- [ ] label-input düzeni okunur kalır

### Küçük Android ekran

- Release suite kapsami: EVET
- [ ] 360px genişlikte yatay gövde taşması yok
- [ ] modal/sidebar ekranı kaplamaz

### Android landscape

- Release suite kapsami: EVET
- [ ] yükseklik daralınca içerik scroll edilebilir
- [ ] üst menü/butonlar üst üste binmez

## Kabul kurallari

- [ ] 360px küçük Android genişlikte gövde yatay taşma üretmemeli.
- [ ] 393/412px standart Android genişliklerinde kart ve form düzeni okunur kalmalı.
- [ ] 600/768px fold-tablet aralığında gereksiz tek kolon sıkışması olmamalı.
- [ ] Landscape görünümde üst menü, modal, tablo ve form alanları çakışmamalı.
- [ ] Geniş tablolar yalnız kendi container içinde yatay scroll kullanmalı.
- [ ] Form inputları, selectler ve aksiyon butonları dokunma alanını korumalı.
- [ ] P5B ve P5C CSS dosyaları base.html üzerinden yüklü kalmalı.

## Opsiyonel ekran goruntusu kaniti

- Klasor: `C:\bys360\project\reports\visual\android_responsive_p5e\screenshots`
- Bulunan ekran goruntusu sayisi: 0
- Not: P5E icin screenshot zorunlu degildir; gorsel UAT sonrasi bu klasore eklenirse raporda sayilir.
