# BYS360 — Nihai Devir ve Sürdürülebilirlik Ana Dosyası

```
Document Status: CANONICAL
Production Source SHA: cb2e57c5d1829ea743c696ae78595a20755f3f07
Production Package: BYS360_FULL_LIVE_cb2e57c.zip
Package SHA256: 895dc9d57021a0107682edb06fd2b99e2f6d17d1d7e6db97fcf6edb9274c476c
Package File Count: 2136
Database Revision: e0efcd07abf7 (single head, independently verified against migrations/versions/*.py — 74 migration files, no branch points)
Last Production Validation: 2026-08-24
Handover Status: READY
```

**Bu belge kimdir için yazıldı:** Bu dosyayı ve repository'yi teslim alan yeni bir profesyonel geliştirici, sistem yöneticisi veya dış firma — bu sohbete, önceki geliştiriciye, ya da başka bir AI asistanına erişimi olmadan — BYS360'ı anlayabilmeli, kurabilmeli, test edebilmeli, geliştirebilmeli, release üretebilmeli, canlıya güvenli şekilde deploy edebilmeli ve bir sonraki kişiye devredebilmelidir.

**Kanıt disiplini notu (bu belgenin kendi metodolojisi):** Bu belgedeki her iddia iki kategoriden birine aittir ve açıkça öyle işaretlenmiştir:
- **REPO-VERIFIED** — repository kaynak kodu, git geçmişi, migration zinciri veya bu devir dalgası sırasında gerçekten çalıştırılan komutlardan doğrudan doğrulanmış.
- **OPERATOR-ATTESTED** — canlı sunucuya (RDP, PowerShell, DB, dosya sistemi) bu dokümantasyon oturumunun hiçbir zaman erişimi olmadığı için, yalnızca sistemi işleten operatörün sağladığı kanıt/beyan olarak kaydedilmiş. Bu dokümantasyon oturumu üretim ortamına doğrudan erişmedi ve erişmeyecek.

Bu ayrım, belgenin geri kalanında tutarlı şekilde korunmuştur.

---

## 0. Üretim Durumu — Provenance ile

**Verification provenance:** Production deployment of `cb2e57c` was completed and validated on 2026-08-24 based on operator-supplied production deployment logs and live user-acceptance evidence. The documentation-generation session itself did not have direct RDP or production access.

| Alan | Değer | Kaynak |
|---|---|---|
| Deployment token | `PASS_BYS360_CB2E57C_CLEAN_PRODUCTION_DEPLOYMENT` | OPERATOR-ATTESTED |
| Production state | `BYS360_PRODUCTION=UPDATED` | OPERATOR-ATTESTED |
| Active source SHA | `cb2e57c5d1829ea743c696ae78595a20755f3f07` | OPERATOR-ATTESTED (deployment) + REPO-VERIFIED (SHA exists, is the pushed HEAD of `phase5-critical-lint-clean-v1`, and passed exact-head Quality + Score100 CI — see §13) |
| Active package | `BYS360_FULL_LIVE_cb2e57c.zip`, SHA256 `895dc9d57021a0107682edb06fd2b99e2f6d17d1d7e6db97fcf6edb9274c476c`, 2136 dosya | REPO-VERIFIED (built by this session's canonical builder, independently SHA256-verified, deterministic Build #2 byte-identical) |
| Database | PostgreSQL 15, revizyon `e0efcd07abf7`, migration NOT_REQUIRED | Revizyon numarası REPO-VERIFIED (migration zinciri tek head, dallanma yok); "canlıda bu revizyonda çalışıyor" kısmı OPERATOR-ATTESTED |
| Service / Local health / Public health | PASS / 200 / 200 | OPERATOR-ATTESTED |
| Smoke / Security critical / New critical errors | PASS / 0 / 0 | OPERATOR-ATTESTED |
| UTF-8 Windows startup | PASS | OPERATOR-ATTESTED (canlı davranış); mekanizmanın kendisi REPO-VERIFIED (bkz. §7) |
| Live task | `BYS360 Live Waitress 80`, Running | OPERATOR-ATTESTED |
| Portal external video acceptance | PASS — canlı Portal composer'da Fotoğraf ekle / Video dosyası / Video bağlantısı üçü de görünür, video-link alanı operatör tarafından manuel test edildi | OPERATOR-ATTESTED (canlı); kök neden ve CSS düzeltmesi REPO-VERIFIED (bkz. §16) |

**Bu dokümantasyon oturumunun kendi doğrudan doğruladığı en son durum** (RDP olmadan, yalnız repo/CI kanıtıyla): `cb2e57c` HEAD'i `origin/phase5-critical-lint-clean-v1`'e push edilmiş, `git ls-remote` ile teyit edilmiş; aynı exact-head SHA için Quality ve Score100 GitHub Actions workflow'ları operatör tarafından sağlanan taze ekran görüntülerinde `succeeded` durumda ve Checkout log satırında `cb2e57c5d1829ea743c696ae78595a20755f3f07` görünüyor; `BYS360_FULL_LIVE_cb2e57c.zip` bu oturumda üretilip clean-room extract ile doğrulanmış. Bunun ötesindeki (gerçek sunucuya kurulum, canlı health, canlı kullanıcı ekranı) her şey operatör beyanıdır.

---

## 1. Executive Summary (Teknik Olmayan Yönetici İçin)

**BYS360 nedir:** Bir Türk kamu kurumu (T.C. Kültür ve Turizm Bakanlığı'na bağlı; `.env.example` varsayılan e-posta alan adı `ktb.gov.tr`) için geliştirilmiş, kurumsal bir personel/performans/iletişim yönetim platformudur.

**Ne çözer:** Tek bir web uygulamasında şunları bir araya getirir — personel/İK kayıtları ve izin/devam yönetimi, performans değerlendirme süreçleri (amir onay zincirleri dahil), kurum içi sosyal "Portal" (paylaşım/duyuru/yorum), anketler, destek/talep (helpdesk), iç iletişim/bildirim, karar-destek amaçlı yapay zekâ panelleri, sanal asistan sohbet arayüzü, dosya merkezi (güvenli dosya paylaşımı), ve bir yönetim panosu (dashboard).

**Hangi modülleri var:** Personel/İK, Performans, Portal, Anketler, İletişim, Destek, Ayarlar/Yetki Matrisi, Dosya Merkezi, Yönetim Panosu, AI Karar Destek, Sanal Asistan. Her birinin ayrıntısı §2'de.

**Kuruma ne kazandırır:** Dağınık Excel/e-posta/kağıt süreçlerini tek, denetlenebilir (audit-logged), rol-tabanlı yetkilendirmeli bir sisteme taşır; performans değerlendirme sürecini (amir görüşü → üst amir → Başkan onayı) sistematik ve izlenebilir hale getirir; KVKK'ya duyarlı veri erişim sınırları uygular (bkz. §15).

**Neden devredilebilir:** Sistem tek bir kişinin hafızasına değil — sürüm kontrolüne (git), otomatik testlere (4000+ test), CI kalite kapılarına (Ruff/mypy/secret-gate/Step1/Step2/Score100), deterministik release paketlerine (SHA256 doğrulanabilir), ve bu belge dahil yazılı runbook'lara dayanır. Ayrıntılı kanıt için bkz. §25 "Bus Factor".

**Neden sürdürülebilir:** Her değişiklik dalgası aynı disiplinle ilerler — odaklı testler → tam kalite kapıları (Step1 + Step2, 4000+ test) → commit → push → exact-head CI doğrulaması → deterministik paket üretimi → kontrollü deployment → canlı kullanıcı kabulü. Bu belge bu döngünün her adımını §21'de anlatır.

---

## 2. Sistem Mimarisi

**Kaynak:** Flask 3.1.3 / Python 3.12 backend, Jinja2 şablonlar, PostgreSQL 15 (canlı) / SQLite (local dev), SQLAlchemy 2.0 ORM, Flask-Migrate/Alembic migration, Flask-Login + rol-tabanlı yetkilendirme, Flask-WTF CSRF, özel CSP (Content-Security-Policy) katmanı, Waitress WSGI sunucusu (canlı), Windows Scheduled Task ile process yönetimi.

Kimlik doğrulama, yetkilendirme, dosya depolama, arka plan işleri, mail gibi ortak altyapı bileşenleri aşağıda; ardından iş modülleri tablo halinde.

### Ortak altyapı

| Bileşen | Nerede | Not |
|---|---|---|
| **Authentication** | `app/auth/routes.py` → `app/main_handlers/auth_handlers.py` (`login`, `forgot_password`, `logout`, `setup_admin`) | Web login IP+kimlik bazlı throttle + CAPTCHA (`get_auth_throttle_state`/`record_auth_failure`); mobil login (`/api/mobile/auth/login`) için ayrı bir throttle YOK, yalnız genel Flask-Limiter varsayılanına (200/dk) tabi — bilinen, kabul edilmiş bir risk (STATUS.md Faz 2B). |
| **Authorization** | `app/route_support.py` | Rol aileleri: `ADMIN_FAMILY_ROLES = {admin, baskan, baskan_yardimcisi, grup_baskani, mali_musavir}`, `MANAGER_FAMILY_ROLES = ADMIN_FAMILY_ROLES ∪ {birim_sorumlusu, koordinator}`. Ana guard: `menu_key_required(menu_key)` → `app.services.settings.effective_menu.build_menu_visibility_map(user)`'a bakar. **Admin bypass'i kaldırılmıştır** — admin dahil herkes canlı menü görünürlük haritasına tabidir (kod içi not: `BYS360_SETTINGS_LIVE_AUTHORITY_V2`). |
| **CSRF** | `app/extensions.py` (`csrf = CSRFProtect()`), özel PWA/iOS oturum-yenileme hata işleyicisi `app/__init__.py` içinde | — |
| **CSP** | `app/security/headers.py` (`build_csp_header`, `DEFAULT_CSP`), env üzerinden `config.py:685-704` | P0 hedefi: script-src için varsayılan `unsafe-inline` YOK; nonce inline/harici `<script>`/`<style>` etiketlerine uygulanır. |
| **Rate limiting** | `app/security/api_rate_limit.py` (Flask-Limiter, varsayılan `200 per minute`) | — |
| **Dosya yükleme güvenliği** | `app/security/upload_security.py` (`validate_upload`, `safe_store_filename`) | `UPLOAD_STRICT_MIME_VALIDATION=true` varsayılan |
| **Arka plan işleri** | `app/tasks/{core_background_tasks.py, feedback_tasks.py}` | Redis+RQ destekli, hem worker içinde hem inline fallback modda çalışabilir (`_ensure_app_context()`) |
| **Mail** | `app/services/mail_service.py`, `notification_mailer.py`, `daily_weather_mail.py`, `executive_mail_center_v2.py` | Varsayılan SMTP `smtp.office365.com:587`, TLS |
| **Raporlama** | `reportlab`, `openpyxl`, `XlsxWriter`; `app/services/pdf_export_guard.py` | PDF satır limiti varsayılan 250 (inline export) |
| **Reverse proxy farkındalığı** | `app/core/reverse_proxy.py` (`apply_reverse_proxy_fix`, Werkzeug `ProxyFix`, prod/staging'de varsayılan aktif, 1 hop) | `X-Forwarded-Proto/Host` tek güvenilir proxy adımından okunur |

### İş modülleri

| Modül | Amaç | Ana route/service/model | Yetki modeli | Kritik operasyon notu |
|---|---|---|---|---|
| **Personnel/İK** | Personel kaydı, izin/devam, delegasyon, organizasyon birimleri | `app/institutional/routes.py` (facade) + `hr_personnel_operations_routes.py`, `hr_personnel_leave_routes.py`, `hr_personnel_delegation_routes.py`, `hr_leave_attendance_routes.py`, `org_unit_routes.py`; servisler `app/services/hr_operations_service.py`, `hierarchy_*_service.py`; modeller `app/models/hr_models.py`, `org_models.py` | `menu_key_required` + rol aileleri | `hr_scope_helpers.py` "otomatik wildcard-import dönüşümü için güvenli değil, manuel refactor gerekli" olarak işaretli (ARCHITECTURE.md). |
| **Performance** | Değerlendirme dönemleri, ağırlıklandırma, amir onay hiyerarşisi | `app/performance/routes.py`, `phase10_development_guidance_ui.py`, `app/routes_performance_admin.py`; servisler `app/services/performance_service.py`, `app/services/performance/*` (`process_engine_phase6_president_approvals.py` dahil); modeller `performance_models.py`, `performance_process_engine_models.py`, `performance_low_score_models.py`, `performance_archive_models.py` | `admin_required`/`manager_required`/`menu_key_required` | İş kuralları için bkz. §17. |
| **Portal** | Kurum-içi sosyal akış: gönderi, fotoğraf, video dosyası, harici video linki, yorum, moderasyon | `app/portal/routes.py` (862 satır) | `menu_key_required`; ayrıca `PORTAL_EDITOR_ROLES`/`PORTAL_GROUP_MANAGER_ROLES`/`PORTAL_PROFILE_ADMIN_ROLES` | Video-URL görünürlük geçmişi ve backend detayları için bkz. §16. |
| **Anketler (Surveys)** | Anket oluşturma/atama/sonuç | `app/communication/surveys_routes.py` (1074 satır) | `menu_key_required` + `consume_form_token` (çift-gönderim önleyici) | — |
| **İletişim (Communication)** | Mesaj, bildirim, duyuru, popup | `app/communication/routes.py` (uyumluluk hub'ı) + `communication_phase2..9_service.py` (çok sayıda faz-numaralı servis dosyası) | `menu_key_required` | Okunmamış bildirim sayısı için `app_context_processor` kaydı var. |
| **Nabız Yoklaması (Feedback/Pulse)** | Kurum-içi periyodik geri bildirim anketleri, kampanya/aksiyon takibi, yönetici görünümü | `app/communication/feedback_*_routes.py` (action-plan, analytics, campaign, core, meeting); servisler `app/services/feedback_*` | `menu_key_required` (menü anahtarları `feedback_dashboard`/`feedback_pulse`/`feedback_campaigns`/`feedback_results`/`feedback_actions`/`feedback_manager`/`feedback_admin`) | Genel Anketler (Surveys) modülünden AYRI, kendi analitik/kampanya altyapısına sahip bir alt sistemdir. |
| **Kurumsal Bilgilendirme Merkezi (CIC)** | Doğum günü/yıldönümü gibi kurumsal otomatik bilgilendirme e-postaları | `app/communication/corporate_information_center_routes.py`; servisler `app/services/cic/*` (kendi README.md'si var) | admin/yönetici | Ayrı Scheduled Task ailesi var (bkz. §18); `app/services/corporate_information_center.py` (2764 satır) repodaki "kritik dev dosya" örneklerinden biri (bkz. bu bölümün altındaki "Bilinen mimari borç" notu). |
| **Yönetici Özeti (Executive Summary)** | Yöneticiler için otomatik özet raporu + test-mail | `app/executive_summary/routes.py` (`/yonetici-ozeti`, `/yonetici-ozeti/data`, `/yonetici-ozeti/test-mail`); servisler `app/services/executive_mail_center.py` + `_v2.py` | admin/sistem yöneticisi (menü bölümü `executive_summary`) | Sabah/gece otomatik mail görevleri için bkz. §18 (Executive Summary 0001/0830). |
| **Mobil API / PWA** | Flutter mobil istemci için salt-okunur+sınırlı-yazma JSON API; web tarafında Progressive Web App desteği | `app/api/mobile/` (blueprint `/api/mobile`, `domains/*` alt paketleri — iletişim, performans, destek, anket, AI özet, asistan); PWA: `app/pwa/routes.py` **ve** `app/pwa_blueprint.py` | Mobil auth guard (`app/api/mobile/domains/auth.py`) — mobil login için ayrı brute-force throttle YOK (bkz. yukarıdaki Authentication notu) | **⚠️ İki ayrı PWA implementasyonu bulundu** (`app/pwa/` ve `app/pwa_blueprint.py`, ikisi de `/manifest.webmanifest` benzeri uçlar kaydediyor) — hangisinin kanonik olduğu bu tur içinde netleştirilemedi, ayrı bir teknik-borç maddesi olarak §26'da işaretlendi. |
| **Destek (Support)** | Talep/bilet, yardım makaleleri | `app/support/routes.py` (1213 satır), `help_center_content.py` (1061 satır) | `admin_required`/`is_admin_family_user`/`is_manager_family_user`/`menu_key_required` | Ek dosyası doğrulaması `app/security/upload_security.py` üzerinden. |
| **Ayarlar/Yetki Matrisi** | Menü görünürlüğü, rol/yetki motoru, kataloglar | Admin UI `app/admin/role_matrix_routes.py` vb.; **asıl mantık bir servis paketi**: `app/services/settings/*` | Kendisi yetkilendirmenin kaynağı | `effective_menu.py` (2111 satır) — repodaki tek "kritik dev dosya" işaretli modüllerden biri; canlı menü görünürlüğünün otoriter kaynağı. |
| **Dashboard** | Ana HTML pano + JSON veri/grafik uçları | `app/dashboard/routes.py` | `login_required` + `menu_key_required("dashboard")` | Rotalar: `/dashboard`, `/performance/dashboard` (alias), `/dashboard/rebuild-data`. |
| **Sanal Asistan (AI Agent)** | Sohbet tabanlı asistan | `app/ai_agent/routes.py` (ayrı `Blueprint`, `/ai-agent` öneki) | Kendi `before_request` guard'ı; `/healthz` hariç kimlik doğrulama zorunlu | Bkz. §28. |
| **AI Karar Destek** | Performans/analiz panellerinde öneri/analiz | `app/ai/routes.py`, `app/admin/ai_*_routes.py` (çok sayıda faz dosyası); `app/services/ai/*` | Admin/yönetici erişimi | **Varsayılan olarak `AI_PROVIDER_MODE=stub`** — gerçek bir LLM'e bağlanmaz, deterministik `StubAIClient` kullanır. Gerçek sağlayıcı için `AI_API_KEY`/`AI_PROVIDER_MODE` açıkça ayarlanmalı. Bkz. §28. |
| **Dosya Merkezi (File Center)** | Kurum-içi güvenli dosya paylaşımı ve büyük dosya transferi (upload/download, şifreli süreli guest link, guest upload talebi, chunked büyük dosya yükleme, transfer paketleri, kota, güvenlik taraması) | `app/file_center/{routes,services,mail_service,settings_service,maintenance_service,permissions}.py` (44 route, 1154+1268 satır); 15 model `app/models/file_center_models.py` | Kendi rol-matrisi tabanlı izin modeli (`app/file_center/permissions.py`, 14 `can_*` bayrak) + guest link/upload akışları için ayrı token+parola katmanı | ClamAV entegrasyonu opsiyonel (`FILE_CENTER_CLAMAV_ENABLED`), varsayılan kapalı — devre dışıyken yalnız uzantı/MIME sezgisel kontrolü çalışır, gerçek virüs taraması yapılmaz. **⚠️ 15 tablosunun hiçbiri Alembic migration ile takip edilmiyor** (bkz. §34.7). Tam ayrıntı: **§34**. |

**Veri akışı özeti:** İstemci (tarayıcı/mobil) → Flask route (yetki guard'ı) → servis katmanı (iş mantığı; CONTRIBUTING.md kuralı: route dosyaları iş mantığı İÇERMEMELİ, servis katmanını çağırmalı) → SQLAlchemy ORM → PostgreSQL. Şablon render'da CSP nonce enjekte edilir. Dosya yüklemeleri `app/security/upload_security.py`'den geçer.

**Bilinen mimari borç:** `app/services/corporate_information_center.py` (2764 satır) ve birkaç başka dosya, 2026-06-09 tarihli bir envanterde (`docs/architecture/BYS360_ROUTE_ARCHITECTURE_INVENTORY_P1A.md`) "kritik dev dosya" (god file) olarak işaretlenmişti; mobil API route dosyası (`app/api/mobile/routes.py`) benzer bir bölünmeden geçirilerek 2379→235 satıra indirildi (P1B-P1E dalgaları, `app/api/mobile/domains/*`). Bu, gelecekteki "büyük dosya bölme" çalışmaları için kanıtlanmış bir şablon sunar.

**Kod tabanında mevcut ama aktif olmayan modüller:** `app/config/removed_modules.py`'deki `REMOVED_MODULES` sözlüğü, üç modülün kodunun repoda TAM olarak durduğunu ama route/menü/AI bağlamından ÇIKARILDIĞINI gösterir: `repository` (Belge/Medya Merkezi), `education` (Eğitim/İSG), `strategy` (Strateji) — üçü de `True` (kaldırılmış); `portal` açıkça `False` (aktif) olarak işaretlenmiştir, karışıklığı önlemek için. Bu üç modülün kodu silinmemiştir ama bu belge onları CURRENT/aktif özellik olarak SUNMAZ.

**Menüde görünmeyen ama operasyonel açıdan önemli sistemler** (bu turun kod taraması ile bulundu, önceki devir dosyasında hiç geçmiyordu):

| Sistem | Ne işe yarar | Kod konumu |
|---|---|---|
| **Schema Guard** | DB şema kendiliğinden onarım/kontrol katmanı, `AUTO_REPAIR_SCHEMA` env bayrağına bağlı | `app/schema_guard*.py` (app kökünde 5 dosya) |
| **Query Health** | DB/sorgu sağlığı gözlem paneli, statik sorgu koruması, index sözleşmeleri | `app/services/query_health/` |
| **Settings Snapshot/Rollback** | Ayarların versiyonlanması ve geri alınabilmesi | `app/services/settings/snapshots.py`, `rollback_handler.py` |
| **Onboarding servisi** | Kullanıcı ilk-kullanım/karşılama akışı | `app/services/onboarding_service.py` |
| **Excel toplu içe/dışa aktarma** | Personel/hiyerarşi/karne verisi için toplu Excel import-export | `app/services/excel_import_pipeline_service.py`, `app/services/personnel/excel_import.py`, `app/services/hierarchy_excel_preview_service.py` |
| **Asistan eğitim bankası / adım-adım tutor** | Sanal Asistan'ın rehberli kullanım kılavuzu/eğitim katmanı, sohbet Q&A'dan AYRI | `app/assistant_training_bank/`, `app/services/ai_agent/assistant_*_tutor*.py`, `assistant_knowledge_bank_v1.py` |
| **Otomatik Hiyerarşi / yönetici zinciri senkronu** | Organizasyon şemasının otomatik türetilmesi | `app/services/auto_hierarchy_service.py`, `explicit_manager_chain_service.py`, `assignment_sync_service.py` |
| **Portal Sosyal Otomatik İçe Aktarma (Instagram)** | Instagram içeriğinin Portal'a otomatik aktarımı — menüde SAYFASI yok, yalnız arka-plan otomasyonu (bilinçli olarak; kod içi not: link havuzu sayfası kasıtlı olarak geri getirilmedi) | `app/services/instagram_portal_sync.py`, `app/services/portal_social_task_service.py`; Scheduled Task için bkz. §18 |
| **Maintenance Mode** | Genel bakım-modu banner'ı/kilidi | `MAINTENANCE_MODE`/`MAINTENANCE_MESSAGE` env bayrakları |

Bunların HER BİRİ yalnız yukarıdaki tek satırla belgelenmiştir (PARTIAL kapsam) — derinlemesine akış/güvenlik/DB detayı bu dokümantasyon dalgasının kapsamı dışındadır. **Tam, repo-türetilmiş özellik envanteri ve her özelliğin gerçek devir-kapsam durumu (DOCUMENTED/PARTIAL/UNDOCUMENTED/HISTORICAL) için bkz. `docs/handover/BYS360_FEATURE_COVERAGE_MATRIX.md`.**

---

## 3. Dizin Haritası

### C:\bys360 — REPO-VERIFIED kısım (bu geliştirme/build makinesinden doğrudan gözlemlendi)

Bu makine (Claude Code oturumunun çalıştığı geliştirme/build ortamı) `C:\bys360` altında şunları içeriyor:

| Klasör | Ne işe yarar | Persistent mi | Silinebilir mi |
|---|---|---|---|
| `C:\bys360\project` | Kanonik ana git checkout — `.env.example`'daki `BYS360_PROJECT_ROOT` varsayılanı da bu yoldur; kurulum belgeleri (`BYS360_KURULUM_REHBERI.md`) release paketinin buraya extract edilmesini öngörür | Evet | Hayır — ana kod tabanı |
| `C:\bys360\worktrees\*` | Bu oturumun kullandığı izole git worktree'leri (her biri ayrı bir branch/dalga için) | Hayır, geliştirme sırasında geçici | Kullanım bitince evet, `git worktree remove` ile |
| `C:\bys360\backups` | `BACKUP_RUNBOOK.md`'de tanımlı kod/DB yedekleri (`predeploy_<timestamp>` alt klasörleri) | Evet | Hayır — retention politikasına göre yönetilir (bkz. §10) |
| `C:\bys360\logs` | Uygulama/deployment logları | Evet | Log rotasyonu ile yönetilir, tamamen silinmez |
| `C:\bys360\releases` | Bu oturumda üretilen release paketleri (zip + manifest + sha256sums) | Evet (bilinçli tutulur) | Eski paketler retention politikasına göre temizlenebilir |
| `C:\bys360\reports` | Kalite/audit raporları | Yarı-persistent | Evet, tekrar üretilebilir |
| `C:\bys360\scratchpad`, `\tmp`, `\pytest-temp`, `\_pytest_tmp_phase12b`, `\audit_tmp`, `\release_out`, `\.pytest_cache` | Geliştirme/test/build sırasında oluşan geçici çalışma alanları | Hayır | Evet, güvenle silinebilir |

**Önemli epistemik not:** Bu tablo, Claude Code'un ÇALIŞTIĞI geliştirme/build makinesinin gerçek `C:\bys360` yapısını yansıtır — bu, CANLI ÜRETİM Windows Server'ının dosya sistemi ile AYNI makine DEĞİLDİR. Bu devir dalgasının kendi talimatında adı geçen `overlays`, `archive`, `storage`, `local_storage`, `deploy_logs`, `staging` klasörleri bu geliştirme makinesinde **gözlemlenmedi** ve repository içindeki hiçbir belgede (DEPLOYMENT.md, BACKUP_RUNBOOK.md, docs/handover/*) bu isimlerle doğrulanmadı. Bunlar üretim sunucusunda gerçekten var olabilir (örn. `FILE_CENTER_STORAGE_ROOT` ortam değişkeni Dosya Merkezi için ayrı bir disk/volume yolu öngörür — `.env.example` örneği: `D:/bys360_storage/file_center`), ancak bu belge onları REPO-VERIFIED olarak sunmaz. **Yeni operatör: üretim sunucusunun gerçek dizin yapısını doğrudan RDP ile kontrol edip bu tabloyu güncellemelidir.**

### Uygulama kaynağı ile persistent veri ayrımı

`BYS360_DEVIR_PAKETI_V1.md` ve `scripts/release/build_bys360_safe_release.py`'nin dışlama kuralları, bu ayrımı somutlaştırır:

- **Uygulama kaynağı** (release paketine girer, git-tracked): `app/`, `migrations/`, `requirements.txt`, `wsgi.py`, `run_server.py`, `config.py`, `DEPLOYMENT.md` (builder'ın `REQUIRED_PACKAGE_PATH_PREFIXES`'i).
- **Persistent/hassas veri** (release paketine ASLA girmez, builder tarafından dışlanır): `.env*` (yalnız `.env.example`/`.env.docker.example` istisna), `instance/`, `logs/`, `uploads/`, `reports/`, `backups/`, `.git/`, SQLite/dump/bak/log/anahtar dosyaları, **Dosya Merkezi storage kökü** (`FILE_CENTER_STORAGE_ROOT`, tanımlıysa — bkz. §34.6).

---

## 4. Local Development

**Gereksinimler (REPO-VERIFIED, üç bağımsız kaynaktan doğrulandı — README.md, CONTRIBUTING.md, `.github/workflows/bys360-ci.yml`):** Python **3.12**, PostgreSQL 15 (opsiyonel — local'de SQLite yeterli), Git.

```bash
git clone <repo-url>
cd bys360
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt   # yalnız geliştirme/test için

copy .env.example .env
```

`.env` içinde en azından şunları ayarlayın (değerler `.env.example`'da örneklenmiştir, gerçek secret DEĞİL):

```
DATABASE_URL=sqlite:///instance/bys360_local_dev.sqlite3
SECRET_KEY=<local-gelistirme-icin-rastgele-bir-deger>
APP_ENV=development
```

**⚠️ Önemli varsayılan davranış:** `config.py`, `DATABASE_URL` ortam değişkeni tanımlı DEĞİLSE `sqlite:///:memory:` (bellek-içi, kalıcı OLMAYAN) veritabanına düşer. `.env` dosyanızda `DATABASE_URL`'i mutlaka açıkça ayarlayın, aksi halde her `flask db upgrade` / yeniden başlatma döngüsünde veri kaybedersiniz.

```bash
python -m compileall app config.py scripts migrations
flask db upgrade
python run.py
# tarayıcıda http://127.0.0.1:8000/login
```

`run.py`, `run_server.py` ve `wsgi.py` FARKLI amaçlara hizmet eder — birbirinin yerine kullanmayın:

| Dosya | Amaç | Waitress kullanır mı |
|---|---|---|
| `run.py` | Sade geliştirme girişi (`app.run(debug=False)`) | Hayır |
| `run_server.py` | Gerçek operasyonel giriş — UTF-8 stdio sağlamlaştırması (bkz. §7), `APP_ENV` production/staging ise Waitress'e geçer | Evet (yalnız prod/staging'de) |
| `wsgi.py` | Harici WSGI sunucuları için (`application = create_app()`) — doğrudan çalıştırıldığında hiçbir şey yapmaz | Hayır (kendisi başlatmaz) |

**Test/kalite komutları (copy/paste, `.github/workflows/bys360-ci.yml`'in gerçek CI adımlarıyla birebir):**

```bash
# Secret gate
python scripts/quality/bys360_secret_repo_gate.py --root .

# Ruff (tam select seti)
python -m ruff check app config.py wsgi.py run.py scripts tests

# mypy
python -m mypy app tests scripts --ignore-missing-imports --no-error-summary

# Step1 (hızlı, ~60-65 sn)
python -m pytest tests/quality -m "ci_safe" --cov=app --cov-report= --cov-fail-under=0 --tb=short -q

# Step2 (kapsamlı, ~26-28 dk) — tam komut çok uzun olduğu için .github/workflows/bys360-ci.yml
# dosyasındaki "Run integration and architecture tests" adımını KAYNAK olarak kullanın; özet:
python -m pytest tests/integration tests/architecture tests/security tests/critical \
  tests/services tests/migrations tests/release tests/communication tests/behavior \
  tests/mobile tests/performance \
  tests/quality/test_workflow_orphan_presentation_subsystem_cleanup_contract.py \
  [+ ~38 ayrı isimlendirilmiş tests/test_*.py dosyası — tam liste workflow dosyasında] \
  --cov=app --cov-append --cov-report=term-missing \
  --cov-report=xml:reports/quality/coverage.xml --cov-fail-under=0 --tb=short -q
```

**Yeni geliştirici için önemli uyarı:** Yukarıdaki Step2 komutunu ELLE yeniden yazmaya ÇALIŞMAYIN — dosya adı listesi çok uzun ve zamanla değişebilir. `.github/workflows/bys360-ci.yml` dosyasının kendisi TEK GÜVENİLİR KAYNAKTIR (README.md bunu açıkça söyler); local komutlar yalnız basitleştirilmiş alt kümelerdir.

---

## 5. Configuration / Environment

**Kural: bu bölümde hiçbir gerçek secret DEĞERİ yoktur — yalnız değişken adı, zorunluluk durumu, amaç ve local/production farkı.**

| Değişken | Zorunlu mu | Amaç | Local/Production farkı |
|---|---|---|---|
| `APP_ENV` | Evet | `development`/`testing`/`staging`/`production` | prod/staging'de güvenlik fail-fast kapıları devreye girer (bkz. §6) |
| `APP_BASE_URL` | Prod/staging'de fiilen zorunlu | Dış erişim URL'i, şema çözümlemesi için kaynak | prod/staging'de HTTPS harici host'a çözümlenmezse `RuntimeError` ile boot engellenir |
| `DATABASE_URL` / `SQLALCHEMY_DATABASE_URI` | Evet (prod'da) | ORM bağlantı dizesi | Boşsa `sqlite:///:memory:`'e düşer — prod'da bu KABUL EDİLEMEZ, `DATABASE_URL` her zaman açıkça ayarlanmalı |
| `SECRET_KEY` | Evet (prod'da fail-fast) | Flask session/CSRF imzalama | Boşsa `validate_live_security_defaults` prod/staging'de boot'u engeller |
| `TCKN_ENCRYPTION_KEY` | Şiddetle önerilir (yalnız uyarı, fail-fast değil) | TCKN/kimlik verisinin şifrelenmesi | Eksikse yalnız log uyarısı — ama KVKK açısından prod'da ASLA eksik bırakılmamalı |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`, `MAIL_USE_TLS` | Mail özellikleri için | SMTP yapılandırması | Varsayılan `smtp.office365.com:587`, TLS açık |
| `CSP_ENABLED`, `CSP_REPORT_ONLY`, `CSP_NONCE_ENABLED`, `CSP_*_SRC` | Hayır (güvenli varsayılanlar var) | Content-Security-Policy ince ayarı | `CSP_REPORT_ONLY` prod/staging dışında varsayılan `true`; prod/staging'de zorlanır |
| `SENTRY_DSN`, `SENTRY_ENVIRONMENT`, `SENTRY_TRACES_SAMPLE_RATE` | Hayır (`SENTRY_REQUIRED_IN_PRODUCTION=false` varsayılan) | Hata izleme | Boş bırakılabilir; bırakılırsa hata izleme kapalı olur (log ile bildirilir) |
| `RATELIMIT_STORAGE_URI`, `SECURITY_RATE_LIMIT_BACKEND` | Hayır | Rate-limit deposu (memory/redis/file) | Prod'da redis önerilir |
| `FILE_CENTER_STORAGE_ROOT` | Dosya Merkezi aktifse zorunlu | Kalıcı disk/volume yolu | Prod'da gerçek, ayrı bir volume; local'de boş bırakılabilir (`FILE_CENTER_ENABLED=false` varsayılan) |
| `SESSION_COOKIE_SECURE`, `REMEMBER_COOKIE_SECURE` | Hayır (akıllı varsayılan var) | Çerez güvenliği | "Akıllı downgrade" mantığı — bkz. §6, açıkça `true` istenip HTTPS/harici host koşulu sağlanmazsa otomatik `false`'a düşürülür (uyarı ile) |
| `TRUSTED_HOSTS` | Hayır (otomatik seed edilir) | Host header doğrulaması | Prod/staging'de literal `'*'` YASAK — `RuntimeError` |

**Secret değerleri bu belgeye veya herhangi bir repo dosyasına ASLA yazılmaz.** Gerçek teslim yöntemi için bkz. §31.

---

## 6. Production Architecture

**Platform:** Windows Server, Python 3.12, Flask, Waitress WSGI, Windows Görev Zamanlayıcı (Scheduled Task) ile process yönetimi.

**Not — repoda iki ayrı deployment hikayesi bulundu:** `docker-compose.yml`, `.env.docker.example` ve `docker/entrypoint.sh` bir Docker+gunicorn+Postgres+Redis yolu tanımlar; ancak `DEPLOYMENT.md` ve `run_server.py` yalnız Windows/Waitress/Scheduled-Task yolunu "canlı" olarak belgeler. **Bu belge, operatörün onayladığı gerçek canlı mimariyi (Windows/Waitress) kanonik kabul eder**; Docker yolu muhtemelen alternatif/test amaçlıdır ve iki yolu tek bir dokümanda uzlaştıran bir kaynak repoda bulunamadı — yeni operatör bunu netleştirmelidir.

### Scheduled Task: `BYS360 Live Waitress 80`

Kanonik installer: **`scripts/windows/install_bys360_live_waitress_80_task_v1.ps1`** (TD-034, plan/apply modlu — `-Apply` VERİLMEDEN çalıştırıldığında hiçbir sistem değişikliği yapmaz, yalnız planı basar).

```powershell
# DRY-RUN (varsayılan, güvenli):
.\scripts\windows\install_bys360_live_waitress_80_task_v1.ps1 `
  -ProjectRoot "C:\bys360\project" -Port 80

# GERÇEK UYGULAMA:
.\scripts\windows\install_bys360_live_waitress_80_task_v1.ps1 `
  -ProjectRoot "C:\bys360\project" -Port 80 -Apply -ConfirmReplace
```

İç komut (script tarafından tam olarak inşa edilir):

```
$env:APP_PORT = '80'; $env:PYTHONUTF8 = '1'; $env:PYTHONIOENCODING = 'utf-8'; & '<venv>\Scripts\python.exe' '<ProjectRoot>\run_server.py' *>> 'C:\bys360\logs\bys360_live_waitress_80.log'
```

Tetikleyici: `-AtStartup` (sistem açılışında, saat bazlı değil). Ayarlar: `-AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable`.

**⚠️ Doğrulanması gereken nokta:** Bu installer script'i, kendi içinde `-RunLevel Highest` / SYSTEM principal'ı AÇIKÇA ayarlamıyor (`New-ScheduledTaskPrincipal` çağrısı script içinde yok). Bu devir dalgasının brifinginde "SYSTEM, Highest" varsayılmıştı — **yeni operatör, canlı sunucudaki görevin gerçek çalıştırma düzeyini `Get-ScheduledTask -TaskName "BYS360 Live Waitress 80" | Select-Object -ExpandProperty Principal` ile doğrudan kontrol etmelidir.**

Task yeniden başlatma (DEPLOYMENT.md §7):

```powershell
Stop-ScheduledTask -TaskName "BYS360 Live Waitress 80"
# port 80'e bağlı kalıntı python/waitress process'i varsa sonlandır
Start-ScheduledTask -TaskName "BYS360 Live Waitress 80"
Start-Sleep -Seconds 8
Invoke-WebRequest http://127.0.0.1/login
```

---

## 7. Windows UTF-8 Hardening (Historical Incident + Kalıcı Çözüm)

**HISTORICAL olay:** Canlı Windows Server 2019 "BYS360 Live Waitress 80" Scheduled Task'ında, yönlendirilmiş stdout varsayılan olarak sistem ANSI kod sayfasına (cp1252) düşüyordu. `run_server.py`'nin Türkçe başlangıç mesajı (`"BYS360 başlatılıyor..."`) bu kod sayfasında kodlanamayan karakterler içerdiği için `UnicodeEncodeError` fırlatılıyor ve process, Waitress port'a bağlanamadan çöküyordu. Görev Zamanlayıcı'da task "Running" görünüyordu ama port 80 hiç açılmıyordu — health check'ler başarısız oluyordu.

**Kalıcı çözüm (REPO-VERIFIED, commit `18bf31a`, 2026-08-24), iki katman:**

1. **Uygulama seviyesi** — `run_server.py:_ensure_utf8_stdio()`: `sys.stdout`/`sys.stderr` için `.reconfigure(encoding="utf-8")` çağrılır, modül import edilir edilmez (`create_app` import'undan ÖNCE, `# noqa: E402` ile bilinçli olarak). Fail-safe: reconfigure başarısız olsa bile process çökmez (`contextlib.suppress`).
2. **Scheduled Task seviyesi** — installer script'in inşa ettiği komuta `PYTHONUTF8=1` ve `PYTHONIOENCODING=utf-8` ortam değişkenleri eklendi (yukarıdaki §6'daki komut satırına bakın).

**⚠️ GELECEKTE BU MEKANİZMAYI KALDIRMAYIN.** Her iki katman da bilinçli olarak birlikte tutulur (defense-in-depth): uygulama seviyesi tek başına yeterli olsa da, Scheduled Task seviyesindeki env değişkenleri Python'un KENDİ başlatma aşamasını da güvence altına alır (uygulama kodu çalışmaya başlamadan önce). İkisinden birini kaldırmak, bu tam üretim kesintisi senaryosunu yeniden açar. Yeni test kanıtı: `tests/quality/test_run_server_utf8_stdio_hardening_v1.py` — gerçek negatif kontrol (cp1252'ye zorlanmış bir subprocess düzeltme olmadan gerçekten çöküyor, düzeltmeyle çökmüyor).

---

## 8. Health Check

`app/routes.py:72-74`:
```python
@main_bp.get("/healthz")
def healthz():
    return jsonify({"status": "ok", "service": "bys360"}), 200
```

**Bu sığ bir liveness check'tir — DB bağlantısı KONTROL ETMEZ, kimlik doğrulama gerektirmez.** "healthz OK" tek başına veritabanının erişilebilir olduğunun kanıtı DEĞİLDİR.

**Doğru kullanım:**

- **Local/backend-doğrudan health check:** `http://127.0.0.1/healthz` — 400 dönebilir; bu bir kesinti (outage) DEĞİLDİR, `Host` header'ının reverse-proxy'siz doğrudan çağrıda `TRUSTED_HOSTS`/scheme beklentisiyle uyuşmamasından kaynaklanır. Doğru local doğrulama, gerçek proxy header'larını taklit ederek yapılmalı: `Host: bys360.canakkaletarihialan.gov.tr` ve `X-Forwarded-Proto: https`.
- **Public health check (asıl kanonik doğrulama):** `https://bys360.canakkaletarihialan.gov.tr/healthz` → beklenen: `200`.

**Neden böyle:** `config.py` içindeki `SESSION_COOKIE_SECURE`/HTTPS fail-fast mantığı, process başlangıcında `APP_BASE_URL`/`PREFERRED_URL_SCHEME` env değişkenlerinden çözümlenir — canlı isteğin `Host`/`X-Forwarded-Proto` header'larından DEĞİL. Ancak `ProxyFix` (prod/staging'de varsayılan aktif, 1 hop) sayesinde `request.scheme`/`request.host`, reverse proxy'nin ilettiği header'ları YANSITIR — bu yüzden gerçek genel HTTPS yolundan geçen bir health check, backend'e doğrudan (proxy'yi atlayarak) yapılan bir problamdan FARKLI davranır. Bir health probu proxy'yi atlarsa, uygulamaya `http`/iç host olarak görünür.

Ayrıca ikinci, ayrı bir health endpoint daha vardır: `app/ai_agent/routes.py` → `@ai_agent_bp.get("/healthz")` — Sanal Asistan alt sistemi için, dış smoke testler amaçlı, hassas veri sızdırmayan filtrelenmiş bir `status` payload'u döner.

---

## 9. Database

**PostgreSQL 15**, Windows service adı: `postgresql-x64-15` (operatör kurulumuna göre; repo bu servis adını doğrudan belgelemez, standart PostgreSQL 15 Windows kurulum adıdır — OPERATOR-ATTESTED doğrulama önerilir).

**Güncel migration head (REPO-VERIFIED, bu oturumda migration zinciri bağımsız olarak ayrıştırılarak doğrulandı):** `e0efcd07abf7` (`migrations/versions/e0efcd07abf7_add_user_security_stamp.py`). Toplam 74 migration dosyası, tek head, dallanma yok.

**Alembic kullanımı:** `alembic.ini` yalnız `script_location = migrations` belirtir; `sqlalchemy.url` alanı bilinçli olarak bir yer tutucudur (`sqlite:///:memory:`), gerçek bağlantı `.env`/`DATABASE_URL` üzerinden Flask-Migrate tarafından sağlanır. **Migration her zaman `flask db upgrade` (Flask-Migrate sarmalayıcısı) ile çalıştırılır — çıplak `alembic upgrade` KOMUTU repo genelinde HİÇBİR YERDE kullanılmaz.**

### Migration karar ağacı

```
Yeni bir deployment yapılacak
        │
        ▼
Kaynak kod migration dosyası eklendi mi?
(migrations/versions/ altında yeni dosya var mı?)
        │
   ┌────┴────┐
  Evet       Hayır
   │           │
   ▼           ▼
DB YEDEĞİ AL   Migration ATLANIR
(pg_dump)      (NOT_REQUIRED)
   │
   ▼
Staging'de dene (mümkünse)
   │
   ▼
Canlı task'i DURDUR
   │
   ▼
`flask db upgrade` çalıştır
   │
   ▼
Başarılı mı?
   │
 ┌─┴─┐
Evet  Hayır
 │      │
 ▼      ▼
Task'i   DB'yi yedekten geri yükle,
BAŞLAT   deployment'ı DURDUR, kök nedeni
         araştır — asla "biraz daha dene"
         mantığıyla ilerleme
```

**NE ZAMAN `flask db upgrade` çalıştırılır:** Yalnız yeni bir migration dosyası deployment kapsamına girdiğinde. Bu handover dalgasının kendisi (`cb2e57c`) migration İÇERMİYOR — `Database migration: NOT_REQUIRED` bu yüzden doğrudur.

**NE ZAMAN çalıştırılMAZ:** Kod değişikliği yalnız template/CSS/JS/route/servis seviyesindeyse ve `migrations/versions/` altında yeni dosya yoksa.

**Schema'yı manuel değiştirme YASAĞI:** Şema değişiklikleri YALNIZ Alembic migration dosyaları üzerinden yapılır. Doğrudan `ALTER TABLE`/`CREATE TABLE` gibi manuel SQL komutlarıyla canlı şemayı değiştirmek, migration zincirini geçmişte-doğrulanamaz hale getirir ve sonraki `flask db upgrade` çalıştırmalarını bozabilir.

**Deployment öncesi DB backup kuralı:** Her deployment'tan ÖNCE, migration içersin içermesin, `BACKUP_RUNBOOK.md`'de tanımlı `pg_dump` prosedürü çalıştırılır (bkz. §10). Migration içeren deployment'lar için bu ZORUNLUDUR, atlanamaz.

---

## 10. Backup / Restore

**Kod ile DB yedeği birbirinden AYRIDIR.** `.env` güvenli, ayrı bir kanalda tutulur — asla release paketine veya kod yedeğine girmez.

### Kod yedeği

```powershell
robocopy "C:\bys360\project" "C:\bys360\backups\predeploy_<timestamp>\project" /E `
  /XD .git .venv __pycache__ logs instance reports dist_secure `
  /XF *.pyc *.log *.sqlite *.sqlite3 *.db
```

### PostgreSQL yedeği

```powershell
pg_dump --format=custom --file=$Out "%DATABASE_URL%"
```
`DATABASE_URL` ASLA ekrana yazdırılmaz/loglanmaz; güvenli bir kurumsal terminalde çalıştırılır.

### Restore — kod

```powershell
Stop-ScheduledTask -TaskName "BYS360 Live Waitress 80"
# yedeği project üzerine geri kopyala (robocopy, ters yönde)
Start-ScheduledTask -TaskName "BYS360 Live Waitress 80"
```

Otomatikleştirilmiş bir yardımcı script mevcuttur: **`scripts\windows\rollback_bys360_live_release_v1.ps1`** (TD-036) — **varsayılan olarak DRY-RUN**'dur (yalnız planı basar, hiçbir dosya kopyalamaz); gerçekten uygulamak için `-Apply` gerekir. `.env`, `instance\`, `logs\`, `uploads` (`app\static\uploads` dahil), `reports\` her zaman KORUNUR, asla üzerine yazılmaz.

```powershell
.\scripts\windows\rollback_bys360_live_release_v1.ps1 `
  -BackupRoot "C:\bys360\backups\predeploy_YYYYMMDD_HHMMSS" -Apply
```

### Restore — PostgreSQL

```powershell
pg_restore --clean --if-exists --dbname "%DATABASE_URL%" "<dump-dosyasi>"
```
Canlı restore, yetkili onay + planlı kesinti gerektirir — bu otomatikleştirilmemiştir, manuel ve kontrollü bir adımdır.

### Hangi veri ayrı korunur

| Veri | Nerede | Release paketine girer mi |
|---|---|---|
| `.env` | Sunucu üzerinde, güvenli kanal | Hayır |
| `instance/` | Uygulama çalışma dizini | Hayır |
| `logs/` | `C:\bys360\logs` | Hayır |
| Yüklenen dosyalar (`app/static/uploads`) | Ayrı, kalıcı disk/volume (git-ignored) | Hayır |
| **Dosya Merkezi storage** (`FILE_CENTER_STORAGE_ROOT`) | Ayrı, kalıcı disk/volume — DB yalnız metadata tutar, dosya baytları burada | Hayır — ayrı, dosya-sistemi-seviyeli yedek gerekir (bkz. §34.6/§34.10) |
| PostgreSQL verisi | PostgreSQL sunucu instance'ı, ayrı `pg_dump` yedeği | Hayır (kod paketinden tamamen bağımsız) |

### Saklama (retention) politikası

| Yedek türü | Saklama süresi |
|---|---|
| Deployment-öncesi kod yedeği | 30 gün |
| Kritik migration-öncesi DB yedeği | 90 gün |
| Aylık güvenli arşiv | 1 yıl |
| KVKK-hassas geçici çıktılar | Yalnız gerekli olduğu sürece, sonra güvenli silme |

### Restore drill (doğrulama)

Yedek doğrulama şu adımları içermeli: dosya var mı ve boyutu sıfır değil mi, restore bir TEST ortamında gerçekten denendi mi, yedekte `.env`/token/PII/gereksiz log yok mu, saklama konumu politikaya uygun mu.

---

## 11. Clean Production Deployment (Kanonik Runbook)

Bu runbook, bu oturumda gerçekten kullanılan modeli (release paketi üretimi, exact-head CI doğrulaması, SHA256 zinciri) ve `DEPLOYMENT.md`/`BACKUP_RUNBOOK.md`'nin belgelediği prosedürleri birleştirir.

**⚠️ Interactive PowerShell riski:** Bu runbook'un tamamını canlı bir PowerShell oturumuna satır satır YAPIŞTIRMAYIN. Uzun deployment akışları bir `.ps1` dosyası olarak kaydedilip **ayrı bir PowerShell process'inde** (`powershell.exe -File deploy.ps1`) çalıştırılmalıdır — interaktif olarak yapıştırılan uzun bloklar, terminal buffer/paste-throttling sorunları veya kısmi yapıştırma nedeniyle sessizce yarım kalabilir. **İç içe (nested), AYNI sınırlayıcıyı (delimiter) kullanan here-string ASLA kullanmayın** (`@'...'@` içinde başka bir `@'...'@` — bu bir parse hatasına yol açar).

| # | Aşama | Komut/Kontrol |
|---|---|---|
| 1 | Precheck | `git status --short`, `git rev-parse HEAD` — çalışma ağacı temiz mi, doğru SHA mı |
| 2 | Package SHA256 | `Get-FileHash BYS360_FULL_LIVE_<sha>.zip -Algorithm SHA256` — manifest'teki değerle eşleşmeli |
| 3 | Current health | `Invoke-WebRequest https://<domain>/healthz` — deployment ÖNCESİ mevcut durum kaydı |
| 4 | Config preserve | `.env`, `instance\`, `logs\`, storage konumlarının yolu not edilir (üzerine yazılmayacaklar) |
| 5 | Tasks quiesce | İlgili tüm Scheduled Task'ler (mail scheduler'lar dahil) durum kontrolü — deployment sırasında çakışma önlenir |
| 6 | Port 80 stop | `Stop-ScheduledTask -TaskName "BYS360 Live Waitress 80"`; kalıntı process varsa sonlandır |
| 7 | Old app remove | Eski `project` içeriği yedeklenip (bkz. §10) temizlenir |
| 8 | Full ZIP extract | `BYS360_FULL_LIVE_<sha>.zip` → `C:\bys360\project` |
| 9 | .env restore | Güvenli kanaldan `.env` geri konur (ASLA pakette gelmez) |
| 10 | instance restore | `instance\` klasörü korunur/geri konur |
| 11 | storage preserve | Yükleme/Dosya Merkezi storage yolu DOKUNULMADAN bırakılır |
| 12 | Fresh venv | `python -m venv .venv` (temiz) |
| 13 | Dependencies | `pip install -r requirements.txt` |
| 14 | Compile | `python -m compileall app config.py scripts migrations` |
| 15 | Runtime validator | Uygulama import edilebiliyor mu (`python -c "from app import create_app; create_app()"` benzeri bir kontrol, prod env değişkenleriyle) |
| 16 | DB revision | `flask db current` — canlı DB'nin hangi revizyonda olduğu kontrol edilir |
| 17 | Migration decision | §9'daki karar ağacına göre `flask db upgrade` gerekli mi belirlenir |
| 18 | Canonical installer dry run | `install_bys360_live_waitress_80_task_v1.ps1` **`-Apply` OLMADAN** çalıştırılır — plan gözden geçirilir |
| 19 | Apply | Gerekliyse `-Apply -ConfirmReplace` ile gerçek uygulama |
| 20 | Health | `/healthz` — hem local (proxy header taklidiyle) hem public |
| 21 | Process identity | Task'in gerçekten doğru Python/venv'i çalıştırdığı doğrulanır |
| 22 | Smoke | `/login`, ana modül ekranları (performans, personel, mesajlaşma, anket/destek, admin dashboard) |
| 23 | Fresh log gate | `bys360_live_waitress_80.log` içinde §21'de listelenen kritik pattern'ler taranır (bkz. §19) |
| 24 | Task states | İlgili tüm Scheduled Task'lerin son durumu kaydedilir |
| 25 | Final health | Son bir `/healthz` + kritik ekran taraması |
| 26 | Deployment receipt | SHA, paket adı, SHA256, saat, health sonucu, smoke sonucu bir "deployment receipt" olarak `C:\bys360\logs` veya `deploy_logs` altına yazılır |

---

## 12. Release Build

**Kanonik builder:** `scripts/release/build_bys360_safe_release.py` (`PACKAGE = "BYS360_SAFE_RELEASE_BUILDER_PHASE2_V3_DETERMINISTIC"`, `SCHEMA_VERSION = 2`).

**Mekanizma (REPO-VERIFIED, bu oturumda gerçekten çalıştırılıp doğrulandı):**

- **Kaynak:** yalnız `git ls-files -z` — **filesystem fallback YOK**; git kullanılamazsa `GitDiscoveryError` ile build durur (fail-closed).
- **Dirty tree fail-closed:** `git status --porcelain=v1` ile tracked/staged herhangi bir değişiklik varsa `DirtySourceError`.
- **Kaynak SHA sabitleme:** `--source-sha` verilirse `git rev-parse HEAD` ile birebir eşleşmeli, aksi halde hata.
- **Yasaklı dizin/dosya kuralları:** `.git`, `.venv`, `node_modules`, `__pycache__`, `instance`, `logs`, `uploads`, `reports`, `backups`, `releases`, `.github`, `tests`, `mobile_flutter`, `.codex`, `.claude` her zaman dışlanır. `"archive"` özel muamele görür: `app/` altındaki `archive` (örn. `app/templates/performance/archive/`, gerçek bir canlı özellik dizini) DIŞLANMAZ; `app/` DIŞINDAKİ her `archive` segmenti (örn. `docs/archive/`) dışlanır. `.env*` regex'i yalnız `ALLOWED_ENV_TEMPLATE_BASENAMES = {.env.example, .env.docker.example}` istisnasıyla çalışır — başka hiçbir `.env*` varyantı sızamaz. (Bu iki kural, 2026-08-23/24 tarihli gerçek bir hata düzeltmesinin sonucudur — önceki versiyon `app/templates/performance/archive/`'i ve `.env.example`'ı yanlışlıkla paketten düşürüyordu.)
- **Determinizm:** Her zip girdisi için sabit tarih/saat (kaynak commit'in `git show -s --format=%ct` epoch'undan, build makinesinin saatinden DEĞİL), sabit external attribute, sıralı dosya yazımı — **aynı commit için byte-birebir aynı zip garantisi.**
- **Manifest + SHA256SUMS:** `<ad>.manifest.json` (source_sha, included/excluded sayıları, sıralı dosya listesi — mutlak yol/kullanıcı adı/secret İÇERMEZ) ve `<ad>.sha256sums.txt`.
- **Required/forbidden audit:** `--verify` modu, `REQUIRED_PACKAGE_PATH_PREFIXES = (app/, migrations/, requirements.txt, wsgi.py, run_server.py, config.py, DEPLOYMENT.md)`'in varlığını, yasaklı dizinlerin YOKLUĞUNU, manifest↔zip SHA256 tutarlılığını, beklenmeyen ekstra/eksik dosya olmadığını kontrol eder.
- **Clean-room extraction:** Bağımsız bir geçici dizine extract edilip içerik doğrudan denetlenir.
- **Build #2 determinism:** Aynı komut ikinci kez çalıştırılıp iki zip'in SHA256'sı karşılaştırılır — bu oturumda `cb2e57c` için ikisi de **`895dc9d57021a0107682edb06fd2b99e2f6d17d1d7e6db97fcf6edb9274c476c`** çıkardı, birebir aynı.

**CLI kullanımı:**

```bash
python scripts/release/build_bys360_safe_release.py \
  --root . \
  --output C:/bys360/releases/BYS360_FULL_LIVE_<sha>/BYS360_FULL_LIVE_<sha>.zip \
  --source-sha <tam-git-sha>

# Doğrulama:
python scripts/release/build_bys360_safe_release.py \
  --verify C:/bys360/releases/BYS360_FULL_LIVE_<sha>/BYS360_FULL_LIVE_<sha>.zip \
  --expected-source-sha <tam-git-sha>
```

**Örnek nihai paket (bu belgenin kanonik SHA'sı):** `BYS360_FULL_LIVE_cb2e57c.zip` — 2136 dosya, SHA256 `895dc9d57021a0107682edb06fd2b99e2f6d17d1d7e6db97fcf6edb9274c476c`.

`scripts\security\build_bys360_secure_release_v1_5.py` ve eski PowerShell sarmalayıcıları **DEPRECATED**'dir — kullanılmamalıdır.

---

## 13. CI / Quality Gates

İki AYRI, birbirini tamamlayan GitHub Actions workflow'u:

### Quality (`.github/workflows/bys360-ci.yml`, job: `quality-gate`)

`ubuntu-latest`, Python 3.12, `postgres:15` servis konteyneri, `timeout-minutes: 45`, checkout `fetch-depth: 0`. Sırayla: secret/repo gate → safe-release audit → Ruff (tam select seti) → compileall → safe-release audit (tekrar) → **Step1** → **Step2** → gerçek PostgreSQL 15 migration-integrity gate → coverage ratchet gate → mypy → operations audit → Quality9 CI contract gate → Ruff syntax sanity → `pip-audit` bağımlılık zafiyeti taraması. Ölçülen yaklaşık süre: Step1 ~60-65sn, Step2 ~26-28dk.

### Score100 (`.github/workflows/bys360-score100-quality-gate-v1.yml`)

`windows-latest`, Python 3.12, `workflow_dispatch` + `pull_request` (master/main) tetikleyicili. Tek adım: `scripts\windows\repair_bys360_score100_quality_gate_v1.ps1 -Mode gate -RunPipAudit -RunRuff` → gerçek uygulaması `scripts/quality/bys360_score100_quality_gate_v1.py`. Kontroller: bağımlılık pinleme, Android imzalama, git-tracked `.env`, secret pattern'ler, TCKN şifreleme varlığı, exec route'lar, duplicate endpoint/test skip, app-factory duplicate kural, wildcard import, broad except, repo şekli.

### Exact-head kuralı (KRİTİK — ASLA ihmal edilmez)

**Bir workflow'un "succeeded" olması TEK BAŞINA yeterli DEĞİLDİR.** Checkout adımının log çıktısındaki gerçek SHA (`git log -1 --format=%H` satırı), doğrulanmak istenen commit ile **birebir** eşleşmelidir. Eski bir workflow çalıştırması (farklı bir commit için, hatta bir önceki commit için) yeni commit için kanıt SAYILMAZ. Bu belgenin kendi hazırlanışında (bkz. §0) bu kural harfiyen uygulandı: `cb2e57c` için hem Quality hem Score100'ün Checkout log satırında tam olarak `cb2e57c5d1829ea743c696ae78595a20755f3f07` görülmeden attestation verilmedi.

**GitHub Actions doğrudan okunamıyorsa** (bu oturumun kendi durumu — `gh` CLI kurulu değil, doğrudan API/browser erişimi yok), operatörden TAZE ekran görüntüsü istenmelidir; Checkout SHA görünmeden hiçbir PASS token'ı verilmemelidir.

---

## 14. Test Strategy

| Aile | Dizin | Ne test eder |
|---|---|---|
| Unit/static (loose) | `tests/test_*.py` (~34 dosya) | AST/statik kontroller, route smoke, yardımcı fonksiyon testleri |
| Behavior | `tests/behavior/` (6) | Gerçek servis/model davranışı |
| Security | `tests/security/` (~70) | CSP dalgaları, auth/CAPTCHA/rate-limit, negatif/injection testleri |
| Service | `tests/services/` (~80, en büyük alt dizin) | Servis katmanı birim testleri |
| Quality | `tests/quality/` (36) | Kalite-kapısı script'lerinin KENDİ meta-testleri (secret gate, scoring, debt registry, coverage ratchet) |
| Integration | `tests/integration/` (13) | Gerçek HTTP/DB akış testleri |
| Architecture | `tests/architecture/` (~70) | Route mimarisi/refactor-dalga sözleşme testleri |
| Migrations | `tests/migrations/` (7) | Gerçek Alembic `upgrade()`/`downgrade()` testleri, izole SQLite |
| Release | `tests/release/` (2) | Release-paketleme/audit testleri |
| Communication | `tests/communication/` (7) | İletişim route kayıt sözleşmesi (0-import statik kontrol) |
| Mobile | `tests/mobile/` (1) | Mobil domain sözleşmesi |
| Performance | `tests/performance/` (8) | **Performans YÖNETİM MODÜLÜ** testleri (yük/benchmark testi DEĞİL) |
| Critical | `tests/critical/` (7) | Geniş smoke/sözleşme kapıları |
| Load | `tests/load/` (6) | Locust yük testi script'leri — **CI'da ÇALIŞTIRILMAZ**, kapsam dışı |

**Negative controls:** Güvenlik testlerinde (host-spoof reddi, CSRF, rate-limit aşımı vb.) sistematik olarak kullanılır — "olumlu" testin yanında "bu girdi REDDEDİLMELİ" testleri de yazılır.

### Portal video wave — test-harness false-positive olayı (HISTORICAL LESSON)

2026-08-24 tarihli bir dalgada, Portal video-URL alanının canlıda görünmediği bulunup düzeltildi (CSS grid taşma hatası, bkz. §16). Bu düzeltme, **kendisiyle hiç ilgisi olmayan** iki eski test dosyasında yanlış-pozitif FAIL'e yol açtı:

- `test_no_important_declaration_added_by_this_pilot_precise_diff_check` — minified bir CSS satırında yapılan küçük bir değişiklik, aynı fiziksel satırdaki DOKUNULMAMIŞ bir `!important` kuralını "yeni eklenmiş" gibi raporluyordu (satır-bazlı, kaba `git diff` taraması nedeniyle).
- İki adet `test_no_new_css_file_was_added` (Meeting Final Gate ve P0 Completion testleri) — `git status --porcelain -- app/static/css/` dizininin TAMAMEN boş olmasını şart koşuyordu; bu, Meeting özelliğiyle HİÇ ilgisi olmayan herhangi bir CSS değişikliğinde yanlış FAIL veriyordu.

**Kanıtlanan çözüm:** Her iki mekanizma da, gerçek false-positive olduğu KANITLANDIKTAN sonra (senkron negatif-kontrol fixture'larıyla — bkz. commit `32517cf`), AYRI bir "test-harness düzeltme" dalgasında, minimal ve kapsamı sıkı tutularak düzeltildi: satır-bazlı diff yerine git'in kendi token/word-level diff algoritması (`git diff --no-index --word-diff=porcelain`), ve repo-geneli git-status kontrolü yerine "sahip olunan" (owned-scope) şablon dosyalarının kendi içeriğine bakan bir kontrol.

**Kural (bu olaydan çıkarılan, kalıcı):**
1. Test ASLA bypass edilmez (skip/xfail ile borç gizlenmez).
2. Bir testin false-positive olduğu İDDİA edilmez — senkron/izole negatif-kontrol fixture'larıyla KANITLANIR (gerçek pozitif senaryonun hâlâ yakalandığı da ayrıca kanıtlanır).
3. Harness düzeltmesi, onu tetikleyen özellik değişikliğinden AYRI bir commit/dalgada, dar kapsamda yapılır — özellik değişikliğiyle karıştırılmaz.

---

## 15. Security

- **Authentication/Authorization/Role matrix:** bkz. §2 "Ortak altyapı" tablosu.
- **CSRF:** Flask-WTF `CSRFProtect`, PWA/iOS için özel oturum-yenileme hata işleyicisi.
- **CSP + nonce:** `app/security/headers.py` — script-src varsayılan olarak `unsafe-inline` içermez, nonce inline etiketlere uygulanır.
- **Host validation:** `TRUSTED_HOSTS`, prod/staging'de literal `'*'` yasak; `ProxyFix` tek güvenilir proxy hop'u onurlandırır.
- **Rate limiting:** Flask-Limiter, varsayılan `200/dk`; ayrıca login-özel throttle (`LOGIN_IP_MAX_ATTEMPTS=12`, `LOGIN_IDENTITY_MAX_ATTEMPTS=6`, `LOGIN_LOCKOUT_MINUTES=15`, `LOGIN_CAPTCHA_THRESHOLD≥3`).
- **Secret gate:** `scripts/quality/bys360_secret_repo_gate.py` — git-native aday modeli (tracked + staged + untracked-ama-gitignore'da-olmayan), hardcoded secret-key atamalarını (`SECRET_KEY`, `DATABASE_URL`, `TCKN_ENCRYPTION_KEY`, `SENTRY_DSN`, vb.) ve yasaklı repo eserlerini (gerçek `.env` vb.) tarar; placeholder kelime allowlist'i (yanlış-pozitifleri önlemek için) ve `len(value)<16` sezgisiyle çalışır.
- **TCKN encryption:** `TCKN_ENCRYPTION_KEY` ile şifreleme; eksikse yalnız uyarı (fail-fast değil) — prod'da mutlaka ayarlanmalı.
- **Audit trail:** `app/security/audit.py` (kritik operasyonlar için).
- **File upload validation:** `app/security/upload_security.py` — `UPLOAD_STRICT_MIME_VALIDATION=true` varsayılan; Dosya Merkezi'nde opsiyonel ClamAV taraması.
- **Video URL host validation / YouTube spoof koruması:** bkz. §16.
- **Sentry opsiyonel davranış:** `SENTRY_REQUIRED_IN_PRODUCTION=false` varsayılan — DSN boşsa hata izleme sessizce kapalı kalır, boot engellenmez; DSN ayarlanırsa placeholder-görünümlü değerler reddedilir.

**KVKK bağlamı (repo belgeleriyle desteklenen):** `docs/handover/BYS360_GUVENLIK_KVKK_NOTLARI.md` — minimum veri toplama, RBAC, performans verisinin yayınlanana/onaylanana kadar gizli tutulması, AI'nin yalnız danışma amaçlı (insan denetimli) olması, kritik operasyonlarda audit log, `.env`/DB dump/logların release paketine ASLA girmemesi. Rol bazlı görünürlük tablosu mevcuttur (Personel/Amir/Koordinatör-Grup Başkanı/Başkan-Admin).

**⚠️ Kanıtsız iddia uyarısı:** Repository içinde resmi bir **ISO 27001** veya **ISO 42001** sertifikasyon kanıtı (denetim raporu, sertifika numarası, sertifikasyon kuruluşu adı) BULUNAMADI. Bu belge böyle bir sertifikasyonun VAR olduğunu iddia ETMEZ — yalnız KVKK'ya duyarlı tasarım pratiklerinin repo belgelerinde desteklendiğini belirtir.

---

## 16. Portal Video

**Canlı davranış (bu dalganın konusu):** Portal composer'da üç medya seçeneği yan yana durur — **Fotoğraf ekle**, **Video dosyası**, **Video bağlantısı**. Video bağlantısı YouTube (`youtube.com`, `youtu.be`, `youtube-nocookie.com`, `m.youtube.com`, `music.youtube.com`) ve Vimeo (`vimeo.com`, `player.vimeo.com`) linklerini kabul eder.

**Backend (REPO-VERIFIED, `app/portal/routes.py`):** `_portal_video_embed_url(raw_url)` — host allowlist doğrulaması yapar, güvenli embed URL'i üretir (`youtube-nocookie.com` kullanır, izleme çerezlerini azaltmak için). `_save_portal_video_link(post, raw_url)` — doğrulanmış linki `PortalPostAttachment` olarak kaydeder. Feed render'ında `<iframe>` `sandbox` ve `referrerpolicy` ile güvenli şekilde gömülür (`app/templates/portal/_post_card.html`).

**Host spoof koruması:** `youtube.com.attacker.example` gibi prefix-spoof denemeleri, `notyoutube.com` gibi lookalike host'lar, `javascript:`/`data:` şema denemeleri, raw `<iframe>` markup enjeksiyonu — hepsi reddedilir (`tests/security/test_portal_video_link_host_validation_negative.py`, 31 test).

**CSS görünürlük kök nedeni (HISTORICAL, bu dalgada bulunup düzeltildi):** `.portal-media-tools` ve `.bys360-v2121-media-tools` grid container'ları çıplak `1fr` track kullanıyordu. CSS spec'ine göre çıplak `1fr`, `minmax(auto,1fr)`'e çözümlenir ve track, içeriğin min-content genişliğinin ALTINA küçülemez. İki dosya-yükleme `<input type="file">` alanının geniş min-content genişliği yüzünden grid'in TOPLAM hesaplanan genişliği container'ı aşıyor, üçüncü sütunu (video bağlantısı) ekran dışına itiyor ve `.portal-composer-card{overflow:hidden}` tarafından görünmez şekilde kırpıyordu. Alan `display:block`/`visibility:visible` kalıyordu — yüzeysel görünürlük kontrolleri geçiyordu — ama gerçek layout konumunda kullanıcı tarafından erişilemezdi.

**Düzeltme:** `grid-template-columns` bildirimlerinde `1fr` → `minmax(0,1fr)` (standart grid-track-taşma düzeltmesi). Gerçek render edilmiş DOM üzerinde hem masaüstü (1440px, 3 eşit 125px sütun) hem mobil (375px, tek sütun, sıfır yatay taşma) genişlikte doğrulandı; `getBoundingClientRect()` VE daha katı `checkVisibility()` API'si ile.

**Canlı kullanıcı kabulü:** OPERATOR-ATTESTED (bkz. §0) — canlı Portal composer'da üç alan da görünür, video-link alanı operatör tarafından manuel test edildi.

---

## 17. Performance Module Rules

**Kanıt kaynağı sınırlaması:** Bu bölüm yalnız repository'de doğrudan bulunan/onaylanmış iş kurallarını içerir. Repoda AÇIKÇA doğrulanmamış hiçbir iş kuralı burada iddia EDİLMEZ.

- **Değerlendirme sırası ve amir görüşü zinciri:** `app/services/performance/process_engine_phase6_president_approvals.py` dosya adı, sürecin "Başkan Onayları" adımı içerdiğini doğrular — süreç motoru, çok-adımlı bir amir/yönetici onay zinciri olarak modellenmiştir (`app/services/performance/*` altında `reason_codes`, `low_score_process_service` gibi ayrı modüller de mevcuttur).
- **Düşük skor süreci:** `app/models/performance_low_score_models.py` ve `app/services/performance/low_score_process_service.py` dosyalarının varlığı, sistemde ayrı bir "düşük skor" (repoda "<70" için özel bir sayısal eşik doğrudan doğrulanamadı — YALNIZ ayrı bir süreç/model dosyasının VARLIĞI doğrulanabildi) sürecinin ayrı bir iş akışı olarak ele alındığını gösterir.
- **Arşiv (archive):** `app/models/performance_archive_models.py` ve `app/templates/performance/archive/` (5 şablon dosyası, release builder'ın açıkça KORUDUĞU bir dizin — bkz. §12) — geçmiş değerlendirme dönemlerinin arşivlendiği ayrı bir alt sistem doğrulanmıştır.
- **Vekalet:** `app/institutional/hr_personnel_delegation_routes.py` dosyasının varlığı, personel/İK tarafında bir vekalet (delegasyon) mekanizması olduğunu doğrular; bu mekanizmanın Performans modülünün amir-onay zincirine NASIL entegre olduğu bu araştırma turunda tek tek doğrulanmadı.
- **Dönemler (periods), gelişim önerileri (development suggestions):** `phase10_development_guidance_ui.py` dosya adı "gelişim rehberliği" (development guidance) özelliğinin var olduğunu doğrular; menü anahtarı `performance_development_guidance`.
- **Hatırlatmalar (reminders):** menü anahtarı `performance_meeting_p3_reminders` ("Hatırlatma ve Aksatan Amirler"), `app/services/performance/reminder_notification_service.py`, `phase9_reminder_policy.py`, `phase10_reminder_notification_center.py`, ayrıca `app/services/ai_decision/reminder_integration.py`/`reminder_policy.py` (AI Karar Destek entegrasyonu).
- **Notlar (interim notes):** menü anahtarı `performance_interim_notes` ("Dönem İçi Notlar"), `app/services/performance/scorecard_midterm_notes.py`, `interim_notes_runtime.py`, `interim_feedback_policy.py`.

**⚠️ Bu belge, "<70 süreci", ">90 çok başarılı" gibi SAYISAL eşikleri veya "üçüncü amir" gibi organizasyonel detayları, bu araştırma turunda repo içinde doğrudan doğrulanan bir kaynak (config değeri, sabit tanım, veya açık dokümantasyon cümlesi) BULUNAMADIĞI için İDDİA ETMEZ.** Yeni operatör, bu spesifik sayısal eşikleri ve organizasyonel akış detaylarını `app/services/performance/` içindeki servis kodunu doğrudan okuyarak veya sistemin mevcut iş sahibiyle (product owner) doğrulayarak tamamlamalıdır.

---

## 18. Scheduled Task Envanteri

**⚠️ OPERATOR-ATTESTED bölüm — bu dokümantasyon oturumunun canlı Windows Görev Zamanlayıcı'ya erişimi YOKTUR.** Aşağıdaki durum tablosu operatör tarafından bildirilmiştir; repo'daki installer script kanıtlarıyla çapraz referanslanmıştır.

| Görev Adı | Bildirilen Durum | Repo'da installer kanıtı |
|---|---|---|
| BYS360 CIC Auto Mail Scheduler | Ready | `install_bys360_cic_auto_mail_scheduler_task.ps1` — REPO-VERIFIED |
| BYS360 CIC Staff Noon Mail 1300 | Disabled | — (adı bu araştırma turunda tek başına doğrulanamadı) |
| BYS360 Daily Weather Personnel Mail | Ready | `install_bys360_daily_mail_tasks_v1_4.ps1` / `install_bys360_daily_weather_mail_task.ps1` — REPO-VERIFIED |
| BYS360 Executive Summary 0001 | Ready | `register_bys360_executive_summary_tasks_v2_14_3.ps1` (kanonik; `_v2_14_1.ps1` eski/devreden) — REPO-VERIFIED |
| BYS360 Executive Summary 0830 | Ready | `register_bys360_executive_summary_tasks_v2_14_3.ps1` (kanonik; `_v2_14_1.ps1` eski/devreden) — REPO-VERIFIED |
| BYS360 Internal Test | Disabled | — |
| BYS360 Live 80 | Disabled | — (muhtemelen `BYS360 Live Waitress 80`'in öncülü/eski versiyonu) |
| **BYS360 Live Waitress 80** | **Running** | `install_bys360_live_waitress_80_task_v1.ps1` — REPO-VERIFIED, KANONİK canlı task |
| BYS360 Live Watchdog 80 | Disabled | **Repo'da BU İSİMLE HİÇBİR installer/referans bulunamadı** — yalnız operatör beyanına dayanır |
| BYS360 Performance Mail Reminder 09 | Disabled | **Repo'da BU İSİMLE HİÇBİR installer/referans bulunamadı** — yalnız operatör beyanına dayanır |

**⚠️ KRİTİK UYARI (görevin kendi talimatından, açıkça korunmuştur):**
- **Watchdog** (`BYS360 Live Watchdog 80`) **deprecated ve disabled** olarak bildirilmiştir — yanlışlıkla yeniden AKTİF EDİLMEMELİDİR.
- **Performance Mail Reminder 09** disabled olarak bildirilmiştir — yanlışlıkla yeniden AKTİF EDİLMEMELİDİR.

**Ek tarihsel not (REPO-VERIFIED, `HANDOVER_10_10_EVIDENCE_20260708.md`, 2026-07-08 tarihli anlık görüntü):** "BYS360 Portal Press News Scan V3A" görevi o tarihte artık YOKTU ("görev artık yok") — bu envanterde de görünmemelidir. Bu 2026-07-08 belgesi güncel bir kaynak DEĞİLDİR, yalnız tarihsel bir kontrol noktasıdır; canlı görev envanteri her zaman doğrudan Görev Zamanlayıcı'dan (`Get-ScheduledTask`) teyit edilmelidir.

---

## 19. Logging / Incident Response

**Log yolları:**

| Log | Yol |
|---|---|
| Live Waitress startup/runtime log | `C:\bys360\logs\bys360_live_waitress_80.log` (installer script'te sabit tanımlı) |
| Deployment receipts | `C:\bys360\logs` altında (§11 adım 26) |
| Uygulama genel logu | `.env`'deki `BYS360_LOG_DIR` (varsayılan `logs`) |
| Kalite/CI raporları | `reports/quality/` (repo içi, geçici) |

**Kritik pattern'ler (bir deployment/health taramasında ARANMALI):**

```
Traceback
UnicodeEncodeError
TemplateNotFound
OperationalError
ModuleNotFoundError
ImportError
RuntimeError
PermissionError
Address already in use
```

**Güvenlik-kritik regex:** `critical=[1-9][0-9]*` — yalnız 1 veya daha büyük bir sayı eşleşmelidir. **`critical=0` bir eşleşme DEĞİLDİR ve yanlış-pozitif olarak SAYILMAMALIDIR** — sıfır kritik hata, temiz bir durumun beklenen ifadesidir, alarm tetiklememelidir.

**İlk müdahale (BYS360_BAKIM_RUNBOOK.md'den, "beyaz ekran" senaryosu):** `/healthz` kontrolü → task durumu (`Get-ScheduledTask`) → log'da yukarıdaki pattern'ler → gerekirse §20 rollback prosedürü.

---

## 20. Rollback

**Application rollback ve DB rollback KESİN OLARAK AYRIDIR — birbirine karıştırılmaz.**

- **Migration çalışmadıysa (veya deployment migration İÇERMİYORSA): DB rollback YAPILMAZ.** Yalnız kod (application) rollback yeterlidir.
- **Migration çalışıp başarısız olduysa:** Önce kodu geri al (aşağıya bakın), sonra §10'daki `pg_restore` prosedürüyle DB'yi migration-öncesi yedekten geri yükle — bu YETKİLİ ONAY ve planlı kesinti gerektirir, otomatik değildir.

### Release rollback karar ağacı

```
Sorun tespit edildi
        │
        ▼
Sorun kod mu, DB mi, yoksa altyapı mı (Redis/SMTP/vb.)?
        │
   ┌────┼────┐
  Kod   DB   Altyapı
   │     │      │
   ▼     ▼      ▼
 Aşağı  Migration  Task/servis
 bak    rollback   yeniden
        (yukarı)   başlat,
                   DB/kod'a
                   DOKUNMA
```

**Kod rollback:** Körlemesine "eski bir zip'i geri yükle" YAPILMAZ. **Yalnız daha önce `--verify` ile doğrulanmış, geçerliliği kanıtlanmış bir release paketi kullanılır** (SHA256 + manifest doğrulaması geçmiş). `scripts\windows\rollback_bys360_live_release_v1.ps1 -Apply` ile, en son `predeploy_<timestamp>` yedeğinden geri dönülür.

---

## 21. GitHub / Branch / Release Workflow

Bu proje boyunca fiilen kullanılan ve doğrulanmış geliştirici akışı:

```
1. branch     → yeni/mevcut bir çalışma dalı (worktree ile izole edilebilir)
2. change     → kod değişikliği (minimal, kapsamı net)
3. focused    → değişikliğin doğrudan etkilediği testler
   tests
4. full gates → Ruff, mypy, secret gate, Step1, Step2 (TAM, 0 failed şart)
5. commit     → açık pathspec ile stage (`git add -- <dosya>`, ASLA `git add -A`/`.`)
6. push       → normal push (force/rebase/amend YASAK), yalnız açık kullanıcı onayıyla
7. exact-head → Quality + Score100 workflow'ları, checkout SHA'sı hedef commit ile
   CI            BİREBİR eşleşmeli (bkz. §13)
8. package    → scripts/release/build_bys360_safe_release.py, deterministik doğrulama
9. parallel   → independent SHA256, clean-room extraction, required/forbidden audit
   proof
10. deployment → §11'deki runbook, yalnız açık onayla
11. live       → canlı ortamda gerçek kullanıcı ekranı/DOM doğrulaması (string-grep
   acceptance    YETERLİ DEĞİL)
```

**Force push yasağı:** Bu proje boyunca hiçbir aşamada `--force`/`--force-with-lease` kullanılmadı. **Kontrollü fast-forward:** Bir dalga diğerinin üzerine, `git merge --ff-only <sha>` ile entegre edilir (merge commit/rebase/cherry-pick OLMADAN) — yalnız hedef commit gerçekten mevcut HEAD'in doğrudan devamıysa çalışır, aksi halde DURUR.

**Scope verification:** Her commit'ten önce `git diff --stat` ile değişen dosya listesi, beklenen kapsamla (yalnız ilgili modülün dosyaları) karşılaştırılır — beklenmeyen bir dosya varsa commit YAPILMAZ.

---

## 22. Documentation Map

| Belge | Amaç | Kim okumalı | Bu ana dosyayla ilişkisi |
|---|---|---|---|
| `README.md` | Hızlı genel bakış, kurulum özeti | Herkes (ilk okuma) | Bu belge daha kapsamlı bir SÜPERSET'tir |
| `ARCHITECTURE.md` | **DİKKAT: gerçek bir mimari belge DEĞİL** — 2026-06-13 tarihli iki süreç-disiplini kararı (wildcard-import temizliği, SAFE/HOTFIX/OVERLAY belge üretiminin durdurulması) | Süreç geçmişi merak eden | Bu ana dosyanın §2'si asıl mimari kaynaktır |
| `STATUS.md` | Kronolojik "Faz" değişiklik günlüğü — **son kayıtlı girdi 2026-07-15, bu worktree'nin (`phase5-*`) daha sonraki işini YANSITMIYOR, güncelliği şüpheli** | Geçmiş faz kararlarının detayını arayan | Güncel durum için bu ana dosya + `git log` kullanılmalı |
| `CONTRIBUTING.md` | Yeni geliştirici onboarding, modül haritası, kod kuralları | Yeni geliştirici | Bu ana dosyanın §4/§23'ü ile örtüşür, tamamlayıcıdır |
| `SECURITY.md` | Güvenlik ilkeleri (bu turda içerik detaylı okunmadı — varlığı doğrulandı) | Güvenlik incelemesi yapan | §15 ile birlikte okunmalı |
| `DEPLOYMENT.md` | **Kanonik, GÜNCEL (2026-08-23) deployment prosedürü** | Deployment yapan operatör | Bu ana dosyanın §11'i DEPLOYMENT.md'yi temel alır ve genişletir |
| `BACKUP_RUNBOOK.md` | **Kanonik, GÜNCEL (2026-08-15) yedekleme/restore prosedürü** | Operatör | Bu ana dosyanın §10'u bunu temel alır |
| `docs/handover/*.md` (BAKIM_RUNBOOK, CANLIYA_ALMA_REHBERI, RISK_VE_SUREKLILIK_PLANI, KURULUM_REHBERI, MODUL_ENVANTERI, GUVENLIK_KVKK_NOTLARI, DEVIR_PAKETI_V1) | **SUPERSEDED** — 2026-06-24 tarihli, kök dizindeki DEPLOYMENT.md/BACKUP_RUNBOOK.md'nin daha eski/hafif versiyonları. İçerik ÇELİŞKİLİ değil, yalnız daha eski. | Tarihsel bağlam | Bu ana dosya bunların yerini alır (bkz. §33 index) |
| `docs/handover/HANDOVER_10_10_EVIDENCE_20260708.md` | **HISTORICAL** — 2026-07-08 tarihli, "10/10 V6" anlık kanıt görüntüsü | Tarihsel kanıt arşivi | Güncel değil, yalnız o tarihki durumun kaydı |
| `docs/governance/*` | Kalite puanlama metodolojisi, teknik borç politikası, historical governance kararları | Kalite/skor sorularını inceleyen | §26'da özetlenmiştir |
| `docs/security/BYS360_SECRET_ROTATION_AND_HISTORY_CLEANUP_RUNBOOK.md` | Secret sızıntısı durumunda git-history temizleme prosedürü | Güvenlik olayı müdahalesi | §15/§31 ile birlikte okunmalı |
| `docs/architecture/*` | Route mimarisi envanteri ve mobil route bölme raporları (P1A-P1E) | Refactor geçmişini inceleyen | §2'de özetlenmiştir |

---

## 23. New Developer First Day — İlk Gün Kontrol Listesi

```
[ ] 1. Repo clone edildi
[ ] 2. Python 3.12 doğrulandı (`python --version`)
[ ] 3. venv oluşturuldu ve aktive edildi
[ ] 4. `pip install -r requirements.txt` ve `requirements-dev.txt` tamamlandı
[ ] 5. `.env.example` → `.env` kopyalandı, en az DATABASE_URL/SECRET_KEY/APP_ENV dolduruldu
[ ] 6. Local DB erişimi kuruldu (SQLite dosya-tabanlı, `:memory:` DEĞİL)
[ ] 7. `flask db upgrade` çalıştırıldı
[ ] 8. `python run.py` ile local başlatma başarılı, `/login` açılıyor
[ ] 9. `/healthz` 200 dönüyor
[ ] 10. Step1 + odaklı bir test dosyası çalıştırıldı, PASS görüldü
[ ] 11. Bu ana dosyanın §2 (Mimari) ve §4 (Local Dev) bölümleri okundu
[ ] 12. SECURITY.md ve bu dosyanın §15'i okundu
[ ] 13. §12 (Release Builder) çalışma mantığı anlaşıldı (henüz kendisi çalıştırılmadı)
[ ] 14. Üretim erişimi almadan ÖNCE §11 (Deployment Runbook) ve §20 (Rollback) baştan sona okundu
[ ] 15. §34 (Dosya Merkezi) okundu; Dosya Merkezi storage yapısı ve **15 tablosunun Alembic migration'a DAHİL OLMADIĞI** (§34.7) anlaşıldı
[ ] 16. Dosya Merkezi guest/share güvenlik mekanizması (token+parola, `app/file_center/permissions.py`) incelendi
[ ] 17. Dosya Merkezi ile ilgili mevcut testler çalıştırıldı: `python -m pytest tests/security/test_file_center_v1l_hardening_static.py tests/security/test_file_center_sidebar_v1n_static.py tests/security/test_csp_wave9_file_center_contract.py -v`
```

---

## 24. 30 / 60 / 90 Gün Bakım Planı

**30 gün:**
- Loglar taranır (§19'daki kritik pattern'ler için)
- `/healthz` (local + public) manuel kontrol
- Son yedeklerin (`C:\bys360\backups`) varlığı ve boyutu doğrulanır
- Bağımlılık taraması gözden geçirilir (`pip-audit` CI çıktısı)

**60 gün:**
- Gerçek bir **restore drill** yapılır (bir TEST ortamında, hem kod hem DB restore denenir — yalnız dosyanın var olduğunu kontrol etmek YETERLİ DEĞİLDİR)
- İzin/rol matrisi spot-check (Ayarlar > Yetki Matrisi üzerinden birkaç kullanıcı örneklem kontrolü)
- CI workflow'larının (Quality, Score100) son durumları gözden geçirilir
- Dokümantasyon drift kontrolü — bu ana dosyadaki komutlar/yollar hâlâ doğru mu

**90 gün:**
- Tam bir **disaster recovery simülasyonu** (bkz. §28)
- Güvenlik incelemesi (CSP/CSRF/rate-limit ayarları, secret rotasyon ihtiyacı)
- Teknik borç kaydı gözden geçirilir (`docs/governance/BYS360_TECHNICAL_DEBT_POLICY.md`, `config/quality/bys360_technical_debt_registry.json`)
- Tam bir **handover simülasyonu** — yeni/farklı bir kişi bu belgeyi takip ederek sıfırdan local kurulum yapabiliyor mu

---

## 25. Bus Factor / Devredilebilirlik

**"BYS360 neden kişiye bağlı değildir":**

| Kanıt | Nerede |
|---|---|
| Kaynak kontrolü | Git, tam commit geçmişi, `origin/phase5-critical-lint-clean-v1` |
| Deterministik release | `scripts/release/build_bys360_safe_release.py` — aynı commit için byte-birebir aynı zip (bu oturumda ampirik olarak kanıtlandı) |
| Dokümante edilmiş deployment | `DEPLOYMENT.md`, `BACKUP_RUNBOOK.md`, bu ana dosyanın §11'i |
| Database migration geçmişi | `migrations/versions/` — 74 dosya, tam Alembic zinciri, tek head |
| Otomatik testler | 4000+ test (Step1 554 + Step2 ~4049), 14 ayrı test ailesi |
| CI kapıları | Quality + Score100, exact-head kuralıyla |
| Operasyonel runbook'lar | Bu ana dosyanın §9-§20 arası bölümleri |
| Backup/restore | `BACKUP_RUNBOOK.md` + `rollback_bys360_live_release_v1.ps1` (dry-run varsayılan, kanıtlanmış otomasyon) |
| Ortam dokümantasyonu | `.env.example`, `.env.docker.example`, bu ana dosyanın §5'i |
| Modül dokümantasyonu | Bu ana dosyanın §2'si |
| Release receipt'leri | Manifest + SHA256SUMS her paket için, `C:\bys360\releases` |
| Exact-head doğrulama | §13 — "succeeded" tek başına yetmez, SHA eşleşmesi zorunlu |

---

## 26. Known Limitations / Debt

**CURRENT (aktif, bilinen):**
- `app/services/settings/effective_menu.py` (2111 satır) ve `app/services/corporate_information_center.py` (2764 satır) hâlâ "kritik dev dosya" (god file) sınıfında — mobil route'larda yapılan başarılı bölme (P1B-P1E) örneği henüz bunlara uygulanmadı.
- `docs/handover/*.md` seti (§22'de listelenen 7 dosya) 2026-06-24'ten beri güncellenmemiş — kök dizindeki `DEPLOYMENT.md`/`BACKUP_RUNBOOK.md` ile içerik olarak çelişmiyor ama daha eski/hafif.
- STATUS.md son girdisi 2026-07-15 — mevcut `phase5-critical-lint-clean` dalgasının işini yansıtmıyor.
- Mobil login (`/api/mobile/auth/login`) için özel bir throttle mekanizması YOK, yalnız genel 200/dk rate-limit'e tabi (bilinçli kabul edilmiş risk, STATUS.md Faz 2B).
- Windows/Waitress ve Docker/gunicorn olmak üzere iki ayrı deployment yolu repoda bir arada bulunuyor, tek bir belgede uzlaştırılmamış — hangisinin ne zaman kullanılacağı netleştirilmeli.
- `install_bys360_live_waitress_80_task_v1.ps1`, SYSTEM/Highest çalıştırma düzeyini script içinde açıkça ayarlamıyor — canlı görevin gerçek principal'ı doğrudan doğrulanmalı.
- **Dosya Merkezi'nin 15 tablosu hiçbir Alembic migration dosyasında yer almıyor** — bootstrap tarihsel olarak arşivlenmiş bir tek-seferlik `db.create_all()` script'i (`scripts/archive/pre_handover_20260708/local/create_file_center_tables_local_v1.py`) ile yapılmış. Yeni bir ortamda yalnız `flask db upgrade` çalıştırmak bu tabloları OLUŞTURMAZ (bkz. §34.7). Bu, kalıcı bir teknik borçtur — düzeltmek ödev/geliştirme kapsamı gerektirir, bu dokümantasyon dalgasının kapsamı DIŞINDADIR.
- **İki ayrı, örtüşen PWA implementasyonu** bulundu: `app/pwa/routes.py` ve `app/pwa_blueprint.py`, ikisi de benzer manifest/service-worker uçları kaydediyor gibi görünüyor — hangisinin kanonik/aktif olduğu bu dokümantasyon dalgası kapsamında netleştirilemedi (kod davranışı değiştirilmedi, yalnız tespit edildi).
- Menü kayıt sistemi (`app/menu_registry.py`, 1514 satır) çalışma zamanında onlarca ardışık `BEGIN/END` blok yamasıyla mutasyona uğratılıyor — statik dosya okuması "gerçek" canlı menüyü tam yansıtmayabilir, yalnız kodu ÇALIŞTIRARAK kesin doğrulanabilir.
- Repoda kodu TAM duran ama aktif olmayan üç modül var (`repository`/Belge-Medya, `education`/Eğitim-İSG, `strategy`/Strateji — `app/config/removed_modules.py`) — bunlar CURRENT/aktif özellik SAYILMAZ, yeni operatör bunları yanlışlıkla aktifleştirmemelidir.

**HISTORICAL (kapanmış, artık aktif borç DEĞİL — aktif borçmuş gibi gösterilmez):**
- Windows UTF-8 cp1252 startup çökmesi — kalıcı olarak düzeltildi (§7), iki katmanlı korumayla.
- Portal video-URL CSS görünürlük hatası — kök nedeni bulunup düzeltildi (§16).
- Release builder'ın `app/templates/performance/archive/` ve `.env.example`'ı yanlışlıkla dışlaması — düzeltildi (§12).
- Test-harness false-positive'leri (Style-2A `!important` diff kontrolü, Meeting "no new CSS" kontrolü) — ayrı, dar kapsamlı bir dalgada düzeltildi (§14).

**Governance/skorlama (HISTORICAL_UNRECONSTRUCTABLE durumu — bkz. §26.1):**
- Documentation-Handover skoru = 85.
- `cb2e57c` (Production Source SHA) için, taze exact-head Quality+Score100 CI kanıtıyla: `LIVE_READINESS_FINAL=98`, `TRANSFERABILITY_FINAL=95` — bu, GERÇEKTEN onaylı bir governance kararı (`BYS360-GOV-CEILING-WAIVER-001`, registry JSON'da `APPROVED`) ile GERÇEK exact-head CI kanıtının bir arada bulunmasından kaynaklanır. Bu kanıt YALNIZ `cb2e57c`'ye özeldir — ondan sonraki her yeni commit (bu dokümantasyon commit'leri dahil), skoru korumak için KENDİ taze exact-head kanıtını ayrıca sağlamalıdır (ayrıntı ve tam kanıt zinciri için bkz. §26.1).

**Bu belge "her şey kusursuz" gibi gerçeği aşan hiçbir ifade KULLANMAZ.** Yukarıdaki liste kasıtlı olarak eksiksiz tutulmaya çalışılmıştır.

### 26.1 Historical Governance Truth (KESİNLİKLE DEĞİŞTİRİLMEDEN KORUNUR)

- **Onaylı durum adı:** `HISTORICAL_UNRECONSTRUCTABLE` (kaynak: `docs/governance/BYS360_GOV_LEGACY_001_DECISION_RECORD.md`, satır 23) — bu durum **ASLA** `FULLY_RECONCILED` olarak yeniden yazılmaz.
- **Yasal borç sayıları:** `historical_legacy_total = 38` (`P0:0, P1:0, P2:17, P3:21`); `MAPPED_LEGACY_OPEN_COUNT = 0`; `UNMAPPED_LEGACY_OPEN_COUNT = 38`.
- **Onaylı karar kaydı:** `BYS360-GOV-LEGACY-001` (2026-08-21/22/23) — bu kararın skor üzerindeki tek başına etkisi `governance_only_final_score_delta = 0`.

- **⚠️ İKİNCİ DÜZELTME — bu bölümün BİR ÖNCEKİ versiyonu da hatalıydı.** Bu ana dosyanın ikinci versiyonu, `BYS360-GOV-CEILING-WAIVER-001`'in "onaylı/aktif bir waiver OLARAK DOĞRULANAMADI" dediğinde, yalnız `docs/governance/BYS360_GOV_HISTORICAL_GAP_ACCEPTANCE_POLICY_V1.md` (politika BELGESİ) okunmuştu — asıl KARAR KAYDININ, bu politika belgesinden SONRA, `config/quality/bys360_technical_debt_registry.json` (registry_version 1.1.0) dosyasının `reconciliation_ceiling_waiver_decision` alanına YAPISAL/makine-okunur bir onay olarak (Markdown değil, JSON alanı olarak) işlendiği GÖZDEN KAÇIRILMIŞTI. Bu, eksik araştırmanın sonucuydu — belge dosyaları tarandı, registry JSON'ının bu spesifik alanı taranmadı.

- **GERÇEK, TAM DOĞRULANMIŞ DURUM (registry dosyasından doğrudan okunmuştur):**
  ```
  config/quality/bys360_technical_debt_registry.json → reconciliation_ceiling_waiver_decision:
    decision_id            = BYS360-GOV-CEILING-WAIVER-001
    decision_status         = APPROVED
    approval_mode           = HUMAN_EXPLICIT_TOKEN
    approval_token          = "APPROVE BYS360-GOV-CEILING-WAIVER-001"
    approval_date           = 2026-08-23
    approver_role           = HUMAN_PROJECT_OWNER
    policy_id                = FORMAL_HISTORICAL_GAP_ACCEPTANCE_POLICY_V1
    decision_record_reference = docs/governance/BYS360_GOV_HISTORICAL_GAP_ACCEPTANCE_POLICY_V1.md
  ```
  Bu karar kaydı **GERÇEK ve ONAYLI**dır — insan proje sahibi tarafından açık bir onay token'ıyla onaylanmış. **Ancak** kaydın kendi `canonical_eligibility_note` alanı çok açık: *"DECISION_RECORD_PRESENT=YES, CANONICAL_WAIVER_ELIGIBILITY ile AYNI ŞEY DEĞİLDİR."* Karar kaydının VAR OLMASI tek başına hiçbir commit için tavanı kaldırmaz — `scripts/quality/bys360_score_reconcile_v1.py`'nin `waiver_active` hesaplaması (satır 851-861), skorlanan HER COMMIT için AYRI AYRI, aşağıdaki 8 koşulun TAMAMININ bağımsız ve taze şekilde sağlanmasını şart koşar:

  ```python
  waiver_active = (
      fully_verified                                                  # 1) hiçbir kapı UNKNOWN değil
      and registry_structurally_valid                                 # 2) registry kendi şemasını geçiyor
      and registry_commit_verified                                    # 3) registry içeriği skorlanan commit'in GERÇEK git tree'siyle eşleşiyor
      and isinstance(ceiling_waiver, dict)                             # 4) karar kaydı VAR
      and ceiling_waiver.get("decision_status") == "APPROVED"          # 5) karar ONAYLI
      and registry.get("reconciliation_status") == "HISTORICAL_UNRECONSTRUCTABLE"  # 6)
      and registry_validation.registry_counts.get("REGISTRY_ACTIVE_COUNT") == 0    # 7) açık teknik borç yok
      and _score100_evidence_verified(canonical_manifest, scored_commit)          # 8) SKORLANAN COMMIT'İN KENDİ taze, exact-head Score100 kanıtı
  )
  ```

- **§3 sorusunun KESİN, DOĞRULANMIŞ cevabı — bu sefer gerçekten kanıtla:** `cb2e57c5d1829ea743c696ae78595a20755f3f07` için hesaplayıcı **İKİ KEZ, bizzat** çalıştırıldı — bir kez dış kanıt OLMADAN (Run A), bir kez `--evidence-file` ile gerçek, genuinely-inspected exact-head Quality+Score100 CI ekran görüntüsü kanıtı (§13'te zaten doğrulanmış olan aynı ekran görüntüleri, `evidence_type=REMOTE_CI_VERIFIED`, `provenance=USER_SUPPLIED_REMOTE_PROOF`) verilerek (Run B). Yukarıdaki 8 koşulun TAMAMI bağımsız olarak doğrulandı: `registry_structurally_valid` (registry gate: 0 finding), `registry_commit_verified=True` (uygulama dosyaları `cb2e57c` ile mevcut HEAD arasında `git diff --stat` ile birebir aynı — dokümantasyon-only commitler registry'yi değiştirmedi), `REGISTRY_ACTIVE_COUNT=0` (14/14 kapalı, doğrudan sayıldı), `approval_baseline_commit=fe984cf1...` gerçek bir commit (`git cat-file -t` ile doğrulandı).

  **Sonuç: `waiver_active=True` GERÇEKTEN ve MEŞRU şekilde hesaplanıyor — bu bir "var olmayan waiver'ı diriltme" değil, gerçekten onaylı bir kararın, kendi tasarlanmış koşullarını GERÇEKTEN karşılayan bir commit için GERÇEKTEN tetiklenmesidir.**

- **Kanıtsız (Run A, evidence-less) vs. kanıtlı (Run B, evidence-aware) tam karşılaştırma — `cb2e57c` için:**

  | Metrik | Evidence-limited (Run A) | Evidence-aware RAW (Run B) | Governance FINAL (Run B) |
  |---|---|---|---|
  | Code Quality | 100.0 | 100.0 | 100.0 |
  | Test Assurance | 91.05 | 91.05 | 91.05 |
  | Security | 60.0 (dependency_audit=UNKNOWN) | 100.0 (dependency_audit=PASS, REMOTE_CI_VERIFIED) | 100.0 |
  | CI-Release | 60.0 (postgres_migration_integrity_gate=UNKNOWN) | 100.0 (PASS, REMOTE_CI_VERIFIED) | 100.0 |
  | Operations | 100.0 | 100.0 | 100.0 |
  | Documentation-Handover | 85.0 | 85.0 | 85.0 |
  | Maintainability | 100.0 | 100.0 | 100.0 |
  | **LIVE_READINESS** | raw=80.4705, final=**80** | raw=**97.6705** | final=**98** |
  | **TRANSFERABILITY** | raw=88.289, final=**88** | raw=**95.089** | final=**95** |

  ```
  CURRENT_CEILING        = 89 (metodolojide sabit, değişmedi)
  CEILING_APPLIED         = Run A: True (numerik olarak bağlayıcı değildi, ikisi de zaten 89 altındaydı) / Run B: False (waiver_active=True olduğu için tavan hiç uygulanmadı)
  ACTIVE_WAIVER (bu commit için) = Run A: False / Run B: True
  GOVERNANCE_RECORD        = BYS360-GOV-CEILING-WAIVER-001 (APPROVED, registry JSON'da), BYS360-GOV-LEGACY-001 (APPROVED, ayrı ve öncül karar)
  CANONICAL_EVIDENCE_COMPOSITION (Run B) = 10 REMOTE_CI_VERIFIED gate + 1 REGISTRY_DERIVED gate, 0 UNKNOWN, 0 EVIDENCE_CONFLICT, completeness=FULL
  ```

  Rapor dosyaları (bu makineye özel geçici konum, komutlarla yeniden üretilebilir):
  - Run A: `C:/bys360_pytest_tmp/score_evidenceless_cb2e57c.json`
  - Run B: `C:/bys360_pytest_tmp/score_evidenceaware_cb2e57c.json`
  - Kanıt dosyası: `C:/bys360_pytest_tmp/bys360_canonical_evidence_cb2e57c.json`

- **⚠️ Bu waiver'ın kapsamı — GENELLEŞTİRİLMEMELİDİR:** `waiver_active`, registry'deki karar kaydının VARLIĞINA rağmen, HER commit için OTOMATİK DEĞİLDİR. Koşul #8 (`_score100_evidence_verified`), skorlanan COMMIT'İN KENDİ taze exact-head Score100 kanıtını gerektirir. Gelecekte yeni bir commit geldiğinde (örn. bu dokümantasyon dalgasının kendi commit'leri `6188d39`/`9cb91d2`/bu düzeltme), o commit için AYRI, TAZE exact-head Quality+Score100 CI kanıtı sağlanmadan `waiver_active` tekrar `False`'a düşer (nitekim `6188d39` için evidence-less çalıştırıldığında tam olarak bu gözlemlendi: `waiver_active=False`, final=80/88). **Bu belgenin CURRENT olarak sunduğu `LIVE_FINAL=98`/`TRANSFER_FINAL=95`, özellikle ve yalnızca `cb2e57c5d1829ea743c696ae78595a20755f3f07` (Production Source SHA) için, o commit'in kendi exact-head CI kanıtıyla birlikte geçerlidir** — dokümantasyon-only commit'ler (`6188d39`, `9cb91d2` ve bu düzeltme) uygulama hazırlık skorunu ARTIRMAZ/DEĞİŞTİRMEZ, çünkü uygulama dosyaları (`app/`, `tests/`, `scripts/`, `config.py`, vb.) `cb2e57c` ile bu belgenin kendisi de dahil sonraki tüm commit'ler arasında birebir aynıdır (`git diff --stat` ile doğrulandı).

---

## 27. Mobile

**Repo kanıtı:** `app/api/mobile/` (REST API, `domains/*` alt paketlerine bölünmüş — bkz. §2), README.md'de "Flutter mobil istemci" ifadesi geçiyor, `mobile_flutter` adlı bir dizin/referans release builder'ın yasaklı-dizin listesinde mevcut (yani repo içinde bir Flutter proje dizini VAR, ancak bu araştırma turunda içeriği detaylı incelenmedi).

**Bu belgenin net ayrımı:**
- **Mevcut, çalışan:** Mobil REST API (`app/api/mobile/routes.py` + `domains/*`, mobil auth/dashboard/notification/personel-okuma/support-anket-yazma/assistant-chat/communication/personel-yazma/KPI uçları) — bu, gerçek, canlı bir API yüzeyidir.
- **Responsive web:** Ana web arayüzünün mobil tarayıcıda kullanılabilirliği (bu belgede ayrıca doğrulanmadı, ancak modern bir Flask/Jinja + CSS stack'inde tipik olarak beklenir).
- **Flutter/native:** Repo içinde bir Flutter proje dizini referansı bulunsa da, **bu belge bunun üretim durumunu (tamamlanmış mı, App Store/Play Store'da mı, hangi aşamada) İDDİA ETMEZ** — bu araştırma turunda doğrulanmadı. **Tamamlanmamış/gelecekteki bir iş, üretim yeteneği gibi SUNULMAZ.**

Yeni operatör, mobil istemcinin (Flutter) gerçek dağıtım durumunu ayrı olarak doğrulamalıdır.

---

## 28. AI / Decision Support

**Rolü:** BYS360'daki AI, **öneri, analiz ve rehberlik** sağlar — **nihai kurumsal karar verici DEĞİLDİR**. İki ayrı alt sistem:

1. **AI Karar Destek** (`app/ai/`, `app/admin/ai_*_routes.py`, `app/services/ai/*`) — performans/analiz panellerinde öneri üretir.
2. **Sanal Asistan** (`app/ai_agent/`, `app/services/ai_agent/*`) — sohbet arayüzü.

**Kritik mimari gerçek (REPO-VERIFIED):** `config.py`'de `AI_PROVIDER_MODE` **varsayılan olarak `'stub'`**dır — yani AI özellikleri **varsayılan kurulumda gerçek bir LLM'e BAĞLANMAZ**, `StubAIClient` adlı deterministik bir sınıf kullanır. Gerçek bir sağlayıcıya (`OpenAICompatibleAIClient`) bağlanmak için `AI_API_KEY` ve `AI_PROVIDER_MODE` açıkça ayarlanmalıdır.

**İnsan onayı / yetki modeli korunur:** Performans modülündeki amir-onay zinciri (`process_engine_phase6_president_approvals.py`) ve genel yetki matrisi (`app/services/settings/effective_menu.py`), AI önerilerinden BAĞIMSIZ olarak çalışır — AI hiçbir yerde otomatik onay/red kararı VERMEZ, yalnız insan karar vericiye girdi sağlar.

---

## 29. Disaster Recovery Checklist

Sunucu tamamen kaybedildiğinde, sıfırdan geri dönüş sıralı adımları:

```
1.  Yeni Windows Server kurulumu hazırlanır
2.  Python 3.12 kurulur
3.  PostgreSQL 15 kurulur (Windows service: postgresql-x64-15 — OPERATOR-ATTESTED
    doğrulama gerekir)
4.  En son geçerli PostgreSQL yedeği (§10) yeni sunucuya taşınır, henüz restore
    EDİLMEZ
5.  En son doğrulanmış release paketi (SHA256 + manifest ile teyit edilmiş) veya
    repo/git bundle'ı temin edilir
6.  `.env` GÜVENLİ KANALDAN (§31) geri alınır — repo/pakette ASLA yoktur
7.  `instance\` klasörü (varsa ayrı yedeği) geri konur
8.  `app/static/uploads` (varsa) VE **Dosya Merkezi storage kökü**
    (`FILE_CENTER_STORAGE_ROOT`, ayrı kalıcı disk/volume) dosya-sistemi
    seviyesinde geri konur — DB restore'undan (adım 9) BAĞIMSIZ, ayrı bir
    dosya-kopyalama işlemidir (bkz. §34.10)
9.  PostgreSQL restore: `pg_restore --clean --if-exists --dbname "%DATABASE_URL%" <dump>`
10. `python -m venv .venv` + `pip install -r requirements.txt`
11. `flask db current` ile restore edilen DB'nin revizyonu doğrulanır — `e0efcd07abf7`
    ile eşleşmeli (veya paketle birlikte gelen migration'lar varsa `flask db upgrade`).
    **⚠️ Dosya Merkezi'nin 15 tablosu bu revizyon zincirinde YOKTUR** (§34.7) — bunlar
    yalnız adım 9'daki PostgreSQL restore'u SIFIRDAN bir DB değil, Dosya Merkezi
    tablolarını zaten içeren gerçek bir yedekten yapıyorsanız geri gelir. Sıfırdan bir
    DB + yalnız `flask db upgrade` senaryosunda Dosya Merkezi tabloları OLUŞMAZ.
12. `scripts\windows\install_bys360_live_waitress_80_task_v1.ps1` (önce dry-run,
    sonra `-Apply -ConfirmReplace`) ile Scheduled Task kurulur
13. `/healthz` (local, proxy header taklidiyle + public) doğrulanır
14. §11'deki smoke listesi (login, ana modül ekranları) çalıştırılır — Dosya Merkezi
    için ayrıca `/file-center` sayfasının açıldığı ve mevcut kayıtların (varsa)
    göründüğü doğrulanır
15. Log gate (§19) taranır — kritik pattern YOK doğrulanır
```

---

## 30. Handover Acceptance Checklist

```
[ ] Repo erişimi sağlandı
[ ] Bu ana dosyanın §2 (Architecture) bölümü okundu
[ ] Local kurulum başarılı (§4)
[ ] Step1 + odaklı testler çalıştırıldı, PASS görüldü
[ ] DB bağlantısı (local + production revizyon kavramı) anlaşıldı (§9)
[ ] Bir yedek gerçekten alındı (§10)
[ ] Restore yöntemi anlaşıldı (dry-run script'i test edildi) (§10)
[ ] Release build üretildi (`--audit-only` veya gerçek build ile) (§12)
[ ] CI gate (exact-head kuralı dahil) anlaşıldı (§13)
[ ] Deployment dry-run (installer script `-Apply` OLMADAN) anlaşıldı (§11, §6)
[ ] Scheduled Task'ler incelendi, Watchdog/Performance-Reminder'ın disabled
    kalması gerektiği anlaşıldı (§18)
[ ] Health check doğru yöntemle (proxy header'larıyla) çalıştırıldı (§8)
[ ] Incident runbook (§19) okundu
[ ] Secret teslim prosedürü tamamlandı (§31)
[ ] Production erişim prosedürü tamamlandı (operatörle koordineli, ayrı kanal)
```

---

## 31. Secret Handover

**Bu belgeye veya repodaki hiçbir dosyaya gerçek secret DEĞERİ yazılmaz.** Aşağıdaki liste yalnız secret ADLARINI ve teslim YÖNTEM KATEGORİSİNİ belirtir — değerlerin kendisini DEĞİL.

| Secret | Teslim yöntemi kategorisi |
|---|---|
| Production `.env` (tüm içeriği) | Güvenli, ayrı kurumsal kanal (örn. şifreli parola yöneticisi paylaşımı, kurumsal secret-vault) — ASLA e-posta/chat düz metin |
| PostgreSQL DB kimlik bilgileri | Güvenli kanal; DB erişim yetkisi ayrıca DBA/yetkili onayı gerektirir |
| SMTP kimlik bilgileri | Güvenli kanal |
| `SECRET_KEY` | Güvenli kanal; rotasyon gerekiyorsa `docs/security/BYS360_SECRET_ROTATION_AND_HISTORY_CLEANUP_RUNBOOK.md` izlenir |
| `TCKN_ENCRYPTION_KEY` | Güvenli kanal — KVKK açısından özellikle hassas, erişim en dar çevrede tutulmalı |
| Sentry DSN (varsa) | Güvenli kanal |
| GitHub kimlik bilgileri/erişim | Kurumsal GitHub organizasyon erişim prosedürü (SSO/2FA), repo sahibi onayı ile |
| Sunucu/VPN/RDP kimlik bilgileri | Kurumsal IT güvenlik prosedürü; RDP erişimi ayrı, denetlenebilir bir onay akışı gerektirir |

Bir secret'in repoya yanlışlıkla girdiğinden şüpheleniliyorsa, `docs/security/BYS360_SECRET_ROTATION_AND_HISTORY_CLEANUP_RUNBOOK.md` prosedürü İZLENİR (secret'i rotate et → `git filter-repo` ile geçmişten temizle → doğrulama komutlarını çalıştır).

---

## 32. Source of Truth Kuralı

| Konu | Kaynak |
|---|---|
| Kod davranışı | Repository source code (bu belge DEĞİL — belge kodu AÇIKLAR, EZMEZ) |
| DB şeması | Alembic migrations (`migrations/versions/`) + canlı DB'nin gerçek revizyonu (`flask db current`) |
| Production binary/source | Doğrulanmış (`--verify` geçmiş) FULL release paketi + kaynak SHA |
| Operasyon | Bu handover dosyası + `DEPLOYMENT.md`/`BACKUP_RUNBOOK.md` (kanonik runbook'lar) |
| CI | Taze, exact-head workflow kanıtı (bkz. §13) — eski bir çalıştırma kanıt SAYILMAZ |
| Historical governance | `docs/governance/` registry (§26.1) |

---

## 33. Eski Belgeler — Index

Eski handover paketleri/belgeleri SİLİNMEMİŞTİR — aşağıda CURRENT/SUPERSEDED/HISTORICAL olarak etiketlenmiştir.

| Belge | Etiket | Not |
|---|---|---|
| **`docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md`** (bu dosya) | **CURRENT** | Tek kanonik devir belgesi |
| `README.md`, `DEPLOYMENT.md`, `BACKUP_RUNBOOK.md`, `CONTRIBUTING.md` (kök dizin) | CURRENT | Bu ana dosyanın dayandığı, güncel (Ağustos 2026) kaynak belgeler |
| `docs/handover/BYS360_BAKIM_RUNBOOK.md`, `BYS360_CANLIYA_ALMA_REHBERI.md`, `BYS360_RISK_VE_SUREKLILIK_PLANI.md`, `BYS360_KURULUM_REHBERI.md`, `BYS360_MODUL_ENVANTERI.md`, `BYS360_GUVENLIK_KVKK_NOTLARI.md`, `BYS360_DEVIR_PAKETI_V1.md`, eski `docs/handover/README.md` | **SUPERSEDED** | 2026-06-24 tarihli; kök dizindeki güncel belgelerin daha eski/hafif versiyonları; içerik ÇELİŞKİLİ değil |
| `docs/handover/HANDOVER_10_10_EVIDENCE_20260708.md` | **HISTORICAL** | 2026-07-08 tarihli, "10/10 V6" anlık kanıt görüntüsü — o tarihin kaydı, güncel durum DEĞİL |
| `docs/archive/pre_handover_20260708/**` (217 dosya) | **HISTORICAL** | 2026-07-08 öncesi dönemin geniş özellik/refactor notu arşivi |
| `docs/archive/legacy-root/*.json` | **HISTORICAL** | Eski manifest/rapor dosyaları |

**Not:** Bu devir dalgasının kendi brifinginde örnek olarak verilen `BYS360_HANDOVER_10_10_SOURCE_V6_20260708` adlı bir paket, tam repo taramasıyla ARANDI ve **bu isimle repoda hiçbir dosya/paket bulunamadı**. En yakın gerçek eşleşme `HANDOVER_10_10_EVIDENCE_20260708.md`'dir (farklı isim, aynı tarih) — bu belge yukarıdaki tabloda HISTORICAL olarak zaten doğru şekilde işaretlenmiştir. Var olmayan bir dosya adı bu index'e gerçekmiş gibi eklenmemiştir.

---

## 34. Dosya Merkezi / Güvenli Dosya Transferi

**Not — bu bölümün eklenme gerekçesi:** İlk devir dalgasında Dosya Merkezi yalnız §2'nin modül tablosunda tek bir satırla ve birkaç dağınık cümleyle geçiyordu (kanıt: bu turun kendi araştırma ajanı, 9 ayrı satır/cümle buldu, hiçbiri Portal Video (§16) veya Performance (§17) kadar derinlikli değildi). Bu bölüm o boşluğu kapatır. **WeTransfer benzeri bir ürün değildir** — tüm "guest" akışları hâlâ kimliği doğrulanmış bir sahip kullanıcı tarafından BAŞLATILIR (link/talep oluşturma authenticated bir işlemdir); bu belge Dosya Merkezi'ni **"kurum içi güvenli dosya paylaşımı ve büyük dosya transferi"** olarak tanımlar.

### 34.1 Amaç

Kurum-içi kullanıcıların dosya yüklemesi/indirmesi, parola korumalı süreli misafir bağlantılarıyla dış kişilerle güvenli paylaşım yapması, misafirlerden dosya talep etmesi, büyük dosyaları parçalı (chunked) yüklemesi ve bunların hepsinin kota/güvenlik/denetim kaydı altında yönetilmesi.

### 34.2 Kaynak dosyalar

| Katman | Dosya(lar) |
|---|---|
| Route'lar (44 endpoint) | `app/file_center/routes.py` (1154 satır) |
| Servisler | `app/file_center/services.py` (1268 satır, çekirdek mantık), `mail_service.py` (SMTP), `settings_service.py` (DB-destekli ayarlar), `maintenance_service.py` (bakım/kota/expiry), `permissions.py` (rol-matrisi yetkilendirme) |
| Modeller | `app/models/file_center_models.py` (348 satır, 15 model sınıfı) |
| Şablonlar (13 dosya) | `app/templates/file_center/{index,chunk_upload,guest_download,guest_upload,admin,logs,maintenance,quota,requests,role_matrix,security,settings,transfers}.html` |
| JS | **Ayrı `app/static/js/*file_center*` dosyası YOK** — tüm istemci JS'i şablonlar içinde inline `<script>` bloklarıdır (`chunk_upload.html:20-51`, `index.html:178-187`) |
| Menü | `app/templates/base.html:613-640` (ayrı `menu_registry.py` dosyası YOK — bu repoda menü ana olarak `base.html` içinde tanımlıdır); alt-öğeler: Dosyalarım, Transfer Paketleri, Dosya Talepleri, Büyük Dosya Yükleme, Dosya Merkezi Yönetimi, Güvenlik Taraması, Kota Yönetimi, Bakım Merkezi, Ayarlar, Rol Matrisi |
| Operasyon script'leri | `scripts/local/file_center_ops_tick_v1l.py` (bakım tick'i), `scripts/local/audit_file_center_secret_hygiene_v1l.py`, `scripts/windows/repair_file_center_secret_hygiene_v1l.ps1` |

Tüm route'lar `main_bp` üzerinde kayıtlıdır (ayrı bir Blueprint DEĞİL), `app/routes.py:304`'te import edilir. Guest-olmayan HER route, `_enabled_or_message()` ile hem `can_use_file_center(current_user)` hem `file_center_enabled()` (DB/env destekli kapatma anahtarı) kontrolünden geçer.

### 34.3 Kullanıcı akışı (authenticated)

| Akış | Route | Metod | Durum |
|---|---|---|---|
| Dosya yükleme | `/file-center/upload` | POST | **IMPLEMENTED** — tek dosya, `FILE_CENTER_MAX_FILE_GB` (varsayılan 5GB) sınırlı |
| Dosya indirme (sahip) | `/file-center/download/<id>` | GET | **IMPLEMENTED** |
| Dosya silme | `/file-center/delete/<id>` | POST | **IMPLEMENTED** — soft-delete, aktif guest linkleri de iptal eder |
| Guest link oluşturma | `/file-center/share/<id>` | POST | **IMPLEMENTED** — zorunlu parola (route seviyesinde min 6 karakter) |
| Guest link iptali | `/file-center/share/<id>/revoke` | POST | **IMPLEMENTED** |
| Transfer paketi (çoklu dosya gruplama) | `/file-center/transfers*` | GET/POST | **CONDITIONAL** — birden fazla ZATEN-yüklenmiş dosyayı gruplar; alıcı (`FileTransferRecipient`) satırları kaydedilir ama route'larda onları GERÇEKTEN e-postalayan bir adım BULUNAMADI (bkz. §34.13) |
| Misafirden dosya talebi oluşturma | `/file-center/requests/create` | POST | **IMPLEMENTED** — parola, expiry, izinli uzantı listesi, istek-özel boyut sınırı |
| Talep daveti e-postası gönderme | `/file-center/requests/<id>/send-email` | POST | **IMPLEMENTED** — sahip tarafından tetiklenir, otomatik DEĞİL |
| Klasörler | — | — | **NOT_IMPLEMENTED (kullanıcı arayüzünde)** — `FileStorageFolder` modeli var ama onu oluşturan/listeleyen hiçbir route bulunamadı; muhtemelen gelecekteki bir özellik için hazırlanmış taslak |

### 34.4 Guest/share akışı (kimlik doğrulama gerektirmeyen kısım)

**Guest download** (`GET/POST /guest/files/<token>`, `file_center_guest_download`, giriş GEREKMEZ):
- Token: sahip kullanıcı `create_guest_link()` çağırır → `secrets.token_urlsafe(32)` üretilir; DB'de yalnız `sha256(token)` (`token_hash`, unique+indexed) saklanır. **Ayrıca** düz-metin `public_token` da ayrı bir kolonda tutulur (sahibin arayüzünde linki tekrar gösterebilmesi için) — yani token tamamen hash-only değildir.
- **Parola:** zorunlu, `werkzeug.security.generate_password_hash` ile saklanır.
- **Süre sonu (expiry):** `expires_at = now + gün` (varsayılan 7 gün, `FILE_CENTER_GUEST_DEFAULT_EXPIRES_DAYS`).
- **İndirme sayacı:** `download_count` vs `max_downloads` (varsayılan 5, `FILE_CENTER_DEFAULT_DOWNLOAD_LIMIT`).
- **Not/mesaj alanı:** `FileShareLink` modelinde YOK.
- Kullanılabilirlik: `is_active AND expires_at >= now AND download_count < max_downloads`.
- Her indirme denemesi `FileDownloadLog`'a yazılır (`wrong_password`/`blocked_by_security`/`success`).

**Guest upload** (`GET/POST /guest/upload/<token>`, `file_center_guest_upload`, giriş GEREKMEZ):
- Aynı token/hash/parola deseni, `FileRequest` üzerinde.
- İstek-özel `max_file_gb` ve `allowed_extensions` (global sınırla birlikte, daha KISITLAYICI olan uygulanır).
- Guest'ten `guest_name`/`guest_email` (opsiyonel) toplanır, `FileRequestUpload` satırına IP+user-agent ile birlikte kaydedilir.
- Talep sahibinin kotasına yazılır (dosya sahibi=talep sahibi, guest DEĞİL).
- İndirme sayacı kavramı YOK (bu bir yükleme ucu); `upload_count`/`last_upload_at` sayaç olarak tutulur.

**Genel durum özeti:** Guest download = **IMPLEMENTED**; Guest upload = **IMPLEMENTED**; Parola = **IMPLEMENTED** (zorunlu); Expiry = **IMPLEMENTED**; İndirme sayısı = **IMPLEMENTED** (yalnız download tarafında); Not alanı = **NOT_IMPLEMENTED**; Bildirim (guest'e otomatik mail) = **CONDITIONAL** (yalnız sahip elle tetiklerse).

### 34.5 Chunk (parçalı) büyük dosya yükleme — tam akış

Sayfa: `/file-center/chunk-upload` (`chunk_upload.html`). Üç adım:

1. **Session create** — `POST /file-center/chunk-upload/session-json` (JS/AJAX; form-encoded `/session` varyantı da var) → `create_chunk_upload_session()`: `total_size_bytes`, `chunk_size_bytes` (varsayılan `FILE_CENTER_DEFAULT_CHUNK_MB`=10MB), opsiyonel bütün-dosya `sha256_hash` alır; `token_urlsafe(32)` session token üretir, `storage_root()/temp/chunk_sessions/<owner_id>/<token>` geçici dizinini açar, `expires_at = now+24h`.
2. **Part upload** — `POST .../chunk/<index>` → her parça `{index:08d}.part.tmp` olarak stream edilir, atomik `.replace()` ile `.part`'a dönüşür. **Parçalar salt `chunk_index` ile sıralanır/kimliklenir** (client hash'i DEĞİL). Her parçanın SHA256+boyutu ayrıca hesaplanıp `FileUploadChunk` satırına yazılır; son parça hariç her parçanın boyutu `chunk_size_bytes`'ı AŞAMAZ.
3. **Finalize** — `POST .../finalize` → `finalize_chunk_upload_session()`:
   - **Eksik-parça kontrolü:** `range(total_chunks)` içindeki her index karşılığı bir satır var mı — yoksa `ValueError` ile temiz başarısızlık (eksik index listesi hata mesajında).
   - Kota tekrar kontrol edilir (tam `total_size_bytes` için).
   - Yasaklı uzantı reddi.
   - Parçalar **sırayla** birleştirilirken YENİDEN bir SHA256 ve toplam bayt hesaplanır.
   - **Boyut doğrulaması:** `total != expected` ise → durum `failed`, kısmi dosya SİLİNİR, hata fırlatılır.
   - **Hash doğrulaması:** session-create'te client bir `sha256_hash` verdiyse, hesaplanan hash ile karşılaştırılır; UYUŞMAZSA → `failed`, dosya SİLİNİR. Client hash vermediyse bu kontrol ATLANIR (durum `verified` yerine `completed` olur).
   - Başarıda: yeni `FileStorageItem` (`scan_status="pending"`), bir `FileSecurityScan` kaydı kuyruğa alınır, geçici dizin silinir.

**Client-side resume:** `chunk_upload.html`'in inline JS'i, önce status endpoint'ini sorgular, zaten alınmış index'leri bir `Set`'e koyar ve onları tekrar göndermez — "bağlantı kopunca devam" tamamen istemci-taraflı bir davranıştır, sunucu tarafında idempotent parça saklaması dışında zorunlu kılınmaz.

**Chunk bütünlüğü — özet:** parça-boyutu kontrolü VAR, eksik-parça kontrolü VAR, toplam-boyut kontrolü VAR, TÜM-DOSYA SHA256 kontrolü VAR (ama yalnız client bunu session-create'te sağladıysa) — **parça-bazlı client-declared hash karşılaştırması YOK** (parça hash'i hesaplanıp saklanır ama hiçbir şeyle karşılaştırılmaz).

### 34.6 Storage

- Kök: `storage_root()` — `FILE_CENTER_STORAGE_ROOT` env/config değerinden okunur. **Prod'da (APP_ENV/FLASK_ENV/ENV `production`/`prod`/`canli`/`live` veya `BYS360_PRODUCTION` bayrağı) tanımsızsa `RuntimeError` fırlatır** — üretimde bu değişken ZORUNLUDUR. Local'de `<instance_path>/file_center_storage`'a düşer. Alt klasörler: `uploads/`, `deleted/`, `quarantine/`, `temp/`.
- `.env.example` örnekleri: Windows `D:/bys360_storage/file_center`, Linux `/var/lib/bys360/file_center` — gerçek değer BOŞ gönderilir (repo hiçbir gerçek yol içermez).
- **DB yalnız metadata tutar** (`storage_path`, `original_filename`, `stored_filename`, `content_type`, `extension`, `size_bytes`, `sha256_hash`) — dosya baytları YALNIZ diskte yaşar; `FileStorageItem` modelinde BLOB/bytes kolonu YOK.
- Path-traversal koruması: `secure_file_path()` sonuçlanan yolu `.relative_to(root)` ile kontrol eder — kök dışına çıkan bir yol `ValueError` fırlatır.
- Güvenlik-işaretli dosyalar `uploads/`↔`quarantine/` arasında fiziksel olarak TAŞINIR (kopyalanmaz).
- **Cleanup:** `run_file_center_maintenance_tick()` (linkler/talepler expiry + kota yeniden hesaplama + bekleyen tarama + disk-doluluk özeti) tek çağrıda çalışır, `scripts/local/file_center_ops_tick_v1l.py` ile tetiklenir. **Bu script uygulama-içi bir zamanlayıcıya (Celery/RQ) BAĞLI DEĞİL** — harici bir Windows Görev Zamanlayıcı girişi gerektirir; bu turda böyle bir görevin repoda AKTİF şekilde kurulu olduğuna dair kanıt bulunamadı (yalnız arşivlenmiş `install_file_center_scheduled_tasks_v1l.ps1` var). **Yeni operatör bunu doğrulamalı ve gerekiyorsa kurmalıdır.**
- **Orphan-file taraması YOK** — bakım tick'i link/talep süre-dolumu ve kota hesabı yapar ama diskte DB kaydı olmayan dosyaları ARAMAZ.

### 34.7 Database (gerçek modeller, yalnız var olan alanlar)

15 model, hepsi `app/models/file_center_models.py`, hepsi `TimestampMixin` (created_at/updated_at) miras alır:

| Model | Tablo | Ana alanlar |
|---|---|---|
| `FileStorageFolder` | `file_storage_folders` | id, owner_user_id, parent_id, name, is_deleted *(route'suz — kullanılmıyor)* |
| `FileStorageItem` | `file_storage_items` | id, owner_user_id, folder_id, original_filename, stored_filename, storage_path, content_type, extension, size_bytes, sha256_hash, status, **scan_status**, is_deleted, deleted_at, deleted_by_user_id |
| `FileTransfer` | `file_transfers` | id, owner_user_id, title, message, status, expires_at |
| `FileTransferItem` | `file_transfer_items` | id, transfer_id, file_id |
| `FileTransferRecipient` | `file_transfer_recipients` | id, transfer_id, recipient_user_id, recipient_email, recipient_name, status |
| `FileShareLink` | `file_share_links` | id, file_id, **token_hash** (unique), **public_token**, password_hash, expires_at, max_downloads, download_count, is_active, revoked_at/by |
| `FileRequest` | `file_requests` | id, owner_user_id, title, description, recipient_name/email, token_hash, public_token, password_hash, expires_at, max_file_gb, allowed_extensions, status, upload_count, closed_at, revoked_at/by |
| `FileRequestUpload` | `file_request_uploads` | id, request_id, file_id, guest_name, guest_email, ip_address, user_agent, status |
| `FileDownloadLog` | `file_download_logs` | id, file_id, share_link_id, downloaded_by_user_id, guest_label, ip_address, user_agent, status |
| `FileAccessLog` | `file_access_logs` | id, file_id, actor_user_id, action, ip_address, user_agent, detail |
| `FileQuotaUsage` | `file_quota_usage` | id, user_id (unique), used_bytes, file_count |
| `FileSecurityScan` | `file_security_scans` | id, file_id, status, scanner, result_message, scanned_at |
| `FileAuditLog` | `file_audit_logs` | id, actor_user_id, file_id, action, message, ip_address, user_agent |
| `FileQuotaPolicy` | `file_quota_policies` | id, scope_type, scope_value, max_storage_gb, max_single_file_gb, max_transfer_gb, warning_threshold_percent, **hard_stop_enabled** |
| `FileUploadSession` | `file_upload_sessions` | id, owner_user_id, session_token, total_size_bytes, chunk_size_bytes, total_chunks, sha256_hash, status, temp_dir, finalized_file_id, expires_at |
| `FileUploadChunk` | `file_upload_chunks` | id, session_id, chunk_index, size_bytes, sha256_hash, storage_path, status |
| `FileCenterMailLog` | `file_center_mail_logs` | id, request_id, actor_user_id, recipient_email, subject, body, purpose, status, error_message, sent_at |
| `FileCenterRolePermission` | `file_center_role_permissions` | id, role_key (unique), 14 adet `can_*` boolean bayrak |
| `FileCenterSetting` | `file_center_settings` | id, key (unique), value, value_type, group_key |

**⚠️ KRİTİK OPERASYONEL BULGU:** Bu 15 tablonun HİÇBİRİ `migrations/versions/` altında bir Alembic dosyasına sahip DEĞİLDİR. Repo geçmişinde bunlar bir kerelik, artık **arşivlenmiş** bir script (`scripts/archive/pre_handover_20260708/local/create_file_center_tables_local_v1.py`, `db.create_all()` çağıran) ile oluşturulmuştu. **Sonuç:** sıfırdan bir ortamda yalnız `flask db upgrade` çalıştırmak Dosya Merkezi tablolarını OLUŞTURMAZ. Bu, mevcut canlı veritabanında (zaten bir kez `db.create_all()` ile oluşturulduğu için) sorun YARATMAZ, ama gelecekteki bir "sıfırdan kurulum" veya "yeni ortam" senaryosunda ciddi bir şaşırtıcı boşluktur. **Bu, bu dokümantasyon dalgasının düzeltme kapsamı DIŞINDADIR** (yalnız belgeleniyor) — düzeltmek gerçek bir Alembic migration dosyası yazmayı gerektirir, bu uygulama-kodu değişikliğidir.

### 34.8 Security

| Kontrol | Mekanizma |
|---|---|
| Auth/ownership | `@login_required` + `_can_manage_file()`/`_can_manage_request()` (owner_user_id eşleşmesi veya admin-benzeri) |
| Rol-bazlı yetki | `app/file_center/permissions.py`, rol-matrisi tabanlı (`can_manage_file_center_admin`, `can_create_guest_links`, `can_create_guest_upload_requests`, `can_use_chunk_upload`, `can_manage_file_center_settings`, `can_manage_file_center_quota_policy`, `can_manage_file_center_role_matrix` dahil) |
| Guest token üretimi | `secrets.token_urlsafe(32)`; yalnız SHA256 hash sorgulanır (`token_hash`), ama düz metin de `public_token` kolonunda AYRICA saklanır |
| Parola | `werkzeug.security.generate_password_hash`/`check_password_hash` (salted); minimum 6 karakter route seviyesinde |
| Path traversal | `werkzeug.utils.secure_filename()` + `secure_file_path()`'in `.relative_to(root)` kontrolü |
| Uzantı/MIME | `blocked_extensions()` (varsayılan `.exe,.bat,.cmd,.ps1,.vbs,.scr,.dll,.msi,.js,.jar,.com,.pif`, `FILE_CENTER_BLOCKED_EXTENSIONS` ile genişletilebilir), opsiyonel allow-list (`FILE_CENTER_ALLOWED_EXTENSIONS`), çift-uzantı sezgisi, şüpheli MIME prefix listesi |
| Boyut sınırı | `FILE_CENTER_MAX_FILE_GB` (varsayılan 5.0), `FILE_CENTER_MAX_TRANSFER_GB` (varsayılan 20.0) — hem `Content-Length` ön-kontrolü hem stream-sırasında sayaç |
| Virüs taraması | **Opsiyonel ClamAV** (`FILE_CENTER_CLAMAV_ENABLED`, varsayılan `false`) — `subprocess.run` ile `FILE_CENTER_CLAMAV_COMMAND` (varsayılan `clamscan --no-summary --infected`) çalıştırır, timeout `FILE_CENTER_CLAMAV_TIMEOUT_SECONDS` (varsayılan 60). **Kapalıyken yalnız sezgisel (uzantı/MIME/çift-uzantı/boş-dosya) kontrol yapılır — GERÇEK virüs taraması YOKTUR** (kod içi literal mesaj: "Temel dosya türü ve güvenlik ön kontrolü geçti. Gerçek antivirüs taraması etkin değil.", `tests/security/test_file_center_v1l_hardening_static.py:51`'de de doğrulanmıştır). |
| Rate limiting | Bkz. §34.9 |
| CSRF | Global `CSRFProtect()`; iki misafir şablonu dahil TÜM formlarda `csrf_token`; chunk-upload AJAX JS'i her `FormData` POST'una `csrf_token` ekler |
| İndirme yetkisi | Her indirmede `can_download_file()` (silinmiş/karantinada/bloklu/tarama-temiz-değil → engellenir) |
| Audit logging | `FileAuditLog` (hemen hemen her durum-değiştiren işlemde), ayrıca `FileAccessLog`/`FileDownloadLog` (okuma/indirme-özel) |
| Süresi dolmuş/iptal token | `is_available()` kontrolü (`is_active`, `expires_at`, sayaç) her erişimde tekrar değerlendirilir |

### 34.9 Rate limit'ler (gerçek config key'leri)

Dinamik olarak, route-dekoratörü DEĞİL, `app/security/api_rate_limit.py::_apply_file_center_limits()` ile uygulanır (`app/__init__.py:294`'ten çağrılır):

| Endpoint | Config key | Varsayılan |
|---|---|---|
| `file_center_guest_download` | `FILE_CENTER_GUEST_DOWNLOAD_RATE_LIMIT` | 20/saat |
| `file_center_guest_upload` | `FILE_CENTER_GUEST_UPLOAD_RATE_LIMIT` | 10/saat |
| `file_center_upload` | `FILE_CENTER_AUTH_UPLOAD_RATE_LIMIT` | 30/saat |
| `file_center_chunk_upload_session_create` **ve** `..._session_create_json` | `FILE_CENTER_CHUNK_SESSION_RATE_LIMIT` (İKİSİ AYNI KEY'İ PAYLAŞIR) | 20/saat |
| `file_center_chunk_upload_part` | `FILE_CENTER_CHUNK_PART_RATE_LIMIT` | 240/saat |
| `file_center_chunk_upload_finalize` | `FILE_CENTER_CHUNK_FINALIZE_RATE_LIMIT` | 60/saat |

`ENABLE_API_RATE_LIMIT=true` (varsayılan) ve `flask-limiter` paketi gerektirir; paket eksikse sessizce no-op olur.

### 34.10 Backup / Restore

- **DB backup TEK BAŞINA YETERLİ DEĞİLDİR.** DB yalnız metadata tutar (§34.6) — dosya baytları `FILE_CENTER_STORAGE_ROOT` altında, PostgreSQL'in tamamen dışında yaşar.
- Doğru sıra: (1) `pg_dump` (DB metadata), (2) `FILE_CENTER_STORAGE_ROOT` kökünün dosya-sistemi seviyeli yedeği (örn. `robocopy`/benzeri, `uploads/`+`deleted/`+`quarantine/` alt klasörleri dahil — `temp/` hariç tutulabilir, oturum-geçicidir).
- Restore sırası: PostgreSQL restore + storage-kökü restore BİRLİKTE, tutarlı bir zaman noktasından yapılmalı — biri diğerinden farklı bir zaman noktasından gelirse DB'de dosya kaydı olup fiziksel dosyanın olmaması (veya tersi) riski oluşur (bkz. §34.13 incident sınıfları).
- §10'daki genel "Hangi veri ayrı korunur" tablosu artık Dosya Merkezi storage'ı ayrı bir satır olarak listeler.

### 34.11 Operasyon (yeni sistem yöneticisi için)

- **Storage kapasitesi takibi:** `storage_health_summary()` (bakım tick'inin bir parçası) disk doluluk yüzdesini hesaplar, `FILE_CENTER_DISK_ALERT_PERCENT` (varsayılan 85) aşılırsa `file_center_disk_alert` audit kaydı YAZAR — **bu yalnız bir UYARI mekanizmasıdır, upload'ları ENGELLEMEZ.**
- **Hangi klasör yedeklenir:** `FILE_CENTER_STORAGE_ROOT` kökünün tamamı (temp/ hariç tutulabilir).
- **Orphan file riski:** VAR — bakım tick'i diskte DB kaydı olmayan dosyaları ARAMAZ (§34.6). Periyodik manuel/scripted bir çapraz-kontrol henüz yoktur.
- **Cleanup nasıl çalışır:** `run_file_center_maintenance_tick()` → link/talep expiry + kota yeniden hesaplama + bekleyen güvenlik taraması + disk özeti; harici bir zamanlayıcı (Windows Görev Zamanlayıcı) gerektirir, uygulama-içi otomatik DEĞİLDİR (§34.6).
- **DB restore sonrası storage neden AYRICA gerekir:** çünkü DB yalnız "bu dosya şu yolda, şu boyutta" der — dosyanın kendisi PostgreSQL'in içinde DEĞİLDİR; DB'yi geri yükleyip storage'ı geri yüklemezseniz, uygulama var olmayan dosyalara işaret eden kayıtlarla dolu olur (indirme denemeleri 404/500 verir).
- **Kota:** `FileQuotaPolicy.hard_stop_enabled=True` DEĞİLSE (varsayılan `False`), kota aşımı upload'u ENGELLEMEZ — yalnız arayüzde uyarı/tehlike rengi gösterir. Gerçek bir sert-durdurma istiyorsanız ilgili politikada bu bayrağı açık ayarlamak gerekir.

### 34.12 Troubleshooting — gerçek anlamlı incident sınıfları

| Sınıf | Muhtemel neden |
|---|---|
| Upload 413 / boyut reddi | `FILE_CENTER_MAX_FILE_GB`/`_MAX_TRANSFER_GB` aşıldı, veya ters-proxy'nin kendi `client_max_body_size`'ı |
| Chunk finalize başarısız — "Eksik parçalar var" | Bir veya daha fazla `chunk_index` hiç yüklenmedi/timeout oldu — istemci JS'in resume mantığını tetiklemesi gerekir |
| Chunk finalize başarısız — hash uyuşmazlığı | Ağ bozulması veya istemcinin gönderdiği `sha256_hash` yanlış — dosya SİLİNMİŞ, yeniden yüklenmesi gerekir |
| Süresi dolmuş guest link/talep | `expires_at` geçmiş — `is_available()` `False` döner, kullanıcıya "süresi doldu" mesajı |
| Geçersiz token | Yanlış/eski link, ya da veritabanında hiç eşleşme yok (`token_hash` bulunamadı) |
| Storage path erişilemez | `FILE_CENTER_STORAGE_ROOT` yanlış yapılandırılmış, disk bağlı değil, veya izin sorunu — prod'da bu env eksikse `RuntimeError` ile BAŞLANGIÇTA engellenir |
| Disk dolu | `storage_health_summary()`'nin `file_center_disk_alert` audit kaydı loglarda aranmalı |
| DB kaydı var, dosya yok | Storage restore'u DB restore'undan farklı bir zaman noktasından yapıldıysa (bkz. §34.10) — indirme `send_file` seviyesinde hata verir |
| Dosya var, DB kaydı yok | Manuel dosya-sistemi müdahalesi veya kısmi restore sonrası — orphan file, hiçbir otomatik tarama bunu bulmaz (§34.6) |
| Guest-link parola/erişim sorunu | Yanlış parola denemeleri `FileDownloadLog`'da `wrong_password` olarak görünür — brute-force paterni için loglar taranmalı |

### 34.13 Known Limitations (yalnız kod tarafından gerçekten desteklenen sınırlamalar)

- Maksimum dosya boyutu: `FILE_CENTER_MAX_FILE_GB` (varsayılan 5GB); transfer paketi toplamı: `FILE_CENTER_MAX_TRANSFER_GB` (varsayılan 20GB) — sabit değil, DB'den de override edilebilir (`settings_service.py`).
- Desteklenen dosya türleri: allow-list boşsa (varsayılan) hemen hemen her tür kabul edilir, yalnız sabit bir blocked-list (`.exe,.bat,.cmd,.ps1,.vbs,.scr,.dll,.msi,.js,.jar,.com,.pif`) reddedilir.
- Expiry davranışı: guest link/talep süresi dolunca erişim otomatik kapanır (`is_available()`), ama fiziksel dosya/DB kaydı OTOMATİK silinmez — yalnız erişim engellenir.
- Guest kısıtlamaları: parola ZORUNLU, not/mesaj alanı YOK, indirme sayacı yalnız download tarafında var (upload tarafında yok).
- **Quota:** varsayılan olarak yalnız advisory (uyarı) — `hard_stop_enabled=True` açıkça ayarlanmadıkça sert bir engelleme YOKTUR.
- **Virüs taraması:** varsayılan olarak YOKTUR (yalnız ClamAV açıkça etkinleştirilirse gerçek tarama olur; aksi halde yalnız sezgisel kontrol).
- **Harici obje depolama (S3/Azure Blob/GCS) desteği YOKTUR** — yalnız yerel dosya sistemi (`storage_root()` altında).
- **Çoklu dosya tek-istekte yükleme YOKTUR** — hem normal upload hem guest upload tam olarak bir dosya/istek kabul eder; "Transfer Paketleri" özelliği zaten-yüklenmiş dosyaları GRUPLAR, tek-istekte çoklu yükleme değildir.
- **Klasör (folder) özelliği kullanıcı arayüzünde YOKTUR** — model var, route/servis desteği yok.
- **Transfer alıcılarına (`FileTransferRecipient`) otomatik e-posta bildirimi bulunamadı** — kayıtlar oluşturulur ama route'larda onları e-postalayan bir adım tespit edilemedi.
- **15 tablonun hiçbiri Alembic migration'da DEĞİLDİR** (bkz. §34.7 — bu bölümün en kritik operasyonel bulgusudur).

### 34.14 Source of Truth (Dosya Merkezi için, §32'nin genel kuralına ek)

| Konu | Kaynak |
|---|---|
| Davranış | `app/file_center/routes.py` + `services.py` (bu bölümdeki HER iddia bunlardan doğrudan okunmuştur) |
| DB | `app/models/file_center_models.py` — **Alembic migration YOK, yalnız model tanımı + tarihsel bir kerelik bootstrap script'i** (§34.7) |
| Storage | `FILE_CENTER_STORAGE_ROOT` ortam değişkeni/DB ayarı — gerçek üretim yolu bu dokümantasyon oturumunda doğrulanmadı, operatör tarafından RDP ile teyit edilmelidir |
| Security | `app/file_center/permissions.py`, `app/security/api_rate_limit.py`, `tests/security/test_file_center_*.py` |
| Production state | OPERATOR-ATTESTED dağıtım kanıtı (bkz. §0) — bu bölüm Dosya Merkezi'nin CANLIDA gerçekten hangi verilerle dolu olduğunu İDDİA ETMEZ, yalnız KODUN neyi desteklediğini belgeler |
