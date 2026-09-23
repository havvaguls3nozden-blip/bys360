Doküman Adı: BYS360 Veritabanı ve Migration Yönetimi
Doküman Türü: Teknik / Mimari
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası, yerel HEAD değil)
Son Güncelleme: 2026-09-02

---

## 1. Kapsam

Bu doküman BYS360'ın veritabanı katmanını ve migration (şema geçişi) yönetim modelini, kod ve çalıştırılabilir doğrulama üzerinden tarif eder. Yedekleme prosedürünün adım adım işletimi ve cutover/rollback operasyonel akışı Belge 06 ve Belge 14 kapsamındadır; burada yalnızca ilişki ve mimari sözleşme düzeyinde referans verilir.

## 2. PostgreSQL rolü ve SQLite ilişkisi

- **Canlı ortam:** PostgreSQL 15, Windows servis adı `postgresql-x64-15` (`docs/handover/LIVE_INSTALLATION.md:62-65`, `DOCUMENTATION_DERIVED`). Bu servis-adı kontrolü yalnızca eski/tarihsel `scripts/windows/deploy_bys360_ec4e56b_production_v1..v4.ps1` script'lerinde bulunur (`SCRIPT_VERIFIED`, `grep` ile doğrulandı) — bu script'ler bu current-state fazının kapsamı dışındaki, farklı bir SHA'ya (`ec4e56b`) ait, izlenmeyen (untracked) dosyalardır. Güncel `prepare_bys360_candidate.ps1`/`cutover_bys360_candidate.ps1` script'leri bu kontrolü **içermez** (bkz. Belge 03 §3, negatif `grep` sonucu).
- **Yerel geliştirme/test/CI varsayılanı:** SQLite. `config.py:544`: `_raw_database_url = (os.getenv("DATABASE_URL") or "").strip() or 'sqlite:///:memory:'` — `DATABASE_URL` tanımlı değilse uygulama **bellek içi SQLite**'a düşer (`CODE_VERIFIED`).
- **Docker/pilot profili:** `docker-compose.yml` içinde `postgres:15-alpine` imajı kullanılır (`CODE_VERIFIED`).
- SQLAlchemy 2.0.36 (`Flask-SQLAlchemy` 3.1.1 üzerinden), `psycopg2-binary` 2.9.9 PostgreSQL sürücüsü olarak `requirements.txt`'te sabitlenmiştir (`CODE_VERIFIED`).

## 3. Migration modeli: Flask-Migrate / Alembic, tek zincir

- `migrations/versions/` altında **77 `.py` dosyası** bulunur (`CODE_VERIFIED`, bu oturumda yeniden sayıldı).
- Zincir, düz doğrusal revizyonların yanı sıra **birleştirme (merge) revizyonları** içerir; örneğin `migrations/versions/20260513_perf_live_gate_merge_sp1a_v58.py` dosyası `v58a1c2d3e4f` revizyonunu (kendisi `f3c8d2a6e501`'in devamıdır) ana zincire geri birleştirir (`CODE_VERIFIED` — dosya içi çapraz referans doğrulandı). Bu, tek-head sonucunun bir kazayla değil kasıtlı birleştirme noktalarıyla elde edildiğini gösterir.
- **Güncel tek head:** `v1a2d3e4f5b6` (`migrations/versions/v1a2d3e4f5b6_add_performance_period_single_active_constraint.py`). Bu oturumda **doğrudan çalıştırılarak** iki kez doğrulandı:
  ```
  FLASK_APP=wsgi.py PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m flask db heads
  → v1a2d3e4f5b6 (head)
  ```
  Komut, boş SQLite üzerinde beklenen bir `user_menu_permissions` guard-exception'ı loglar (bkz. §5) — bu, migration defekti değil, önceden bilinen savunmacı davranıştır (`CODE_VERIFIED`).
- `v1a2d3e4f5b6`'nın `down_revision`'ı **doğrudan `c51c29032d4f`**'dir (`CODE_VERIFIED` — dosya satır 58-59). Bu önemlidir: `docs/handover/DATABASE_MIGRATION.md`, eski SHA `ec4e56bd9bab2ce59e9543fc647f55dffd37d94b`'de doğrulanmış head'in `c51c29032d4f` olduğunu belgeler. Güncel HEAD (`873e6d3`) `v1a2d3e4f5b6`, o revizyonun **doğrudan ve tek bir sonraki adımıdır** — yani zincir **dallanmadan, kopmadan devam etmiştir**; bu bir tutarsızlık değil, beklenen ilerlemedir (`CODE_VERIFIED` çapraz doğrulama).

## 4. Şema koruma (schema guard) — iki farklı mekanizma, birbirine karıştırılmamalı

Kod tabanında **iki ayrı, birbirini tamamlayan** şema koruma mekanizması vardır; bu doküman ikisini net biçimde ayırır (eski bir iç rapor bunları karıştırdığı için `DATABASE_MIGRATION.md` de benzer bir uyarı taşır):

### 4a. Boot-time şema **sözleşme doğrulaması** (salt-okunur, DDL üretmez)

- `app/bootstrap/schema_contract.py` (778 satır) — `EXPECTED_SCHEMA` adlı statik bir `dict[str, set[str]]` içinde, canlı omurgadaki her tablo için beklenen zorunlu kolon adlarını tanımlar (örnek tablolar: `users`, `organization_units`, `performance_periods`, `performance_weight_configs`, `performance_evaluations`, `performance_evaluation_items`, `evaluation_assignments`, ... — `CODE_VERIFIED`, satır 14-120+).
- `app/bootstrap/schema_validation.py:validate_required_schema(app, expected_schema)` (36 satır) — `sqlalchemy.inspect()` ile gerçek veritabanı şemasını okur, eksik tablo/kolonları tek tek listeler, `app.extensions["schema_check_errors"]`'a yazar ve loglar. **Yalnızca `app.config.get("STRICT_SCHEMA_CHECK", False)` açıksa** `RuntimeError("Şema doğrulama başarısız: ...")` fırlatarak açılışı durdurur; kapalıysa yalnızca hata loglar, açılışı engellemez (`CODE_VERIFIED` — satır 35-36).
- Bu doğrulama, her `create_app()` çağrısında **otomatik çalışmaz**; `app/startup_checks.py:should_run_schema_validation_on_boot()` üç durumda atlar: (1) migration komutu algılanırsa (`flask db ...`, `alembic ...` vb. — `is_schema_migration_command()`), (2) `app.config["TESTING"]` açıksa, (3) veritabanı dialect'i `sqlite` ise (`CODE_VERIFIED` — satır 50-65). Yani bu sözleşme doğrulaması **fiilen yalnızca PostgreSQL'e karşı, gerçek (test olmayan) çalışma zamanında** devreye girer.

### 4b. Çalışma zamanı DDL onarım motoru (varsayılan kapalı, isteğe bağlı)

- `app/schema_guard_engine.py:repair_runtime_schema()` — `TABLE_REPAIRS` (`app/schema_guard_core_repairs.py`, çekirdek tablo/index onarımları, `app/schema_guard_core_maintenances.py`'de 621 satırlık bakım/legacy-adoption verisiyle beslenir) ve `SCHEMA_PATCHES` (`app/schema_guard_patches.py`, 99 satır — `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...` biçiminde idempotent delta'lar, örn. `performance_evaluations.workflow_status`, `performance_periods.minimum_presence_days_for_evaluation`) listelerini PostgreSQL'e uygular.
- **Varsayılan kapalıdır.** `should_auto_repair_schema()`: yalnızca `AUTO_REPAIR_SCHEMA=true` ortam değişkeni **açıkça** verildiğinde ve komut satırı bir migration komutu içermediğinde `True` döner (`CODE_VERIFIED` — `app/schema_guard_engine.py:264-269`, `app/startup_checks.py:90-96`). `production`/`staging` `APP_ENV`'de açık bırakılırsa "migration sonrası geçici kullanım dışında önerilmez" uyarısı loglanır (`CODE_VERIFIED`, `app/startup_checks.py:92-93`).
- **SQLite'ta hiçbir DDL uygulamaz** — yalnızca "create_all/migration akışı kullanılacak" diye loglar ve çıkar (`CODE_VERIFIED`, `app/schema_guard_engine.py:151-154`).
- Sahiplik (owner) ve yetki (privilege) farkındalığı vardır: PostgreSQL'de tablo sahibi çalışan rolden farklıysa (`owner_mismatch`) veya `42501`/`insufficient privilege` hatası alınırsa ilgili adım **atlanır**, hata fırlatılmaz — yalnızca loglanır (`CODE_VERIFIED` — satır 160-233). Zaten var olan nesneler için (`42P07`/`42710`/"already exists") sessizce devam eder.
- `app/schema_guard.py` bu iki alt sistemi (`schema_guard_types.py`, `schema_guard_core_repairs.py`, `schema_guard_patches.py`, `schema_guard_engine.py`) tek bir geriye-dönük-uyumlu isim alanında yeniden dışa veren bir orkestratör dosyasıdır (`CODE_VERIFIED`).

### 4c. Neden iki mekanizma birden var

`docs/handover/DATABASE_MIGRATION.md` (eski SHA'da yazılmış ama bu oturumda mantığı doğrulanan bir açıklamayla), `schema_contract.py`'ın beklediği bazı kolonların (`performance_evaluations`, `personnel_leaves`, `attendance_exceptions`, `message_threads` üzerinde toplam 15 kolon) tarihsel olarak yalnızca ham-SQL kendi-kendini-onaran (`schema_guard_patches.py`/`schema_guard_core_maintenances.py`) yoldan var olduğunu, migration zincirinin bunları hiç oluşturmadığını belgeler; bu drift `c51c29032d4f` migration'ıyla kapatılmıştır (`c51c29032d4f`, `v1a2d3e4f5b6`'nın doğrudan atası — bkz. §3). **Bu tarihsel drift kapanmış olsa da, iki mekanizmanın bir arada var olması mimari bir gerçek olarak kalmaya devam ediyor** — gelecekte model değişikliği yapan biri hem migration eklemeli hem de `schema_contract.py`'daki `EXPECTED_SCHEMA`'yı güncellemelidir; ikisi birbirinden bağımsız, elle senkronize edilen dosyalardır (`CODE_VERIFIED` — kod incelemesi; otomatik senkronizasyon mekanizması tespit edilmedi, bu bir defekt iddiası değil, mimari bir gözlemdir).

## 5. "Guarded exception" logları — beklenen davranış, defekt değil

Bu oturumda `flask db heads` boş bir SQLite veritabanına karşı çalıştırıldığında, `user_menu_permissions` tablosu henüz yokken loglanan bir `sqlite3.OperationalError: no such table: user_menu_permissions` hatası gözlemlendi (`CODE_VERIFIED`, bu oturumda yeniden üretildi). `docs/handover/DATABASE_MIGRATION.md` bunun `app.factory`'nin her `create_app()` çağrısında etkili menü-yetki bağlamını kurmaya çalışırken, ilgili tablolar (`user_menu_permissions`, `role_menu_defaults`) henüz yoksa çökmek yerine loglayan, önceden var olan bir savunmacı guard davranışı olduğunu açıklar (`DOCUMENTATION_DERIVED`, ancak bu oturumda gözlemlenen log çıktısıyla tutarlı — `CODE_VERIFIED` düzeyine yükseltildi). Gerçek, en az bir kez migrate edilmiş bir üretim veritabanında bu tablolar mevcuttur ve bu log gürültüsü görünmez.

## 6. Migration idempotency ve legacy/adoption güvenliği

- `SCHEMA_PATCHES` içindeki tüm `ALTER TABLE` ifadeleri `IF NOT EXISTS` biçimindedir — tekrar çalıştırılabilir (`CODE_VERIFIED`, `app/schema_guard_patches.py`).
- File Center 19 tablosu (`app/models/file_center_models.py` içinde `__tablename__` sayımıyla bu oturumda **doğrudan yeniden doğrulandı: 19**, `docs/handover/DATABASE_MIGRATION.md`'deki iddiayla tutarlı — `CODE_VERIFIED`), `migrations/versions/10858a18e9ac_adopt_file_center_schema_into_alembic_.py` migration'ı ile Alembic'e "adopt" edilmiştir (sıfırdan oluşturma değil, önceden var olan tabloları Alembic mülkiyetine alma) (`DOCUMENTATION_DERIVED`, migration dosya adı ve varlığı bu oturumda doğrulandı — içerik satır satır tekrar okunmadı).
- Bu adoption deseni (var olan tabloyu koşullu `CREATE TABLE IF NOT EXISTS` + koşullu `ALTER`/`INDEX` ile "sahiplenme"), `schema_guard_core_repairs.py`/`TABLE_REPAIRS`'te de aynı prensiple tekrarlanır — hem migration hem runtime-repair katmanı, var olan üretim verisini bozmama ilkesini paylaşır (`CODE_VERIFIED`).

## 7. Migration rollback politikası (özet — ayrıntı Belge 06 kapsamında)

`docs/handover/ROLLBACK.md` başlıkları: "PRE-MIGRATION rollback — trivial" / "POST-MIGRATION rollback — requires real verification, not a blanket assumption" / **"Alembic downgrade is never run automatically"** / "DB backups are never deleted by rollback" (`DOCUMENTATION_DERIVED` — başlıklar bu oturumda okundu, ayrıntı yeniden doğrulanmadı; ayrıntılı operasyonel prosedür Belge 06'ya bırakılmıştır). Mimari düzeyde önemli olan tek nokta: **Alembic `downgrade` komutu hiçbir otomasyon tarafından otomatik tetiklenmez**; geri alma, migration sonrası bir yedekten geri yükleme ile ele alınır, ham `downgrade` çalıştırma ile değil.

## 8. Yedekleme öncesi kural (backup-before-migration) — çapraz referans

`c51c29032d4f` gibi veri ekleyen (`ADD COLUMN ... NOT NULL DEFAULT ...`) migration'lar dahil, her canlı migration adımından önce `pg_dump` ile yedek alınması akışın bir parçasıdır (`SCRIPT_VERIFIED` — cutover script akışı, ayrıntı `BACKUP_RUNBOOK.md`/`DISASTER_RECOVERY.md` ile Belge 06 kapsamındadır, burada tekrar edilmemiştir).

## 9. Üretim revizyon durumu

Bu incelemenin kapsamında canlı sunucuya doğrudan erişim yoktur; canlıda fiilen hangi Alembic revizyonunun çalıştığı bu oturumda **doğrulanamadı**. Eski `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:60` satırı, önceki bir kontrol noktasında canlının `e0efcd07abf7` revizyonunda olduğunu ve "migration NOT_REQUIRED" durumunu belirtir — ancak bu, **farklı ve daha eski bir SHA'ya ait tarihsel bir operatör beyanıdır** (`PRODUCTION_HISTORICAL`), güncel HEAD (`873e6d3`, head revizyon `v1a2d3e4f5b6`) ile doğrudan karşılaştırılabilir değildir; iki revizyon arasında zincirsel ilişki bu oturumda doğrulanmadı. **`PRODUCTION_KNOWN_REVISION: NOT_YET_FINALIZED / REQUIRES_FINAL_REFRESH`** — cutover/final teslim öncesi canlı sunucuda `flask db current` çalıştırılarak taze biçimde doğrulanmalıdır.

## 10. Alembic sürümü — netleştirilmemiş nokta

`requirements.txt` Alembic'i **doğrudan** sabitlemez (Flask-Migrate 4.0.7'nin geçişli bağımlılığıdır). `build/wheelhouse/` içinde `alembic-1.19.1-py3-none-any.whl` bulunmaktadır, ancak bu wheelhouse ve eşlik eden `requirements.lock`, kendi başlığında belirttiği üzere **eski SHA `ec4e56bd9bab2ce59e9543fc647f55dffd37d94b`'ye karşı** yeniden üretilmiştir (`CODE_VERIFIED` — `requirements.lock` başlık yorumu). Güncel HEAD (`873e6d3`) için Alembic'in fiilen çözümlenen (resolved) sürümü bu oturumda ayrıca doğrulanmadı — `NOT_YET_FINALIZED`.

---

## Ek — Bu belgede tespit edilen açık teknik bulgular

1. `v1a2d3e4f5b6` (güncel tek head) doğrudan `c51c29032d4f`'nin (eski SHA'da doğrulanmış head) devamıdır — zincir kopmamış, dallanmamış. Bu bir **doğrulama**, bir tutarsızlık değildir.
2. `build/wheelhouse/` + `requirements.lock` ikilisi **eski SHA `ec4e56b`**'ye karşı üretilmiştir; güncel HEAD `873e6d3` için yeniden üretilmemiştir. Puantaj öncesi/final release aşamasında bu ikilinin güncel HEAD'e karşı yeniden üretilip üretilmeyeceği netleştirilmelidir.
3. Üretimde fiilen çalışan Alembic revizyonu bu oturumda doğrulanamadı (`NOT_YET_FINALIZED`); eski handover belgesindeki `e0efcd07abf7` rakamı farklı ve daha eski bir kontrol noktasına aittir, güncel referans olarak kullanılmamalıdır.
4. Boot-time şema sözleşmesi (`schema_contract.py`) ile migration zinciri arasında otomatik bir tutarlılık kontrolü (örn. CI'da "her migration sonrası contract'ı yeniden üret/karşılaştır" adımı) bu incelemede tespit edilmedi; ikisi elle senkronize edilen ayrı dosyalardır — bu bir defekt iddiası değil, gelecekteki model değişiklikleri için dikkat edilmesi gereken bir mimari özelliktir.
