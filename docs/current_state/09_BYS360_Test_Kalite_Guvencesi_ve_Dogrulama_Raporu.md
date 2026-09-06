Doküman Adı: BYS360 Test, Kalite Güvencesi ve Doğrulama Raporu
Doküman Türü: Kalite
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası, yerel HEAD değil)
Son Güncelleme: 2026-09-02

---

## 1. Kapsam ve önemli metodolojik uyarı

**Bu belgedeki test/coverage rakamları, önceki bir doğrulama turunda elde edilmiş rakamlardır ve bu current-state incelemesinde yeniden çalıştırılarak üretilmemiştir.** Bu fazın kapsamı tam test paketinin yeniden koşulmasını içermez (coverage kampanyası bu fazın dışındadır). Aşağıdaki sayılar PRODUCTION_HISTORICAL olarak etiketlenmiştir; bu incelemede yalnızca `reports/quality/` altındaki **mevcut** artefaktlarla (bu turda yeniden üretilmemiş, önceden var olan JSON/XML raporlar) **çapraz okuma** yapılmış, tam yeniden ölçüm iddia edilmemiştir.

## 2. LOCAL test sonuçları (önceki doğrulama turundan aktarılan — PRODUCTION_HISTORICAL)

| Adım | Sonuç | Kanıt |
|---|---|---|
| TRUE FULL (tüm pytest kapsamı) | 5684 passed, 4 skipped, 0 failed, 0 errors | PRODUCTION_HISTORICAL — önceki tur |
| Canonical Step 1 (`tests/quality -m "ci_safe"`) | 619 passed, 1 skipped, 0 failed | PRODUCTION_HISTORICAL — önceki tur |
| Canonical Step 2 (geniş entegrasyon/mimari kapsam) | 5065 passed, 3 skipped, 0 failed | PRODUCTION_HISTORICAL — önceki tur |
| Full mypy | PASS, 0 hata | PRODUCTION_HISTORICAL — önceki tur |
| Secret gate | PASS, 0 bulgu | PRODUCTION_HISTORICAL — önceki tur; bkz. §5 çapraz doğrulama |
| Coverage ratchet | PASS | PRODUCTION_HISTORICAL — önceki tur; bkz. §5 çapraz doğrulama |
| Local coverage (combined line+branch) | %36,5722 | PRODUCTION_HISTORICAL — önceki tur; bkz. §5 çapraz doğrulama |
| Coverage baseline (taban, değişmedi) | %27,62 | PRODUCTION_HISTORICAL — önceki tur; bkz. §5 çapraz doğrulama |

## 3. Uzak doğrulanmış kontrol noktası

`7d73ff4d468cad11d78d2339ba770f70b5ec0baf` — uzaktan (remote CI) doğrulanmış tarihsel/mevcut kontrol noktasıdır. **Bu, yerel HEAD (`873e6d3348e644c5384a33a99c517600a3346cfd`) ile birebir aynı değildir.** Önceki devir belgesinde vurgulanan "exact-head kuralı" (bir workflow'un yalnızca "succeeded" görünmesi yetmez, checkout log'undaki SHA doğrulanmak istenen commit ile birebir eşleşmelidir — DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:557-561`) bu iki SHA arasındaki farkı **kapatmaz**: `7d73ff4` için üretilmiş bir CI kanıtı, `873e6d3` için otomatik olarak geçerli sayılamaz. Bu fark açıkça NOT_YET_FINALIZED olarak işaretlenir; final teslim öncesi yeniden, HEAD'e özel taze CI kanıtı üretilmelidir.

## 4. Alembic / migration doğrulaması (bu incelemede fiilen çalıştırılmış)

`FLASK_APP=wsgi.py python -m flask db heads` komutu bu incelemede **fiilen çalıştırılmış** ve tek head döndürmüştür: `v1a2d3e4f5b6 (head)` (CODE_VERIFIED/TEST_VERIFIED — bu, bu fazın teknik doğrulama kayıtlarında da yer almaktadır). Komut ayrıca boş SQLite üzerinde beklenen, önceden bilinen bir `user_menu_permissions` guard-exception logu üretmiştir — bu savunmacı bir davranıştır, migration defekti değildir. `migrations/versions/` altında 77 `.py` dosyası bulunmaktadır (CODE_VERIFIED).

**Not:** Önceki devir belgesi (SHA `cb2e57c`, 2026-08-24) migration dosya sayısını 74 olarak kaydetmiştir (DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:842`). 74→77 farkı, `cb2e57c` ile mevcut HEAD `873e6d3` arasında geçen commit'lerde 3 yeni migration dosyasının eklendiğini gösterir — bu doğal bir ilerleme farkıdır, bir tutarsızlık değildir.

## 5. Bu incelemede yapılan çapraz doğrulama (mevcut rapor artefaktları üzerinden)

Aşağıdaki kontroller, bu incelemede **testleri yeniden çalıştırmadan**, `reports/quality/` altında zaten var olan (bu HEAD'e ait, bu inceleme kapsamında üretilmiş) rapor dosyalarının okunmasıyla yapılmıştır:

- **`reports/quality/BYS360_SECRET_REPO_GATE_V1_REPORT.json`** (`generated_at: 2026-09-02T22:44:02`): `finding_count: 0`, `warning_count: 315` (yalnızca placeholder/referans türü, gerçek bulgu değil), `ok: true`, 3298 dosya tarandı. Bu bulgu, önceki turun "secret gate PASS 0 findings" iddiasını **doğrulamaktadır**.
- **`reports/quality/BYS360_QUALITY9_CI_GATE_REPORT.json`** (`generated_at: 2026-09-01T21:21:53`): `python_files: 973`, `syntax_errors: 0`, `app_print_calls: 0`, `ok: true`. `973` rakamı, önceki bir teknik incelemede kaydedilen `find app -name "*.py" | wc -l = 973` bulgusuyla birebir tutarlıdır.
- **`reports/quality/coverage_baseline.json`**: `combined_pct: 27.62`, `combined_pct_precise: 27.619308622802812` — önceki turun "COVERAGE_BASELINE %27,62 (değişmedi)" iddiasını **birebir doğrular**.
- **`reports/quality/coverage.xml`** (bu inceleme kapsamında üretilmiş, `timestamp` Sep 2 22:12): `lines-valid=101984, lines-covered=41158, branches-valid=29422, branches-covered=6900`. Ratchet script'inin kendi formülüyle (satır+branch birleşik oran) hesaplandığında: `(41158+6900)/(101984+29422) = 48058/131406 ≈ %36,5697` — önceki turun bildirdiği **%36,5722** rakamıyla (küçük yuvarlama farkı dışında) pratik olarak **birebir örtüşmektedir**. Bu, önceki turdaki LOCAL_COVERAGE rakamının bu HEAD için gerçek, tutarlı bir ölçüme dayandığını güçlü biçimde destekler (SCRIPT_VERIFIED cross-read; bu incelemede pytest/coverage yeniden koşulmamış, yalnızca önceden üretilmiş XML artefaktı okunmuştur).

**Sonuç:** Bu fazda incelenen `reports/quality/` artefaktları, önceki turda bildirilen secret-gate, dosya sayısı, coverage baseline ve local coverage rakamlarıyla **çelişmemekte, aksine bunları destekler nitelikte** bulunmuştur. Herhangi bir tutarsızlık tespit edilmemiştir.

## 6. Test felsefesi ve aile taksonomisi (DOCUMENTATION_DERIVED, önceki devir belgesinden — SHA `cb2e57c`, 2026-08-24)

Aşağıdaki tablo önceki devir belgesinden (`docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md` §14) alınmıştır; dosya sayıları `cb2e57c` anına aittir ve bu turda tek tek yeniden sayılmamıştır — yönelim/metodoloji bilgisi olarak güvenilirdir, kesin dosya sayıları için `tests/` dizini bu HEAD'de ayrıca sayılmalıdır (bu incelemede `find tests -name "test_*.py" | wc -l = 384` genel toplamı CODE_VERIFIED olarak doğrulanmıştır).

| Aile | Dizin | Ne test eder |
|---|---|---|
| Unit/static (loose) | `tests/test_*.py` | AST/statik kontroller, route smoke, yardımcı fonksiyon testleri |
| Behavior | `tests/behavior/` | Gerçek servis/model davranışı |
| Security | `tests/security/` | CSP, auth/CAPTCHA/rate-limit, negatif/injection testleri |
| Service | `tests/services/` | Servis katmanı birim testleri (en büyük alt dizinlerden biri) |
| Quality | `tests/quality/` | Kalite-kapısı script'lerinin kendi meta-testleri (secret gate, scoring, debt registry, coverage ratchet) |
| Integration | `tests/integration/` | Gerçek HTTP/DB akış testleri |
| Architecture | `tests/architecture/` | Route mimarisi/refactor-dalga sözleşme testleri |
| Migrations | `tests/migrations/` | Gerçek Alembic `upgrade()`/`downgrade()` testleri, izole SQLite |
| Release | `tests/release/` | Release-paketleme/audit testleri |
| Communication | `tests/communication/` | İletişim route kayıt sözleşmesi (0-import statik kontrol) |
| Mobile | `tests/mobile/` | Mobil domain sözleşmesi |
| Performance | `tests/performance/` | **Performans YÖNETİM MODÜLÜ** testleri (yük/benchmark testi DEĞİL) |
| Critical | `tests/critical/` | Geniş smoke/sözleşme kapıları |
| Load | `tests/load/` | Locust yük testi script'leri — **CI'da çalıştırılmaz**, kapsam dışı |

Bu incelemede `find tests -maxdepth 1 -type d` ile aynı 13 üst dizin adı bu HEAD'de de doğrulanmıştır (CODE_VERIFIED): `architecture, behavior, communication, critical, integration, load, migrations, mobile, performance, quality, release, security, services`.

**Negatif kontroller ilkesi:** Güvenlik testlerinde (host-spoof reddi, CSRF, rate-limit aşımı vb.) sistematik olarak "bu girdi REDDEDİLMELİ" testleri yazılır — yalnızca "olumlu" senaryo test edilmez (DOCUMENTATION_DERIVED).

**Test bypass yasağı ilkesi** (DOCUMENTATION_DERIVED, aynı belge §14): Test asla skip/xfail ile bypass edilerek borç gizlenmez; bir testin false-positive olduğu iddia edilmez, senkron/izole negatif-kontrol fixture'larıyla kanıtlanır; harness düzeltmesi, onu tetikleyen özellik değişikliğinden ayrı bir commit/dalgada yapılır.

## 7. mypy, bağımlılık/güvenlik denetimi

- `pyproject.toml` içinde `[tool.mypy]` bölümü ve çok sayıda modül-özel `[[tool.mypy.overrides]]` bloğu mevcuttur — SQLAlchemy `db.Model` runtime attribute'ları, `conftest.py` çoklu-modül isim çakışması gibi bilinen sınırlamalar için hedefli gevşetmeler içerir (CODE_VERIFIED, dosya doğrudan okunmuştur).
- CI kalite akışında `pip-audit` bağımlılık zafiyeti taraması yer aldığı önceki devir belgesinde belgelenmiştir (DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:551`); bu turda ayrıca yeniden çalıştırılmamıştır.
- "Full mypy PASS 0 errors" iddiası PRODUCTION_HISTORICAL'dır (önceki tur); bu incelemede mypy yeniden koşulmamıştır.

## 8. Coverage ratchet mekanizması — neden salt yüzde yeterli değildir

`scripts/quality/bys360_coverage_ratchet.py` ve `reports/quality/coverage_baseline.json` (CODE_VERIFIED, dosyalar mevcut ve okunmuştur) şu ilkeyi uygular: taban değer (`combined_pct`) **hiçbir script tarafından otomatik yükseltilemez** — yükseltme yalnızca gerçek coverage artışından sonra, insan gözden geçirmesiyle yapılan ayrı bir eylemdir (CODE_VERIFIED, `coverage_baseline.json` içindeki `_comment` alanı). Taban dosyasının `_history` alanı, geçmiş her ölçüm dalgasının (Phase 6 → Phase 9 → 24.16 → 27.62) **gerekçesini, komutlarını ve tekrarlanabilirlik kanıtını** (3 bağımsız çalıştırma, sıfır varyans) kayıt altında tutar — bu, coverage rakamının keyfi/kozmetik biçimde şişirilmediğine dair güçlü bir iç kanıt zinciridir.

**Coverage yüzdesi neden tek başına kalite ölçütü değildir:**
1. Coverage, bir satırın **çalıştırıldığını** gösterir, o satırın **doğru davrandığını** göstermez — assertion'sız veya zayıf assertion'lı bir test %100 satır coverage'ı ile birlikte hiçbir gerçek hata yakalamayabilir.
2. BYS360'da coverage kasıtlı olarak dar bir CI kapsamına (`--cov=app`, belirli test dizinleri) göre ölçülür; bu, "kapsam dışı" hiçbir kodun test edilmediği anlamına gelmez, yalnızca bu spesifik metriğin o kapsamı yansıttığı anlamına gelir.
3. Negatif kontroller (§6), mimari sözleşme testleri (`tests/architecture/`) ve migration testleri (`tests/migrations/`) gibi test aileleri, coverage yüzdesine katkısı düşük olsa bile (bazıları saf statik/AST kontrolüdür, hiç `app.*` import etmez) kritik regresyon koruması sağlar — coverage yüzdesi bunların değerini yakalamaz.
4. Coverage ratchet'in kendisi "gate" olarak yalnızca **düşüşü** engeller; mevcut düşük taban (%27,62) yüksek bir kalite hedefi olarak sunulmamalıdır — bu, gerçek/dürüst bir taban olarak kayıtlıdır, aspirasyonel değildir (CODE_VERIFIED, `coverage_baseline.json` `_comment`: "This value is NOT aspirational").

## 9. Tarihsel/yeniden inşa edilemeyen kanıt politikası

Bazı geçmiş governance/skor kararları (ör. `BYS360-GOV-CEILING-WAIVER-001`, `BYS360-GOV-LEGACY-001`), belirli bir SHA'ya (`cb2e57c`) özel, o anki taze exact-head CI kanıtına bağlı olarak hesaplanmıştır ve **her yeni commit için otomatik miras alınmaz** — hesaplama mantığı (`waiver_active`), skorlanan commit'in **kendi** taze exact-head Score100 kanıtını ayrıca şart koşar (DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:900-917`). Bu current-state fazı için böyle bir taze governance skoru **üretilmemiştir** ve üretilmesi bu fazın kapsamı dışındadır. Dolayısıyla mevcut HEAD (`873e6d3`) için LIVE_READINESS/TRANSFERABILITY gibi puanlar bu belgede **iddia edilmez**; bunlar yalnızca eski, farklı bir SHA'ya ait tarihsel/kontrol-noktası bilgisi olarak DOC-08'de ayrıca referanslanır.

## 10. Sınırlamalar

- Bu belgedeki test sayıları bu incelemede **yeniden yürütülmemiştir**; önceki tur rakamlarına ve mevcut rapor artefaktlarının çapraz okumasına dayanır.
- `tests/` içindeki alt dizin bazlı kesin dosya sayıları (§6 tablosu) `cb2e57c` anına aittir; bu HEAD için tek tek yeniden sayılmamıştır (yalnız toplam `test_*.py` dosya sayısı = 384 bu turda doğrulanmıştır).
- Mobil/PWA'ya özgü test kapsamı bu turda ayrıca değerlendirilmedi — NOT_YET_FINALIZED.
- Uzak CI kontrol noktası (`7d73ff4`) ile yerel HEAD (`873e6d3`) arasındaki fark, exact-head kuralına göre henüz kapatılmamıştır (bkz. §3) — final teslim öncesi zorunlu.
