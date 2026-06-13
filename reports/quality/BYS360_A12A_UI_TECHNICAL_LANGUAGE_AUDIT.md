# BYS360 A12A UI Teknik Dil Audit

Tarih: 2026-06-13T08:39:22

## Sonuç

- OK: True
- Karar: A12A_AUDIT_COMPLETED
- Taranan dosya sayısı: 678
- Finding count: 3794
- High risk user visible count: 768
- Compileall returncode: 0
- Pytest returncode: 0

## Pytest Summary

```json
{
  "passed": 744,
  "skipped": 2,
  "deselected": 34
}
```

## Family Dağılımı

```json
{
  "project_phase_terms": 2673,
  "hard_ui": 770,
  "developer_ui_terms": 351
}
```

## File Class Dağılımı

```json
{
  "static_user_visible_asset": 1333,
  "other_review": 2,
  "template_user_visible": 2459
}
```

## En Çok Bulgu Olan Dosyalar

```json
{
  "app/static/js/bys360_assistant_module.js": 220,
  "app/templates/performance/feedback_aftercare_new.html": 200,
  "app/templates/performance_scorecard_detail.html": 149,
  "app/static/css/bys360_mobile_app_experience_v5.css": 128,
  "app/templates/performance/meeting_development_faz10.html": 127,
  "app/templates/base.html": 91,
  "app/templates/communication/phase1_dashboard.html": 76,
  "app/static/css/bys360_home_weather.css": 70,
  "app/static/js/survey_builder_phase2.js": 66,
  "app/static/js/survey_builder_phase3.js": 65,
  "app/static/css/phase5_5_scorecard_mobile.css": 59,
  "app/templates/performance/president_card_review.html": 54,
  "app/static/css/survey_jotform_phase2.css": 44,
  "app/templates/periods.html": 42,
  "app/templates/home.html": 40,
  "app/templates/performance/_development_guidance_scorecard_section.html": 40,
  "app/static/css/survey_jotform_phase3.css": 39,
  "app/static/css/ai_decision_faz10.css": 37,
  "app/static/css/survey_jotform_phase1.css": 36,
  "app/templates/corporate_information_center/overview.html": 36,
  "app/templates/performance_low_score_processes.html": 36,
  "app/templates/performance/_phase5_scorecard_ui_styles.html": 33,
  "app/templates/settings.html": 33,
  "app/templates/performance_v2_phase3_assignment.html": 32,
  "app/static/css/corporate_information_center_v3_0_phase6.css": 31,
  "app/static/css/ai_decision_faz11.css": 26,
  "app/static/css/bys360_portal.css": 25,
  "app/templates/ai_decision/_interim_feedback_panel.html": 25,
  "app/templates/performance/feedback_aftercare.html": 25,
  "app/templates/performance/meeting_p4_development_guidance.html": 24,
  "app/templates/performance/_phase5_microguide.html": 23,
  "app/templates/portal/feed.html": 23,
  "app/templates/scorecard_pdf.html": 23,
  "app/static/css/corporate_information_center_v3_0_phase7.css": 22,
  "app/static/css/faz4_support_account_mobile.css": 20,
  "app/templates/evaluation_form.html": 20,
  "app/templates/communication/phase9b_dashboard.html": 19,
  "app/templates/performance/evaluation_form.html": 18,
  "app/static/js/bys360_screen_title_fix_v18_8.js": 17,
  "app/templates/communication/phase9_release_center.html": 17,
  "app/templates/communication/phase9d_stabilization_center.html": 17,
  "app/templates/hr_attendance.html": 17,
  "app/templates/ai_decision/faz12_final_gate.html": 16,
  "app/templates/feedback_meetings_list.html": 16,
  "app/static/css/ai_decision_faz7_historical_archive.css": 15,
  "app/static/css/ai_decision_faz8_period_scope.css": 15,
  "app/static/js/bys360_assistant_performance_kb_v10.js": 15,
  "app/templates/communication/phase9c_pilot_opening_center.html": 15,
  "app/templates/portal/_composer.html": 15,
  "app/static/css/ai_decision_faz9_reminder.css": 14
}
```

## High Risk User Visible Bulgular

```json
[
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 2,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-panel {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 11,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-head {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 20,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-eyebrow {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 29,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-head h2 {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 35,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-head p {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 40,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-count {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 48,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-count strong {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 53,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-count span { font-size: 12px; }"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 54,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-summary {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 60,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-summary div {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 66,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-summary span {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 72,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-summary strong {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 76,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-grid {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 81,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-card {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 87,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-card-top {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 96,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-card-top em {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 101,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-card h3 {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 106,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-card p {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 111,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-card small {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 119,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-card.priority-critical { border-color: rgba(139, 0, 0, 0.30); }"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 120,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-card.priority-high { border-color: rgba(139, 0, 0, 0.22); }"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 121,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-note {"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 127,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-head { flex-direction: column; }"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 128,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-summary,"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 129,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-grid { grid-template-columns: 1fr; }"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "line_no": 130,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": ".ai-dev-guidance-count { width: 100%; }"
  },
  {
    "path": "app/static/css/app.css",
    "line_no": 472,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "/* Sayfa başlığı bloğu varsa orada da kırmızı dev banner etkisini azaltır. */"
  },
  {
    "path": "app/static/css/bys360_ai_agent_panel.css",
    "line_no": 13,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": ".ai-agent-ask-bar{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:end}.ai-agent-ask-bar textarea{min-height:62px;resize:vertical;border-radius:18px;border:1px solid rgba(139,0,0,.14);padding:12px;outline:none}.ai-agent-ask-bar button,.ai-agent-refresh{border-radius:16px;padding:12px 16px;color:#fff;background:linear-gradient(135deg,#680000,#8B0000 52%,#b91c1c);box-shadow:0 10px 22px rgba(139,0,0,.18)}.ai-agent-metrics-grid{grid-template-columns:repeat(4,minmax(0,1fr))}.ai-agent-"
  },
  {
    "path": "app/static/css/bys360_android_responsive_completion_v2.css",
    "line_no": 108,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "@media (max-width:980px), (pointer:coarse) and (max-device-width:980px){"
  },
  {
    "path": "app/static/css/bys360_assistant_module.css",
    "line_no": 4,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "/* BYS360_ASISTANI_MODULU_PERSONEL_LEAVE_DELEGATION_KB_V9 | Personel/izin/devamsızlık/vekâlet bilgi bankası */"
  },
  {
    "path": "app/static/css/bys360_elegant_hero_overrides.css",
    "line_no": 133,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "/* Başlıklar: dev ve kaba değil; yönetici ekranına yakışan ölçü */"
  },
  {
    "path": "app/static/css/bys360_elegant_hero_overrides.css",
    "line_no": 605,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "/* Sayfa başlığı bloğu varsa orada da kırmızı dev banner etkisini azaltır. */"
  },
  {
    "path": "app/static/css/bys360_live_hero_polish.css",
    "line_no": 258,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "/* Sayfa başlığı bloğu varsa orada da kırmızı dev banner etkisini azaltır. */"
  },
  {
    "path": "app/static/css/bys360_mobile_clean_native_v4.css",
    "line_no": 3,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "Önceki Faz1/V2/V3 dosyaları base.html'den devre dışı bırakılır; bu dosya mobilde tek otoritedir. */"
  },
  {
    "path": "app/static/css/bys360_mobile_white_screen_maintenance_v6.css",
    "line_no": 1,
    "family": "hard_ui",
    "term": "Repair",
    "file_class": "static_user_visible_asset",
    "line": "/* BYS360 Mobile White Screen Repair V6"
  },
  {
    "path": "app/static/css/bys360_mobile_white_screen_maintenance_v6.css",
    "line_no": 2,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "Amaç: V5 asistan kopya katmanını devreden çıkarınca mobil sayfanın görünür ve kaydırılabilir kalmasını sağlamak. */"
  },
  {
    "path": "app/static/css/bys360_topbar_sidebar_clean_v9.css",
    "line_no": 3,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "Menü sırası, Kullanıcı bölümü, Jinja/route yapısı değiştirilmez. */"
  },
  {
    "path": "app/static/css/dashboard_showcase.css",
    "line_no": 619,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "/* Sayfa başlığı bloğu varsa orada da kırmızı dev banner etkisini azaltır. */"
  },
  {
    "path": "app/static/css/performance_completion_phase9_development_guidance.css",
    "line_no": 1,
    "family": "hard_ui",
    "term": "DEV",
    "file_class": "static_user_visible_asset",
    "line": "/* BYS360_PERFORMANCE_COMPLETION_PHASE9_DEVELOPMENT_GUIDANCE_CSS */"
  },
  {
    "path": "app/static/js/bys360_ai_everywhere_v1.js",
    "line_no": 103,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "test:function(p){return /interim-notes|donem-ici-not|feedback-aftercare|feedback-meeting-guide|feedback-followup|development|gelisim|gelişim|meeting-development/i.test(p);},"
  },
  {
    "path": "app/static/js/bys360_ai_everywhere_v1.js",
    "line_no": 110,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "links:[['Dönem İçi Notlar','/performance/interim-notes'],['Gelişim Rehberi','/performance/meeting-development/faz10']]"
  },
  {
    "path": "app/static/js/bys360_ai_everywhere_v1.js",
    "line_no": 151,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "action:'Rol matrisi, kişi bazlı görünürlük, modül ayarı ve route erişim kontrolünü birlikte düşünmenizi sağlar.',"
  },
  {
    "path": "app/static/js/bys360_android_responsive_completion_v2.js",
    "line_no": 38,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "var wanted = \"width=device-width, initial-scale=1, viewport-fit=cover, interactive-widget=resizes-content\";"
  },
  {
    "path": "app/static/js/bys360_android_responsive_completion_v2.js",
    "line_no": 39,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "if (!/width\\s*=\\s*device-width/i.test(content) || !/viewport-fit\\s*=\\s*cover/i.test(content)) {"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 104,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "{ title: 'Devamsızlık ve Vekâlet', href: '/hr-management/attendance', keywords: ['vekalet', 'vekâlet', 'devamsizlik', 'devamsızlık', 'gorev devri', 'görev devri', 'vekil', 'vekil personel', 'vekalet tanimla'], text: 'Devamsızlık kayıtları ve vekâlet tanımları bu ekranda takip edilir.' },"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 114,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "{ title: 'Gelişim Rehberi', href: '/performance/meeting-development/faz10', keywords: ['gelisim rehberi', 'gelisim onerisi', 'egitim onerisi'], text: 'Değerlendirme sonrası gelişim önerileri ve rehber notlar için kullanılır.' },"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 366,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "return /\\b(bu sayfa|bu ekran|burada ne|neredeyim|hangi ekrandayim|hangi ekrandayım|hangi sayfadayim|hangi sayfadayım|sayfa yardimi|sayfa yardımı|ekran yardimi|ekran yardımı|az onceki konu|az önceki konu|kaldigimiz yer|kaldığımız yer|devam edelim|nereden devam|sayfa değişince|sayfa degisince|konusmalar silinmesin|konuşmalar silinmesin|sohbet kayboluyor)\\b/.test(n);"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 575,
    "family": "hard_ui",
    "term": "DEV",
    "file_class": "static_user_visible_asset",
    "line": "// V5_SAYFA_BAZLI_YARDIM_OTURUM_DEVAMLILIGI"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 610,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "function routeForCurrentPage() {"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 616,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "var sayfa yolu = routeForCurrentPage();"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 620,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "routeTitle: sayfa yolu ? sayfa yolu.title : '',"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 621,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "routeText: sayfa yolu ? sayfa yolu.text : '',"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 671,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "var sayfa yolu = routeForCurrentPage();"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 676,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "parts.push('Bu ekranda işlem yaparken rol matrisi, kişi/birim bazlı görünürlük ve güvenli erişim sınırları geçerlidir. Ne yapmak istediğinizi yazarsanız bu ekrandan devam edilecek adımları sırayla anlatırım.');"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 686,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "var sayfa yolu = routeForCurrentPage();"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 687,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "var text = 'Aynı oturum içinde kaldığımız yerden devam edebiliriz.';"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 689,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "else if (ctx && (ctx.routeTitle || ctx.heading)) text += ' Son bağlam: “' + (ctx.routeTitle || ctx.heading) + '”.';"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 691,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "text += ' Bir önceki işlemden devam etmek için yapmak istediğiniz adımı yazın; ben aynı oturum bağlamını koruyarak yönlendireceğim.';"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 700,
    "family": "hard_ui",
    "term": "DEV",
    "file_class": "static_user_visible_asset",
    "line": "// V9_PERSONEL_IZIN_DEVAMSIZLIK_VEKALET_TAM_BILGI_BANKASI"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 747,
    "family": "hard_ui",
    "term": "DEV",
    "file_class": "static_user_visible_asset",
    "line": "// V9_PERSONEL_IZIN_DEVAMSIZLIK_VEKALET_TAM_BILGI_BANKASI_CEVAPLARI"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 773,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "return moduleStepAnswer('İzin kaydı / izin talebi', 'Sol şerit > Personel Yönetimi > İzin ve Devamsızlık Takibi', ['Personel Yönetimi yetkilisi', 'İK/personel yetkilisi', 'Yetkili amir', 'Kurum ayarına göre personelin kendisi'], ['İzin ve Devamsızlık Takibi ekranını açın', 'Yeni izin kaydı veya izin talebi işlemini seçin', 'İlgili personeli seçin', 'İzin türünü belirleyin', 'Başlangıç ve bitiş tarih/saat bilgisini girin', 'Gerekirse açıklama ve belge ekleyin', 'Kaydedin veya onaya gönderin', 'On"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 780,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "if (/\\b(devamsizlik nedir|devamsızlık nedir|devamsizlik kaydi|devamsızlık kaydı|devamsizlik nasil|devamsızlık nasıl|ise gelmedi|işe gelmedi|gec kaldi|geç kaldı)\\b/.test(n)) {"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 781,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "return moduleStepAnswer('Devamsızlık kaydı', 'Sol şerit > Personel Yönetimi > Devamsızlık ve Vekâlet', ['Personel Yönetimi yetkilisi', 'İK/personel yetkilisi', 'Yetkili amir'], ['Devamsızlık ve Vekâlet ekranını açın', 'Personeli seçin', 'Devamsızlık türünü veya olay tipini belirleyin', 'Tarih/saat bilgisini girin', 'Gerekli açıklama veya belgeyi ekleyin', 'Kaydedin', 'Kayıt sonrası rapor ve personel geçmişi etkisini kontrol edin'], ['Devamsızlık kaydı personel geçmişi, izin dengelemesi ve raporl"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 784,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "if (/\\b(vekalet nasil|vekâlet nasıl|vekalet tanimla|vekâlet tanımla|vekil ata|gorev devri|görev devri|amir izinli|izinli amir|vekalet nerede|vekâlet nerede)\\b/.test(n)) {"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 785,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "return moduleStepAnswer('Vekâlet tanımlama', 'Sol şerit > Personel Yönetimi > Devamsızlık ve Vekâlet', ['Admin', 'Personel Yönetimi yetkilisi', 'İK/personel yetkilisi', 'Yetkili amir'], ['Devamsızlık ve Vekâlet ekranını açın', 'Asıl personeli veya izinli amiri seçin', 'Vekil olacak personeli seçin', 'Başlangıç ve bitiş tarihlerini belirleyin', 'Vekâlet kapsamını seçin', 'Kaydedin', 'İlgili süreçlerde vekilin yetki/görev devrinin doğru çalıştığını kontrol edin'], ['Vekâlet süresi izin/devamsızlık"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 789,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "return makeAnswer('İzinli amir varsa BYS360’da önce izin/devamsızlık kaydı ve varsa vekâlet tanımı kontrol edilmelidir. Performans sürecinde değerlendirme görevinin boşa düşmemesi için vekil veya yetkili akış kurum kuralına göre devreye alınır. Asistan performans puanı belirlemez; yalnızca doğru ekranları ve kontrol adımlarını gösterir: önce İzin ve Devamsızlık Takibi, sonra Devamsızlık ve Vekâlet, ardından ilgili performans görev/süreç ekranı kontrol edilir.', [{ title: 'İzin ve Devamsızlık Tak"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 805,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "if (/\\b(bu ekranda ne yapabilirim|bu sayfada ne yapabilirim|burada ne yapacagim|burada ne yapacağım|sayfa yardimi|sayfa yardımı|ekran yardimi|ekran yardımı|nereden devam|nereden devam edecegim|nereden devam edeceğim)\\b/.test(n)) {"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 809,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "if (/\\b(az onceki konu|az önceki konu|kaldigimiz yer|kaldığımız yer|devam edelim|kaldigimiz yerden|kaldığımız yerden|onceki konudan|önceki konudan)\\b/.test(n)) {"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 845,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "return makeAnswer('Size BYS360 içinde adım adım rehberlik ederim: personel kaydı, izin, devamsızlık, vekâlet, performans Dönemler, Sorular / Kriterler, Değerlendirme Görevleri, Başkan Onayları, karne, raporlar, rol matrisi, menü görünürlüğü, destek talepleri, anketler, mesajlar, bildirimler ve AI Karar Destek ayrımı gibi konularda yardımcı olurum. Soruyu eksik veya günlük dille yazsanız bile niyetinizi BYS360 ekranlarıyla eşleştirmeye çalışırım. İdari karar üretmem, performans puanı belirlemem v"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 877,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "if (/\\b(vekalet|vekâlet|devamsizlik|devamsızlık|vekil|gorev devri|görev devri)\\b/.test(n)) {"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 878,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "return makeAnswer('Devamsızlık ve vekâlet için doğru yol: Sol şerit > Personel Yönetimi > Devamsızlık ve Vekâlet. Bu ekranda devamsızlık kayıtları izlenir; vekâlet tanımlanacaksa asıl kişi, vekil personel, başlangıç-bitiş tarihi, vekâlet kapsamı ve not bilgisi girilir. Kaydettikten sonra vekâlet kayıtları listesinde durum kontrol edilir. Vekâlet, özellikle izinli amirlerde performans/onay görevlerinin doğru kişiye yönlenmesi için kullanılır.', ["
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 897,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "return makeAnswer('Performans notu için doğru yol: Sol şerit > Performans Yönetimi > Dönem İçi Notlar. Bu ekran puan verme ekranı değildir; dönem içindeki olumlu/olumsuz gözlem, başarı, gelişim ihtiyacı veya genel not kaydı için kullanılır. Adım adım: 1) Dönem İçi Notlar sekmesini açın. 2) Yeni Not / Not Ekle butonuna basın. 3) İlgili dönem ve personeli seçin. 4) Not türünü ve açıklamayı yazın. 5) Kaydedin. Notlar otomatik puan üretmez; değerlendirme döneminde amire hatırlatma ve gelişim desteği"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 925,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "if (/\\b(izin ve devamsizlik|izin ve devamsızlık|izin nasil calisir|izin nasıl çalışır|izin sureci|izin süreci|izin detay)\\b/.test(n)) {"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 926,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "return makeAnswer('İzin süreci şöyle çalışır: 1) Sol şerit > Personel Yönetimi > İzin ve Devamsızlık Takibi ekranına girilir. 2) Personel seçilir. 3) İzin türü ve tarih aralığı girilir. 4) Gerekirse açıklama, belge ve vekil personel bilgisi eklenir. 5) Kayıt oluşturulur. 6) İzin bakiyesi, izin listesi ve onay/izleme durumu kontrol edilir. 7) İzinli kişi amirse Devamsızlık ve Vekâlet ekranında görev devri de kontrol edilmelidir. Bu akış performans görevleri ve onay süreçlerinin boşa düşmemesi içi"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 942,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "return makeAnswer('Destek süreci için doğru yol: Sol şerit > Yardım Merkezi. Kullanıcı önce kategori seçer, kısa bir başlık yazar, sorunu anlaşılır şekilde açıklar ve varsa ekran görüntüsü/dosya ekler. Talep kaydedildikten sonra durum, cevaplar, ek mesajlar ve kapanış bilgisi aynı alandan takip edilir. Asistan kullanım sorularında rehberlik eder; teknik sorun devam ediyorsa destek talebi oluşturulmalıdır.', [{ title: 'Yardım Merkezi', href: '/support' }]);"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1300,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "var routeTitles = ROUTES.map(function (r) { return r.title; });"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1302,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "ok: badLeft.length === 0 && routeTitles.indexOf('Dönemler') !== -1 && routeTitles.indexOf('İzin ve Devamsızlık Takibi') !== -1,"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1305,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "route_count: ROUTES.length,"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1306,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "safe_routes: routeTitles,"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1540,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "\"4. İzin, devamsızlık ve vekâlet\","
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1557,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "return \"BYS360 içinde personel işlemleri, izin-devamsızlık-vekalet süreçleri, performans dönemleri, Değerlendirme Kriterleri, görev üretimi, Başkan Onayları, karne-yayın süreci, rol matrisi, menü görünürlüğü, raporlar, destek talepleri, anketler, bildirimler ve AI Karar Destek Merkezi hakkında adım adım yardımcı olurum.\";"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1560,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "if (/izin|devamsızlık|vekalet|vekâlet/.test(q)) {"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1566,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "\"- Vekâlet ve devamsızlık takibi: Personel Yönetimi > Devamsızlık ve Vekâlet\","
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1572,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "\"4. İzin, devamsızlık veya vekâlet bilgilerini tarih aralığıyla kaydedin.\","
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1614,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "\"5. Menü görünse bile erişim yoksa backend route yetkisi ayrıca kontrol edilmelidir.\","
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1620,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "if (/bu sayfada|bu ekran|nereden devam|kaldığımız yer|az önceki konu/.test(q)) {"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1622,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "return \"Şu an bulunduğunuz ekranı dikkate alarak yardımcı olabilirim. Sayfa yolu: \" + path + \". Sorunuzu bu ekran üzerinden sorarsanız ilgili işlem adımlarını buradan devam ettiririm.\";"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1794,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "\"Bu ekrandan personelin izin kayıtları, izin tarihleri ve devamsızlık bilgileri takip edilir.\","
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1810,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "\"Bu ekran devamsızlık kayıtları ve vekâlet tanımları için kullanılır.\","
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1815,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "\"3. Amir izinliyse sürecin kime devredileceğini kontrol etme\","
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1946,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "\"nereden devam edeceğim\","
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1993,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "\"4. Backend route hata vermiş olabilir.\","
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 1998,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "\"3. Waitress/uygulama loglarında ilgili route hatasını kontrol edin.\","
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 2016,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "\"5. Menü açık görünse bile backend route yetkisi ayrıca kontrol edilmelidir.\","
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 2041,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "phrases: [\"rol matrisi yansımıyor\", \"açıyorum kapanmıyor\", \"kapattım görünmeye devam ediyor\", \"rol matrisi çalışmıyor\"],"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 2051,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "\"6. Backend route yetkisi menüden bağımsız şekilde ayrıca kontrol edilmelidir.\","
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 2130,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "\"Rapor veya dashboard açılmıyorsa veri, yetki ve route/template katmanı birlikte kontrol edilmelidir.\","
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 2136,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "\"4. Backend loglarında rapor route hatası var mı inceleyin.\","
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 2305,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "key: \"meeting_development\","
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 2306,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "urls: [\"/performance/meeting-development/faz9\", \"/performance/meeting-development\"],"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 2326,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "help: \"Şu an İzin ve Devamsızlık Takibi ekranındasınız. Personelin izin kayıtları, izin tarihleri ve devamsızlık bilgileri buradan takip edilir.\""
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 2334,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "help: \"Şu an Devamsızlık ve Vekâlet ekranındasınız. Devamsızlık bilgileri ve vekâlet ilişkileri buradan takip edilir. İzinli amir varsa süreçlerin doğru kişiye devredildiği kontrol edilmelidir.\""
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 2656,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "if (q.includes(\"vekalet\") || q.includes(\"vekâlet\") || q.includes(\"devamsızlık\")) {"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 2706,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "\"5. Backend route yetkisi ayrıca korunmalıdır.\""
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 2715,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "return \"BYS360 içinde personel işlemleri, izin-devamsızlık-vekalet süreçleri, performans dönemleri, Değerlendirme Kriterleri, görev üretimi, Başkan Onayları, karne-yayın süreci, rol matrisi, menü görünürlüğü, raporlar, destek talepleri, anketler, bildirimler ve AI Karar Destek Merkezi hakkında adım adım yardımcı olurum.\";"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 3092,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "strongKeywords: [\"izin ve devamsızlık takibi\", \"izin türü\", \"izin başlangıç\", \"izin bitiş\", \"izin kaydı\"],"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 3093,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "weakKeywords: [\"izin\", \"devamsızlık\"],"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 3094,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "help: \"Şu an İzin ve Devamsızlık Takibi ekranındasınız. Personelin izin kayıtları ve devamsızlık bilgileri buradan takip edilir.\""
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 3100,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "urlHints: [\"attendance\", \"delegation\", \"vekalet\", \"vekâlet\", \"devamsizlik\"],"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 3101,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "strongKeywords: [\"devamsızlık ve vekâlet\", \"vekil\", \"asıl kişi\", \"vekâlet başlangıç\", \"vekâlet bitiş\"],"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 3102,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "weakKeywords: [\"devamsızlık\", \"vekalet\", \"vekâlet\", \"vekil\"],"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 3353,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "\"/performance/meeting-development/faz10\": {"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 3365,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "\"/performance/meeting-development/faz9\": {"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 3734,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "\"/performance/meeting-development/faz10\": {"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 3746,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "\"/performance/meeting-development/faz9\": {"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 4230,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "keywords: ['izin', 'izin kaydı', 'izin talebi', 'izin bakiyesi', 'devamsızlık takibi'],"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 4241,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "keywords: ['devamsızlık', 'vekalet', 'vekâlet', 'vekil', 'görev devri'],"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 4244,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "attention: ['Vekâlet süresi ilgili izin/devamsızlık tarihiyle uyumlu olmalıdır.']"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 4310,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "attention: ['Menü görünürlüğü ile backend route yetkisi birlikte korunmalıdır.']"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 4577,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "keywords: ['personel', 'sicil', 'unvan', 'birim', 'üst birim', 'yönetici', 'izin', 'devamsızlık', 'vekâlet'],"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 4578,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "actions: ['Personel kaydı arama veya güncelleme', 'Birim, üst birim, unvan ve yönetici bağlantısını kontrol etme', 'İzin, devamsızlık ve vekâlet kayıtlarını izleme', 'Performans zincirini etkileyen personel verisini doğrulama'],"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 5055,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "keywords: ['izin', 'devamsızlık', 'vekâlet', 'vekalet', 'izin talebi'],"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 5056,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "description: 'Bu ekran izin, devamsızlık ve vekâlet süreçlerinin kayıtlı ve izlenebilir yürütülmesi için kullanılır.',"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 5057,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "actions: ['İzin veya devamsızlık kaydını inceleme', 'Vekâlet ilişkisini kontrol etme', 'Performans/onay süreçlerinde vekilin etkisini doğrulama'],"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 5446,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "var dataSignals = attrOf('[data-nav-key], [data-module], [data-screen], [data-page-title], [data-route], [data-' + 'end' + 'point]', ['data-nav-key', 'data-module', 'data-screen', 'data-page-title', 'data-route', 'data-' + 'end' + 'point'], 24);"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 5479,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "{ id:'development_suggestions', screen:'Gelişim Önerileri', bölüm:'Performans Yönetimi', href:'/performance/development-suggestions', paths:['/performance/development*','/performans/gelisim*','/performans/gelişim*'], keywords:['gelişim önerisi','gelişim alanı','rehber not','aksiyon planı'], family:'performance', description:'Bu ekran düşük performans veya gelişim ihtiyacı görülen alanlar için rehber gelişim önerilerinin kayıt altına alınması için kullanılır.', actions:['Gelişim notlarını incelem"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 5492,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "{ id:'leave_delegation', screen:'İzin, Devamsızlık ve Vekâlet', bölüm:'Personel Yönetimi', href:'/personnel/leaves', paths:['/personnel/leaves*','/leave*','/attendance*','/delegation*','/personnel/delegation*','/personnel/attendance*'], keywords:['izin','devamsızlık','vekâlet','vekalet','izin talebi','izin kaydı'], family:'personnel', description:'Bu ekran izin, devamsızlık ve vekâlet süreçlerinin kayıtlı ve izlenebilir yürütülmesi için kullanılır.', actions:['İzin veya devamsızlık kaydını incel"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 5950,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "{id:'leave',module:'Personel Yönetimi',screen:'İzin ve Devamsızlık Takibi',href:'/hr-management/leave',keys:['izin','izin nasıl girilir','izin nasil girilir','izin talebi','izin kaydı','izin kaydi','izin bakiyesi','devamsızlık','devamsizlik','rapor izin'],who:['Personel yetkilisi','İK/Admin','Yetki verilmiş yönetici'],steps:['Personel Yönetimi veya İzin Yönetimi bölümüne girin.','İzin Talebi / İzin Kaydı ekranını açın.','Personeli seçin.','İzin türünü, başlangıç ve bitiş tarihini girin.','Gerekl"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 5951,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "{id:'delegation',module:'Personel Yönetimi',screen:'Vekâlet Yönetimi',href:'/hr-management/attendance',keys:['vekâlet','vekalet','vekil ata','görev devri','gorev devri','asıl kişi','asil kisi','vekil kim olacak'],who:['Admin','Personel/İK yetkilisi','Yetki verilmiş yönetici'],steps:['Vekâlet Yönetimi ekranına girin.','Asıl kişiyi seçin.','Vekil olacak kişiyi seçin.','Başlangıç ve bitiş tarihini belirleyin.','Vekâlet kapsamını seçin.','Kaydedin ve ilgili süreçlerde vekilin görünüp görünmediğini k"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 5964,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "{id:'development',module:'Performans Yönetimi',screen:'Gelişim Önerisi',href:'/performance/development-guidance',keys:['gelişim önerisi','gelisim onerisi','rehber alan','eğitim önerisi','egitim onerisi','gelişim planı'],who:['Amirler, performans yetkilileri ve yetkili yöneticiler'],steps:['Gelişim Önerisi / Rehber Alan ekranına girin.','Personel veya dönem bağlamını seçin.','Güçlü yön, gelişim alanı ve takip önerisini yazın.','Kaydedin ve karne/yayın görünürlüğünü kontrol edin.'],watch:['Öneri d"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 5974,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "{id:'profile',module:'Kullanıcı Hesabı',screen:'Profil / Şifre / Oturum',href:'/account',keys:['profilim','hesabım','hesabim','şifre','sifre','parola','çıkış','cikis','oturum','giriş yapamıyorum','giris yapamiyorum'],who:['Kullanıcı kendi hesabında; Admin yetkili kullanıcı hesaplarında işlem yapar.'],steps:['Profil / Hesabım ekranına girin.','Yetkiniz dahilindeki bilgileri kontrol edin.','Şifre/parola işlemlerinde güvenlik kurallarına uyun.'],watch:['3 hatalı giriş gibi güvenlik kuralları devrey"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 6028,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "if (/(kaldigimiz yer|kaldığımız yer|devam edelim|son konu)/.test(n)) {"
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "line_no": 6030,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "return response('Kaldığımız yer', st && st.topic ? ('Son konuştuğumuz konu: ' + st.topic + '. Aynı konu üzerinden devam edebiliriz; yapmak istediğiniz adımı yazmanız yeterli.') : 'Bu oturumda kayıtlı son konu bulamadım. Yapmak istediğiniz işlemi yazarsanız kaldığınız yerden yönlendiririm.', []);"
  },
  {
    "path": "app/static/js/bys360_assistant_performance_kb_v10.js",
    "line_no": 22,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "development: safeRoute('Performans Yönetimi > Gelişim Önerileri', '/performance/development-suggestions'),"
  },
  {
    "path": "app/static/js/bys360_assistant_performance_kb_v10.js",
    "line_no": 25,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "delays: safeRoute('Performans Yönetimi > Hatırlatma ve Aksatan Amirler', '/performance/meeting-development/faz9')"
  },
  {
    "path": "app/static/js/bys360_assistant_performance_kb_v10.js",
    "line_no": 36,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "function routeLine(route){"
  },
  {
    "path": "app/static/js/bys360_assistant_performance_kb_v10.js",
    "line_no": 37,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "return route ? `Doğru ekran: ${route.label}` : '';"
  },
  {
    "path": "app/static/js/bys360_assistant_performance_kb_v10.js",
    "line_no": 49,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "answer: `Anladım. Bu işlem Performans Yönetimi içindedir.\\n\\n${routeLine(ROUTES.periods)}\\n\\nKim yapabilir?\\n- Admin\\n- Sistem Yöneticisi\\n- Performans Yetkilisi\\n- Yetki verilmiş İK/personel kullanıcısı\\n\\nAdım adım:\\n1. Sol şeritten Performans Yönetimi bölümüne girin.\\n2. Dönemler sekmesini açın.\\n3. Yeni Dönem Oluştur / Yeni Dönem Ekle butonuna basın.\\n4. Dönem adını, dönem türünü, başlangıç ve bitiş tarihini girin.\\n5. Kapsam tipini seçin: tüm kurum, birim, üst birim, kategori/grup veya seçi"
  },
  {
    "path": "app/static/js/bys360_assistant_performance_kb_v10.js",
    "line_no": 97,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "id: 'development_v10',"
  },
  {
    "path": "app/static/js/bys360_assistant_performance_kb_v10.js",
    "line_no": 139,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "routes: ROUTES,"
  },
  {
    "path": "app/static/js/bys360_assistant_role_report_support_ai_kb_v11.js",
    "line_no": 29,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "const routeLine = (route) => route ? `Doğru ekran: ${route.label}` : '';"
  },
  {
    "path": "app/static/js/bys360_assistant_role_report_support_ai_kb_v11.js",
    "line_no": 34,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "answer:`Anladım. Bu konu Sistem Ayarları ve Yetkilendirme alanındadır.\\n\\nBYS360’da rol matrisi, kullanıcıların hangi modülü, sekmeyi ve işlemi görebileceğini belirleyen merkezi kontrol yapısıdır.\\n\\nDoğru ekranlar:\\n- Sistem Ayarları > Modül Bazlı Rol Matrisi\\n- Sistem Ayarları > Performans Yönetimi Rol Matrisi\\n- Sistem Ayarları > Kullanıcı Yetkileri\\n- Sistem Ayarları > Birim Bazlı Menü Profilleri\\n\\nKim yapabilir?\\n- Admin\\n- Sistem Yöneticisi\\n- Yetki verilmiş ayar/yetki yöneticisi\\n\\nAdım "
  },
  {
    "path": "app/static/js/bys360_assistant_role_report_support_ai_kb_v11.js",
    "line_no": 74,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "answer:`BYS360 içinde yetkiniz dahilindeki işlemleri bulmanıza ve doğru sırayla tamamlamanıza yardımcı olurum.\\n\\nYardımcı olabileceğim başlıklar:\\n1. Personel işlemleri\\n2. İzin, devamsızlık ve vekâlet süreçleri\\n3. Performans Yönetimi\\n4. Dönemler, Değerlendirme Kriterleri ve görev üretimi\\n5. Başkan Onayları ve 70 altı süreçler\\n6. Rol matrisi, menü görünürlüğü ve yetki kontrolleri\\n7. Dashboard ve raporlar\\n8. Destek talepleri\\n9. Anketler, bildirimler, duyurular ve mesajlaşma\\n10. AI Karar "
  },
  {
    "path": "app/static/js/bys360_assistant_role_report_support_ai_kb_v11.js",
    "line_no": 79,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "answer:`Bu durumda ekran veya yönlendirme canlı kullanıcı deneyimine uygun olmayabilir.\\n\\nKontrol sırası:\\n1. Asistanın verdiği link güvenli menü haritasında var mı?\\n2. Sayfa 404, 500, JSON veya beyaz ekran veriyor mu?\\n3. Kullanıcının bu sayfaya yetkisi var mı?\\n4. Sol menüdeki görünürlük ile backend route yetkisi aynı mı?\\n5. Ekranda teknik ifadeler var mı: tanılama, örnek kayıt, test, faz, workflow, sync gibi?\\n6. Gerekirse destek talebi açılmalı ve ilgili ekran adı belirtilmelidir.\\n\\nDikk"
  },
  {
    "path": "app/static/js/bys360_assistant_role_report_support_ai_kb_v11.js",
    "line_no": 94,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "window.BYS360_ASSISTANT_ROLE_REPORT_SUPPORT_AI_KB_V11 = { version: VERSION, title: MODULE_TITLE, routes: ROUTES, answers, findAnswer, sanitizeText,"
  },
  {
    "path": "app/static/js/bys360_live_full_overlay_v2_13_0.js",
    "line_no": 108,
    "family": "hard_ui",
    "term": "debug",
    "file_class": "static_user_visible_asset",
    "line": "[/\\bdebug\\b/gi, \"kontrol\"],"
  },
  {
    "path": "app/static/js/bys360_live_full_overlay_v2_13_0.js",
    "line_no": 109,
    "family": "hard_ui",
    "term": "endpoint",
    "file_class": "static_user_visible_asset",
    "line": "[/\\bendpoint\\b/gi, \"bağlantı\"],"
  },
  {
    "path": "app/static/js/bys360_mobile_app_experience_v3.js",
    "line_no": 7,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "var V3_RE = /settings|ayar|role|rol|permission|yetki|matrix|matris|personnel|personel|users|kullanici|org-units|organization|birim|leave|izin|delegation|vekalet|attendance|devamsizlik/i;"
  },
  {
    "path": "app/static/js/bys360_mobile_app_experience_v3.js",
    "line_no": 9,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "var PERSONNEL_RE = /personnel|personel|users|kullanici|org-units|organization|birim|leave|izin|delegation|vekalet|attendance|devamsizlik/i;"
  },
  {
    "path": "app/static/js/bys360_mobile_app_experience_v3.js",
    "line_no": 25,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "return /rol|role|yetki|permission|matris|matrix|menü|menu|personel|sicil|unvan|birim|izin|vekalet|vekâlet|devamsizlik|devamsızlık|kullanici|kullanıcı|modül|module|ayar|settings|görünürlük|gorunurluk/.test(text);"
  },
  {
    "path": "app/static/js/bys360_mobile_native_app_v3.js",
    "line_no": 161,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "static_user_visible_asset",
    "line": "// Önceki hotfixlerden kalan kilit sınıflarını temizle."
  },
  {
    "path": "app/static/js/bys360_mobile_white_screen_maintenance_v6.js",
    "line_no": 4,
    "family": "hard_ui",
    "term": "repair",
    "file_class": "static_user_visible_asset",
    "line": "function repair() {"
  },
  {
    "path": "app/static/js/bys360_mobile_white_screen_maintenance_v6.js",
    "line_no": 25,
    "family": "hard_ui",
    "term": "repair",
    "file_class": "static_user_visible_asset",
    "line": "document.addEventListener('DOMContentLoaded', repair);"
  },
  {
    "path": "app/static/js/bys360_mobile_white_screen_maintenance_v6.js",
    "line_no": 27,
    "family": "hard_ui",
    "term": "repair",
    "file_class": "static_user_visible_asset",
    "line": "repair();"
  },
  {
    "path": "app/static/js/bys360_mobile_white_screen_maintenance_v6.js",
    "line_no": 29,
    "family": "hard_ui",
    "term": "repair",
    "file_class": "static_user_visible_asset",
    "line": "setTimeout(repair, 250);"
  },
  {
    "path": "app/static/js/bys360_mobile_white_screen_maintenance_v6.js",
    "line_no": 30,
    "family": "hard_ui",
    "term": "repair",
    "file_class": "static_user_visible_asset",
    "line": "setTimeout(repair, 900);"
  },
  {
    "path": "app/static/js/bys360_reports_ai_pro.js",
    "line_no": 40,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "holder.insertAdjacentHTML('beforeend', '<div data-bys-heavy-panels-error=\"1\" class=\"bys-pro-card bys-pro-card-pad\"><div class=\"bys-pro-empty\">Ağır dashboard panelleri şu anda yüklenemedi. Ana göstergeler çalışmaya devam ediyor.</div></div>');"
  },
  {
    "path": "app/static/js/bys360_screen_title_fix_v18_8.js",
    "line_no": 32,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "\"/performance/meeting-development/faz10\": {"
  },
  {
    "path": "app/static/js/bys360_screen_title_fix_v18_8.js",
    "line_no": 42,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "\"/performance/meeting-development/faz9\": {"
  },
  {
    "path": "app/static/js/corporate_information_center_recipients_save_v2.js",
    "line_no": 20,
    "family": "hard_ui",
    "term": "debug",
    "file_class": "static_user_visible_asset",
    "line": "var debugStaff = root.querySelector('#debugStaffCount');"
  },
  {
    "path": "app/static/js/corporate_information_center_recipients_save_v2.js",
    "line_no": 21,
    "family": "hard_ui",
    "term": "debug",
    "file_class": "static_user_visible_asset",
    "line": "var debugManager = root.querySelector('#debugManagerCount');"
  },
  {
    "path": "app/static/js/corporate_information_center_recipients_save_v2.js",
    "line_no": 61,
    "family": "hard_ui",
    "term": "debug",
    "file_class": "static_user_visible_asset",
    "line": "if(debugStaff) debugStaff.value=st;"
  },
  {
    "path": "app/static/js/corporate_information_center_recipients_save_v2.js",
    "line_no": 62,
    "family": "hard_ui",
    "term": "debug",
    "file_class": "static_user_visible_asset",
    "line": "if(debugManager) debugManager.value=mn;"
  },
  {
    "path": "app/static/js/corporate_information_center_v4_4_active_cleanup.js",
    "line_no": 26,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "['active','is-active','current','selected','router-link-active'].forEach(function(c){ a.classList.remove(c); });"
  },
  {
    "path": "app/static/js/corporate_information_center_v4_6_celebrations_studio.js",
    "line_no": 17,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "['active','is-active','current','selected','router-link-active'].forEach(function(c){a.classList.remove(c);});"
  },
  {
    "path": "app/static/js/corporate_information_center_v4_6b_celebrations_final.js",
    "line_no": 11,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "['active','is-active','current','selected','router-link-active','text-primary','link-primary','btn-link'].forEach(function(c){a.classList.remove(c);});"
  },
  {
    "path": "app/static/js/messages_mobile_maintenance.js",
    "line_no": 9,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "static_user_visible_asset",
    "line": "if (link.dataset.hotfixBound === '1') return;"
  },
  {
    "path": "app/static/js/messages_mobile_maintenance.js",
    "line_no": 10,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "static_user_visible_asset",
    "line": "link.dataset.hotfixBound = '1';"
  },
  {
    "path": "app/static/js/messages_mobile_maintenance.js",
    "line_no": 20,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "static_user_visible_asset",
    "line": "if (link.dataset.hotfixBound === '1') return;"
  },
  {
    "path": "app/static/js/messages_mobile_maintenance.js",
    "line_no": 21,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "static_user_visible_asset",
    "line": "link.dataset.hotfixBound = '1';"
  },
  {
    "path": "app/static/js/performance_dashboard_advanced.js",
    "line_no": 24,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "static_user_visible_asset",
    "line": "target.innerHTML = '<div class=\"pdash-card__head compact\"><h2>Ek analiz panelleri</h2><i class=\"fa-solid fa-layer-group\"></i></div><div class=\"pdash-heavy-placeholder\"><p>Ek analiz panelleri güvenli modda açılmadı. Ana dashboard ve hızlı geçişler çalışmaya devam eder.</p></div>';"
  },
  {
    "path": "app/templates/_premium_ui_macros.html",
    "line_no": 6,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<h4 class=\"bys-premium-hub-title\">İletişim, duyuru, anket ve randevu aynı kurumsal ritimde çalışsın</h4>"
  },
  {
    "path": "app/templates/_premium_ui_macros.html",
    "line_no": 23,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<a href=\"{{ url_for('main.feedback_meetings_list') }}\" class=\"bys-premium-nav-link {% if active == 'meetings' %}active{% endif %}\"><span><i class=\"fa-solid fa-calendar-check\"></i> Randevu Sistemi</span><i class=\"fa-solid fa-arrow-right\"></i></a>"
  },
  {
    "path": "app/templates/about_bys360.html",
    "line_no": 153,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": ".bys-device {"
  },
  {
    "path": "app/templates/about_bys360.html",
    "line_no": 161,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": ".bys-device-top {"
  },
  {
    "path": "app/templates/about_bys360.html",
    "line_no": 171,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": ".bys-device-dots { display: flex; gap: .45rem; }"
  },
  {
    "path": "app/templates/about_bys360.html",
    "line_no": 172,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": ".bys-device-dots span {"
  },
  {
    "path": "app/templates/about_bys360.html",
    "line_no": 176,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": ".bys-device-title {"
  },
  {
    "path": "app/templates/about_bys360.html",
    "line_no": 182,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": ".bys-device-body { padding: .95rem; background: rgba(255,255,255,.02); }"
  },
  {
    "path": "app/templates/about_bys360.html",
    "line_no": 183,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": ".bys-device-body img,"
  },
  {
    "path": "app/templates/about_bys360.html",
    "line_no": 591,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"bys-device\">"
  },
  {
    "path": "app/templates/about_bys360.html",
    "line_no": 592,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"bys-device-top\">"
  },
  {
    "path": "app/templates/about_bys360.html",
    "line_no": 593,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"bys-device-dots\"><span></span><span></span><span></span></div>"
  },
  {
    "path": "app/templates/about_bys360.html",
    "line_no": 594,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"bys-device-title\">{{ hero_device_title }}</div>"
  },
  {
    "path": "app/templates/about_bys360.html",
    "line_no": 597,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"bys-device-body\">"
  },
  {
    "path": "app/templates/about_bys360.html",
    "line_no": 598,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<img src=\"{{ hero_device_image_url }}\" alt=\"BYS360 dashboard ekranı\">"
  },
  {
    "path": "app/templates/account.html",
    "line_no": 534,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "Fotoğrafınız silinse bile sistem otomatik olarak varsayılan kurumsal avatarı göstermeye devam eder."
  },
  {
    "path": "app/templates/account_change_password.html",
    "line_no": 362,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "Sisteme güvenli biçimde devam edebilmek için önce şifrenizi güncellemeniz gerekiyor."
  },
  {
    "path": "app/templates/account_security_setup.html",
    "line_no": 359,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "Hesabınızı güvenli biçimde kullanmaya devam edebilmek için önce güvenlik sorunuzu tanımlamalısınız."
  },
  {
    "path": "app/templates/admin/performance_menu_visibility_settings.html",
    "line_no": 45,
    "family": "hard_ui",
    "term": "route",
    "file_class": "template_user_visible",
    "line": "<div class=\"alert alert-warning mt-4 mb-3\">Menü görünürlüğü tek başına yeterli değildir; route ve backend yetki kontrolleri de aynı anahtarlarla çalışmalıdır.</div>"
  },
  {
    "path": "app/templates/admin_system_scan.html",
    "line_no": 36,
    "family": "hard_ui",
    "term": "route",
    "file_class": "template_user_visible",
    "line": "<p class=\"scan-text\">Bu ekran; route yogunlugu, kritik tablo butunlugu, degerlendirme omurgasi ve guvenlik sertlestirme basliklarini yonetsel gozle izlenebilir hale getirir.</p>"
  },
  {
    "path": "app/templates/admin_system_scan.html",
    "line_no": 47,
    "family": "hard_ui",
    "term": "route",
    "file_class": "template_user_visible",
    "line": "<div class=\"scan-stat\"><div class=\"label\">Route</div><div class=\"value\">{{ route_count|default(0) }}</div></div>"
  },
  {
    "path": "app/templates/admin_user_create.html",
    "line_no": 421,
    "family": "hard_ui",
    "term": "route",
    "file_class": "template_user_visible",
    "line": "Amir alanları route tarafında sicil numarası olarak işlenir. Bu yüzden seçimler sicil odaklı yapılmalıdır. :contentReference[oaicite:3]{index=3}"
  },
  {
    "path": "app/templates/ai_agent/panel.html",
    "line_no": 167,
    "family": "hard_ui",
    "term": "route",
    "file_class": "template_user_visible",
    "line": "<div class=\"ai-agent-route-grid\">"
  },
  {
    "path": "app/templates/ai_agent/panel.html",
    "line_no": 344,
    "family": "hard_ui",
    "term": "route",
    "file_class": "template_user_visible",
    "line": "const href = url(item.url || item.route || item.href);"
  },
  {
    "path": "app/templates/ai_decision/_development_guidance_panel.html",
    "line_no": 4,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<section class=\"ai-dev-guidance-panel\" aria-label=\"Gelişim önerisi karar destek alanı\">"
  },
  {
    "path": "app/templates/ai_decision/_development_guidance_panel.html",
    "line_no": 5,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"ai-dev-guidance-head\">"
  },
  {
    "path": "app/templates/ai_decision/_development_guidance_panel.html",
    "line_no": 7,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<span class=\"ai-dev-guidance-eyebrow\">Karar Destek Merkezi</span>"
  },
  {
    "path": "app/templates/ai_decision/_development_guidance_panel.html",
    "line_no": 11,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"ai-dev-guidance-count\">"
  },
  {
    "path": "app/templates/ai_decision/_development_guidance_panel.html",
    "line_no": 18,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"ai-dev-guidance-summary\">"
  },
  {
    "path": "app/templates/ai_decision/_development_guidance_panel.html",
    "line_no": 24,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"ai-dev-guidance-grid\">"
  },
  {
    "path": "app/templates/ai_decision/_development_guidance_panel.html",
    "line_no": 26,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<article class=\"ai-dev-guidance-card priority-{{ card.priority or 'normal' }}\">"
  },
  {
    "path": "app/templates/ai_decision/_development_guidance_panel.html",
    "line_no": 27,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"ai-dev-guidance-card-top\">"
  },
  {
    "path": "app/templates/ai_decision/_development_guidance_panel.html",
    "line_no": 36,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<article class=\"ai-dev-guidance-card\">"
  },
  {
    "path": "app/templates/ai_decision/_development_guidance_panel.html",
    "line_no": 43,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<p class=\"ai-dev-guidance-note\">{{ guidance_context.safe_visibility_note or 'Hassas içerik gösterilmez; yalnızca yetki kapsamındaki güvenli özetler kullanılır.' }}</p>"
  },
  {
    "path": "app/templates/ai_decision/_faz9_reminder_panel.html",
    "line_no": 2,
    "family": "hard_ui",
    "term": "endpoint",
    "file_class": "template_user_visible",
    "line": "<section class=\"ai-faz9-reminder-panel\" data-ai-reminder-endpoint=\"/ai/decision-support/performance/reminders/summary\">"
  },
  {
    "path": "app/templates/ai_decision/faz11_development_guidance.html",
    "line_no": 6,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "{% include 'ai_decision/_development_guidance_panel.html' ignore missing %}"
  },
  {
    "path": "app/templates/assignment_recommendations.html",
    "line_no": 28,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"ai-title\">{{ ai_pressure_panel.headline if ai_pressure_panel else 'Görev devri baskısı' }}</div>"
  },
  {
    "path": "app/templates/assignment_recommendations.html",
    "line_no": 60,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"ai-kicker\"><i class=\"fa-solid fa-building-shield\"></i> Kalıcı görev devri baskısı</div>"
  },
  {
    "path": "app/templates/assignment_rule_audit.html",
    "line_no": 34,
    "family": "hard_ui",
    "term": "repair",
    "file_class": "template_user_visible",
    "line": "<div class=\"alert {% if audit.can_auto_repair %}alert-success{% else %}alert-danger{% endif %} border-0 shadow-sm\">"
  },
  {
    "path": "app/templates/assignment_rule_audit.html",
    "line_no": 35,
    "family": "hard_ui",
    "term": "repair",
    "file_class": "template_user_visible",
    "line": "<strong>{% if audit.can_auto_repair %}Görev üretimi güvenli.{% else %}Görev üretimi otomatik durdurulmalı.{% endif %}</strong>"
  },
  {
    "path": "app/templates/assistant_training_bank.html",
    "line_no": 154,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<article class=\"bys360-teach-track\" data-tags=\"personel izin devamsızlık vekalet organizasyon sicil\">"
  },
  {
    "path": "app/templates/assistant_training_bank.html",
    "line_no": 157,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<p>Personel kaydı, sicil, birim, üst birim, yönetici, izin, devamsızlık ve vekâlet işlemlerini güvenli sırayla anlatır.</p>"
  },
  {
    "path": "app/templates/assistant_training_bank.html",
    "line_no": 184,
    "family": "hard_ui",
    "term": "route",
    "file_class": "template_user_visible",
    "line": "<h3><i class=\"fa-solid fa-route\"></i> Ekran Tanıma Akışı</h3>"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 9,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 288,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<link rel=\"apple-touch-startup-image\" href=\"/static/pwa/splash/iphone5.png\" media=\"(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)\">"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 289,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<link rel=\"apple-touch-startup-image\" href=\"/static/pwa/splash/iphone8.png\" media=\"(device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2)\">"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 290,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<link rel=\"apple-touch-startup-image\" href=\"/static/pwa/splash/iphone11.png\" media=\"(device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 2)\">"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 291,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<link rel=\"apple-touch-startup-image\" href=\"/static/pwa/splash/iphone14.png\" media=\"(device-width: 390px) and (device-height: 844px) and (-webkit-device-pixel-ratio: 3)\">"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 292,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<link rel=\"apple-touch-startup-image\" href=\"/static/pwa/splash/iphone14pro.png\" media=\"(device-width: 393px) and (device-height: 852px) and (-webkit-device-pixel-ratio: 3)\">"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 293,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<link rel=\"apple-touch-startup-image\" href=\"/static/pwa/splash/iphone14promax.png\" media=\"(device-width: 430px) and (device-height: 932px) and (-webkit-device-pixel-ratio: 3)\">"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 294,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<link rel=\"apple-touch-startup-image\" href=\"/static/pwa/splash/ipad_9_7.png\" media=\"(device-width: 768px) and (device-height: 1024px) and (-webkit-device-pixel-ratio: 2)\">"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 295,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<link rel=\"apple-touch-startup-image\" href=\"/static/pwa/splash/ipad_10_5.png\" media=\"(device-width: 834px) and (device-height: 1112px) and (-webkit-device-pixel-ratio: 2)\">"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 296,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<link rel=\"apple-touch-startup-image\" href=\"/static/pwa/splash/ipad_11.png\" media=\"(device-width: 834px) and (device-height: 1194px) and (-webkit-device-pixel-ratio: 2)\">"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 297,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<link rel=\"apple-touch-startup-image\" href=\"/static/pwa/splash/ipad_12_9.png\" media=\"(device-width: 1024px) and (device-height: 1366px) and (-webkit-device-pixel-ratio: 2)\">"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 384,
    "family": "hard_ui",
    "term": "endpoint",
    "file_class": "template_user_visible",
    "line": "{% set current_ep = request.endpoint or '' %}"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 408,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "{% set performance_subsection_visible = menu_map.get('scorecards', False) or menu_map.get('performance_dashboard', False) or menu_map.get('performance_criteria', False) or menu_map.get('criteria', False) or menu_map.get('performance_periods', False) or menu_map.get('periods', False) or menu_map.get('performance_evaluation_tasks', False) or menu_map.get('assignments', False) or menu_map.get('performance_task_management', False) or menu_map.get('performance_hierarchy_tree', False) or menu_map.get("
  },
  {
    "path": "app/templates/base.html",
    "line_no": 437,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "{% set is_perf_open = current_ep.startswith('main.performance_criteria') or current_ep.startswith('main.performance_period') or current_ep.startswith('main.performance_task_management') or current_ep.startswith('main.performance_hierarchy') or current_ep.startswith('main.performance_v2_phase5') or current_ep.startswith('main.performance_feedback') or current_ep.startswith('main.feedback_') or is_publish_active or current_path.startswith('/performance/hierarchy') or current_path.startswith('/perf"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 546,
    "family": "hard_ui",
    "term": "route",
    "file_class": "template_user_visible",
    "line": "{% if menu_map.get('performance_process_tracking', False) %}{{ nav_item(safe_url_for('main.performance_process_tracking', fallback='/performance/process-tracking'), 'fa-route', 'Süreç Takibi', current_path.startswith('/performance/process-tracking') or current_path.startswith('/performans/surec-takibi')) }}{% endif %}"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 550,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "{% if menu_map.get('performance_meeting_p3_reminders', False) %}{{ nav_item(safe_url_for('main.performance_meeting_p3_reminders', fallback='/performance/meeting-development/faz9'), 'fa-bell', 'Hatırlatma ve Aksatan Amirler', current_path.startswith('/performance/meeting-development/faz9') or current_path.startswith('/performans/toplanti-gelistirme/faz9-hatirlatma')) }}{% endif %}"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 556,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "{% if menu_map.get('performance_development_guidance', False) %}{{ nav_item(safe_url_for('main.performance_meeting_p4_development_guidance', fallback='/performance/meeting-development/faz10'), 'fa-seedling', 'Gelişim Rehberi', current_path.startswith('/performance/meeting-development/faz10') or current_path.startswith('/performans/toplanti-gelistirme/faz10-gelisim-rehberi')) }}{% endif %}"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 558,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "{% if menu_map.get('performance_feedback_meetings', False) %}{{ nav_item(safe_url_for('main.manager_feedback_requests'), 'fa-comments', 'Geri Bildirim Talepleri', current_path.startswith('/performance/feedback-requests')) }}{{ nav_item(safe_url_for('main.feedback_meetings_list'), 'fa-calendar-week', 'Randevu Sistemi', current_path.startswith('/performance/feedback-meetings')) }}{% endif %}"
  },
  {
    "path": "app/templates/base.html",
    "line_no": 729,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"modal-dialog modal-dialog-centered\"><div class=\"modal-content\"><div class=\"modal-header\"><h5 class=\"modal-title\" id=\"aboutBys360ModalLabel\"><span class=\"modal-title-icon\"><i class=\"fa-solid fa-circle-info\"></i></span><span>{{ about_modal.title|default('BYS360 Hakkında') }}</span></h5><button type=\"button\" class=\"btn-close\" data-bs-dismiss=\"modal\" aria-label=\"Kapat\"></button></div><div class=\"modal-body\"><div class=\"about-version-row\">{% for badge in about_modal.badges|default(['Kurum"
  },
  {
    "path": "app/templates/communication/phase2_survey_builder.html",
    "line_no": 13,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"col-md-4\"><label class=\"form-label fw-bold\">Şablon kullan</label><select name=\"template_id\" class=\"form-select\" {% if mode == 'edit' %}disabled{% endif %}><option value=\"\">Şablon seçmeden devam et</option>{% for row in templates %}<option value=\"{{ row.id }}\">{{ row.title }}</option>{% endfor %}</select>{% if mode == 'edit' %}<div class=\"form-text\">Düzenleme modunda mevcut soru yapısı kullanılır.</div>{% endif %}</div>"
  },
  {
    "path": "app/templates/communication/phase9_release_center.html",
    "line_no": 39,
    "family": "hard_ui",
    "term": "Hotfix",
    "file_class": "template_user_visible",
    "line": "<li>Hotfix ve rollback kararı yazılı kayıtla yönetilir.</li>"
  },
  {
    "path": "app/templates/communication/phase9_release_center.html",
    "line_no": 114,
    "family": "hard_ui",
    "term": "Hotfix",
    "file_class": "template_user_visible",
    "line": "<li>Hotfix ve rollback kararı yazılı kayıtla yönetilir.</li>"
  },
  {
    "path": "app/templates/communication/phase9b_dashboard.html",
    "line_no": 10,
    "family": "hard_ui",
    "term": "migration",
    "file_class": "template_user_visible",
    "line": "<p class=\"text-muted mb-0\">Veri geçişi, migration görünürlüğü, sicil omurgası ve güvenlik kapıları için canlı öncesi kontrol merkezi.</p>"
  },
  {
    "path": "app/templates/communication/phase9b_dashboard.html",
    "line_no": 72,
    "family": "hard_ui",
    "term": "migration",
    "file_class": "template_user_visible",
    "line": "<div class=\"small text-muted mb-2\">Versiyon klasörü: {{ payload.migration.versions_dir }}</div>"
  },
  {
    "path": "app/templates/communication/phase9b_dashboard.html",
    "line_no": 74,
    "family": "hard_ui",
    "term": "migration",
    "file_class": "template_user_visible",
    "line": "<li class=\"list-group-item d-flex justify-content-between\"><span>Versiyon dosyası</span><strong>{{ payload.migration.version_count }}</strong></li>"
  },
  {
    "path": "app/templates/communication/phase9b_dashboard.html",
    "line_no": 75,
    "family": "hard_ui",
    "term": "migration",
    "file_class": "template_user_visible",
    "line": "<li class=\"list-group-item d-flex justify-content-between\"><span>SQL hotfix dosyası</span><strong>{{ payload.migration.sql_count }}</strong></li>"
  },
  {
    "path": "app/templates/communication/phase9b_dashboard.html",
    "line_no": 75,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "template_user_visible",
    "line": "<li class=\"list-group-item d-flex justify-content-between\"><span>SQL hotfix dosyası</span><strong>{{ payload.migration.sql_count }}</strong></li>"
  },
  {
    "path": "app/templates/communication/phase9b_dashboard.html",
    "line_no": 76,
    "family": "hard_ui",
    "term": "migration",
    "file_class": "template_user_visible",
    "line": "<li class=\"list-group-item d-flex justify-content-between\"><span>Son dosya</span><strong>{{ payload.migration.latest_version.name if payload.migration.latest_version else '-' }}</strong></li>"
  },
  {
    "path": "app/templates/communication/phase9b_transition_center.html",
    "line_no": 9,
    "family": "hard_ui",
    "term": "migration",
    "file_class": "template_user_visible",
    "line": "<p class=\"text-muted mb-0\">Sicil omurgası, migration görünürlüğü, env sertleştirmesi ve güvenlik denetimi aynı ekranda yönetilir.</p>"
  },
  {
    "path": "app/templates/communication/phase9d_dashboard.html",
    "line_no": 10,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "template_user_visible",
    "line": "<p class=\"text-muted mb-0\">İlk 72 saat stabilizasyonu, sıcak izleme sinyalleri, hotfix baskısı ve kapanış kararları için merkezi görünüm.</p>"
  },
  {
    "path": "app/templates/communication/phase9d_dashboard.html",
    "line_no": 96,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "template_user_visible",
    "line": "<h5 class=\"mb-0\">Son hotfix kayıtları</h5>"
  },
  {
    "path": "app/templates/communication/phase9d_dashboard.html",
    "line_no": 103,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "template_user_visible",
    "line": "{% for row in payload.hotfix_rows %}"
  },
  {
    "path": "app/templates/communication/phase9d_dashboard.html",
    "line_no": 113,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "template_user_visible",
    "line": "<tr><td colspan=\"3\" class=\"text-muted\">Henüz hotfix kaydı bulunmuyor.</td></tr>"
  },
  {
    "path": "app/templates/communication/phase9d_stabilization_center.html",
    "line_no": 9,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "template_user_visible",
    "line": "<p class=\"text-muted mb-0\">İlk 72 saatte check-in, hotfix ve saha sinyalleri aynı merkezden kayıt altına alınır.</p>"
  },
  {
    "path": "app/templates/communication/phase9d_stabilization_center.html",
    "line_no": 73,
    "family": "hard_ui",
    "term": "Hotfix",
    "file_class": "template_user_visible",
    "line": "<h5 class=\"mb-3\">Hotfix kaydı</h5>"
  },
  {
    "path": "app/templates/communication/phase9d_stabilization_center.html",
    "line_no": 74,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "template_user_visible",
    "line": "<form method=\"post\" action=\"{{ url_for('main.communication_phase9d_hotfix_create') }}\" class=\"vstack gap-3\">"
  },
  {
    "path": "app/templates/communication/phase9d_stabilization_center.html",
    "line_no": 75,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "template_user_visible",
    "line": "<input type=\"hidden\" name=\"hotfix_token\" value=\"{{ hotfix_token }}\">"
  },
  {
    "path": "app/templates/communication/phase9d_stabilization_center.html",
    "line_no": 93,
    "family": "hard_ui",
    "term": "Hotfix",
    "file_class": "template_user_visible",
    "line": "<button class=\"btn btn-outline-danger\" type=\"submit\">Hotfix kaydet</button>"
  },
  {
    "path": "app/templates/corporate_information_center/recipients.html",
    "line_no": 47,
    "family": "hard_ui",
    "term": "debug",
    "file_class": "template_user_visible",
    "line": "<input type=\"hidden\" name=\"debug_staff_count\" id=\"debugStaffCount\" value=\"0\">"
  },
  {
    "path": "app/templates/corporate_information_center/recipients.html",
    "line_no": 48,
    "family": "hard_ui",
    "term": "debug",
    "file_class": "template_user_visible",
    "line": "<input type=\"hidden\" name=\"debug_manager_count\" id=\"debugManagerCount\" value=\"0\">"
  },
  {
    "path": "app/templates/db_check.html",
    "line_no": 735,
    "family": "hard_ui",
    "term": "migration",
    "file_class": "template_user_visible",
    "line": "Bu kayıtlar mimari uyumsuzluk veya migration eksikliği gösterebilir."
  },
  {
    "path": "app/templates/errors/403.html",
    "line_no": 6,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
  },
  {
    "path": "app/templates/errors/503.html",
    "line_no": 5,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
  },
  {
    "path": "app/templates/errors/503.html",
    "line_no": 22,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<p class=\"muted\">Sağlık uçları erişime açıksa izleme sistemleri çalışmaya devam eder.</p>"
  },
  {
    "path": "app/templates/feedback_audit_dashboard.html",
    "line_no": 7,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "Talep ve randevu akışının işlem izi ile yönetici cevap hızını aynı ekranda görün."
  },
  {
    "path": "app/templates/feedback_audit_dashboard.html",
    "line_no": 74,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<h3 class=\"hero-title\">Talep ile randevu arasındaki işlem izini ve yönetici cevap hızını birlikte takip edin</h3>"
  },
  {
    "path": "app/templates/feedback_audit_dashboard.html",
    "line_no": 84,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<a href=\"{{ url_for('main.feedback_meetings_list', scope=selected_scope) }}\" class=\"btn-soft primary\"><i class=\"fa-solid fa-calendar-week\"></i> Randevu Listesi</a>"
  },
  {
    "path": "app/templates/feedback_audit_dashboard.html",
    "line_no": 90,
    "family": "hard_ui",
    "term": "migration",
    "file_class": "template_user_visible",
    "line": "<div class=\"side-sub\">{% if audit_ready %}Talep ve randevu aksiyonları oluştuğu anda işlem izi bu panelden izlenebilir.{% else %}Kod hazır. Veritabanında audit_logs tablosu yoksa olaylar işlenmez; canlıya geçmeden önce migration çalıştırılmalı.{% endif %}</div>"
  },
  {
    "path": "app/templates/feedback_audit_dashboard.html",
    "line_no": 90,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"side-sub\">{% if audit_ready %}Talep ve randevu aksiyonları oluştuğu anda işlem izi bu panelden izlenebilir.{% else %}Kod hazır. Veritabanında audit_logs tablosu yoksa olaylar işlenmez; canlıya geçmeden önce migration çalıştırılmalı.{% endif %}</div>"
  },
  {
    "path": "app/templates/feedback_audit_dashboard.html",
    "line_no": 96,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"glass-card stat-card\"><div class=\"stat-label\">Audit Olayı</div><div class=\"stat-value\">{{ audit_counts.event_count or 0 }}</div><div class=\"stat-sub\">Talep ve randevu akışından okunan toplam işlem izi.</div></div>"
  },
  {
    "path": "app/templates/feedback_audit_dashboard.html",
    "line_no": 98,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"glass-card stat-card\"><div class=\"stat-label\">Randevu Sayısı</div><div class=\"stat-value\">{{ audit_counts.meeting_count or 0 }}</div><div class=\"stat-sub\">Kapsama giren görüşme kaydı.</div></div>"
  },
  {
    "path": "app/templates/feedback_audit_dashboard.html",
    "line_no": 100,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"glass-card stat-card\"><div class=\"stat-label\">Ort. Planlama</div><div class=\"stat-value\">{% if audit_counts.avg_schedule_hours is not none %}{{ audit_counts.avg_schedule_hours }} sa{% else %}-{% endif %}</div><div class=\"stat-sub\">Talebin randevuya bağlanma ortalaması.</div></div>"
  },
  {
    "path": "app/templates/feedback_audit_dashboard.html",
    "line_no": 136,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"empty-box\">Henüz audit verisi oluşmadı. İlk talep veya randevu aksiyonlarından sonra bu tablo dolacaktır.</div>"
  },
  {
    "path": "app/templates/feedback_audit_dashboard.html",
    "line_no": 142,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<p class=\"section-sub\">İlk yanıtı veya randevuya bağlanması belirgin şekilde uzayan kayıtlar burada görünür.</p>"
  },
  {
    "path": "app/templates/feedback_executive_summary_dashboard.html",
    "line_no": 152,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<a class=\"mini-btn\" href=\"{{ url_for('main.feedback_meeting_detail', meeting_id=item.meeting_id, scope=selected_scope) }}\"><i class=\"fa-solid fa-calendar-check\"></i> Randevuyu Aç</a>"
  },
  {
    "path": "app/templates/feedback_go_live_center.html",
    "line_no": 82,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"glass-card stat-card\"><div class=\"stat-label\">Açık Talep</div><div class=\"stat-value\">{{ cards.open_feedback_requests or 0 }}</div><div class=\"stat-sub\">Randevuya bağlanmayı bekleyen geri bildirim talepleri.</div></div>"
  },
  {
    "path": "app/templates/feedback_go_live_center.html",
    "line_no": 223,
    "family": "hard_ui",
    "term": "endpoint",
    "file_class": "template_user_visible",
    "line": "{% for item in endpoint_checks %}"
  },
  {
    "path": "app/templates/feedback_meeting_detail.html",
    "line_no": 3,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "{% block title %}Randevu Detayı - BYS360{% endblock %}"
  },
  {
    "path": "app/templates/feedback_meeting_detail.html",
    "line_no": 5,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "{% block page_title %}Randevu Detayı{% endblock %}"
  },
  {
    "path": "app/templates/feedback_meeting_detail.html",
    "line_no": 72,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<span class=\"soft-pill\"><i class=\"fa-solid fa-calendar-days\"></i> Randevu #{{ meeting.id }}</span>"
  },
  {
    "path": "app/templates/feedback_meeting_detail.html",
    "line_no": 78,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"hero-sub\">Yönetici: {{ meeting.manager.ad }} {{ meeting.manager.soyad }} · Randevu ID: #{{ meeting.id }}{% if meeting.feedback_request and meeting.feedback_request.period %} · Dönem: {{ meeting.feedback_request.period.title }}{% endif %}{% if meeting.employee.sicil_no %} · Sicil: {{ meeting.employee.sicil_no }}{% endif %}</div>"
  },
  {
    "path": "app/templates/feedback_meeting_detail.html",
    "line_no": 85,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<a href=\"{{ url_for('main.feedback_meetings_list', scope=selected_scope) }}\" class=\"btn-soft secondary\"><i class=\"fa-solid fa-arrow-left\"></i> Randevu Listesi</a>"
  },
  {
    "path": "app/templates/feedback_meeting_detail.html",
    "line_no": 88,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<a href=\"#update-panel\" class=\"btn-soft primary\"><i class=\"fa-solid fa-pen\"></i> Randevuyu Düzenle</a>"
  },
  {
    "path": "app/templates/feedback_meeting_detail.html",
    "line_no": 93,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"side-card\"><div class=\"side-label\">Zaman Özeti</div><div class=\"side-value\">{{ meeting.meeting_date.strftime('%d.%m.%Y') if meeting.meeting_date else '-' }} · {{ meeting.meeting_start.strftime('%H:%M') if meeting.meeting_start else '--:--' }}{% if meeting.meeting_end %} - {{ meeting.meeting_end.strftime('%H:%M') }}{% endif %}</div><div class=\"side-sub\">Randevu türü ve konum bilgisi bu kartta birlikte gösterilir.</div></div>"
  },
  {
    "path": "app/templates/feedback_meeting_detail.html",
    "line_no": 133,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<p class=\"section-sub\">Talep ve bağlı randevu üzerinde yapılan son aksiyonlar.</p>"
  },
  {
    "path": "app/templates/feedback_meeting_detail.html",
    "line_no": 154,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<h3 class=\"section-title\">Randevu durumu güncelle</h3>"
  },
  {
    "path": "app/templates/feedback_meeting_detail.html",
    "line_no": 195,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"micro-box\">Bağlı amirlerden biri randevuyu oluşturduktan sonra diğer amirler de aynı kaydı düzenleyebilir. Saat çakışmaları kaydedilmeden önce yeniden kontrol edilir.</div>"
  },
  {
    "path": "app/templates/feedback_meeting_detail.html",
    "line_no": 205,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"micro-box\">Bu randevunun detaylarını görüntüleyebilirsiniz. Durum güncelleme yetkisi yalnızca randevuyu yöneten amir veya yönetici rolündeki kullanıcılar içindir.</div>"
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "line_no": 6,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "{% block title %}Randevu Sistemi - BYS360{% endblock %}"
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "line_no": 8,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "{% block page_title %}Randevu Sistemi{% endblock %}"
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "line_no": 10,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "Geri bildirim görüşmelerini, yaklaşan randevuları ve geçmiş oturumları tek bir kurumsal akışta takip edin."
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "line_no": 130,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "side_title='Sıradaki randevu',"
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "line_no": 134,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"scope-strip\"><div><strong>{{ scope_role_title or \"Kapsam görünümü\" }}</strong> · {{ scope_label or \"Kurum geneli\" }}<br><span style=\"color:#6b7280;font-size:.82rem;\">Bu görünümde {{ scope_user_count or 0 }} personel ve {{ scope_unit_count or 0 }} birim için randevu akışı izleniyor.</span></div><div style=\"display:flex;gap:8px;flex-wrap:wrap;align-items:center;\"><a href=\"{{ url_for('main.feedback_operations_dashboard', scope=selected_scope) }}\" class=\"btn-soft secondary\"><i class=\"fa-"
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "line_no": 138,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "note='Randevu sistemi, performans modülünden kopuk bir ek sayfa gibi değil; mesajlaşma ve geri bildirim akışıyla aynı kurumsal hissi taşıyor.',"
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "line_no": 139,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "metric=visible_count ~ \" görünür randevu\","
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "line_no": 143,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "{{ premium_metric_card('Toplam Randevu', filter_counts.get('all', 0), 'fa-solid fa-calendar-week', 'Sistemde sizin görünümünüze düşen toplam kayıt.') }}"
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "line_no": 146,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "{{ premium_metric_card('Benim Akışım', filter_counts.get('my_managed', 0) + filter_counts.get('my_employee', 0), 'fa-solid fa-user-clock', 'Yönettiğiniz ve katıldığınız toplam randevu görünümü.') }}"
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "line_no": 152,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"mobile-state\" id=\"meetingToolbarState\">Randevu filtreleri açık.</div>"
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "line_no": 188,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "{% call list_workspace_panel(title='Yaklaşan randevular', text='Henüz zamanı gelmemiş veya bugün gerçekleşecek görüşmeler burada listelenir.', badge=upcoming_meetings|length ~ ' kayıt', badge_tone='gray', icon='fa-solid fa-hourglass-start', note='Kartlarda kişi, zaman ve aksiyon bilgileri birlikte gösterilir.', note_icon='fa-solid fa-route') %}"
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "line_no": 188,
    "family": "hard_ui",
    "term": "route",
    "file_class": "template_user_visible",
    "line": "{% call list_workspace_panel(title='Yaklaşan randevular', text='Henüz zamanı gelmemiş veya bugün gerçekleşecek görüşmeler burada listelenir.', badge=upcoming_meetings|length ~ ' kayıt', badge_tone='gray', icon='fa-solid fa-hourglass-start', note='Kartlarda kişi, zaman ve aksiyon bilgileri birlikte gösterilir.', note_icon='fa-solid fa-route') %}"
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "line_no": 223,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"empty-box\"><i class=\"fa-solid fa-calendar-check\"></i><h5 class=\"empty-title\">Yaklaşan randevu görünmüyor</h5><p class=\"empty-text\">Seçili filtre altında bugüne veya sonrasına düşen bir kayıt yok. Görünümü değiştirerek geçmiş ya da ertelenen kayıtları inceleyebilirsiniz.</p></div>"
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "line_no": 252,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"meeting-side-card\"><div class=\"meeting-side-label\">Kapanış Duruşu</div><div class=\"meeting-side-value\">{% if meeting.status == 'tamamlandi' %}Görüşme tamamlanmış durumda.{% elif meeting.status == 'ertelendi' %}Oturum ertelenmiş görünüyor.{% elif meeting.status == 'iptal_edildi' %}Randevu iptal edilmiş durumda.{% else %}Kayıt geçmiş görünüme düştü.{% endif %}</div></div>"
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "line_no": 259,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<div class=\"empty-box\"><i class=\"fa-solid fa-clock-rotate-left\"></i><h5 class=\"empty-title\">Geçmiş oturum görünmüyor</h5><p class=\"empty-text\">Bu görünümde henüz kapanmış bir randevu yok.</p></div>"
  },
  {
    "path": "app/templates/feedback_operations_dashboard.html",
    "line_no": 6,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "Bekleyen talepleri, yaklaşan görüşmeleri ve sıkışan randevu yükünü tek operasyon ekranında izleyin."
  },
  {
    "path": "app/templates/feedback_operations_dashboard.html",
    "line_no": 65,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<h3 class=\"hero-title\">Geri bildirim talebi ile randevu akışını tek yerden okuyun</h3>"
  },
  {
    "path": "app/templates/feedback_operations_dashboard.html",
    "line_no": 70,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<span class=\"tone-pill watch\"><i class=\"fa-solid fa-clock-rotate-left\"></i> {{ ops_counts.delayed_meetings or 0 }} sorunlu randevu</span>"
  }
]
```

## Sonraki Adım

A12B: high_risk_user_visible listesindeki gerçek kullanıcıya görünen teknik ifadeler güvenli metinlerle değiştirilecek.