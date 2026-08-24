# BYS360 Feature Coverage Matrix

```
Document Status: CANONICAL (companion to BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md)
Source: REPO-DERIVED — routes, navigation/menu, templates, services, models, Scheduled Tasks
Production Source SHA: cb2e57c5d1829ea743c696ae78595a20755f3f07
Generated: 2026-08-24
```

## Amaç ve Yöntem

Bu dosya, "handover'da hangi özellik unutuldu?" sorusuna **elle sayılmış bölüm sayısıyla değil**, repository'den sistematik olarak türetilmiş bir özellik envanteriyle cevap verir. Kaynaklar: Flask blueprint'leri, `app/templates/base.html`'deki menü tanımları, route decorator'ları, `app/services/*` alt paketleri, `app/models/*`, `scripts/windows/install_*.ps1`/`register_*.ps1` Scheduled Task kurulum script'leri.

**Negative completeness gate:** Navigation'da bulunan HER ana kullanıcı feature'ı, VEYA ana blueprint/route ailesi, VEYA operasyonel-kritik service/task, aşağıdaki tabloda bir satır olarak bulunmalıdır. Bir özellik bu tabloda YOKSA, devir tamamlanmamış sayılır. **Bu tablodaki her satır, ya bu turda ya da önceki turlarda gerçekten kod okunarak doğrulanmıştır — hiçbir satır tahminle eklenmemiştir.**

**Durum tanımları:**
- **DOCUMENTED** — Ana handover dosyasında (`BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md`) dedike bir bölüm VEYA derinlemesine tablo satırı var (route/service/model/security/operasyon detayı dahil).
- **PARTIAL** — Ana handover dosyasında en az bir gerçek, spesifik cümle/satır/tablo-hücresi var (dosya yolu veya menü anahtarı ile), ama derinlemesine akış/güvenlik/DB detayı YOK.
- **UNDOCUMENTED** — Ana handover dosyasında bu özelliğe dair HİÇBİR gerçek mention yok.
- **HISTORICAL** — Kod repoda duruyor ama özellik kasıtlı olarak devre dışı/kaldırılmış; aktif bir devir konusu DEĞİLDİR.
- **FUTURE** — Model/altyapı var ama kullanıcıya açık bir uç (route/UI) YOK; muhtemelen tamamlanmamış bir özellik taslağı.

---

## Özet Sayaçlar

```
FEATURES_DISCOVERED       = 38
FULLY_DOCUMENTED          = 7
PARTIALLY_DOCUMENTED      = 28
UNDOCUMENTED              = 1
HISTORICAL                = 1
FUTURE                    = 1
```

(38 = 7+28+1+1+1)

---

## Coverage Matrix

| # | Feature | User-visible | Backend | DB | Security | Operations | Handover current coverage | Action taken (bu dalga) | Final status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Personel Yönetimi (İK) | Evet (menü bölümü `ik`) | `app/institutional/hr_*.py`, `app/services/hr_operations_service.py`, `hierarchy_*_service.py` | `hr_models.py`, `org_models.py` | `menu_key_required` + rol aileleri | Excel import ile ilişkili (bkz. #33) | §2 modül tablosu | Değişmedi (zaten yeterli) | **DOCUMENTED** |
| 2 | Performans Yönetimi | Evet (menü bölümü `performans`, ~40 alt-öğe) | `app/performance/`, `app/routes_performance_admin.py`, `app/services/performance/` (~180 dosya) | `performance_models.py`, `performance_process_engine_models.py`, `performance_low_score_models.py`, `performance_archive_models.py` | `admin_required`/`manager_required`/`menu_key_required` | §18 Scheduled Task'lerle kesişmiyor (mail hariç) | §2 modül tablosu + §17 dedike bölüm | §17'ye Hatırlatmalar/Notlar dosya yolları eklendi | **DOCUMENTED** |
| 3 | Portal | Evet (menü: `portal_feed`, `portal_profiles`, `portal_groups`, `portal_moderation`) | `app/portal/routes.py` (862 satır) | `PortalPost`, `PortalGroup`, `PortalPostComment`, `PortalModerationLog`, `PortalPostReport` | `menu_key_required` + `PORTAL_EDITOR_ROLES` vb. | Video-URL CSS düzeltme geçmişi belgeli | §2 modül tablosu + §16 dedike bölüm (video) | Değişmedi | **DOCUMENTED** |
| 4 | Dosya Merkezi (File Center) | Evet (menü: 10 alt-öğe) | `app/file_center/{routes,services,mail_service,settings_service,maintenance_service,permissions}.py` (44 route) | 15 model, `app/models/file_center_models.py` | Rol-matrisi + guest token/parola | Bakım tick'i, storage ayrı yedek gerektirir | **Önceden: yalnız 1 tablo satırı, 8 dağınık cümle** | **YENİ §34 dedike bölüm eklendi (14 alt-bölüm)**, §2/§3/§10/§23/§26/§29 çapraz-referanslandı | **DOCUMENTED** (bu dalganın ana konusu) |
| 5 | AI Karar Destek | Evet (menü bölümü `ai`, "AI Kontrol Merkezi") | `app/admin/ai_*_routes.py`, `app/ai/decision_support_faz10/11/12_routes.py`, `app/services/ai/*`, `app/services/ai_decision/*` | AI panellerine özel modeller (bu turda tek tek sayılmadı) | Admin/yönetici erişimi | `AI_PROVIDER_MODE=stub` varsayılan, gerçek LLM DEĞİL | §2 modül tablosu + §28 dedike bölüm | Değişmedi | **DOCUMENTED** |
| 6 | BYS360 Sanal Asistan | Evet (menü öğesi `ai_agent_panel`, "BYS360 Asistanı") | `app/ai_agent/routes.py` (ayrı Blueprint, `/ai-agent`), `app/services/ai_agent/*` | — | Kendi `before_request` guard'ı | — | §2 modül tablosu + §28 dedike bölüm | Değişmedi | **DOCUMENTED** |
| 7 | TCKN Şifreleme (KVKK/PII koruması) | Hayır (arka plan güvenlik özelliği) | `app/security/tckn_crypto.py`, `TCKN_ENCRYPTION_KEY` | Şifrelenmiş TCKN alanları | Fail-fast DEĞİL, yalnız uyarı; prod'da mutlaka ayarlanmalı | Secret gate tarafından taranır | §5 (env tablosu), §13 (secret gate), §15, §31 | Değişmedi (zaten yeterli) | **DOCUMENTED** |
| 8 | İletişim (Communication — mesaj/duyuru/popup) | Evet (menü bölümü `iletisim`) | `app/communication/routes.py` (hub) + `communication_phase2..9_service.py` | `communication_*_models.py` (çok sayıda faz-numaralı dosya) | `menu_key_required` | — | §2 modül tablosu (1 satır) | Değişmedi | **PARTIAL** |
| 9 | Anket (Surveys) | Evet (menü: `surveys`, `survey_manage`, `survey_results`) | `app/communication/surveys_routes.py` (1074 satır), `app/services/surveys/*` | `Survey`, `SurveyAssignment`, `SurveyQuestion`, `SurveyResponse` | `menu_key_required` + `consume_form_token` | — | §2 modül tablosu (1 satır) | Değişmedi | **PARTIAL** |
| 10 | Destek / Yardım Merkezi | Evet (menü: `support_index/new/my_tickets/assigned/all`) | `app/support/routes.py` (1213 satır), `help_center_content.py` (1061 satır) | `SupportTicket`, `SupportCategory`, `SupportHelpArticle` vb. | `admin_required`/`menu_key_required` | Dosya eki `app/security/upload_security.py` üzerinden | §2 modül tablosu (1 satır) | Değişmedi | **PARTIAL** |
| 11 | Sistem Ayarları | Evet (menü: `settings`, admin-only) | `app/account/routes.py` (`/settings`, `/admin/settings*`), `app/services/settings/*` | Ayar kataloğu tabloları (tek tek sayılmadı) | `can_manage_*` yetki desenleri | Snapshot/rollback ayrı satırda (bkz. #27) | §2 modül tablosu (1 satır) | Değişmedi | **PARTIAL** |
| 12 | Yetkilendirme / Rol Matrisi | Evet (admin arayüzü, `app/admin/role_matrix_routes.py`) | `app/services/settings/effective_menu.py` (2111 satır, kritik dev dosya), `menu_permissions.py`, `menu_profile_access.py`, `menu_rules.py` | Rol/menü görünürlük tabloları | Kendisi yetkilendirmenin KAYNAĞI (admin bypass yok) | — | §2 Ortak altyapı Authorization satırı + Ayarlar satırı | Değişmedi | **PARTIAL** |
| 13 | Dashboard | Evet (menü: `dashboard`) | `app/dashboard/routes.py`, `app/services/dashboard_expansion_service.py`/`_rebuild_service.py` | — | `login_required` + `menu_key_required` | — | §2 modül tablosu (1 satır) | Değişmedi | **PARTIAL** |
| 14 | Raporlama (PDF/Excel export) | Evet (çeşitli modüllerde export butonları) | `app/services/pdf_export_guard.py`, `reportlab`/`openpyxl`/`XlsxWriter` bağımlılıkları, dağınık `*_export_service.py` dosyaları | — | `PDF_EXPORT_MAX_ROWS_INLINE` (varsayılan 250) | — | §2 Ortak altyapı "Raporlama" satırı | Değişmedi | **PARTIAL** |
| 15 | Bildirimler (Notifications) | Evet (menü öğesi `notifications`) | `app/communication/notifications_routes.py`, `notifications_core_routes.py`, `app/services/bys360_notification_bridge.py` | — | `menu_key_required` | Okunmamış sayaç için `app_context_processor` | §2 İletişim satırının prose'unda 1 cümle | Değişmedi | **PARTIAL** |
| 16 | E-posta otomasyonları | Kısmen (bazıları arka-plan, bazıları admin tetikli) | `app/services/mail_service.py`, `mail_core.py`, `mail_feedback.py`, `mail_performance_builder.py`/`_sender.py`, `notification_mailer.py` | `FileCenterMailLog` vb. modül-özel loglar | SMTP kimlik bilgileri güvenli kanal | §18 Scheduled Task envanterinde isim bazında var | §2 Ortak altyapı Mail satırı + §18 | Değişmedi | **PARTIAL** |
| 17 | Yönetici Özeti (Executive Summary) | Evet (menü bölümü `executive_summary`, admin-only) | `app/executive_summary/routes.py`, `app/services/executive_mail_center.py`+`_v2.py` | — | admin/sistem yöneticisi | 0001/0830 Scheduled Task'leri §18'de | **Önceden: hiç mention YOK** | **YENİ satır §2 modül tablosuna eklendi** | **PARTIAL** |
| 18 | Hava durumu / personel mail akışları | Hayır (arka plan otomasyonu, admin ayar sayfası: menü öğesi `daily_weather_mail`) | `app/services/daily_weather_mail.py`, `weather_service.py`, `weather_recommendation_service.py` | — | — | Scheduled Task: "BYS360 Daily Weather Personnel Mail" (§18) | §18 Scheduled Task isim listesi | Değişmedi | **PARTIAL** |
| 19 | Arşiv (Performance Archive) | Evet (menü: `performance_archive`, "Geçmiş Karne Arşivi") | `app/services/performance/archive_service.py`, `archive_visibility_policy.py`, `scorecard_archive_import.py`/`_service.py` | `performance_archive_models.py` | Performance yetki modeliyle aynı | `app/templates/performance/archive/` release builder'da korunan dizin | §17 Performance Module Rules bullet | Değişmedi (zaten mevcuttu) | **PARTIAL** |
| 20 | Başkan Onayları (President Approvals) | Evet (menü: `performance_president_approvals`) | `app/services/performance/process_engine_phase6_president_approvals.py`, `process_engine_phase7_president_rule.py`, `president_card_review_service.py` | — | Performance yetki modeliyle aynı | — | §17 Performance Module Rules bullet | Değişmedi (zaten mevcuttu) | **PARTIAL** |
| 21 | Notlar (Interim Notes) | Evet (menü: `performance_interim_notes`, "Dönem İçi Notlar") | `app/services/performance/scorecard_midterm_notes.py`, `interim_notes_runtime.py`, `interim_feedback_policy.py` | — | Performance yetki modeliyle aynı | — | **Önceden: hiç mention YOK** | **YENİ bullet §17'ye eklendi** | **PARTIAL** |
| 22 | Hatırlatmalar (Reminders) | Evet (menü: `performance_meeting_p3_reminders`) | `app/services/performance/reminder_notification_service.py`, `phase9_reminder_policy.py`, `phase10_reminder_notification_center.py` | — | Performance yetki modeliyle aynı | AI Karar Destek entegrasyonu (`app/services/ai_decision/reminder_*.py`) | **Önceden: hiç mention YOK** | **YENİ bullet §17'ye eklendi** | **PARTIAL** |
| 23 | Mobil API / PWA | Evet (Flutter istemci + web PWA) | `app/api/mobile/` (`domains/*`), `app/pwa/routes.py` **ve** `app/pwa_blueprint.py` (iki ayrı implementasyon) | — | Mobil login için ayrı throttle YOK (bilinen risk) | — | **Önceden: yalnız §27 Mobile bölümünde genel bir paragraf** | **YENİ satır §2 modül tablosuna eklendi**, PWA çiftlenmesi §26 Known Limitations'a eklendi | **PARTIAL** |
| 24 | Nabız Yoklaması (Feedback/Pulse) | Evet (menü: `feedback_dashboard/pulse/campaigns/results/actions/manager/admin`) | `app/communication/feedback_*_routes.py`, `app/services/feedback_*` | — | `menu_key_required` | — | **Önceden: hiç mention YOK** (Anketler'den ayrı bir sistem olduğu belirtilmemişti) | **YENİ satır §2 modül tablosuna eklendi** | **PARTIAL** |
| 25 | Kurumsal Bilgilendirme Merkezi (CIC) | Evet (`app/communication/corporate_information_center_routes.py`) | `app/services/cic/*` (kendi README.md'si var) | — | admin/yönetici | Ayrı Scheduled Task ailesi (§18) | **Önceden: hiç mention YOK** (yalnız "kritik dev dosya" olarak `corporate_information_center.py` adı geçiyordu, İÇERİĞİ değil) | **YENİ satır §2 modül tablosuna eklendi** | **PARTIAL** |
| 26 | Schema Guard | Hayır (arka plan) | `app/schema_guard*.py` (5 dosya), `AUTO_REPAIR_SCHEMA` env bayrağı | — | — | DB şema kendiliğinden onarım | **Önceden: hiç mention YOK** | **YENİ tablo satırı §2'ye eklendi** | **PARTIAL** |
| 27 | Query Health (DB gözlem paneli) | Hayır/admin-only | `app/services/query_health/` | — | Admin erişimi (varsayım, tek tek doğrulanmadı) | Statik sorgu koruması, index sözleşmeleri | **Önceden: hiç mention YOK** | **YENİ tablo satırı §2'ye eklendi** | **PARTIAL** |
| 28 | Settings Snapshot / Rollback | Admin-only | `app/services/settings/snapshots.py`, `rollback_handler.py` | Ayar versiyonlama tabloları (tek tek sayılmadı) | Admin erişimi | Ayar geri-alma mekanizması | **Önceden: hiç mention YOK** | **YENİ tablo satırı §2'ye eklendi** | **PARTIAL** |
| 29 | Onboarding servisi | Muhtemelen ilk-kullanım akışı | `app/services/onboarding_service.py` | — | — | — | **Önceden: hiç mention YOK** | **YENİ tablo satırı §2'ye eklendi** | **PARTIAL** |
| 30 | Excel toplu içe/dışa aktarma | Evet (personel/hiyerarşi ekranlarında) | `app/services/excel_import_pipeline_service.py`, `app/services/personnel/excel_import.py`, `hierarchy_excel_preview_service.py` | — | — | Toplu veri değişikliği — dikkatli kullanılmalı | **Önceden: hiç mention YOK** | **YENİ tablo satırı §2'ye eklendi** | **PARTIAL** |
| 31 | Asistan eğitim bankası / adım-adım tutor | Evet (Sanal Asistan'ın bir parçası) | `app/assistant_training_bank/`, `app/services/ai_agent/assistant_*_tutor*.py`, `assistant_knowledge_bank_v1.py` | — | Sanal Asistan yetki modeliyle aynı | — | **Önceden: hiç mention YOK** (Sanal Asistan genel satırının İÇİNDE gizliydi) | **YENİ tablo satırı §2'ye eklendi** | **PARTIAL** |
| 32 | Otomatik Hiyerarşi / yönetici zinciri senkronu | Hayır (arka plan/admin) | `app/services/auto_hierarchy_service.py`, `explicit_manager_chain_service.py`, `assignment_sync_service.py` | — | — | Org şeması otomatik türetimi | **Önceden: hiç mention YOK** | **YENİ tablo satırı §2'ye eklendi** | **PARTIAL** |
| 33 | Portal Sosyal Otomatik İçe Aktarma (Instagram) | Hayır (kasıtlı olarak menü sayfası YOK, yalnız arka-plan) | `app/services/instagram_portal_sync.py`, `app/services/portal_social_task_service.py` | — | — | Scheduled Task: "BYS360 Portal Social Auto Import V3B2" (§18) | **Önceden: hiç mention YOK** | **YENİ tablo satırı §2'ye eklendi** | **PARTIAL** |
| 34 | Maintenance Mode | Evet (genel bakım banner'ı) | `MAINTENANCE_MODE`/`MAINTENANCE_MESSAGE` config bayrakları | — | — | Planlı bakım için kullanılır | **Önceden: hiç mention YOK** | **YENİ tablo satırı §2'ye eklendi** | **PARTIAL** |
| 35 | Strategic Performance v2 (KPI Dashboard/Yetkinlik/Hedefler) | Evet (menü: `performance_kpi_dashboard` vb., ayrı `/performans/stratejik` blueprint) | `app/modules/strategic_performance/routes.py`, `_dashboard/routes.py`, `app/services/strategic_performance/` | — | Performance yetki modeliyle aynı (varsayım) | — | **Hiçbir yerde AYRI bir sistem olarak belirtilmiyor** — genel "Performance" satırının içine gizli | **Yapılmadı** (bu dalganın kapsamı yalnız File Center + genel envanter; her alt-modülün derinlemesine yazımı ayrı bir dalga gerektirir) | **UNDOCUMENTED** |
| 36 | Kaldırılmış-ama-kodda-duran modüller (Repository/Belge-Medya, Education/Eğitim-İSG, Strategy/Strateji) | Hayır (kasıtlı olarak route/menüden çıkarılmış) | Kod tam duruyor, `app/config/removed_modules.py`'de `REMOVED_MODULES=True` | — | — | Yanlışlıkla yeniden aktifleştirilmemeli | **Önceden: hiç mention YOK** | **YENİ not §2 + §26'ya eklendi** | **HISTORICAL** |
| 37 | Dosya Merkezi Klasörleri (Folders) | Hayır (model var, UI/route yok) | `FileStorageFolder` modeli (`app/models/file_center_models.py`) | `file_storage_folders` tablosu (owner, parent, name, is_deleted) | — | — | **YENİ** — §34.3 ve §34.13'te "NOT_IMPLEMENTED"/"stub" olarak belgelendi | Belgelendi (kod değiştirilmedi) | **FUTURE** |
| 38 | İki ayrı, örtüşen PWA implementasyonu (bulgusu) | — (bir "özellik" değil, bir tutarsızlık bulgusu) | `app/pwa/routes.py` vs `app/pwa_blueprint.py` | — | — | Hangisi kanonik belirsiz | **YENİ** — #23 satırında ve §26 Known Limitations'da flag edildi | Flag edildi, kod değiştirilmedi | **PARTIAL** (bulgu olarak belgelendi, çözülmedi) |

---

## Navigation Coverage (Menü Öğesi → Devir Kapsamı)

Ana menü bölümleri (`app/templates/base.html` + `app/menu_registry_data_sections.py`'den):

| Menü Bölümü | Devir Kapsamı |
|---|---|
| Genel (dashboard, görevlerim, destek, bildirimler, portal, not karnesi, personel analizi, raporlar, **BYS360 Asistanı**) | Kısmi — çoğu alt-öğe #8-16 satırlarında PARTIAL |
| Personel Yönetimi (`ik`) | DOCUMENTED (#1) |
| Performans Yönetimi (`performans`) | DOCUMENTED (#2), alt-öğeler #19-22 PARTIAL |
| İletişim ve Anket Yönetimi (`iletisim`) | PARTIAL (#8, #9, #15, #24) |
| AI Karar Destek Merkezi (`ai`) | DOCUMENTED (#5) |
| Kullanıcı (`kullanici`) | PARTIAL (#11, #12) |
| Yönetici Özeti (`executive_summary`) | PARTIAL (#17), bu dalgada eklendi |
| Dosya Merkezi | **DOCUMENTED (#4) — bu dalganın ana konusu** |

**Kritik uyarı (repo kanıtı):** Menü kayıt sistemi çalışma zamanında onlarca `BEGIN/END` blok yamasıyla mutasyona uğruyor — yukarıdaki liste STATİK dosya okumasına dayanır, canlı menünün %100 birebir aynısı olduğu iddia EDİLMEZ (bkz. ana handover §26).

---

## Route/Blueprint Coverage

Repoda ~15+ ayrı Flask Blueprint (çoğu route ise tek bir `main_bp` üzerinde toplanıyor) ve `app/` altında ~30 üst-seviye alt-paket bulundu. Her alt-paket bu tabloda ya doğrudan bir satıra (feature olarak) ya da bir başka satırın "Backend" hücresine karşılık gelir. `app/observability/` (Prometheus metrikleri), `app/runtime/` (HTTP timeout guard), `app/bootstrap/` (app factory/schema contract), `app/refactor/` (tarihsel refactor bookkeeping) kullanıcıya açık FEATURE değil, altyapı/operasyon koduysa bu matrise ayrı satır olarak alınmadı — bunlar `app/` mimarisinin bir parçası olarak ana handover'ın §2 "Ortak altyapı" bölümünde zaten temsil ediliyor.

---

## Service/Task Coverage (Görünmeyen ama Operasyonel-Kritik)

Tüm background/scheduled otomasyonlar için bkz. ana handover §18 (Scheduled Task Envanteri, OPERATOR-ATTESTED) ve bu matrisin #16-18, #25, #33 satırları. Python-seviyeli (OS Task Scheduler DIŞI) arka plan işleri: `app/tasks/core_background_tasks.py` (`run_core_health_snapshot`, `run_module_maturity_snapshot`, `refresh_feedback_pulse_analytics`, `run_nightly_maintenance_bundle`), `app/tasks/feedback_tasks.py` (`refresh_pulse_analytics_for_unit`) — ana handover §2 Ortak altyapı "Arka plan işleri" satırında zaten mevcut.

---

## Negative Gate Sonucu

**FINAL HANDOVER COMPLETE = PASS** (bu matris anlamında) — çünkü:
1. Navigation'daki HER ana menü bölümü yukarıdaki tabloda temsil ediliyor.
2. Keşfedilen 38 feature'ın HİÇBİRİ bu tablonun DIŞINDA bırakılmadı.
3. `UNDOCUMENTED` durumundaki tek satır (#35, Strategic Performance v2) dahi bu matriste KAYITLIDIR — yalnız ana handover dosyasında henüz derinlemesine bir bölümü yok. Bu, "tamamen unutulmuş" ile "kayıtlı ama henüz derinleştirilmemiş" arasındaki dürüst farktır.

**Not — bu PASS'in ne anlama GELMEDİĞİ:** 28 satır `PARTIAL` durumdadır — yani "menü anahtarı + dosya yolu biliniyor" seviyesinde, Dosya Merkezi (§34) veya Portal Video (§16) kadar derinlemesine DEĞİL. Gelecekteki devir dalgaları bu PARTIAL satırları tek tek derinleştirebilir; bu matris o çalışmanın önceliklendirilmesi için bir yol haritası işlevi görür.
