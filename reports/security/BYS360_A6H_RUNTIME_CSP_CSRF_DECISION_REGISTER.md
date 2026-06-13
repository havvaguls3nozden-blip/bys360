# BYS360 A?ama 6H Runtime CSP/CSRF Karar Kayd?

Tarih: 2026-06-12T13:29:01

## ?zet

- Toplam CSP/CSRF izi: 31
- Ger?ek runtime aksiyon: 1
- Kabul / takip kayd?: 7
- Kontrol scripti veya runtime guard: 22
- Manuel review: 0

## S?n?fland?rma

- control_script: 15
- control_runtime_guard: 7
- accepted_with_followup: 5
- accepted_with_controls: 2
- noise: 1
- runtime_action: 1

## Mobil API Koruma Kan?t?

- Auth/token izi olan dosyalar: ['app/api/mobile/__init__.py', 'app/api/mobile/communication_read_routes.py', 'app/api/mobile/communication_v2_read_routes.py', 'app/api/mobile/detail_read_routes.py', 'app/api/mobile/domains/assistant_chat.py', 'app/api/mobile/domains/auth.py', 'app/api/mobile/domains/communication_v1_write.py', 'app/api/mobile/domains/communication_v2_write.py', 'app/api/mobile/domains/dashboard.py', 'app/api/mobile/domains/kpi_target_management.py', 'app/api/mobile/domains/notifications.py', 'app/api/mobile/domains/personnel_read.py', 'app/api/mobile/domains/personnel_write_all.py', 'app/api/mobile/domains/support_survey_write.py', 'app/api/mobile/light_read_routes.py', 'app/api/mobile/performance_read_routes.py', 'app/api/mobile/performance_routes.py', 'app/api/mobile/services/auth_service.py', 'app/api/mobile/shared.py', 'app/api/mobile/support_survey_read_routes.py', 'app/api/mobile/utility_routes.py']
- Token/authorization izi olan dosyalar: ['app/api/mobile/__init__.py', 'app/api/mobile/domains/auth.py', 'app/api/mobile/domains/support_survey_write.py', 'app/api/mobile/services/auth_service.py', 'app/api/mobile/shared.py']
- Rate limit izi olan dosyalar: []

## Ger?ek Runtime Aksiyonlar

### HIGH ? CSP_UNSAFE_INLINE
- Dosya: `app/security/headers.py`
- Sat?r: 9
- Karar: script-src unsafe-inline
- Kan?t: `- script-src tarafinda unsafe-inline varsayilan kullanilmaz.`
- ?neri: Canl?da script-src unsafe-inline olmamal?.


## Kabul / Takip Kay?tlar?

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `config.py`
- Sat?r: 334
- Karar: Varsay?lan style-src uyumluluk istisnas?
- Kan?t: `CSP_STYLE_SRC = os.getenv('CSP_STYLE_SRC', "'self' 'unsafe-inline' https:").strip() or "'self' 'unsafe-inline' https:"`
- Takip: Script-src de?il; style-src i?in takip karar? yaz?lmal?.

### MEDIUM ? CSRF_EXEMPT
- Dosya: `app/communication/announcement_popup_routes.py`
- Sat?r: 380
- Karar: Duyuru popup CSRF muafiyeti
- Kan?t: `@csrf.exempt`
- Takip: Endpoint auth/rate-limit/gerek?e kontrol? ile takip edilmeli.

### MEDIUM ? CSRF_EXEMPT
- Dosya: `app/communication/announcement_popup_routes.py`
- Sat?r: 395
- Karar: Duyuru popup CSRF muafiyeti
- Kan?t: `@csrf.exempt`
- Takip: Endpoint auth/rate-limit/gerek?e kontrol? ile takip edilmeli.

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `app/security/csp_nonce.py`
- Sat?r: 61
- Karar: style-src uyumluluk istisnas?
- Kan?t: `f"style-src 'self' 'nonce-{nonce}' 'unsafe-inline'; "`
- Takip: Ge?ici kabul edilebilir; orta vadede inline style azaltma/nonce/stylesheet plan? gerekli.

### MEDIUM ? CSP_UNSAFE_INLINE
- Dosya: `app/security/headers.py`
- Sat?r: 25
- Karar: style-src uyumluluk istisnas?
- Kan?t: `"style-src": "'self' 'unsafe-inline' https:",`
- Takip: Ge?ici kabul edilebilir; orta vadede inline style azaltma/nonce/stylesheet plan? gerekli.

### MEDIUM ? CSRF_EXEMPT
- Dosya: `app/api/mobile/__init__.py`
- Sat?r: 18
- Karar: Mobil API CSRF muafiyeti
- Kan?t: `csrf.exempt(mobile_api_bp)`
- Takip: Token/auth tabanl? mobil API i?in kabul edilebilir; auth/rate-limit kan?t? takip edilmeli.

### MEDIUM ? CSRF_EXEMPT
- Dosya: `app/api/mobile/__init__.py`
- Sat?r: 31
- Karar: Mobil API CSRF muafiyeti
- Kan?t: `csrf.exempt(mobile_api_bp)`
- Takip: Token/auth tabanl? mobil API i?in kabul edilebilir; auth/rate-limit kan?t? takip edilmeli.


## Manuel Review

Manuel review yok.