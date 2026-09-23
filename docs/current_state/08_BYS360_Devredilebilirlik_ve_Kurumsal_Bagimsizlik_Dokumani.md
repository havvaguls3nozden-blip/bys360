Doküman Adı: BYS360 Devredilebilirlik ve Kurumsal Bağımsızlık Dokümanı
Doküman Türü: Devir / Süreklilik
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası, yerel HEAD değil)
Son Güncelleme: 2026-09-02

---

## 1. Amaç

Bu doküman, BYS360'ın belirli bir kişiye, firmaya veya araca bağımlı **olmadan** kurum tarafından sahiplenilip sürdürülebilir olup olmadığını değerlendirir. **Bu belge nihai bir devredilebilirlik puanı yayımlamaz** — nedeni §8'de açıklanmıştır.

## 2. Tek geliştirici bağımlılığı — mitigasyon durumu

BYS360'ın mevcut geliştirme geçmişi (commit mesajları, tek `Git user: BYS360 Quality Gate` deseni) tek/az sayıda geliştiriciye işaret eder — bu risk hem `docs/handover/BYS360_RISK_VE_SUREKLILIK_PLANI.md` (DOCUMENTATION_DERIVED: "Tek geliştirici bilgisi → Devir zorluğu") hem önceki devir belgesinin "Bus Factor" bölümünde (DOCUMENTATION_DERIVED) açıkça kabul edilir. Azaltım kanıtları:

| Kanıt | Kaynak/kanıt türü |
|---|---|
| Kaynak kontrolü altında tam commit geçmişi | CODE_VERIFIED (`git log`) |
| Deterministik release üretimi (aynı commit → byte-birebir aynı zip) | DOCUMENTATION_DERIVED, `wheelhouse_identity_sha256` mekanizmasıyla tutarlı (CODE_VERIFIED: `reports/quality/BYS360_WHEELHOUSE_BUILD_REPORT.json` deterministik SHA256 kimlik alanı içerir) |
| Yazılı runbook seti (`docs/handover/`, kök `DEPLOYMENT.md`/`BACKUP_RUNBOOK.md`) | CODE_VERIFIED (dosyalar mevcut ve bu turda kısmen okunmuştur) |
| Otomatik test paketi (TRUE FULL 5684 passed) | PRODUCTION_HISTORICAL — bkz. DOC-09 |
| CI kalite kapıları (Quality + Score100) | DOCUMENTATION_DERIVED, script dosyaları CODE_VERIFIED mevcut |
| Migration zinciri tek head, tekrarlanabilir (`flask db heads`) | CODE_VERIFIED, bu oturumda fiilen çalıştırıldı |

**Kalan risk:** İş kuralı detayları (ör. performans süreçlerindeki sayısal eşikler, organizasyonel onay zincirinin tüm ayrıntıları) kodun kendisinde her zaman açık biçimde ifade edilmemiştir — önceki devir belgesi bu konuda dürüstçe "repoda açıkça doğrulanmamış hiçbir iş kuralı iddia edilmez" ilkesini benimsemiştir (DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:640,650`). Bu, yeni bir ekibin bazı iş kurallarını yalnızca kod okuyarak değil, mevcut iş sahibiyle (product owner) doğrulayarak tamamlaması gerektiği anlamına gelir — REQUIRES_FINAL_REFRESH / kurumsal bilgi aktarımı gerektirir.

## 3. Yeniden üretilebilir kurulum

- Python 3.12 + `requirements.txt` ile standart `pip install` akışı (CODE_VERIFIED, §4/DOC-07).
- `.env.example` / `.env.docker.example` — değersiz şablonlar, gerçek secret içermez (CODE_VERIFIED).
- `flask db upgrade` ile sıfırdan şema kurulumu — Dosya Merkezi'nin 19 tablosu dahil artık tüm şema Alembic zincirine dahildir (tarihsel bir `db.create_all()` boşluğu `10858a18e9ac_adopt_file_center_schema_into_alembic_` migration'ı ile kapatılmıştır) (DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:863`).
- `python -m compileall app config.py scripts migrations` ile statik derlenebilirlik kontrolü (CODE_VERIFIED, komut `DEPLOYMENT.md` ve `README.md` içinde tutarlı biçimde tekrarlanır).

## 4. Çevrimdışı (offline) dağıtım yaklaşımı

**Somut kanıt bulunmuştur:** `requirements.lock` (kilitli, tam sürümlü bağımlılık listesi) ve `build/wheelhouse/` (59 önceden indirilmiş `.whl` dosyası) bu HEAD'de mevcuttur (CODE_VERIFIED, dosyalar doğrudan listelenmiştir). **Açıklık notu:** `requirements.lock`'ın kendi başlığı bunun güncel HEAD (`873e6d3`) için değil, **eski SHA `ec4e56bd9bab2ce59e9543fc647f55dffd37d94b`** için üretildiğini belirtir. Bunun pratik riski, `git diff ec4e56bd9bab2ce59e9543fc647f55dffd37d94b..HEAD -- requirements.txt` komutunun **boş** dönmesiyle (bu turda ayrıca çalıştırılıp doğrulanmıştır) düşük olarak değerlendirilir — doğrudan bağımlılık dosyası iki SHA arasında bayt-bayt aynıdır. Ancak bu, lock/wheelhouse'un güncel HEAD'e karşı **yeniden üretilip doğrulanmış olduğu** anlamına gelmez; bkz. DOC-16 §3, ledger `DEPENDENCY_LOCK_STATUS`. `reports/quality/BYS360_WHEELHOUSE_BUILD_REPORT.json` (`generated_at: 2026-08-25T14:40:16`, `ok: true`, `wheel_count: 59`, hedef `python_version: 3.12, platform: win_amd64, abi: cp312`, deterministik `wheelhouse_identity_sha256`) bu wheelhouse'un başarıyla üretildiğini gösterir (SCRIPT_VERIFIED, rapor bu oturumda okunmuştur).

Bu, teoride `pip install --no-index --find-links build/wheelhouse -r requirements.lock` ile ağ erişimi olmadan bağımlılık kurulumunun mümkün olduğunu **destekler**. Ancak bu komutun bu HEAD'de fiilen (gerçek bir hedef makinede, sıfır ağ erişimiyle) çalıştırılıp `python -c "from app import create_app; create_app()"` ile doğrulandığına dair bu oturumda kanıt **üretilmemiştir** — `docs/handover/RELEASE_VERIFICATION.md`'nin "DEPENDENCY HANDOVER" kategorisi tam olarak bu koşulu (gerçek offline kurulum denemesi) "acceptable level" için şart koşar. Bu madde **NOT_YET_FINALIZED** olarak işaretlenir.

## 5. Kaynak sahipliği

Tüm kaynak kod kurumun git deposunda, standart açık teknolojilerle (Flask/Python/PostgreSQL/SQLAlchemy/Jinja2) yazılıdır — kapatılmış (proprietary), yalnızca tek bir satıcıya özel bir framework veya lisanslı bileşen bu turda tespit edilmemiştir (CODE_VERIFIED, `requirements.txt` içeriği açık kaynak kütüphanelerden oluşur). Release paketleri `.git/` klasörü içermez; kaynak kimliği manifest/SHA256 ile doğrulanır, tam git geçmişi ayrı bir git remote veya `git bundle` ile teslim edilir (DOCUMENTATION_DERIVED, `docs/handover/HANDOVER_10_10_EVIDENCE_20260708.md:33-35`, `README.md:157`).

## 6. Standart teknolojiler — vendor bağımsızlığı

| Katman | Teknoloji | Bağımsızlık notu |
|---|---|---|
| Backend | Flask 3.1.3 / Python 3.12 | Açık kaynak, geniş ekosistem |
| ORM/Migration | SQLAlchemy 2.0.36 / Flask-Migrate (Alembic) | Standart, PostgreSQL dışına da taşınabilir |
| Veritabanı | PostgreSQL 15 | Açık kaynak, kurulu tabanı geniş |
| Sunucu | Waitress 3.0.1 (WSGI) | Saf Python, herhangi bir WSGI uyumlu ortamda çalışır |
| Kuyruk | Redis + RQ | Açık kaynak; mimari olarak isteğe bağlıdır — CODE_VERIFIED, 5 dosyada doğrudan doğrulandı: `app/core/healthcheck.py`, `async_job_queue.py`, `shared_cache_store.py`, `runtime_cache.py`, `app/security/rate_limit_store.py` (ayrıntı DOC-02 §6) |
| AI sağlayıcı | Varsayılan "stub" (`internal_stub_plus`), dış servise bağımlı değil | CODE_VERIFIED, `config.py:722-724` — bkz. DOC-05 §6 |

Bu teknoloji seçimi, kurumun tek bir bulut sağlayıcısına, tek bir SaaS AI sağlayıcısına veya kapalı bir platforma bağımlı kalmadan sistemi işletebilmesini destekler.

## 7. Veri ve yapılandırma sahipliği

- Uygulama verisi tamamen kurumun kendi PostgreSQL veritabanında tutulur; `.env`, `instance\`, dosya depolama dizinleri (`C:\bys360\storage`, `C:\bys360\local_storage`) kalıcı/uygulama-dışı durum olarak sınıflandırılır ve hiçbir release/candidate işlemi bunları silmez/üzerine yazmaz (DOCUMENTATION_DERIVED, `docs/handover/SECRETS_AND_PERSISTENCE.md:1-19`).
- Yapılandırma (`.env` üzerinden) kurumun kendi kontrolündedir; kaynak kodun kendisinde gerçek secret bulunmaz (CODE_VERIFIED, secret gate 0 finding — bkz. DOC-09 §5).
- KVKK açısından veri, üçüncü taraf bir SaaS'a değil, kurumun kendi altyapısına (Windows Server + PostgreSQL) yerleşiktir.

## 8. Neden nihai bir devredilebilirlik puanı bu belgede yayımlanmıyor

`docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md` §26.1, **farklı ve daha eski bir SHA** (`cb2e57c5d1829ea743c696ae78595a20755f3f07`, 2026-08-24) için hesaplanmış şu tarihsel puanları içerir (DOCUMENTATION_DERIVED, doğrudan okunmuştur):

> `LIVE_READINESS_FINAL=98`, `TRANSFERABILITY_FINAL=95` (governance final, `cb2e57c` özelinde, `BYS360-GOV-CEILING-WAIVER-001` onaylı waiver kararı + o anki taze exact-head Quality+Score100 CI kanıtının birlikte bulunmasına dayalı).

Aynı belge, bu puanın hesaplama mantığının (`waiver_active`, `scripts/quality/bys360_score_reconcile_v1.py:851-861`) **her yeni commit için ayrı ayrı, o commit'in kendi taze exact-head Score100 kanıtını** şart koştuğunu açıkça belirtir — yani bu puan **otomatik olarak sonraki commit'lere miras kalmaz**.

**Bu current-state fazı için önemli sonuçlar:**
1. Yukarıdaki `95/100` (TRANSFERABILITY_FINAL) rakamı, mevcut HEAD (`873e6d3348e644c5384a33a99c517600a3346cfd`) için **geçerli bir güncel puan değildir** — yalnızca **PRIOR/CHECKPOINT** bir tarihsel referans olarak, farklı bir SHA'ya (`cb2e57c`) ait olduğu açıkça belirtilerek anılabilir.
2. `cb2e57c` ile mevcut HEAD arasında (kaynak kod, dokümantasyon-only olmayan commit'ler dahil) değişiklikler olmuş olabilir; bu current-state fazı bu farkı satır satır `git diff --stat` ile ayrıca doğrulamamıştır — NOT_YET_FINALIZED.
3. Bu fazın amacı, Puantaj öncesi bir "current-state" dokümantasyonu üretmektir; final/kapsamlı bir governance skorlama turu değildir.
4. Dolayısıyla bu belge, mevcut HEAD için **yeni bir sayısal devredilebilirlik puanı üretmez veya iddia etmez**. Böyle bir puan, Puantaj entegrasyonu tamamlandıktan, kalan açık teknik madde defteri (`19_...`) kapatıldıktan ve final HEAD için taze exact-head CI kanıtı üretildikten **sonra**, ayrı ve açık bir governance turu ile hesaplanmalıdır (final kapanış sırası için bkz. `19_BYS360_Acik_Teknik_Madde_ve_Finalizasyon_Defteri.md`).

## 9. Test otomasyonu — vendor/kişi bağımsızlığı açısından

Otomatik test paketinin genişliği (TRUE FULL 5684 passed / 4 skipped / 0 failed / 0 errors, PRODUCTION_HISTORICAL — bkz. DOC-09), tek bir geliştiricinin zihinsel modeline değil, çalıştırılabilir/tekrarlanabilir doğrulamaya dayanan bir devir zeminini destekler. Migration testleri (`tests/migrations/`, gerçek Alembic `upgrade()`/`downgrade()` testleri, izole SQLite) migration'ların tekrarlanabilirliğini doğrudan hedefler (DOCUMENTATION_DERIVED, önceki devir belgesi test taksonomisi — bkz. DOC-09 §6).

## 10. Migration tekrarlanabilirliği

Bu oturumda `flask db heads` fiilen çalıştırılmış ve tek head (`v1a2d3e4f5b6`) doğrulanmıştır (TEST_VERIFIED). Bu, migration zincirinin dallanmadığını ve sıfırdan bir ortamda deterministik biçimde uygulanabileceğini gösterir. Boş SQLite üzerinde beklenen, önceden bilinen bir `user_menu_permissions` guard-exception logu görülmüştür — bu savunmacı bir davranıştır, migration defekti değildir (CODE_VERIFIED/TEST_VERIFIED).

## 11. Release doğrulama

SHA256/manifest tabanlı clean-room doğrulama prosedürü mevcuttur (bkz. DOC-05 §13, DOC-07 §3). "Handover-ready" kavramı `docs/handover/RELEASE_VERIFICATION.md` içinde tek bir boolean olarak DEĞİL, sekiz ayrı, kanıta dayalı kategori (Source/Dependency/Database/Operations/Deployment/Rollback/Documentation/Secret Separation) olarak tanımlanmıştır — bu belge de aynı ilkeyi benimser ve bu kategorilerin **her biri için ayrı ayrı kanıt durumu** aşağıda özetlenmiştir.

| Kategori | Bu fazda gözlemlenen kanıt durumu |
|---|---|
| Source Handover | Kısmi — SHA doğrulama mekanizması var (CODE_VERIFIED), ancak §8'deki üç-SHA farkı henüz kapatılmadı |
| Dependency Handover | Kısmi — wheelhouse/lock mevcut (CODE_VERIFIED), gerçek offline kurulum denemesi bu turda yapılmadı (NOT_YET_FINALIZED) |
| Database Handover | Güçlü — tek head migration bu oturumda fiilen doğrulandı (TEST_VERIFIED) |
| Operations Handover | Belgesel — runbook seti mevcut (DOCUMENTATION_DERIVED), bağımsız bir operatör tarafından fiilen denendiğine dair kanıt bu turda aranmadı |
| Deployment Handover | Belgesel — script'ler mevcut (CODE_VERIFIED dosya varlığı), uçtan uca gerçek prova bu turda yapılmadı |
| Rollback Handover | Belgesel — prosedür yazılı, gerçek başarısız-cutover sonrası rollback tatbikatı bu turda yapılmadı |
| Documentation Handover | Bu current-state fazının kendisi bu kategoriyi ilerletmektedir; §13 (DOC-07)'deki SHA tutarsızlığı henüz çözülmedi |
| Secret Separation | Güçlü — secret gate 0 finding bu oturumda çapraz okundu (bkz. DOC-09 §5) |

## 12. Dokümantasyon

Bkz. DOC-07 §12 (dokümantasyon haritası). Bu current-state seti, önceki `docs/handover/` setinin yerini almaz; onu güncel HEAD'e göre yeniden ifade eden, ek bir "puantaj öncesi" katmandır. Kurumsal görsel kimlik ve arayüz standardı da (`20_BYS360_Kurumsal_Tasarim_ve_Arayuz_Standardi.md`) devredilebilirliğin bir parçasıdır — devralan bir ekip, yalnızca kodu değil, kurumun görsel/dil kimliğini de tutarlı biçimde sürdürebilmelidir.

## 13. Operasyonel devir

Adım adım candidate/cutover/rollback prosedürleri `docs/handover/CANDIDATE_PREPARATION.md`, `CUTOVER.md`, `ROLLBACK.md` içinde script-hizalı biçimde yazılmıştır (CODE_VERIFIED, script dosyaları bu HEAD'de mevcuttur; belgelerin script'lerle satır satır uyumu bu turda yeniden doğrulanmadı — DOCUMENTATION_DERIVED).

## 14. Sonuç

BYS360, standart açık teknolojiler, sürüm kontrolü, tekrarlanabilir migration, otomatik test paketi ve yazılı runbook'lar üzerine kurulu bir mimariye sahiptir; bu, kişiye/firmaya bağımlılığı **azaltan** somut, kod düzeyinde doğrulanmış unsurlardır. Ancak nihai bir "devredilebilirlik puanı" veya "final handover-ready" iddiası, (a) Puantaj entegrasyonu tamamlanmadan, (b) mevcut HEAD için taze exact-head CI kanıtı üretilmeden, (c) §8/§11'deki açık maddeler kapatılmadan bu belgede **yapılmamaktadır** — bu, mevcut kanıtların yetersiz olduğu anlamına gelmez, yalnızca bu fazın kapsamının (Puantaj öncesi current-state dokümantasyonu) böyle bir nihai skorlamayı içermediği anlamına gelir.
