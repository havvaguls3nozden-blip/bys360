Doküman Adı: BYS360 Güvenlik, Yetkilendirme, KVKK ve Denetim Dokümanı
Doküman Türü: Güvenlik
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası, yerel HEAD değil)
Son Güncelleme: 2026-09-02

---

## 1. Kapsam ve amaç

Bu doküman, BYS360'ın kimlik doğrulama, yetkilendirme, rol/menü/kişi/birim kapsam modeli, hassas veri koruması, yapay zekâ (AI) veri sınırları, denetim (audit) kaydı, güvenli yapılandırma, sır (secret) yönetimi, ağ maruziyeti, sürüm bütünlüğü ve KVKK yaklaşımını **kod düzeyinde doğrulanmış** olgularla anlatır. Aşağıdaki her iddia, mümkün olduğunca dosya:satır referansıyla CODE_VERIFIED olarak işaretlenmiştir; doğrudan kod okunarak teyit edilemeyen kısımlar DOCUMENTATION_DERIVED veya NOT_YET_FINALIZED olarak ayrıca belirtilmiştir.

**Sertifikasyon uyarısı:** Bu belge; ISO 27001, ISO 42001 sertifikasyonu, bağımsız penetrasyon testi veya "KVKK uyumlu" (certified) statüsü **iddia etmez**. Repo içinde böyle bir sertifikasyon kanıtı (denetim raporu, sertifika numarası, akredite kuruluş adı) bulunmamıştır. Kullanılan ifadeler yalnızca "ISO 27001 ilkeleriyle uyum hedefi", "KVKK kapsamında veri minimizasyonu ve yetki sınırlaması yaklaşımı", "uyum yaklaşımı", "destekleyici teknik tedbir" düzeyindedir.

---

## 2. Kimlik doğrulama (Authentication)

- Flask-Login 0.6.3 tabanlı oturum yönetimi (CODE_VERIFIED, `requirements.txt`).
- Giriş formu; sicil no veya e-posta + şifre ile çalışır (`app/main_handlers/auth_handlers.py:160-165`).
- **Brute-force koruması, çok katmanlı:**
  - IP ve kimlik (identity) bazlı deneme sınırlama: `LOGIN_IP_MAX_ATTEMPTS=12`, `LOGIN_IDENTITY_MAX_ATTEMPTS=6`, `LOGIN_LOCKOUT_MINUTES=15` (CODE_VERIFIED, `config.py:631-633`).
  - Aritmetik CAPTCHA eşiği: `LOGIN_CAPTCHA_THRESHOLD=3` (varsayılan) — başarısız deneme sayısı eşiği aştığında devreye girer (CODE_VERIFIED, `config.py:638`; captcha üretim/doğrulama `app/route_support.py:474-486`).
  - Başarısız girişte kullanıcı bazlı sayaç (`user.failed_login_attempts`) artırılır, eşik aşılınca `captcha_required` bayrağı DB'ye yazılır (CODE_VERIFIED, `app/main_handlers/auth_handlers.py:175-194`).
  - Bilinmeyen kullanıcı adı için de zorunlu CAPTCHA seçeneği vardır (`LOGIN_FORCE_CAPTCHA_FOR_UNKNOWN_USER`, varsayılan `True`) — kullanıcı numaralandırma (enumeration) saldırılarını zorlaştırır (CODE_VERIFIED, `app/main_handlers/auth_handlers.py:184`).
- Mobil giriş uç noktası (`/api/mobile/auth/login`) için ayrı/özel bir throttle mekanizması **yoktur**; yalnızca genel oran sınırlamasına (rate limit) tabidir. Bu, önceki devir belgesinde de bilinçli kabul edilmiş bir risk olarak işaretlenmiştir (DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:860`) — mevcut HEAD'de ayrıca doğrulanmadı, REQUIRES_FINAL_REFRESH.

## 3. Yetkilendirme mimarisi — tek karar zinciri

BYS360'da iki tamamlayıcı yetkilendirme mekanizması vardır; ikisi de `app/route_support.py` içinde toplanmıştır (CODE_VERIFIED, dosya bu HEAD'de okunmuştur):

### 3.1 Rol ailesi tabanlı decorator'lar

```
ADMIN_FAMILY_ROLES   = {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"}
MANAGER_FAMILY_ROLES = ADMIN_FAMILY_ROLES | {"birim_sorumlusu", "koordinator"}
PORTAL_EDITOR_ROLES  = ADMIN_FAMILY_ROLES | {"koordinator"}
```
(CODE_VERIFIED, `app/route_support.py:66-70`)

`admin_required`, `manager_required`, `portal_editor_required` decorator'ları bu rol ailelerine göre 403 (`render_access_denied()`) döner (CODE_VERIFIED, `app/route_support.py:443-471`). `app/auth/decorators.py` bu decorator'ları geriye-dönük uyumluluk için `app.route_support`'tan yeniden dışa aktaran ince bir alias katmanıdır (CODE_VERIFIED, `app/auth/decorators.py:1-12`) — gerçek kaynak `app/route_support.py`'dir.

`User.role` alanı, ayrı bir Role tablosuna FK değil, serbest metin bir string kolonudur (varsayılan `"personel"`) (CODE_VERIFIED, `app/models/core_models.py:59`).

### 3.2 Canlı menü yetki haritası (`menu_key_required`) — admin bypass YOK

Bu, BYS360'ın en önemli yetkilendirme kararıdır ve doğrudan kodda doğrulanmıştır:

```python
# app/route_support.py:424-436
def menu_key_required(menu_key: str):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("main.login"))
            # BYS360_SETTINGS_LIVE_AUTHORITY_V2:
            # Admin/üst rol bypassı kaldırıldı. Bir route menu_key_required ile
            # korunuyorsa son karar da Ayarlar > Rol Matrisi / kişi-birim
            # görünürlüğünden gelen canlı menü haritasıdır.
            if not can_access_menu(current_user, menu_key):
                return render_access_denied()
            return view_func(*args, **kwargs)
        return wrapper
    return decorator
```

`can_access_menu(user, menu_key)` → `build_menu_visibility_map(user).get(menu_key, False)` (CODE_VERIFIED, `app/route_support.py:404-421`). Yani `menu_key_required` ile korunan bir route'ta **admin rolü otomatik geçiş hakkı vermez** — son karar DB'deki (`role_menu_defaults` → `unit_menu_profiles` → `user_menu_permissions`) canlı görünürlük katmanına aittir. Bu bulgu, önceki devir belgesindeki aynı tespiti (`docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:1584`) bağımsız olarak doğrular.

**Tek, dar kapsamlı istisna (CODE_VERIFIED):** `app/services/settings/effective_menu_parts/public_build_context.py:9-27` — `apply_admin_period_reminder_public_build_wrapper`, yalnızca admin-ailesi kullanıcılar için **üç spesifik menü anahtarını** (`performance_period_management_center`, `performance_evaluator_reminder_center`, `performance_evaluation_live_tracking` + üst kategori anahtarları) rol matrisi/kişi override kapatsa bile görünür tutar. Bu, eski/stale kapalı kayıtların adminin kendi yönetim ekranlarını görmesini engellemesini önleyen dar bir **menü görünürlük** düzeltmesidir — genel bir "admin her şeyi görür" kuralı değildir ve backend route yetkilendirmesini (ör. `admin_required`) etkilemez; ilgili route'lar ayrıca kendi rol-ailesi decorator'larına tabidir.

### 3.3 Katmanlı menü otoritesi

Yorum satırında açıkça belgelenen sıra: **Rol matrisi tabanı → birim profili → kişi özel ayarı → teknik/rol güvenlik kapısı** (CODE_VERIFIED, `app/services/settings/effective_menu.py:135-139`). Karşılık gelen modeller: `RoleMenuDefault`, `UnitMenuProfile`, `UserMenuPermission` (CODE_VERIFIED, `app/models/settings_models.py:13,70`; `app/models/core_models.py:386`).

Karar motoru fiziksel olarak `app/services/settings/effective_menu.py` (299 satır, facade) + `app/services/settings/effective_menu_parts/` alt paketi (12 dosya, ~3064 satır) içine dağılmıştır; ~8 ardışık "wrapper" fonksiyonu `build_menu_visibility_map` değişkenini sırayla sarar (CODE_VERIFIED, dosya doğrudan okunmuştur). Bu, bakım açısından karmaşık ama davranışsal olarak izlenebilir bir zincirdir — her sarmalayıcı blok kod içi `BYS360_...` etiketleriyle işaretlidir.

**Bilinen kısıt (önceki devir belgesinden doğrulanmış, DOCUMENTATION_DERIVED):** `/admin/role-matrix` salt-okunur referans ekranı (`app/services/role_matrix_ui_service.py`) tamamen kod-içi sabit (hardcoded) veri render eder ve **canlı DB durumunu yansıtmaz**. Gerçek görünürlük her zaman `role_menu_defaults`/`unit_menu_profiles`/`user_menu_permissions` tablolarındaki güncel kayıtlara göre belirlenir. Bu iki ekran arasında bir "drift" riski olarak açıkça belgelenmiştir (`docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:1623-1624`).

## 4. Rol/kişi/birim kapsam görünürlüğü

Örgüt yapısı `OrganizationUnit`, `OrganizationUnitVersion`, `EmployeeOrgAssignmentHistory` modelleriyle temsil edilir (CODE_VERIFIED, `app/models/org_models.py`). Görünürlük ilkesi (DOCUMENTATION_DERIVED, `docs/handover/BYS360_GUVENLIK_KVKK_NOTLARI.md:16-24`, bu current-state fazında kod düzeyinde ayrıca teyit edilmedi — REQUIRES_FINAL_REFRESH kişi/birim sorgu filtrelerinin her modülde ayrı ayrı doğrulanması için):

| Kullanıcı | Görünürlük |
|---|---|
| Personel | Kendi verisi ve kişi detaysız grup özeti |
| Amir | Görevli olduğu personel ve yetki kapsamı |
| Koordinatör/Grup Başkanı | Kendi organizasyon kapsamı |
| Başkan/Admin | Rolüne göre genel görünürlük |

## 5. Hassas kayıtlar — sağlık raporları, performans verileri

- Performans değerlendirme geçmişi ayrı bir tabloda (`PerformanceEvaluationHistory`) tutulur; aktör, seviye, durum geçişi ve skor anlık görüntüsü (JSON) kaydedilir (CODE_VERIFIED, `app/models/audit_misc_models.py:26-43`).
- Performans arşivi ayrı model/şablon setiyle yönetilir (`app/models/performance_archive_models.py`) (DOCUMENTATION_DERIVED, önceki devir belgesi §17, bu turda ayrıca doğrulanmadı).
- Sağlık raporu alanına özgü ayrı bir erişim-kısıtlama katmanı bu oturumda kod düzeyinde ayrıca aranmadı — NOT_YET_FINALIZED.
- KVKK notları belgesinde belirtilen "hassas performans verileri yayın/onay tamamlanmadan açılmaz" ilkesi (DOCUMENTATION_DERIVED, `docs/handover/BYS360_GUVENLIK_KVKK_NOTLARI.md:11`) menü/backend düzeyinde bu fazda tekil olarak yeniden doğrulanmadı — REQUIRES_FINAL_REFRESH.

## 6. AI veri sınırları — insan denetimi zorunlu, karar yetkisi yok

`app/services/ai/visibility_gate.py`, AI ekranlarının yetki/KVKK maskeleme/güvenli görünürlük sözleşmesini tanımlar; modül docstring'i açıkça "Ham istem/yanıt metni döndürmez, öneri uygulamaz, kayıt oluşturmaz, kayıt güncellemez ve nihai idari karar vermez" der (CODE_VERIFIED, `app/services/ai/visibility_gate.py:23-29`). Sözleşme sabitleri (CODE_VERIFIED, aynı dosya satır 31-40):

```python
DB_WRITE_ENABLED = False
AI_FINAL_DECISION_ENABLED = False
AI_AUTO_APPLY_ENABLED = False
RAW_AI_PAYLOAD_VISIBLE = False
RAW_AI_EXPORT_ENABLED = False
SAFE_CSV_EXPORT_ENABLED = True
KVKK_MASKING_REQUIRED = True
PERSONAL_DATA_EXPORT_ENABLED = False
HUMAN_REVIEW_REQUIRED = True
```

Hassas alan takma adları (`SENSITIVE_FIELD_ALIASES`, satır 48-64) TC/TCKN, kimlik, sicil, telefon, e-posta, IBAN, ad/soyad, adres gibi alanları kapsar — maskeleme bu alan listesine göre uygulanır.

**Varsayılan AI sağlayıcı modu "stub"tur, gerçek dış servise bağlı değildir:**
```python
AI_PROVIDER_MODE = os.getenv('AI_PROVIDER_MODE', 'stub')
AI_PROVIDER_NAME = os.getenv('AI_PROVIDER_NAME', 'internal_stub_plus')
AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'bys360-ai-stub-v2')
```
(CODE_VERIFIED, `config.py:722-724`) — üretim ortamında gerçek bir sağlayıcıya bağlanmak, ortam değişkeni ile açık bir yapılandırma değişikliği gerektirir; varsayılan davranış dışsal AI çağrısı yapmaz.

## 7. Redaksiyon (maskeleme)

`app/services/ai/redaction.py` — e-posta ve uzun sayı (TC/telefon benzeri) maskeleme fonksiyonları (`_mask_email`, `_mask_long_number`, `redact_text`, `redact_payload`) (CODE_VERIFIED, dosya doğrudan okunmuştur). Yönetim ekranı: `app/templates/admin_ai_redaction_rules.html`. `AIRedactionRule` modeli, kural bazlı maskelemenin DB'den yönetilebildiğini gösterir (CODE_VERIFIED, `app/services/ai/visibility_gate.py:16` import listesi).

## 8. Denetim kayıtları (Audit log)

- Tek bir merkezi tablo: `audit_logs` (`AuditLog` modeli) — `user_id`, `action`, `entity_type`, `entity_id`, `old_data_json`, `new_data_json`, `summary`, `endpoint`, `ip_address` alanlarıyla (CODE_VERIFIED, `app/models/audit_misc_models.py:6-23`).
- Yazma katmanı: `app/services/audit_service.py::write_audit_log()` (CODE_VERIFIED, dosya doğrudan okunmuştur) — istek endpoint'i ve IP adresini otomatik ekler.
- Güvenlik olayları için ayrı bir üst katman: `app/services/audit_event_service.py::record_security_event()` — aynı `audit_logs` tablosuna, varsayılan `entity_type="security_event"` ile yazar (yani **ayrı bir tablo değil**, aynı tabloda `entity_type`/`action` ile ayrışan kayıtlardır); istek bağlamı (method, path, endpoint, IP, user-agent) ve aktör (user_id, role) bilgisini otomatik ekler; DB yazımı başarısız olursa canlı isteği bozmadan yalnızca uygulama logına düşer (CODE_VERIFIED, `app/services/audit_event_service.py:30-76`).
- **Kapsam gözlemi:** Denetim kaydı ilk bakışta tek bir merkezi tabloya yazılıyormuş gibi görünebilir; ancak yapılan teknik incelemede bunun doğru olmadığı, birbirinden bağımsız **üç ayrı** denetim mekanizması bulunduğu tespit edilmiştir:
  1. **Merkezi `audit_logs` tablosu** (`AuditLog` modeli) — yalnızca `app/services/audit_service.py::write_audit_log()` (çağıranı: `app/services/audit_event_service.py::record_security_event()`, yalnızca `app/bootstrap/operational_guards.py` içinden tetiklenir) ve Performans modülünün `app/services/performance/feedback_audit_service.py:146`, `period_delete_service.py:204` dosyalarınca doğrudan kullanılır.
  2. **Dosya Merkezi'nin kendi tablosu** (`FileAuditLog` modeli, `file_audit_logs` tablosu, `app/models/file_center_models.py`) — `app/file_center/services.py:261`, `maintenance_service.py:64,146,167` tarafından yazılır; merkezi `audit_logs` ile **karıştırılmamalıdır**.
  3. **Performans vekâlet/zincir denetimi** (`AssignmentAuditLog` modeli, `app/services/performance/models_phase5_template.py:44`) — `app/services/performance/delegation.py:264`, `effective_chain.py:203` tarafından yazılır; bu da merkezi `audit_logs`'tan **ayrı** bir tablodur.

  Doğru ifade şudur: "Dosya Merkezi ve Performans modülünün kritik state-change akışları, **kendi ayrı denetim tablolarında** (`file_audit_logs`, ilgili performans denetim tabloları) izlenir; bootstrap güvenlik olayları ve bir kısım performans akışı **merkezi** `audit_logs` tablosunda izlenir. 'Her state-change tek bir merkezi audit tablosunda izlenir' biçimindeki bir genelleme yanlış olur."
- Ayrıca, Ayarlar/Rol Matrisi değişiklikleri için **özel bir değişiklik günlüğü** vardır: `SettingsChangeLog` (`settings_change_logs` tablosu) — aktör, hedef kullanıcı/rol/birim, `change_scope`, `action_type`, önceki/yeni durum (JSON) ve **geri alma (rollback) izlenebilirliği** (`reverted_from_log_id`, `is_rollback`) içerir (CODE_VERIFIED, `app/models/settings_models.py:89-108`). Bu, yetki/menü değişikliklerinin kendisinin de denetlenebilir ve geri alınabilir olduğunu gösterir.
- Başarısız giriş denemeleri bir sayaç alanında (`User.failed_login_attempts`) izlenir ve throttle/captcha tetikler (bkz. §2), ancak her başarısız giriş denemesinin ayrıca `audit_logs`'a satır olarak yazıldığına dair kod kanıtı bu turda bulunmadı — NOT_YET_FINALIZED.

## 9. Veri minimizasyonu ve KVKK ilkeleri (uyum yaklaşımı)

BYS360, aşağıdaki teknik tedbirlerle KVKK'nın veri minimizasyonu ve yetki sınırlaması ilkelerine **uyum yaklaşımını** destekler (CODE_VERIFIED bulgular, sertifikasyon iddiası değildir):

- Rol/menü/kişi/birim bazlı erişim kısıtlaması (bkz. §3-4).
- AI panellerinde ham veri dışa aktarımı kapalı, KVKK maskeleme zorunlu (bkz. §6-7).
- `.env`, DB dump ve loglar release paketine girmez (bkz. §10-11).
- Audit iz sürülebilirliği kritik akışlarda mevcuttur (bkz. §8).

## 10. Güvenli yapılandırma — çalışma zamanı öz-denetim

`app/security/audit.py::collect_runtime_security_findings(config)` (CODE_VERIFIED, dosya doğrudan okunmuştur), uygulama başlatılırken şu kontrolleri otomatik yapar ve `critical`/`warning`/`info` seviyesinde bulgu üretir:

- `SECRET_KEY` tanımlı mı, en az 32 karakter mi (production/staging'de critical).
- `SESSION_COOKIE_SECURE` / `REMEMBER_COOKIE_SECURE` production benzeri ortamda açık mı.
- `MAX_CONTENT_LENGTH` etkin mi (yükleme boyutu limiti).
- `REQUEST_GUARD_ENABLED`, `LOGIN_THROTTLE_ENABLED`, `WTF_CSRF_ENABLED` açık mı (CSRF kapalıysa **critical**).
- `TCKN_ENCRYPTION_KEY` tanımlı mı (production'da uyarı; eksikse fail-fast değil, yalnız uyarı — bu bilinçli bir tasarım kararıdır, prod'a çıkmadan önce mutlaka ayarlanmalıdır).
- `SENTRY_DSN` gerçek mi yoksa placeholder mı (`sentry.io/...`, `your-public-key`, `change-me` gibi placeholder desenleri reddedilir).
- PostgreSQL bağlantısında `sslmode=disable` var mı (production benzeri ortamda critical).
- CSP (`Content-Security-Policy`) etkin mi, `unsafe-inline` script var mı, nonce üretimi açık mı (production/pilot'ta nonce kapalıysa critical).

Bulgular `log_runtime_security_posture()` ile uygulama başlatılırken loglanır (CODE_VERIFIED, aynı dosya satır 183-200).

## 11. Sır (secret) yönetimi

- `.env` gerçek dosyası **hiçbir zaman** release paketine girmez; yalnızca `.env.example` ve `.env.docker.example` (değer içermeyen şablonlar) paketlenebilir (DOCUMENTATION_DERIVED + SCRIPT_VERIFIED, `docs/handover/SECRETS_AND_PERSISTENCE.md:10,28-31`; `scripts/release/build_bys360_safe_release.py` filtre kuralları bu HEAD'de dosya olarak mevcuttur).
- `SECRET_KEY` doğrulaması: boş olamaz, bilinen placeholder olamaz (`CHANGE_ME`, `change-me`, `changeme`, dev-anahtarı), en az 32 karakter — `APP_ENV` production/staging iken sert `RuntimeError` ile zorlanır (DOCUMENTATION_DERIVED, `SECRETS_AND_PERSISTENCE.md:74-81`, `config.py` içinde satır aralığı olarak belgelenmiş; bu oturumda tam satır numarası ayrıca doğrulanmadı).
- Repo sır tarama script'i: `scripts/quality/bys360_secret_repo_gate.py` (`BYS360_SECRET_REPO_GATE_V2_PHASE1`) — `SECRET_KEY`, `DATABASE_URL`, `SQLALCHEMY_DATABASE_URI`, `POSTGRES_PASSWORD`, bare `SECRET` (ör. `FLASK_SECRET`) gibi anahtarları git-native aday modeliyle (tracked+staged+untracked-ama-ignore'da-olmayan) tarar (CODE_VERIFIED, dosya doğrudan okunmuştur).
- **Bu fazda çapraz okunan güncel kanıt:** `reports/quality/BYS360_SECRET_REPO_GATE_V1_REPORT.json`, `generated_at: 2026-09-02T22:44:02`, `finding_count: 0`, `ok: true`, 3298 dosya tarandı, 315 uyarı (placeholder/referans türünde, bulgu değil) — bu, secret gate'in "0 bulgu ile PASS" olduğu iddiasını **doğrular** (CODE_VERIFIED cross-read; bu oturumda script yeniden çalıştırılmadı, mevcut rapor artefaktı okunmuştur).
- Ayrı bir release-özel sır tarayıcı da mevcuttur: `scripts/release/scan_bys360_release_secrets.py` (paketlenmiş ZIP içeriğini tarar).

## 12. Ağ maruziyeti ve yönlendirme güvenliği

- `TRUSTED_HOSTS` — Flask 3.1'in yerleşik Host-header doğrulaması kullanılır; production/staging ortamında wildcard (`'*'`) yasaktır (CODE_VERIFIED, `config.py:481-514`).
- Açık yönlendirme (open redirect) koruması: `is_safe_redirect_target()` — hedef host'un güven kökü **asla** istemcinin gönderdiği `request.host`/`request.host_url` başlığından türetilmez; bunun yerine sunucu tarafı sabit `APP_BASE_URL` (+ opsiyonel host allowlist) kullanılır (CODE_VERIFIED, `app/route_support.py:317-368`, ayrıntılı sözleşme `app/security/redirect_guard.py` docstring'inde).
- Sağlık uç noktaları (`/healthz`, `/readyz`, `/versionz`) giriş gerektirmez ve `main_bp` altında yayınlanır (CODE_VERIFIED, `app/routes.py:72-86,176-202`).
- Dosya yükleme güvenliği: `app/security/upload_security.py` mevcut, `UPLOAD_STRICT_MIME_VALIDATION` varsayılan açık (DOCUMENTATION_DERIVED, dosya varlığı CODE_VERIFIED ancak içerik bu turda satır satır incelenmedi).
- CSP başlık katmanı: `app/security/headers.py` mevcut (CODE_VERIFIED, dosya varlığı doğrulandı; nonce/script-src davranışı §10'daki öz-denetim kontrolleriyle tutarlı).
- Portal video gömme (embed) için host allowlist (YouTube/Vimeo alt kümesi) ve iframe `sandbox`/`referrerpolicy` koruması mevcuttur (DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:622-634`; bu turda dosya düzeyinde ayrıca yeniden okunmadı).

## 13. Sürüm bütünlüğü ve tamper doğrulama

- Release paketi üç birlikte üretilen artefaktla teslim edilir: `.zip`, `.manifest.json` (schema_version 2, `source_sha`, dosya listesi), `.sha256sums.txt` (DOCUMENTATION_DERIVED, `docs/handover/RELEASE_VERIFICATION.md:9-17`; `scripts/release/build_bys360_safe_release.py` dosyası bu HEAD'de mevcuttur — CODE_VERIFIED dosya varlığı).
- Doğrulama komutu: `python scripts/release/build_bys360_safe_release.py --verify <zip> --expected-source-sha <sha>` — ZIP içeriğini yeniden hash'ler, manifest/sha256sums tutarlılığını çapraz kontrol eder, yasaklı yol (gerçek `.env`, `instance/`, `.sqlite3`, `.key` vb.) varlığını reddeder (DOCUMENTATION_DERIVED, aynı belge).
- **Exact-head kuralı:** Bir CI workflow'unun "succeeded" olması tek başına kanıt sayılmaz; checkout log'undaki gerçek SHA, doğrulanmak istenen commit ile birebir eşleşmelidir (DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:557-561`). Bu current-state fazında bu kural, HEAD `873e6d3348e644c5384a33a99c517600a3346cfd` için ayrıca uygulanmamıştır; uzak doğrulanmış kontrol noktası `7d73ff4d468cad11d78d2339ba770f70b5ec0baf`'dir ve yerel HEAD ile **birebir aynı değildir** — bu fark açıkça NOT_YET_FINALIZED olarak işaretlenir, final teslimde exact-head kuralına göre yeniden doğrulanmalıdır.

## 14. Operasyonel kontroller ve olay yönetimi

Olay müdahale adımları (DOCUMENTATION_DERIVED, `docs/handover/BYS360_GUVENLIK_KVKK_NOTLARI.md:27-34`, bu current-state fazında tatbikat/tekrar yürütme ile ayrıca doğrulanmadı — PRODUCTION_HISTORICAL / süreç tanımı):

1. Paylaşım durdurulur.
2. Sır döndürülür (rotate edilir).
3. Etkilenen kullanıcı/servis tespit edilir.
4. Audit log korunur.
5. Kalıcı düzeltme yapılır.
6. Olay raporu yazılır.

## 15. AI için insan karar zorunluluğu — özet

AI panelleri (`ai_agent`, `ai_decision`, `assistant_training_bank` modülleri) öneri/özet üretir; nihai idari karar mekanizması insan onayına bağlıdır. Bu, hem kod sözleşmesinde (`HUMAN_REVIEW_REQUIRED=True`, `AI_FINAL_DECISION_ENABLED=False`, §6) hem de önceki devir belgesinde ("AI karar vermez; insan denetimli özet üretir", `docs/handover/BYS360_GUVENLIK_KVKK_NOTLARI.md:12`) tutarlı biçimde ifade edilmiştir.

---

## Ek — Kanıt sınıflandırma özeti

Bu belgedeki iddiaların büyük çoğunluğu CODE_VERIFIED'dır (doğrudan bu HEAD'deki kaynak kod okunarak). DOCUMENTATION_DERIVED olarak işaretlenen kısımlar önceki devir belgelerinden alınmış ve bu turda ayrıca satır satır yeniden doğrulanmamıştır. NOT_YET_FINALIZED/REQUIRES_FINAL_REFRESH olarak işaretlenen maddeler (mobil login throttle detayı, sağlık raporu erişim kısıtlaması, başarısız giriş denemesinin audit_logs'a yazılıp yazılmadığı, exact-head CI doğrulamasının güncel HEAD için tekrarı) final dokümantasyon yenileme aşamasında kapatılmalıdır.
