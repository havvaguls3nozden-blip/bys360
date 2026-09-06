Doküman Adı: BYS360 Sorun Giderme ve Müdahale Kılavuzu
Doküman Türü: Operasyon / Sorun Giderme
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası, yerel HEAD değil)
Son Güncelleme: 2026-09-02

---

Kanıt sınıflandırma anahtarı Belge 03 ile aynıdır. Bu belge `docs/handover/BYS360_KURULUM_REHBERI.md` §7 ("Sık hata kontrolleri") ve `DISASTER_RECOVERY.md`'nin doğrudan genişletilmiş halefidir; ayrı ayrı tekrarlanan ayrıntılar için ilgili current-state belgesine (03/04/06/13/14) çapraz referans verilir.

---

## 1. Uygulamaya erişilemiyor (site tamamen erişilemez)

1. `Get-ScheduledTask -TaskName "BYS360 Live Waitress 80"` ile görev durumunu kontrol edin (Bölüm 2 ile devam).
2. `Get-NetTCPConnection -LocalPort 80 -State Listen` ile port 80'de gerçekten bir dinleyici olup olmadığını doğrulayın.
3. `C:\bys360\logs\bys360_live_waitress_80.log`'un son satırlarını inceleyin — `Traceback`, `UnicodeEncodeError`/`UnicodeDecodeError`, `sqlalchemy.exc.OperationalError` gibi gerçek hata desenlerine bakın (Belge 04 §1, `Test-LogForRealErrors` desenleriyle aynı mantık — bare "error" substring'i değil).
4. Ağ/firewall/reverse-proxy katmanı ayrıca kontrol edilmelidir — bu katmanın varlığına dair temkinli değil, somut bir kanıt zinciri mevcuttur: `config.py:655`'te `PROXY_FIX_ENABLED` production/staging'de varsayılan açıktır ve cutover script'i genel uç noktayı `https://` üzerinden kontrol eder — Waitress'in önünde bir TLS sonlandırıcı katmanın bulunduğuna dair güçlü işaret vardır (bkz. DOC-13 §1). Bu katmanın kendisi bu repo'nun kapsamı dışındadır; bu belge yalnızca uygulama/Windows Task katmanını kapsar.

## 2. Port 80'de dinleyici yok

- Görev `Running` görünüyor ama port 80'de dinleyici yoksa: `run_server.py` sürecin içinde erken çökmüş olabilir (log'a bakın, Bölüm 1 madde 3).
- Görev `Ready`/`Stopped` görünüyorsa: `Start-ScheduledTask -TaskName "BYS360 Live Waitress 80"` ile manuel başlatıp ardından tekrar `Get-NetTCPConnection` ile doğrulayın (görevin gerçekten portu bağlaması birkaç saniye sürebilir — cutover script'inin kendi `Wait-CandidatePortListening`/başlatma bekleme mantığı 40 saniyeye kadar bekler, `cutover_bys360_candidate.ps1` `Start-LiveService`, satır 1099-1103: 20 deneme × 2 saniye).
- Eğer başka bir süreç port 80'i tutuyorsa (eski/artık kalmış bir süreç): kontrollü şekilde sonlandırılmalı, ardından görev yeniden başlatılmalıdır — bkz. Belge 13 §6 (DEFECT Z), gerçek cutover akışı bu senaryoyu PID/yol/zaman doğrulamasıyla otomatik engeller, ama manuel bir restart (Belge 04 §7) bu korumayı **sağlamaz**, operatörün elle doğrulaması gerekir.

## 3. Scheduled Task durmuş / beklenmedik şekilde sonlanmış

**Güncel durum (Belge 13 §5c):** canlı Scheduled Task, geçmişte yaşanan tekrarlayan 72 saatlik kesinti sorununun ardından sertleştirilmiştir — mekanik olarak doğrulanan güncel ayarlar `RestartCount=3`, `RestartInterval=PT1M`, `ExecutionTimeLimit=PT0S` (sınırsız). Yani görev süreci beklenmedik şekilde sonlanırsa, Task Scheduler artık **1 dakika arayla en fazla 3 kez otomatik olarak yeniden başlatmayı dener**. Repo'daki `install_bys360_live_waitress_80_task_v1.ps1` script'i bu parametreleri hâlâ geçirmediğinden (bkz. Belge 13 §5a), görev script'ten yeniden kaydedilirse bu otomatik yeniden başlatma davranışı kaybolabilir — böyle bir yeniden kayıttan sonra ayarların hâlâ yerinde olduğu ayrıca doğrulanmalıdır.

3 otomatik denemenin tümü tükenirse (veya görev script'ten sertleştirme kaybolacak şekilde yeniden kaydedilmişse) görev **otomatik olarak yeniden başlamaz**, yalnızca bir sonraki sistem açılışında (`AtStartup`) tekrar tetiklenir. Bu durum, günlük kontrol listesinde (`/healthz` her gün kontrol edilmeli, Belge 04 §1) erken yakalanması gereken bir sınıf arızadır. Manuel müdahale:

```powershell
Get-ScheduledTaskInfo -TaskName "BYS360 Live Waitress 80"
Start-ScheduledTask -TaskName "BYS360 Live Waitress 80"
```

Ardından `/healthz` ile doğrulayın.

## 4. `/healthz` başarısız (200 dönmüyor / hiç yanıt yok)

- `/healthz` hiçbir zaman veritabanına dokunmaz (`app/routes.py:72-74`, CODE_VERIFIED: sabit `{"status":"ok"}` döner) — bu endpoint'in başarısız olması, veritabanı değil, **Python sürecinin kendisinin** ayakta olmadığı/yanıt vermediği anlamına gelir. Bölüm 1-3'e dönün.
- Yanıt var ama 5xx ise: `run_server.py`/Waitress seviyesinde bir hata olabilir; log dosyasını inceleyin.

## 5. `/readyz` başarısız (503, `status=degraded`)

`app/routes.py:77-86` (CODE_VERIFIED): bu, `current_app.extensions["schema_check_errors"]`'in boş olmadığı anlamına gelir — yani uygulama ayakta ama **şema-sözleşme kontrolü** (`app.bootstrap.schema_contract`/`schema_validation`) hata bulmuş. Bu, veritabanı migration durumuyla doğrudan ilişkilidir:

1. `flask db current` ile veritabanının fiili Alembic revizyonunu, `flask db heads` ile beklenen hedefi karşılaştırın (Belge 06 §7).
2. Eksik/hatalı sütun/tablo varsa (`app/bootstrap/schema_contract.py`'nin beklediği ama hiçbir migration'ın oluşturmadığı bir alan — bu tür bir gerçek boşluk daha önce `c51c29032d4f` migration'ıyla kapatılmıştır, `docs/handover/DATABASE_MIGRATION.md`), yeni bir migration gerekebilir — bu, canlıda **elle** düzeltilmez, candidate/cutover akışından geçirilmelidir.
3. `payload.schema_error_count` alanı kaç alanın eksik olduğunu sayısal olarak verir; bu sayı `/readyz` yanıtında görünür.

## 6. Veritabanı erişilemez

- `DATABASE_URL` bağlantısını `psql` ile doğrudan test edin (`psql -h <host> -p <port> -U <user> -d <db>`).
- PostgreSQL Windows servisinin (`postgresql-x64-15` — bu isim tarihsel V4 script'inin varsayımıydı, bu HEAD'deki yeni script'ler artık **servis adını kontrol etmiyor**, bkz. Belge 03 §3 discrepancy notu) fiilen çalıştığını `Get-Service` ile manuel doğrulayın — yeni script'ler bunu sizin için yapmaz.
- `pg_dump.exe`/`pg_restore.exe`/`psql.exe`'nin `C:\Program Files\PostgreSQL\15\bin` altında (veya yapılandırılmış `$PgBinPath`'te) var olduğunu doğrulayın — candidate/cutover script'leri bu üçünün varlığını Faz 1'de zaten kontrol eder ve yoksa `PRECHECK_FAILED` ile kapanır.

## 7. Redis erişilemez

Redis mimari olarak **isteğe bağlıdır** (bkz. DOC-02 §6, CODE_VERIFIED) — `REDIS_URL`/`CACHE_REDIS_URL` tanımlı değilse veya erişilemezse sistem dosya/JSON veya bellek-içi yedek moda düşer, açılışı engellemez. Redis bağlantı hatası şüphesinde: `redis-cli ping` ile bağlantıyı doğrudan test edin; uygulamanın yedek moda düşüp düşmediğini log'dan izleyin.

## 8. Migration uyumsuzluğu

- Semptom: `flask db upgrade` hata veriyor veya `/readyz` `degraded` dönüyor.
- **Canlıda asla elle `ALTER TABLE`/manuel şema düzeltmesi yapılmaz** (Belge 04 §10). Doğru yol: sorunu candidate-prep'in shadow-rehearsal fazında (Belge 14 §4, Faz 10-13) yeniden üretip orada düzeltmek, ardından yeni bir candidate/cutover koşusu yapmak.
- Cutover'ın **canlı** migration'ı (Faz 12/20) başarısız olursa: **asla körü körüne yeniden denemeyin** — `flask db current`'ı gerçek `DATABASE_URL` ile çalıştırıp veritabanının fiilen hangi durumda olduğunu önce doğrulayın (Belge 06 §11, madde 3).

## 9. Login problemi

`docs/handover/BYS360_KURULUM_REHBERI.md` §7 tablosuna göre (DOCUMENTATION_DERIVED, bu belgenin kapsamında yeniden doğrulanmadı): `DATABASE_URL`, port, app factory hatası kontrol edilmelidir. `/healthz` 200 dönüyorsa süreç ayaktadır; login'e özgü bir sorun muhtemelen kimlik doğrulama/oturum katmanına (Belge 05/11 kapsamı) ilişkindir.

## 10. Yetki (authorization) problemi

Rol/menü/yetki motoruna ilişkin ayrıntılı sorun giderme Belge 05/11 kapsamındadır (yetkilendirme modeli, menü görünürlüğü, backend guard). Bu belge yalnızca operasyon/deployment katmanını kapsar; "kullanıcı X, Y sayfasını görmeli ama görmüyor" türü sorunlar için ilgili yetkilendirme dokümantasyonuna bakın.

## 11. Mail/e-posta gönderim hatası

Bu belgenin kapsamında SMTP/mail entegrasyonunun kod seviyesi ayrıntıları incelenmemiştir. Operasyonel ilk adım: ilgili zamanlanmış görevin (Belge 04 §6'daki mail görevleri listesi) `Get-ScheduledTaskInfo` ile son çalışma sonucunu (`LastTaskResult`) kontrol edin; `0` dışında bir kod, görevin kendi log çıktısının incelenmesini gerektirir.

## 12. Zamanlanmış görev (mail/bildirim/rapor) çalışmadı

1. `Get-ScheduledTask -TaskName "<görev adı>" | Get-ScheduledTaskInfo` ile `LastRunTime`/`LastTaskResult`/`NextRunTime` kontrol edilir.
2. Görevin kendi log dosyası (varsa) incelenir.
3. Görevin ilgili `install_bys360_*.ps1`/`register_bys360_*.ps1` script'i ile **yeniden** kurulup kurulmaması gerektiği (parametre/yol değişikliği olup olmadığı) değerlendirilir — bu script'lerin çoğu (ana canlı görev dışında) bu belgenin kapsamında tek tek satır satır incelenmemiştir.

## 13. Release doğrulama hatası (`--verify` başarısız)

`scripts/release/build_bys360_safe_release.py --verify` başarısız olursa (Belge 14 §2, Belge 03 §12):

- **Bu paketi candidate hazırlığı için kullanmayın.** Hash/manifest doğrulaması, `Test-PackageHash`/`Test-PackageManifest`/`Test-EmbeddedSourceSha` fazlarında zaten kendiliğinden tekrar uygulanır ve tutarsız bir paket `PACKAGE_FAILED`/`MANIFEST_FAILED`/`SOURCE_SHA_FAILED` ile candidate hazırlığını erkenden durdurur — ama bunu candidate-prep'e bırakmadan önce, `--verify` çıktısındaki `findings` listesini okuyup **kök nedeni** (eksik dosya, hash uyuşmazlığı, yasaklı yol) belirleyin.
- Paketi yeniden inşa edin (`build_bys360_safe_release.py`), gerekirse `--expected-source-sha`'yı doğru, bağımsız bir kaynaktan (repo `git rev-parse HEAD`, e-posta, ayrı manifest) alın — **asla ZIP dosya adının kendisine güvenmeyin**.

## 14. Cutover başarısızlığı

Bkz. Belge 06 §11 (tam felaket kurtarma kontrol listesi, bu belgede tekrarlanmaz). Kısa özet: **her zaman önce `FAILURE_RECEIPT.txt`'yi okuyun**, hangi fazın başarısız olduğunu 20 adımlık akışla (Belge 14 §5) eşleştirin, Faz 12 (canlı migration) başarısızlığında veritabanının fiili durumunu **doğrulamadan hiçbir varsayımda bulunmayın**.

## 15. Rollback kararı

- Migration hiç çalışmadıysa (cutover Faz 1-11 arasında başarısız oldu): rollback trivial'dir, ek onay gerekmez (Belge 06 §9(a)).
- Migration çalıştıysa (Faz 12+ başarılı, sonra bir kontrol başarısız oldu): rollback yalnızca operatörün **kendi doğruladığı** kod/şema uyumluluğu kanıtıyla, `-PostMigrationAppTreeCompatible` açık bayrağıyla yapılabilir (Belge 06 §9(b)) — asla varsayılmaz.
- Hiçbir durumda otomatik Alembic downgrade **çalıştırılmaz** — bu, `rollback_bys360_candidate.ps1`'in mutlak bir tasarım kuralıdır (Belge 06 §9 giriş).

## 16. Log inceleme ve kanıt toplama (incident evidence capture)

1. İlgili `C:\bys360\deploy_logs\<run>\` dizininin **tamamını** (log dosyası + `FAILURE_RECEIPT.txt`/`DEPLOYMENT_RECEIPT.txt` + varsa `candidate_health_boot.stdout/stderr.log`) değiştirilmeden bir arşiv konumuna kopyalayın.
2. `C:\bys360\logs\bys360_live_waitress_80.log`'un ilgili zaman aralığındaki bölümünü ayrıca saklayın.
3. Gerçek ERROR/CRITICAL taraması için Bölüm 1 madde 3'teki desen listesini kullanın — fresh/boş bir veritabanında beklenen `user_menu_permissions`/`role_menu_defaults` "guarded exception" satırlarını (Belge 06 §12) yanlışlıkla migration arızası olarak yorumlamayın.
4. Olayı Belge 04 §13'teki (İşletim/Bakım Kılavuzu) olay-kayıt prosedürüne göre kaydedin.

## 17. Hızlı referans tablosu

| Semptom | İlk bakılacak yer |
|---|---|
| Site tamamen erişilemez | Bölüm 1-3 |
| `/healthz` 200 değil | Bölüm 4 |
| `/readyz` 503/degraded | Bölüm 5 |
| DB bağlantı hatası | Bölüm 6 |
| Redis hatası | Bölüm 7 |
| Migration hatası | Bölüm 8 |
| Login açılmıyor | Bölüm 9 |
| Yetki görünmüyor | Bölüm 10 |
| Mail gitmiyor | Bölüm 11 |
| Zamanlanmış görev çalışmadı | Bölüm 12 |
| Release `--verify` başarısız | Bölüm 13 |
| Cutover ortada durdu | Bölüm 14 |
| Rollback gerekiyor mu | Bölüm 15 |
