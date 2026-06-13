# BYS360 Teknik Borç Temizlik Sırası — V2.17.0

Bu sıra, canlı uygulamayı bozmadan teknik borcu azaltmak için önerilir.

## P0 — Repo güvenliği ve hijyen

1. `.gitignore` güçlendirilecek.
2. `.env` gerçek değerleri repodan çıkarılacak.
3. `.env.example` üretilecek.
4. `.venv`, `.backup`, `.quality_backup`, `.bak`, `tmp_*` Git takibinden çıkarılacak.
5. Backup klasörleri `_local_quarantine` altına alınacak.
6. Parola/token rotasyonu yapılacak.
7. `compileall` ve `git status` kontrol edilecek.

## P1 — Route dosyası teknik borcu

1. `50KB+` route dosyaları raporlanacak.
2. Önce sadece en büyük dosyalar ele alınacak.
3. Route içindeki iş mantığı `services/` altına taşınacak.
4. Blueprint dosyaları sadece endpoint ve request/response katmanı olarak kalacak.
5. Her parçalama sonrası compileall ve route smoke test yapılacak.

Önerilen ilk hedefler:

- `app/api/mobile/routes.py`
- `app/communication/*phase*_routes.py`
- `app/admin/ai_phase*_routes.py`
- Büyük `menu_registry.py` veya katalog dosyaları

## P2 — Phase dosyalarının konsolidasyonu

1. Aynı modüle ait `phase1`, `phase2`, `phase3` dosyaları gruplanacak.
2. Aktif kullanılan route'lar manifest ile doğrulanacak.
3. Eski/boş/tekrar route dosyaları pasifleştirilecek.
4. Aktif fonksiyonlar tek modül dosyasına veya servis katmanına alınacak.
5. Kullanıcıya görünen hiçbir endpoint bozulmadan alias/redirect korunacak.

## P3 — Test ve kalite kapısı

1. `python -m compileall app config.py scripts`
2. Startup audit
3. Route registry check
4. Alembic heads check
5. Login/logout smoke test
6. Kurumsal Bilgilendirme CSRF test
7. Performans düşük puan/onay smoke test
8. Mobil API health test

## Kural

Önce güvenlik ve repo hijyeni tamamlanmadan büyük refactor yapılmamalıdır. Çünkü dirty repo üzerinde refactor yapılırsa neyin gerçek kod, neyin yedek/deneme olduğu karışır.
