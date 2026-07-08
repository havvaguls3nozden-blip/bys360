# BYS360 Canlı Paket İlk 10/10 Değerlendirmesi

## İlk bulgular

- Zip toplam sıkıştırılmış boyut: yaklaşık 351 MB.
- Açılmış toplam içerik: yaklaşık 1.05 GB.
- Paket içinde `.env` kayıtları bulundu; gerçek canlı sırların rotate edilmesi gerekir.
- Paket içinde `.venv/`, `.dart_tool/`, `__pycache__/`, `.git/`, `instance/`, `logs/` ve iç içe `project/` kopyaları bulundu.
- `app/templates/portal/_post_card.html` içinde `post.body|replace(... )|safe` kullanımı görüldü.
- Aynı dosyada `attachment.stored_path|safe` ile sosyal embed render ediliyor.
- `base.html` içinde `attrs|safe` makro kullanımı var.
- `corporate_information_center/overview.html` içinde `problems|join('<br>')|safe` kullanımı var.
- CI workflow şu an `tests/security` ve `tests/critical` klasörlerini ana akışta çalıştırmıyor; ruff/mypy kapsamı da dar.

## İlk karar

Önce Red Gate V1 uygulanmalı: XSS düzeltmesi, regresyon testi, paket hijyeni, SECRET_KEY sadeleştirmesi ve CI kapsam genişletme.

## Dikkat

Bu raporda secret değerleri özellikle gösterilmemiştir. `.env` paket dışına çıkarılmalı ve canlıda kullanılmış olabilecek tüm sırlar döndürülmelidir.
