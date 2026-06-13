# BYS360_MOBILE_V2_8_75_APP_MATURITY_P1_CHECK
from __future__ import annotations

import argparse
from pathlib import Path

MARKER = "BYS360_MOBILE_V2_8_75_APP_MATURITY_P1"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def fail(message: str) -> None:
    raise SystemExit(f"{MARKER}_GATE_FAIL {message}")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"missing {label}: {needle}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        fail(f"forbidden {label}: {needle}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    mobile_root = project_root / "mobile_flutter" / "bys360_mobile_native"
    if not mobile_root.exists():
        fail(f"mobile root not found: {mobile_root}")

    pubspec = read(mobile_root / "pubspec.yaml")
    app = read(mobile_root / "lib" / "app.dart")
    main_dart = read(mobile_root / "lib" / "main.dart")
    theme = read(mobile_root / "lib" / "core" / "theme" / "app_theme.dart")
    copy = read(mobile_root / "lib" / "core" / "utils" / "bys360_copy.dart")
    dashboard = read(mobile_root / "lib" / "features" / "dashboard" / "dashboard_screen.dart")
    app_gradle = read(mobile_root / "android" / "app" / "build.gradle.kts")

    assert_contains(pubspec, "version: 2.8.75+75", "mobile version")
    assert_contains(pubspec, f"# {MARKER}_PUBSPEC", "pubspec marker")

    assert_contains(app, "darkTheme: BYS360Theme.dark", "dark theme registration")
    assert_contains(app, "themeMode: ThemeMode.system", "system theme mode")
    assert_contains(app, f"// {MARKER}_APP_THEME_MODE", "app marker")

    assert_contains(theme, "static ThemeData get dark", "dark theme")
    assert_contains(theme, "Brightness.dark", "dark brightness")
    assert_contains(theme, f"// {MARKER}_THEME", "theme marker")

    assert_contains(main_dart, "BYSMobileCrashService.instance.initialize", "crash bootstrap")
    assert_contains(main_dart, f"// {MARKER}_MAIN_CRASH_BOOTSTRAP", "main marker")

    crash_service_path = mobile_root / "lib" / "core" / "diagnostics" / "bys_mobile_crash_service.dart"
    assert_contains(read(crash_service_path), "PlatformDispatcher.instance.onError", "platform crash handler")
    assert_contains(read(crash_service_path), f"// {MARKER}_CRASH_SERVICE", "crash marker")

    cache_path = mobile_root / "lib" / "core" / "cache" / "dashboard_summary_cache.dart"
    cache = read(cache_path)
    assert_contains(cache, "freshFor = Duration(minutes: 5)", "dashboard cache ttl")
    assert_contains(cache, "SharedPreferences.getInstance", "dashboard cache storage")
    assert_contains(cache, f"// {MARKER}_DASHBOARD_CACHE", "cache marker")

    assert_contains(dashboard, "DashboardSummaryCache.save(summary)", "dashboard cache save")
    assert_contains(dashboard, "DashboardSummaryCache.readFresh()", "dashboard cache fallback")
    assert_contains(dashboard, f"// {MARKER}_DASHBOARD_CACHE_HOOK", "dashboard marker")
    assert_not_contains(dashboard, "endpointnızı", "broken endpoint copy")

    assert_contains(copy, "genericUnavailable", "copy generic unavailable")
    assert_contains(copy, f"// {MARKER}_COPY_CLEANER", "copy marker")
    assert_not_contains(copy, "endpointnızı", "broken endpoint copy in cleaner")

    test_path = mobile_root / "test" / "bys360_mobile_v2_8_75_app_maturity_gate_test.dart"
    if not test_path.exists():
        fail("missing v2.8.75 app maturity test")
    assert_contains(read(test_path), "dashboard summary cache stores", "cache test")

    # P0 release readiness must remain intact.
    assert_not_contains(app_gradle, 'signingConfig = signingConfigs.getByName("debug")', "debug release signing regression")
    assert_contains(app_gradle, "bys360ReleaseKeystoreProperties", "P0 release signing properties")

    print(f"{MARKER}_GATE_OK")


if __name__ == "__main__":
    main()
