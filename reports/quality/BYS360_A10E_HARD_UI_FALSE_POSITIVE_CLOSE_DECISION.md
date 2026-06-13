# BYS360 A10E Hard UI False Positive Kapanış Kararı

Tarih: 2026-06-12T19:09:47

## Sonuç

- OK: True
- Karar: A10E_HARD_UI_CLOSED
- Real user-facing hit count: 0
- Manual review hit count: 1
- Allowed manual review count: 1
- Unallowed manual review count: 0
- False positive hit count: 56
- Compileall returncode: 0

## İzin Verilen Manuel İnceleme

```json
[
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/diagnostics/bys_mobile_crash_service.dart",
    "line": 28,
    "term": "exception",
    "sample": "unawaited(_store(details.exceptionAsString(), details.stack));",
    "suggested_message": "Beklenmeyen bir hata oluştu.",
    "decision": "manual_review"
  }
]
```

## Kapatılmamış Manuel İnceleme

```json
[]
```

## Not

A10C hard UI bulgularında gerçek kullanıcıya görünen teknik metin bulunmadı; kod içi/sanitizer/diagnostic false-positive olarak kapatıldı.