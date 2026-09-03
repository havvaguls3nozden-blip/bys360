Doküman Adı: BYS360 Yedekleme, Geri Dönüş ve Felaket Kurtarma Kılavuzu
Doküman Türü: Operasyon / Felaket Kurtarma
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası, yerel HEAD değil)
Son Güncelleme: 2026-09-02

---

Bu belge `docs/handover/DISASTER_RECOVERY.md`, `DATABASE_MIGRATION.md` ve `ROLLBACK.md`'nin doğrudan halefidir; bu HEAD'deki gerçek `cutover_bys360_candidate.ps1` ve `rollback_bys360_candidate.ps1` içeriğine göre yeniden ifade edilmiştir. Kanıt sınıflandırma anahtarı Belge 03 ile aynıdır.

---

## 1. Veritabanı yedeği — ne zaman, nasıl, nereye

Bu HEAD'de **iki** ayrı `pg_dump` çağrı noktası tespit edilmiştir (SCRIPT_VERIFIED):

| Nerede | Fonksiyon | Dizin | Amaç |
|---|---|---|---|
| Aday hazırlama (Faz 10/16) | `Backup-SourceDatabase`, `prepare_bys360_candidate.ps1:1196-1226` | `C:\bys360\backups\candidate_prep_<DeployId>\<db>.dump` | Shadow rehearsal'ın restore edeceği kaynak dump |
| Cutover (Faz 5/20) | `Backup-LiveDatabase`, `cutover_bys360_candidate.ps1:742-767` | `C:\bys360\backups\predeploy_cutover_<DeployId>\<db>.dump` | Canlı migration'dan **hemen önce** alınan son yedek |

Her iki fonksiyon da aynı disiplini uygular: `pg_dump -F c` (custom format), `$env:PGPASSWORD` yalnızca çağrı süresince set edilip `finally` bloğunda temizlenir, dosyanın **var olduğu** ve **sıfır bayt olmadığı** ayrıca doğrulanır — biri eksikse `DB_BACKUP_FAILED` ile kapanır. Bu yedekler **hiçbir zaman** cutover veya rollback tarafından silinmez (script içinde `Remove-Item` çağrısı bu dizinlere karşı yoktur; `docs/handover/ROLLBACK.md`'nin "DB backups are never deleted by rollback" iddiası bu HEAD'de doğrulanmıştır).

**Önemli boşluk (bilinçli işaretleniyor):** Bu iki nokta dışında, kurumun düzenli (candidate-prep/cutover tetiklemeyen) bir **zamanlanmış** PostgreSQL yedekleme görevi bu repoda tespit edilmemiştir (SCRIPT_VERIFIED, negatif — `scripts/windows` altında bağımsız bir backup-scheduler script'i yok; `scripts/archive/pre_handover_20260708/windows/pre_live_backup_plan.ps1` yalnızca arşivlenmiş, aktif kullanımda olmayan bir dosyadır). **REQUIRES_INSTITUTIONAL_DECISION**: kurumun bir cutover/candidate-prep çalıştırılmayan haftalarda/aylarda düzenli, bağımsız bir DB yedekleme rutini (örn. günlük `pg_dump` cron/Scheduled Task) tanımlaması önerilir; bu current-state fazı bu rutinin var olduğunu doğrulayamaz.

## 2. Uygulama paketi yedeği

- **Release ZIP'leri**: `C:\bys360\releases\` altında güncel ve önceki FULL release ZIP'leri saklanır (`docs/handover/LIVE_INSTALLATION.md`'nin dizin yapısı tablosu, DOCUMENTATION_DERIVED — bu HEAD'de doğrudan gözlemlenemez çünkü bu bir üretim sunucusu yol yapısıdır).
- **Önceki ağaç**: Her başarılı cutover, tam önceki `C:\bys360\project\` ağacını (kendi `.venv`'i dahil) **silmez, taşır**: `C:\bys360\previous\<timestamp>_<PreviousSourceSha>\` (`Move-ApplicationTreeIntoPlace`, `cutover_bys360_candidate.ps1:848-894`, SCRIPT_VERIFIED). Bu, uygulama-kodu seviyesinde anlık bir "yedek" işlevi görür.
- **`.env` / `instance\`**: cutover Faz 6/20 (`Protect-PersistentState`, satır 774-804), taşımadan **önce** bu iki öğeyi `C:\bys360\backups\cutover_state_<DeployId>\` altına kopyalar (Copy-Item, taşımaz) — `.env` yoksa `STATE_PRESERVE_FAILED` ile kapanır. `$StorageRoot`/`$LocalStorageRoot` bu adımda **kopyalanmaz**, çünkü onlar zaten yerinde, dokunulmamış kalır (satır 801 açık log mesajı).

## 3. Kalıcı dosyalar (persistent files)

`C:\bys360\storage\` ve `C:\bys360\local_storage\` — Dosya Merkezi ve diğer disk-üstü kalıcı içerik — hiçbir candidate hazırlığı, cutover veya rollback adımı tarafından **asla** yeniden oluşturulmaz, üzerine yazılmaz veya silinmez (bu üç script'te de bu iki kök için `Remove-Item`/`Copy-Item` hedefi olarak kullanım **yoktur** — yapısal garanti, script başlıklarında da açıkça belirtilmiştir). Bu klasörlerin kendi yedeklenmesi (örn. dosya sunucusu düzeyinde snapshot/replikasyon) bu deployment modelinin kapsamı **dışındadır** — **REQUIRES_INSTITUTIONAL_DECISION**.

## 4. Yapılandırma yedeği

`.env` içeriği Bölüm 2'de anlatıldığı gibi her cutover'da otomatik olarak `C:\bys360\backups\cutover_state_<DeployId>\.env` altına kopyalanır. Ayrıca kurumun bu dosyayı (ve gerçek PostgreSQL kimlik bilgilerini) kendi güvenli, script dışı bir kanalda (parola yöneticisi, kasa) ayrıca sakladığı varsayılır — bu, `docs/handover/SECRETS_AND_PERSISTENCE.md`'nin "must be supplied externally" ilkesinin doğal sonucudur; bu current-state fazı kurumun böyle bir kasa kullanıp kullanmadığını doğrulayamaz (**NOT_YET_FINALIZED**).

## 5. RPO / RTO

| Alan | Değer | Durum |
|---|---|---|
| RPO (Recovery Point Objective) | Tanımlanmamış | **REQUIRES_INSTITUTIONAL_DECISION** — repoda veya `docs/handover/` altında sayısal bir RPO hedefi bulunamadı |
| RTO (Recovery Time Objective) | Tanımlanmamış | **REQUIRES_INSTITUTIONAL_DECISION** — aynı şekilde bulunamadı |

Bulgu: mevcut mekanizma, RPO'yu **her cutover anına** (Faz 5/20 yedeği, migration'dan hemen önce) sıkıştırır — yani "planlı bir cutover sırasında" veri kaybı penceresi teorik olarak sıfıra yakındır, ama **cutover'lar arası dönemde** günlük/haftalık bir yedekleme rutini olmadığı sürece (Bölüm 1'deki boşluk), gerçek RPO son cutover'dan bu yana geçen süre kadar büyüktür. RTO ise cutover'ın 6-15. fazları (durdur → taşı → migrate et → başlat) ile sınırlıdır ve bu adımların **saniyeler/düşük dakikalar** mertebesinde olması tasarım hedefidir (`docs/handover/CUTOVER.md`, "downtime window ... should therefore be dominated by steps 6–15 only"), ama bu süre bu HEAD'de gerçek bir üretim koşumuyla **ölçülmemiştir** (PRODUCTION_HISTORICAL/NOT_YET_FINALIZED).

## 6. Geri yükleme (restore) bağımlılıkları

Bir `pg_dump` yedeğini geri yüklemek için gereklidir:
- `pg_restore.exe` (`$PgBinPath`, varsayılan `C:\Program Files\PostgreSQL\15\bin`).
- Hedef veritabanına bağlanabilecek uygun rol (uygulama rolü, `--no-owner --no-privileges` bayraklarıyla — `docs/handover/DATABASE_MIGRATION.md`'de ayrıntılı gerekçelendirilmiş: gerçek üretim dump'ı postgres-owned fonksiyon/trigger içerir, bu bayraklar olmadan `pg_restore` exit code 1 ile döner).
- Restore çıkış kodunun **kesinlikle 0** olduğunun doğrulanması — tablo sayısının "yeterli görünmesi" **kabul edilebilir bir kanıt değildir** (bu, önceki bir tooling sürümünde gevşek kabul edilip sonradan sıkılaştırılmış, DOCUMENTATION_DERIVED).

## 7. Geri yükleme prosedürü (manuel, felaket senaryosu)

1. Hangi yedeğin geri yükleneceğini kesinleştirin — ilgili `deploy_logs\<run>\` dizinindeki log/makbuz, tam yedek yolunu (`$Script:Receipt.DB_BACKUP_PATH`) içerir; birden fazla yakın-zamanlı yedek varsa **yalnızca dosya zaman damgasına göre tahmin etmeyin**.
2. Geri yükleme öncesi, mevcut (kısmen migrate edilmiş olabilecek) veritabanının **kendi** anlık yedeğini alın — atacak olsanız bile, geri yükleme sırasında bir şey ters giderse geri dönecek bir noktanız olsun.
3. `pg_restore --no-owner --no-privileges` ile, uygulama rolü olarak geri yükleyin; `exit_code == 0` şartını kesin tutun.
4. Geri yüklenen veritabanının Alembic revizyonunu (`flask db current` veya doğrudan `SELECT version_num FROM alembic_version;`) beklenen değerle karşılaştırarak doğrulayın.

## 8. Rollback paketi prosedürü (uygulama kodu)

`rollback_bys360_candidate.ps1` (SCRIPT_VERIFIED, script başlığı ve receipt şeması, satır 1-181):

- **Zorunlu, tahminsiz parametreler**: `-PreviousDir` ve `-ActiveDeploymentReceiptPath` — script "en son" bir önceki dizini veya makbuzu **otomatik keşfetmez**; operatör açıkça belirtmelidir (satır 79-81, 91-114 gerekçe).
- **Aktif-dağıtım makbuz bağlama** (Faz 3a, coordinator eklentisi, 2026-08-26): mevcut `C:\bys360\project`'in `SOURCE_SHA`'sı, verilen `-ActiveDeploymentReceiptPath`'teki `DEPLOYMENT_RECEIPT.txt`'nin `CANDIDATE_SOURCE_SHA` alanıyla; `-PreviousDir`'in kendisi de aynı makbuzun `PREVIOUS_DIR`/`PREVIOUS_SOURCE_SHA` alanlarıyla eşleşmelidir — uyuşmazlıkta `Invoke-FailClosed`, hiçbir canlı adım (görev durdurma, ağaç taşıma) çalışmadan önce.
- **Receipt alanları**: `PREVIOUS_DIR`, `PREVIOUS_SOURCE_SHA`, `CURRENT_SOURCE_SHA_BEFORE`, `DEPLOYMENT_BINDING`, `QUARANTINE_DIR`, `DB_REVISION_AWARENESS`, `ROLLBACK_PATH` (`PRE_MIGRATION` | `POST_MIGRATION_ATTESTED`), `SERVICE_RESULT`, `LOCAL_HEALTH`, `PUBLIC_HEALTH`, `ROLLBACK_EXIT_CODE` (satır 169-181, CODE_VERIFIED).
- **Hiçbir şey silinmez**: geri dönülen mevcut ağaç karantinaya alınır (taşınır), geri yüklenen `-PreviousDir` **kopyalanır** (taşınmaz) — yeniden deneme/denetim için sağlam kalır (satır 74-77).

## 9. Migration geri dönüşü (rollback) sınırlamaları — Alembic downgrade hiçbir zaman otomatik değildir

`rollback_bys360_candidate.ps1`'in başlığında **büyük harflerle** yazılmıştır: "THIS SCRIPT NEVER RUNS AN AUTOMATIC ALEMBIC DOWNGRADE -- NOT EVER, NOT UNDER ANY FLAG." (satır 14-22, SCRIPT_VERIFIED). `-Downgrade`/`-RunAlembicDowngrade` gibi bir anahtar **yoktur ve eklenmeyecektir**. Mevcut DB revizyonu yalnızca operatör bilgisi için okunup loglanır (`Get-CurrentDbRevisionForAwareness`), asla yıkıcı bir aksiyon tetiklemez. Manuel bir şema downgrade'i gerekiyorsa bu, bu script'in kapsamı dışında, ayrı, insan-incelemeli bir işlemdir.

### İki rollback yolu

- **(a) Migration-öncesi (trivial, her zaman güvenli)**: cutover, canlı `flask db upgrade` (Faz 12/20) hiç çalışmadan önce başarısız oldu. Veritabanı hiç değişmedi; uygulama ağacını geri almak koşulsuz güvenlidir. Script bunu **otomatik** algılar (mevcut DB revizyonu == önceki ağacın kendi `CANDIDATE_READY.json`'ındaki `MIGRATION_HEAD`'i ise) ve ek onay istemez.
- **(b) Migration-sonrası (açık, kanıta dayalı operatör onayı gerektirir)**: canlı migration başarıyla tamamlandı ama sonradan bir kontrol (health/smoke/security) başarısız oldu ve operatör kodu geri almak istiyor — veritabanı zaten yeni revizyonda. Bu **yalnızca** önceki ağacın kodunun zaten-ilerlemiş şemayla gerçekten uyumlu olduğu **kanıtlanmışsa** güvenlidir. Script bunu asla varsaymaz: `-PostMigrationAppTreeCompatible` anahtarı **açıkça** geçirilmelidir; bu, operatörün ilgili çift için (`git diff <previous>..<candidate> --stat`, `app/`, `config.py`, `wsgi.py`, `run_server.py` dışında değişiklik olup olmadığı) kendisinin doğruladığı bir beyandır. Bu belge, geçmişte bir sürüm çiftinin (`cb2e57c` → `ec4e56b`) bu şekilde güvenli bulunduğunu **yalnızca o çifte özgü tarihsel bir veri noktası** olarak aktarır (`docs/handover/ROLLBACK.md`), gelecekteki hiçbir çift için genellenemez.

## 10. Sürüm-seviyesi (release-level) rollback

Uygulama-ağacı rollback'i yeterli değilse (örn. `previous\` dizini artık mevcut değilse — daha sonraki bir cutover tarafından üzerine yazıldıysa), kurtarma `C:\bys360\releases\` altındaki saklı FULL release ZIP'ine döner ve bu, **tam bir candidate-hazırlama girdisi** olarak yeniden ele alınır (`docs/handover/DISASTER_RECOVERY.md`, DOCUMENTATION_DERIVED) — kısmi parçalardan bir ağaç yeniden inşa etmeye **çalışılmaz**.

## 11. Felaket kurtarma kontrol listesi

1. İlgili `FAILURE_RECEIPT.txt`'yi (veya başarılıysa `DEPLOYMENT_RECEIPT.txt`'yi) okuyun — hangi fazda durduğunu **her zaman önce** belirleyin.
2. Fazı Belge 14/15'teki 20 adımlık cutover akışıyla eşleştirin: 6'dan önce mi (canlı hiç durmadı) — 6 ile 11 arası mı (durdu ama migration hiç çalışmadı, migration-öncesi trivial rollback) — 12'de mi (en yüksek riskli durum, veritabanının **gerçek** durumu kontrol edilmeden hiçbir varsayımda bulunulmaz) — 13-19 arası mı (migration tamamlandı, migration-sonrası dikkatli rollback) — yalnızca 20'de mi (uygulama aslında sağlıklı, yalnızca makbuz yazımı başarısız, düşük riskli bir defter tutma sorunu).
3. Faz 12 (canlı migration) başarısızlığında: **asla körü körüne yeniden denemeyin**. Gerçek `DATABASE_URL` ile `flask db current` çalıştırıp veritabanının fiilen hangi revizyonda olduğunu doğrudan sorgulayın — migration kısmen DDL uygulamış, hiç uygulamamış veya (script'in kendi migration'ının transaction sınırlarına bağlı olarak) kısmen commit etmiş olabilir.
4. `previous\<timestamp_SHA>\` ağacının hâlâ mevcut olduğunu doğrulayın (Bölüm 10'daki sınırlama).
5. Bir kurtarma kararı verilmeden önce mevcut (olası kısmi) durumun **kendi** yedeğini alın (Bölüm 7, adım 2).
6. Kurtarma sonrası: `/healthz`, `/readyz`, ve mümkünse `/versionz` (loopback'ten) ile doğrulayın; DB revizyonunun beklenen değerle eşleştiğini teyit edin.

## 12. Geri yükleme sonrası doğrulama

- `flask db current` beklenen revizyonu döndürüyor mu.
- `/healthz` 200, `/readyz` `status=ready` (200) dönüyor mu.
- File Center tablo sayısı 19/19 mu (`cutover_bys360_candidate.ps1:1050-1066`'daki aynı 19 tablo listesiyle elle karşılaştırılabilir; SCRIPT_VERIFIED tablo adları: `file_storage_folders, file_storage_items, file_transfers, file_transfer_items, file_transfer_recipients, file_share_links, file_requests, file_request_uploads, file_download_logs, file_access_logs, file_quota_usage, file_security_scans, file_audit_logs, file_quota_policies, file_upload_sessions, file_upload_chunks, file_center_mail_logs, file_center_role_permissions, file_center_settings`).
- Fresh/boş bir veritabanında beklenen "guarded exception" log satırları (`user_menu_permissions`/`role_menu_defaults` ile ilgili `ERROR`-seviyeli, ama zararsız satırlar) dışında gerçek ERROR/CRITICAL yok mu (Bölüm 1'deki desen listesiyle).

**Özet uyarı:** Bu belgedeki her prosedür bu HEAD'deki gerçek script içeriğinden türetilmiştir (SCRIPT_VERIFIED), ama **hiçbiri bu current-state fazında gerçek üretim sunucusuna karşı fiilen çalıştırılmamıştır**. Bir felaket kurtarma tatbikatının (dry run) gerçek/gerçeğe-yakın verilerle en az bir kez uygulanması, bu prosedürün "devredilebilir" sayılabilmesi için `docs/handover/RELEASE_VERIFICATION.md`'deki Devredilebilirlik Gate rubriğinin (Kategori 6: ROLLBACK HANDOVER) açık şartıdır.
