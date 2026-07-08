# BYS360 A?ama 6G CSP / CSRF Risk Ayr??t?rma

Tarih: 2026-06-12T13:22:37

## ?zet

- Toplam CSP/CSRF izi: 31
- Ger?ek aksiyon: 19
- G?zden ge?irilecek / kabul gerek?esi istenen: 6
- Audit/yorum/g?r?lt?: 6

## S?n?flar

- actionable: 19
- accepted_or_review: 6
- audit_rule: 4
- noise: 2

## Konu Tipleri

- CSP_UNSAFE_INLINE: 20
- CSRF_DISABLED: 7
- CSRF_EXEMPT: 4

## Ger?ek Aksiyon Bulgular?

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `app/security/startup_audit.py`
- Sat?r: 101
- Kan?t: `if "'unsafe-inline'" in script_src and not bool(app.config.get("CSP_ALLOW_UNSAFE_INLINE_SCRIPT", False)):`
- ?neri: CSP unsafe kullan?m? g?zden ge?irilmeli.

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `app/security/startup_audit.py`
- Sat?r: 102
- Kan?t: `security_errors.append("CSP_SCRIPT_SRC icinde unsafe-inline bulunamaz; nonce tabanli CSP kullanilmalidir.")`
- ?neri: CSP unsafe kullan?m? g?zden ge?irilmeli.

### HIGH ? CSRF_EXEMPT
- Dosya: `app/api/mobile/__init__.py`
- Sat?r: 18
- Kan?t: `csrf.exempt(mobile_api_bp)`
- ?neri: CSRF muafiyeti ger?ek endpointte g?r?n?yor; gerek?e ve koruma kontrol edilmeli.

### HIGH ? CSRF_EXEMPT
- Dosya: `app/api/mobile/__init__.py`
- Sat?r: 31
- Kan?t: `csrf.exempt(mobile_api_bp)`
- ?neri: CSRF muafiyeti ger?ek endpointte g?r?n?yor; gerek?e ve koruma kontrol edilmeli.

### HIGH ? CSRF_DISABLED
- Dosya: `scripts/quality/bys360_mobile_auth_guard_matrix_gate_p4a.py`
- Sat?r: 243
- Kan?t: `app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)`
- ?neri: CSRF global kapal? olabilir; canl?da kabul edilmez.

### HIGH ? CSRF_DISABLED
- Dosya: `scripts/quality/bys360_mobile_performance_response_gate_p3e.py`
- Sat?r: 152
- Kan?t: `app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)`
- ?neri: CSRF global kapal? olabilir; canl?da kabul edilmez.

### HIGH ? CSRF_DISABLED
- Dosya: `scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b.py`
- Sat?r: 258
- Kan?t: `app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)`
- ?neri: CSRF global kapal? olabilir; canl?da kabul edilmez.

### HIGH ? CSRF_DISABLED
- Dosya: `scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v2.py`
- Sat?r: 293
- Kan?t: `app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)`
- ?neri: CSRF global kapal? olabilir; canl?da kabul edilmez.

### HIGH ? CSRF_DISABLED
- Dosya: `scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v3.py`
- Sat?r: 312
- Kan?t: `app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)`
- ?neri: CSRF global kapal? olabilir; canl?da kabul edilmez.

### HIGH ? CSRF_DISABLED
- Dosya: `scripts/quality/bys360_mobile_support_survey_notifications_response_gate_p3d.py`
- Sat?r: 143
- Kan?t: `app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)`
- ?neri: CSRF global kapal? olabilir; canl?da kabul edilmez.

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `scripts/security/check_bys360_p0_security_observability_v1.py`
- Sat?r: 107
- Kan?t: `failures.append('CSP_SCRIPT_SRC varsayılanı unsafe-inline içermeyecek şekilde güncellenmemiş.')`
- ?neri: CSP unsafe kullan?m? g?zden ge?irilmeli.

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `scripts/security/check_bys360_p0_security_observability_v1.py`
- Sat?r: 112
- Kan?t: `if 'inject_csp_nonce_into_html' not in headers or "'unsafe-inline'" in script_default:`
- ?neri: CSP unsafe kullan?m? g?zden ge?irilmeli.

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `scripts/security/check_bys360_p0_security_observability_v1.py`
- Sat?r: 113
- Kan?t: `failures.append('CSP header/nonce uygulaması eksik veya DEFAULT_CSP script tarafında unsafe-inline içeriyor.')`
- ?neri: CSP unsafe kullan?m? g?zden ge?irilmeli.

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `scripts/security/check_bys360_p0_sentry_dbssl_csp_v2.py`
- Sat?r: 98
- Kan?t: `failures.append('CSP_SCRIPT_SRC varsayılanı unsafe-inline içermeyecek şekilde güncellenmemiş.')`
- ?neri: CSP unsafe kullan?m? g?zden ge?irilmeli.

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `scripts/security/check_bys360_p0_sentry_dbssl_csp_v2.py`
- Sat?r: 113
- Kan?t: `if "'unsafe-inline'" in script_default:`
- ?neri: CSP unsafe kullan?m? g?zden ge?irilmeli.

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `scripts/security/check_bys360_p0_sentry_dbssl_csp_v2.py`
- Sat?r: 114
- Kan?t: `failures.append('DEFAULT_CSP script-src hala unsafe-inline içeriyor.')`
- ?neri: CSP unsafe kullan?m? g?zden ge?irilmeli.

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `scripts/security/check_bys360_p0_sentry_dbssl_csp_v2.py`
- Sat?r: 166
- Kan?t: `failures.append('.env içinde CSP_ALLOW_UNSAFE_INLINE_SCRIPT=true var; script unsafe-inline kapatılmalı.')`
- ?neri: CSP unsafe kullan?m? g?zden ge?irilmeli.

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `scripts/security/check_bys360_p0_sentry_dbssl_csp_v2.py`
- Sat?r: 167
- Kan?t: `if "'unsafe-inline'" in csp_script:`
- ?neri: CSP unsafe kullan?m? g?zden ge?irilmeli.

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `scripts/security/check_bys360_p0_sentry_dbssl_csp_v2.py`
- Sat?r: 168
- Kan?t: `failures.append('.env CSP_SCRIPT_SRC içinde unsafe-inline var; nonce tabanlı CSP kullanılmalı.')`
- ?neri: CSP unsafe kullan?m? g?zden ge?irilmeli.


## G?zden Ge?irilecek Bulgular

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `config.py`
- Sat?r: 334
- Kan?t: `CSP_STYLE_SRC = os.getenv('CSP_STYLE_SRC', "'self' 'unsafe-inline' https:").strip() or "'self' 'unsafe-inline' https:"`
- Not: CSP unsafe kullan?m? g?zden ge?irilmeli.

### MEDIUM ? CSRF_EXEMPT
- Dosya: `app/communication/announcement_popup_routes.py`
- Sat?r: 380
- Kan?t: `@csrf.exempt`
- Not: Popup/duyuru endpoint muafiyeti gerek?elendirilmeli; rate limit ve auth kontrol edilmeli.

### MEDIUM ? CSRF_EXEMPT
- Dosya: `app/communication/announcement_popup_routes.py`
- Sat?r: 395
- Kan?t: `@csrf.exempt`
- Not: Popup/duyuru endpoint muafiyeti gerek?elendirilmeli; rate limit ve auth kontrol edilmeli.

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `app/security/csp_nonce.py`
- Sat?r: 61
- Kan?t: `f"style-src 'self' 'nonce-{nonce}' 'unsafe-inline'; "`
- Not: style-src unsafe-inline ge?ici uyumluluk olabilir; nonce/stylesheet plan?yla azalt?lmal?.

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `app/security/headers.py`
- Sat?r: 25
- Kan?t: `"style-src": "'self' 'unsafe-inline' https:",`
- Not: style-src unsafe-inline ge?ici uyumluluk olabilir; nonce/stylesheet plan?yla azalt?lmal?.

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `app/security/headers.py`
- Sat?r: 67
- Kan?t: `value = _remove_token(value, "'unsafe-inline'")`
- Not: CSP unsafe kullan?m? g?zden ge?irilmeli.
