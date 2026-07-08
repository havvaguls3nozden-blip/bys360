# BYS360 AI Destekli Ekran Rehberi Working V2

Bu paket, ekranlarda görünen ancak kullanıcı tıklayınca işlevsiz kalan **AI destekli ekran rehberi** kartını gerçek çalışan rehber haline getirir.

## Ne değişti?

- `bys360_ai_everywhere_v2.js` eklendi.
- Kart üzerindeki soru butonları artık kart içinde anlık rehber cevabı üretir.
- Aynı soru kanonik `BYS360AssistantModule` paneline de aktarılır.
- Asistan paneli geç yüklenirse kısa süre beklenip tekrar denenir.
- `base.html` V1 yerine V2 JS/CSS dosyalarını yükler.

## Güvenlik sınırı

Kart idari karar vermez, performans puanı üretmez, kişisel/hassas veri göstermez. Sadece ekran amacı, işlem sırası, yetki kontrolü ve güvenli yönlendirme üretir.

## Kontrol

Tarayıcıda herhangi bir BYS360 sayfasında:

1. AI destekli ekran rehberi kartı görünmeli.
2. `Asistana sor` veya örnek soru butonuna basılmalı.
3. Kart içinde `Rehber cevabı` alanı açılmalı.
4. BYS360 Asistanı paneli açılmalı ve soru sohbet alanına aktarılmalı.
