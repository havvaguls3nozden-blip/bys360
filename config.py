import logging
import ipaddress
import os
import secrets
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
logger = logging.getLogger(__name__)

# BYS360_CANLI_SAGLAMLASTIRMA_FAZ1_8_DOTENV_FALLBACK_V2
try:
    from dotenv import load_dotenv  # type: ignore
except ModuleNotFoundError:
    def load_dotenv(dotenv_path=None, override: bool = False, **_kwargs):
        """python-dotenv yoksa uygulamayı düşürmeyen minimum .env okuyucu."""
        path = dotenv_path or ".env"
        try:
            with open(path, "r", encoding="utf-8-sig") as handle:
                lines = handle.readlines()
        except FileNotFoundError:
            return False
        except OSError:
            return False

        loaded = False
        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not key:
                continue
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            if override or key not in os.environ:
                os.environ[key] = value
                loaded = True
        return loaded


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DOTENV_PATH = Path(BASE_DIR) / '.env'
load_dotenv(DOTENV_PATH)


def str_to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def _host_is_local_or_private(hostname: str | None) -> bool:
    host = (hostname or '').strip().lower()
    if not host:
        return False
    if host in {'localhost', '127.0.0.1', '::1'}:
        return True
    try:
        ip_value = ipaddress.ip_address(host)
    except ValueError:
        return False
    return bool(ip_value.is_private or ip_value.is_loopback or ip_value.is_link_local)


def _default_secure_cookie(app_env: str, app_base_url: str) -> bool:
    parsed = urlparse((app_base_url or '').strip())
    scheme = (parsed.scheme or '').lower()
    hostname = parsed.hostname
    if scheme and scheme != 'https':
        return False
    if _host_is_local_or_private(hostname):
        return False
    return app_env in {'production', 'staging'}


def _resolve_secure_cookie(raw_value: str | None, app_env: str, app_base_url: str) -> bool:
    parsed = urlparse((app_base_url or '').strip())
    scheme = (parsed.scheme or '').lower()
    hostname = parsed.hostname
    if (scheme and scheme != 'https') or _host_is_local_or_private(hostname):
        return False
    return str_to_bool(raw_value, _default_secure_cookie(app_env, app_base_url))


def _coerce_positive_int(raw_value: str | None, fallback: int) -> int:
    try:
        value = int(str(raw_value or '').strip())
    except (TypeError, ValueError):
        return fallback
    return value if value > 0 else fallback


def _coerce_float(raw_value: str | None, fallback: float) -> float:
    try:
        return float(str(raw_value or '').strip())
    except (TypeError, ValueError):
        return fallback


def _append_db_sslmode(db_url: str, app_env: str) -> str:
    """Production/staging PostgreSQL baglantilarinda SSL'i guvenli varsayilan yap.

    Eski paketlerde DATABASE_URL icinde SSL kapalı bağlantı parametresi kalabildigi icin sadece
    eksik degeri tamamlamak yeterli degildi. Canli/staging ortaminda uzak
    PostgreSQL kullaniliyorsa `disable` degeri, bilincli olarak
    DB_ALLOW_SSL_DISABLE=true verilmedikce `require` ile ezilir.
    """
    raw = (db_url or '').strip()
    if not raw:
        return raw
    parsed = urlparse(raw)
    scheme = (parsed.scheme or '').lower()
    if not scheme.startswith('postgres'):
        return raw
    if app_env not in {'production', 'staging'}:
        return raw
    if _host_is_local_or_private(parsed.hostname):
        return raw

    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    requested_sslmode = (os.getenv('DB_SSLMODE', 'require').strip() or 'require').lower()
    allow_disable = str_to_bool(os.getenv('DB_ALLOW_SSL_DISABLE'), False)
    current_sslmode = (query.get('sslmode') or '').strip().lower()

    if current_sslmode in {'', 'disable'} and not allow_disable:
        query['sslmode'] = requested_sslmode
    elif current_sslmode == 'disable' and allow_disable:
        query['sslmode'] = 'disable'
    return urlunparse(parsed._replace(query=urlencode(query)))

def _normalize_runtime_redis_url(raw_url: str | None, app_env: str) -> tuple[str, str | None]:
    """Bare-metal canlıda docker hostname redis://redis:6379 ayarını sessizce bozmasın.

    Docker/compose kullanılıyorsa BYS360_DEPLOYMENT_MODE=docker verilerek bu hostname
    bilinçli biçimde korunabilir. Aksi halde çözümlenemeyen docker hostname'i güvenli
    şekilde file/memory fallback'e düşürülür.
    """
    try:
        from app.services.redis_config_guard import sanitize_redis_url
        return sanitize_redis_url(
            raw_url,
            app_env=app_env,
            deployment_mode=os.getenv('BYS360_DEPLOYMENT_MODE', ''),
        )
    except Exception as exc:
        logger.exception("BYS360 critical exception captured in config.py", exc_info=exc)
        return (raw_url or '').strip(), None


def _is_sqlite_url(db_url: str) -> bool:
    return (db_url or '').strip().lower().startswith('sqlite:')


class Config:
    APP_ENV = os.getenv('APP_ENV', 'development').strip().lower()
    APP_BASE_URL = os.getenv('APP_BASE_URL', 'http://127.0.0.1:8000').strip()

    DOTENV_PATH = str(DOTENV_PATH)
    REQUIRE_DOTENV_FILE = str_to_bool(os.getenv('REQUIRE_DOTENV_FILE'), APP_ENV in {'production', 'staging'})
    STRICT_ENV_VALIDATION = str_to_bool(os.getenv('STRICT_ENV_VALIDATION'), APP_ENV in {'production', 'staging'})

    # BYS360_MAINTENANCE_10_SHORT_TERM_SECRET_KEY_HARDENING
    # Production/staging ortamı güçlü SECRET_KEY olmadan başlamamalıdır.
    # Development ortamında sabit anahtar yerine her süreçte geçici anahtar üretilir.
    _raw_secret_key = (os.getenv("SECRET_KEY") or "").strip()
    _secret_placeholder_values = {
        '',
        'CHANGE_ME',
        'change-me',
        'changeme',
        'bys360-dev-session-key-change-me-before-production',
    }
    _secret_is_strong = bool(_raw_secret_key and _raw_secret_key not in _secret_placeholder_values and len(_raw_secret_key) >= 32)
    if _secret_is_strong:
        SECRET_KEY = _raw_secret_key
    elif APP_ENV in {'production', 'staging'}:
        raise RuntimeError('Production/staging ortamında güçlü ve benzersiz SECRET_KEY zorunludur.')
    else:
        SECRET_KEY = os.environ.get("FLASK_SECRET") or "bys360-local-dev-only-secret"


    _raw_database_url = (os.getenv("DATABASE_URL") or "").strip() or 'sqlite:///:memory:'
    SQLALCHEMY_DATABASE_URI = _append_db_sslmode(_raw_database_url, APP_ENV)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    _is_prod_like = APP_ENV in {'production', 'staging'}
    _default_pool_size = 25 if _is_prod_like else 10
    _default_max_overflow = 15 if _is_prod_like else 20
    _default_pool_recycle = 1800 if _is_prod_like else 900
    _default_pool_timeout = 30

    if _is_sqlite_url(SQLALCHEMY_DATABASE_URI):
        SQLALCHEMY_ENGINE_OPTIONS = {}
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': str_to_bool(os.getenv('DB_POOL_PRE_PING'), True),
            'pool_recycle': _coerce_positive_int(os.getenv('DB_POOL_RECYCLE'), _default_pool_recycle),
            'pool_size': _coerce_positive_int(os.getenv('DB_POOL_SIZE'), _default_pool_size),
            'max_overflow': _coerce_positive_int(os.getenv('DB_MAX_OVERFLOW'), _default_max_overflow),
            'pool_timeout': _coerce_positive_int(os.getenv('DB_POOL_TIMEOUT'), _default_pool_timeout),
            'pool_use_lifo': str_to_bool(os.getenv('DB_POOL_USE_LIFO'), True),
        }

    # BYS360_MAINTENANCE_ROADMAP_PHASE4_SCALABILITY_PERFORMANCE_CONFIG
    # Faz 4: cache, DB pool ve bildirim polling yükünü azaltma ayarları.
    CACHE_DEFAULT_TTL = _coerce_positive_int(os.getenv('CACHE_DEFAULT_TTL'), 30)
    _raw_runtime_redis_url, RUNTIME_REDIS_CONFIG_WARNING = _normalize_runtime_redis_url(os.getenv('REDIS_URL', ''), APP_ENV)
    _raw_cache_redis_url, CACHE_REDIS_CONFIG_WARNING = _normalize_runtime_redis_url(os.getenv('CACHE_REDIS_URL', _raw_runtime_redis_url), APP_ENV)
    RUNTIME_CACHE_BACKEND = os.getenv('RUNTIME_CACHE_BACKEND', 'redis' if _raw_runtime_redis_url else 'memory').strip().lower() or 'memory'
    CACHE_REDIS_URL = _raw_cache_redis_url
    NOTIFICATION_UNREAD_CACHE_TTL = _coerce_positive_int(os.getenv('NOTIFICATION_UNREAD_CACHE_TTL'), 30)
    PERFORMANCE_REPORT_CACHE_TTL = _coerce_positive_int(os.getenv('PERFORMANCE_REPORT_CACHE_TTL'), 60)
    DASHBOARD_CACHE_TTL = _coerce_positive_int(os.getenv('DASHBOARD_CACHE_TTL'), 30)

    PUBLICATION_UPLOAD_MAX_CONTENT_LENGTH = int(os.getenv('PUBLICATION_UPLOAD_MAX_CONTENT_LENGTH', 150 * 1024 * 1024))
    EDUCATION_EBOOK_MAX_CONTENT_LENGTH = int(os.getenv('EDUCATION_EBOOK_MAX_CONTENT_LENGTH', 150 * 1024 * 1024))
    _base_max_content_length = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    MAX_CONTENT_LENGTH = max(_base_max_content_length, PUBLICATION_UPLOAD_MAX_CONTENT_LENGTH, EDUCATION_EBOOK_MAX_CONTENT_LENGTH)

    # BYS360_MAINTENANCE_ROADMAP_PHASE2_SECURITY_HARDENING_V1
    ALLOWED_UPLOAD_EXTENSIONS = os.getenv('ALLOWED_UPLOAD_EXTENSIONS', 'pdf,png,jpg,jpeg,gif,webp,docx,xlsx,pptx,zip,csv,txt').strip() or 'pdf,png,jpg,jpeg,gif,webp,docx,xlsx,pptx,zip,csv,txt'
    UPLOAD_MAX_FILENAME_LENGTH = _coerce_positive_int(os.getenv('UPLOAD_MAX_FILENAME_LENGTH'), 180)
    UPLOAD_STRICT_MIME_VALIDATION = str_to_bool(os.getenv('UPLOAD_STRICT_MIME_VALIDATION'), True)

    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'app', 'static', 'uploads'))
    REPORT_FOLDER = os.getenv('REPORT_FOLDER', os.path.join(BASE_DIR, 'reports'))
    LOG_FOLDER = os.getenv('LOG_FOLDER', os.path.join(BASE_DIR, 'logs'))
    PDF_EXPORT_MAX_ROWS_INLINE = _coerce_positive_int(os.getenv('PDF_EXPORT_MAX_ROWS_INLINE'), 250)

    SESSION_COOKIE_HTTPONLY = str_to_bool(os.getenv('SESSION_COOKIE_HTTPONLY'), True)
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    SESSION_COOKIE_SECURE = _resolve_secure_cookie(os.getenv('SESSION_COOKIE_SECURE'), APP_ENV, APP_BASE_URL)

    REMEMBER_COOKIE_HTTPONLY = str_to_bool(os.getenv('REMEMBER_COOKIE_HTTPONLY'), True)
    REMEMBER_COOKIE_SECURE = _resolve_secure_cookie(os.getenv('REMEMBER_COOKIE_SECURE'), APP_ENV, APP_BASE_URL)

    WTF_CSRF_TIME_LIMIT = int(os.getenv('WTF_CSRF_TIME_LIMIT', 3600))
    SESSION_REFRESH_EACH_REQUEST = str_to_bool(os.getenv('SESSION_REFRESH_EACH_REQUEST'), True)
    PERMANENT_SESSION_LIFETIME_MINUTES = int(os.getenv('PERMANENT_SESSION_LIFETIME_MINUTES', 30))

    DEFAULT_FIRST_LOGIN_PASSWORD = os.getenv('DEFAULT_FIRST_LOGIN_PASSWORD', '').strip()

    REQUEST_GUARD_ENABLED = str_to_bool(os.getenv('REQUEST_GUARD_ENABLED'), True)
    ROOT_POST_BURST_LIMIT = _coerce_positive_int(os.getenv('ROOT_POST_BURST_LIMIT'), 8)
    ROOT_POST_WINDOW_SECONDS = _coerce_positive_int(os.getenv('ROOT_POST_WINDOW_SECONDS'), 60)
    SUSPICIOUS_PROBE_BURST_LIMIT = _coerce_positive_int(os.getenv('SUSPICIOUS_PROBE_BURST_LIMIT'), 20)
    SUSPICIOUS_PROBE_WINDOW_SECONDS = _coerce_positive_int(os.getenv('SUSPICIOUS_PROBE_WINDOW_SECONDS'), 120)
    SECURITY_LOG_COOLDOWN_SECONDS = _coerce_positive_int(os.getenv('SECURITY_LOG_COOLDOWN_SECONDS'), 300)
    REDIS_URL, REDIS_CONFIG_WARNING = _normalize_runtime_redis_url(os.getenv('REDIS_URL', ''), APP_ENV)
    CACHE_REDIS_URL, CACHE_REDIS_CONFIG_WARNING = _normalize_runtime_redis_url(os.getenv('CACHE_REDIS_URL', REDIS_URL), APP_ENV)
    CACHE_BACKEND = os.getenv('CACHE_BACKEND', 'redis' if CACHE_REDIS_URL else 'file').strip().lower() or ('redis' if CACHE_REDIS_URL else 'file')
    CACHE_KEY_PREFIX = os.getenv('CACHE_KEY_PREFIX', 'bys360').strip() or 'bys360'
    CACHE_FILE = os.getenv('CACHE_FILE', '').strip()
    REDIS_CONNECT_TIMEOUT = _coerce_float(os.getenv('REDIS_CONNECT_TIMEOUT'), 1.0)
    REDIS_SOCKET_TIMEOUT = _coerce_float(os.getenv('REDIS_SOCKET_TIMEOUT'), 1.0)

    SECURITY_RATE_LIMIT_BACKEND = os.getenv('SECURITY_RATE_LIMIT_BACKEND', 'redis' if REDIS_URL else 'file').strip().lower() or ('redis' if REDIS_URL else 'file')
    SECURITY_RATE_LIMIT_SHARED = str_to_bool(os.getenv('SECURITY_RATE_LIMIT_SHARED'), True)
    SECURITY_RATE_LIMIT_FILE = os.getenv('SECURITY_RATE_LIMIT_FILE', '').strip()
    SECURITY_RATE_LIMIT_REDIS_URL, SECURITY_RATE_LIMIT_REDIS_CONFIG_WARNING = _normalize_runtime_redis_url(os.getenv('SECURITY_RATE_LIMIT_REDIS_URL', REDIS_URL), APP_ENV)

    LOGIN_THROTTLE_ENABLED = str_to_bool(os.getenv('LOGIN_THROTTLE_ENABLED'), True)
    LOGIN_IP_MAX_ATTEMPTS = _coerce_positive_int(os.getenv('LOGIN_IP_MAX_ATTEMPTS'), 12)
    LOGIN_IDENTITY_MAX_ATTEMPTS = _coerce_positive_int(os.getenv('LOGIN_IDENTITY_MAX_ATTEMPTS'), 6)
    LOGIN_LOCKOUT_MINUTES = _coerce_positive_int(os.getenv('LOGIN_LOCKOUT_MINUTES'), 15)

    FEEDBACK_PULSE_ANALYTICS_CACHE_ENABLED = str_to_bool(os.getenv('FEEDBACK_PULSE_ANALYTICS_CACHE_ENABLED'), True)
    FEEDBACK_PULSE_ANALYTICS_CACHE_TTL_SECONDS = _coerce_positive_int(os.getenv('FEEDBACK_PULSE_ANALYTICS_CACHE_TTL_SECONDS'), 60)

    LOGIN_CAPTCHA_THRESHOLD = int(os.getenv('LOGIN_CAPTCHA_THRESHOLD', 3))
    LOGIN_FAILURE_WINDOW_MINUTES = int(os.getenv('LOGIN_FAILURE_WINDOW_MINUTES', 30))
    LOGIN_FORCE_CAPTCHA_FOR_UNKNOWN_USER = str_to_bool(os.getenv('LOGIN_FORCE_CAPTCHA_FOR_UNKNOWN_USER'), True)
    LOGIN_GENERIC_ERROR_MESSAGE = (
        os.getenv('LOGIN_GENERIC_ERROR_MESSAGE', 'Giriş başarısız. Bilgilerinizi kontrol edip tekrar deneyin.').strip()
        or 'Giriş başarısız. Bilgilerinizi kontrol edip tekrar deneyin.'
    )

    AUTO_REPAIR_SCHEMA = str_to_bool(os.getenv('AUTO_REPAIR_SCHEMA'), False)
    STRICT_SCHEMA_CHECK = str_to_bool(os.getenv('STRICT_SCHEMA_CHECK'), APP_ENV in {'production', 'staging'})

    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').strip().upper() or 'INFO'
    APP_LOG_FILE_MAX_BYTES = _coerce_positive_int(os.getenv('APP_LOG_FILE_MAX_BYTES'), 2_000_000)
    APP_LOG_BACKUP_COUNT = _coerce_positive_int(os.getenv('APP_LOG_BACKUP_COUNT'), 5)
    OPS_LOG_FILE_MAX_BYTES = _coerce_positive_int(os.getenv('OPS_LOG_FILE_MAX_BYTES'), 2_000_000)
    OPS_LOG_BACKUP_COUNT = _coerce_positive_int(os.getenv('OPS_LOG_BACKUP_COUNT'), 5)

    PROXY_FIX_ENABLED = str_to_bool(os.getenv('PROXY_FIX_ENABLED'), APP_ENV in {'production', 'staging'})
    PROXY_FIX_X_FOR = _coerce_positive_int(os.getenv('PROXY_FIX_X_FOR'), 1)
    PROXY_FIX_X_PROTO = _coerce_positive_int(os.getenv('PROXY_FIX_X_PROTO'), 1)
    PROXY_FIX_X_HOST = _coerce_positive_int(os.getenv('PROXY_FIX_X_HOST'), 1)
    PROXY_FIX_X_PORT = _coerce_positive_int(os.getenv('PROXY_FIX_X_PORT'), 1)
    PROXY_FIX_X_PREFIX = _coerce_positive_int(os.getenv('PROXY_FIX_X_PREFIX'), 1)

    WAITRESS_THREADS = _coerce_positive_int(os.getenv('WAITRESS_THREADS'), 12 if _is_prod_like else 4)
    GUNICORN_BIND = os.getenv('GUNICORN_BIND', f"{os.getenv('APP_HOST', '0.0.0.0')}:{os.getenv('APP_PORT', '8000')}").strip() or '0.0.0.0:8000'
    GUNICORN_WORKERS = _coerce_positive_int(os.getenv('GUNICORN_WORKERS'), 3)
    GUNICORN_WORKER_CLASS = os.getenv('GUNICORN_WORKER_CLASS', 'gevent').strip() or 'gevent'
    GUNICORN_TIMEOUT = _coerce_positive_int(os.getenv('GUNICORN_TIMEOUT'), 120)
    GUNICORN_KEEPALIVE = _coerce_positive_int(os.getenv('GUNICORN_KEEPALIVE'), 5)
    GUNICORN_LOG_LEVEL = os.getenv('GUNICORN_LOG_LEVEL', LOG_LEVEL).strip().lower() or 'info'

    TCKN_ENCRYPTION_KEY = os.getenv('TCKN_ENCRYPTION_KEY', '').strip()

    # BYS360_MAINTENANCE_ROADMAP_PHASE2_SECURITY_HARDENING_V1
    SENTRY_DSN = (os.getenv("SENTRY_DSN") or "").strip()
    SENTRY_ENVIRONMENT = os.getenv('SENTRY_ENVIRONMENT', APP_ENV).strip() or APP_ENV
    SENTRY_RELEASE = os.getenv('SENTRY_RELEASE', '').strip()
    SENTRY_TRACES_SAMPLE_RATE = _coerce_float(os.getenv('SENTRY_TRACES_SAMPLE_RATE'), 0.1)
    SENTRY_PROFILES_SAMPLE_RATE = _coerce_float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE'), 0.0)
    SENTRY_SEND_DEFAULT_PII = str_to_bool(os.getenv('SENTRY_SEND_DEFAULT_PII'), False)
    SENTRY_REQUIRED_IN_PRODUCTION = str_to_bool(os.getenv('SENTRY_REQUIRED_IN_PRODUCTION'), False)

    MAINTENANCE_MODE = str_to_bool(os.getenv('MAINTENANCE_MODE'), False)
    MAINTENANCE_MESSAGE = os.getenv('MAINTENANCE_MESSAGE', 'Sistem şu anda planlı bakım modunda. Lütfen kısa süre sonra tekrar deneyin.').strip()
    SLOW_REQUEST_THRESHOLD_MS = int(os.getenv('SLOW_REQUEST_THRESHOLD_MS', 1000))

    CSP_ENABLED = str_to_bool(os.getenv('CSP_ENABLED'), True)
    # BYS360_MAINTENANCE_10_SHORT_TERM_CSP_ENFORCE_DEFAULT
    # Geliştirmede raporlama, production/staging ortamında aksi belirtilmezse enforce.
    CSP_REPORT_ONLY = str_to_bool(os.getenv('CSP_REPORT_ONLY'), APP_ENV not in {'production', 'staging'})
    CSP_POLICY = os.getenv('CSP_POLICY', '').strip()
    CSP_NONCE_ENABLED = str_to_bool(os.getenv('CSP_NONCE_ENABLED'), APP_ENV in {'production', 'staging'})
    CSP_ALLOW_UNSAFE_INLINE_SCRIPT = str_to_bool(os.getenv('CSP_ALLOW_UNSAFE_INLINE_SCRIPT'), False)
    CSP_DEFAULT_SRC = os.getenv('CSP_DEFAULT_SRC', "'self'").strip() or "'self'"
    CSP_BASE_URI = os.getenv('CSP_BASE_URI', "'self'").strip() or "'self'"
    CSP_FORM_ACTION = os.getenv('CSP_FORM_ACTION', "'self'").strip() or "'self'"
    CSP_FRAME_ANCESTORS = os.getenv('CSP_FRAME_ANCESTORS', "'self'").strip() or "'self'"
    CSP_IMG_SRC = os.getenv('CSP_IMG_SRC', "'self' data: blob: https:").strip() or "'self' data: blob: https:"
    CSP_STYLE_SRC = os.getenv('CSP_STYLE_SRC', "'self' 'unsafe-inline' https:").strip() or "'self' 'unsafe-inline' https:"
    # BYS360_P0_SECURITY_OBSERVABILITY_V1: script tarafinda unsafe-inline varsayilan kapali; nonce uygulanir.
    CSP_SCRIPT_SRC = os.getenv('CSP_SCRIPT_SRC', "'self' https:").strip() or "'self' https:"
    CSP_FONT_SRC = os.getenv('CSP_FONT_SRC', "'self' data: https:").strip() or "'self' data: https:"
    CSP_CONNECT_SRC = os.getenv('CSP_CONNECT_SRC', "'self' https:").strip() or "'self' https:"
    CSP_OBJECT_SRC = os.getenv('CSP_OBJECT_SRC', "'none'").strip() or "'none'"
    HSTS_POLICY = os.getenv('HSTS_POLICY', 'max-age=31536000; includeSubDomains').strip() or 'max-age=31536000; includeSubDomains'
    REFERRER_POLICY = os.getenv('REFERRER_POLICY', 'strict-origin-when-cross-origin').strip() or 'strict-origin-when-cross-origin'
    PERMISSIONS_POLICY = os.getenv('PERMISSIONS_POLICY', 'geolocation=(), microphone=(), camera=()').strip() or 'geolocation=(), microphone=(), camera=()'
    CACHE_CONTROL_POLICY = os.getenv('CACHE_CONTROL_POLICY', 'no-store').strip() or 'no-store'
    CROSS_ORIGIN_OPENER_POLICY = os.getenv('CROSS_ORIGIN_OPENER_POLICY', 'same-origin').strip() or 'same-origin'
    CROSS_ORIGIN_RESOURCE_POLICY = os.getenv('CROSS_ORIGIN_RESOURCE_POLICY', 'same-origin').strip() or 'same-origin'
    TCKN_ALLOWED_ROLES = tuple(item.strip() for item in os.getenv('TCKN_ALLOWED_ROLES', 'admin,baskan,baskan_yardimcisi,grup_baskani,koordinator').split(',') if item.strip())

    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.office365.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    ALLOWED_EMAIL_DOMAINS = tuple(item.strip().lower() for item in os.getenv('ALLOWED_EMAIL_DOMAINS', 'ktb.gov.tr').split(',') if item.strip()) or ('ktb.gov.tr',)
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', '')

    AI_ENABLED = str_to_bool(os.getenv('AI_ENABLED'), True)
    AI_PROVIDER_MODE = os.getenv('AI_PROVIDER_MODE', 'stub').strip().lower() or 'stub'
    AI_PROVIDER_NAME = os.getenv('AI_PROVIDER_NAME', 'internal_stub_plus').strip() or 'internal_stub_plus'
    AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'bys360-ai-stub-v2').strip() or 'bys360-ai-stub-v2'
    AI_BASE_URL = os.getenv('AI_BASE_URL', '').strip().rstrip('/')
    AI_API_KEY = os.getenv('AI_API_KEY', '').strip()
    AI_REQUEST_PATH = os.getenv('AI_REQUEST_PATH', '/chat/completions').strip() or '/chat/completions'
