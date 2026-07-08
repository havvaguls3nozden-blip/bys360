# BYS360_SCORE_100_QUALITY_GATE_V1 Raporu

- Durum: **PASS**
- Tahmini kalite puanı: **92/100**
- Üretim zamanı: `2026-06-14T10:44:52`
- Proje kökü: `C:\bys360\project`
- Mod: `gate`
- Bulgu sayısı: FAIL=0, WARN=4, PASS=9

## Repo Özeti

- `py_files`: 1446
- `jinja_templates`: 443
- `css_files`: 158
- `js_files`: 90
- `md_files`: 331
- `scripts_files`: 364

## Bulgular

### [WARN] Devasa kaynak dosyaları var

**Kontrol:** `LARGE_SOURCE_FILES`

Bakım maliyeti yüksek dosyalar tespit edildi.

**Kanıt:**

```json
[
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "size_kb": 367.6
  }
]
```

**Öneri:** Devasa dosyaları alan bazlı modüllere bölün; özellikle JS/Python route dosyalarını küçük servis dosyalarına ayırın.

### [WARN] exec()/compile() kullanımı bulundu

**Kontrol:** `PYTHON_EXEC_COMPILE_USAGE`

Dinamik kod yürütme lint, test ve IDE görünürlüğünü zayıflatır; route yükleme için özellikle risklidir.

**Kanıt:**

```json
[
  {
    "path": "app/schema_guard_engine.py",
    "line": 22,
    "preview": "INDEX_COLUMNS_RE = re.compile(r\"\\bON\\s+([a-zA-Z_][a-zA-Z0-9_]*)\\s*\\((.*?)\\)\", re.IGNORECASE | re.DOTALL)"
  },
  {
    "path": "app/schema_guard_engine.py",
    "line": 23,
    "preview": "TABLE_RE = re.compile(r\"(?:ALTER|CREATE TABLE(?: IF NOT EXISTS)?)\\s+([a-zA-Z_][a-zA-Z0-9_]*)\", re.IGNORECASE)"
  },
  {
    "path": "app/schema_guard_engine.py",
    "line": 142,
    "preview": "def _safe_exec(connection, statement: str) -> str:"
  },
  {
    "path": "app/schema_guard_engine.py",
    "line": 167,
    "preview": "applied.append(f\"{repair.table}: {_safe_exec(connection, repair.create_sql)}\")"
  },
  {
    "path": "app/schema_guard_engine.py",
    "line": 187,
    "preview": "applied.append(f\"{repair.table}: {_safe_exec(connection, statement)}\")"
  },
  {
    "path": "app/schema_guard_engine.py",
    "line": 205,
    "preview": "applied.append(f\"{repair.table}: {_safe_exec(connection, statement)}\")"
  },
  {
    "path": "app/schema_guard_engine.py",
    "line": 229,
    "preview": "applied.append(f\"{label}: {_safe_exec(connection, statement)}\")"
  },
  {
    "path": "app/api/mobile/communication_read_routes.py",
    "line": 19,
    "preview": "exec(_COMMUNICATION_READ_ROUTE_SOURCE, route_globals, route_globals)"
  },
  {
    "path": "app/api/mobile/communication_v2_read_routes.py",
    "line": 19,
    "preview": "exec(_COMMUNICATION_V2_READ_ROUTE_SOURCE, route_globals, route_globals)"
  },
  {
    "path": "app/api/mobile/detail_read_routes.py",
    "line": 19,
    "preview": "exec(_DETAIL_READ_ROUTE_SOURCE, route_globals, route_globals)"
  },
  {
    "path": "app/api/mobile/light_read_routes.py",
    "line": 19,
    "preview": "exec(_LIGHT_READ_ROUTE_SOURCE, route_globals, route_globals)"
  },
  {
    "path": "app/api/mobile/performance_read_routes.py",
    "line": 18,
    "preview": "exec(_PERFORMANCE_READ_ROUTE_SOURCE, route_globals, route_globals)"
  },
  {
    "path": "app/api/mobile/support_survey_read_routes.py",
    "line": 19,
    "preview": "exec(_SUPPORT_SURVEY_READ_ROUTE_SOURCE, route_globals, route_globals)"
  },
  {
    "path": "app/api/mobile/utility_routes.py",
    "line": 19,
    "preview": "exec(_UTILITY_ROUTE_SOURCE, route_globals, route_globals)"
  },
  {
    "path": "app/security/headers.py",
    "line": 35,
    "preview": "_SCRIPT_TAG_WITHOUT_NONCE_RE = re.compile(r\"<script\\b(?![^>]*\\bnonce=)\", re.IGNORECASE)"
  },
  {
    "path": "app/security/tckn_crypto.py",
    "line": 21,
    "preview": "_TCKN_RE: Final[re.Pattern[str]] = re.compile(r\"^\\d{11}$\")"
  },
  {
    "path": "app/services/announcement_popup_service.py",
    "line": 81,
    "preview": "VIDEO_ID_RE = re.compile(r\"^[A-Za-z0-9_-]{6,64}$\")"
  },
  {
    "path": "app/services/announcement_popup_service.py",
    "line": 82,
    "preview": "VIMEO_ID_RE = re.compile(r\"^[0-9]{4,32}$\")"
  },
  {
    "path": "app/services/announcement_popup_service.py",
    "line": 83,
    "preview": "DAILYMOTION_ID_RE = re.compile(r\"^[A-Za-z0-9]{4,32}$\")"
  },
  {
    "path": "app/services/live_core_smoke_endpoint_gate.py",
    "line": 22,
    "preview": "ROUTE_RE = re.compile(r\"@[^\\n]*?\\.route\\(\\s*([\\\"'])(?P<path>/[^\\\"']*)\\1\", re.UNICODE)"
  },
  {
    "path": "app/services/live_core_smoke_endpoint_gate.py",
    "line": 23,
    "preview": "URL_FOR_RE = re.compile(r\"url_for\\(\\s*([\\\"'])(?P<endpoint>[^\\\"']+)\\1\", re.UNICODE)"
  },
  {
    "path": "app/services/security_compliance_final_gate.py",
    "line": 164,
    "preview": "def _check_compile(root: Path, files: dict[str, str], findings: list[Finding]) -> None:"
  },
  {
    "path": "app/services/security_compliance_final_gate.py",
    "line": 190,
    "preview": "secret_url = re.compile(r\"postgresql\\+psycopg2://[^\\s'\\\"<>]+:[^\\s'\\\"<>]+@\", re.I)"
  },
  {
    "path": "app/services/security_compliance_final_gate.py",
    "line": 191,
    "preview": "generic_secret = re.compile(r\"(?i)(SECRET_KEY|DATABASE_URL|SQLALCHEMY_DATABASE_URI|MAIL_PASSWORD|TCKN_ENCRYPTION_KEY)\\s*=\\s*['\\\"][^'\\\"]{8,}['\\\"]\")"
  },
  {
    "path": "app/services/security_compliance_final_gate.py",
    "line": 374,
    "preview": "_check_compile(root, files, findings)"
  },
  {
    "path": "app/services/ai/excel_preview.py",
    "line": 87,
    "preview": "_EMAIL_RE = re.compile(r\"^[^@\\s]{2,}@[^@\\s]+\\.[^@\\s]+$\", re.IGNORECASE)"
  },
  {
    "path": "app/services/ai/excel_preview.py",
    "line": 88,
    "preview": "_TCKN_RE = re.compile(r\"(?<!\\d)\\d{11}(?!\\d)\")"
  },
  {
    "path": "app/services/ai/excel_preview.py",
    "line": 89,
    "preview": "_PHONE_RE = re.compile(r\"(?<!\\d)(?:\\+?90)?0?5\\d{9}(?!\\d)\")"
  },
  {
    "path": "app/services/ai/excel_preview.py",
    "line": 90,
    "preview": "_IBAN_RE = re.compile(r\"\\bTR\\d{2}[A-Z0-9]{5,}\\b\", re.IGNORECASE)"
  },
  {
    "path": "app/services/ai/excel_preview.py",
    "line": 91,
    "preview": "_LONG_DIGIT_RE = re.co
... (kısaltıldı)
```

**Öneri:** Route/string yükleme kalıntılarını normal Python modüllerine taşıyın. Gerekli teknik kullanım varsa allowlist'e gerekçeli ekleyin.

### [WARN] Script/doküman kalabalığı yüksek

**Kontrol:** `REPO_SCRIPT_DOC_BLOAT`

Tek seferlik script veya dağınık dokümantasyon sayısı yüksek görünüyor.

**Kanıt:**

```json
{
  "scripts_files": 364,
  "md_files": 331
}
```

**Öneri:** Yeni tek seferlik SAFE/HOTFIX üretimini durdurun; kalıcı gate ve merkezi doküman yaklaşımına geçin.

### [WARN] TCKN şifreleme kullanımı için aday kod bulundu

**Kontrol:** `TCKN_ENCRYPTION_CONFIG_WITH_USAGE`

Anahtar ve encrypt/decrypt benzeri kullanım var; gerçek model alanlarına bağlandığı manuel doğrulanmalı.

**Kanıt:**

```json
{
  "config_hits": [
    {
      "path": "config.py",
      "line": 325,
      "preview": "TCKN_ENCRYPTION_KEY = os.getenv('TCKN_ENCRYPTION_KEY', '').strip()"
    },
    {
      "path": "app/config/release_manifest.py",
      "line": 72,
      "preview": "\"TCKN_ENCRYPTION_KEY\","
    },
    {
      "path": "app/security/audit.py",
      "line": 105,
      "preview": "if prod_like and not str(config.get('TCKN_ENCRYPTION_KEY', '') or '').strip():"
    },
    {
      "path": "app/security/audit.py",
      "line": 109,
      "preview": "message='TCKN_ENCRYPTION_KEY tanimli degil.',"
    },
    {
      "path": "app/security/startup_audit.py",
      "line": 80,
      "preview": "if not app.config.get(\"TCKN_ENCRYPTION_KEY\"):"
    },
    {
      "path": "app/security/startup_audit.py",
      "line": 81,
      "preview": "app.logger.warning(\"TCKN_ENCRYPTION_KEY tanimli degil; hassas kimlik verisi modulu acik kalacaksa canliya cikmadan once anahtar set edin.\")"
    },
    {
      "path": "app/security/tckn_crypto.py",
      "line": 44,
      "preview": "raise TcknCryptoError(\"TCKN_ENCRYPTION_KEY tanımlı değil.\")"
    },
    {
      "path": "app/security/tckn_crypto.py",
      "line": 65,
      "preview": "key = current_app.config.get(\"TCKN_ENCRYPTION_KEY\")"
    },
    {
      "path": "app/security/tckn_crypto.py",
      "line": 70,
      "preview": "return os.getenv(\"TCKN_ENCRYPTION_KEY\", \"\").strip()"
    },
    {
      "path": "app/services/security_compliance_final_gate.py",
      "line": 191,
      "preview": "generic_secret = re.compile(r\"(?i)(SECRET_KEY|DATABASE_URL|SQLALCHEMY_DATABASE_URI|MAIL_PASSWORD|TCKN_ENCRYPTION_KEY)\\s*=\\s*['\\\"][^'\\\"]{8,}['\\\"]\")"
    }
  ],
  "usage_hits": [
    {
      "path": "app/security/tckn_crypto.py",
      "line": 72,
      "preview": "def encrypt_tckn(value: str | int | None, *, key: str | None = None) -> str:"
    }
  ]
}
```

**Öneri:** Unit test ekleyin: düz TCKN değeri DB'ye açık yazılmamalı; yetkili okuma maskeli/çözülmüş kurala göre çalışmalı.

### [INFO] Repo şekil özeti üretildi

**Kontrol:** `REPO_SHAPE_SUMMARY`

Kaynak dosya sayıları rapora eklendi.

**Kanıt:**

```json
{
  "py_files": 1446,
  "jinja_templates": 443,
  "css_files": 158,
  "js_files": 90,
  "md_files": 331,
  "scripts_files": 364
}
```

### [PASS] Android imzalama örnek dosyası placeholder görünüyor — `mobile_flutter/bys360_mobile_native/android/key.properties.example`

**Kontrol:** `ANDROID_SIGNING_EXAMPLE_SECRET`

key.properties.example içinde gerçek parola gibi görünen değer bulunmadı.

### [PASS] Flask URL map çift route kontrolü temiz

**Kontrol:** `APP_FACTORY_DUPLICATE_RULES`

Aynı endpoint + path + method kombinasyonu tekrar etmiyor.

**Kanıt:**

```json
{
  "rules": 933
}
```

### [PASS] Geniş except blokları bulundu

**Kontrol:** `BROAD_EXCEPT_COUNT`

Toplam 2004 adet except Exception / bare except pattern'i bulundu.

**Kanıt:**

```json
{
  "count": 2004,
  "sample": [
    {
      "path": "app/error_handlers.py",
      "line": 24,
      "preview": "except Exception:"
    },
    {
      "path": "app/error_handlers.py",
      "line": 58,
      "preview": "except Exception:"
    },
    {
      "path": "app/error_handlers.py",
      "line": 103,
      "preview": "except Exception:"
    },
    {
      "path": "app/error_handlers.py",
      "line": 116,
      "preview": "except Exception:"
    },
    {
      "path": "app/error_handlers.py",
      "line": 129,
      "preview": "except Exception:"
    },
    {
      "path": "app/error_handlers.py",
      "line": 150,
      "preview": "except Exception:"
    },
    {
      "path": "app/error_handlers.py",
      "line": 170,
      "preview": "except Exception:"
    },
    {
      "path": "app/error_handlers.py",
      "line": 173,
      "preview": "except Exception:"
    },
    {
      "path": "app/error_handlers.py",
      "line": 179,
      "preview": "except Exception:"
    },
    {
      "path": "app/error_handlers.py",
      "line": 194,
      "preview": "except Exception:"
    },
    {
      "path": "app/error_handlers.py",
      "line": 199,
      "preview": "except Exception:"
    },
    {
      "path": "app/error_handlers.py",
      "line": 208,
      "preview": "except Exception:"
    },
    {
      "path": "app/error_handlers.py",
      "line": 217,
      "preview": "except Exception:"
    },
    {
      "path": "app/error_support.py",
      "line": 21,
      "preview": "except Exception:  # pragma: no cover - rollback'in de patlamasi zor ama can sıkıcı."
    },
    {
      "path": "app/live_scope.py",
      "line": 336,
      "preview": "except Exception:"
    },
    {
      "path": "app/live_scope.py",
      "line": 468,
      "preview": "except Exception:"
    },
    {
      "path": "app/live_scope.py",
      "line": 489,
      "preview": "except Exception:"
    },
    {
      "path": "app/live_scope.py",
      "line": 492,
      "preview": "except Exception:"
    },
    {
      "path": "app/live_scope.py",
      "line": 513,
      "preview": "except Exception:"
    },
    {
      "path": "app/live_scope.py",
      "line": 516,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 423,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 467,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 480,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 493,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 520,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 525,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 531,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 576,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 588,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 643,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 662,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 683,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 713,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 721,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 749,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 810,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 824,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 848,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 887,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 910,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 947,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 971,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 1161,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 1174,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 1250,
      "preview": "except Exception:"
    },
    {
      "path": "app/menu_registry.py",
      "line": 1259,
      "preview": "except E
... (kısaltıldı)
```

**Öneri:** Sessiz hata yutma yerine spesifik exception yakalayın ve log/geri bildirim standardını uygulayın.

### [PASS] Saha raporunda işaretlenen eski bağımlılık pinleri görünmüyor — `requirements.txt`

**Kontrol:** `DEPENDENCY_REPORT_FLAGGED_PINS`

requirements.txt, rapordaki riskli pinlerle birebir eşleşmiyor.

### [PASS] Çift endpoint testi aktif görünüyor

**Kontrol:** `DUPLICATE_ENDPOINT_TEST_ACTIVE`

Duplicate endpoint testi tests altında bulundu ve skip/env koşulu arkasında görünmüyor.

**Kanıt:**

```json
[
  {
    "path": "tests/integration/test_http_db_core_flows.py",
    "line": 67
  },
  {
    "path": "tests/quality/test_app_factory_registers_routes_without_duplicate_endpoints.py",
    "line": 16
  }
]
```

### [PASS] .env git takibinde görünmüyor

**Kontrol:** `ENV_TRACKED_BY_GIT`

git ls-files çıktısında .env/.env.production gibi gerçek ortam dosyası takipli görünmedi.

### [PASS] ruff bulguları var

**Kontrol:** `RUFF_CHECK`

ruff check app toplam 7522 bulgu döndürdü. F821=0, F403=0.

**Kanıt:**

```json
{
  "returncode": 1,
  "count": 7522,
  "F821": 0,
  "F403": 0,
  "stderr_tail": ""
}
```

**Öneri:** Önce F821 ve wildcard importları sıfırlayın; sonra ruff backlog'u paket paket azaltın.

### [PASS] Secret pattern taraması temiz

**Kontrol:** `SECRET_PATTERN_SCAN`

Taranan konfigürasyon dosyalarında bariz secret pattern bulunmadı.

### [PASS] Wildcard import bulunmadı

**Kontrol:** `WILDCARD_IMPORTS`

Python AST taramasında wildcard import görünmedi.

**Kanıt:**

```json
{
  "parse_errors": 55
}
```
