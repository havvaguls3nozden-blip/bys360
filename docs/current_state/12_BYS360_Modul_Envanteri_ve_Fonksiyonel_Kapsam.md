Doküman Adı: BYS360 Modül Envanteri ve Fonksiyonel Kapsam
Doküman Türü: Teknik / Fonksiyonel Envanter
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası, yerel HEAD değil)
Son Güncelleme: 2026-09-02

---

## 1. Kapsam ve yöntem

Bu doküman, `app/` dizini altındaki her üst düzey Python paketini doğrudan dizin taraması ve kod okumasıyla envanterler (`CODE_VERIFIED`). Yetkilendirme ve denetim (audit) sütunları **yüksek düzeyde** tutulmuştur; derinlemesine yetkilendirme mimarisi `11_BYS360_Rol_Yetki_ve_Erisim_Kontrol_Modeli.md` belgesinin kapsamındadır. Bu envanter, `docs/handover/BYS360_MODUL_ENVANTERI.md` (mevcut temel/baseline belge, iş alanı bazlı ve üst düzey) ile karşılaştırılmış; §12'de karşılaştırma notu yer alır.

**Önemli, öncelikli uyarı — Puantaj:** Personel devam/mesai (Puantaj) modülü **bu inceleme kapsamında koddan doğrulanabilir, uçtan uca çalışan bir özellik olarak bulunamamıştır.** Puantaj **PLANLANAN / ONAYLANAN BİR SONRAKİ GELİŞTİRME**dir, halihazırda uygulanmış değildir. Bkz. §11 için önemli bir netleştirme: personel modülünde **izin/devamsızlık istisnası (leave/attendance-exception) takibi** zaten mevcuttur, ancak bu, tam bir Puantaj (giriş-çıkış saat takibi/mesai) sistemiyle **karıştırılmamalıdır** — ayrıntı §11'dedir.

## 2. Modül dizini haritası (özet tablo)

| Dizin | .py dosya sayısı | Genel işlev alanı |
|---|---|---|
| `app/about` | 2 | Kurumsal "Hakkında" sayfası |
| `app/account` | 2 | Kullanıcı hesap ayarları |
| `app/admin` | 32 | Sistem yönetimi, AI karar desteği yönetim ekranları, operasyon araçları |
| `app/ai` | 13 | AI karar desteği (özetleme/öneri) faz route'ları |
| `app/ai_agent` | 2 | Sanal asistan blueprint girişi |
| `app/api/mobile` | ~12 | Native mobil uygulama JSON API |
| `app/assistant_training_bank` | 0 (veri) | Asistan bilgi tabanı (JSON) |
| `app/auth` | 3 | Kimlik doğrulama |
| `app/communication` | 38 | Mesajlaşma, duyuru, anket, geri bildirim, e-posta |
| `app/core` | 6 | Çekirdek altyapı (sağlık kontrolü, loglama, izleme, tarih yardımcıları) |
| `app/dashboard` | 2 | Ana pano |
| `app/executive_summary` | 4 | Yönetici Özeti raporlama modülü |
| `app/file_center` | 7 | Dosya Merkezi (transfer/paylaşım/depolama) |
| `app/institutional` | 23 | Personel/İK yönetimi (organizasyon, izin, vekâlet, raporlar) |
| `app/main_handlers` | 11 | Ana sayfa/hesap/karşılaştırma iş mantığı yardımcıları |
| `app/modules/strategic_performance` | — | Stratejik performans (KPI/hedef/yetkinlik) |
| `app/modules/strategic_performance_dashboard` | — | Stratejik performans paneli (bkz. mimari doküman Ek §3) |
| `app/performance` | 63 (59 üst düzey + `rules/`/`services/` alt paketlerinde 4 yardımcı dosya — tümü "route dosyası" değildir, bkz. §6.1) | Performans değerlendirme (en büyük modül) |
| `app/portal` | 2 (+1005 satırlık routes.py) | Kurumsal sosyal portal (duvar/gönderi/grup) |
| `app/pwa` | 2 | PWA (installable web app) desteği |
| `app/refactor` | 19 | İç mimari/kalite sözleşme sabitleri (kullanıcıya yönelik özellik değil) |
| `app/security`, `app/services`, `app/support`, `app/tasks`, `app/observability`, `app/runtime`, `app/template_helpers`, `app/config` | — | Yatay (cross-cutting) altyapı katmanları |

## 3. Kimlik, Hesap ve Kimlik Doğrulama

### 3.1 `app/auth` — Kimlik Doğrulama

- **AMAÇ:** Giriş/çıkış, oturum yönetimi, parola sıfırlama.
- **ANA ÖZELLİKLER:** Sicil/e-posta ile giriş, `security_stamp` tabanlı oturum geçersiz kılma (`app/__init__.py:load_user` — parola sıfırlanırsa eski çerezler kademeli olarak geçersiz sayılır), yetki dekoratörleri (`app/auth/decorators.py`).
- **BAĞIMLILIKLAR:** Flask-Login, `app/security/passwords.py`, `app/security/captcha_guard.py`.
- **ÇEKİRDEK TABLOLAR:** `users` (`app/models/core_models.py`).
- **ANA ROUTE'LAR:** `app.auth.routes` → `main_bp` üzerine eklenir (ayrı blueprint değildir, bkz. DOC-02 §4).
- **YETKİLENDİRME SINIRI:** Girişsiz erişilebilen tek yüzey; sonrası tüm route'lar `@login_required`.
- **DENETİM SINIRI:** Giriş denemeleri `failed_login_attempts` sayacı ve CAPTCHA/throttle mekanizmasıyla sınırlanır; ayrı bir `audit_logs` kaydına yazıldığına dair kod kanıtı bu turda bulunamadı (`app/main_handlers/auth_handlers.py` içinde `AuditLog`/`write_audit_log`/`record_security_event` referansı yok) — doğru durum NOT_YET_FINALIZED'dir, bkz. DOC-05 §8.
- **DURUM:** Uygulanmış, canlı.

### 3.2 `app/account` — Hesap Ayarları

- **AMAÇ:** Kullanıcının kendi profil/iletişim/bildirim tercihlerini yönetmesi.
- **BAĞIMLILIKLAR:** `app/main_handlers/account_handlers.py`, `account_communication_helpers.py`, `account_settings_helpers.py`, `account_visibility_helpers.py`.
- **ÇEKİRDEK TABLOLAR:** `users` (profil alanları).
- **DURUM:** Uygulanmış, canlı.

### 3.3 `app/about` — Hakkında

- **AMAÇ:** Kurumsal tanıtım/versiyon bilgisi sayfası.
- **BAĞIMLILIKLAR:** `app/main_handlers/about_handlers.py`.
- **DURUM:** Uygulanmış, canlı.

## 4. Yönetim ve Sistem Ayarları

### 4.1 `app/admin` — Sistem Yönetimi

- **AMAÇ:** Kullanıcı/rol yönetimi, hiyerarşi yönetişimi, AI karar desteği yönetim ekranları, operasyonel araçlar (Ops).
- **ANA ÖZELLİKLER:** Kullanıcı CRUD, Excel personel içe aktarma (`load_workbook` ile), rol matrisi (`role_matrix_routes.py`), hiyerarşi yönetişimi (`hierarchy_governance_routes.py`), canlıya geçiş yardımcıları (`go_live_routes.py`), Ops sağlık/içe aktarma/performans/personel/kullanıcı-eylem servisleri (`ops_*_services.py`, `ops_routes.py`), 12 ayrı AI karar desteği faz route dosyası (`ai_phase2/5/6/7/8/9/10/11/12_routes.py`) + 8 tematik AI karar desteği route dosyası (`ai_decision_advanced/dashboard/foundation/governance/logs/policy/quality/recommendation/reporting_routes.py`).
- **BAĞIMLILIKLAR:** `app.route_registry.main_bp` (route'lar buraya eklenir — kendi `admin_bp`'si tanımlı ama canlıda **kayıtlı değildir**, bkz. DOC-02 Ek §1), `app/services/ai/*`, `app/services/auto_hierarchy_service.py`, `app/services/personnel/*`.
- **ÇEKİRDEK TABLOLAR:** `users`, `personnel_categories`, `organization_units`, `role_menu_defaults`, `system_settings`, `module_settings`, `unit_menu_profiles`, `settings_change_logs` (`app/models/settings_models.py`), `ai_request_logs`, `ai_recommendations`, `ai_feedback_logs`, `ai_redaction_rules`, `ai_summary_cache` (`app/models/ai_models.py`).
- **YETKİLENDİRME SINIRI:** `admin`/`super_admin`/`system_admin`/`sistem_yoneticisi` rol ailesi (ayrıntı DOC-11'de).
- **DENETİM SINIRI:** `audit_logs`, `settings_change_logs` (`app/models/audit_misc_models.py`, `app/models/settings_models.py`).
- **DURUM:** Uygulanmış, canlı. AI karar desteği fazlarının bir kısmının canlı kapsamda (`app/live_scope.py`) görünürlüğü kısıtlı olabilir — bkz. DOC-02 §11.

## 5. AI Karar Desteği ve Sanal Asistan

### 5.1 `app/ai` (+ `app/services/ai`, `app/services/ai_decision`) — AI Karar Desteği

- **AMAÇ:** Özetleme, önceliklendirme, risk farkındalığı, rapor yorumlama; **karar almaz**, öneri/özet üretir (kurumsal ilke — bkz. `05_BYS360_Guvenlik_Yetkilendirme_KVKK_ve_Denetim.md` §6, §15).
- **ANA ÖZELLİKLER:** Dashboard özet/brifing, HR izin brifingi, performans tutarlılık/özet analizleri, destek talebi triyajı, öneri uygulama/toplu uygulama, AI geri bildirim loglama (`app/ai/routes.py`), 11 "faz" route dosyası (`decision_support_faz1_ui_safe.py`, `faz3..faz12_routes.py`).
- **BAĞIMLILIKLAR:** `app/services/ai/client.py` (sağlayıcı anlık görüntüsü — `get_provider_snapshot`), `app/services/ai/guardrails.py` (`AIAccessDenied`, `AIInputError`, `AIResourceNotFound`, `AIServiceDisabled` — erişim/girdi/servis-kapalı korumaları).
- **ÇEKİRDEK TABLOLAR:** `ai_request_logs`, `ai_recommendations`, `ai_feedback_logs`, `ai_redaction_rules`, `ai_summary_cache`.
- **MİMARİ NOT:** Bu modülün route'ları `main_bp`'ye doğrudan eklenir (`app/ai/routes.py: from app.route_registry import main_bp`); ayrıca faz10/11/12 için tanımlanan alt-blueprint'lerin kayıt guard'ı bu dosyada tanımlı olmayan isimler arar — canlı erişilebilirlikleri bu incelemede tam doğrulanamadı (bkz. DOC-02 Ek §3, `NOT_YET_FINALIZED`).
- **DURUM:** Uygulanmış (çok sayıda fazlı iterasyonla), canlı kapsamda `ai_center` menü anahtarı altında görünür.

### 5.2 `app/ai_agent` (+ `app/services/ai_agent`, `app/assistant_training_bank`) — Sanal Asistan

- **AMAÇ:** Kullanıcı rehberliği, yetki kontrollü özet, güvenli yönlendirme kartları, teknik olmayan kurumsal cevap dili.
- **ANA ÖZELLİKLER:** `assistant_training_bank.json` (278 satır) içinde soru-cevap bilgi tabanı — örnek: "Dönemler nerede" → `/performance/periods` güvenli yönlendirmesi (`CODE_VERIFIED`). `app/services/assistant_role_matrix_v10.py`, `app/services/assistant_module_access.py`, `app/services/assistant_shortcut_visibility.py` — modül erişimi ve bağlam işlemcileri (uygulama başlangıcında opsiyonel kayıt, `app/__init__.py:OPTIONAL_STARTUP_REGISTRATIONS`).
- **YETKİLENDİRME SINIRI:** Asistanın gösterdiği kısayollar/özetler kullanıcının kendi rol/menü erişimiyle sınırlıdır (rol matrisi tabanlı görünürlük).
- **DURUM:** Uygulanmış, canlı (`assistant_center` ve alt menü anahtarları).

## 6. Performans Yönetimi (en büyük modül)

### 6.1 `app/performance` (+ `app/services/performance*`, `app/modules/strategic_performance*`)

- **AMAÇ:** Dönem/kapsam yönetimi, kriterler, amir zinciri (1./2./3. amir), puanlama, 70 altı Başkan/Üst Onay süreci, yayın ön onayı, karne/arşiv, raporlama, toplantı/geliştirme takip süreçleri, KPI/hedef/yetkinlik/öz değerlendirme (stratejik performans alt modülü).
- **ANA ÖZELLİKLER (59 üst düzey route dosyası + `rules/`/`services/` alt paketlerinde 4 yardımcı dosya = 63 `.py` dosyası toplam; seçili örnekler):** `evaluation_core_routes.py`, `assignment_rule_routes.py`, `low_score_process_routes.py` (70 altı süreç), `president_approval_card_routes.py` / `president_low_score_card_routes.py`, `engagement_*_routes.py` (geri bildirim/e-posta/yayın), `meeting_*_routes.py` (11 dosya — toplantı geliştirme fazları), `v2_1_1..v2_1_11_*_routes.py` (kategori/dönem kapsamı, canlı takip, hatırlatma merkezi), `history_import_routes.py`, `performance_archive_routes.py`, `reporting_routes.py`, `hierarchy_ui_routes.py`.
- **ALT PAKETLER:** `app/performance/rules/`, `app/performance/services/`.
- **STRATEJİK PERFORMANS ALT MODÜLÜ:** `app/modules/strategic_performance/` — `performance_target_periods`, `performance_targets`, `competency_library`, `role_competency_templates`, `self_reviews` tabloları (`CODE_VERIFIED`); ayrı bir `strategic_performance_bp` olarak `CORE_BLUEPRINT_SEQUENCE`'te **opsiyonel** kayıtlıdır. `app/modules/strategic_performance_dashboard/` ayrı bir panel Blueprint'i tanımlar; canlı kayıt durumu DOC-02 Ek §2'de netleştirilmemiş olarak işaretlenmiştir.
- **BAĞIMLILIKLAR:** `app/institutional` (izin/devamsızlık verisi, değerlendirme muafiyeti hesaplarını besler), `app/communication` (geri bildirim toplantıları, e-posta hatırlatmaları), `app/services/mail_performance_sender.py`.
- **ÇEKİRDEK TABLOLAR:** `performance_periods`, `performance_criteria`, `performance_weight_configs`, `performance_evaluations`, `performance_evaluation_items`, `evaluation_assignments`, `assignment_coverage_logs`, `performance_result_snapshots`, `performance_import_batches(_rows)`, `performance_publish_logs` (`app/models/performance_models.py`); ayrıca `performance_archived_results` (`performance_archive_models.py`), `performance_low_score_processes(_events)` (`performance_low_score_models.py`), `performance_process_flows(_steps)`, `performance_scoring_history`, `performance_president_approvals`, `performance_process_notifications`, `performance_feedback_pipeline_flows(_steps)` (`performance_process_engine_models.py`).
- **YETKİLENDİRME SINIRI:** Rol ailesi + amir hiyerarşisi tabanlı çok katmanlı yetki (personel/1. amir/2. amir/3. amir opsiyonel/Başkan) — ayrıntı DOC-11'de.
- **DENETİM SINIRI:** `performance_evaluation_history` (`audit_misc_models.py`), `performance_publish_logs`, `performance_scoring_history`.
- **ENTEGRASYONLAR:** E-posta (hatırlatma/yayın bildirimleri), AI karar desteği (özet/tutarlılık analizi), Sanal asistan (rehberlik kartları).
- **DURUM:** Uygulanmış, canlı, en olgun ve en geniş kapsamlı modül. Puantaj'ın canlıya alınmasıyla bu modülün "devam/mazeret muafiyeti" hesaplama mantığının (`minimum_presence_days_for_evaluation`, `leave_skip_threshold_days`, `absence_skip_threshold_days`, `auto_skip_if_fully_absent`) Puantaj verisiyle bütünleşmesi **gelecekteki bir entegrasyon konusudur** (bkz. §11).

## 7. Personel Yönetimi (İK)

### 7.1 `app/institutional` — Personel/İK Yönetimi

- **AMAÇ:** Organizasyon birimi yönetimi, izin/devamsızlık, vekâlet, personel özlük işlemleri, personel öz-hizmet talepleri, İK raporları.
- **ANA ÖZELLİKLER:** `hr_leave_attendance_routes.py` (izin/devamsızlık), `hr_personnel_delegation_routes.py` (vekâlet), `hr_personnel_extension_routes.py`, `hr_personnel_operations_routes.py`, `hr_personnel_phase10..13_routes.py`, `hr_personnel_analytics_routes.py`, `hr_personnel_reports_routes.py`, `hr_reports_routes.py`, `hr_request_analytics_routes.py`, `hr_request_task_routes.py` (öz-hizmet talep/görev takibi), `org_unit_routes.py`, `publication_routes.py`, `hr_live_p0_shims.py` (canlı eksik-uç noktalar için geçici uyumluluk katmanı).
- **ÇEKİRDEK TABLOLAR:** `organization_units`, `organization_unit_versions`, `employee_org_assignment_history` (`org_models.py`); `leave_balances`, `personnel_leaves`, `attendance_exceptions`, `delegation_assignments`, `personnel_document_categories(_documents)`, `personnel_self_service_request_*` (10 tablo — şablon/talep/ek/log/görev/SLA/eskalasyon), `personnel_position_histories`, `personnel_asset_assignments`, `personnel_checklist_*`, `personnel_lifecycle_cases(_tasks)`, `personnel_exit_interviews`, `personnel_handover_records(_items)`, `personnel_approval_stations`, `personnel_digital_handover_documents`, `personnel_exit_risk_assessments` (`hr_models.py` — toplam 30 tablo, İK en zengin ikinci tablo grubudur).
- **BAĞIMLILIKLAR:** `performance_periods` (izin kayıtları dönem bazlı ilişkilendirilir), `app/services/personnel/*`.
- **YETKİLENDİRME SINIRI:** `admin_users`, `org_units`, `hr_leave_tracking` canlı kapsam anahtarları; genişletilmiş İK ekranları (`hr_management`, `hr_reports`, `personnel_*`) `app/live_scope.py`'de zaman içinde daralıp genişletilmiş (bkz. §11).
- **DENETİM SINIRI:** `personnel_status_history`, `personnel_process_notes`, `settings_change_logs` üzerinden dolaylı; ayrıntı DOC-11'de.
- **DURUM:** Uygulanmış, canlı — **ama Puantaj (devam/mesai saat takibi) bu modülün bir parçası değildir**, bkz. §11.

## 8. İletişim, Anket ve Geri Bildirim

### 8.1 `app/communication` (+ `app/services/communication*`, `app/services/cic`)

- **AMAÇ:** Mesajlaşma, duyuru/bildirim, anket, geri bildirim/nabız, destek talepleri, e-posta ve zamanlanmış hatırlatmalar, kurumsal bilgi merkezi (CIC).
- **ANA ÖZELLİKLER (38 route dosyası):** `messages_*_routes.py` (çekirdek/ek/etkileşim), `announcements_*_routes.py`, `announcement_popup_routes.py`, `feedback_*_routes.py` (aksiyon planı/analitik/kampanya/çekirdek/toplantı), `surveys_*_routes.py`, `notifications_*_routes.py`, `corporate_information_center_routes.py`, `daily_weather_mail_routes.py`, `executive_mail_center_v2_routes.py`, `phase1..phase9d_routes.py` (10 fazlı iletişim genişlemesi).
- **ÇEKİRDEK TABLOLAR:** `message_threads(_participants)`, `messages`, `message_reactions(_comments)`, `message_typing_states`, `message_attachments`, `notifications`, `surveys`, `survey_questions(_options)`, `survey_assignments(_responses)(_answers)`, `feedback_requests`, `mail_logs`, `evaluation_publish_logs`, `feedback_meetings` (`communication_models.py`); `announcements`, `announcement_reads` (`announcement_popup_models.py`); `feedback_campaigns`, `feedback_questions(_options)`, `feedback_campaign_assignments`, `feedback_submissions(_answers)`, `feedback_pulse_entries`, `feedback_action_plans` (`feedback_models.py`); `support_categories`, `support_tickets(_messages)(_attachments)(_status_history)`, `support_feedback_ratings`, `support_help_articles` (`support_models.py`); ayrıca 5 fazlı ek tablo grubu (`communication_phase1..5_models.py` — toplam 19 ek tablo: bülten, anket şablonu, SLA politikası, yönetici raporu, dijest/eskalasyon/saklama politikası vb.).
- **BAĞIMLILIKLAR:** `app/services/mail_core.py`, `app/services/cic/*` (kurumsal bilgi merkezi), `app/support` (destek talebi çekirdek modeli paylaşımlı).
- **ENTEGRASYONLAR:** SMTP (`MAIL_SERVER`/`SMTP_HOST` ortam değişkenleri — bkz. DOC-16), performans modülü (geri bildirim toplantıları).
- **DURUM:** Uygulanmış, canlı, çok fazlı (aşamalı) geliştirme deseni bu modülde en belirgin olanıdır.

### 8.2 `app/support` — Destek Merkezi

- **AMAÇ:** Kullanıcı destek talepleri ve yardım merkezi içeriği.
- **BAĞIMLILIKLAR:** `app/support/help_center_content.py`; `main_bp`'ye eklenir (`app.route_registry.MODULAR_ROUTE_MODULES` listesinde).
- **DURUM:** Uygulanmış, canlı (`support_index`, `support_new`, `support_my_tickets`, `support_assigned`, `support_all` menü anahtarları).

## 9. Dosya Merkezi

### 9.1 `app/file_center`

- **AMAÇ:** Kurum içi dosya depolama, transfer, paylaşım bağlantıları, talep bazlı yükleme.
- **ANA ÖZELLİKLER:** `services.py`, `permissions.py` (izin modeli), `maintenance_service.py`, `settings_service.py`, `mail_service.py`.
- **ÇEKİRDEK TABLOLAR:** 19 tablo — `file_storage_folders(_items)`, `file_transfers(_items)(_recipients)`, `file_share_links`, `file_requests(_uploads)`, `file_download_logs`, `file_access_logs`, `file_quota_usage(_policies)`, `file_security_scans`, `file_audit_logs`, `file_upload_sessions(_chunks)`, `file_center_mail_logs`, `file_center_role_permissions`, `file_center_settings` (bu oturumda doğrudan sayıldı, `docs/handover/DATABASE_MIGRATION.md`'deki 19 rakamıyla tutarlı — `CODE_VERIFIED`).
- **DENETİM SINIRI:** `file_audit_logs`, `file_access_logs`, `file_download_logs` — dosya bazlı ayrıntılı denetim izi.
- **DURUM:** Uygulanmış, canlı. Dosya Merkezi izin/audit/rollback maddelerinde açık teknik defterin bulunduğu bilinmektedir — ayrıntı `19_BYS360_Acik_Teknik_Madde_ve_Finalizasyon_Defteri.md` belgesindedir, bu belge yalnızca modülün varlığını ve tablo sayısını doğrular.

## 10. Portal, PWA, Dashboard, Yönetici Özeti

### 10.1 `app/portal` — Kurumsal Sosyal Portal

- **AMAÇ:** Kurum içi sosyal duvar — gönderi, grup, yorum, tepki, moderasyon.
- **ANA ÖZELLİKLER:** `routes.py` (1005 satır — dizindeki en büyük tekil route dosyalarından biri), profil/grup/gönderi/yorum/tepki/kaydetme/rapor/moderasyon/sabitleme/aktivite akışı.
- **ÇEKİRDEK TABLOLAR:** 15 tablo — `portal_profiles`, `portal_groups(_members)`, `portal_posts`, `portal_post_audiences(_attachments)(_reactions)(_comments)`, `portal_comment_reactions(_mentions)`, `portal_saved_posts`, `portal_post_reports`, `portal_moderation_logs`, `portal_pinned_posts`, `portal_activity_logs` (`portal_models.py`).
- **MİMARİ NOT:** `app/config/removed_modules.py` içinde `portal` anahtarı `REMOVED_MODULES["portal"] = False` olarak işaretlidir — yani **kaldırılmamıştır, canlıda aktif kabul edilir** (`CODE_VERIFIED`). Route kaydı `is_module_removed("portal")` kontrolüne bağlı olarak koşullu yapılır (`app/route_registry.py:32-33`).
- **DURUM:** Uygulanmış, canlı.

### 10.2 `app/pwa` (+ `app/pwa_routes.py`, `app/pwa_blueprint.py`) — PWA Desteği

- **AMAÇ:** Yüklenebilir web uygulaması desteği (manifest/service worker).
- **DURUM:** Uygulanmış, canlı; `pwa_bp` `app/__init__.py:97`'de kayıtlıdır.

### 10.3 `app/dashboard` — Ana Pano

- **AMAÇ:** Kullanıcı rolüne göre özetlenmiş ana pano.
- **BAĞIMLILIKLAR:** `app/main_handlers/dashboard_handlers.py`, `app/performance/*`, `app/institutional/*` verilerini özetler.
- **DURUM:** Uygulanmış, canlı.

### 10.4 `app/executive_summary` — Yönetici Özeti

- **AMAÇ:** Üst yönetim için özet raporlama ve otomatik e-posta dağıtımı.
- **ANA ÖZELLİKLER:** `service.py`, `mail_engine.py` (SMTP entegrasyonu, `MAIL_SERVER`/`SMTP_HOST`).
- **BAĞIMLILIKLAR:** Ayrı bir `executive_summary_bp` olarak `app/__init__.py:216`'da (try/except korumalı, hata durumunda sessizce atlanabilir) kaydedilir.
- **ENTEGRASYONLAR:** Windows Scheduled Task ile zamanlanmış çalıştırma (`scripts/windows/register_bys360_executive_summary_tasks_v2_14_1/3.ps1`, `run_executive_summary_0001/0830.ps1`).
- **DURUM:** Uygulanmış, canlı.

## 11. Puantaj — mevcut durum netleştirmesi (kritik bölüm)

Puantaj'ın **halihazırda uygulanmış** bir özellikmiş gibi sunulması yanlış olur. Kod taraması şu sonucu vermiştir:

- `app/` altında `"puantaj"` (case-insensitive) geçen **tek** dosya `app/services/ai_agent/assistant_full_live_usage_guide_v2.py`'dir; burada "puantaj" kelimesi, sanal asistanın arama anahtar kelimeleri listesinde **"Devamsızlık ve istisna kayıtları"** konusuna eşanlamlı bir arama terimi olarak geçer: `("devamsızlık", "devamsizlik", "puantaj", "attendance", "istisna", "mazeret", "geç kalma", "gec kalma")` (`CODE_VERIFIED` — satır 338). Yani sistemde "puantaj" yazıp arayan bir kullanıcı, asistan tarafından **mevcut** devamsızlık/istisna kayıtları ekranına yönlendirilir — bu, **gerçek bir Puantaj modülünün varlığı anlamına gelmez**, yalnızca terim eşleştirmesidir.
- `"timesheet"` (İngilizce) hiçbir dosyada geçmemektedir (`CODE_VERIFIED`).
- Personel modülünde (`app/models/hr_models.py`) gerçekten var olan ve bu terimle karıştırılabilecek modeller: `LeaveBalance` (`leave_balances`), `PersonnelLeave` (`personnel_leaves`), `AttendanceException` (`attendance_exceptions`), `DelegationAssignment` (`delegation_assignments`). Bunlar **izin bakiyesi, izin talebi, devamsızlık istisnası (mazeret/geç kalma vb. tek günlük/kısmi günlük kayıtlar) ve vekâlet** takibidir; her biri performans değerlendirmesini etkileyen alanlar taşır (`blocks_performance_evaluation`, `performance_mode`, `day_fraction`) — yani bu veri modelinin asıl amacı **performans değerlendirme muafiyeti hesaplamasını beslemektir**, bağımsız bir zaman/mesai (giriş-çıkış saat, fazla mesai, resmi tatil/vardiya) yönetim sistemi **değildir**.

**Sonuç:** Puantaj (tam personel devam/mesai sistemi — giriş-çıkış saat kaydı, vardiya, fazla mesai, bordroya veri besleme vb.) bu incelemenin kapsamında **PLANLANAN / ONAYLANAN BİR SONRAKİ GELİŞTİRME** olarak doğrulanmıştır; herhangi bir kısmi/gömülü Puantaj alt sistemi bulunmamıştır. Var olan tek yakın kavram, izin/devamsızlık **istisna** kaydıdır ve bu zaten performans modülüyle entegredir — bu ayrım gelecekteki Puantaj tasarımında **çakışma/yeniden isimlendirme riski** taşıdığından (örn. "devamsızlık istisnası" ile "puantaj kaydı" kavramlarının kullanıcı arayüzünde birbirine karışması), Puantaj geliştirme fazına geçmeden önce ürün/iş analizi düzeyinde netleştirilmesi önerilir.

## 12. `docs/handover/BYS360_MODUL_ENVANTERI.md` (baseline) ile karşılaştırma

Baseline belge (60 satır) iş alanı bazlı, kod dizini bazlı değildir; şu üst düzey alanları listeler: **Ana omurga** (kimlik/rol/ayarlar/audit/bildirim), **Personel Yönetimi**, **Performans Yönetimi**, **İletişim ve Anket Yönetimi**, **AI Karar Destek**, **Sanal Asistan**, **Mobil** (Flutter native, API tabanlı ekranlar). Bu incelemede bu alanların tümü kod tabanında karşılığı bulunarak doğrulanmıştır (`CODE_VERIFIED`); baseline belgede **fazladan/eksik bir modül iddiası tespit edilmedi** — belge güncel HEAD ile çelişmiyor, yalnızca çok daha az ayrıntılıdır (kod dizini/tablo/route dosyası düzeyine inmez). Baseline'da **Puantaj hiç anılmamaktadır** — bu da mevcut kod durumuyla tutarlıdır.

## 12a. Tasarım standardıyla ilişki

Yukarıdaki tüm modüller aynı kurumsal görsel kimliği ve arayüz standardını paylaşır — bkz. `docs/current_state/20_BYS360_Kurumsal_Tasarim_ve_Arayuz_Standardi.md`. Hiçbir modül bağımsız bir görsel dil oluşturmamalıdır (DOC-20 §12).

## 13. Yatay (cross-cutting) altyapı katmanları — özet

Kullanıcıya doğrudan görünen bir "modül" olmayan, tüm modüllerin üzerine kurulduğu katmanlar: `app/security/` (17 dosya — CSRF, CAPTCHA, parola, TCKN şifreleme, yükleme güvenliği, hız sınırlama, güvenlik başlıkları), `app/services/` (en büyük dizin — iş mantığı servisleri, alt paketler: `ai/`, `ai_agent/`, `ai_decision/`, `analytics_center/`, `cic/`), `app/support/`, `app/tasks/` (arka plan görevleri — `core_background_tasks.py`, `feedback_tasks.py`), `app/observability/` (`prometheus_metrics.py`), `app/runtime/` (`http_timeout_guard.py`), `app/template_helpers/`, `app/config/` (canlı kapsam/menü/yayın manifesti). `app/refactor/` (19 dosya) kullanıcıya yönelik bir özellik değildir — iç mimari/kalite kapıları için sözleşme sabitleri ve "faz" hedef listeleri tutar (`CODE_VERIFIED`, dosya adları: `faz1e_deletion_allowlist.py`, `final_quality_*_contract.py`, `hotfix_merge_registry.py`, `phase_alias_manifest.py` vb.).

---

## Ek — Bu belgede tespit edilen, izlenmesi gereken bulgular

1. **Puantaj bulunmamaktadır** — yalnızca asistan arama anahtar kelimesi olarak "puantaj" geçer, gerçek bir modül değildir (bkz. §11). Bu, yanlış anlaşılmaya çok açık bir nokta olduğundan kurumsal iletişimde özellikle vurgulanmalıdır.
2. `admin_bp` (tanımlı, canlıda kayıtsız) ve `strategic_performance_dashboard_bp` (kayıt çağrısı bulunamadı) ile ilgili gözlemler DOC-02'de detaylandırılmıştır; modül envanteri açısından pratik etkisi, bu iki alt sistemin canlıda erişilebilirliğinin **ek doğrulama gerektirmesidir** (`NOT_YET_FINALIZED`).
3. `app/institutional`'daki izin/devamsızlık/vekâlet veri modeli ile gelecekteki Puantaj modülü arasında kavramsal çakışma riski (§11) — ürün tasarımı aşamasında netleştirilmesi önerilir.
