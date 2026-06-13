# BYS360 Portal V3B — Sosyal Medya Paylaşımlarını Normal Portal Gönderisi Yapma

Bu paket X ve Instagram tekil gönderi bağlantılarını ayrı kart açmadan normal portal gönderisi olarak yayınlar.

## Önemli canlı kural
- API olmadan X/Instagram profil kazıma yapılmaz.
- Desteklenen güvenli kullanım: tekil gönderi bağlantısı, link havuzu ve tekrar paylaşım engeli.
- X için oEmbed denenir; erişim olmazsa güvenli blockquote bağlantısı kullanılır.
- Instagram için görsel/metin kopyalanmaz; gönderi bağlantısı embed/permalink olarak kullanılır.

## Kullanım
Yönetici ekranı: `/portal/social-import`

Komutla link işleme:
```powershell
C:\bys360\project\.venv\Scripts\python.exe .\scripts\portal\run_bys360_social_media_embed_scan_v3b.py --project-root "C:\bys360\project" --manual --url "https://x.com/TarihiAlan/status/..."
```
