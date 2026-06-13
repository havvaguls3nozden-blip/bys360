# BYS360 A12B UI Teknik Dil Precision Audit

Tarih: 2026-06-13T08:42:17

## Sonuç

- OK: True
- Karar: A12B_PRECISION_AUDIT_COMPLETED
- Source high risk count: 300
- Classified count: 300
- False positive count: 278
- Real user visible candidate count: 10
- Review candidate count: 12
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

## Decision Dağılımı

```json
{
  "false_positive_css_not_visible": 34,
  "false_positive_substring": 187,
  "review_user_visible_string": 2,
  "false_positive_js_code_or_regex": 17,
  "false_positive_js_code_identifier": 16,
  "review_user_visible_text": 10,
  "false_positive_template_code_or_attribute": 24,
  "real_user_visible_candidate": 10
}
```

## Gerçek Kullanıcı Metni Adayları - Dosya Dağılımı

```json
{
  "app/templates/communication/phase9d_dashboard.html": 3,
  "app/templates/communication/phase9d_stabilization_center.html": 3,
  "app/templates/communication/phase9_release_center.html": 2,
  "app/templates/communication/phase9b_dashboard.html": 2
}
```

## Review Adayları - Dosya Dağılımı

```json
{
  "app/templates/communication/phase9b_dashboard.html": 4,
  "app/static/js/bys360_ai_everywhere_v1.js": 1,
  "app/static/js/bys360_assistant_role_report_support_ai_kb_v11.js": 1,
  "app/templates/admin/performance_menu_visibility_settings.html": 1,
  "app/templates/admin_system_scan.html": 1,
  "app/templates/ai_decision/_development_guidance_panel.html": 1,
  "app/templates/assistant_training_bank.html": 1,
  "app/templates/communication/phase9b_transition_center.html": 1,
  "app/templates/feedback_meetings_list.html": 1
}
```

## Gerçek Kullanıcı Metni Adayları

```json
[
  {
    "path": "app/templates/communication/phase9_release_center.html",
    "line_no": 39,
    "family": "hard_ui",
    "term": "Hotfix",
    "file_class": "template_user_visible",
    "line": "<li>Hotfix ve rollback kararı yazılı kayıtla yönetilir.</li>",
    "a12b_decision": "real_user_visible_candidate"
  },
  {
    "path": "app/templates/communication/phase9_release_center.html",
    "line_no": 114,
    "family": "hard_ui",
    "term": "Hotfix",
    "file_class": "template_user_visible",
    "line": "<li>Hotfix ve rollback kararı yazılı kayıtla yönetilir.</li>",
    "a12b_decision": "real_user_visible_candidate"
  },
  {
    "path": "app/templates/communication/phase9b_dashboard.html",
    "line_no": 75,
    "family": "hard_ui",
    "term": "migration",
    "file_class": "template_user_visible",
    "line": "<li class=\"list-group-item d-flex justify-content-between\"><span>SQL hotfix dosyası</span><strong>{{ payload.migration.sql_count }}</strong></li>",
    "a12b_decision": "real_user_visible_candidate"
  },
  {
    "path": "app/templates/communication/phase9b_dashboard.html",
    "line_no": 75,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "template_user_visible",
    "line": "<li class=\"list-group-item d-flex justify-content-between\"><span>SQL hotfix dosyası</span><strong>{{ payload.migration.sql_count }}</strong></li>",
    "a12b_decision": "real_user_visible_candidate"
  },
  {
    "path": "app/templates/communication/phase9d_dashboard.html",
    "line_no": 10,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "template_user_visible",
    "line": "<p class=\"text-muted mb-0\">İlk 72 saat stabilizasyonu, sıcak izleme sinyalleri, hotfix baskısı ve kapanış kararları için merkezi görünüm.</p>",
    "a12b_decision": "real_user_visible_candidate"
  },
  {
    "path": "app/templates/communication/phase9d_dashboard.html",
    "line_no": 96,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "template_user_visible",
    "line": "<h5 class=\"mb-0\">Son hotfix kayıtları</h5>",
    "a12b_decision": "real_user_visible_candidate"
  },
  {
    "path": "app/templates/communication/phase9d_dashboard.html",
    "line_no": 113,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "template_user_visible",
    "line": "<tr><td colspan=\"3\" class=\"text-muted\">Henüz hotfix kaydı bulunmuyor.</td></tr>",
    "a12b_decision": "real_user_visible_candidate"
  },
  {
    "path": "app/templates/communication/phase9d_stabilization_center.html",
    "line_no": 9,
    "family": "hard_ui",
    "term": "hotfix",
    "file_class": "template_user_visible",
    "line": "<p class=\"text-muted mb-0\">İlk 72 saatte check-in, hotfix ve saha sinyalleri aynı merkezden kayıt altına alınır.</p>",
    "a12b_decision": "real_user_visible_candidate"
  },
  {
    "path": "app/templates/communication/phase9d_stabilization_center.html",
    "line_no": 73,
    "family": "hard_ui",
    "term": "Hotfix",
    "file_class": "template_user_visible",
    "line": "<h5 class=\"mb-3\">Hotfix kaydı</h5>",
    "a12b_decision": "real_user_visible_candidate"
  },
  {
    "path": "app/templates/communication/phase9d_stabilization_center.html",
    "line_no": 93,
    "family": "hard_ui",
    "term": "Hotfix",
    "file_class": "template_user_visible",
    "line": "<button class=\"btn btn-outline-danger\" type=\"submit\">Hotfix kaydet</button>",
    "a12b_decision": "real_user_visible_candidate"
  }
]
```

## Review Adayları

```json
[
  {
    "path": "app/static/js/bys360_ai_everywhere_v1.js",
    "line_no": 151,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "action:'Rol matrisi, kişi bazlı görünürlük, modül ayarı ve route erişim kontrolünü birlikte düşünmenizi sağlar.',",
    "a12b_decision": "review_user_visible_string"
  },
  {
    "path": "app/static/js/bys360_assistant_role_report_support_ai_kb_v11.js",
    "line_no": 94,
    "family": "hard_ui",
    "term": "route",
    "file_class": "static_user_visible_asset",
    "line": "window.BYS360_ASSISTANT_ROLE_REPORT_SUPPORT_AI_KB_V11 = { version: VERSION, title: MODULE_TITLE, routes: ROUTES, answers, findAnswer, sanitizeText,",
    "a12b_decision": "review_user_visible_string"
  },
  {
    "path": "app/templates/admin/performance_menu_visibility_settings.html",
    "line_no": 45,
    "family": "hard_ui",
    "term": "route",
    "file_class": "template_user_visible",
    "line": "<div class=\"alert alert-warning mt-4 mb-3\">Menü görünürlüğü tek başına yeterli değildir; route ve backend yetki kontrolleri de aynı anahtarlarla çalışmalıdır.</div>",
    "a12b_decision": "review_user_visible_text"
  },
  {
    "path": "app/templates/admin_system_scan.html",
    "line_no": 36,
    "family": "hard_ui",
    "term": "route",
    "file_class": "template_user_visible",
    "line": "<p class=\"scan-text\">Bu ekran; route yogunlugu, kritik tablo butunlugu, degerlendirme omurgasi ve guvenlik sertlestirme basliklarini yonetsel gozle izlenebilir hale getirir.</p>",
    "a12b_decision": "review_user_visible_text"
  },
  {
    "path": "app/templates/ai_decision/_development_guidance_panel.html",
    "line_no": 7,
    "family": "hard_ui",
    "term": "dev",
    "file_class": "template_user_visible",
    "line": "<span class=\"ai-dev-guidance-eyebrow\">Karar Destek Merkezi</span>",
    "a12b_decision": "review_user_visible_text"
  },
  {
    "path": "app/templates/assistant_training_bank.html",
    "line_no": 184,
    "family": "hard_ui",
    "term": "route",
    "file_class": "template_user_visible",
    "line": "<h3><i class=\"fa-solid fa-route\"></i> Ekran Tanıma Akışı</h3>",
    "a12b_decision": "review_user_visible_text"
  },
  {
    "path": "app/templates/communication/phase9b_dashboard.html",
    "line_no": 10,
    "family": "hard_ui",
    "term": "migration",
    "file_class": "template_user_visible",
    "line": "<p class=\"text-muted mb-0\">Veri geçişi, migration görünürlüğü, sicil omurgası ve güvenlik kapıları için canlı öncesi kontrol merkezi.</p>",
    "a12b_decision": "review_user_visible_text"
  },
  {
    "path": "app/templates/communication/phase9b_dashboard.html",
    "line_no": 72,
    "family": "hard_ui",
    "term": "migration",
    "file_class": "template_user_visible",
    "line": "<div class=\"small text-muted mb-2\">Versiyon klasörü: {{ payload.migration.versions_dir }}</div>",
    "a12b_decision": "review_user_visible_text"
  },
  {
    "path": "app/templates/communication/phase9b_dashboard.html",
    "line_no": 74,
    "family": "hard_ui",
    "term": "migration",
    "file_class": "template_user_visible",
    "line": "<li class=\"list-group-item d-flex justify-content-between\"><span>Versiyon dosyası</span><strong>{{ payload.migration.version_count }}</strong></li>",
    "a12b_decision": "review_user_visible_text"
  },
  {
    "path": "app/templates/communication/phase9b_dashboard.html",
    "line_no": 76,
    "family": "hard_ui",
    "term": "migration",
    "file_class": "template_user_visible",
    "line": "<li class=\"list-group-item d-flex justify-content-between\"><span>Son dosya</span><strong>{{ payload.migration.latest_version.name if payload.migration.latest_version else '-' }}</strong></li>",
    "a12b_decision": "review_user_visible_text"
  },
  {
    "path": "app/templates/communication/phase9b_transition_center.html",
    "line_no": 9,
    "family": "hard_ui",
    "term": "migration",
    "file_class": "template_user_visible",
    "line": "<p class=\"text-muted mb-0\">Sicil omurgası, migration görünürlüğü, env sertleştirmesi ve güvenlik denetimi aynı ekranda yönetilir.</p>",
    "a12b_decision": "review_user_visible_text"
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "line_no": 188,
    "family": "hard_ui",
    "term": "route",
    "file_class": "template_user_visible",
    "line": "{% call list_workspace_panel(title='Yaklaşan randevular', text='Henüz zamanı gelmemiş veya bugün gerçekleşecek görüşmeler burada listelenir.', badge=upcoming_meetings|length ~ ' kayıt', badge_tone='gray', icon='fa-solid fa-hourglass-start', note='Kartlarda kişi, zaman ve aksiyon bilgileri birlikte gösterilir.', note_icon='fa-solid fa-route') %}",
    "a12b_decision": "review_user_visible_text"
  }
]
```

## Sonraki Adım

A12C: yalnızca real_user_visible_candidate ve gerekirse review adayları üzerinde güvenli metin temizliği yapılacak.