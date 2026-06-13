# BYS360 Android Responsive Visual Regression Guide P6A

Bu belge, P5F ile kapanan Android responsive teslim kanıtının gerçek cihaz/görsel UAT bulguları ile izlenmesi için oluşturulmuştur.

## Kaynak Kanıt
- P5F final evidence report: `reports/architecture/BYS360_ANDROID_RESPONSIVE_FINAL_EVIDENCE_GATE_P5F_REPORT.json`
- Beklenen cihaz sayısı: `7`
- Beklenen hedef yüzey sayısı: `0`

## Screenshot Klasörü
- `reports/visual/android_responsive_p6a/screenshots`

Screenshot zorunlu değildir; fakat gerçek cihaz kontrolünde görsel kanıt eklenirse bu klasöre alınır.

## Kontrol Kapsamı
- 360px küçük Android
- 393/412px standart Android
- 480px büyük Android
- 600/768px fold/tablet
- 851x393 landscape
- dashboard, home, evaluation_form, admin_ai
- geniş tablolar, geniş formlar, modal/sidebar ve dokunma alanları

## Kabul Kuralı
P5F zinciri temiz kalmalı, P5B/P5C CSS dosyaları base.html üzerinden yüklü olmalı ve yeni UAT bulguları varsa P6A bulgu şablonuyla kayıt altına alınmalıdır.
