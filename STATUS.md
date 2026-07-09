# BYS360 STATUS.md

## 2026-07-08 â€” Devredilebilirlik TemizliÄŸi ve Kaynak Paket StandardÄ±

### Ã–zet

BYS360 kaynak aÄŸacÄ±nda devredilebilirliÄŸi dÃ¼ÅŸÃ¼ren tek kullanÄ±mlÄ±k script, iÃ§ iÃ§e proje kopyasÄ±, backup/log/instance kalÄ±ntÄ±sÄ± ve eski overlay raporlarÄ±nÄ±n ayrÄ±ÅŸtÄ±rÄ±lmasÄ± baÅŸlatÄ±ldÄ±.

### Kararlar

- Aktif `scripts/` alanÄ±nda yalnÄ±zca CI/test/dokÃ¼man tarafÄ±ndan kullanÄ±lan veya elle onaylanmÄ±ÅŸ scriptler kalacak.
- ReferanssÄ±z `ARCHIVE_CANDIDATE` scriptleri Task Scheduler kontrolÃ¼nden sonra `scripts/archive/pre_handover_YYYYMMDD/` altÄ±na taÅŸÄ±nacak.
- `project/project/`, `backups/`, `logs/`, `instance/*.sqlite*`, `.bak` ve gerÃ§ek `.env` dosyalarÄ± kaynak paketten Ã§Ä±karÄ±lacak.
- README proje tanÄ±tÄ±mÄ± ve hÄ±zlÄ± kurulum dokÃ¼manÄ± olarak yeniden yazÄ±lacak.
- STATUS gÃ¼ncel durumun tek kaynaÄŸÄ± olarak sÃ¼rdÃ¼rÃ¼lecek; her temizlik/geliÅŸtirme turunda yeni rapor yÄ±ÄŸÄ±nÄ± yerine bu dosya gÃ¼ncellenecek.

### SayÄ±sal Durum

- Script envanteri: 365 kayÄ±t
- KEEP: 49
- REVIEW: 27
- ARCHIVE_CANDIDATE: 90
- ALREADY_ARCHIVED: 199

### Sonraki Ä°ÅŸler

1. Task Scheduler raporu ile `ARCHIVE_CANDIDATE` listesini karÅŸÄ±laÅŸtÄ±r.
2. GÃ¼venli olan adaylarÄ± `git mv` ile arÅŸivle.
3. Repo gÃ¼rÃ¼ltÃ¼sÃ¼nÃ¼ temizle.
4. README ve STATUS deÄŸiÅŸikliklerini normal commit olarak iÅŸle.
5. CI ve temel smoke testleri Ã§alÄ±ÅŸtÄ±r.

## 2026-07-08 - Faz 2A SQL Identifier Trace

Kapsam:
- app/routes_president_scorecard_v2.py
- app/services/menu_visibility.py
- app/services/assistant_role_matrix_v10.py
- app/services/executive_mail_center.py
- app/schema_guard_engine.py

Sonuc:
- Kritik dosyalarda dis kullanici girdisine dogrudan bagli SQL identifier kullanimi tespit edilmedi.
- routes_president_scorecard_v2.py icinde tablo ve siralama alanlari sabit aday listeleri ve kolon kontrolu uzerinden geliyor.
- menu_visibility.py icinde tablo secimi candidate table listeleri uzerinden yapiliyor; kullanici/rol degerleri params ile baglaniyor.
- assistant_role_matrix_v10.py icinde request.form yalnizca checkbox gorunurluk degeri icin kullaniliyor; SQL kolonlari role_menu_defaults kolon kontrolu ve sabit aday kolon listeleriyle belirleniyor.
- executive_mail_center.py icinde tablo secimi sabit mail log aday listesi uzerinden yapiliyor.
- schema_guard_engine.py icinde tablo bilgisi ic schema repair/patch tanimlarindan geliyor.

Karar:
- Faz 2A kapsamindaki bes kritik dosyada acil kod degisikligi gerektiren SQL injection bulgusu yok.
- Proje genelinde dinamik SQL kullanimi yaygin oldugu icin genel SQL envanteri Faz 2A disinda ayri teknik borc basligi olarak izlenecek.

Test:
- Faz 2A read-only trace sonrasi git calisma agaci temizdi.
