# BYS360 Faz 2C3 Final Closure Evidence

Tarih: 2026-06-13T11:28:36

## Sonuç

- OK: True
- Karar: PHASE2C3_GREEN_CLOSED_AUTH_IMPORT_APPLIED
- Explicit expected count: 10
- Explicit OK: True
- Remaining wildcard expected count: 1
- Remaining wildcard OK: True
- App AST wildcard count: 62
- Mobile shared remaining count: 1
- Compileall returncode: 0
- Contract pytest returncode: 0
- Auth guard pytest returncode: 0
- Default pytest returncode: 0
- Tests green: True

## Explicit Status

```json
[
  {
    "file": "app/api/mobile/domains/assistant_chat.py",
    "has_mobile_shared_wildcard": false,
    "has_mobile_shared_explicit": true,
    "ok": true
  },
  {
    "file": "app/api/mobile/domains/auth.py",
    "has_mobile_shared_wildcard": false,
    "has_mobile_shared_explicit": true,
    "ok": true
  },
  {
    "file": "app/api/mobile/domains/communication_v1_write.py",
    "has_mobile_shared_wildcard": false,
    "has_mobile_shared_explicit": true,
    "ok": true
  },
  {
    "file": "app/api/mobile/domains/communication_v2_write.py",
    "has_mobile_shared_wildcard": false,
    "has_mobile_shared_explicit": true,
    "ok": true
  },
  {
    "file": "app/api/mobile/domains/dashboard.py",
    "has_mobile_shared_wildcard": false,
    "has_mobile_shared_explicit": true,
    "ok": true
  },
  {
    "file": "app/api/mobile/domains/kpi_target_management.py",
    "has_mobile_shared_wildcard": false,
    "has_mobile_shared_explicit": true,
    "ok": true
  },
  {
    "file": "app/api/mobile/domains/notifications.py",
    "has_mobile_shared_wildcard": false,
    "has_mobile_shared_explicit": true,
    "ok": true
  },
  {
    "file": "app/api/mobile/domains/personnel_read.py",
    "has_mobile_shared_wildcard": false,
    "has_mobile_shared_explicit": true,
    "ok": true
  },
  {
    "file": "app/api/mobile/domains/personnel_write_all.py",
    "has_mobile_shared_wildcard": false,
    "has_mobile_shared_explicit": true,
    "ok": true
  },
  {
    "file": "app/api/mobile/domains/support_survey_write.py",
    "has_mobile_shared_wildcard": false,
    "has_mobile_shared_explicit": true,
    "ok": true
  }
]
```

## Remaining Wildcard Status

```json
[
  {
    "file": "app/api/mobile/routes.py",
    "has_mobile_shared_wildcard": true,
    "has_mobile_shared_explicit": false,
    "ok": true,
    "reason": "Bilinçli facade import; C4'te ayrı değerlendirilecek."
  }
]
```

## Mobile Shared Remaining

```json
[
  {
    "file": "app/api/mobile/routes.py",
    "line_no": 7,
    "module": "app.api.mobile.shared",
    "level": 0
  }
]
```

## Default Pytest Summary

```json
{
  "passed": 746,
  "skipped": 2,
  "deselected": 34,
  "failed": 0,
  "errors": 0,
  "warnings": 0
}
```

## Sonraki Adım

Faz 2C4: app/api/mobile/routes.py bilinçli facade import ayrı ve yedekli full-gate ile değerlendirilebilir.