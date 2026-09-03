Doküman Adı: BYS360 Rol, Yetki ve Erişim Kontrol Modeli
Doküman Türü: Güvenlik / Yetkilendirme
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası, yerel HEAD değil)
Son Güncelleme: 2026-09-02

---

## 1. Amaç

Bu doküman, "hangi rol/birim/kişi hangi menüyü ve hangi route ailesini görebilir/kullanabilir" sorusunun **kod düzeyinde doğrulanmış** cevabını verir. Kaynak öncelik sırası: (1) gerçek kod (`app/route_support.py`, `app/services/settings/effective_menu*`, `app/models/`), (2) önceki devir belgesi (`docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md` §37, §36), (3) diğer handover belgeleri. Her iddia kanıt etiketiyle sunulur.

## 2. Veri modeli

| Model | Tablo | Rol | Kanıt |
|---|---|---|---|
| `User.role` | `users` | Serbest metin rol adı (FK değil), varsayılan `"personel"` | CODE_VERIFIED (`app/models/core_models.py:59`) |
| `RoleMenuDefault` | `role_menu_defaults` | Rol bazlı varsayılan menü görünürlüğü | CODE_VERIFIED (`app/models/settings_models.py:13`) |
| `UnitMenuProfile` | `unit_menu_profiles` | Organizasyon birimi bazlı menü profili (rol varsayılanını geçersiz kılabilir) | CODE_VERIFIED (`app/models/settings_models.py:70`) |
| `UserMenuPermission` | `user_menu_permissions` | Kişi bazlı menü override'ı (en spesifik katman) | CODE_VERIFIED (`app/models/core_models.py:386`) |
| `SettingsChangeLog` | `settings_change_logs` | Rol/birim/kişi yetki değişikliklerinin kendisinin denetim izi + rollback referansı | CODE_VERIFIED (`app/models/settings_models.py:89-108`) |
| `OrganizationUnit` / `OrganizationUnitVersion` / `EmployeeOrgAssignmentHistory` | — | Organizasyon birim yapısı ve kişi-birim atama geçmişi | CODE_VERIFIED (`app/models/org_models.py`) |

## 3. Rol aileleri (backend enforcement — `app/route_support.py`)

```python
ADMIN_FAMILY_ROLES        = {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"}
MANAGER_FAMILY_ROLES      = ADMIN_FAMILY_ROLES | {"birim_sorumlusu", "koordinator"}
PORTAL_EDITOR_ROLES       = ADMIN_FAMILY_ROLES | {"koordinator"}
PORTAL_GROUP_MANAGER_ROLES= ADMIN_FAMILY_ROLES
PORTAL_PROFILE_ADMIN_ROLES= {"admin", "baskan", "baskan_yardimcisi"}
```
CODE_VERIFIED, `app/route_support.py:66-70`.

Bu ailelere karşılık gelen decorator'lar: `admin_required`, `manager_required`, `portal_editor_required` (CODE_VERIFIED, `app/route_support.py:443-471`). `app/auth/decorators.py` yalnızca bu üçünü (`admin_required`, `manager_required`, `menu_key_required`) `app.route_support`'tan yeniden dışa aktaran bir geriye-uyumluluk köprüsüdür (CODE_VERIFIED).

Rol karşılaştırması normalize edilerek yapılır (`normalize_role_name` — trim + lowercase) (CODE_VERIFIED, `app/route_support.py:112-113`).

## 4. "Menü gizleme tek başına güvenlik değildir" ilkesi — doğrulanmış

Bu, mission talebinde özellikle sorgulanan iddiadır. Kod düzeyinde doğrulama:

1. **Menünün kendisi bir yetki kaynağıdır, yalnızca UI kozmetiği değildir.** `menu_key_required` decorator'ı, sayfayı render etmeden ÖNCE `can_access_menu()` çağırır ve `False` dönerse `render_access_denied()` (403) döner (CODE_VERIFIED, `app/route_support.py:424-436`). Yani bir route `menu_key_required` ile korunuyorsa, menüde görünmeyen bir öğeye URL'i bilerek doğrudan gidilse dahi backend aynı görünürlük haritasına bakarak reddeder — **"menü gizli ama route açık"** senaryosu bu decorator için yapısal olarak mümkün değildir, çünkü ikisi aynı fonksiyonu (`build_menu_visibility_map`) kullanır.
2. **Admin bypass'ı bilinçli olarak kaldırılmıştır.** Kod içi yorum: *"Admin/üst rol bypassı kaldırıldı. Bir route menu_key_required ile korunuyorsa son karar da Ayarlar > Rol Matrisi / kişi-birim görünürlüğünden gelen canlı menü haritasıdır."* (CODE_VERIFIED, `app/route_support.py:430-433`, etiket `BYS360_SETTINGS_LIVE_AUTHORITY_V2`).
3. **Rol-ailesi decorator'ları (`admin_required` vb.) ayrı ve bağımsız bir katmandır** — bunlar menü haritasına hiç bakmaz, doğrudan `user.role` üzerinden karar verir (CODE_VERIFIED, `app/route_support.py:443-459`). Bir route her iki decorator'ı da taşıyabilir (örn. `/admin/role-matrix`: `@login_required` + `@admin_required`, DOCUMENTATION_DERIVED `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:1582`).
4. **Dar kapsamlı, açıkça sınırlı istisna:** Yalnızca 3 performans-dönem yönetim menü anahtarı için, admin-ailesi kullanıcıların görünürlüğü rol matrisi/kişi override'ı ne olursa olsun `True` olarak zorlanır (CODE_VERIFIED, `app/services/settings/effective_menu_parts/public_build_context.py:9-27`, `bys360_context.py:463-485`). Bu **yalnızca menü görünürlüğünü** etkiler; ilgili route'ların backend yetkilendirmesi (varsa `admin_required`/`manager_required`) bu wrapper'dan bağımsız olarak ayrıca uygulanır. Bu istisna dışında rol matrisinde kapatılan bir menü öğesi hem UI'da hem backend kararında kapalı kalır.

**Sonuç:** "Menü gizleme tek başına güvenlik sınırı değildir; backend de uygulamalıdır" ilkesi, `menu_key_required` decorator'ının kendi tasarımı gereği zaten sağlanmıştır — çünkü UI görünürlüğü ile backend kararı **aynı fonksiyon çağrısına** dayanır, iki ayrı/senkronize edilmesi gereken sistem değildir. Yukarıdaki §4.4'teki dar istisna dışında admin rolü için otomatik bir "her şeyi gör" kısayolu yoktur.

## 5. Katmanlı menü otoritesi (rol matrisi → birim profili → kişi override)

Sıra, kod içi yorumla açıkça belgelenmiştir: **Rol matrisi tabanı → birim profili → kişi özel ayarı → teknik/rol güvenlik kapısı** (CODE_VERIFIED, `app/services/settings/effective_menu.py:135-139`). Karar motoru:

```
app/route_support.py::build_menu_visibility_map(user)   [ince köprü]
  → app/services/settings/effective_menu.py::build_menu_visibility_map   [299 satır facade]
      → app/services/settings/effective_menu_parts/*.py   [12 dosya, ~3064 satır]
```
CODE_VERIFIED (dosyalar doğrudan okunmuştur; toplam dosya/satır sayıları önceki devir belgesindeki `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:1569,1593` tespitiyle tutarlıdır).

Yazma katmanı (DB'ye kaydetme): `app/services/settings/menu_profile_access.py` — `save_role_menu_defaults_handler`, `save_unit_menu_profile_handler`, `save_user_menu_overrides_handler`, `clear_user_menu_overrides_handler` (DOCUMENTATION_DERIVED, önceki devir belgesi §37.5; dosya varlığı bu turda CODE_VERIFIED).

## 6. Menü kayıt (registry) ve kaldırılmış modüller

- `app/menu_registry.py` (+ `menu_registry_data_performance.py`, `menu_registry_data_personnel.py`, `menu_registry_data_sections.py`) — sistemin tüm menü tanımlarının statik kaynağı (CODE_VERIFIED, dosya varlığı).
- `flatten_menu_definitions()` ile düzleştirilen menü öğeleri, `is_removed_menu_key()` ile kapsam dışı bırakılan anahtarlar için süzülür (CODE_VERIFIED, `app/route_support.py:79-92`).
- Kapsam dışı bırakılan üç modül: `repository` (Belge/Medya), `education` (Eğitim/İSG), `strategy` (Strateji) — bunlar aktif özellik SAYILMAZ (DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:866`, kaynak: `app/config/removed_modules.py`; bu turda dosya varlığı ayrıca doğrulanmadı — REQUIRES_FINAL_REFRESH).

## 7. Salt-okunur referans ekran — bilinen sınır

`/admin/role-matrix` (`admin_role_matrix_center`, `app/admin/role_matrix_routes.py`, `@login_required` + `@admin_required`) tamamen `app/services/role_matrix_ui_service.py` içindeki **kod-içi sabit** (hardcoded) `ROLES`/`GROUPS` dataclass verisini render eder ve **hiçbir DB tablosuna dokunmaz** (DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:1595,1600,1623-1624`; dosyanın kendi docstring'i bunu itiraf eder). Bu ekran, gerçek görünürlük kararını (rol matrisi/birim profili/kişi override tablolarındaki güncel kayıtlar) **yansıtmayabilir** — yönetici bu ekrana bakarak yanlış bir "kim ne görüyor" sonucuna varabilir. Bu, dokümantasyon ile davranış arasında değil, **iki ayrı ekran arasında** bir tutarsızlık riskidir ve kodda açıkça uyarılmaz. Yeni operatörlerin gerçek yetki durumunu her zaman `/settings` içindeki düzenlenebilir matristen veya doğrudan ilgili DB tablolarından teyit etmesi önerilir.

## 8. Manager/koordinatör kapsamları ve özel iş akışları

- `koordinator` rolü hem `MANAGER_FAMILY_ROLES` hem `PORTAL_EDITOR_ROLES` içindedir — birim yönetimi ve portal içerik editörlüğü yetkisini birlikte taşır (CODE_VERIFIED, §3).
- `mali_musavir` (mali müşavir) rolü `ADMIN_FAMILY_ROLES` içinde sınıflandırılmıştır — bu, mali müşavirin admin-seviyesi genel yönetim yetkisiyle değil, aynı rol-ailesi menü/route kapısından geçtiği anlamına gelir; gerçek scope farkları (mali veriye özel filtreleme vb.) bu turda ayrıca aranmadı — NOT_YET_FINALIZED.
- Performans modülünde vekalet (delegasyon) mekanizması `app/services/performance/delegation.py` üzerinden **`AssignmentAuditLog`**'a bağlıdır (CODE_VERIFIED, dosya `AssignmentAuditLog(` çağrısı içerir, satır 264 — **koordinatör düzeltmesi**, peer-review/Agent 2: önceki taslak bunu yanlışlıkla merkezi `AuditLog` modeliyle karıştırıyordu; `AssignmentAuditLog` ayrı bir model, `app/services/performance/models_phase5_template.py:44`'te tanımlı — bkz. DOC-05 §8 düzeltmesi); delegasyonun performans amir-onay zincirine tam entegrasyon detayı önceki devir belgesinde de "tek tek doğrulanmadı" olarak işaretlenmiştir (DOCUMENTATION_DERIVED, `docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md:645`) — REQUIRES_FINAL_REFRESH.

## 9. Auditability ve delegasyon — yetki değişikliğinin kendisi izlenir

`SettingsChangeLog` modeli, rol matrisi / birim profili / kişi bazlı yetki değişikliklerinin kim tarafından, ne zaman, hangi kapsamda (`change_scope`), önceki/yeni durumla birlikte yapıldığını kaydeder ve **geri alma (rollback) zincirini** (`reverted_from_log_id`, `is_rollback`) destekler (CODE_VERIFIED, `app/models/settings_models.py:89-108`). Bu, yetki modelinin kendisinin de denetlenebilir ve tersine çevrilebilir olduğunu gösteren güçlü bir kanıttır.

## 10. Özet tablo — erişim kararı hangi katmanda verilir

| Karar türü | Mekanizma | Admin bypass var mı |
|---|---|---|
| Sayfa/route erişimi (rol ailesi) | `admin_required` / `manager_required` / `portal_editor_required` | Rolün ailede olması yeterli (tasarım gereği) |
| Menü öğesi görünürlüğü + ilişkili route (`menu_key_required`) | Canlı DB haritası (`build_menu_visibility_map`) | **Hayır** — kaldırılmıştır (§4.2), yalnız 3 dar istisna hariç (§4.4) |
| Ayarlar > Rol Matrisi ekranı (yazma) | `admin_required` | Rolün ailede olması yeterli |
| `/admin/role-matrix` (salt-okunur referans) | `admin_required`, statik veri | N/A — DB'ye bağlı değil |

## 11. NOT_YET_FINALIZED / REQUIRES_FINAL_REFRESH kalemleri

- Kaldırılmış modüllerin (`app/config/removed_modules.py`) bu HEAD'de içerik olarak doğrulanması.
- Mali müşavir rolünün admin-ailesi içindeki gerçek veri-scope farkının doğrulanması.
- Performans delegasyon-onay zinciri entegrasyonunun uçtan uca doğrulanması.
- `/admin/role-matrix` ile canlı DB durumu arasındaki drift riskinin bu HEAD'de fiilen gözlemlenip gözlemlenmediği (yalnızca kod/docstring kanıtı var, canlı ekran karşılaştırması bu fazda yapılmadı).
