Doküman Adı: BYS360 İşletim, Bakım ve Güncelleme Kılavuzu
Doküman Türü: Operasyon / Bakım
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası, yerel HEAD değil)
Son Güncelleme: 2026-09-02

---

Bu belge, `docs/handover/BYS360_BAKIM_RUNBOOK.md`'nin (kısa, madde işaretli bir runbook) doğrudan halefidir ve onu bu HEAD'deki gerçek script/endpoint içeriğine göre genişletir. Kanıt sınıflandırma anahtarı Belge 03 ile aynıdır.

---

## 1. Günlük kontroller

| Kontrol | Nasıl yapılır | Kanıt |
|---|---|---|
| `/login` erişilebilir mi | Tarayıcı/`curl` ile HTTP 200/302 beklenir | DOCUMENTATION_DERIVED (`BYS360_BAKIM_RUNBOOK.md`) |
| `/healthz` doğru JSON dönüyor mu | `curl http://<host>/healthz` → `{"status":"ok","service":"bys360"}`, HTTP 200 | CODE_VERIFIED (`app/routes.py:72-74`) |
| `/readyz` durumu | `status=ready` (200) mi yoksa `status=degraded` (503, `schema_error_count>0`) mi | CODE_VERIFIED (`app/routes.py:77-86`) — `degraded` dönerse şema-sözleşme hatası var demektir, aynı gün içinde araştırılmalı |
| Son 24 saatte 5xx artışı | Log dosyası (`C:\bys360\logs\bys360_live_waitress_80.log`) taranır | DOCUMENTATION_DERIVED, log yolu SCRIPT_VERIFIED (`cutover_bys360_candidate.ps1:121` `$LogPath` varsayılanı) |
| Mail/bildirim zamanlanmış görevleri beklenen saatte çalışmış mı | `Get-ScheduledTask` + Görev Zamanlayıcı geçmişi | Bkz. Bölüm 6 (görev envanteri) |
| Loglarda tekrarlı hata deseni var mı | `Test-LogForRealErrors` desenleriyle aynı mantık: `\| ERROR \|`, `\| CRITICAL \|`, `Traceback`, `UnicodeEncodeError/DecodeError`, `sqlalchemy.exc.OperationalError`, `SchemaAdoptionError` — bare "error"/"critical" substring **değil** | SCRIPT_VERIFIED (`prepare_bys360_candidate.ps1:351-381`, `cutover_bys360_candidate.ps1:297` benzeri) |

## 2. Haftalık kontroller

- Yedek alınmış mı — bkz. Belge 06. **Not:** bu HEAD'de ayrı, zamanlanmış/bağımsız bir "haftalık DB backup" script'i **tespit edilmemiştir**; script tabanlı `pg_dump` yalnızca candidate hazırlığı (`Backup-SourceDatabase`, `prepare_bys360_candidate.ps1:1196-1226`) ve cutover'ın kendi akışı (`Backup-LiveDatabase`, `cutover_bys360_candidate.ps1:~742`) içinde tetiklenir — yani bir cutover/candidate-prep çalıştırılmadığı haftalarda otomatik bir DB yedeği **alınmaz** (SCRIPT_VERIFIED, negatif arama sonucu: `scripts/` altında bağımsız bir zamanlanmış backup script'i bulunamadı). Bu, **REQUIRES_INSTITUTIONAL_DECISION** olarak işaretlenir: kurumun düzenli (cutover'dan bağımsız) bir PostgreSQL yedekleme politikası ayrıca tanımlanmalıdır.
- Disk doluluk oranı — özellikle `C:\bys360\storage`, `C:\bys360\local_storage`, `C:\bys360\backups`, `C:\bys360\releases`, `C:\bys360\logs`, `C:\bys360\deploy_logs`, `C:\bys360\previous`, `C:\bys360\candidate` altları (DOC-03'te ayrı bir "Dizin Yapısı" bölümü yoktur — bu yollar DOC-04/06/13'e dağılmış script referanslarından derlenmiştir, tek bir merkezi envanter olarak henüz konsolide edilmemiştir).
- Log rotasyonu çalışıyor mu — bu HEAD'de kod tabanında ayrı bir log-rotasyon mekanizması aranmış, `scripts/` altında bulunamamıştır (SCRIPT_VERIFIED, negatif); bu **REQUIRES_INSTITUTIONAL_DECISION** olarak işaretlenmelidir (Waitress log dosyası `*>>` ile append modunda büyümeye devam eder — `install_bys360_live_waitress_80_task_v1.ps1:82`).
- Bekleyen migration var mı — `flask db current` vs `flask db heads` karşılaştırması (bkz. Belge 06/`DATABASE_MIGRATION.md`).
- Kullanıcı/rol değişiklikleri audit log'a düşüyor mu — DOCUMENTATION_DERIVED, ilgili yetkilendirme/audit belgeleriyle (Belge 05/11) çapraz okunmalı, bu belgenin kapsamı dışında derinlemesine doğrulanmamıştır.

## 3. Aylık kontroller

- Güvenli release preflight çalıştırılır: `scripts/windows/check_bys360_release_zip_preflight_v1.ps1` ve/veya `scripts/release/build_bys360_safe_release.py --verify` (dosyaların varlığı CODE_VERIFIED; bu belgeyi yazarken içerikleri tek tek çalıştırılmadı).
- Yetki matrisi örnek kullanıcılarla test edilir — ayrıntı Belge 05/11 kapsamındadır.
- Performans, personel, iletişim/anket ve destek kritik akışları gözden geçirilir.
- Eski log ve geçici dosyalar temizlenir — manuel operatör işlemi; otomatik bir temizlik script'i bu inceleme sırasında `scripts/windows` altında tespit edilmemiştir.
- Kalite kapısı taraması: `python scripts\quality\bys360_score100_quality_gate_v1.py --project-root . --mode audit --output-dir reports\quality\score100_quality_gate_v1` (dosya varlığı CODE_VERIFIED: `scripts/quality/bys360_score100_quality_gate_v1.py`).

## 4. Log konumları (bu HEAD'de doğrulanan)

| Log | Yol | Kanıt |
|---|---|---|
| Canlı uygulama (Waitress/Scheduled Task stdout+stderr) | `C:\bys360\logs\bys360_live_waitress_80.log` | SCRIPT_VERIFIED (`install_bys360_live_waitress_80_task_v1.ps1:42`, `cutover_bys360_candidate.ps1:121`) |
| Aday hazırlama çalışma günlüğü | `C:\bys360\deploy_logs\candidate_prep_<timestamp>\candidate_prep.log` | SCRIPT_VERIFIED (`prepare_bys360_candidate.ps1:196-198`) |
| Cutover çalışma günlüğü | `C:\bys360\deploy_logs\cutover_<timestamp>\cutover.log` | SCRIPT_VERIFIED (`cutover_bys360_candidate.ps1:151-153`) |
| Aday sağlık-boot stdout/stderr | `C:\bys360\deploy_logs\<run>\candidate_health_boot.stdout.log` / `.stderr.log` | SCRIPT_VERIFIED (`prepare_bys360_candidate.ps1:1791-1792`) |
| Hata makbuzu (her fazda) | `C:\bys360\deploy_logs\<run>\FAILURE_RECEIPT.txt` | SCRIPT_VERIFIED (her üç script) |
| Başarı makbuzu (yalnızca cutover) | `C:\bys360\deploy_logs\cutover_<timestamp>\DEPLOYMENT_RECEIPT.txt` | SCRIPT_VERIFIED (`cutover_bys360_candidate.ps1:1344-1355`) |

## 5. Veritabanı büyümesi

Bu incelemede canlı veritabanının gerçek boyutu/büyüme eğrisi doğrudan gözlemlenememiştir (bu oturumun canlı sunucuya erişimi yoktur) — **NOT_YET_FINALIZED**. Operatör, `pg_dump` çıktı boyutunu (`Backup-SourceDatabase`/`Backup-LiveDatabase`'in yazdığı `.dump` dosyası boyutu, her ikisi de sıfır bayt kontrolü yapar — `prepare_bys360_candidate.ps1:1217-1220`) zaman içinde izleyerek kaba bir büyüme sinyali elde edebilir; bu, kurumsal bir kapasite planlama sürecinin yerini tutmaz.

## 6. Zamanlanmış görevler (Scheduled Tasks) envanteri

Bu HEAD'de `scripts/windows/install_bys360_*.ps1` altında canlı görev kurulum/kayıt script'leri bulunmaktadır (dosya adları CODE_VERIFIED, `Glob` ile listelendi): ana canlı servis (`install_bys360_live_waitress_80_task_v1.ps1`), günlük mail görevleri (`install_bys360_daily_mail_tasks_v1_4.ps1`, `v1_6`), günlük hava durumu maili, günlük "pulse" maili, kurumsal bilgi merkezi görevleri (`install_corporate_information_center_tasks_v3_0_phase2.ps1`, `install_bys360_corporate_information_tasks_v3_0.ps1`), yönetici özet görevleri (`register_bys360_executive_summary_tasks_v2_14_1.ps1`, `_v2_14_3`), sosyal medya otomatik içe aktarma (`install_bys360_social_auto_import_v3b2_task.ps1`), CIC otomatik mail zamanlayıcı (`install_bys360_cic_auto_mail_scheduler_task.ps1`). Bu belge her birinin **canlı sunucuda gerçekten kurulu olup olmadığını** doğrulayamaz (PRODUCTION_HISTORICAL/operatör beyanına dayalı olmalı) — yalnızca repodaki kurulum script'lerinin **varlığını** doğrular.

## 7. Uygulama yeniden başlatma prosedürü

Görev bazlı, planlı bir yeniden başlatma (canlıya alma **dışında**, örn. bellek sızıntısı şüphesi, ayarlanan bir env değişikliğinin devreye alınması) için:

```powershell
Stop-ScheduledTask -TaskName "BYS360 Live Waitress 80" -ErrorAction SilentlyContinue
# port 80'in gerçekten boşaldığını doğrulayın (Get-NetTCPConnection -LocalPort 80 -State Listen)
Start-ScheduledTask -TaskName "BYS360 Live Waitress 80"
```

Bu komut çifti `docs/handover/BYS360_CANLIYA_ALMA_REHBERI.md`'de zaten belgelenmiştir ve görev adı bu HEAD'de doğrulanmıştır. **Dikkat:** bu basit restart, cutover script'inin yaptığı PID/süreç-bağlama (`Test-ProcessBinding`) veya release-identity (`Test-ReleaseIdentityBinding`) kontrollerini **yapmaz** — yalnızca görevi durdurup başlatır; port 80'in gerçekten boşaldığının teyidi operatörün elle yapması gereken bir adımdır (bkz. Belge 13, "eski/yanlış süreç" riski).

## 8. Dağıtım (deployment) prosedürü

Tam kod-değişikliği içeren bir dağıtım için Belge 14'teki candidate → cutover akışı **hedef prosedürdür**. Basit bir restart (Bölüm 7) kod değiştirmez, yalnızca çalışan süreci yeniler.

## 9. Bağımlılık güncelleme prosedürü

- `requirements.txt` (24 üst düzey pin, `docs/handover/CANDIDATE_PREPARATION.md`'de belirtilmiş) doğrudan bağımlılıklardır.
- `requirements.lock`, tüm bağımlılık grafiğinin (doğrudan + geçişli) tam çözümlenmiş halidir; bu HEAD'de mevcuttur (bkz. Belge 03 §6).
- `build/wheelhouse/`, `scripts/release/build_bys360_wheelhouse.py` ile üretilir (script mevcut, CODE_VERIFIED); bu bakım kılavuzunun kapsamında bu script'in içeriği ayrıntılı olarak incelenmemiştir.
- Bir bağımlılık güncellemesi yapılacaksa: `requirements.txt` güncellenir → lock dosyası ve wheelhouse yeniden üretilir → yeni bir FULL release paketi (`build_bys360_safe_release.py --wheelhouse-dir ...`, schema_version=3) inşa edilir → normal candidate/cutover akışından geçirilir. Bu, doğrudan bir "canlıda `pip install --upgrade`" işlemi **değildir** ve bu modelde asla önerilmez (offline/hava boşluklu operasyon ilkesiyle çelişir).

## 10. Migration disiplini

- Manuel şema değişikliği (canlı veritabanına elle `ALTER TABLE` vb.) bu deployment modelinin **dışındadır** ve `docs/handover/BYS360_BAKIM_RUNBOOK.md`'nin devamı olan `BYS360_RISK_VE_SUREKLILIK_PLANI.md` bunu açıkça yasaklamaktadır (DOCUMENTATION_DERIVED).
- Her migration, adaylık aşamasında shadow veritabanı üzerinde prova edilmeden canlıya asla uygulanmaz (bkz. Belge 03 §8 "Veritabanı migration prosedürü" ve Belge 14 §4, Faz 10-13).
- `AUTO_REPAIR_SCHEMA` varsayılan olarak `False`'tur (`factory_bootstrap.py`, `prepare_bys360_candidate.ps1` script başlığı satır 109-113'te CODE_VERIFIED olarak alıntılanmıştır) — canlıda kendiliğinden şema onarımı **aktif değildir**, yalnızca salt-okunur şema kontrolü çalışır.

## 11. Güvenlik yaması (patching) süreci

Bu belgenin kapsamında ayrı bir OS/paket güvenlik yaması takvimi doğrulanmamıştır — **REQUIRES_INSTITUTIONAL_DECISION**. Uygulama seviyesinde, her release paketi `scripts/release/scan_bys360_release_secrets.py` ile secret taramasından geçmeden FULL (schema_version=3) paket olarak imzalanamaz (`build_bys360_safe_release.py`, `secret_scan_status`/`secret_scan_findings` manifest alanları, `prepare_bys360_candidate.ps1:639-641`'de bu alanların `PASS`/`0` olmadığı sürece candidate hazırlığının reddedildiği doğrulanmıştır — SCRIPT_VERIFIED).

## 12. Denetim (audit) kaydı gözden geçirme

Uygulama içi audit modeli (durum değiştiren işlemler + erişim denemeleri) Belge 05/11 kapsamındadır; bu belge yalnızca operasyonel/deployment audit izini (deploy_logs altındaki makbuzlar) kapsar.

## 13. Olay kayıt altına alma (incident recording)

Her başarısız candidate-prep/cutover/rollback fazı otomatik olarak `FAILURE_RECEIPT.txt` üretir (Faz adı, zaman damgası, neden, log yolu — Bölüm 4). Bir üretim olayı (canlı kesinti, veri tutarsızlığı şüphesi) yaşandığında:

1. İlgili `deploy_logs\<run>\` dizinindeki tüm makbuz ve log dosyaları **değiştirilmeden** arşivlenir.
2. Olayın hangi cutover fazında gerçekleştiği (Belge 15 "Sorun Giderme" tablosuyla eşleştirilerek) tespit edilir.
3. Kurumsal bir olay kaydı (tarih, etki süresi, kök neden, alınan aksiyon) tutulur — bu kaydın resmi şablonu bu current-state fazında tanımlanmamıştır (**REQUIRES_INSTITUTIONAL_DECISION**).

## 14. Kapasite / performans gözden geçirme

Bu current-state fazında ayrı bir kapasite planlama süreci veya performans izleme aracı (APM) doğrulanmamıştır — **NOT_YET_FINALIZED**. Yalnızca uygulama içi `/versionz`'in `route_count` alanı ve `schema_error_count` alanı, temel bir çalışma-zamanı sinyali olarak günlük kontrolde kullanılabilir (Bölüm 1).

## 15. Sürüm takibi (version tracking)

- Her cutover, `CANDIDATE_SOURCE_SHA`/`PREVIOUS_SOURCE_SHA` çiftini `DEPLOYMENT_RECEIPT.txt`'ye yazar (Bölüm 4).
- `/versionz` endpoint'i, çalışan sürecin `source_sha`/`migration_head` bilgisini (yalnızca loopback'ten) gerçek zamanlı olarak dışa verir (Belge 03 §10).
- Bu current-state dokümantasyon setinin kendisi `873e6d3348e644c5384a33a99c517600a3346cfd` HEAD'ine göre yazılmıştır — belgedeki her script satır referansı bu SHA'ya bağlıdır; sonraki bir commit'te satır numaraları kayabilir.

## 16. Bakım sahipliği (ownership)

"Tek geliştirici bilgisi" riskiyle doğrudan bağlantılı olarak: bu belge setinin amacı, tek bir kişiye/firmaya bağlı kalmadan devredilebilir bir operasyon modeli sunmaktır (`docs/handover/BYS360_RISK_VE_SUREKLILIK_PLANI.md`, DOCUMENTATION_DERIVED). Bakım sorumluluğunun kurum içinde mi yoksa dış bir yüklenicide mi olacağı, bu current-state fazının kapsamı dışında bir kurumsal karardır — **REQUIRES_INSTITUTIONAL_DECISION**.
