# BYS360 A?ama 6E ?retim Ortam De?i?kenleri S?zle?mesi

Tarih: 2026-06-12T13:19:58
Kaynak: reports\security\BYS360_A6F_STRICT_ENV_SAMPLE.env
Strict mod: True

## ?zet

- OK: True
- Passed: 16
- Warnings: 0
- Failed: 0

## Bulgular

### PASS ? REQUIRED_KEY_PRESENT
- Seviye: info
- Anahtar: `SECRET_KEY`
- Mesaj: SECRET_KEY tan?ml?.

### PASS ? REQUIRED_KEY_PRESENT
- Seviye: info
- Anahtar: `DATABASE_URL`
- Mesaj: DATABASE_URL tan?ml?.

### PASS ? REQUIRED_KEY_PRESENT
- Seviye: info
- Anahtar: `SENTRY_DSN`
- Mesaj: SENTRY_DSN tan?ml?.

### PASS ? REQUIRED_KEY_PRESENT
- Seviye: info
- Anahtar: `SESSION_COOKIE_SECURE`
- Mesaj: SESSION_COOKIE_SECURE tan?ml?.

### PASS ? REQUIRED_KEY_PRESENT
- Seviye: info
- Anahtar: `REMEMBER_COOKIE_SECURE`
- Mesaj: REMEMBER_COOKIE_SECURE tan?ml?.

### PASS ? REQUIRED_KEY_PRESENT
- Seviye: info
- Anahtar: `WTF_CSRF_ENABLED`
- Mesaj: WTF_CSRF_ENABLED tan?ml?.

### PASS ? REQUIRED_KEY_PRESENT
- Seviye: info
- Anahtar: `CSP_ENABLED`
- Mesaj: CSP_ENABLED tan?ml?.

### PASS ? SECRET_KEY_STRONG
- Seviye: info
- Anahtar: `SECRET_KEY`
- Mesaj: SECRET_KEY uzunlu?u yeterli.

### PASS ? DATABASE_IS_POSTGRESQL
- Seviye: info
- Anahtar: `DATABASE_URL`
- Mesaj: DATABASE_URL PostgreSQL g?r?n?yor.

### PASS ? DATABASE_SSL_NOT_DISABLED
- Seviye: info
- Anahtar: `DATABASE_URL`
- Mesaj: DATABASE_URL SSL modu g?venli g?r?n?yor.

### PASS ? SENTRY_DSN_VALID_SHAPE
- Seviye: info
- Anahtar: `SENTRY_DSN`
- Mesaj: SENTRY_DSN bi?imi uygun g?r?n?yor.

### PASS ? DEBUG_DISABLED
- Seviye: info
- Anahtar: `DEBUG`
- Mesaj: DEBUG/FLASK_DEBUG a??k de?il.

### PASS ? SECURE_COOKIE_ENABLED
- Seviye: info
- Anahtar: `SESSION_COOKIE_SECURE`
- Mesaj: SESSION_COOKIE_SECURE=true.

### PASS ? SECURE_COOKIE_ENABLED
- Seviye: info
- Anahtar: `REMEMBER_COOKIE_SECURE`
- Mesaj: REMEMBER_COOKIE_SECURE=true.

### PASS ? CSRF_ENABLED
- Seviye: info
- Anahtar: `WTF_CSRF_ENABLED`
- Mesaj: CSRF kapal? g?r?nm?yor.

### PASS ? CSP_ENABLED
- Seviye: info
- Anahtar: `CSP_ENABLED`
- Mesaj: CSP kapal? g?r?nm?yor.
