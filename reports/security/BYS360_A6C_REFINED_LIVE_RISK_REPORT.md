# BYS360 A?ama 6C G?r?lt?s?z Canl? Risk Raporu

Tarih: 2026-06-12T13:11:30

## ?zet

- Toplam ham bulgu: 883
- Ger?ek aksiyon bulgusu: 262
- Referans/?rnek/yorum/test g?r?lt?s?: 621
- Actionable High: 102
- Actionable Medium: 160

## Ger?ek Aksiyon Bulgu Tipleri

- SQLITE_REFERENCE: 128
- DEFAULT_PASSWORD_LITERAL: 68
- SECRET_ASSIGNMENT: 21
- CSP_UNSAFE_INLINE_OR_EVAL: 19
- CSRF_DISABLED_OR_EXEMPT: 11
- DB_SSL_DISABLED: 6
- SENTRY_EMPTY_OR_PLACEHOLDER: 5
- DEBUG_ENABLED: 2
- ENV_FILE_PRESENT: 1
- DATABASE_FILE_PRESENT: 1

## ?lk 80 Ger?ek Aksiyon Bulgusu

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `.env`
- Sat?r: 2
- Kan?t: `DATABASE_URL=sqlite:///C:/bys360/project/instance/bys360_local_dev.sqlite3`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `alembic.ini`
- Sat?r: 16
- Kan?t: `sqlalchemy.url = sqlite:///:memory:`

### HIGH ? DEFAULT_PASSWORD_LITERAL
- Dosya: `config.py`
- Sat?r: 171
- Kan?t: `'CHANGE_ME',`

### HIGH ? DEFAULT_PASSWORD_LITERAL
- Dosya: `config.py`
- Sat?r: 173
- Kan?t: `'changeme',`

### MEDIUM ? SECRET_ASSIGNMENT
- Dosya: `config.py`
- Sat?r: 178
- Kan?t: `SECRET_KEY=***MASKED***`

### MEDIUM ? SECRET_ASSIGNMENT
- Dosya: `config.py`
- Sat?r: 182
- Kan?t: `SECRET_KEY=***MASKED*** '').strip() or secrets.token_urlsafe(48)`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `config.py`
- Sat?r: 185
- Kan?t: `_raw_database_url = (os.getenv("DATABASE_URL") or "").strip() or 'sqlite:///:memory:'`

### MEDIUM ? SECRET_ASSIGNMENT
- Dosya: `config.py`
- Sat?r: 246
- Kan?t: `DEFAULT_FIRST_LOGIN_PASSWORD=***MASKED*** '').strip()`

### MEDIUM ? SECRET_ASSIGNMENT
- Dosya: `config.py`
- Sat?r: 310
- Kan?t: `SENTRY_DSN=***MASKED*** or "").strip()`

### HIGH ? CSP_UNSAFE_INLINE_OR_EVAL
- Dosya: `config.py`
- Sat?r: 334
- Kan?t: `CSP_STYLE_SRC = os.getenv('CSP_STYLE_SRC', "'self' 'unsafe-inline' https:").strip() or "'self' 'unsafe-inline' https:"`

### MEDIUM ? SECRET_ASSIGNMENT
- Dosya: `config.py`
- Sat?r: 351
- Kan?t: `MAIL_PASSWORD=***MASKED*** '')`

### MEDIUM ? SECRET_ASSIGNMENT
- Dosya: `config.py`
- Sat?r: 361
- Kan?t: `AI_API_KEY=***MASKED*** '').strip()`

### HIGH ? DEFAULT_PASSWORD_LITERAL
- Dosya: `docker-compose.yml`
- Sat?r: 12
- Kan?t: `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-change_me_only_for_local}`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `app\menu_registry_data_sections.py`
- Sat?r: 620
- Kan?t: `"endpoint": "main.db_check",`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `app\menu_registry_data_sections.py`
- Sat?r: 621
- Kan?t: `"active_endpoints": ["main.db_check"],`

### HIGH ? DEFAULT_PASSWORD_LITERAL
- Dosya: `app\startup_checks.py`
- Sat?r: 80
- Kan?t: `if strict_env_validation and (not database_uri or "CHANGE_ME" in database_uri or database_uri == "sqlite:///:memory:"):`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `app\startup_checks.py`
- Sat?r: 80
- Kan?t: `if strict_env_validation and (not database_uri or "CHANGE_ME" in database_uri or database_uri == "sqlite:///:memory:"):`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `migrations\env.py`
- Sat?r: 21
- Kan?t: `return current_app.extensions['migrate'].db.get_engine()`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `migrations\env.py`
- Sat?r: 24
- Kan?t: `return current_app.extensions['migrate'].db.engine`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `migrations\env.py`
- Sat?r: 40
- Kan?t: `target_db = current_app.extensions['migrate'].db`

### HIGH ? DEFAULT_PASSWORD_LITERAL
- Dosya: `scripts\check_bys360_mobile_v2_8_74_android_release_ready_p0.py`
- Sat?r: 88
- Kan?t: `if "YOUR_LOCAL_" in key_text or "CHANGE_ME" in key_text:`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\split_clean_bys360_source_for_upload.ps1`
- Sat?r: 47
- Kan?t: `"*.db",`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\split_clean_bys360_source_for_upload.ps1`
- Sat?r: 48
- Kan?t: `"*.sqlite",`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\split_clean_bys360_source_for_upload.ps1`
- Sat?r: 49
- Kan?t: `"*.sqlite3",`

### MEDIUM ? CSRF_DISABLED_OR_EXEMPT
- Dosya: `app\communication\announcement_popup_routes.py`
- Sat?r: 380
- Kan?t: `@csrf.exempt`

### MEDIUM ? CSRF_DISABLED_OR_EXEMPT
- Dosya: `app\communication\announcement_popup_routes.py`
- Sat?r: 395
- Kan?t: `@csrf.exempt`

### HIGH ? DEFAULT_PASSWORD_LITERAL
- Dosya: `app\core\monitoring.py`
- Sat?r: 16
- Kan?t: `"CHANGE_ME",`

### MEDIUM ? SECRET_ASSIGNMENT
- Dosya: `app\security\audit.py`
- Sat?r: 30
- Kan?t: `secret_key=***MASKED*** '') or '').strip()`

### MEDIUM ? CSRF_DISABLED_OR_EXEMPT
- Dosya: `app\security\audit.py`
- Sat?r: 92
- Kan?t: `code='csrf_disabled',`

### MEDIUM ? SECRET_ASSIGNMENT
- Dosya: `app\security\audit.py`
- Sat?r: 113
- Kan?t: `sentry_dsn=***MASKED*** '') or '').strip().lower()`

### HIGH ? DB_SSL_DISABLED
- Dosya: `app\security\audit.py`
- Sat?r: 131
- Kan?t: `if observability_like and db_uri.startswith('postgres') and 'sslmode=disable' in db_uri:`

### HIGH ? DB_SSL_DISABLED
- Dosya: `app\security\audit.py`
- Sat?r: 135
- Kan?t: `message='PostgreSQL baglantisinda sslmode=disable gorunuyor.',`

### HIGH ? CSP_UNSAFE_INLINE_OR_EVAL
- Dosya: `app\security\audit.py`
- Sat?r: 150
- Kan?t: `if observability_like and csp_enabled and "'unsafe-inline'" in script_src and not _is_truthy(config.get('CSP_ALLOW_UNSAFE_INLINE_SCRIPT', False)):`

### HIGH ? CSP_UNSAFE_INLINE_OR_EVAL
- Dosya: `app\security\audit.py`
- Sat?r: 154
- Kan?t: `message='CSP script-src icinde unsafe-inline var.',`

### HIGH ? CSP_UNSAFE_INLINE_OR_EVAL
- Dosya: `app\security\audit.py`
- Sat?r: 155
- Kan?t: `action='Nonce tabanli CSP kullan ve unsafe-inline script iznini kaldir.',`

### HIGH ? CSP_UNSAFE_INLINE_OR_EVAL
- Dosya: `app\security\csp_nonce.py`
- Sat?r: 61
- Kan?t: `f"style-src 'self' 'nonce-{nonce}' 'unsafe-inline'; "`

### HIGH ? CSP_UNSAFE_INLINE_OR_EVAL
- Dosya: `app\security\headers.py`
- Sat?r: 9
- Kan?t: `- script-src tarafinda unsafe-inline varsayilan kullanilmaz.`

### HIGH ? CSP_UNSAFE_INLINE_OR_EVAL
- Dosya: `app\security\headers.py`
- Sat?r: 25
- Kan?t: `"style-src": "'self' 'unsafe-inline' https:",`

### HIGH ? CSP_UNSAFE_INLINE_OR_EVAL
- Dosya: `app\security\headers.py`
- Sat?r: 67
- Kan?t: `value = _remove_token(value, "'unsafe-inline'")`

### MEDIUM ? SECRET_ASSIGNMENT
- Dosya: `app\security\startup_audit.py`
- Sat?r: 43
- Kan?t: `secret_key=***MASKED*** or "").strip()`

### HIGH ? DEFAULT_PASSWORD_LITERAL
- Dosya: `app\security\startup_audit.py`
- Sat?r: 48
- Kan?t: `if first_login_password in {"123456", "12345678", "password", "admin", "changeme", "CHANGE_ME"}:`

### MEDIUM ? SECRET_ASSIGNMENT
- Dosya: `app\security\startup_audit.py`
- Sat?r: 51
- Kan?t: `sentry_dsn=***MASKED*** or "").strip()`

### HIGH ? DB_SSL_DISABLED
- Dosya: `app\security\startup_audit.py`
- Sat?r: 59
- Kan?t: `security_errors.append("PostgreSQL baglantisinda sslmode=disable canli/staging icin kullanilamaz.")`

### HIGH ? CSP_UNSAFE_INLINE_OR_EVAL
- Dosya: `app\security\startup_audit.py`
- Sat?r: 101
- Kan?t: `if "'unsafe-inline'" in script_src and not bool(app.config.get("CSP_ALLOW_UNSAFE_INLINE_SCRIPT", False)):`

### HIGH ? CSP_UNSAFE_INLINE_OR_EVAL
- Dosya: `app\security\startup_audit.py`
- Sat?r: 102
- Kan?t: `security_errors.append("CSP_SCRIPT_SRC icinde unsafe-inline bulunamaz; nonce tabanli CSP kullanilmalidir.")`

### HIGH ? DEFAULT_PASSWORD_LITERAL
- Dosya: `app\security\__init__.py`
- Sat?r: 205
- Kan?t: `"123456",`

### HIGH ? DEFAULT_PASSWORD_LITERAL
- Dosya: `app\security\__init__.py`
- Sat?r: 206
- Kan?t: `"12345678",`

### HIGH ? DEFAULT_PASSWORD_LITERAL
- Dosya: `app\security\__init__.py`
- Sat?r: 209
- Kan?t: `"changeme",`

### HIGH ? DEFAULT_PASSWORD_LITERAL
- Dosya: `app\security\__init__.py`
- Sat?r: 211
- Kan?t: `"CHANGE_ME",`

### HIGH ? DEFAULT_PASSWORD_LITERAL
- Dosya: `app\services\config_hardening_service.py`
- Sat?r: 26
- Kan?t: `"changeme",`

### MEDIUM ? SECRET_ASSIGNMENT
- Dosya: `app\services\config_hardening_service.py`
- Sat?r: 99
- Kan?t: `secret_key=***MASKED*** "")`

### HIGH ? DEFAULT_PASSWORD_LITERAL
- Dosya: `app\services\message_service.py`
- Sat?r: 112
- Kan?t: `allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-")`

### HIGH ? DEBUG_ENABLED
- Dosya: `app\services\security_compliance_final_gate.py`
- Sat?r: 272
- Kan?t: `_add(findings, "UYARI", "runtime.debug_true", "debug=True izi bulundu", ", ".join(debug_true[:8]))`

### HIGH ? DEBUG_ENABLED
- Dosya: `app\services\security_compliance_final_gate.py`
- Sat?r: 274
- Kan?t: `_add(findings, "OK", "runtime.debug_true", "Çalışma zamanı dosyalarında debug=True izi bulunmadı")`

### HIGH ? DEFAULT_PASSWORD_LITERAL
- Dosya: `app\services\security_hardening_service.py`
- Sat?r: 61
- Kan?t: `"changeme",`

### MEDIUM ? CSRF_DISABLED_OR_EXEMPT
- Dosya: `app\api\mobile\__init__.py`
- Sat?r: 18
- Kan?t: `csrf.exempt(mobile_api_bp)`

### MEDIUM ? CSRF_DISABLED_OR_EXEMPT
- Dosya: `app\api\mobile\__init__.py`
- Sat?r: 31
- Kan?t: `csrf.exempt(mobile_api_bp)`

### MEDIUM ? SECRET_ASSIGNMENT
- Dosya: `app\services\ai\client.py`
- Sat?r: 169
- Kan?t: `api_key=***MASKED*** "") or "").strip()`

### MEDIUM ? SECRET_ASSIGNMENT
- Dosya: `app\services\ai\client.py`
- Sat?r: 174
- Kan?t: `api_key=***MASKED***`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `app\services\ai\excel_preview.py`
- Sat?r: 172
- Kan?t: `"db_write_enabled": self.db_write_enabled,`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `app\services\ai\excel_preview.py`
- Sat?r: 179
- Kan?t: `"db_write_enabled": self.db_write_enabled,`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `app\services\ui_context\__init__.py`
- Sat?r: 2
- Kan?t: `from .db_check import build_db_check_context`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\db\repair_bys360_local_sqlite_schema_bootstrap_v2.py`
- Sat?r: 86
- Kan?t: `return raw in {"", "sqlite:///:memory:", "sqlite://", "sqlite:///:memory"} or raw.endswith(":memory:")`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\db\repair_bys360_local_sqlite_schema_bootstrap_v2.py`
- Sat?r: 92
- Kan?t: `return f"sqlite:///{posix}"`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\db\repair_bys360_local_sqlite_schema_bootstrap_v2.py`
- Sat?r: 102
- Kan?t: `if raw.startswith("sqlite:///"):`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\db\repair_bys360_local_sqlite_schema_bootstrap_v2.py`
- Sat?r: 103
- Kan?t: `value = unquote(raw[len("sqlite:///"):])`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\db\repair_bys360_local_sqlite_schema_bootstrap_v2.py`
- Sat?r: 157
- Kan?t: `patterns = ["*.sqlite", "*.sqlite3", "*.db"]`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\db\repair_bys360_local_sqlite_schema_bootstrap_v2.py`
- Sat?r: 209
- Kan?t: `default_path = root / "instance" / "bys360_local.sqlite"`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\db\repair_bys360_local_sqlite_schema_bootstrap_v2.py`
- Sat?r: 368
- Kan?t: `"Local geliştirme ortamında boş `sqlite:///:memory:` veya yanlış SQLite bağlantısı nedeniyle oluşan `no such table: users` beyaz ekranını düzeltir.",`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\maintenance\bys360_technical_debt_cleanup_safe_v19.py`
- Sat?r: 324
- Kan?t: `elif name.endswith((".sqlite", ".sqlite3", ".db")):`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\maintenance\bys360_technical_debt_cleanup_safe_v19.py`
- Sat?r: 330
- Kan?t: `"has_sqlite_rule": ".sqlite" in gitignore_text or "*.db" in gitignore_text,`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\maintenance\bys360_technical_debt_cleanup_safe_v20.py`
- Sat?r: 323
- Kan?t: `local_dbs = list((project_root / "instance").glob("*.sqlite3")) if (project_root / "instance").exists() else []`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\maintenance\bys360_technical_debt_cleanup_safe_v20.py`
- Sat?r: 332
- Kan?t: `"has_sqlite_rule": "*.sqlite" in text or "*.sqlite3" in text,`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\maintenance\bys360_technical_debt_cleanup_safe_v21.py`
- Sat?r: 323
- Kan?t: `elif name.endswith((".sqlite", ".sqlite3", ".db")):`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\maintenance\bys360_technical_debt_cleanup_safe_v21.py`
- Sat?r: 329
- Kan?t: `"has_sqlite_rule": ".sqlite" in gitignore_text or "*.db" in gitignore_text or ".sqlite3" in gitignore_text,`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\maintenance\bys360_technical_debt_cleanup_safe_v8.py`
- Sat?r: 41
- Kan?t: `LOCAL_DB_EXTS = {".sqlite", ".sqlite3", ".db"}`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\maintenance\bys360_technical_debt_cleanup_safe_v9.py`
- Sat?r: 205
- Kan?t: `local_db_count = len(list((root / "instance").glob("*.sqlite*"))) if (root / "instance").exists() else 0`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\maintenance\bys360_technical_debt_cleanup_safe_v9.py`
- Sat?r: 308
- Kan?t: `"local_dbs": [str(p.relative_to(root)) for p in (root / "instance").glob("*.sqlite*")] if (root / "instance").exists() else [],`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\maintenance\bys360_tech_debt_cleanup_safe_v1.py`
- Sat?r: 109
- Kan?t: `".zip", ".7z", ".rar", ".gz", ".tar", ".exe", ".dll", ".pyd", ".pyc", ".sqlite",`

### MEDIUM ? SQLITE_REFERENCE
- Dosya: `scripts\maintenance\bys360_tech_debt_cleanup_safe_v1.py`
- Sat?r: 110
- Kan?t: `".db", ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mov", ".avi", ".mp3",`
