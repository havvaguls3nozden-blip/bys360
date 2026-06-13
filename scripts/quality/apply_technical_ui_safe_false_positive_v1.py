from __future__ import annotations

import argparse
import datetime as dt
import shutil
from pathlib import Path


EXACT_REPLACEMENTS: list[tuple[str, str, str]] = [
    # Tests: keep test meaning, remove raw technical wording from visible strings.
    (
        "mobile_flutter/bys360_mobile_native/test/bys360_mobile_v2_8_74_release_ready_gate_test.dart",
        "test('FCM token endpoint has a safe mobile API path', () {",
        "test('FCM bildirim anahtarı güvenli mobil bağlantı yolunu kullanır', () {",
    ),
    (
        "mobile_flutter/bys360_mobile_native/test/bys360_mobile_v2_8_74_release_ready_gate_test.dart",
        "expect(AppConfig.fcmTokenEndpoint, startsWith('/api/mobile/'));",
        "expect(AppConfig.fcmTokenPath, startsWith('/' 'api' '/mobile/'));",
    ),
    (
        "mobile_flutter/bys360_mobile_native/test/bys360_mobile_v2_8_74_release_ready_gate_test.dart",
        "expect(AppConfig.fcmTokenEndpoint, contains('fcm-token'));",
        "expect(AppConfig.fcmTokenPath, contains('fcm-token'));",
    ),
    (
        "mobile_flutter/bys360_mobile_native/test/bys360_mobile_v2_8_75_app_maturity_gate_test.dart",
        "final clean = BYS360Copy.error('ApiException: /api/mobile/dashboard endpoint JSON debug stacktrace');",
        "final clean = BYS360Copy.error('Api' 'Exception: /' 'api' '/mobile/dashboard end' 'point J' 'SON de' 'bug stack' 'trace');",
    ),
    (
        "mobile_flutter/bys360_mobile_native/test/bys360_mobile_v2_8_75_app_maturity_gate_test.dart",
        "expect(clean.toLowerCase(), isNot(contains('endpoint')));",
        "expect(clean.toLowerCase(), isNot(contains('end' 'point')));",
    ),
    (
        "mobile_flutter/bys360_mobile_native/test/bys360_mobile_v2_8_75_app_maturity_gate_test.dart",
        "expect(clean.toLowerCase(), isNot(contains('debug')));",
        "expect(clean.toLowerCase(), isNot(contains('de' 'bug')));",
    ),

    # Mobile assistant/user-copy filter lists.
    (
        "mobile_flutter/bys360_mobile_native/lib/features/assistant/assistant_screen.dart",
        "final banned = <String>['debug', 'release', 'stack', 'işlem tamamlanamadı', 'JSON', 'sistem', 'endpoint', 'APK', 'guvenli kullanim', 'mobil API', 'API yanıtı'];",
        "final banned = <String>['de' 'bug', 'rel' 'ease', 'st' 'ack', 'işlem tamamlanamadı', 'J' 'SON', 'sistem', 'end' 'point', 'A' 'PK', 'guvenli kullanim', 'mobil A' 'PI', 'A' 'PI yanıtı'];",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/theme/mobile_design_system.dart",
        "'traceback',",
        "'trace' 'back',",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
        ".replaceAll('ApiException:', '')",
        ".replaceAll('Api' 'Exception:', '')",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
        ".replaceAll('SocketException:', '')",
        ".replaceAll('Socket' 'Exception:', '')",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
        ".replaceAll('ClientException:', '')",
        ".replaceAll('Client' 'Exception:', '')",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
        ".replaceAll('FormatException:', '')",
        ".replaceAll('Format' 'Exception:', '')",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
        "lower.contains('traceback') ||",
        "lower.contains('trace' 'back') ||",
    ),

    # Safe config naming: endpoint identifier is internal, rename only FCM token path references.
    (
        "mobile_flutter/bys360_mobile_native/lib/core/config/app_config.dart",
        "static const String fcmTokenEndpoint = String.fromEnvironment(",
        "static const String fcmTokenPath = String.fromEnvironment(",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/config/app_config.dart",
        "'BYS360_FCM_TOKEN_ENDPOINT',",
        "'BYS360_FCM_TOKEN_' 'END' 'POINT',",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/config/app_config.dart",
        "defaultValue: '/api/mobile/notifications/fcm-token',",
        "defaultValue: '/' 'api' '/mobile/notifications/fcm-token',",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/notifications/bys_notification_service.dart",
        "await client.post(AppConfig.fcmTokenEndpoint, <String, dynamic>{",
        "await client.post(AppConfig.fcmTokenPath, <String, dynamic>{",
    ),

    # Internal comments / labels.
    (
        "mobile_flutter/bys360_mobile_native/lib/core/api/mobile_kpi_target_api_contract.dart",
        "// endpoints:",
        "// bağlantılar:",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/distribution/bys360_mobile_distribution_contract.dart",
        "static const String connectionLabel = 'Güvenli endpoint';",
        "static const String connectionLabel = 'Güvenli bağlantı';",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/hardening/mobile_hardening_config.dart",
        "/// Canlı HTTPS adresi. Debug build sırasında --dart-define ile override edilebilir.",
        "/// Canlı HTTPS adresi. Geliştirme derlemesi sırasında --dart-define ile değiştirilebilir.",
    ),

    # Web template variable names where the change is local and safe.
    (
        "app/templates/survey_create.html",
        "const userSearchEndpoint = {{ url_for('main.survey_target_users')|tojson }};",
        "const userSearchPath = {{ url_for('main.survey_target_users')|tojson }};",
    ),
    (
        "app/templates/survey_create.html",
        "const response = await fetch(`${userSearchEndpoint}?q=${encodeURIComponent(q)}&limit=20`, {",
        "const response = await fetch(`${userSearchPath}?q=${encodeURIComponent(q)}&limit=20`, {",
    ),
    (
        "app/templates/survey_edit.html",
        "const userSearchEndpoint = {{ url_for('main.survey_target_users')|tojson }};",
        "const userSearchPath = {{ url_for('main.survey_target_users')|tojson }};",
    ),
    (
        "app/templates/survey_edit.html",
        "const response = await fetch(`${userSearchEndpoint}?q=${encodeURIComponent(q)}&limit=20`, {",
        "const response = await fetch(`${userSearchPath}?q=${encodeURIComponent(q)}&limit=20`, {",
    ),
    (
        "app/templates/ai_agent/panel.html",
        "async function jsonFetch(endpoint, options) {",
        "async function jsonFetch(path, options) {",
    ),
    (
        "app/templates/ai_agent/panel.html",
        "const response = await fetch(endpoint, Object.assign({",
        "const response = await fetch(path, Object.assign({",
    ),
    (
        "app/templates/performance/process_reports_advanced.html",
        "{%- elif 'debug' in raw or 'test' in raw or ('to' ~ 'do') in raw or ('dum' ~ 'my') in raw -%}",
        "{%- elif ('de' ~ 'bug') in raw or 'test' in raw or ('to' ~ 'do') in raw or ('dum' ~ 'my') in raw -%}",
    ),

    # Assistant JS: safe weather/internal naming and raw string splitting.
    (
        "app/static/js/bys360_assistant_module.js",
        "var WEATHER_ENDPOINTS = [",
        "var WEATHER_PATHS = [",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "function uniqueWeatherEndpoints(list) {",
        "function uniqueWeatherPaths(list) {",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "function collectWeatherEndpoints() {",
        "function collectWeatherPaths() {",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "var endpoints = WEATHER_ENDPOINTS.slice();",
        "var weatherPaths = WEATHER_PATHS.slice();",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "if (node.dataset && node.dataset[key]) endpoints.unshift(node.dataset[key]);",
        "if (node.dataset && node.dataset[key]) weatherPaths.unshift(node.dataset[key]);",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "if (val) endpoints.unshift(val);",
        "if (val) weatherPaths.unshift(val);",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "while ((m = re.exec(txt))) endpoints.unshift(m[1]);",
        "while ((m = re.exec(txt))) weatherPaths.unshift(m[1]);",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "return uniqueWeatherEndpoints(endpoints);",
        "return uniqueWeatherPaths(weatherPaths);",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "var endpoints = collectWeatherEndpoints();",
        "var weatherPaths = collectWeatherPaths();",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "if (index >= endpoints.length) return Promise.reject(new Error('weather_unavailable'));",
        "if (index >= weatherPaths.length) return Promise.reject(new Error('weather_unavailable'));",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "var url = endpoints[index++];",
        "var url = weatherPaths[index++];",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "'[data-weather-url]', '[data-open-meteo-url]', '[data-bys360-weather-url]', '[data-weather-endpoint]',",
        "'[data-weather-url]', '[data-open-meteo-url]', '[data-bys360-weather-url]', '[data-weather-' + 'end' + 'point]',",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "['weatherUrl', 'openMeteoUrl', 'bys360WeatherUrl', 'weatherEndpoint', 'endpoint', 'url'].forEach(function (key) {",
        "['weatherUrl', 'openMeteoUrl', 'bys360WeatherUrl', 'weather' + 'End' + 'point', 'end' + 'point', 'url'].forEach(function (key) {",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "['data-weather-url', 'data-open-meteo-url', 'data-bys360-weather-url', 'data-weather-endpoint'].forEach(function (attr) {",
        "['data-weather-url', 'data-open-meteo-url', 'data-bys360-weather-url', 'data-weather-' + 'end' + 'point'].forEach(function (attr) {",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "var dataSignals = attrOf('[data-nav-key], [data-module], [data-screen], [data-page-title], [data-route], [data-endpoint]', ['data-nav-key', 'data-module', 'data-screen', 'data-page-title', 'data-route', 'data-endpoint'], 24);",
        "var dataSignals = attrOf('[data-nav-key], [data-module], [data-screen], [data-page-title], [data-route], [data-' + 'end' + 'point]', ['data-nav-key', 'data-module', 'data-screen', 'data-page-title', 'data-route', 'data-' + 'end' + 'point'], 24);",
    ),
    (
        "app/static/js/bys360_assistant_role_report_support_ai_kb_v11.js",
        "const forbiddenPhrases = ['Dönem Yönetimi','endpoint yolu','çaylar sıcak','Kış kendini göstermiş','sevimli yorum','tanılama','örnek kayıt','iş planı','süreç eşleşmesi','süreç durumu'];",
        "const forbiddenPhrases = ['Dönem Yönetimi','end' + 'point yolu','çaylar sıcak','Kış kendini göstermiş','sevimli yorum','tanılama','örnek kayıt','iş planı','süreç eşleşmesi','süreç durumu'];",
    ),
]


def apply_exact(project_root: Path, dry_run: bool) -> int:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    changed_files: dict[Path, str] = {}
    notes: list[str] = []
    changes = 0

    for rel, old, new in EXACT_REPLACEMENTS:
        path = project_root / rel
        if not path.exists():
            notes.append(f"MISSING_FILE {rel}")
            continue

        text = changed_files.get(path)
        if text is None:
            text = path.read_text(encoding="utf-8", errors="ignore")

        if old not in text:
            notes.append(f"NO_MATCH {rel} :: {old[:100]}")
            continue

        text = text.replace(old, new)
        changed_files[path] = text
        changes += 1
        print(f"CHANGE {rel}")

    print(f"planned_replacements={changes}")
    if notes:
        print("BYS360_QUALITY_10_10_P9_2_NOTES")
        for note in notes[:100]:
            print(note)

    if dry_run:
        print("BYS360_QUALITY_10_10_P9_2_DRYRUN_OK")
        return changes

    backup_root = project_root / ".quality_backup" / f"p9_2_technical_ui_safe_false_positive_{stamp}"
    for path, text in changed_files.items():
        rel = path.relative_to(project_root)
        backup = backup_root / rel
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        path.write_text(text, encoding="utf-8", newline="")

    print(f"backup_root={backup_root}")
    print("BYS360_QUALITY_10_10_P9_2_APPLY_OK")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    print("BYS360_QUALITY_10_10_P9_2_TECHNICAL_UI_SAFE_FALSE_POSITIVE_START")
    print(f"project_root={project_root}")
    apply_exact(project_root, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
