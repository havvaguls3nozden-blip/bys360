# BYS360 A?ama 7B Rollback / Yedek Plan?

Tarih: 2026-06-12T13:42:17

## ?zet

- OK: True
- Eksik girdi: []
- Son A6 evidence zip: `C:\bys360\releases\BYS360_A6_SECURITY_EVIDENCE_20260612_133606.zip`

## Yay?n ?ncesi Al?nacak Yedekler

### 1. Kod paketi yede?i
- Ama?: Canl?ya ??kmadan ?nce ?al??an mevcut kodun geri d?n?lebilir kopyas? al?n?r.
- Komut ?ablonu: `Compress-Archive -Path C:\bys360\project\* -DestinationPath C:\bys360\backups\BYS360_CODE_BACKUP_<timestamp>.zip -Force`
- ??ermeli: app, scripts, migrations, templates, static, requirements, config dosyalar?
- ??ermemeli: .env, instance, reports, quarantine, .venv, __pycache__, SQLite/DB dosyalar?

### 2. PostgreSQL veri taban? yede?i
- Ama?: Canl? verinin yay?n ?ncesi geri d?n?? noktas? al?n?r.
- Komut ?ablonu: `pg_dump --format=custom --file=C:\bys360\backups\BYS360_DB_BACKUP_<timestamp>.dump <DATABASE_URL veya ba?lant? parametreleri>`
- ??ermeli: T?m ?ema ve veri
- ??ermemeli: Parola a??k metin olarak rapora yaz?lmamal?

### 3. Windows servis / g?rev yede?i
- Ama?: Waitress/servis/zamanlanm?? g?rev ayarlar? geri al?nabilir hale getirilir.
- Komut ?ablonu: `sc.exe qc "BYS360 Live Waitress 80" > C:\bys360\backups\BYS360_SERVICE_QC_<timestamp>.txt`
- ??ermeli: Servis ad?, ?al??ma yolu, kullan?c?, port, ba?latma komutu
- ??ermemeli: Servis hesab? parolas?

### 4. Zamanlanm?? g?rev yede?i
- Ama?: Otomatik mail, ?zet ve zamanl? i?ler canl? ?ncesi kay?t alt?na al?n?r.
- Komut ?ablonu: `schtasks /Query /FO LIST /V > C:\bys360\backups\BYS360_SCHEDULED_TASKS_<timestamp>.txt`
- ??ermeli: G?rev ad?, tetikleyici, komut, son ?al??ma durumu
- ??ermemeli: Parola/gizli anahtar

### 5. Env s?zle?mesi kontrol?
- Ama?: Canl? ortam de?i?kenleri strict gate?e uygun olmal?.
- Komut ?ablonu: `python scripts/security/validate_a6e_production_env_contract.py --env-file <canli_env_yolu> --strict`
- ??ermeli: DATABASE_URL PostgreSQL + sslmode=require/verify, SENTRY_DSN, SECRET_KEY, secure cookies, CSRF/CSP a??k
- ??ermemeli: .env i?eri?ini evidence paketine koyma

## Rollback Ad?mlar?

- 1. Canl? yay?ndan ?nce bak?m penceresi ve sorumlu ki?i belirlenir.
- 2. Kod yede?i, DB yede?i, servis/g?rev yede?i al?nmadan yay?n yap?lmaz.
- 3. Yeni paket uygulan?r.
- 4. Uygulama ba?lat?l?r ve smoke test yap?l?r.
- 5. Kritik hata varsa servis durdurulur.
- 6. ?nceki kod yede?i geri a??l?r.
- 7. Gerekirse PostgreSQL dump geri y?klenir.
- 8. Servis/zamanlanm?? g?rev ayarlar? ?nceki kayda g?re geri al?n?r.
- 9. Tekrar smoke test yap?l?r.
- 10. Sonu? raporlan?r.

## Go / No-Go Kriterleri

- A7A OK=True olmal?.
- A6 evidence zip mevcut olmal?.
- Release s?z?nt? say?s? 0 olmal?.
- Strict env gate canl? de?erlerle ge?meli.
- compileall exit code 0 olmal?.
- ruff F821 exit code 0 olmal?.
- DB yede?i al?nmadan canl? uygulama yap?lmamal?.
- Rollback paketi do?rulanmadan canl? uygulama yap?lmamal?.

## Karar

A7B sonucu: Rollback/yedek plan? i?in gerekli temel kan?t girdileri mevcut. Canl?ya dokunmadan plan kayd? olu?turuldu.