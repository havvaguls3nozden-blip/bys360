Doküman Adı: BYS360 Kurulum, Yapılandırma ve Canlıya Geçiş Kılavuzu
Doküman Türü: Operasyon / Kurulum
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası, yerel HEAD değil)
Son Güncelleme: 2026-09-02

---

## Kanıt sınıflandırma anahtarı

`CODE_VERIFIED` (kod/script doğrudan bu belge yazılırken okundu) · `SCRIPT_VERIFIED` (release/ops script'i satır referansıyla okundu) ·
`DOCUMENTATION_DERIVED` (önceki `docs/handover/` belgesinden alınmış, bu oturumda bağımsız yeniden doğrulanmış) ·
`PRODUCTION_HISTORICAL` (geçmiş olay/operatör beyanına dayalı, bu oturumda doğrudan gözlemlenmedi) · `PLANNED_FUTURE` ·
`NOT_YET_FINALIZED` (bu fazda netleştirilmemiş, gelecekte doğrulanacak bir olgu sorunu) · `REQUIRES_INSTITUTIONAL_DECISION` (bir olgu sorunu değil, kurumun kendisinin yazılı olarak karar vermesi gereken bir politika/tercih boşluğu — ör. yedekleme sıklığı, RPO/RTO hedefi; **taksonomi eklemesi, peer-review/Agent 1 bulgusu**: bu etiket DOC-04/06'da zaten kullanılıyordu, burada resmî olarak tanımlandı).

**Önemli çerçeve notu:** Bu belge iki farklı şeyi birbirinden özenle ayırır:

1. **MEVCUT BİLİNEN ÜRETİM (CURRENT KNOWN PRODUCTION)** — canlı sunucuda bugün fiilen ne çalıştığına dair, çoğunlukla operatör beyanına/eski belgelere dayalı, bu oturumdan doğrudan doğrulanamayan bilgi.
2. **HEDEF RELEASE PROSEDÜRÜ (TARGET RELEASE PROCEDURE)** — bu HEAD'de (`873e6d3`) commit'lenmiş, kodu tamamlanmış candidate/cutover/rollback script'lerinin **tanımladığı**, ancak gerçek üretim sunucusuna karşı bu inceleme sürecinin doğrudan gözlemleyemediği prosedür. Bu script'lerin gerçek üretime karşı fiilen çalıştırılıp çalıştırılmadığı **PRODUCTION_HISTORICAL/NOT_YET_FINALIZED**'dir — bkz. `reports/executive/BYS360_Kurumsal_Rapor_Kaynak.md` §14: mimari "hazırlanıyor/doğrulama aşamasında" olarak nitelendirilmiş, "canlıya alınmış" olarak değil. Bu current-state fazında bu durumun değiştiğine dair bağımsız kanıt yoktur; aksi ispatlanmadıkça aynı sınıflandırma korunur.

---

## 1. Desteklenen işletim sistemi ve çalışma zamanı

- **Hedef üretim ortamı**: Windows Server, canlı sunaklı bilgisayar adı `CATAB-BYS360` (SCRIPT_VERIFIED — `prepare_bys360_candidate.ps1:161` ve `cutover_bys360_candidate.ps1:111`, `$ExpectedHostName` parametresinin varsayılan değeri; her iki script de `Test-HostPrerequisites`/eşdeğeri içinde bu adla **tam eşleşme** ister, aksi halde `PRECHECK_FAILED` ile kapanır).
- Genel kamuya açık ad (public hostname), `cutover_bys360_candidate.ps1:131`'de varsayılan parametre olarak `bys360.canakkaletarihialan.gov.tr` — SCRIPT_VERIFIED, ancak bu değerin bugün gerçekten DNS'te bu şekilde çözüldüğü bu oturumdan doğrulanamaz (LIVE_DOMAIN alanı coordinator olgu defterinde `NOT_YET_FINALIZED` olarak işaretli).
- Operatör oturumunun **yükseltilmiş (Administrator)** olması gerekir; script'ler bunu açıkça kontrol etmez (yalnızca tarihsel V4 script'inin bu kontrolü yaptığı belgelenmiştir — `docs/handover/LIVE_INSTALLATION.md`), ancak `Register-ScheduledTask`/`Stop-ScheduledTask`/`Start-ScheduledTask` gibi çağrılar zaten yükseltilmiş oturum gerektirir; script pratikte yetkisiz bir oturumda ilgili adımda native hata ile durur.

## 2. Python 3.12

- `pyproject.toml`'da `python_version = "3.12"` pin'i mevcuttur (CODE_VERIFIED). `requirements.txt` içinde ayrı bir `python_requires` ifadesi **yoktur** — 3.12 gereksinimi operasyonel bir gerçektir, mevcut venv'in bytecode cache dizinlerinin `cpython-312` etiketini taşımasıyla ve script'lerin kendi kontrolleriyle desteklenir.
- `prepare_bys360_candidate.ps1`'in `Resolve-Bys360BasePython312` fonksiyonu (satır 484-504) **hiçbir zaman** bare `python`/`py` komutunu gerçek iş için çağırmaz: yalnızca `py -3.12 -c "import sys; print(sys.executable)"` ile **mutlak yol** çözer, ardından `--version` çıktısının `Python 3\.12\.` desenine uyduğunu doğrular; uymazsa `PRECHECK_FAILED` ile kapanır (SCRIPT_VERIFIED).
- Bu, `docs/handover/LIVE_INSTALLATION.md`'de anlatılan gerçek üretim arızasının (bare `python` PATH'te değildi) doğrudan yapısal düzeltmesidir — SCRIPT_VERIFIED olarak doğrulandı, önceki belgenin "yeni script bunu koruyacak" öngörüsü doğru çıkmıştır.

## 3. PostgreSQL 15

- `prepare_bys360_candidate.ps1` ve `cutover_bys360_candidate.ps1`, `$PgBinPath` parametresinin varsayılan değeri olarak `C:\Program Files\PostgreSQL\15\bin` kullanır (SCRIPT_VERIFIED — sırasıyla satır 172 ve 124) ve `Test-HostPrerequisites` bu yolda `pg_dump.exe`, `pg_restore.exe`, `psql.exe` dosyalarının varlığını doğrular (`prepare_bys360_candidate.ps1:519-528`).
- **Doğrulanmış fark (eski belgeyle çelişki):** `docs/handover/LIVE_INSTALLATION.md`, "tarihsel script'in `postgresql-x64-15` adlı bir Windows servisini kontrol ettiğini, yeni script'lerin de bunu koruyacağının beklendiğini" belirtir. Bu current-state incelemesinde `prepare_bys360_candidate.ps1` ve `cutover_bys360_candidate.ps1` içinde `Get-Service`/`postgresql-x64-15` deseni **aranmış ve bulunamamıştır** (SCRIPT_VERIFIED — negatif grep sonucu). Yeni script'ler yalnızca istemci ikili dosyalarının (`pg_dump.exe` vb.) varlığını kontrol eder; PostgreSQL Windows servisinin fiilen çalışır durumda olduğunu **ayrıca doğrulamaz** — bu, bir bağlantı denemesinde (`Test-PostgresAdminAuth`, `Get-ProductionDbConnection`) dolaylı olarak ortaya çıkar, ama adı geçen servis kontrolü artık scriptte yoktur. Bu, eski belge setiyle **gerçek script içeriği arasındaki somut bir sapmadır** ve sessizce tekrar edilmemiştir.
- İki ayrı PostgreSQL rolü ayrımı script'te doğrulandı: uygulama rolü (`DATABASE_URL`'den ayrıştırılır, `CREATEDB` verilmez) ve admin rolü (`$PostgresAdminUser`, varsayılan `postgres`; parola **hiçbir zaman** parametre olarak alınmaz, yalnızca `Read-Host -AsSecureString` ile, sadece shadow-rehearsal fazı başladığında, interaktif olarak istenir — `prepare_bys360_candidate.ps1:1775`).

## 4. Redis / arka plan iş kuyruğu

`requirements.txt` içinde `redis==5.0.8`, `rq==2.3.3` pinleri mevcuttur (CODE_VERIFIED). **Güncelleme (peer-review, Agent 1 bulgusu — bu soru artık kapalıdır):** Redis mimari olarak **isteğe bağlıdır** — `REDIS_URL`/`CACHE_REDIS_URL` tanımlı değilse sistem dosya/JSON veya bellek-içi yedek moda düşer, açılışı engellemez. Bkz. DOC-02 §6 (CODE_VERIFIED, 5 dosyada doğrudan doğrulanmıştır: `app/core/healthcheck.py`, `async_job_queue.py`, `shared_cache_store.py`, `runtime_cache.py`, `app/security/rate_limit_store.py`). Kurulum sırasında Redis'in mevcut olmaması, açılışı engellemez ancak yedek moda düşürür.

## 5. Ortam değişkenleri ve secret yönetimi

- `.env` dosyası **hiçbir zaman** release paketinin içinde yer almaz; yalnızca `.env.example` / `.env.docker.example` şablonları (değerleri boş) paketlenebilir — `scripts/release/build_bys360_safe_release.py`'nin `ALLOWED_ENV_TEMPLATE_BASENAMES = {".env.example", ".env.docker.example"}` allowlist'i (CODE_VERIFIED, satır 81). Bu repoda şu an bir `.env.production.example` **yoktur**.
- `SECRET_KEY` doğrulaması `config.py` içinde (yaklaşık satır 524-541, `docs/handover/SECRETS_AND_PERSISTENCE.md`'de belgelenmiş) boş olmama, bilinen placeholder olmama (`CHANGE_ME`, `changeme`, `bys360-dev-session-key-change-me-before-production` vb.) ve en az 32 karakter şartlarını `APP_ENV` `production`/`staging` olduğunda sert `RuntimeError` ile zorunlu kılar; bu doğrulama hiçbir aşamada gevşetilmez.
- Üretim `.env` değerleri hiçbir aşamada diske düz metin olarak kopyalanmaz: candidate hazırlığı sırasında `Get-Bys360ProductionEnvValues` (`prepare_bys360_candidate.ps1:1015`) gerçek `python-dotenv` kütüphanesiyle okunur ve yalnızca alt süreç ortam değişkeni olarak, `Invoke-WithBys360RuntimeEnvironment` (satır 1053) ile enjekte edilip iş bitince tam olarak eski haline döndürülür.

## 6. Bağımlılık kurulumu — çevrimdışı wheelhouse modeli

Coordinator olgu defterinde bu alan "Agent 2 tarafından teyit edilecek" olarak işaretliydi. Bu incelemede **doğrudan bu worktree'de** kontrol edildi:

- `requirements.lock` — **MEVCUT** (kök dizinde, `ls requirements.lock` ile doğrulandı, CODE_VERIFIED).
- `build/wheelhouse/` — **MEVCUT**, içinde gerçek `.whl` dosyaları var (örnek: `Flask_Limiter-3.5.0-py3-none-any.whl`, `SQLAlchemy-2.0.36-cp312-cp312-win_amd64.whl`, CODE_VERIFIED).
- Bu, `docs/handover/LIVE_INSTALLATION.md` / `CANDIDATE_PREPARATION.md`'nin yazıldığı zamanki durumdan (o belgeler bu artefaktların "henüz bu worktree'de mevcut olmadığını, kardeş bir iş akışına ait olduğunu" belirtiyordu) **farklıdır — artık mevcutlar**. Bu, olumlu yönde bir güncelleme olarak coordinator olgu defterine işlenmelidir.
- `scripts/release/build_bys360_wheelhouse.py` de kök `scripts/release/` altında mevcuttur (CODE_VERIFIED).
- Kurulum komutu (`prepare_bys360_candidate.ps1:868`, `New-CandidateVirtualEnv` fonksiyonu, "REAL production path" olarak açıkça yorumlanmış):
  ```
  pip install --no-index --find-links wheelhouse -r requirements.lock
  ```
  `--no-index` hiçbir index'e (PyPI dahil) bağlanmaz. Script, `requirements.lock` + `wheelhouse\` **ikisi de yoksa** varsayılan olarak `VENV_FAILED` ile kapanır; `-AllowNetworkInstallFallback` anahtarı yalnızca script'in kendi geliştirme/test aşaması için var olup **üretimde asla kullanılmamalıdır** (script başlığında açıkça uyarılmıştır).
- Wheelhouse bütünlüğü, `Get-WheelhouseIdentitySha256` (satır 409-456) ile gerçek `.whl` dosyalarından **bağımsızca yeniden hesaplanır** (ordinal sıralama; kültüre bağlı sıralamanın Türkçe sistem locale'inde farklı sonuç verdiği doğrudan tespit edilip düzeltilmiştir — script yorumu, satır 418-427).

## 7. Statik dosyalar / şablonlar

`app/`, `migrations/`, `requirements.txt`, `wsgi.py`, `run_server.py`, `config.py`, `DEPLOYMENT.md` — release paketinin **zorunlu** içeriğidir (`build_bys360_safe_release.py`'nin `REQUIRED_PACKAGE_PATH_PREFIXES`, CODE_VERIFIED, satır 109). Şablonlar ve statik varlıklar `app/` altında paketle birlikte gelir; ayrıca bir "statik dosya derleme" adımı bu script'lerde tanımlı değildir.

## 8. Veritabanı migration prosedürü

Ayrıntılı prosedür `06_...Yedekleme...` ve `14_...Release_Candidate_Cutover...` belgelerinde tekrarlanmayacak şekilde `docs/handover/DATABASE_MIGRATION.md`'ye dayanır; özet:

- Migration zinciri **tek head**'e sahiptir; bu oturumda coordinator tarafından doğrudan çalıştırılmış (`flask db heads` → `v1a2d3e4f5b6 (head)`, boş SQLite üzerinde) — CODE_VERIFIED, coordinator olgu defterinde kayıtlı.
- `migrations/versions` altında 77 `.py` dosyası mevcuttur (CODE_VERIFIED).
- Aday hazırlığı sırasında migration, gerçek üretim verisinin bir kopyasının restore edildiği **tek kullanımlık shadow veritabanı** üzerinde, uygulamanın gerçek rolüyle, gerçek `.env` değerleriyle prova edilir (`Invoke-ShadowMigrationAsAppUser`, `prepare_bys360_candidate.ps1`). Canlı migration (cutover Faz 12/20) **aynı kod yolunu** gerçek veritabanına karşı çalıştırır (`flask db upgrade`, `cutover_bys360_candidate.ps1:1015-1041`, SCRIPT_VERIFIED).
- Migration öncesi/sonrası şema-sözleşme kontrolü (`app.bootstrap.schema_contract.get_expected_schema()` / `validate_required_schema()`) hem shadow'da (`Test-ShadowSchemaContract`, prepare script) hem canlıda (`Test-LiveSchemaContract`, `cutover_bys360_candidate.ps1:950-1014`) **gerçek uygulama fonksiyonları** çağrılarak yapılır, yeniden implementasyon değildir.

## 9. Windows Scheduled Task / çalışma zamanı kurulumu

- Canlı görev adı: **`BYS360 Live Waitress 80`** (SCRIPT_VERIFIED, `scripts/windows/install_bys360_live_waitress_80_task_v1.ps1:40`, varsayılan `-TaskName` parametresi).
- Bu installer script **plan/apply** modelindedir: `-Apply` verilmeden **hiçbir** `Register-ScheduledTask`/`Set-ScheduledTask`/`Start-ScheduledTask`/`Stop-ScheduledTask` çağrısı yapılmaz (satır 101-152); mevcut aynı isimli görev varsa `-ConfirmReplace` verilmeden sessizce üzerine yazılmaz (çarpışma koruması, satır 104-114).
- Task; `Register-ScheduledTaskAction -Execute "powershell.exe"` ile, `$env:APP_PORT` atayan bir PowerShell katmanı üzerinden `.venv\Scripts\python.exe run_server.py`'yi çalıştırır; `AtStartup` tetikleyicisi ve `SYSTEM` / `ServiceAccount` / `RunLevel Highest` principal ile kurulur (satır 124-141, CODE_VERIFIED). `PYTHONUTF8`/`PYTHONIOENCODING` açıkça `utf-8` ayarlanır — Türkçe başlangıç mesajlarının Scheduled-Task-redirected konsolun varsayılan ANSI codepage'inde encode edilemediği, canlı sunucuda gerçekten yaşanmış bir arızanın (kök neden olarak doğrulanmış) doğrudan düzeltmesidir (satır 69-79 yorumu).
- **Bilinen sertleştirme açığı (bkz. Belge 13):** bu installer, `New-ScheduledTaskSettingsSet` çağrısında (satır 126) yalnızca `-AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable` belirtir; `ExecutionTimeLimit`, `RestartCount`, `RestartInterval` parametreleri **açıkça geçirilmez**. Bu, PowerShell'in varsayılan `PT72H` (72 saat) execution time limit'inin ve varsayılan "otomatik yeniden başlatma yok" davranışının **hiç değiştirilmediği** anlamına gelir — bu belge setinde bu, "zaten düzeltilmiş" olarak değil, **açık/bekleyen operasyonel sertleştirme maddesi** olarak işaretlenir (bkz. Belge 13, §PT72H).

## 10. Sağlık doğrulama uç noktaları

Doğrudan kaynak kodundan doğrulandı (CODE_VERIFIED, `app/routes.py`):

| Uç nokta | Satır | Davranış |
|---|---|---|
| `GET /healthz` | 72-74 | `{"status":"ok","service":"bys360"}`, her zaman 200, login gerektirmez |
| `GET /readyz` | 77-86 | Şema kontrolü hatasızsa `status=ready` + 200; hata varsa `status=degraded` + 503 |
| `GET /versionz` | 176-202 | `service`, `app_env`, `route_count`, `schema_error_count` her zaman döner; `source_sha`/`migration_head` **yalnızca loopback (127.0.0.1/::1) bağlantılarına** açıklanır (`_bys360_request_is_from_loopback`, satır 156-173 — ham soket peer adresine bakar, `X-Forwarded-For` sahtekarlığına karşı korumalıdır) |

`versionz`'in `source_sha`/`migration_head` alanları, çalışan sürecin kendi `CANDIDATE_READY.json`'ını (`C:\bys360\project\..\CANDIDATE_READY.json`, yani candidate kökünde) okuyarak doldurulur (`_bys360_release_identity`, satır 130-150) — dev/local ortamlarda dosya yoksa sessizce `None` döner, hata fırlatmaz.

## 11. Aday hazırlama (candidate preparation) — özet

Tam prosedür Belge 14'te. Bu belgede yalnızca kurulum akışındaki yeri özetlenir: `prepare_bys360_candidate.ps1`, 16 fazlı, tamamen izole bir süreçtir; canlı Scheduled Task'a, `C:\bys360\project`'e, canlı veritabanına **asla dokunmaz** (script başlığı, satır 27-45, yapısal olarak zorlanmış kısıtlar). Başarı çıktısı `CANDIDATE_READY.json`'dır.

## 12. Checksum doğrulama

`scripts/release/build_bys360_safe_release.py --verify <zip> --expected-source-sha <sha>` komutu (`docs/handover/RELEASE_VERIFICATION.md`'de tam anlatılmış, bu belgede tekrarlanmaz) paketin SHA256'sını, manifest'i ve sha256sums.txt'yi çapraz doğrular. Ayrıca `RELEASE_SOURCE_SHA.txt` paketin **içine gömülü** olduğundan (script başlığı "EMBEDDED SOURCE SHA", satır 132-149) bu dosya ZIP'in bütün-paket hash kapısının kapsamındadır — sidecar `manifest.json` tek başına artık güvenilir kabul edilmez, gömülü değer otoritedir (`Test-EmbeddedSourceSha`, satır 747-777).

## 13. Cutover ve rollback — özet

Ayrıntı Belge 14'te. Cutover 20 fazlıdır (`cutover_bys360_candidate.ps1`, SCRIPT_VERIFIED faz başlıkları): geçerli `CANDIDATE_READY.json` olmadan **hiçbir** canlı adım çalışmaz (Faz 1/20, "hard gate"). Rollback (`rollback_bys360_candidate.ps1`) hiçbir zaman otomatik Alembic downgrade çalıştırmaz; migration-öncesi durum "trivial", migration-sonrası durum operatörün açık `-PostMigrationAppTreeCompatible` onayını gerektirir.

## 14. Rollback tetikleme kriterleri

- Cutover'ın herhangi bir fazı `Invoke-FailClosed` ile başarısız olursa (`FAILURE_RECEIPT.txt` yazılır, Faz adı ve neden içerir) — hangi rollback yolunun (migration-öncesi/sonrası) geçerli olduğu, başarısız olan fazın canlı migration'dan (Faz 12/20) önce mi sonra mı olduğuna göre belirlenir (bkz. Belge 06 ve Belge 15).
- Cutover başarıyla tamamlanmış ama sonradan (smoke, health, güvenlik günlük taraması) bir sorun operatör tarafından tespit edilirse: rollback yalnızca `-PostMigrationAppTreeCompatible` açık onayıyla, kaynak diff'i (`git diff <previous>..<candidate> --stat`) gerçekten okunarak yapılır — asla varsayım olarak değil.

## 15. Post-cutover kontroller

`cutover_bys360_candidate.ps1` Faz 16-19/20 (SCRIPT_VERIFIED, satır numaraları önceki bölümlerde listelendi): yerel `/healthz` 200, `/versionz` üzerinden release-identity binding (`Test-ReleaseIdentityBinding`), `/readyz` readiness gate (`Test-ReadinessGate`), genel (public) health kontrolü (`-SkipPublicHealthCheck` ile açıkça atlanabilir, sessiz atlama yoktur), salt-okunur smoke kontrolleri (`file_center`/`portal` blueprint kaydı, guest/chunk endpoint'leri) ve gerçek ERROR/CRITICAL desenlerine göre günlük taraması (`Test-LogForRealErrors`, bare substring match değil).

## 16. Özet: MEVCUT BİLİNEN ÜRETİM vs. HEDEF PROSEDÜR

| Konu | MEVCUT BİLİNEN ÜRETİM | HEDEF (bu HEAD'deki script'ler) |
|---|---|---|
| Görev adı | `BYS360 Live Waitress 80` (PRODUCTION_HISTORICAL + SCRIPT_VERIFIED isim eşleşmesi) | Aynı |
| Canlıya geçiş yöntemi | Bilinmiyor/operatör beyanına dayalı — tarihsel tekil script (`deploy_bys360_ec4e56b_production_v4.ps1`) en azından bir kez gerçek üretime karşı denenmiş ve VENV fazında başarısız olmuş (script'in kendi başlığı, PRODUCTION_HISTORICAL) | 3 parçalı candidate/cutover/rollback modeli — kodu tamamlanmış, izole test ortamında uçtan uca denenmiş (`Kurumsal_Rapor_Kaynak.md` §14), **gerçek üretime karşı bu HEAD'de hiç çalıştırıldığına dair bu oturumdan doğrulanabilir kanıt yok** |
| PostgreSQL servis kontrolü | Tarihsel script `postgresql-x64-15` servis adını kontrol ediyordu (DOCUMENTATION_DERIVED) | Yeni script'ler bu kontrolü **yapmıyor** (SCRIPT_VERIFIED, negatif) |
| Bağımlılık kurulumu | Bilinmiyor (muhtemelen mevcut venv'e `pip install -r requirements.txt`) | Çevrimdışı `requirements.lock` + `wheelhouse\` (artık bu worktree'de mevcut) |

**Sonuç:** Bu belge, kurulumu iki katmanlı okumalıdır — bir sistem yöneticisi sıfırdan bir host kurarken önce Bölüm 1-7'yi (host önkoşulları) tamamlar, ardından gerçek bir canlı geçiş için Belge 14'teki candidate/cutover akışını **kurumun kendi onayıyla, ilk kez gerçek üretime karşı dikkatle** uygular — bu ilk gerçek çalıştırma, mevcut current-state fazının kapsamında değildir.
