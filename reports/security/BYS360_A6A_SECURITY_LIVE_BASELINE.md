# BYS360 A?ama 6A G?venlik ve Canl? Haz?rl?k Baseline

Tarih: 2026-06-12T13:05:09

## ?zet

- Toplam bulgu: 1276
- High: 761
- Medium: 515
- Low: 0

## Bulgu Tipleri

- SENTRY_PLACEHOLDER_OR_DISABLED: 647
- HARDCODED_SECRET_LIKE_VALUE: 298
- SQLITE_RUNTIME_FILE_REFERENCE: 194
- HARDCODED_DEFAULT_PASSWORD: 75
- CSP_UNSAFE_INLINE_OR_EVAL: 22
- CSRF_DISABLED_OR_EXEMPT: 21
- DB_SSL_DISABLED: 11
- ENV_FILE_PRESENT: 4
- DEBUG_ENABLED: 2
- ERROR_TEMPLATE_MISSING: 1
- RELEASEIGNORE_MISSING_RULE: 1

## ?lk 80 Bulgu

### MEDIUM ? SQLITE_RUNTIME_FILE_REFERENCE
- Dosya: `.env`
- Sat?r: 2
- Kan?t: `DATABASE_URL=sqlite:///C:/bys360/project/instance/bys360_local_dev.sqlite3`
- ?neri: Canl? pakette ger?ek SQLite dosyas? ya da runtime DB yolu s?zmamal?.

### HIGH ? DB_SSL_DISABLED
- Dosya: `.env.docker.example`
- Sat?r: 12
- Kan?t: `DATABASE_URL=postgresql+psycopg2://bys_user:change_me_only_for_local@postgres:5432/bys_db?sslmode=disable`
- ?neri: ?retim PostgreSQL ba?lant?s?nda SSL kapal? g?r?nmemeli.

### HIGH ? HARDCODED_DEFAULT_PASSWORD
- Dosya: `.env.docker.example`
- Sat?r: 12
- Kan?t: `DATABASE_URL=postgresql+psycopg2://bys_user:change_me_only_for_local@postgres:5432/bys_db?sslmode=disable`
- ?neri: Varsay?lan/parola kal?nt?lar? canl? pakete girmemeli.

### HIGH ? DB_SSL_DISABLED
- Dosya: `.env.docker.example`
- Sat?r: 13
- Kan?t: `SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://bys_user:change_me_only_for_local@postgres:5432/bys_db?sslmode=disable`
- ?neri: ?retim PostgreSQL ba?lant?s?nda SSL kapal? g?r?nmemeli.

### HIGH ? HARDCODED_DEFAULT_PASSWORD
- Dosya: `.env.docker.example`
- Sat?r: 13
- Kan?t: `SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://bys_user:change_me_only_for_local@postgres:5432/bys_db?sslmode=disable`
- ?neri: Varsay?lan/parola kal?nt?lar? canl? pakete girmemeli.

### HIGH ? DB_SSL_DISABLED
- Dosya: `.env.docker.example`
- Sat?r: 15
- Kan?t: `DB_SSLMODE=disable`
- ?neri: ?retim PostgreSQL ba?lant?s?nda SSL kapal? g?r?nmemeli.

### HIGH ? HARDCODED_DEFAULT_PASSWORD
- Dosya: `.env.docker.example`
- Sat?r: 18
- Kan?t: `POSTGRES_PASSWORD=***MASKED***`
- ?neri: Varsay?lan/parola kal?nt?lar? canl? pakete girmemeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `.env.docker.example`
- Sat?r: 18
- Kan?t: `POSTGRES_PASSWORD=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### HIGH ? SENTRY_PLACEHOLDER_OR_DISABLED
- Dosya: `.env.docker.example`
- Sat?r: 39
- Kan?t: `SENTRY_DSN=`
- ?neri: Sentry/izleme DSN ger?ek ?retim de?eriyle env ?zerinden tan?mlanmal?; placeholder kalmamal?.

### HIGH ? HARDCODED_DEFAULT_PASSWORD
- Dosya: `.env.example`
- Sat?r: 6
- Kan?t: `DATABASE_URL=CHANGE_ME`
- ?neri: Varsay?lan/parola kal?nt?lar? canl? pakete girmemeli.

### HIGH ? DB_SSL_DISABLED
- Dosya: `.env.production.example`
- Sat?r: 8
- Kan?t: `# PostgreSQL SSL zorunlu: sslmode=disable kullanılmaz.`
- ?neri: ?retim PostgreSQL ba?lant?s?nda SSL kapal? g?r?nmemeli.

### HIGH ? SENTRY_PLACEHOLDER_OR_DISABLED
- Dosya: `.env.production.example`
- Sat?r: 13
- Kan?t: `# Sentry: placeholder kabul edilmez. Production/pilot ortamında gerçek DSN zorunludur.`
- ?neri: Sentry/izleme DSN ger?ek ?retim de?eriyle env ?zerinden tan?mlanmal?; placeholder kalmamal?.

### HIGH ? SENTRY_PLACEHOLDER_OR_DISABLED
- Dosya: `.env.production.example`
- Sat?r: 14
- Kan?t: `SENTRY_DSN=***MASKED***`
- ?neri: Sentry/izleme DSN ger?ek ?retim de?eriyle env ?zerinden tan?mlanmal?; placeholder kalmamal?.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `.env.production.example`
- Sat?r: 14
- Kan?t: `SENTRY_DSN=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### HIGH ? CSP_UNSAFE_INLINE_OR_EVAL
- Dosya: `.env.production.example`
- Sat?r: 21
- Kan?t: `# CSP: script tarafında unsafe-inline yok, nonce tabanlı çalışır.`
- ?neri: CSP nonce/hash tabanl? hale getirilmeli; unsafe-inline/unsafe-eval azalt?lmal?.

### HIGH ? CSP_UNSAFE_INLINE_OR_EVAL
- Dosya: `.env.production.example`
- Sat?r: 27
- Kan?t: `CSP_STYLE_SRC='self' 'unsafe-inline' https:`
- ?neri: CSP nonce/hash tabanl? hale getirilmeli; unsafe-inline/unsafe-eval azalt?lmal?.

### MEDIUM ? SQLITE_RUNTIME_FILE_REFERENCE
- Dosya: `alembic.ini`
- Sat?r: 16
- Kan?t: `sqlalchemy.url = sqlite:///:memory:`
- ?neri: Canl? pakette ger?ek SQLite dosyas? ya da runtime DB yolu s?zmamal?.

### HIGH ? SENTRY_PLACEHOLDER_OR_DISABLED
- Dosya: `config.py`
- Sat?r: 169
- Kan?t: `_secret_placeholder_values = {`
- ?neri: Sentry/izleme DSN ger?ek ?retim de?eriyle env ?zerinden tan?mlanmal?; placeholder kalmamal?.

### HIGH ? HARDCODED_DEFAULT_PASSWORD
- Dosya: `config.py`
- Sat?r: 171
- Kan?t: `'CHANGE_ME',`
- ?neri: Varsay?lan/parola kal?nt?lar? canl? pakete girmemeli.

### HIGH ? HARDCODED_DEFAULT_PASSWORD
- Dosya: `config.py`
- Sat?r: 173
- Kan?t: `'changeme',`
- ?neri: Varsay?lan/parola kal?nt?lar? canl? pakete girmemeli.

### HIGH ? SENTRY_PLACEHOLDER_OR_DISABLED
- Dosya: `config.py`
- Sat?r: 176
- Kan?t: `_secret_is_strong = bool(_raw_secret_key and _raw_secret_key not in _secret_placeholder_values and len(_raw_secret_key) >= 32)`
- ?neri: Sentry/izleme DSN ger?ek ?retim de?eriyle env ?zerinden tan?mlanmal?; placeholder kalmamal?.

### MEDIUM ? SQLITE_RUNTIME_FILE_REFERENCE
- Dosya: `config.py`
- Sat?r: 185
- Kan?t: `_raw_database_url = (os.getenv("DATABASE_URL") or "").strip() or 'sqlite:///:memory:'`
- ?neri: Canl? pakette ger?ek SQLite dosyas? ya da runtime DB yolu s?zmamal?.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `config.py`
- Sat?r: 246
- Kan?t: `DEFAULT_FIRST_LOGIN_PASSWORD=***MASKED***'DEFAULT_FIRST_LOGIN_PASSWORD', '').strip()`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### HIGH ? SENTRY_PLACEHOLDER_OR_DISABLED
- Dosya: `config.py`
- Sat?r: 310
- Kan?t: `SENTRY_DSN=***MASKED***"SENTRY_DSN") or "").strip()`
- ?neri: Sentry/izleme DSN ger?ek ?retim de?eriyle env ?zerinden tan?mlanmal?; placeholder kalmamal?.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `config.py`
- Sat?r: 310
- Kan?t: `SENTRY_DSN=***MASKED***"SENTRY_DSN") or "").strip()`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### HIGH ? CSP_UNSAFE_INLINE_OR_EVAL
- Dosya: `config.py`
- Sat?r: 334
- Kan?t: `CSP_STYLE_SRC = os.getenv('CSP_STYLE_SRC', "'self' 'unsafe-inline' https:").strip() or "'self' 'unsafe-inline' https:"`
- ?neri: CSP nonce/hash tabanl? hale getirilmeli; unsafe-inline/unsafe-eval azalt?lmal?.

### HIGH ? CSP_UNSAFE_INLINE_OR_EVAL
- Dosya: `config.py`
- Sat?r: 335
- Kan?t: `# BYS360_P0_SECURITY_OBSERVABILITY_V1: script tarafinda unsafe-inline varsayilan kapali; nonce uygulanir.`
- ?neri: CSP nonce/hash tabanl? hale getirilmeli; unsafe-inline/unsafe-eval azalt?lmal?.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `config.py`
- Sat?r: 351
- Kan?t: `MAIL_PASSWORD=***MASKED***'MAIL_PASSWORD', '')`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `config.py`
- Sat?r: 361
- Kan?t: `AI_API_KEY=***MASKED***'AI_API_KEY', '').strip()`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### HIGH ? HARDCODED_DEFAULT_PASSWORD
- Dosya: `docker-compose.yml`
- Sat?r: 12
- Kan?t: `POSTGRES_PASSWORD=***MASKED***`
- ?neri: Varsay?lan/parola kal?nt?lar? canl? pakete girmemeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `docker-compose.yml`
- Sat?r: 12
- Kan?t: `POSTGRES_PASSWORD=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? SQLITE_RUNTIME_FILE_REFERENCE
- Dosya: `app\menu_registry_data_sections.py`
- Sat?r: 620
- Kan?t: `"endpoint": "main.db_check",`
- ?neri: Canl? pakette ger?ek SQLite dosyas? ya da runtime DB yolu s?zmamal?.

### MEDIUM ? SQLITE_RUNTIME_FILE_REFERENCE
- Dosya: `app\menu_registry_data_sections.py`
- Sat?r: 621
- Kan?t: `"active_endpoints": ["main.db_check"],`
- ?neri: Canl? pakette ger?ek SQLite dosyas? ya da runtime DB yolu s?zmamal?.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `app\route_support.py`
- Sat?r: 489
- Kan?t: `token=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `app\route_support.py`
- Sat?r: 490
- Kan?t: `session[f"form_token=***MASKED***"] = token`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `app\route_support.py`
- Sat?r: 496
- Kan?t: `key = f"form_token=***MASKED***"`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `app\schema_guard_engine.py`
- Sat?r: 130
- Kan?t: `token=***MASKED***'"')`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### HIGH ? HARDCODED_DEFAULT_PASSWORD
- Dosya: `app\startup_checks.py`
- Sat?r: 80
- Kan?t: `if strict_env_validation and (not database_uri or "CHANGE_ME" in database_uri or database_uri == "sqlite:///:memory:"):`
- ?neri: Varsay?lan/parola kal?nt?lar? canl? pakete girmemeli.

### MEDIUM ? SQLITE_RUNTIME_FILE_REFERENCE
- Dosya: `app\startup_checks.py`
- Sat?r: 80
- Kan?t: `if strict_env_validation and (not database_uri or "CHANGE_ME" in database_uri or database_uri == "sqlite:///:memory:"):`
- ?neri: Canl? pakette ger?ek SQLite dosyas? ya da runtime DB yolu s?zmamal?.

### HIGH ? SENTRY_PLACEHOLDER_OR_DISABLED
- Dosya: `docs\BYS360_OPS_HARDENING_V1_README.md`
- Sat?r: 46
- Kan?t: `- Gerçek `SECRET_KEY`, `DATABASE_URL`, `SENTRY_DSN` ve mail bilgileri yalnızca sunucu/gizli ortam yönetiminde tutulur.`
- ?neri: Sentry/izleme DSN ger?ek ?retim de?eriyle env ?zerinden tan?mlanmal?; placeholder kalmamal?.

### HIGH ? DB_SSL_DISABLED
- Dosya: `docs\BYS360_OPS_HARDENING_V1_README.md`
- Sat?r: 47
- Kan?t: `- Docker local örneğinde `sslmode=disable` sadece yerel Postgres içindir. Canlı dış veritabanında `sslmode=require` kullanılmalıdır.`
- ?neri: ?retim PostgreSQL ba?lant?s?nda SSL kapal? g?r?nmemeli.

### MEDIUM ? SQLITE_RUNTIME_FILE_REFERENCE
- Dosya: `migrations\env.py`
- Sat?r: 21
- Kan?t: `return current_app.extensions['migrate'].db.get_engine()`
- ?neri: Canl? pakette ger?ek SQLite dosyas? ya da runtime DB yolu s?zmamal?.

### MEDIUM ? SQLITE_RUNTIME_FILE_REFERENCE
- Dosya: `migrations\env.py`
- Sat?r: 24
- Kan?t: `return current_app.extensions['migrate'].db.engine`
- ?neri: Canl? pakette ger?ek SQLite dosyas? ya da runtime DB yolu s?zmamal?.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `migrations\env.py`
- Sat?r: 29
- Kan?t: `return get_engine().url.render_as_string(hide_password=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? SQLITE_RUNTIME_FILE_REFERENCE
- Dosya: `migrations\env.py`
- Sat?r: 40
- Kan?t: `target_db = current_app.extensions['migrate'].db`
- ?neri: Canl? pakette ger?ek SQLite dosyas? ya da runtime DB yolu s?zmamal?.

### HIGH ? HARDCODED_DEFAULT_PASSWORD
- Dosya: `scripts\check_bys360_mobile_v2_8_74_android_release_ready_p0.py`
- Sat?r: 88
- Kan?t: `if "YOUR_LOCAL_" in key_text or "CHANGE_ME" in key_text:`
- ?neri: Varsay?lan/parola kal?nt?lar? canl? pakete girmemeli.

### HIGH ? SENTRY_PLACEHOLDER_OR_DISABLED
- Dosya: `scripts\check_bys360_mobile_v2_8_74_android_release_ready_p0.py`
- Sat?r: 89
- Kan?t: `fail("key.properties still contains placeholder values")`
- ?neri: Sentry/izleme DSN ger?ek ?retim de?eriyle env ?zerinden tan?mlanmal?; placeholder kalmamal?.

### HIGH ? SENTRY_PLACEHOLDER_OR_DISABLED
- Dosya: `scripts\repair_bys360_corporate_portal_media_video_v2_3.py`
- Sat?r: 213
- Kan?t: `<input id="portal-video-url" class="portal-input" type="url" name="video_url" maxlength="700" placeholder="YouTube veya Vimeo bağlantısı yapıştırın">`
- ?neri: Sentry/izleme DSN ger?ek ?retim de?eriyle env ?zerinden tan?mlanmal?; placeholder kalmamal?.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `scripts\repair_bys360_mobile_v2_8_74_android_release_ready_p0.py`
- Sat?r: 103
- Kan?t: `storePassword=***MASKED***"storePassword")`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `scripts\repair_bys360_mobile_v2_8_74_android_release_ready_p0.py`
- Sat?r: 105
- Kan?t: `keyPassword=***MASKED***"keyPassword")`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `scripts\repair_bys360_mobile_v2_8_74_android_release_ready_p0.py`
- Sat?r: 191
- Kan?t: `final token=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `scripts\repair_bys360_mobile_v2_8_74_android_release_ready_p0.py`
- Sat?r: 233
- Kan?t: `accessToken=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `scripts\repair_bys360_mobile_v2_8_74_android_release_ready_p0.py`
- Sat?r: 234
- Kan?t: `refreshToken=***MASKED***'refresh_token']?.toString(),`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `scripts\repair_bys360_mobile_v2_8_74_android_release_ready_p0.py`
- Sat?r: 327
- Kan?t: `storePassword=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `scripts\repair_bys360_mobile_v2_8_74_android_release_ready_p0.py`
- Sat?r: 329
- Kan?t: `keyPassword=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### HIGH ? SENTRY_PLACEHOLDER_OR_DISABLED
- Dosya: `scripts\repair_bys360_portal_composer_accordion_v2_6.py`
- Sat?r: 8
- Kan?t: `COMPOSER_TEMPLATE = '{# BYS360_PORTAL_COMPOSER_ACCORDION_V2_6_BEGIN #}\n<section class="portal-card portal-composer-card portal-composer-accordion" aria-label="Yeni portal paylaşım...`
- ?neri: Sentry/izleme DSN ger?ek ?retim de?eriyle env ?zerinden tan?mlanmal?; placeholder kalmamal?.

### HIGH ? SENTRY_PLACEHOLDER_OR_DISABLED
- Dosya: `scripts\repair_bys360_portal_people_premium_v2_10.py`
- Sat?r: 272
- Kan?t: `<input id="portal_people_q" class="portal-input" type="search" name="q" value="{{ portal_people_query or '' }}" placeholder="Örn. Gülsen, Bilgi Teknolojileri, Koordinatör">`
- ?neri: Sentry/izleme DSN ger?ek ?retim de?eriyle env ?zerinden tan?mlanmal?; placeholder kalmamal?.

### HIGH ? SENTRY_PLACEHOLDER_OR_DISABLED
- Dosya: `scripts\repair_bys360_portal_profile_wall_v2_9.py`
- Sat?r: 449
- Kan?t: `<input class="portal-input" type="search" name="q" placeholder="Ad, soyad, birim veya unvan ile ara">`
- ?neri: Sentry/izleme DSN ger?ek ?retim de?eriyle env ?zerinden tan?mlanmal?; placeholder kalmamal?.

### HIGH ? SENTRY_PLACEHOLDER_OR_DISABLED
- Dosya: `scripts\repair_bys360_portal_profile_wall_v2_9.py`
- Sat?r: 496
- Kan?t: `<input class="portal-input" type="search" name="q" value="{{{{ portal_people_query or '' }}}}" placeholder="Örn. Gülsen, Bilgi Teknolojileri, Koordinatör">`
- ?neri: Sentry/izleme DSN ger?ek ?retim de?eriyle env ?zerinden tan?mlanmal?; placeholder kalmamal?.

### MEDIUM ? SQLITE_RUNTIME_FILE_REFERENCE
- Dosya: `scripts\split_clean_bys360_source_for_upload.ps1`
- Sat?r: 47
- Kan?t: `"*.db",`
- ?neri: Canl? pakette ger?ek SQLite dosyas? ya da runtime DB yolu s?zmamal?.

### MEDIUM ? SQLITE_RUNTIME_FILE_REFERENCE
- Dosya: `scripts\split_clean_bys360_source_for_upload.ps1`
- Sat?r: 48
- Kan?t: `"*.sqlite",`
- ?neri: Canl? pakette ger?ek SQLite dosyas? ya da runtime DB yolu s?zmamal?.

### MEDIUM ? SQLITE_RUNTIME_FILE_REFERENCE
- Dosya: `scripts\split_clean_bys360_source_for_upload.ps1`
- Sat?r: 49
- Kan?t: `"*.sqlite3",`
- ?neri: Canl? pakette ger?ek SQLite dosyas? ya da runtime DB yolu s?zmamal?.

### MEDIUM ? SQLITE_RUNTIME_FILE_REFERENCE
- Dosya: `tests\conftest.py`
- Sat?r: 91
- Kan?t: `db_path = test_runtime / "bys360_a5_test.sqlite3"`
- ?neri: Canl? pakette ger?ek SQLite dosyas? ya da runtime DB yolu s?zmamal?.

### MEDIUM ? SQLITE_RUNTIME_FILE_REFERENCE
- Dosya: `tests\conftest.py`
- Sat?r: 92
- Kan?t: `db_uri = "sqlite:///" + db_path.as_posix()`
- ?neri: Canl? pakette ger?ek SQLite dosyas? ya da runtime DB yolu s?zmamal?.

### MEDIUM ? CSRF_DISABLED_OR_EXEMPT
- Dosya: `tests\conftest.py`
- Sat?r: 105
- Kan?t: `WTF_CSRF_ENABLED=False,`
- ?neri: CSRF muafiyetleri canl? endpointlerde gerek?eli ve s?n?rl? olmal?.

### MEDIUM ? CSRF_DISABLED_OR_EXEMPT
- Dosya: `tests\test_sp_routes_smoke.py`
- Sat?r: 33
- Kan?t: `app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)`
- ?neri: CSRF muafiyetleri canl? endpointlerde gerek?eli ve s?n?rl? olmal?.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `app\admin\routes.py`
- Sat?r: 412
- Kan?t: `initial_password=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `app\admin\routes.py`
- Sat?r: 710
- Kan?t: `initial_password=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `app\admin\routes.py`
- Sat?r: 775
- Kan?t: `new_password=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `app\admin\routes.py`
- Sat?r: 810
- Kan?t: `new_password=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `app\admin\routes.py`
- Sat?r: 829
- Kan?t: `must_change_password=***MASKED***"must_change_password")),`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `app\admin\routes.py`
- Sat?r: 923
- Kan?t: `initial_password=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `app\communication\announcements_routes.py`
- Sat?r: 111
- Kan?t: `submit_token=***MASKED***"announcement_send", scope=str(current_user.id))`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `app\communication\announcements_routes.py`
- Sat?r: 132
- Kan?t: `submit_token=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `app\communication\announcement_popup_routes.py`
- Sat?r: 51
- Kan?t: `form_token=***MASKED***"announcement_popup_form", scope=str(current_user.id))`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `app\communication\announcement_popup_routes.py`
- Sat?r: 73
- Kan?t: `return f"form_token=***MASKED*** or 'anonymous'}"`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `app\communication\announcement_popup_routes.py`
- Sat?r: 85
- Kan?t: `token=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? HARDCODED_SECRET_LIKE_VALUE
- Dosya: `app\communication\announcement_popup_routes.py`
- Sat?r: 87
- Kan?t: `token=***MASKED***`
- ?neri: Secret/token/parola benzeri de?erler env/secret manager ?zerinden y?netilmeli.

### MEDIUM ? CSRF_DISABLED_OR_EXEMPT
- Dosya: `app\communication\announcement_popup_routes.py`
- Sat?r: 380
- Kan?t: `@csrf.exempt`
- ?neri: CSRF muafiyetleri canl? endpointlerde gerek?eli ve s?n?rl? olmal?.

### MEDIUM ? CSRF_DISABLED_OR_EXEMPT
- Dosya: `app\communication\announcement_popup_routes.py`
- Sat?r: 395
- Kan?t: `@csrf.exempt`
- ?neri: CSRF muafiyetleri canl? endpointlerde gerek?eli ve s?n?rl? olmal?.
