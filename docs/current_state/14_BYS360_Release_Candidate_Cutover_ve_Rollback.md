Doküman Adı: BYS360 Release, Candidate, Cutover ve Rollback Modeli
Doküman Türü: Operasyon / Release Mühendisliği
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası, yerel HEAD değil)
Son Güncelleme: 2026-09-02

---

Bu belge, `docs/handover/CANDIDATE_PREPARATION.md`, `CUTOVER.md`, `ROLLBACK.md`, `RELEASE_VERIFICATION.md`'nin doğrudan halefidir ve o belgelerin defalarca tekrarladığı "bu, script'in kendisi değil, script'in yazıldığı spesifikasyondan üretildi — gerçek entegre script'e karşı doğrulayın" uyarısını **bu current-state fazında bizzat yerine getirir**: aşağıdaki her adım, bu HEAD'deki (`873e6d3`) gerçek `prepare_bys360_candidate.ps1`, `cutover_bys360_candidate.ps1`, `rollback_bys360_candidate.ps1` ve `scripts/release/build_bys360_safe_release.py` dosyaları doğrudan okunarak yazılmıştır. Kanıt sınıflandırma anahtarı Belge 03 ile aynıdır.

**Genel durum:** Bu üç script artık bu HEAD'de **commit'lenmiş ve entegre** durumdadır (eski belge setinin "henüz görülemedi" notu artık geçerli değildir — bu doğrudan bir güncelleme/düzeltmedir). Ancak `reports/executive/BYS360_Kurumsal_Rapor_Kaynak.md` §14'ün belirttiği gibi bu mimari "izole bir test ortamında uçtan uca denenmiş" ama **gerçek üretim sunucusuna karşı hiç çalıştırılmamış** olarak nitelenmektedir; bu current-state incelemesi bu durumun değiştiğine dair bağımsız kanıt bulamamıştır — dolayısıyla PRODUCTION_HISTORICAL/NOT_YET_FINALIZED sınıflandırması korunur.

---

## 1. Kaynak SHA bağlama — release paketinden çalışan sürece kadar

Bu deployment modelinin merkezi güvenlik özelliği, "hangi git commit'i şu an çalışıyor" sorusunun **her katmanda bağımsızca doğrulanabilir** olmasıdır:

1. `scripts/release/build_bys360_safe_release.py`, paketi `git ls-files`'tan üretir ve `RELEASE_SOURCE_SHA.txt`'yi ZIP'in **içine**, kendi per-dosya SHA256SUMS hesaplanmadan **önce** gömer (CODE_VERIFIED, `EMBEDDED_SOURCE_SHA_FILENAME = "RELEASE_SOURCE_SHA.txt"`, satır 117) — bu, o dosyanın baytlarının bütün-ZIP hash kapısının kapsamında olduğu anlamına gelir.
2. Sidecar `manifest.json` (ZIP'in **yanında** duran, ZIP'e kriptografik olarak bağlı olmayan ayrı bir dosya) da `source_sha` alanını taşır, ama bu artık **tek başına güvenilmez** — bu, "BYS360 DEFECT AH" (2026-09-02) olarak adlandırılan gerçek bir güvenlik açığının kapatılmasıdır: bir saldırgan veya dürüst bir hata (örn. eski bir `manifest.json`'ın yeni bir ZIP'in yanına yanlışlıkla kopyalanması), önceden bu tek alanı fark edilmeden değiştirebilirdi.
3. `prepare_bys360_candidate.ps1`'in `Test-EmbeddedSourceSha` fonksiyonu (Faz 4b/16, satır 747-777, SCRIPT_VERIFIED), extracted candidate ağacındaki gömülü `RELEASE_SOURCE_SHA.txt`'yi okur, 40 hex karakterlik geçerli bir git SHA olduğunu doğrular, Faz 3'te sidecar manifest'ten okunan değerle **eşleştiğini** ister — uyuşmazlıkta `SOURCE_SHA_FAILED`. Eşleşirse, bu noktadan itibaren **gömülü değer otoritedir**: `$Script:Receipt.SOURCE_SHA` bu değerle üzerine yazılır.
4. Bu otoriter `SOURCE_SHA`, `CANDIDATE_READY.json`'a yazılır (Bölüm 3), cutover'ın `Assert-ValidCandidateReceipt`'i tarafından yeniden çapraz kontrol edilir, ve nihayetinde `/versionz`'in (yalnızca loopback'e) döndürdüğü `source_sha` alanına kadar uzanır (`app/routes.py:130-150`, CODE_VERIFIED) — cutover'ın kendi `Test-ReleaseIdentityBinding`'i (Faz 16a/20) bu zincirin son halkasıdır.

## 2. Release arşivi ve hash manifesti

`scripts/release/build_bys360_safe_release.py`'nin ürettiği üç dosya (`docs/handover/RELEASE_VERIFICATION.md` §1'de tam belgelenmiş, bu belgede tekrarlanmaz):

- `BYS360_FULL_LIVE_<SHA>.zip`
- `BYS360_FULL_LIVE_<SHA>.manifest.json` (schema_version `2` klasik build, `3` FULL/wheelhouse-dahil build — CODE_VERIFIED, satır 523: `"schema_version": SCHEMA_VERSION if full_build is None else SCHEMA_VERSION_FULL`)
- `BYS360_FULL_LIVE_<SHA>.sha256sums.txt`

Doğrulama: `python scripts/release/build_bys360_safe_release.py --verify <zip> --expected-source-sha <sha>` — her dosyayı yeniden hash'ler, manifest'in `files[]` listesiyle çapraz kontrol eder, yasaklı yol/isim desenlerinin (`FORBIDDEN_DIR_PARTS`, `FORBIDDEN_SUFFIXES`, `FORBIDDEN_NAME_PATTERNS`, `FORBIDDEN_EXACT_NAMES` — CODE_VERIFIED, satır 41-107) paket içinde **hiç** olmadığını doğrular.

### schema_version=3 FULL paket (wheelhouse-dahil)

`--wheelhouse-dir` bayrağıyla tetiklenir (CODE_VERIFIED, satır 31-33, 708-710). Bu modda manifest **ek olarak** şu alanları taşır (hepsi `prepare_bys360_candidate.ps1`'in `Test-PackageManifest`'i tarafından zorunlu kılınır, satır 628-653, SCRIPT_VERIFIED):

```
requirements_lock_sha256, wheelhouse_identity_sha256, wheelhouse_file_count,
wheelhouse_total_bytes, migration_head, candidate_script_sha256,
cutover_script_sha256, rollback_script_sha256, secret_scanner_sha256,
secret_scan_status, secret_scan_findings
```

`secret_scan_status != "PASS"` veya `secret_scan_findings != 0` ise candidate hazırlığı **daha ekstraksiyonun içeriğine bakmadan** reddedilir (satır 639-641). Extraction sonrası, `prepare_bys360_candidate.ps1` bu iddiaları **körü körüne güvenmez** — Faz 4a/16 (satır 707-723), `candidate_script_sha256`/`cutover_script_sha256`/`rollback_script_sha256`/`secret_scanner_sha256`'yı extracted candidate ağacındaki **gerçek** dosyalardan yeniden hesaplar ve manifest iddiasıyla karşılaştırır; Faz 5a/16 (satır 877-885) `wheelhouse_identity_sha256`'yı gerçek `.whl` dosyalarından bağımsızca yeniden hesaplar; Faz 9/16 (`Test-CandidateMigrationHead`) `migration_head` iddiasını candidate'ın kendi `migrations/` ağacından yeniden çözer. Bu "her zaman taze hesapla, asla körü körüne güvenme" deseni, cutover'ın `CANDIDATE_READY.json`'a karşı yaptığı aynı disiplinin bir katman öncesinde uygulanmasıdır (script başlığı, satır 383-405).

## 3. `CANDIDATE_READY.json` — gerçek şema (bu HEAD'de doğrudan doğrulandı)

`prepare_bys360_candidate.ps1`'in `$Script:Receipt` ordered hashtable'ı (satır 199-222, CODE_VERIFIED) ve `Write-CandidateReadyReceipt` (Faz 14/16, satır 1830-1847) tarafından yazılan **gerçek alan listesi**:

```json
{
  "SCHEMA_VERSION": 1,
  "RECEIPT_KIND": "CANDIDATE_READY",
  "GENERATED_AT": "",
  "SOURCE_SHA": "",
  "PACKAGE_PATH": "",
  "PACKAGE_SHA256": "",
  "CANDIDATE_DIR": "",
  "DEPENDENCY_LOCK_MODE": "OFFLINE_WHEELHOUSE | NETWORK_FALLBACK_TEST_ONLY",
  "DEPENDENCY_LOCK_FILE": "",
  "DEPENDENCY_LOCK_SHA256": "",
  "WHEELHOUSE_IDENTITY_SHA256": "",
  "PIP_CHECK": "",
  "IMPORT_GATES": "",
  "APP_FACTORY_CHECK": "",
  "MIGRATION_HEAD": "",
  "DB_BACKUP_PATH": "",
  "SHADOW_REHEARSAL_RESULT": "",
  "SCHEMA_CONTRACT_CHECK": "",
  "FILE_CENTER_TABLES": "",
  "HEALTH_BOOT_PORT": "",
  "HEALTH_CHECK_RESULT": "",
  "CANDIDATE_READY": "YES | NO"
}
```

Bu dosya iki kopya halinde yazılır: `C:\bys360\candidate\<SOURCE_SHA>\CANDIDATE_READY.json` (cutover'ın okuyacağı yer) ve `C:\bys360\deploy_logs\candidate_prep_<DeployId>\CANDIDATE_READY.json` (arşiv kopyası). `CANDIDATE_READY` alanı yalnızca **tüm** 14 fazın sonunda `"YES"` olarak set edilir; herhangi bir fazın erken başarısızlığı bu dosyayı **hiç yazdırmaz** (script `Invoke-FailClosed` ile `throw` eder, `Main` fonksiyonu bu noktaya asla ulaşmaz).

**Eski belgeyle uyum notu:** `docs/handover/CANDIDATE_PREPARATION.md`'nin listelediği kavramsal alanlar (Source SHA, Package SHA256, Candidate directory, Dependency-lock hash, Migration head) gerçek şemada birebir karşılık bulur (`SOURCE_SHA`, `PACKAGE_SHA256`, `CANDIDATE_DIR`, `DEPENDENCY_LOCK_SHA256`, `MIGRATION_HEAD`) — kavramsal tanım doğru çıkmıştır, yalnızca tam alan adları ve ek alanlar (`WHEELHOUSE_IDENTITY_SHA256`, `SCHEMA_CONTRACT_CHECK`, `FILE_CENTER_TABLES`, `HEALTH_BOOT_PORT` vb.) bu belgede ilk kez tam olarak listelenmektedir.

## 4. Aday hazırlama (candidate preparation) — 16 fazlı akış

`prepare_bys360_candidate.ps1`'in gerçek faz sırası (SCRIPT_VERIFIED, fonksiyon isimleri ve "Phase N/16" log satırları doğrudan grep edildi):

| # | Faz | Fonksiyon |
|---|---|---|
| 1 | PRECHECK — host önkoşulları | `Test-HostPrerequisites` |
| 2 | PACKAGE — hash kapısı | `Test-PackageHash` |
| 3 | MANIFEST — sidecar doğrulama | `Test-PackageManifest` |
| 4 | EXTRACT | `Expand-CandidatePackage` |
| 4b | Gömülü kaynak SHA doğrulama | `Test-EmbeddedSourceSha` |
| 4c | Extracted-candidate secret re-scan | `Test-CandidateExtractedSecretScan` |
| 5 | Candidate venv inşası (çevrimdışı) | `New-CandidateVirtualEnv` |
| 6 | pip check | `Test-CandidatePipCheck` |
| 7 | Import gates | `Test-CandidateImportGates` |
| 8 | `create_app()` + config doğrulama | `Test-CandidateAppFactory` |
| 9 | Migration head doğrulama | `Test-CandidateMigrationHead` |
| 10 | PostgreSQL yedeği (rehearsal kaynağı) | `Backup-SourceDatabase` |
| 11 | Shadow DB admin auth + create/restore/migrate | `Test-PostgresAdminAuth`, `New-ShadowDatabaseAsAdmin`, `Restore-ShadowDatabaseAsAppUser`, `Invoke-ShadowMigrationAsAppUser` |
| 12-13 | Şema-sözleşme kontrolü + sağlık boot | `Test-ShadowSchemaContract`, `Invoke-ShadowRehearsalAndHealthBoot` |
| 14 | `CANDIDATE_READY.json` yazımı | `Write-CandidateReadyReceipt` |

Bu, canlı servise, canlı ağaca veya canlı veritabanına **yapısal olarak** dokunmayan bir akıştır (script başlığı, satır 27-45'te 6 madde halinde sabit kısıtlar olarak listelenmiştir): asla `Stop/Start-ScheduledTask` çağırmaz, asla `C:\bys360\project`'e yazmaz, migration'ı yalnızca kendi oluşturup silediği tek-kullanımlık shadow veritabanına karşı çalıştırır, port 80'i asla bağlamaz (`Resolve-CandidateHealthPort`, varsayılan `18080`, çakışma durumunda `18081..18090` yedekleri), `storage`/`local_storage`'a yazmaz, üretim `.env`'ini asla düz metin olarak diske kopyalamaz.

## 5. Cutover doğrulama — 20 fazlı akış ve sert kapı

`cutover_bys360_candidate.ps1`'in gerçek faz sırası (SCRIPT_VERIFIED):

| # | Faz | Not |
|---|---|---|
| 1 | `CANDIDATE_READY.json` doğrulama (**sert kapı**) | `Assert-ValidCandidateReceipt` — receipt'in disk üzerindeki gerçek candidate ağacına bağlanan alanları **yeniden hesaplanır**, körü körüne güvenilmez |
| 2 | PRECHECK — host önkoşulları | |
| 3 | Mevcut canlı kimlik (bilgi amaçlı) | `Get-CurrentLiveIdentity` |
| 4 | Mevcut DB revizyonu (salt okunur) | `Get-CurrentDbRevision` |
| 5 | Son cutover-öncesi DB yedeği | `Backup-LiveDatabase` |
| 6 | `.env`/`instance\` koruma | `Protect-PersistentState` |
| 7-8 | Canlı görevi durdur + port kapandı mı doğrula | `Stop-LiveService` |
| 9 | Ağaç taşıma: mevcut → `previous\`, candidate → `project\` | `Move-ApplicationTreeIntoPlace` (iki-adımlı taşımanın atomik olmama riskine karşı best-effort geri-alma içerir — script başlığı satır 36-48) |
| 10 | `.env`/`instance\` geri yükleme | `Restore-PersistentState` |
| 11 | Tanıtılan ağacın kimliğini yeniden doğrulama | `Test-PromotedTreeIdentity` |
| 12 | **CANLI** veritabanı migration'ı | `Invoke-LiveMigration` — aynı kod yolu (`flask db upgrade`, `FLASK_APP=wsgi.py`, `APP_ENV=production`), shadow rehearsal'ın zaten kanıtladığı invocation şekliyle, gerçek veritabanına karşı |
| 13/13a | Revizyon + File Center 19/19 + şema-sözleşme doğrulama | `Test-LiveSchemaContract` |
| 15 | Canlı görevi başlat | `Start-LiveService` |
| 16 | Yerel `/healthz` | `Test-LocalHealth` |
| 16a | Sürüm kimliği bağlama | `Invoke-ReleaseIdentityCheck` (üst faz-fonksiyonu, `GET /versionz`; içeride `Test-ReleaseIdentityBinding`'i çağırır — DOC-13 §6 bu iç yardımcı fonksiyonu adlandırır, ikisi çelişmez) |
| 16b | Hazır olma kapısı | `Invoke-ReadinessCheck` (üst faz-fonksiyonu, `GET /readyz`; içeride `Test-ReadinessGate`'i çağırır — DOC-13 §6 bu iç yardımcı fonksiyonu adlandırır, ikisi çelişmez) |
| 17 | Genel (public) `/healthz` | `Test-PublicHealth` (`-SkipPublicHealthCheck` ile yalnızca açık, kayıtlı bir atlama) |
| 18 | Salt-okunur smoke kontrolleri | `Test-SmokeChecks` |
| 19 | Güvenlik/log taraması | `Test-PostDeploySecurity` |
| 20 | `DEPLOYMENT_RECEIPT.txt` | `Write-SuccessReceipt` |

**Sert kapı ayrıntısı:** `Assert-ValidCandidateReceipt` (Faz 1/20, satır 502-638) yalnızca dosyanın var olduğunu kontrol etmez — `SOURCE_SHA`, `PACKAGE_SHA256`, `DEPENDENCY_LOCK_SHA256`, `MIGRATION_HEAD` gibi alanların disk üzerindeki gerçek candidate ağacıyla **hâlâ** tutarlı olduğunu yeniden hesaplayarak doğrular. Bunu atlayan bir bayrak **yoktur** — bu, tasarımın en katı, istisnasız kuralıdır.

## 6. PID/süreç doğrulama ve versionz/readyz kapıları

Bkz. Belge 13 §6 (DEFECT Z, tam ayrıntı) — bu belgede yalnızca özetlenir: `Test-ProcessBinding` (PID→yol→komut satırı→başlangıç zamanı), `Test-ReleaseIdentityBinding` (`/versionz` loopback), `Test-ReadinessGate` (`/readyz`).

## 7. Rollback

Bkz. Belge 06 §8-9 (tam ayrıntı, bu belgede tekrarlanmaz). Özet: `rollback_bys360_candidate.ps1`, `-PreviousDir` ve `-ActiveDeploymentReceiptPath`'i **açıkça** ister (auto-discovery yok), migration-öncesi/sonrası ayrımını yapısal olarak (`Test-AppTreeDbCompatibilityGate`) uygular, Alembic downgrade'i **hiçbir koşulda** çalıştırmaz.

## 8. Fail-closed felsefesi

Üç script de aynı iskeleti paylaşır (CODE_VERIFIED, her üçünde ayrı ayrı doğrulandı): `Set-StrictMode -Version Latest`, `$ErrorActionPreference = 'Stop'`, her fazı saran `Invoke-FailClosed` (bir `FAILURE_RECEIPT.txt` yazıp `throw` eder), ve `$MyInvocation.InvocationName -ne '.'` koruması (dot-source edildiğinde `Main()` çalışmaz — yalnızca fonksiyon tanımları yüklenir, test amaçlı izole çağrılabilirlik sağlar; gerçek çalıştırmada bu koşul her zaman doğrudur). Hiçbir fazda "uyarı ver, devam et" davranışı **canlıyı etkileyen** bir adım için kullanılmaz — DEFECT Z öncesi `Stop-LiveService`'in port kontrolünde yalnızca uyaran eski davranışı, bu HEAD'de artık fail-closed'a çevrilmiştir (script başlığı, satır 78-80).

## 9. Çevrimdışı paket modeli

Bkz. Belge 03 §6 — `requirements.lock` + `build/wheelhouse/` bu HEAD'de **mevcuttur** (eski belge setinin "henüz mevcut değil" notu artık geçersizdir). `-AllowNetworkInstallFallback` yalnızca script'in kendi geliştirme/test amaçlı escape hatch'idir, üretimde kullanılmamalıdır.

## 10. Nihai FULL model — bu current-state fazının sınırı

Proje sıralaması gereği açıkça belirtilir: **bu current-state fazı bir "final FULL build" değildir.** Planlanan sıralama şöyledir: açık teknik maddelerin kapanışı → CURRENT-STATE dokümantasyonu (bu faz) → Puantaj geliştirme → Puantaj entegrasyon/güvenlik/devir doğrulama → kalan teknik defter kapanışı → bilinmeyen defekt taraması → **final kaynak SHA** → uzak CI → **FINAL FULL** → final dokümantasyon yenilemesi → kurumsal teslim. Bu belge setindeki her SHA referansı (`873e6d3...`) bu ara aşamanın anlık görüntüsüdür; nihai FULL release paketi, Puantaj tamamlandıktan ve kaynak kilitlendikten **sonra** yeniden üretilecek ve bu belgeler o noktada tekrar güncellenecektir — bu, şimdiden vaat edilen ama henüz gerçekleşmemiş bir adımdır (**PLANNED_FUTURE**).
