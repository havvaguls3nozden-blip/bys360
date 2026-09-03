Doküman Adı: BYS360 Teknik Devir Teslim ve Sürdürülebilirlik Raporu
Doküman Türü: Devir
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası, yerel HEAD değil)
Son Güncelleme: 2026-09-02

---

## 1. Temel soru: BYS360'ı başka bir ekip devralabilir mi?

**Kısa cevap:** Evet, kod tabanı, test otomasyonu, release/rollback disiplini ve mevcut `docs/handover/` operatör belgeleri bir devir için **yeterli teknik temeli** sağlıyor; ancak bu, tek bir "hazır/final" iddiası olarak sunulmamalıdır. `docs/handover/RELEASE_VERIFICATION.md` içindeki "Devredilebilirlik Gate" rubriği (8 kategori: Source/Dependency/Database/Operations/Deployment/Rollback/Documentation/Secret Separation), skorlamanın **kanıta dayalı ve kategori bazlı** yapılmasını, tek bir toplam sayı olarak iddia edilmemesini şart koşar (DOCUMENTATION_DERIVED, `docs/handover/RELEASE_VERIFICATION.md:116-247`) — bu ilke bu belgede de takip edilmiştir. Bilinen açık teknik maddelerin tam envanteri ayrı bir belgede (`19_BYS360_Acik_Teknik_Madde_ve_Finalizasyon_Defteri.md`, koordinatör tarafından yazılıyor) tutulacaktır; bu rapor yalnızca o defterin varlığına ve rolüne atıfta bulunur, içeriğini tekrarlamaz.

## 2. Repo organizasyonu

- Tek repo, `app/` altında 973 Python dosyası (CODE_VERIFIED — bu fazın koordinatör olgu defterinde de kayıtlı).
- Üst düzey modül dizinleri: `about, account, admin, ai, ai_agent, api, assistant_training_bank, auth, communication, core, dashboard, executive_summary, file_center, institutional, main_handlers, modules, performance, portal, pwa, refactor, ...` (CODE_VERIFIED, `ls app`).
- `migrations/versions/` altında 77 Alembic migration dosyası, tek head zinciri (CODE_VERIFIED — bkz. DOC-09 §4).
- `tests/` altında 384 `test_*.py` dosyası, 13 üst-düzey test ailesi dizini (CODE_VERIFIED — bkz. DOC-09 §6).
- `scripts/` altında release/quality/windows/security gibi operasyonel script aileleri; `scripts/release/build_bys360_safe_release.py` tek yetkili (canonical) release builder'dır — Git-tracked dosyalardan üretir, dosya sistemine fallback yapmaz, çalışma ağacı temiz değilse başarısız olur (fail-closed) (CODE_VERIFIED, `README.md:111-117`).
- `build/wheelhouse/` — offline pip kurulumu için önceden indirilmiş wheel dosyaları (59 wheel, `reports/quality/BYS360_WHEELHOUSE_BUILD_REPORT.json`: `ok: true`, deterministik SHA256 kimlik özeti) (CODE_VERIFIED/SCRIPT_VERIFIED, dosyalar mevcut ve rapor bu oturumda okunmuştur). **Açıklık notu (peer-review, Agent 2 bulgusu):** bu wheelhouse ve eşlik eden `requirements.lock`, kendi başlığına göre güncel HEAD (`873e6d3`) için değil, eski SHA `ec4e56bd9bab2ce59e9543fc647f55dffd37d94b` için üretilmiştir. `requirements.txt` iki SHA arasında bayt-bayt aynı olduğundan (`git diff` ile doğrulandı) pratik risk düşüktür, ancak lock/wheelhouse güncel HEAD'e karşı yeniden üretilip doğrulanmamıştır — bkz. DOC-16 §3.

## 3. Branch/release disiplini

- Mevcut çalışma dalı: `phase5-critical-lint-clean-v1`, HEAD `873e6d3348e644c5384a33a99c517600a3346cfd` (CODE_VERIFIED, `git branch --show-current` + `git rev-parse HEAD`).
- **Exact-head kuralı:** Bir CI workflow'unun "succeeded" görünmesi tek başına yeterli değildir; checkout log'undaki gerçek SHA, doğrulanmak istenen commit ile birebir eşleşmelidir (DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:557-561`). Bu current-state fazı için, yerel HEAD (`873e6d3`) ile uzak doğrulanmış kontrol noktası (`7d73ff4`) **farklıdır** — bu fark açıkça belirtilir; final teslim öncesi HEAD'e özel taze CI kanıtı gereklidir (NOT_YET_FINALIZED).
- Release paketleri üç birlikte üretilen artefaktla teslim edilir: `.zip`, `.manifest.json` (schema_version 2), `.sha256sums.txt` — ayrıntı DOC-05 §13'te.
- Rollback modeli **iki nesil script** içerir (peer-review/Agent 2 netleştirmesi: bu, DOC-06/DOC-14'teki "migration-öncesi/migration-sonrası iki rollback yolu" ayrımından **farklı** bir "iki"dir — burada nesil/script kuşağı kastedilmektedir, karıştırılmamalıdır): yeni "candidate/cutover/rollback" script üçlüsü (`prepare_bys360_candidate.ps1`, `cutover_bys360_candidate.ps1`, `rollback_bys360_candidate.ps1`, canlıya dokunmadan aday hazırlama) ve eski/tekil model (`rollback_bys360_live_release_v1.ps1`, dry-run varsayılan) (CODE_VERIFIED, dosyalar bu HEAD'de mevcuttur).

## 4. Ortam gereksinimleri

| Bileşen | Sürüm | Kanıt |
|---|---|---|
| Python | 3.12 (pin) | CODE_VERIFIED (`pyproject.toml`, `README.md`) |
| Flask | 3.1.3 | CODE_VERIFIED (`requirements.txt`) |
| PostgreSQL | 15 (canlı) | CODE_VERIFIED/DOCUMENTATION_DERIVED |
| SQLite | local geliştirme/test varsayılanı | CODE_VERIFIED |
| Redis + RQ | arka plan iş kuyruğu | CODE_VERIFIED (`requirements.txt`: redis 5.0.8, rq 2.3.3) |
| Waitress | 3.0.1, production/staging WSGI sunucusu | CODE_VERIFIED |
| İşletim sistemi (canlı) | Windows, Scheduled Task ile süreç yönetimi | CODE_VERIFIED/SCRIPT_VERIFIED |
| PowerShell | 5+ veya 7+ | DOCUMENTATION_DERIVED (`DEPLOYMENT.md:19`) |

**Önemli varsayılan davranış uyarısı (CODE_VERIFIED çıkarım, `DEPLOYMENT.md:194-202` ile tutarlı):** `DATABASE_URL` ortam değişkeni açıkça ayarlanmazsa uygulama bellek-içi (kalıcı olmayan) SQLite'a düşer — yeni bir operatör bunu bilmeden her yeniden başlatmada veri kaybedebilir.

## 5. Build / çalıştırma / test komutları (copy/paste, gerçek repo dosyalarından)

```powershell
# Kurulum
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt   # yalnız geliştirme/test için
copy .env.example .env

# Veritabanı
flask db upgrade

# Çalıştırma (yerel)
python run.py
# Çalıştırma (operasyonel, prod/staging'de Waitress'e geçer)
python run_server.py

# Kalite kapıları (CI ile birebir)
python scripts\quality\bys360_secret_repo_gate.py --root .
python -m ruff check app config.py wsgi.py run.py scripts tests
python -m mypy app tests scripts --ignore-missing-imports --no-error-summary
python -m pytest tests/quality -m "ci_safe" --cov=app --cov-report= --cov-fail-under=0 --tb=short -q   # Step1
# Step2 — tam komut .github/workflows/bys360-ci.yml dosyasındadır, ELLE yeniden yazılmamalıdır
```
(DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:183-243`, `README.md`, `DEPLOYMENT.md` — üç dosyada tutarlı biçimde tekrarlanmıştır; bu turda dosyaların varlığı ve komutların dosya içeriğiyle örtüştüğü CODE_VERIFIED'dır.)

**`run.py` / `run_server.py` / `wsgi.py` karıştırılmamalıdır:**

| Dosya | Amaç | Waitress kullanır mı |
|---|---|---|
| `run.py` | Sade geliştirme girişi | Hayır |
| `run_server.py` | Gerçek operasyonel giriş; `APP_ENV` production/staging ise Waitress'e geçer | Evet (yalnız prod/staging'de) |
| `wsgi.py` | Harici WSGI sunucuları için (`application = create_app()`) | Hayır (kendisi başlatmaz) |

(DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:211-217`)

## 6. Kalite kapıları

İki ayrı GitHub Actions workflow'u (DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:545-561`, bu HEAD'de dosya varlığı ayrıca doğrulanmalı):
- **Quality** (`bys360-ci.yml`): secret/repo gate → safe-release audit → Ruff → compileall → Step1 → Step2 → gerçek PostgreSQL migration-integrity gate → coverage ratchet → mypy → operations audit → Quality9 CI contract gate → `pip-audit`.
- **Score100** (`bys360-score100-quality-gate-v1.yml`): bağımlılık pinleme, git-tracked `.env` kontrolü, secret pattern taraması, TCKN şifreleme varlığı, duplicate endpoint/test skip, wildcard import, broad except, repo şekli kontrolleri.

Bu fazda çapraz okunan mevcut rapor artefaktları (secret gate 0 finding, 973 dosya, coverage baseline %27,62) brifing rakamlarıyla tutarlıdır — ayrıntı DOC-09 §5.

## 7. Migration yönetimi

Flask-Migrate/Alembic, **tek zincir** (CODE_VERIFIED). Bu oturumda `flask db heads` fiilen çalıştırılmış, tek head (`v1a2d3e4f5b6`) doğrulanmıştır. Migration öncesi zorunlu DB yedeği (`BACKUP_RUNBOOK.md`), staging'de deneme, canlı görev durdur → kod aktar → migration uygula → görev başlat sırası (`DEPLOYMENT.md:64-76`) belgelenmiştir (DOCUMENTATION_DERIVED). Şema-adopt senaryosu için özel bir migration örneği (`10858a18e9ac_adopt_file_center_schema_into_alembic_`) mevcut olup, fail-closed davranış (beklenmeyen şema durumunda migration'ın sessizce kabul etmek yerine açık hata ile durması) önceki devir belgesinde belgelenmiştir (DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:863`).

## 8. Yapılandırma modeli

- `.env` dosyası `config.py`'nin `DOTENV_PATH`'i üzerinden okunur; `load_dotenv(..., override=False)` — önceden ayarlanmış OS-seviyesi ortam değişkenleri her zaman `.env`'e üstün gelir (DOCUMENTATION_DERIVED, `docs/handover/SECRETS_AND_PERSISTENCE.md:48-50`).
- `.env.example` / `.env.docker.example` — değer içermeyen, yalnızca değişken adı/örnek şablonlar; release paketine girmesine izin verilen tek iki `.env*` dosyasıdır (DOCUMENTATION_DERIVED, aynı belge §10,28-31).
- `SECRET_KEY` doğrulaması production/staging'de zorunludur (bkz. DOC-05 §11).

## 9. Sır (secret) sınırı

`.env`, `instance\`, `C:\bys360\storage`, `C:\bys360\local_storage` ve PostgreSQL veritabanının kendisi **kalıcı, uygulama-dışı durum** olarak sınıflandırılır ve hiçbir candidate build/cutover/rollback tarafından üzerine yazılmaz/yeniden oluşturulmaz/silinmez. Bunun dışındaki her şey (`app/`, `migrations/`, `requirements.txt`, `wsgi.py`, `run_server.py`, `config.py`, `DEPLOYMENT.md`, şablonlar, statik varlıklar) kaynaktan tamamen yeniden üretilebilir uygulama kaynağıdır (DOCUMENTATION_DERIVED, `docs/handover/SECRETS_AND_PERSISTENCE.md:1-19`). Ayrıntı DOC-05 §11.

## 10. Deployment modeli

Windows Scheduled Task (`BYS360 Live Waitress 80`) + Waitress WSGI (CODE_VERIFIED, `requirements.txt`: waitress; SCRIPT_VERIFIED, `scripts/windows/install_bys360_live_waitress_80_task_v1.ps1:40`). Canlıya alma adım sırası (`DEPLOYMENT.md` §6): temiz branch → compileall → kritik testler → DB yedeği → dosya yedeği → migration staging denemesi → görev durdur → kod aktar → migration uygula → görev başlat → `/login`/`/healthz`/kritik ekran kontrolü.

Ayrıca yeni bir "candidate/cutover" modeli mevcuttur (`docs/handover/CANDIDATE_PREPARATION.md`, `CUTOVER.md`): canlıya hiç dokunmadan aday hazırlama, ardından kısa/sınırlı bir cutover penceresi (SCRIPT_VERIFIED, script dosyaları bu HEAD'de mevcuttur).

## 11. Rollback modeli

5xx/beyaz sayfa/migration hatası/yetki bozulması durumunda: görev durdur → son çalışan kod yedeğini geri al → gerekirse DB yedeğini restore et → görev başlat → `/login`, `/healthz`, performans ana ekranı, mesaj/anket ekranları kontrol et (`DEPLOYMENT.md:143-153`). Ayrıntılı prosedür `BACKUP_RUNBOOK.md`'dedir. Rollback güvenliği "her zaman güvenlidir" biçiminde blanket bir iddia olarak sunulmamalı; her release için ayrı, gerçek bir kaynak-diff ile değerlendirilmelidir (DOCUMENTATION_DERIVED, `docs/handover/RELEASE_VERIFICATION.md` §6 "ROLLBACK HANDOVER" rubriği).

## 12. Dokümantasyon haritası

**Bu fazda (`docs/current_state/`) üretilen/üretilecek set:**
- `BYS360_CURRENT_STATE_FACTS.md` — kanonik olgu defteri (koordinatör).
- `05_...Guvenlik_Yetkilendirme_KVKK_ve_Denetim.md` (bu ajan).
- `07_...Teknik_Devir_Teslim_ve_Surdurulebilirlik_Raporu.md` (bu belge).
- `08_...Devredilebilirlik_ve_Kurumsal_Bagimsizlik_Dokumani.md` (bu ajan).
- `09_...Test_Kalite_Guvencesi_ve_Dogrulama_Raporu.md` (bu ajan).
- `11_...Rol_Yetki_ve_Erisim_Kontrol_Modeli.md` (bu ajan).
- `19_BYS360_Acik_Teknik_Madde_ve_Finalizasyon_Defteri.md` — **koordinatör tarafından yazılıyor**, bilinen açık teknik/LOW/DRIFT/operasyon maddelerinin detaylı ledger'ı (AL ailesi, Dashboard LOW, M drift, mobil fail-open/drift, Dosya Merkezi izin/audit/rollback maddeleri, PT72H/RestartCount/AllowHardTerminate sertleştirme, PostgreSQL ROUND uyarısı vb.). Bu rapor o defterin **varlığını ve rolünü kabul eder**, içeriğini tekrarlamaz.
- Diğer ajanların (Agent 1, Agent 2) ürettiği paralel current-state belgeleri (modül envanteri, operasyon/deployment detayı vb.) — bu oturumda içerikleri okunmadı, yalnızca varlıkları biliniyor.
- `20_BYS360_Kurumsal_Tasarim_ve_Arayuz_Standardi.md` — **koordinatör tarafından eklendi (dokümantasyon sertleştirme fazı)**: BYS360'ın kurumsal görsel kimliği ve arayüz standardı; bir devralan ekibin kod düzeyinde tutarlı bir görsel dil sürdürebilmesi için gereken referanstır.

**Operasyonel temel olarak `docs/handover/` seti:**
- `BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md` — en kapsamlı tekil kaynak (~4400 satır, 39+ bölüm), ancak **SHA `cb2e57c5d1829ea743c696ae78595a20755f3f07`'ye ait** (2026-08-24), mevcut HEAD (`873e6d3`) ile **birebir aynı değildir**. `docs/handover/README.md` bu dosyayı "CURRENT" olarak işaretler ve `BYS360_GUVENLIK_KVKK_NOTLARI.md`, `BYS360_RISK_VE_SUREKLILIK_PLANI.md`, `BYS360_MODUL_ENVANTERI.md`, `BYS360_BAKIM_RUNBOOK.md`, `BYS360_KURULUM_REHBERI.md`, `BYS360_CANLIYA_ALMA_REHBERI.md`, `BYS360_DEVIR_PAKETI_V1.md` dosyalarını "SUPERSEDED" (2026-06-24) olarak işaretler — bkz. §13 "Belge SHA tutarsızlığı".
- `BYS360_FEATURE_COVERAGE_MATRIX.md` — repo-türetilmiş özellik envanteri (38 özellik), aynı `cb2e57c` SHA'sına ait.
- `CANDIDATE_PREPARATION.md`, `CUTOVER.md`, `ROLLBACK.md`, `DATABASE_MIGRATION.md`, `DISASTER_RECOVERY.md`, `RELEASE_VERIFICATION.md`, `SECRETS_AND_PERSISTENCE.md` — script-hizalı operatör runbook'ları, `cb2e57c`'den bağımsız/daha kalıcı bir spesifikasyon seviyesinde yazılmış (script isimleri/davranışı bu HEAD'de de doğrulanmıştır).
- Kök dizin: `DEPLOYMENT.md`, `BACKUP_RUNBOOK.md`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md` — bu turda doğrudan okunmuş, komutları bu HEAD'de dosya içeriğiyle örtüşür bulunmuştur (CODE_VERIFIED).

## 13. Belge SHA tutarsızlığı — açıkça raporlanan bulgu

Üç farklı SHA aynı anda "güncel/aktif" olarak dolaşımdadır:

| SHA | Kaynak | Tarih |
|---|---|---|
| `873e6d3348e644c5384a33a99c517600a3346cfd` | Bu current-state fazının yerel HEAD'i | 2026-09-02 |
| `7d73ff4d468cad11d78d2339ba770f70b5ec0baf` | Bu fazın brifinginde verilen "uzak doğrulanmış kontrol noktası" | belirtilmedi |
| `cb2e57c5d1829ea743c696ae78595a20755f3f07` | `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md` ve `BYS360_FEATURE_COVERAGE_MATRIX.md`'nin "Production SHA"sı; `docs/handover/README.md`'nin de referans aldığı SHA | 2026-08-24 |

Bu, üç ayrı belge dalgasının farklı zamanlarda üretildiğinin doğal bir sonucudur, ancak yeni bir operatör için kafa karıştırıcı olabilir. **Öneri:** final dokümantasyon yenileme aşamasında, kanonik "aktif SHA" tek bir belgede (örn. güncellenmiş `docs/handover/README.md`) açıkça belirtilmeli ve diğer tüm belgeler bu tek kaynağa referans vermelidir.

## 14. Operasyonel sahiplik ve bilgi aktarım gereksinimleri

- Sistem şu anda tek geliştirici bilgisine dayanıyor gibi görünmektedir (Bus Factor riski) — ayrıntılı azaltım DOC-08'de ele alınır.
- Yeni bir operatörün ilk gün yapması gerekenler (DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md` §23 "New Developer First Day"): repo clone, local kurulum, `flask db heads` ile migration zincirini doğrulama, kalite kapılarını yerel çalıştırma, `/healthz` kontrolü — bu turda §23'ün tam içeriği satır satır okunmadı, yalnız başlığı ve komut setinin §4'te zaten karşılığı bulunduğu doğrulandı (REQUIRES_FINAL_REFRESH: §23'ün tam metni final yenilemede ayrıca okunmalı).
- 30/60/90 gün bakım planı önceki devir belgesinde ayrı bir bölüm olarak mevcuttur (§24) — bu turda içerik olarak okunmadı, NOT_YET_FINALIZED.

## 15. Değişiklik prosedürü ve bakım sorumlulukları

Önceki devir belgesinin özetlediği disiplin (DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:83`): odaklı testler → tam kalite kapıları (Step1+Step2) → commit → push → exact-head CI doğrulaması → deterministik paket üretimi → kontrollü deployment → canlı kullanıcı kabulü. Bu current-state fazı bu döngüye müdahale etmemiş, yalnızca dokümantasyon üretmiştir (kaynak kod değişikliği yapılmamıştır — bkz. `git status`, CODE_VERIFIED).

## 16. Bilinen açık teknik madde ledger'ı — atıf

Detaylı açık teknik/LOW/DRIFT/operasyon madde listesi bu raporun kapsamı dışındadır; `19_BYS360_Acik_Teknik_Madde_ve_Finalizasyon_Defteri.md` (koordinatör) bu işlevi görecektir. Bu rapor yalnızca aşağıdaki, bu ajan tarafından bu turda **yeni tespit edilen** maddeleri işaretler — bunların ledger'a dahil edilmesi koordinatörün kararındadır:

- `/admin/role-matrix` salt-okunur ekranı ile canlı DB yetki durumu arasındaki drift riski (bkz. DOC-11 §7).
- Audit log kapsamının (yalnız Dosya Merkezi + Performans delegasyon/dönem/geri bildirim akışları + bootstrap güvenlik olayları) blanket bir "her state-change audit'lenir" iddiasından daha dar olduğu (bkz. DOC-05 §8).
- Belge SHA tutarsızlığı (bkz. §13).

## 17. Sonuç

Kod tabanı; sürüm kontrolü, otomatik test paketi (brifing rakamlarıyla binlerce test), CI kalite kapıları (Ruff/mypy/secret-gate/coverage-ratchet), deterministik release paketleri (SHA256 doğrulanabilir) ve yazılı runbook'lara dayanıyor. Bu, bir devrin **teknik olarak mümkün** olduğunu gösterir. Ancak "handover-ready" tek bir onaylanmış boolean olarak iddia edilmemelidir (`docs/handover/RELEASE_VERIFICATION.md` §5) — her kategori kendi kanıtıyla ayrı değerlendirilmeli, mevcut HEAD için taze exact-head CI kanıtı ve §13'teki SHA tutarsızlığının çözümü final teslimin ön koşuludur.
