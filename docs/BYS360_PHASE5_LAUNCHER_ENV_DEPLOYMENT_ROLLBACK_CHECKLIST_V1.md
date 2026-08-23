# BYS360 Faz 5 — Launcher / Environment / Deployment Kontrol Listesi (V1)

Versiyon: `BYS360_PHASE5_LAUNCHER_ENV_DEPLOYMENT_ROLLBACK_CHECKLIST_V1`
Kapsam: `phase5-critical-lint-clean-v1` branch'inde tamamlanan launcher/env
değişikliklerinin canlıya (`C:\bys360\project`) alınması için izlenmesi
gereken adımlar.

Bu belge **yalnızca dokümantasyondur**. Bu worktree'de hiçbir komut, migration,
restart veya dağıtım fiilen ÇALIŞTIRILMAMIŞTIR; aşağıdaki adımlar canlı
sunucudan sorumlu operatör tarafından uygulanmalıdır. `C:\bys360\project`,
`C:\bys360\releases`, `C:\bys360\live_backups`, `C:\bys360\live_rollbacks` ve
Windows Görev Zamanlayıcı bu görev kapsamında değiştirilmemiştir.

## 1. Ön hazırlık — commit ve kaynak export

- [ ] Değişiklikler `phase5-critical-lint-clean-v1` branch'inde ayrı, açıklayıcı
      commit(ler) halinde. Force-push veya amend kullanılmadı.
- [ ] `git status` temiz; beklenmeyen untracked/modified dosya yok.
- [ ] Release için kaynak, çalışan `.git` deposundan **temiz bir export** ile
      alınır (`git archive` veya eşdeğeri) — geliştirme sırasında oluşan
      `__pycache__`, `.pytest_cache`, geçici test dosyaları export'a dahil
      edilmez.
- [ ] HISTORICAL_REFERENCE (2026-08-23 güncellemesi): aşağıdaki "mevcut tooling" artık
      DEPRECATED'dır; canonical builder için DEPLOYMENT.md §8'e bakınız. Orijinal madde,
      değiştirilmeden korunmuştur: Mevcut tooling: `scripts\windows\build_bys360_secure_release_and_preflight_v1.ps1`
      → `scripts\security\build_bys360_secure_release_v1_5.py` ile zip üretip
      `scripts\security\bys360_release_zip_preflight_v1.py` ile preflight
      raporu (`reports\security\release_zip_preflight_v1`) üretiyor. Bu akış
      zip üretimini ve preflight kontrolünü kapsıyor; bulgu: script içinde
      SHA256/manifest üretimi **tespit edilmedi** (grep ile doğrulandı).

## 2. Manifest ve SHA256 listesi (mevcut tooling'de eksik — manuel tamamlanmalı)

**Güncelleme notu (2026-08-23, deterministic-package-builder hardening görevi):** bu bölümdeki
"eksik" bulgusu artık geçmişe aittir (HISTORICAL_REFERENCE) — orijinal metin altta korunmuştur,
değiştirilmemiştir. Canonical release builder `scripts\release\build_bys360_safe_release.py`
artık her build'de otomatik olarak `<output>.sha256sums.txt` (SHA256, göreli yol, sabit
sıralama) ve `<output>.manifest.json` (source SHA, dosya listesi, deterministik sıralama) üretir
ve bunları `--verify` ile doğrular. `scripts\security\build_bys360_secure_release_v1_5.py` ve
bu bölümde anılan eski preflight akışı artık DEPRECATED'dır; bkz. DEPLOYMENT.md §8.

Orijinal (2026 launcher/env görevi zamanındaki) metin, değiştirilmeden:

- [ ] Release zip'i üretildikten sonra, zip içindeki her dosya için SHA256
      hesaplanıp bir manifest dosyasına yazılır. Örnek (yalnızca referans,
      bu görevde ÇALIŞTIRILMADI):
      `Get-ChildItem -Recurse -File | Get-FileHash -Algorithm SHA256`
- [ ] Manifest, release zip'in yanına (`dist_secure\`) `MANIFEST_SHA256.txt`
      adıyla kaydedilir ve release ile birlikte arşivlenir.
- [ ] Zip'in kendisi için de tek bir SHA256 değeri hesaplanıp devreden teslim
      eden ile teslim alan arasında ayrı bir kanaldan (örn. sözlü/yazılı not)
      doğrulanır — böylece aktarım sırasında bozulma/değişiklik tespit edilir.
- [ ] **Bulgu (koordinatöre iletildi):** Bu adım şu an otomatik değil; ayrı bir
      backlog kalemi olarak `build_bys360_secure_release_v1_5.py` içine
      SHA256 manifest üretimi eklenmesi önerilir. Bu görev kapsamında bu
      python dosyasına dokunulmadı (dosya sahipliği dışında).

## 3. Environment kontrol listesi

- [ ] Canlı `.env` dosyası bu görevde güncellenen `.env.example` ile
      karşılaştırılır; yeni eklenen anahtarlar (`PREFERRED_URL_SCHEME`,
      `CSP_ENABLED`, `CSP_REPORT_ONLY`, `CSP_NONCE_ENABLED`,
      `CSP_ALLOW_UNSAFE_INLINE_SCRIPT`, `HSTS_POLICY`, `PROXY_FIX_ENABLED`,
      `PROXY_FIX_X_FOR`, `PROXY_FIX_X_HOST`, `PROXY_FIX_X_PORT`,
      `PROXY_FIX_X_PREFIX`, `PROXY_FIX_X_PROTO`) canlı `.env`'de bilinçli
      olarak set edilir veya `config.py` varsayılanlarına bilinçli olarak
      bırakılır (varsayılanlar production/staging'de zaten güvenli tarafta:
      `CSP_ENABLED=true`, `CSP_NONCE_ENABLED=true` (prod/staging),
      `PROXY_FIX_ENABLED=true` (prod/staging) — bkz. `config.py` satır
      ~172-360).
- [ ] `SECRET_KEY` canlıda güçlü ve benzersiz (32+ karakter, placeholder
      değil) — aksi halde `config.py` `APP_ENV in {production, staging}`
      durumunda `RuntimeError` ile açılışı reddediyor (kod davranışı; bu
      görevde sadece okunarak doğrulandı, değiştirilmedi).
- [ ] `SENTRY_DSN` canlıda gerçek bir DSN ile set edilmiş VEYA
      `SENTRY_REQUIRED_IN_PRODUCTION=false` bilinçli olarak seçilmiş.
      Doğrulanan kod davranışı (`app/core/monitoring.py`,
      `configure_optional_sentry`): DSN boşken uygulama **güvenli şekilde
      açılır** — `app.logger.warning("Sentry DSN tanimli degil; hata izleme
      kapali.")` yazar ve `SENTRY_REQUIRED_IN_PRODUCTION=true` +
      `APP_ENV` production/staging/live/canli/pilot değilse sessizce devam
      eder; `SENTRY_REQUIRED_IN_PRODUCTION=true` ise `RuntimeError` ile
      açılışı reddeder. Placeholder DSN (`change-me`, `sentry.io/...` vb.)
      de aynı şekilde güvenli biçimde reddedilir. Bu, kod okunarak
      doğrulanmıştır; herhangi bir düzeltme gerekmedi.
- [ ] `MAIL_*` / `SMTP_*` / `FILE_CENTER_SMTP_*` canlı değerleri doğru ve
      gerçek şifre `.env.example`'a asla yazılmadı (bu görevde doğrulandı).
- [ ] `DATABASE_URL` canlı veritabanına işaret ediyor, `sqlite:///:memory:`
      fallback'e düşmüyor.

## 4. Backup

- [ ] Dağıtımdan önce canlı `C:\bys360\project` dizininin ve canlı
      veritabanının `C:\bys360\live_backups` altına güncel bir yedeği
      alınmış olmalı (bu görev kapsamında bu dizine dokunulmadı/yedek
      alınmadı — operatör tarafından yapılmalı).
- [ ] Yedeğin geri yüklenebilir olduğu (checksum veya deneme restore ile)
      doğrulanmış olmalı.

## 5. Migration kontrolü

- [ ] Yeni migration var mı kontrol edilir (`alembic`/proje migration
      mekanizması — bu görevde migration dosyalarına dokunulmadı).
- [ ] Migration'lar önce yedek alınmış bir ortamda/staging'de denenir.
- [ ] Migration geri alınabilir mi (downgrade path) değerlendirilir ve
      rollback planına (bkz. Bölüm 9) not düşülür.
- [ ] **ZORUNLU RELEASE KAPISI (Bölüm 3D bulgusu, BYS360_SEC3D_ALEMBIC_SQLITE_FULL_CHAIN_BLOCKED_ENVIRONMENT):**
      Canlıya veya yeni temiz release'e geçmeden önce **disposable ya da
      staging PostgreSQL üzerinde** Alembic `base → head` upgrade,
      `current == head` ve `alembic check` doğrulanacaktır. Bu worktree'de
      izole bir SQLite veritabanında base→head zinciri denendi; zincir
      `71d0eccf02c0`/`e8c3f1a9b4d0`'a kadar hatasız uygulandı, ardından
      pre-existing (2026-07-07 tarihli, bu çalışma kapsamında hiç
      değiştirilmemiş) `migrations/versions/b7f4e2a1c9d0_add_ai_support_tables.py`
      içindeki PostgreSQL-özel ham SQL'de (`SERIAL PRIMARY KEY`, `NOW()`)
      SQLite uyumsuzluğu nedeniyle durdu. Bu makinede disposable bir
      PostgreSQL örneği bulunmadığından tam zincir PostgreSQL üzerinde
      doğrulanamadı:
      - `ALEMBIC_SQLITE_FULL_CHAIN=BLOCKED_ENVIRONMENT`
      - `MIGRATION_REGRESSION=NOT_FOUND`
      - `MIGRATION_FILES_CHANGED=0`
      - `NEW_REVISION_CREATED=0`
      - `REAL_DATABASE_TOUCHED=0`
      - Alembic head (tek): `e0efcd07abf7`
      Bu madde CSP güvenlik dönüşüm çalışmasından bağımsızdır ve o
      çalışmayı engellemez; yalnızca canlıya/yeni temiz release'e geçiş
      öncesi ayrı, zorunlu bir kapıdır.

## 6. Dağıtım adımları (yüksek seviye — bu görevde ÇALIŞTIRILMADI)

- [ ] Yeni release `C:\bys360\releases` altına açılır.
- [ ] `.env` canlı değerleriyle senkronize edilir (Bölüm 3).
- [ ] Bağımlılıklar `.venv` içinde güncellenir
      (`C:\bys360\project\.venv\Scripts\python.exe -m pip install -r requirements.txt`).
- [ ] Migration çalıştırılır (varsa).
- [ ] Servis (Waitress/Gunicorn) yeniden başlatılır.
- [ ] Windows Görev Zamanlayıcı görevleri (aşağıdaki Bölüm 8) yeniden
      kaydedilir/güncellenir.

## 7. Health doğrulaması

- [ ] Uygulama canlı portunda (`APP_HOST:APP_PORT` / `GUNICORN_BIND`) yanıt
      veriyor.
- [ ] Login ekranı ve temel kritik akışlar (giriş, ana sayfa) manuel/otomatik
      smoke testten geçiyor (`BYS360_SMOKE_BASE_URL` ile ilişkili mevcut
      smoke test mekanizması kullanılabilir).
- [ ] Uygulama loglarında (`LOG_FOLDER`/`BYS360_LOG_DIR`) açılışta
      beklenmeyen hata/traceback yok.
- [ ] `bys360_sentry_enabled` (varsa Sentry) beklenen duruma göre
      etkin/pasif.

## 8. HSTS doğrulaması

- [ ] Canlı HTTPS üzerinden yanıt veren bir uçtan `Strict-Transport-Security`
      header'ı kontrol edilir; değeri `.env`'deki `HSTS_POLICY` (veya
      `config.py` varsayılanı `max-age=31536000; includeSubDomains`) ile
      eşleşiyor.
- [ ] HSTS header'ı yalnızca gerçek HTTPS bağlantılarda gönderiliyor (HTTP
      üzerinden test edilen bir istekte yanlışlıkla HSTS zorlanmadığı teyit
      edilir — reverse proxy/`PROXY_FIX_*` ayarları ile `PREFERRED_URL_SCHEME`
      tutarlı olmalı).

## 9. CSP doğrulaması

- [ ] Canlı sayfa yanıtlarında `Content-Security-Policy` header'ı mevcut
      (`CSP_ENABLED=true` iken) ve `CSP_REPORT_ONLY` beklenen moda göre
      (production'da `false` = enforce, aksi halde `Content-Security-Policy-Report-Only`).
- [ ] `CSP_NONCE_ENABLED=true` iken sayfa kaynağında script tag'lerinde
      nonce attribute'u üretiliyor ve header'daki nonce ile eşleşiyor.
- [ ] `CSP_ALLOW_UNSAFE_INLINE_SCRIPT=false` (varsayılan/önerilen) iken
      `'unsafe-inline'` script-src içinde YOK.
- [ ] Tarayıcı konsolunda CSP ihlali/violation hatası yok (özellikle login,
      ana sayfa, dosya merkezi gibi kritik ekranlarda).

## 10. Scheduler doğrulaması

- [ ] `install_bys360_cic_auto_mail_scheduler_task.ps1` çalıştırıldıktan
      sonra `BYS360 CIC Auto Mail Scheduler` görevi Görev Zamanlayıcı'da
      "Ready" durumda ve 5 dakikada bir tetikleniyor.
- [ ] `scripts\windows\run_cic_auto_mail_scheduler.ps1` ilk birkaç
      tetiklemede `C:\bys360\logs\cic_auto_mail_scheduler.log` dosyasına
      START/END satırları yazıyor; art arda binen (overlapping) çalışma
      olmadığı (SKIP satırları varsa normal, hata değil) log üzerinden teyit
      edilir.
- [ ] `install_bys360_daily_weather_mail_task.ps1` / `install_bys360_daily_mail_tasks_v1_4.ps1`
      çalıştırıldığında `scripts\communication\run_daily_weather_personnel_mail.ps1`
      installer tarafından **yeniden üretilir** (`Install-BysTask` fonksiyonu
      `Set-Content` ile üzerine yazar) — canlıdaki dosya bu repodaki statik
      kopyadan farklı olabilir; bu beklenen bir davranıştır, hata değildir.
- [ ] `BYS360 Daily Weather Personnel Mail` görevi planlanan saatte
      (`WeatherHour:WeatherMinute`) tetiklenip `C:\bys360\logs\daily_weather_personnel_mail.log`
      dosyasına yazıyor.
- [ ] İlk canlı doğrulama, mümkünse `--dry-run` bayrağıyla manuel bir deneme
      çalıştırmasıyla yapılır (`send_daily_weather_personnel_mail.py
      --dry-run`) — gerçek mail göndermeden log/sonuç kontrolü sağlar. Bu
      görev kapsamında bu komut ÇALIŞTIRILMADI, yalnızca script'in
      `--dry-run` bayrağını desteklediği kaynak kodundan doğrulandı.
- [ ] Hafta sonu kilidi (CIC için "hafta içi kuralı") beklenen şekilde
      çalışıyor — cumartesi/pazar otomatik mail gönderilmiyor
      (`weekend_blocked` alanı log/JSON çıktısında görülebilir).

## 11. Rollback planı

- [ ] Rollback tetikleyici kriterleri önceden tanımlı (örn. health check
      başarısız, kritik hata oranı eşik üstü, migration hatası).
- [ ] Rollback adımı: yeni release devre dışı bırakılır, `C:\bys360\live_rollbacks`
      altındaki (veya Bölüm 4'te alınan) önceki çalışır sürüm
      `C:\bys360\project` konumuna geri yüklenir.
- [ ] Migration geri alınabilir migration ise downgrade çalıştırılır; değilse
      (örn. veri kaybına yol açacak migration) rollback öncesi veritabanı
      yedeği ayrıca geri yüklenir.
- [ ] Görev Zamanlayıcı görevleri (CIC, Weather, Pulse) önceki sürümün
      launcher/installer script'leriyle tutarlı hale getirilir — yeni
      launcher'lar (`run_cic_auto_mail_scheduler.ps1`,
      `run_daily_weather_personnel_mail.ps1`) eski sürümde yoksa,
      rollback sırasında ilgili Scheduled Task'ların da eski davranışa
      (veya devre dışı) döndürüldüğü teyit edilir.
- [ ] Rollback sonrası Bölüm 7 (health), 8 (HSTS) ve 9 (CSP) maddeleri
      tekrar doğrulanır.
- [ ] Rollback kararı ve nedeni, mevcut `rollback_bys360_home_prestige_safe_v1a.ps1`
      benzeri script'lerin ürettiği rapor formatına uygun şekilde
      kayıt altına alınır.

## Durum özeti

Bu belge PASS/FAIL bildirmez — yalnızca izlenmesi gereken adımların
listesidir. Her madde, ilgili canlı dağıtım sırasında operatör tarafından
işaretlenmelidir. Bu görev kapsamında yukarıdaki hiçbir adım fiilen
çalıştırılmamıştır.
