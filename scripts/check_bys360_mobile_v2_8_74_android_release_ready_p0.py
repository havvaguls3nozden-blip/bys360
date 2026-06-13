# BYS360_MOBILE_V2_8_74_ANDROID_RELEASE_READY_P0_CHECK
from __future__ import annotations

import argparse
from pathlib import Path

MARKER = "BYS360_MOBILE_V2_8_74_ANDROID_RELEASE_READY_P0"


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
    parser.add_argument("--release-preflight", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    mobile_root = project_root / "mobile_flutter" / "bys360_mobile_native"
    if not mobile_root.exists():
        fail(f"mobile root not found: {mobile_root}")

    app_gradle_path = mobile_root / "android" / "app" / "build.gradle.kts"
    settings_path = mobile_root / "android" / "settings.gradle.kts"
    notification_service_path = mobile_root / "lib" / "core" / "notifications" / "bys_notification_service.dart"
    auth_controller_path = mobile_root / "lib" / "core" / "auth" / "auth_controller.dart"
    pubspec_path = mobile_root / "pubspec.yaml"
    gitignore_path = mobile_root / ".gitignore"
    test_path = mobile_root / "test" / "bys360_mobile_v2_8_74_release_ready_gate_test.dart"

    app_gradle = read(app_gradle_path)
    settings = read(settings_path)
    notification_service = read(notification_service_path)
    auth_controller = read(auth_controller_path)
    pubspec = read(pubspec_path)
    gitignore = read(gitignore_path)

    assert_contains(pubspec, "version: 2.8.74+74", "mobile version")
    assert_contains(pubspec, f"{MARKER}_PUBSPEC", "pubspec marker")

    assert_not_contains(app_gradle, 'signingConfig = signingConfigs.getByName("debug")', "debug release signing")
    assert_contains(app_gradle, "bys360ReleaseKeystoreProperties", "release keystore properties")
    assert_contains(app_gradle, "create(\"release\")", "release signing config")
    assert_contains(app_gradle, "rootProject.file(\"key.properties\")", "key.properties loading")
    assert_contains(app_gradle, "file(\"google-services.json\").exists()", "conditional google services")
    assert_contains(app_gradle, "apply(plugin = \"com.google.gms.google-services\")", "conditional google services apply")
    assert_contains(app_gradle, f"{MARKER}_GRADLE", "gradle marker")

    assert_contains(settings, 'id("com.google.gms.google-services") version "4.4.2" apply false', "google services plugin")
    assert_contains(settings, f"{MARKER}_SETTINGS", "settings marker")

    assert_contains(notification_service, "registerDeviceToken", "FCM token registration method")
    assert_contains(notification_service, "Token registration must never break login", "safe token registration")
    assert_contains(notification_service, f"{MARKER}_FCM_NOTIFICATION_SERVICE", "notification service marker")
    assert_contains(auth_controller, "BYSNotificationService.instance.registerDeviceToken(apiClient: _apiClient);", "auth token registration hook")
    assert_contains(auth_controller, f"{MARKER}_AUTH", "auth marker")

    assert_contains(gitignore, "android/key.properties", "key properties ignore")
    assert_contains(gitignore, "*.jks", "jks ignore")
    assert_contains(gitignore, "*.keystore", "keystore ignore")
    if not test_path.exists():
        fail("missing v2.8.74 mobile gate test")

    # The code gate must not require real secrets. Release preflight is a separate opt-in check.
    if args.release_preflight:
        key_props = mobile_root / "android" / "key.properties"
        if not key_props.exists():
            fail("release preflight requires mobile_flutter/bys360_mobile_native/android/key.properties")
        key_text = read(key_props)
        for required in ["storeFile=", "storePassword=", "keyAlias=", "keyPassword="]:
            assert_contains(key_text, required, "key.properties field")
        if "YOUR_LOCAL_" in key_text or "CHANGE_ME" in key_text:
            fail("key.properties still contains placeholder values")
        store_file = None
        for line in key_text.splitlines():
            if line.strip().startswith("storeFile="):
                store_file = line.split("=", 1)[1].strip()
                break
        if not store_file:
            fail("storeFile is empty in key.properties")
        keystore_path = (mobile_root / "android" / store_file).resolve()
        if not keystore_path.exists():
            fail(f"release keystore file not found: {keystore_path}")

    print(f"{MARKER}_GATE_OK")
    if not args.release_preflight:
        print("INFO release preflight is separate: add android/key.properties + keystore, then rerun with --release-preflight")


if __name__ == "__main__":
    main()
