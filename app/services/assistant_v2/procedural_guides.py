"""BYS360 Assistant V2 -- procedural ("how do I...") guide registry (mandate
Phase B/C: legacy procedural-help migration).

The legacy reply chain's step-by-step "how do I add a personnel record" /
"how do I open a performance period" content is scattered across 4 reachable
files in `app/services/ai_agent/`: `assistant_full_stepwise_tutor_v5.py` (28
topics, the highest-priority layer that ALWAYS self-answers and never
delegates further down the chain -- the de-facto live/authoritative source),
`assistant_stepwise_tutor_v4.py` and `assistant_step_guide.py` (both pure
subsets/duplicates of V5's topics, structurally wired but never actually
reached in practice because V5 never falls through), and
`assistant_full_live_usage_guide_v2.py` (mostly duplicates V5 too, plus a
handful of topics V5 doesn't cover). A 5th file, `assistant_visible_tutor_v6.py`,
is confirmed dead code (its entry points are never called). Per the
mandate's own instruction ("Do NOT copy giant canned-answer chains into
V2"), each topic below is condensed to its substantive steps, not a
verbatim copy of the ~3000 combined lines across those files.

Every `required_permission` below was independently verified against real
`'key':` entries in `app/menu_registry.py` / `app/menu_registry_data_sections.py`
(grepped directly, not assumed) -- several plausible-sounding legacy-screen
key guesses (e.g. a distinct `personnel_create`/`leave`/`delegation`/
`personnel_edit`/`attendance` key) did NOT exist under those exact names and
were deliberately NOT used; those topics instead reuse the nearest already-
verified real key from this same registry (see each entry's `evidence`),
consistent with "do not invent permissions."

Same shape/conventions as `capability_registry.py`:
  - frozen dataclasses, list-of-entries, no side effects at import time.
  - `module_key` must already exist in `app.services.settings.module_registry.MODULE_REGISTRY`.
  - `required_permission` is a real, existing menu_key already used
    elsewhere in this registry/codebase (never invented) -- re-checked live
    via `app.route_support.can_access_menu` on every call, exactly the same
    mechanism capabilities use. Where no single existing menu_key precisely
    matches a topic's own screen, the nearest already-verified module-level
    permission is reused (never a new key), and this approximation is
    stated explicitly in that entry's `evidence`.
  - A guide's "related screen" link is never hand-typed here: it is derived
    generically from `required_permission` via
    `app.services.assistant_v2.related_links.resolve_related_link`, the same
    trusted `MENU_SECTIONS` lookup capabilities use (Phase D) -- so a guide
    with no confidently-verifiable permission_key simply gets no clickable
    action button (label-only), never a guessed URL.

This is a deliberately SEPARATE registry from `ASSISTANT_CAPABILITY_REGISTRY`
(not shoehorned into `AssistantCapabilityEntry`) because a guide is static
instructional content, not a live database read -- it has no
`service_handler` to resolve, and its "data" is authored here directly.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.services.settings.module_registry import MODULE_REGISTRY


@dataclass(frozen=True)
class ProceduralGuideEntry:
    guide_key: str
    module_key: str
    intent_tags: tuple[str, ...]
    title: str
    summary: str
    steps: tuple[str, ...]
    required_permission: str | None
    warnings: tuple[str, ...] = ()
    active: bool = True
    evidence: str = ""


_STEP_GUIDE_SOURCE = "app/services/ai_agent/assistant_step_guide.py"

# ---------------------------------------------------------------------------
# Registry -- condensed 1:1 from the 11 real topic branches in
# assistant_step_guide.py's build_bys360_assistant_step_reply() (its 12th
# branch, "assistant_identity", is conversational, not procedural -- already
# covered natively by conversational_intents.py, not duplicated here).
# ---------------------------------------------------------------------------

PROCEDURAL_GUIDE_REGISTRY: list[ProceduralGuideEntry] = [
    ProceduralGuideEntry(
        guide_key="personnel_hr_guide_add_employee",
        module_key="personnel_hr",
        intent_tags=("personel ekle", "personel kaydi", "yeni personel", "sicil no", "nasil eklenir", "personnel", "add"),
        title="Personel Nasıl Eklenir",
        summary="Yeni bir personel özlük kaydı oluşturmak için izlenecek adımlar.",
        steps=(
            "Sol menüden Personel Yönetimi bölümünü açın.",
            "Personel Özlük Dosyaları ekranına girin.",
            "Yeni personel ekleme butonunu kullanın.",
            "Sicil No, ad soyad, unvan, birim, üst birim ve yönetici alanlarını doldurun.",
            "Varsa profil fotoğrafı ve iletişim bilgilerini ekleyin.",
            "Rol ve menü görünürlüğü gerekiyorsa Sistem Ayarları / Rol Matrisi üzerinden kontrol edin.",
            "Kaydettikten sonra personelin organizasyon ve performans zincirinde doğru görünüp görünmediğini kontrol edin.",
        ),
        required_permission="admin_users",
        warnings=("BYS360'da TC yerine Sicil No esas alınır.", "Asistan personel kaydı oluşturmaz; yalnızca doğru adımı gösterir."),
        evidence=f"condensed verbatim from {_STEP_GUIDE_SOURCE}:93-109 (personnel_create_steps); required_permission='admin_users' reused from capability_registry.py's personnel_hr_read_personnel_record (same real menu_key, app/menu_registry.py:1101)",
    ),
    ProceduralGuideEntry(
        guide_key="personnel_hr_guide_leave_and_delegation",
        module_key="personnel_hr",
        intent_tags=("izin", "vekalet", "devamsizlik", "leave", "delegation"),
        title="İzin, Devamsızlık ve Vekâlet İşlemleri",
        summary="İzin, devamsızlık veya vekâlet kaydı oluşturmak için izlenecek adımlar.",
        steps=(
            "Sol menüden Personel Yönetimi bölümünü açın.",
            "İzin ve Devamsızlık Takibi veya Devamsızlık ve Vekâlet ekranına girin.",
            "İlgili personeli ve tarih aralığını seçin.",
            "İzin, devamsızlık veya vekâlet türünü belirleyin.",
            "Vekâlet varsa vekil kişiyi ve geçerlilik süresini tanımlayın.",
            "Kaydetmeden önce performans ve görev akışını etkileyebilecek tarihleri kontrol edin.",
        ),
        required_permission="hr_leave_tracking",
        warnings=("Asistan vekâlet atamaz veya izin onaylamaz; yalnızca işlem yolunu gösterir.",),
        evidence=f"condensed verbatim from {_STEP_GUIDE_SOURCE}:112-127 (leave_delegation_steps); required_permission='hr_leave_tracking' reused from capability_registry.py (real menu_key, app/menu_registry.py:1104)",
    ),
    ProceduralGuideEntry(
        guide_key="performance_mgmt_guide_open_period",
        module_key="performance_mgmt",
        intent_tags=("performans donemi", "donem ac", "yeni donem", "performance", "period", "open"),
        title="Performans Dönemi Nasıl Açılır",
        summary="Yeni bir performans değerlendirme dönemi başlatmak için izlenecek adımlar.",
        steps=(
            "Sol menüden Performans Yönetimi bölümünü açın.",
            "Dönem Yönetimi ekranına girin.",
            "Yeni dönem oluştur butonunu seçin.",
            "Dönem adını, dönem türünü ve tarih aralığını girin.",
            "Kapsam tipini seçin: tüm kurum, birim, kategori veya seçili personel.",
            "Kriter ve ağırlıkların bu dönem için hazır olduğundan emin olun.",
            "Kaydettikten sonra görev üretimi / değerlendirme görevleri ekranından zinciri kontrol edin.",
        ),
        required_permission="performance_reports",
        warnings=("Dönem açma işlemi rol yetkisine bağlıdır.", "Asistan dönem oluşturmaz; sadece adımları anlatır."),
        evidence=f"condensed verbatim from {_STEP_GUIDE_SOURCE}:130-146 (performance_period_steps); required_permission='performance_reports' reused from capability_registry.py's performance_mgmt_list_active_periods (real menu_key, app/menu_registry.py:1157) -- nearest already-verified general performance-operations key, not a topic-exact one",
    ),
    ProceduralGuideEntry(
        guide_key="performance_mgmt_guide_task_generation",
        module_key="performance_mgmt",
        intent_tags=("gorev uret", "degerlendirme gorevi", "gorevleri olustur", "task generation"),
        title="Performans Değerlendirme Görevleri Nasıl Üretilir",
        summary="Bir dönem için amir-personel değerlendirme görevlerinin oluşturulma adımlarını açıklar.",
        steps=(
            "Görev Üretimi ekranını açın.",
            "İlgili dönemi seçin.",
            "Kapsamdaki personel, birim ve amir zincirinin doğru olduğunu kontrol edin.",
            "'Görevleri Oluştur' işlemini çalıştırın.",
            "Eksik veya hatalı amir ataması olan personel varsa önce organizasyon verisini düzeltip yeniden üretin.",
        ),
        required_permission="performance_hierarchy_assignments",
        warnings=("Yanlış/eksik amir ataması, var olmayan bir amir için bekleyen görev göstermemelidir.",),
        evidence="new topic (not in assistant_step_guide.py) -- required_permission='performance_hierarchy_assignments', verified real key, grep-confirmed in app/menu_registry.py",
    ),
    ProceduralGuideEntry(
        guide_key="performance_mgmt_guide_scoring",
        module_key="performance_mgmt",
        intent_tags=("kriter", "degerlendirme kriter", "puanlama", "puan ver", "scoring", "criteria"),
        title="Performans Kriteri ve Puanlama Süreci",
        summary="Amirlerin personeli kriter bazlı puanlama süreci için izlenecek adımlar.",
        steps=(
            "Performans Yönetimi bölümünden Değerlendirme Kriterleri ekranını kontrol edin.",
            "Aktif dönem için kullanılacak kriterlerin açık olduğundan emin olun.",
            "Amir olarak Görevlerim / Performans Görevleri ekranına girin.",
            "Değerlendirilecek personeli seçin.",
            "Her kriter için 1-5 arası puan ve gerekiyorsa açıklama girin.",
            "Nihai sonuç 70 altı veya 90 üstü ise ayrıntılı genel görüş gerekebilir.",
            "Kaydetmeden önce önceki amir görüşü ve süreç uyarılarını kontrol edin.",
        ),
        required_permission="performance_reports",
        warnings=("1 ve 5 puan açıklama zorunluluğu sistem ayarına bağlıdır.", "Asistan puan vermez, puan önermez ve amir görüşü yazmaz; yalnızca ekran yolunu açıklar."),
        evidence=f"condensed verbatim from {_STEP_GUIDE_SOURCE}:149-166 (performance_scoring_steps); required_permission approximated to 'performance_reports' (nearest already-verified performance_mgmt key) -- no distinct scoring-screen menu_key was found in this registry",
    ),
    ProceduralGuideEntry(
        guide_key="performance_mgmt_guide_scorecard_visibility",
        module_key="performance_mgmt",
        intent_tags=("karne", "karnem", "not karnesi", "goremiyorum", "gorunmuyor", "scorecard", "visibility"),
        title="Karne Neden Görünmüyor",
        summary="Personelin kendi karnesini ne zaman ve nasıl görebileceğini, görünmüyorsa neyin kontrol edileceğini açıklar.",
        steps=(
            "Personel kendi karnesini ancak yayın/onay süreci tamamlandıktan sonra görebilir.",
            "Karneniz görünmüyorsa değerlendirme henüz tamamlanmamış olabilir; Süreç Takibi ekranından dönemi kontrol edin.",
            "70 altı sonuç varsa Başkan/Üst Onay süreci bekleniyor olabilir.",
            "Yayın ön onayı gerekiyorsa süreç tamamlanmadan karne açılmaz.",
            "Yayınlandıktan sonra Not Karnesi ekranından güncel sonucu görebilirsiniz.",
        ),
        required_permission="performance_process_tracking",
        warnings=("Asistan puan, amir görüşü veya hassas karne detayı göstermez; sizi ilgili ekrana yönlendirir.", "Yayından önce sonucun görünmemesi beklenen, doğru güvenlik davranışıdır."),
        evidence=(
            f"steps condensed from {_STEP_GUIDE_SOURCE}:169-183 (scorecard_publish_steps); required_permission "
            "updated to 'performance_process_tracking' (verified real key, grep-confirmed in "
            "app/menu_registry.py) -- more precise than an earlier 'performance_reports' approximation, "
            "matching this guide's actual troubleshooting/tracking focus"
        ),
    ),
    ProceduralGuideEntry(
        guide_key="performance_mgmt_guide_scorecard_archive",
        module_key="performance_mgmt",
        intent_tags=("gecmis karne", "karne arsiv", "eski puan", "archive", "scorecard"),
        title="Geçmiş Karne Arşivi Nasıl Kullanılır",
        summary="Önceki dönemlere ait karnelerin nereden görüntüleneceğini açıklar.",
        steps=(
            "Geçmiş Karne Arşivi ekranını açın.",
            "Görmek istediğiniz yılı/dönemi seçin.",
            "Yetki kapsamınıza göre kendi geçmiş sonuçlarınızı veya (yöneticiyseniz) birim sonuçlarını görüntüleyin.",
        ),
        required_permission="performance_archive",
        warnings=("Kişisel geçmiş sonuçlar yalnızca ilgili kişi ve yetkili amiri tarafından görüntülenebilir.",),
        evidence="new topic (not in assistant_step_guide.py) -- required_permission='performance_archive', verified real key, grep-confirmed in app/menu_registry.py",
    ),
    ProceduralGuideEntry(
        guide_key="performance_mgmt_guide_low_score_approval",
        module_key="performance_mgmt",
        intent_tags=("70 alti", "dusuk performans", "baskan onay", "ust onay", "low score", "approval"),
        title="70 Altı Sonuç ve Başkan/Üst Onay Süreci",
        summary="70 altı performans sonucunda izlenen onay sürecini açıklar.",
        steps=(
            "Değerlendirme tamamlanır ve nihai puan hesaplanır.",
            "Nihai puan 70'in altındaysa sonuç doğrudan kesinleşmez.",
            "Kayıt Başkan/Üst Onay sürecine düşer; Başkan Onayları ekranından incelenir.",
            "Onay tamamlanmadan karne personele kesin sonuç olarak yayınlanmaz.",
            "İlk 70 altı sonuçta uyarı/süreç kaydı oluşturulur; aynı yıl ikinci 70 altı sonuçta tekrarlayan düşük performans süreci başlatılır.",
        ),
        required_permission="performance_president_approvals",
        warnings=("Sistem otomatik idari işlem yapmaz; yalnızca yetkili idari sürece kayıt üretir.", "Asistan onay/ret işlemi yapmaz; yalnızca ilgili ekrana yönlendirir."),
        evidence=(
            f"steps condensed from {_STEP_GUIDE_SOURCE}:186-202 (low_score_approval_steps); required_permission "
            "updated to 'performance_president_approvals' (verified real key, grep-confirmed, roles admin/baskan) "
            "-- more precise than an earlier 'performance_reports' approximation, matching the actual gated screen"
        ),
    ),
    ProceduralGuideEntry(
        guide_key="performance_mgmt_guide_publication_preapproval",
        module_key="performance_mgmt",
        intent_tags=("yayin on onay", "final yayin", "karne yayinla", "publish", "preapproval"),
        title="Yayın Ön Onayı ve Final Yayın",
        summary="Değerlendirme sonuçlarının personele yayınlanmadan önceki onay adımlarını açıklar.",
        steps=(
            "Tüm değerlendirmelerin tamamlandığını doğrulayın.",
            "70 altı sonuç varsa Başkan/Üst Onay sürecinin tamamlandığını kontrol edin.",
            "Yayın ön onayı yetkili amiri tarafından verilir.",
            "Ardından yetkili yönetici dönemi final olarak yayınlar.",
            "Yayınlandıktan sonra personel kendi karnesini görebilir.",
        ),
        required_permission="performance_personnel_support_publish_approval",
        warnings=("Ön onay tamamlanmadan final yayın yapılmamalıdır.",),
        evidence="new topic (not in assistant_step_guide.py) -- required_permission='performance_personnel_support_publish_approval', verified real key, grep-confirmed in app/menu_registry.py",
    ),
    ProceduralGuideEntry(
        guide_key="performance_mgmt_guide_in_period_notes",
        module_key="performance_mgmt",
        intent_tags=("donem ici not", "gozlem notu", "olumlu olumsuz olay", "interim note"),
        title="Dönem İçi Not Nasıl Eklenir",
        summary="Değerlendirme dönemi sırasında personel hakkında gözlem notu eklemeyi açıklar.",
        steps=(
            "Dönem İçi Notlar ekranını açın.",
            "İlgili dönemi ve personeli seçin.",
            "Not türünü seçin: olumlu olay, olumsuz olay, başarı, gelişim ihtiyacı veya genel gözlem.",
            "Açıklamayı yazıp kaydedin.",
        ),
        required_permission="performance_interim_notes",
        warnings=("Dönem içi not tek başına puan üretmez; değerlendirme sırasında destekleyici bilgi olarak kullanılır.",),
        evidence="new topic (not in assistant_step_guide.py) -- required_permission='performance_interim_notes', verified real key, grep-confirmed in app/menu_registry.py",
    ),
    ProceduralGuideEntry(
        guide_key="performance_mgmt_guide_development_suggestion",
        module_key="performance_mgmt",
        intent_tags=("gelisim onerisi", "guclu yon", "gelisim alani", "development"),
        title="Gelişim Önerisi Nasıl Yazılır",
        summary="Değerlendirme sonrası personele yönelik gelişim rehberliği eklemeyi açıklar.",
        steps=(
            "Gelişim Rehberi / Gelişim Önerileri ekranını açın.",
            "İlgili personeli ve dönemi seçin.",
            "Güçlü yön, gelişim alanı ve takip notu alanlarını doldurun.",
            "Kaydedin; görünürlük sistem ayarına göre belirlenir.",
        ),
        required_permission="performance_development_guidance",
        warnings=("Gelişim önerisi idari/disiplin kararı değildir.",),
        evidence="new topic (not in assistant_step_guide.py) -- required_permission='performance_development_guidance', verified real key, grep-confirmed in app/menu_registry.py",
    ),
    ProceduralGuideEntry(
        guide_key="performance_mgmt_guide_reports_dashboard",
        module_key="performance_mgmt",
        intent_tags=("performans rapor", "dashboard", "riskli personel", "aksatan amir", "reports"),
        title="Performans Dashboard ve Raporları Kullanımı",
        summary="Performans dashboard ve raporlama ekranlarının genel kullanımını açıklar.",
        steps=(
            "Süreç Raporları / Dashboard ekranını açın.",
            "Dönem, birim, kategori veya personel bazında filtreleyin.",
            "Tamamlanma oranı, düşük performans, riskli personel ve aksatan amir kartlarını inceleyin.",
            "Detay için ilgili karta tıklayıp ayrıntılı rapora geçin.",
        ),
        required_permission="performance_process_reports",
        warnings=("Kişi bazlı detaylar yetki kapsamına göre sınırlıdır.",),
        evidence="new topic (not in assistant_step_guide.py) -- required_permission='performance_process_reports', verified real key, grep-confirmed in app/menu_registry.py",
    ),
    ProceduralGuideEntry(
        guide_key="performance_mgmt_guide_third_supervisor",
        module_key="performance_mgmt",
        intent_tags=("3. amir", "ucuncu amir", "third supervisor"),
        title="3. Amir Kuralı",
        summary="Çok seviyeli değerlendirme yapılarında 3. amirin rolünü açıklar.",
        steps=(
            "3. amir her personel için zorunlu değildir.",
            "Yapıda gerçek 3. amir yoksa sistem boş görev veya boş sütun göstermemelidir.",
            "3. amir yorum modundaysa yalnızca görüş yazar, puana etkisi olmaz; puan modundaysa ağırlık hesabına dahil edilir.",
            "İşlem sırası çok seviyeli yapılarda 3. amir, sonra 2. amir, en son 1. amir şeklindedir.",
            "Kör değerlendirme yoktur; sonraki amir önceki değerlendirmeyi görür.",
        ),
        required_permission="performance_reports",
        warnings=("Bu ayarlar Sistem Ayarları ve Performans Yönetimi yetkileriyle kontrol edilir.",),
        evidence=f"condensed verbatim from {_STEP_GUIDE_SOURCE}:205-220 (third_supervisor_steps); required_permission approximated to 'performance_reports' (nearest already-verified performance_mgmt key)",
    ),
    ProceduralGuideEntry(
        guide_key="settings_auth_guide_role_matrix",
        module_key="settings_auth",
        intent_tags=("rol matrisi", "menu goster", "menu gizle", "yetki", "role matrix", "menu visibility"),
        title="Rol Matrisi ve Menü Görünürlüğü",
        summary="Rol/kullanıcı bazlı menü görünürlüğünü düzenlemek için izlenecek adımlar.",
        steps=(
            "Sistem Ayarları bölümüne girin.",
            "Rol Matrisi / Menü Görünürlüğü ekranını açın.",
            "Düzenlenecek rolü, kullanıcıyı veya birim profilini seçin.",
            "Görünmesi istenen menüleri açık, görünmemesi gerekenleri kapalı yapın.",
            "Kaydettikten sonra aynı yetkinin backend erişim kontrolünde de çalıştığını kontrol edin.",
        ),
        required_permission="settings",
        warnings=("Yetkisiz kullanıcı menüyü hiç görmemeli; URL yazarsa kurumsal erişim engeli ekranı görmelidir.", "Asistan yetki vermez veya kaldırmaz; yalnızca doğru ayar ekranına yönlendirir."),
        evidence=f"condensed verbatim from {_STEP_GUIDE_SOURCE}:223-238 (role_matrix_steps); required_permission='settings' reused from capability_registry.py's settings_auth entries (real menu_key)",
    ),
    ProceduralGuideEntry(
        guide_key="support_help_guide_open_ticket",
        module_key="support_help",
        intent_tags=("destek talebi", "yardim talebi", "ariza", "talep ac", "support", "ticket", "open"),
        title="Destek Talebi Nasıl Açılır",
        summary="Yardım Merkezi üzerinden yeni bir destek talebi oluşturma adımları.",
        steps=(
            "Sol menüden Yardım Merkezi veya Destek Talebi Aç ekranına girin.",
            "Talep konusunu kısa ve anlaşılır yazın.",
            "Kategori ve öncelik alanlarını seçin.",
            "Açıklama bölümüne yaşadığınız sorunu ekleyin.",
            "Gerekirse ekran görüntüsü veya belge ekleyin.",
            "Talebi kaydedin ve Taleplerim ekranından durumunu takip edin.",
        ),
        required_permission="support_my_tickets",
        warnings=("Asistan destek talebinin içeriğini herkese göstermez; yalnızca sizi ilgili ekrana yönlendirir.",),
        evidence=f"condensed verbatim from {_STEP_GUIDE_SOURCE}:241-256 (support_ticket_steps); required_permission='support_my_tickets' reused from capability_registry.py (real menu_key)",
    ),
    ProceduralGuideEntry(
        guide_key="communication_guide_notifications_surveys_messages",
        module_key="communication",
        intent_tags=("anket", "duyuru", "bildirim", "mesaj", "geri bildirim", "communication", "survey", "notification"),
        title="Bildirim, Duyuru, Anket ve Mesaj Kullanımı",
        summary="Bildirimler, duyurular, anketler ve mesajlar ekranlarının genel kullanımını açıklar.",
        steps=(
            "Bildirimler ekranından size gelen sistem bildirimlerini kontrol edin.",
            "Duyurular ekranından kurum içi duyuruları takip edin.",
            "Anketler ekranından size atanmış anketleri yanıtlayın.",
            "Geri bildirim veya nabız ekranları açıksa ilgili formu doldurun.",
            "Mesajlar ekranından yetkiniz dahilindeki konuşmaları takip edin.",
        ),
        required_permission="announcements",
        warnings=("Asistan mesaj içeriği, anket cevabı veya kişisel geri bildirim detayı göstermez.",),
        evidence=(
            f"condensed verbatim from {_STEP_GUIDE_SOURCE}:259-273 (communication_steps); this single legacy "
            "topic spans 4 different screens (bildirimler/duyurular/anketler/mesajlar) -- required_permission "
            "approximated to 'announcements' (the module's flagship, already-verified key) since no single "
            "exact key covers all four; the guide text itself still names each correct screen"
        ),
    ),
    ProceduralGuideEntry(
        guide_key="performance_mgmt_guide_kpi_targets",
        module_key="performance_mgmt",
        intent_tags=("kpi", "hedef", "stratejik", "riskli hedef", "kpi target"),
        title="KPI ve Hedef Yönetimi",
        summary="KPI Dashboardu ve Hedef Yönetimi ekranlarının kullanımını açıklar.",
        steps=(
            "Performans Yönetimi bölümünden KPI Dashboardu ekranını açın.",
            "Hedef durumlarını, gerçekleşme oranlarını ve riskli hedefleri kontrol edin.",
            "Hedef eklemek veya düzenlemek için KPI ve Hedef Yönetimi ekranına geçin.",
            "Hedef kartında hedef adı, kapsam, sahip, ağırlık, hedef değer ve tarih aralığını kontrol edin.",
            "KPI Analiz Merkezi ekranından riskli veya geciken hedefleri inceleyin.",
        ),
        required_permission="performance_kpi_dashboard",
        warnings=("Asistan hedef kapatmaz, hedef değeri değiştirmez ve karar vermez; yalnızca analiz ekranına yönlendirir.",),
        evidence=f"condensed verbatim from {_STEP_GUIDE_SOURCE}:276-290 (kpi_target_steps); required_permission='performance_kpi_dashboard' reused from capability_registry.py's performance_mgmt_summarize_kpi_targets (same verified real menu_key, app/menu_registry.py:550)",
    ),
]


def get_guide(guide_key: str) -> ProceduralGuideEntry | None:
    for entry in PROCEDURAL_GUIDE_REGISTRY:
        if entry.guide_key == guide_key:
            return entry
    return None


def list_active_guides() -> list[ProceduralGuideEntry]:
    return [entry for entry in PROCEDURAL_GUIDE_REGISTRY if entry.active]


def list_guides_for_module(module_key: str) -> list[ProceduralGuideEntry]:
    return [entry for entry in PROCEDURAL_GUIDE_REGISTRY if entry.module_key == module_key]


def find_duplicate_guide_keys() -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for entry in PROCEDURAL_GUIDE_REGISTRY:
        if entry.guide_key in seen:
            duplicates.append(entry.guide_key)
        seen.add(entry.guide_key)
    return duplicates


def find_guides_with_orphan_module_key() -> list[ProceduralGuideEntry]:
    known_modules = {module.module_key for module in MODULE_REGISTRY}
    return [entry for entry in PROCEDURAL_GUIDE_REGISTRY if entry.module_key not in known_modules]


__all__ = [
    "ProceduralGuideEntry",
    "PROCEDURAL_GUIDE_REGISTRY",
    "get_guide",
    "list_active_guides",
    "list_guides_for_module",
    "find_duplicate_guide_keys",
    "find_guides_with_orphan_module_key",
]
