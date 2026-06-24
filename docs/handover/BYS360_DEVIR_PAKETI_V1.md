# BYS360 Devir Paketi V1

## Amaç

Bu dosya, BYS360’ı yeni bir geliştiriciye veya teknik ekibe devretmek için gereken ana bilgi setini özetler. Ayrıntılı kurulum, canlıya alma, güvenlik, modül envanteri ve yedekleme adımları aynı klasördeki diğer dosyalara ayrılmıştır.

## Devirde teslim edilecekler

- Temiz kaynak kod release zipi
- Migration dosyaları
- `requirements.txt` ve `requirements-dev.txt`
- `DEPLOYMENT.md`
- `BACKUP_RUNBOOK.md`
- `SECURITY.md`
- `docs/handover/` klasörü
- Test ve kalite gate komutları
- Canlı ortam ayarlarının gizli kanaldan teslim prosedürü

## Devirde teslim edilmeyecekler

- `.env`
- `.git`
- canlı veritabanı dumpı, güvenli kanal dışında
- log dosyaları
- SQLite geliştirme veritabanı
- imzalama anahtarları
- gerçek parola/token/API anahtarı

## İlk okuma sırası

1. `BYS360_KURULUM_REHBERI.md`
2. `BYS360_CANLIYA_ALMA_REHBERI.md`
3. `BYS360_BAKIM_RUNBOOK.md`
4. `BYS360_GUVENLIK_KVKK_NOTLARI.md`
5. `BYS360_MODUL_ENVANTERI.md`
6. `BYS360_RISK_VE_SUREKLILIK_PLANI.md`

## Teknik çerçeve

BYS360 Flask tabanlı, PostgreSQL/SQLite destekli, Waitress ile canlıda koşturulan, modüler ama ortak kimlik-yetki-ayar omurgası kullanan kurumsal yönetim platformudur.

## Devir kabul kontrolü

- [ ] Temiz release zipinde `.env`, `.git`, log, SQLite ve backup yok.
- [ ] Kurulum dokümanı okunarak lokal ortam kurulabiliyor.
- [ ] `python -m compileall app config.py scripts migrations` geçiyor.
- [ ] `/healthz` çalışıyor.
- [ ] Login sayfası açılıyor.
- [ ] Migration yolu belgelenmiş.
- [ ] Rollback yolu belgelenmiş.
- [ ] Yetki ve güvenlik sınırları belgelenmiş.
