# BYS360 Mobile Route Refactor P1.2

Bu paket **route fonksiyonlarını taşımaz**. Amacı, P1.3 ve sonrası için güvenli servis klasörü, manifest ve sağlık kontrol omurgası kurmaktır.

## P1.2 kapsamı

- `app/api/mobile/services/` klasörü oluşturulur.
- Mobil route grupları için servis dosyaları oluşturulur.
- `split_manifest.py` ile hedef bölme haritası yazılır.
- Aktif URL, endpoint, blueprint veya route decorator değiştirilmez.
- `compileall` ve `create_app` sağlık testi yapılır.

## P1.3 için önerilen ilk mikro adım

En güvenli başlangıç: `auth` ve `health` gibi küçük, düşük bağımlılıklı mobil fonksiyonlar.
