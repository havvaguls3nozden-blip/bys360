# BYS360 A12C UI Teknik Dil Güvenli Temizlik

Tarih: 2026-06-13T08:45:56

## Sonuç

- OK: True
- Karar: A12C_SAFE_CLEANUP_GREEN
- Source A12B OK: True
- Backup root: `C:\bys360\releases\A12C_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP_BACKUP_20260613_084515`
- Target file count: 8
- Total replacements: 16
- Remaining old phrase count: 0
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

## Operations

```json
[
  {
    "path": "app/templates/communication/phase9_release_center.html",
    "status": "patched",
    "replacement_count": 2,
    "backup": "C:\\bys360\\releases\\A12C_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP_BACKUP_20260613_084515\\app\\templates\\communication\\phase9_release_center.html",
    "details": [
      {
        "old": "Hotfix ve rollback kararı yazılı kayıtla yönetilir.",
        "new": "Acil düzeltme ve geri dönüş kararı yazılı kayıtla yönetilir.",
        "count": 2
      }
    ]
  },
  {
    "path": "app/templates/communication/phase9b_dashboard.html",
    "status": "patched",
    "replacement_count": 4,
    "backup": "C:\\bys360\\releases\\A12C_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP_BACKUP_20260613_084515\\app\\templates\\communication\\phase9b_dashboard.html",
    "details": [
      {
        "old": "Veri geçişi, migration görünürlüğü, sicil omurgası ve güvenlik kapıları için canlı öncesi kontrol merkezi.",
        "new": "Veri geçişi, kayıt görünürlüğü, sicil omurgası ve güvenlik kontrolleri için canlı öncesi kontrol merkezi.",
        "count": 1
      },
      {
        "old": "Versiyon klasörü:",
        "new": "Kayıt klasörü:",
        "count": 1
      },
      {
        "old": "Versiyon dosyası",
        "new": "Kayıt dosyası",
        "count": 1
      },
      {
        "old": "SQL hotfix dosyası",
        "new": "Veri düzeltme dosyası",
        "count": 1
      }
    ]
  },
  {
    "path": "app/templates/communication/phase9b_transition_center.html",
    "status": "patched",
    "replacement_count": 1,
    "backup": "C:\\bys360\\releases\\A12C_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP_BACKUP_20260613_084515\\app\\templates\\communication\\phase9b_transition_center.html",
    "details": [
      {
        "old": "Sicil omurgası, migration görünürlüğü, env sertleştirmesi ve güvenlik denetimi aynı ekranda yönetilir.",
        "new": "Sicil omurgası, kayıt görünürlüğü, ortam ayarları ve güvenlik denetimi aynı ekranda yönetilir.",
        "count": 1
      }
    ]
  },
  {
    "path": "app/templates/communication/phase9d_dashboard.html",
    "status": "patched",
    "replacement_count": 3,
    "backup": "C:\\bys360\\releases\\A12C_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP_BACKUP_20260613_084515\\app\\templates\\communication\\phase9d_dashboard.html",
    "details": [
      {
        "old": "İlk 72 saat stabilizasyonu, sıcak izleme sinyalleri, hotfix baskısı ve kapanış kararları için merkezi görünüm.",
        "new": "İlk 72 saat stabilizasyonu, sıcak izleme sinyalleri, acil düzeltme ihtiyacı ve kapanış kararları için merkezi görünüm.",
        "count": 1
      },
      {
        "old": "Son hotfix kayıtları",
        "new": "Son acil düzeltme kayıtları",
        "count": 1
      },
      {
        "old": "Henüz hotfix kaydı bulunmuyor.",
        "new": "Henüz acil düzeltme kaydı bulunmuyor.",
        "count": 1
      }
    ]
  },
  {
    "path": "app/templates/communication/phase9d_stabilization_center.html",
    "status": "patched",
    "replacement_count": 3,
    "backup": "C:\\bys360\\releases\\A12C_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP_BACKUP_20260613_084515\\app\\templates\\communication\\phase9d_stabilization_center.html",
    "details": [
      {
        "old": "İlk 72 saatte check-in, hotfix ve saha sinyalleri aynı merkezden kayıt altına alınır.",
        "new": "İlk 72 saatte günlük kontrol, acil düzeltme ve saha sinyalleri aynı merkezden kayıt altına alınır.",
        "count": 1
      },
      {
        "old": "Hotfix kaydı",
        "new": "Acil düzeltme kaydı",
        "count": 1
      },
      {
        "old": "Hotfix kaydet",
        "new": "Acil düzeltme kaydet",
        "count": 1
      }
    ]
  },
  {
    "path": "app/static/js/bys360_ai_everywhere_v1.js",
    "status": "patched",
    "replacement_count": 1,
    "backup": "C:\\bys360\\releases\\A12C_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP_BACKUP_20260613_084515\\app\\static\\js\\bys360_ai_everywhere_v1.js",
    "details": [
      {
        "old": "route erişim kontrolünü",
        "new": "sayfa erişim kontrolünü",
        "count": 1
      }
    ]
  },
  {
    "path": "app/templates/admin/performance_menu_visibility_settings.html",
    "status": "patched",
    "replacement_count": 1,
    "backup": "C:\\bys360\\releases\\A12C_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP_BACKUP_20260613_084515\\app\\templates\\admin\\performance_menu_visibility_settings.html",
    "details": [
      {
        "old": "route ve backend yetki kontrolleri",
        "new": "sayfa ve sistem yetki kontrolleri",
        "count": 1
      }
    ]
  },
  {
    "path": "app/templates/admin_system_scan.html",
    "status": "patched",
    "replacement_count": 1,
    "backup": "C:\\bys360\\releases\\A12C_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP_BACKUP_20260613_084515\\app\\templates\\admin_system_scan.html",
    "details": [
      {
        "old": "route yogunlugu",
        "new": "ekran yogunlugu",
        "count": 1
      }
    ]
  }
]
```

## Remaining Old Phrases

```json
[]
```

## Sonraki Adım

A12D: Kullanıcıya görünen teknik dil için final doğrulama ve evidence paketi üretilecek.