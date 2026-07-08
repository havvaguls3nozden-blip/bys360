# BYS360 A13B UI Design System Konsolidasyon Planı

Tarih: 2026-06-13T09:39:24

## Sonuç

- OK: True
- Karar: A13B_PLAN_COMPLETED
- Source A13A OK: True
- Source design risk count: 16383
- Source component occurrence count: 10126
- Source duplicate CSS selector count: 518
- Compileall returncode: 0
- Pytest returncode: 0

## Pytest Summary

```json
{
  "passed": 744,
  "skipped": 2,
  "deselected": 34,
  "failed": 0,
  "errors": 0,
  "warnings": 0
}
```

## Önerilen Fazlar

```json
[
  {
    "phase": "A13C",
    "title": "Design token temeli",
    "goal": "Renk, radius, shadow, spacing ve font token dosyasını oluşturmak.",
    "safe_change": true,
    "expected_files": [
      "app/static/css/bys360_design_tokens_v1.css"
    ]
  },
  {
    "phase": "A13D",
    "title": "Ortak component sözleşmesi",
    "goal": "Kart, buton, badge, pill, form ve tablo için ortak sınıf hedeflerini belgelemek.",
    "safe_change": true,
    "expected_files": [
      "reports/quality",
      "app/static/css/bys360_components_v1.css"
    ]
  },
  {
    "phase": "A13E",
    "title": "CSS duplicate selector temizlik planı",
    "goal": "Tekrar eden selectorları risk sırasına göre gruplayıp ilk güvenli temizlik dalgasını hazırlamak.",
    "safe_change": false,
    "expected_files": [
      "app/static/css"
    ]
  },
  {
    "phase": "A13F",
    "title": "Inline style azaltma",
    "goal": "Template içindeki inline style kullanımını parça parça ortak sınıflara almak.",
    "safe_change": false,
    "expected_files": [
      "app/templates"
    ]
  },
  {
    "phase": "A13G",
    "title": "Mobil CSS sadeleştirme",
    "goal": "iOS/Android responsive dosyalarındaki tekrarları tek mobil standart altında toplamak.",
    "safe_change": false,
    "expected_files": [
      "app/static/css/bys360_mobile_*",
      "app/static/css/bys360_ios_*",
      "app/static/css/bys360_android_*"
    ]
  }
]
```

## Component Mapping Plan

```json
[
  {
    "group": "card",
    "target": "bys-card",
    "variants": [
      "bys-card",
      "bys-card--soft",
      "bys-card--glass",
      "bys-card--metric",
      "bys-card--section"
    ],
    "source_hits": [
      {
        "class": "glass-card",
        "count": 479
      },
      {
        "class": "card",
        "count": 306
      },
      {
        "class": "panel-card",
        "count": 179
      },
      {
        "class": "stat-card",
        "count": 158
      },
      {
        "class": "ai-card",
        "count": 73
      },
      {
        "class": "summary-card",
        "count": 48
      },
      {
        "class": "bys-md-card",
        "count": 32
      },
      {
        "class": "portal-card",
        "count": 26
      },
      {
        "class": "pmc-card",
        "count": 26
      }
    ],
    "top120_detected_count": 1327,
    "strategy": "Önce yeni standart sınıf eklenecek; mevcut sınıflar hemen silinmeyecek. Kırılma riskini azaltmak için alias yaklaşımı kullanılacak."
  },
  {
    "group": "button",
    "target": "bys-btn",
    "variants": [
      "bys-btn",
      "bys-btn--primary",
      "bys-btn--secondary",
      "bys-btn--danger",
      "bys-btn--ghost",
      "bys-btn--sm"
    ],
    "source_hits": [
      {
        "class": "btn",
        "count": 296
      },
      {
        "class": "btn-soft",
        "count": 456
      },
      {
        "class": "mini-btn",
        "count": 63
      },
      {
        "class": "pmc-btn",
        "count": 26
      },
      {
        "class": "pub-btn",
        "count": 24
      },
      {
        "class": "performance-btn",
        "count": 29
      },
      {
        "class": "btn-danger",
        "count": 52
      },
      {
        "class": "btn-sm",
        "count": 57
      }
    ],
    "top120_detected_count": 1003,
    "strategy": "Önce yeni standart sınıf eklenecek; mevcut sınıflar hemen silinmeyecek. Kırılma riskini azaltmak için alias yaklaşımı kullanılacak."
  },
  {
    "group": "form",
    "target": "bys-form",
    "variants": [
      "bys-form",
      "bys-form-grid",
      "bys-input",
      "bys-select",
      "bys-label"
    ],
    "source_hits": [
      {
        "class": "form-group",
        "count": 155
      },
      {
        "class": "form-label",
        "count": 144
      },
      {
        "class": "form-control",
        "count": 126
      },
      {
        "class": "form-input",
        "count": 99
      },
      {
        "class": "form-select",
        "count": 159
      },
      {
        "class": "form-grid",
        "count": 60
      }
    ],
    "top120_detected_count": 743,
    "strategy": "Önce yeni standart sınıf eklenecek; mevcut sınıflar hemen silinmeyecek. Kırılma riskini azaltmak için alias yaklaşımı kullanılacak."
  },
  {
    "group": "table",
    "target": "bys-table",
    "variants": [
      "bys-table",
      "bys-table-wrap",
      "bys-table--clean",
      "bys-table--responsive"
    ],
    "source_hits": [
      {
        "class": "table",
        "count": 88
      },
      {
        "class": "table-wrap",
        "count": 97
      },
      {
        "class": "table-responsive",
        "count": 89
      },
      {
        "class": "table-clean",
        "count": 40
      },
      {
        "class": "ai-table-wrap",
        "count": 48
      }
    ],
    "top120_detected_count": 362,
    "strategy": "Önce yeni standart sınıf eklenecek; mevcut sınıflar hemen silinmeyecek. Kırılma riskini azaltmak için alias yaklaşımı kullanılacak."
  },
  {
    "group": "pill_chip",
    "target": "bys-pill",
    "variants": [
      "bys-pill",
      "bys-pill--soft",
      "bys-chip",
      "bys-chip--active"
    ],
    "source_hits": [
      {
        "class": "pill",
        "count": 167
      },
      {
        "class": "bys-pill",
        "count": 35
      },
      {
        "class": "matrix-pill",
        "count": 43
      },
      {
        "class": "tone-pill",
        "count": 30
      },
      {
        "class": "wf-pill",
        "count": 28
      }
    ],
    "top120_detected_count": 303,
    "strategy": "Önce yeni standart sınıf eklenecek; mevcut sınıflar hemen silinmeyecek. Kırılma riskini azaltmak için alias yaklaşımı kullanılacak."
  },
  {
    "group": "badge",
    "target": "bys-badge",
    "variants": [
      "bys-badge",
      "bys-badge--success",
      "bys-badge--warning",
      "bys-badge--danger",
      "bys-badge--info",
      "bys-badge--muted"
    ],
    "source_hits": [
      {
        "class": "badge",
        "count": 124
      },
      {
        "class": "ai-badge",
        "count": 71
      },
      {
        "class": "bys-md-badge",
        "count": 56
      },
      {
        "class": "pmc-badge",
        "count": 42
      }
    ],
    "top120_detected_count": 293,
    "strategy": "Önce yeni standart sınıf eklenecek; mevcut sınıflar hemen silinmeyecek. Kırılma riskini azaltmak için alias yaklaşımı kullanılacak."
  },
  {
    "group": "alert",
    "target": "bys-alert",
    "variants": [
      "bys-alert",
      "bys-alert--info",
      "bys-alert--success",
      "bys-alert--warning",
      "bys-alert--danger"
    ],
    "source_hits": [
      {
        "class": "alert",
        "count": 26
      }
    ],
    "top120_detected_count": 26,
    "strategy": "Önce yeni standart sınıf eklenecek; mevcut sınıflar hemen silinmeyecek. Kırılma riskini azaltmak için alias yaklaşımı kullanılacak."
  }
]
```

## Risk Priority Top 80

```json
[
  {
    "path": "app/static/css/app.css",
    "risk_count": 210,
    "weighted_priority_score": 1924,
    "risk_types": {
      "hardcoded_hex_color": 23,
      "hardcoded_rgb_color": 38,
      "pixel_fixed_width": 10,
      "important_css": 136,
      "absolute_position": 2,
      "pixel_fixed_height": 1
    },
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/static/css/bys360_elegant_hero_overrides.css",
    "risk_count": 324,
    "weighted_priority_score": 324,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/static/css/dashboard_showcase.css",
    "risk_count": 228,
    "weighted_priority_score": 228,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/static/css/messages_whatsapp_mobile.css",
    "risk_count": 224,
    "weighted_priority_score": 224,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/templates/base.html",
    "risk_count": 207,
    "weighted_priority_score": 207,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/partials/settings/_settings_styles.html",
    "risk_count": 200,
    "weighted_priority_score": 200,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/bys360_ios_assistant_responsive_fix_v2.css",
    "risk_count": 193,
    "weighted_priority_score": 193,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/static/css/bys360_android_responsive_completion_v2.css",
    "risk_count": 188,
    "weighted_priority_score": 188,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/templates/settings.html",
    "risk_count": 183,
    "weighted_priority_score": 183,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/bys360_live_hero_polish.css",
    "risk_count": 180,
    "weighted_priority_score": 180,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/static/css/bys360_mobile_app_experience_v5.css",
    "risk_count": 164,
    "weighted_priority_score": 164,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/static/css/corporate_information_center_v4_6_celebrations_studio.css",
    "risk_count": 162,
    "weighted_priority_score": 162,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/static/css/bys360_android_responsive_completion_v1.css",
    "risk_count": 161,
    "weighted_priority_score": 161,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/static/css/bys360_layout_lock_v10.css",
    "risk_count": 161,
    "weighted_priority_score": 161,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/templates/partials/evaluation_form/_evaluation_form_styles.html",
    "risk_count": 161,
    "weighted_priority_score": 161,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/bys360_topbar_sidebar_clean_v9.css",
    "risk_count": 160,
    "weighted_priority_score": 160,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/static/css/bys360_mobile_native_shell_v2.css",
    "risk_count": 151,
    "weighted_priority_score": 151,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/static/css/bys360_portal.css",
    "risk_count": 151,
    "weighted_priority_score": 151,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/static/css/bys360_topbar_gap_final_v8.css",
    "risk_count": 146,
    "weighted_priority_score": 146,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
    "risk_count": 140,
    "weighted_priority_score": 140,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/static/css/bys360_assistant_module.css",
    "risk_count": 137,
    "weighted_priority_score": 137,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/static/css/bys360_ios_responsive_completion_v1.css",
    "risk_count": 136,
    "weighted_priority_score": 136,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/templates/task_management.html",
    "risk_count": 134,
    "weighted_priority_score": 134,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase4_1.css",
    "risk_count": 127,
    "weighted_priority_score": 127,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/static/css/bys360_portal_experience_v2d1_profile_visual_fix.css",
    "risk_count": 114,
    "weighted_priority_score": 114,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/static/css/bys360_assistant_chatgpt_like_v31.css",
    "risk_count": 110,
    "weighted_priority_score": 110,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/static/css/bys360_ios_assistant_responsive_fix_v3.css",
    "risk_count": 110,
    "weighted_priority_score": 110,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/static/css/bys360_mobile_app_experience_v1.css",
    "risk_count": 109,
    "weighted_priority_score": 109,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/static/css/bys360_mobile_clean_native_v4.css",
    "risk_count": 107,
    "weighted_priority_score": 107,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/templates/performance_tasks.html",
    "risk_count": 107,
    "weighted_priority_score": 107,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/bys360_phase11_process_engine.css",
    "risk_count": 106,
    "weighted_priority_score": 106,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/static/css/bys360_home_weather.css",
    "risk_count": 103,
    "weighted_priority_score": 103,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/templates/about_bys360.html",
    "risk_count": 103,
    "weighted_priority_score": 103,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/corporate_information_center_v4_4_performance_style.css",
    "risk_count": 99,
    "weighted_priority_score": 99,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/static/css/bys360_mobile_app_experience_v3.css",
    "risk_count": 98,
    "weighted_priority_score": 98,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/templates/performance_publish.html",
    "risk_count": 98,
    "weighted_priority_score": 98,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/performance_phase3_parts/performance_phase3_part_01.css",
    "risk_count": 96,
    "weighted_priority_score": 96,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/templates/personnel_list.html",
    "risk_count": 96,
    "weighted_priority_score": 96,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/performance_dashboard_analytics.css",
    "risk_count": 95,
    "weighted_priority_score": 95,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/static/css/messages_messenger_mobile.css",
    "risk_count": 94,
    "weighted_priority_score": 94,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/templates/periods.html",
    "risk_count": 93,
    "weighted_priority_score": 93,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/bys360_mobile_app_experience_v4.css",
    "risk_count": 92,
    "weighted_priority_score": 92,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "risk_count": 91,
    "weighted_priority_score": 91,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/org_units_list.html",
    "risk_count": 91,
    "weighted_priority_score": 91,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/performance/feedback_pipeline.html",
    "risk_count": 89,
    "weighted_priority_score": 89,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/performance_phase3_parts/performance_phase3_part_04.css",
    "risk_count": 88,
    "weighted_priority_score": 88,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/templates/performance/personnel_support_publish_approvals.html",
    "risk_count": 88,
    "weighted_priority_score": 88,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/bys360_mobile_app_experience_v2.css",
    "risk_count": 87,
    "weighted_priority_score": 87,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/static/css/performance_phase3_parts/performance_phase3_part_02.css",
    "risk_count": 87,
    "weighted_priority_score": 87,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/templates/evaluation_tasks.html",
    "risk_count": 87,
    "weighted_priority_score": 87,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/publications/library.html",
    "risk_count": 87,
    "weighted_priority_score": 87,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/bys360_phase7_scorecard_ui_v1.css",
    "risk_count": 86,
    "weighted_priority_score": 86,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/templates/performance_mail_reminders.html",
    "risk_count": 86,
    "weighted_priority_score": 86,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/performance_scorecard_detail.html",
    "risk_count": 85,
    "weighted_priority_score": 85,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/scorecard.html",
    "risk_count": 85,
    "weighted_priority_score": 85,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/survey_results.html",
    "risk_count": 85,
    "weighted_priority_score": 85,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/messages_whatsapp_theme.css",
    "risk_count": 83,
    "weighted_priority_score": 83,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/templates/hierarchy_settings.html",
    "risk_count": 82,
    "weighted_priority_score": 82,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/bys360_mobile_native_app_v3.css",
    "risk_count": 79,
    "weighted_priority_score": 79,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/static/css/survey_mobile_hardening.css",
    "risk_count": 79,
    "weighted_priority_score": 79,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/templates/period_create.html",
    "risk_count": 79,
    "weighted_priority_score": 79,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/feedback/quick_feedback.html",
    "risk_count": 78,
    "weighted_priority_score": 78,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/admin/role_matrix_center.html",
    "risk_count": 77,
    "weighted_priority_score": 77,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/admin_users.html",
    "risk_count": 77,
    "weighted_priority_score": 77,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/performance/process_engine_tracking.html",
    "risk_count": 76,
    "weighted_priority_score": 76,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/bys360_reports_ai_pro.css",
    "risk_count": 75,
    "weighted_priority_score": 75,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/templates/_premium_ui_kit.html",
    "risk_count": 75,
    "weighted_priority_score": 75,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/db_check.html",
    "risk_count": 75,
    "weighted_priority_score": 75,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/premium_ui_kit.html",
    "risk_count": 75,
    "weighted_priority_score": 75,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase7_4_release_pro.css",
    "risk_count": 72,
    "weighted_priority_score": 72,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/static/css/bys360_reports_premium_v2.css",
    "risk_count": 71,
    "weighted_priority_score": 71,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/templates/personnel_excel_upload.html",
    "risk_count": 70,
    "weighted_priority_score": 70,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/criteria.html",
    "risk_count": 69,
    "weighted_priority_score": 69,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/survey_create.html",
    "risk_count": 69,
    "weighted_priority_score": 69,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/bys360_ios_pwa_v2_topbar_notification_fix.css",
    "risk_count": 68,
    "weighted_priority_score": 68,
    "risk_types": {},
    "recommended_action": "Mobil responsive dosyaları A13G dalgasına alınmalı."
  },
  {
    "path": "app/templates/forgot_password.html",
    "risk_count": 66,
    "weighted_priority_score": 66,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/static/css/performance_dashboard_advanced.css",
    "risk_count": 65,
    "weighted_priority_score": 65,
    "risk_types": {},
    "recommended_action": "CSS token ve component sınıflarına taşınmalı."
  },
  {
    "path": "app/templates/period_edit.html",
    "risk_count": 65,
    "weighted_priority_score": 65,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/survey_edit.html",
    "risk_count": 65,
    "weighted_priority_score": 65,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  },
  {
    "path": "app/templates/manager_feedback_request_schedule.html",
    "risk_count": 64,
    "weighted_priority_score": 64,
    "risk_types": {},
    "recommended_action": "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
  }
]
```

## Duplicate Selector Plan Top 80

```json
[
  {
    "selector": ":root",
    "count": 59,
    "location_count_sample": 20,
    "first_locations": [
      {
        "path": "app/static/css/analysis_center_ultra.css",
        "line_no": 1
      },
      {
        "path": "app/static/css/app.css",
        "line_no": 1
      },
      {
        "path": "app/static/css/app.css",
        "line_no": 220
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 1
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 121
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".topbar",
    "count": 22,
    "location_count_sample": 20,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 56
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 123
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 138
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 211
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 306
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body",
    "count": 18,
    "location_count_sample": 18,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 15
      },
      {
        "path": "app/static/css/bys360_android_responsive_core_p5b.css",
        "line_no": 19
      },
      {
        "path": "app/static/css/bys360_android_responsive_targeted_p5c.css",
        "line_no": 17
      },
      {
        "path": "app/static/css/bys360_android_responsive_targeted_p5c.css",
        "line_no": 188
      },
      {
        "path": "app/static/css/bys360_android_responsive_targeted_p5c.css",
        "line_no": 390
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".content-wrap",
    "count": 18,
    "location_count_sample": 18,
    "first_locations": [
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 152
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 280
      },
      {
        "path": "app/static/css/bys360_mobile_app_experience_v1.css",
        "line_no": 37
      },
      {
        "path": "app/static/css/bys360_mobile_app_experience_v1.css",
        "line_no": 204
      },
      {
        "path": "app/static/css/bys360_mobile_app_experience_v1.css",
        "line_no": 223
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".topbar-right",
    "count": 15,
    "location_count_sample": 15,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 111
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 174
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 312
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 357
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 109
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".app-sidebar",
    "count": 14,
    "location_count_sample": 14,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 6
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 263
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 181
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 217
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 284
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".page-title",
    "count": 14,
    "location_count_sample": 14,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 104
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 169
      },
      {
        "path": "app/static/css/bys360_android_responsive_targeted_p5c.css",
        "line_no": 292
      },
      {
        "path": "app/static/css/bys360_live_full_v2_17_60.css",
        "line_no": 11
      },
      {
        "path": "app/static/css/bys360_live_full_v2_17_61.css",
        "line_no": 11
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".user-summary",
    "count": 12,
    "location_count_sample": 12,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 116
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 257
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 283
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 328
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 128
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-panel",
    "count": 11,
    "location_count_sample": 11,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_chatgpt_like_v31.css",
        "line_no": 110
      },
      {
        "path": "app/static/css/bys360_assistant_chatgpt_like_v31.css",
        "line_no": 154
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 68
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 142
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 234
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".quick-link",
    "count": 11,
    "location_count_sample": 11,
    "first_locations": [
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 120
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 255
      },
      {
        "path": "app/static/css/bys360_topbar_gap_final_v8.css",
        "line_no": 115
      },
      {
        "path": "app/static/css/bys360_topbar_gap_final_v8.css",
        "line_no": 228
      },
      {
        "path": "app/static/css/bys360_topbar_sidebar_clean_v9.css",
        "line_no": 151
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".cic-badge",
    "count": 11,
    "location_count_sample": 11,
    "first_locations": [
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase4_1.css",
        "line_no": 106
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase4_1.css",
        "line_no": 130
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7.css",
        "line_no": 26
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7.css",
        "line_no": 50
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7_4_release_pro.css",
        "line_no": 383
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".cic-badge.ok",
    "count": 11,
    "location_count_sample": 11,
    "first_locations": [
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase4_1.css",
        "line_no": 123
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase4_1.css",
        "line_no": 147
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7.css",
        "line_no": 43
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7.css",
        "line_no": 67
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7_4_release_pro.css",
        "line_no": 400
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".topbar-left",
    "count": 10,
    "location_count_sample": 10,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 66
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 146
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 202
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 54
      },
      {
        "path": "app/static/css/bys360_topbar_gap_final_v8.css",
        "line_no": 41
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".topbar-brand-logo",
    "count": 10,
    "location_count_sample": 10,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 90
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 127
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 158
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 72
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 211
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".cic-badge.warning",
    "count": 10,
    "location_count_sample": 10,
    "first_locations": [
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase4_1.css",
        "line_no": 124
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase4_1.css",
        "line_no": 148
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7.css",
        "line_no": 44
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7.css",
        "line_no": 68
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7_4_release_pro.css",
        "line_no": 401
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".cic-badge.danger",
    "count": 10,
    "location_count_sample": 10,
    "first_locations": [
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase4_1.css",
        "line_no": 125
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase4_1.css",
        "line_no": 149
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7.css",
        "line_no": 45
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7.css",
        "line_no": 69
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7_4_release_pro.css",
        "line_no": 402
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".cic-badge.neutral",
    "count": 10,
    "location_count_sample": 10,
    "first_locations": [
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase4_1.css",
        "line_no": 126
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase4_1.css",
        "line_no": 150
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7.css",
        "line_no": 46
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7.css",
        "line_no": 70
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7_4_release_pro.css",
        "line_no": 403
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".cic-badge i",
    "count": 10,
    "location_count_sample": 10,
    "first_locations": [
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase4_1.css",
        "line_no": 127
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase4_1.css",
        "line_no": 151
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7.css",
        "line_no": 47
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7.css",
        "line_no": 71
      },
      {
        "path": "app/static/css/corporate_information_center_v3_0_phase7_4_release_pro.css",
        "line_no": 404
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".page-meta",
    "count": 9,
    "location_count_sample": 9,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 98
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 132
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 163
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 196
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 81
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-hero",
    "count": 8,
    "location_count_sample": 8,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 233
      },
      {
        "path": "app/static/css/app.css",
        "line_no": 457
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 366
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 590
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 19
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-hero::after",
    "count": 8,
    "location_count_sample": 8,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 262
      },
      {
        "path": "app/static/css/app.css",
        "line_no": 467
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 395
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 600
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 48
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-hero-inner",
    "count": 8,
    "location_count_sample": 8,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 277
      },
      {
        "path": "app/static/css/app.css",
        "line_no": 447
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 410
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 580
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 63
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-title",
    "count": 8,
    "location_count_sample": 8,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 314
      },
      {
        "path": "app/static/css/app.css",
        "line_no": 463
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 447
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 596
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 100
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-hero-stat",
    "count": 8,
    "location_count_sample": 8,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 363
      },
      {
        "path": "app/static/css/app.css",
        "line_no": 451
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 496
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 584
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 149
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".topbar-brand",
    "count": 8,
    "location_count_sample": 8,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 72
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 152
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 192
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 62
      },
      {
        "path": "app/static/css/bys360_topbar_gap_final_v8.css",
        "line_no": 51
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".mobile-dock",
    "count": 8,
    "location_count_sample": 8,
    "first_locations": [
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 165
      },
      {
        "path": "app/static/css/faz1_mobile_foundation.css",
        "line_no": 316
      },
      {
        "path": "app/static/css/faz4_support_account_mobile.css",
        "line_no": 163
      },
      {
        "path": "app/static/css/mobile_phase_m1.css",
        "line_no": 5
      },
      {
        "path": "app/static/css/mobile_phase_m1.css",
        "line_no": 164
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-launcher",
    "count": 7,
    "location_count_sample": 7,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_chatgpt_like_v31.css",
        "line_no": 149
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 33
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 138
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 201
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 286
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root",
    "count": 7,
    "location_count_sample": 7,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 20
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 137
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 176
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 187
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 285
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ")",
    "count": 7,
    "location_count_sample": 7,
    "first_locations": [
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 52
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 124
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 158
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 193
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 213
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".menu-toggle",
    "count": 6,
    "location_count_sample": 6,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 215
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 272
      },
      {
        "path": "app/static/css/bys360_topbar_gap_final_v8.css",
        "line_no": 197
      },
      {
        "path": "app/static/css/bys360_topbar_sidebar_clean_v9.css",
        "line_no": 242
      },
      {
        "path": "app/static/css/faz1_mobile_foundation.css",
        "line_no": 302
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".mobile-overlay",
    "count": 6,
    "location_count_sample": 6,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 250
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 232
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 289
      },
      {
        "path": "app/static/css/bys360_topbar_gap_final_v8.css",
        "line_no": 164
      },
      {
        "path": "app/static/css/bys360_topbar_gap_final_v8.css",
        "line_no": 259
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".user-menu",
    "count": 6,
    "location_count_sample": 6,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 254
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 281
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 302
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 321
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 362
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".user-dropdown",
    "count": 6,
    "location_count_sample": 6,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 258
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 290
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 339
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 366
      },
      {
        "path": "app/static/css/faz1_mobile_foundation.css",
        "line_no": 90
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".app-sidebar.mobile-open",
    "count": 6,
    "location_count_sample": 6,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 268
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 387
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 228
      },
      {
        "path": "app/static/css/bys360_mobile_emergency_visible_v8.css",
        "line_no": 63
      },
      {
        "path": "app/static/css/bys360_topbar_gap_final_v8.css",
        "line_no": 160
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-form",
    "count": 6,
    "location_count_sample": 6,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_chatgpt_like_v31.css",
        "line_no": 129
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 117
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 279
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 403
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
        "line_no": 199
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-form textarea",
    "count": 6,
    "location_count_sample": 6,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_chatgpt_like_v31.css",
        "line_no": 137
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 118
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 342
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 350
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
        "line_no": 208
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-title p",
    "count": 6,
    "location_count_sample": 6,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 94
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 144
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 264
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
        "line_no": 140
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v2.css",
        "line_no": 117
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-body",
    "count": 6,
    "location_count_sample": 6,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 102
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 270
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 301
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 358
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
        "line_no": 170
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".user-avatar",
    "count": 6,
    "location_count_sample": 6,
    "first_locations": [
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 136
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 265
      },
      {
        "path": "app/static/css/bys360_topbar_gap_final_v8.css",
        "line_no": 131
      },
      {
        "path": "app/static/css/bys360_topbar_gap_final_v8.css",
        "line_no": 246
      },
      {
        "path": "app/static/css/bys360_topbar_sidebar_clean_v9.css",
        "line_no": 167
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".page-subtitle",
    "count": 6,
    "location_count_sample": 6,
    "first_locations": [
      {
        "path": "app/static/css/bys360_topbar_gap_final_v8.css",
        "line_no": 82
      },
      {
        "path": "app/static/css/bys360_topbar_sidebar_clean_v9.css",
        "line_no": 117
      },
      {
        "path": "app/static/css/faz1_mobile_foundation.css",
        "line_no": 135
      },
      {
        "path": "app/static/css/faz1_mobile_foundation.css",
        "line_no": 267
      },
      {
        "path": "app/static/css/mobile_phase_m1.css",
        "line_no": 96
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".brand-logo",
    "count": 5,
    "location_count_sample": 5,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 22
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 184
      },
      {
        "path": "app/static/css/bys360_mobile_app_experience_v1.css",
        "line_no": 209
      },
      {
        "path": "app/static/css/faz1_mobile_foundation.css",
        "line_no": 226
      },
      {
        "path": "app/static/css/mobile_phase_m1.css",
        "line_no": 217
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".user-meta",
    "count": 5,
    "location_count_sample": 5,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 288
      },
      {
        "path": "app/static/css/bys360_topbar_gap_final_v8.css",
        "line_no": 242
      },
      {
        "path": "app/static/css/bys360_topbar_sidebar_clean_v9.css",
        "line_no": 287
      },
      {
        "path": "app/static/css/faz1_mobile_foundation.css",
        "line_no": 249
      },
      {
        "path": "app/static/css/mobile_phase_m1.css",
        "line_no": 356
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "table",
    "count": 5,
    "location_count_sample": 5,
    "first_locations": [
      {
        "path": "app/static/css/bys360_android_responsive_core_p5b.css",
        "line_no": 36
      },
      {
        "path": "app/static/css/bys360_android_responsive_core_p5b.css",
        "line_no": 190
      },
      {
        "path": "app/static/css/bys360_android_responsive_targeted_p5c.css",
        "line_no": 51
      },
      {
        "path": "app/static/css/bys360_android_responsive_targeted_p5c.css",
        "line_no": 67
      },
      {
        "path": "app/static/css/bys360_android_responsive_targeted_p5c.css",
        "line_no": 317
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-tabs",
    "count": 5,
    "location_count_sample": 5,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_chatgpt_like_v31.css",
        "line_no": 109
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 98
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 267
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 289
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
        "line_no": 155
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-header",
    "count": 5,
    "location_count_sample": 5,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_chatgpt_like_v31.css",
        "line_no": 115
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 89
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 245
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
        "line_no": 105
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v2.css",
        "line_no": 107
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-bubble",
    "count": 5,
    "location_count_sample": 5,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_chatgpt_like_v31.css",
        "line_no": 142
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 113
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 275
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 396
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v2.css",
        "line_no": 172
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-mark",
    "count": 5,
    "location_count_sample": 5,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 59
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 91
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 223
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
        "line_no": 117
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v2.css",
        "line_no": 50
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-launcher-text span",
    "count": 5,
    "location_count_sample": 5,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 65
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 232
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
        "line_no": 66
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v2.css",
        "line_no": 69
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v2.css",
        "line_no": 80
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-view",
    "count": 5,
    "location_count_sample": 5,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 103
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 271
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 291
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 410
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
        "line_no": 176
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".app-main",
    "count": 5,
    "location_count_sample": 5,
    "first_locations": [
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 19
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 201
      },
      {
        "path": "app/static/css/bys360_topbar_gap_final_v8.css",
        "line_no": 169
      },
      {
        "path": "app/static/css/bys360_topbar_sidebar_clean_v9.css",
        "line_no": 207
      },
      {
        "path": "app/static/css/mobile_phase_m1.css",
        "line_no": 22
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".content-block textarea",
    "count": 5,
    "location_count_sample": 5,
    "first_locations": [
      {
        "path": "app/static/css/faz1_mobile_foundation.css",
        "line_no": 189
      },
      {
        "path": "app/static/css/faz1_mobile_foundation.css",
        "line_no": 193
      },
      {
        "path": "app/static/css/mobile_phase_m1.css",
        "line_no": 138
      },
      {
        "path": "app/static/css/mobile_phase_m1.css",
        "line_no": 142
      },
      {
        "path": "app/static/css/mobile_phase_m1.css",
        "line_no": 321
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".chat-main",
    "count": 5,
    "location_count_sample": 5,
    "first_locations": [
      {
        "path": "app/static/css/faz3_communication_hr_mobile.css",
        "line_no": 56
      },
      {
        "path": "app/static/css/messages_whatsapp_mobile.css",
        "line_no": 271
      },
      {
        "path": "app/static/css/messages_whatsapp_theme.css",
        "line_no": 81
      },
      {
        "path": "app/static/css/messages_whatsapp_theme.css",
        "line_no": 379
      },
      {
        "path": "app/static/css/messages_whatsapp_theme.css",
        "line_no": 465
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-hero::before",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 250
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 383
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 36
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 397
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-kicker",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 287
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 420
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 73
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 434
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-kicker i",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 308
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 441
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 94
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 455
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-hero .fbx-text",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 327
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 460
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 113
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 474
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-actions",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 333
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 466
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 119
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 480
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-hero .fbx-btn",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 341
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 474
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 127
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 488
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-hero .fbx-btn:hover",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 355
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 488
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 141
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 502
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-hero-stat .label",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 377
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 510
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 163
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 524
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-hero-stat .value",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 389
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 522
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 175
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 536
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-hero-stat .sub",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 401
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 534
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 187
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 548
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .bys-pro-shell .bys-pro-hero .bys-pro-mini-grid",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 406
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 539
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 192
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 553
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .bys-pro-shell .bys-pro-hero .bys-pro-mini",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 410
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 543
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 196
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 557
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .bys-pro-shell .bys-pro-hero .bys-pro-mini span",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 416
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 549
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 202
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 563
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .bys-pro-shell .bys-pro-hero .bys-pro-mini strong",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 419
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 552
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 205
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 566
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-hero :is(.text-white,.text-light)",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 425
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 558
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 211
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 572
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-hero :is(.bg-danger,.text-bg-danger,.badge.bg-danger)",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 430
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 563
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 216
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 577
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body .fbx-shell .fbx-hero .fbx-chip",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 437
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 570
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 223
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 584
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body :is(.page-header,.hero-card,.hero-panel,.performance-hero)",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 473
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 606
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 259
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 620
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "body :is(.page-header,.hero-card,.hero-panel,.performance-hero) :is(h1,h2,h3,p,.text-white)",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/app.css",
        "line_no": 482
      },
      {
        "path": "app/static/css/bys360_elegant_hero_overrides.css",
        "line_no": 615
      },
      {
        "path": "app/static/css/bys360_live_hero_polish.css",
        "line_no": 268
      },
      {
        "path": "app/static/css/dashboard_showcase.css",
        "line_no": 629
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".sidebar-inner",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 10
      },
      {
        "path": "app/static/css/bys360_layout_lock_v10.css",
        "line_no": 191
      },
      {
        "path": "app/static/css/bys360_topbar_sidebar_clean_v9.css",
        "line_no": 39
      },
      {
        "path": "app/static/css/mobile_phase_m1.css",
        "line_no": 78
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": ".brand-ribbon",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 14
      },
      {
        "path": "app/static/css/base_logo_refresh.css",
        "line_no": 180
      },
      {
        "path": "app/static/css/faz1_mobile_foundation.css",
        "line_no": 221
      },
      {
        "path": "app/static/css/mobile_phase_m1.css",
        "line_no": 212
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "html, body",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/bys360_android_responsive_completion_v2.css",
        "line_no": 458
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
        "line_no": 6
      },
      {
        "path": "app/static/css/bys360_portal.css",
        "line_no": 86
      },
      {
        "path": "app/static/css/survey_mobile_hardening.css",
        "line_no": 138
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-launcher-text strong",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 64
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 231
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
        "line_no": 56
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v2.css",
        "line_no": 79
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-launcher-dot",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 66
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 233
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
        "line_no": 76
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v2.css",
        "line_no": 81
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-header-top",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 90
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 262
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
        "line_no": 112
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v2.css",
        "line_no": 114
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-title h2",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 93
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 263
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
        "line_no": 129
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v2.css",
        "line_no": 127
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-tab",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 99
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 268
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 290
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
        "line_no": 162
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  },
  {
    "selector": "#bys360-assistant-module-root .bys360-am-view.is-active[data-panel=\"chat\"]",
    "count": 4,
    "location_count_sample": 4,
    "first_locations": [
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 307
      },
      {
        "path": "app/static/css/bys360_assistant_module.css",
        "line_no": 360
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v1.css",
        "line_no": 185
      },
      {
        "path": "app/static/css/bys360_ios_assistant_responsive_fix_v2.css",
        "line_no": 147
      }
    ],
    "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı."
  }
]
```

## Guardrails

```json
[
  "A13B kod değiştirmez.",
  "A13C önce token ve yeni component CSS dosyası eklemeli; mevcut sınıflar silinmemeli.",
  "İlk uygulama dalgasında yalnızca alias ve düşük riskli ekleme yapılmalı.",
  "Template class değişimleri ayrı fazda ve küçük gruplarla yapılmalı.",
  "Her faz sonunda compileall ve pytest zorunlu.",
  "Mobil responsive dosyaları ayrı dalga olarak ele alınmalı.",
  "inline style temizliği tek seferde yapılmamalı."
]
```

## Sonraki Adım

A13C: design token + ortak component CSS temel dosyası güvenli şekilde eklenecek.