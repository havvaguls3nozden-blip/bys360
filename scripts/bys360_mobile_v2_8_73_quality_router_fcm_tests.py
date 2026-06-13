# -*- coding: utf-8 -*-
"""BYS360 Mobile V2.8.73 repair script.
Safely patches Flutter mobile project for go_router/provider/FCM/test quality layer.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARKER = 'BYS360_MOBILE_V2_8_73_QUALITY_ROUTER_FCM_TESTS'


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8') if path.exists() else ''


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')


def ensure_dependency(pubspec: str, name: str, version: str) -> str:
    if f'\n  {name}:' in pubspec or pubspec.startswith(f'{name}:'):
        return pubspec
    lines = pubspec.splitlines()
    out = []
    inserted = False
    for line in lines:
        if not inserted and line.startswith('dev_dependencies:'):
            out.append(f'  {name}: {version}')
            inserted = True
        out.append(line)
    if not inserted:
        out.append('dependencies:')
        out.append(f'  {name}: {version}')
    return '\n'.join(out) + '\n'


def patch_pubspec(project: Path) -> None:
    path = project / 'mobile_flutter' / 'bys360_mobile_native' / 'pubspec.yaml'
    text = read_text(path)
    if not text:
        raise SystemExit(f'pubspec.yaml bulunamadı: {path}')
    lines = []
    for line in text.splitlines():
        if line.startswith('version:'):
            lines.append('version: 2.8.73+73')
        else:
            lines.append(line)
    text = '\n'.join(lines) + '\n'
    for name, version in {
        'go_router': '^14.2.7',
        'provider': '^6.1.2',
        'firebase_core': '^3.6.0',
        'firebase_messaging': '^15.1.3',
    }.items():
        text = ensure_dependency(text, name, version)
    if f'# {MARKER}' not in text:
        text = text.rstrip() + f'\n\n# {MARKER}\n'
    write_text(path, text)


def patch_app_config(project: Path) -> None:
    path = project / 'mobile_flutter' / 'bys360_mobile_native' / 'lib' / 'core' / 'config' / 'app_config.dart'
    text = read_text(path)
    if not text:
        raise SystemExit(f'app_config.dart bulunamadı: {path}')
    if 'enableFcm' not in text:
        insert = """
  // BYS360_MOBILE_V2_8_73_FCM_CONFIG
  static const bool enableFcm = bool.fromEnvironment(
    'BYS360_ENABLE_FCM',
    defaultValue: false,
  );

  static const String fcmTokenEndpoint = String.fromEnvironment(
    'BYS360_FCM_TOKEN_ENDPOINT',
    defaultValue: '/api/mobile/notifications/fcm-token',
  );
"""
        marker = '  static bool get isProduction =>'
        if marker in text:
            text = text.replace(marker, insert + '\n' + marker)
        else:
            text = text.replace('class AppConfig {', 'class AppConfig {' + insert)
    if 'BYS360_MOBILE_V2_8_73_QUALITY_ROUTER_FCM_TESTS' not in text:
        text = text.rstrip() + f'\n\n// {MARKER}\n'
    write_text(path, text)


def patch_main(project: Path) -> None:
    path = project / 'mobile_flutter' / 'bys360_mobile_native' / 'lib' / 'main.dart'
    text = """// BYS360_MOBILE_V2_8_73_MAIN_NOTIFICATION_BOOTSTRAP
import 'package:flutter/material.dart';

import 'app.dart';
import 'core/notifications/bys_notification_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await BYSNotificationService.instance.initialize();
  runApp(const BYS360MobileApp());
}
"""
    write_text(path, text)


def patch_app(project: Path) -> None:
    path = project / 'mobile_flutter' / 'bys360_mobile_native' / 'lib' / 'app.dart'
    text = """// BYS360_MOBILE_V2_8_73_APP_ROUTER_PROVIDER
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/navigation/bys360_app_router.dart';
import 'core/state/bys_session_controller.dart';
import 'core/theme/app_theme.dart';

class BYS360MobileApp extends StatelessWidget {
  const BYS360MobileApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => BYSSessionController()..restore(),
      child: MaterialApp.router(
        debugShowCheckedModeBanner: false,
        title: 'BYS360 Mobile',
        theme: BYS360Theme.light,
        routerConfig: BYS360AppRouter.router,
      ),
    );
  }
}
"""
    write_text(path, text)


def patch_android_manifest(project: Path) -> None:
    path = project / 'mobile_flutter' / 'bys360_mobile_native' / 'android' / 'app' / 'src' / 'main' / 'AndroidManifest.xml'
    text = read_text(path)
    if not text:
        return
    if 'android.permission.POST_NOTIFICATIONS' not in text:
        if '<uses-permission android:name="android.permission.INTERNET" />' in text:
            text = text.replace(
                '<uses-permission android:name="android.permission.INTERNET" />',
                '<uses-permission android:name="android.permission.INTERNET" />\n    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />',
            )
        else:
            text = text.replace('<manifest xmlns:android="http://schemas.android.com/apk/res/android">', '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />')
    if '<!-- BYS360_MOBILE_V2_8_73_ANDROID_NOTIFICATIONS -->' not in text:
        text = text.replace('</manifest>', '    <!-- BYS360_MOBILE_V2_8_73_ANDROID_NOTIFICATIONS -->\n</manifest>')
    write_text(path, text)


def ensure_copied_files(project: Path, script_root: Path) -> None:
    payload_root = script_root.parent
    relative_files = [
        'mobile_flutter/bys360_mobile_native/lib/core/navigation/bys360_route_names.dart',
        'mobile_flutter/bys360_mobile_native/lib/core/navigation/bys360_app_router.dart',
        'mobile_flutter/bys360_mobile_native/lib/core/state/bys_session_controller.dart',
        'mobile_flutter/bys360_mobile_native/lib/core/notifications/bys_notification_service.dart',
        'mobile_flutter/bys360_mobile_native/test/bys360_mobile_v2_8_73_quality_gate_test.dart',
    ]
    for rel in relative_files:
        src = payload_root / rel
        dst = project / rel
        if src.exists():
            write_text(dst, read_text(src))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', required=True)
    args = parser.parse_args()
    project = Path(args.project_root).resolve()
    script_root = Path(__file__).resolve().parent
    mobile = project / 'mobile_flutter' / 'bys360_mobile_native'
    if not mobile.exists():
        raise SystemExit(f'Mobil proje klasörü bulunamadı: {mobile}')
    ensure_copied_files(project, script_root)
    patch_pubspec(project)
    patch_app_config(project)
    patch_main(project)
    patch_app(project)
    patch_android_manifest(project)
    print('BYS360_MOBILE_V2_8_73_QUALITY_ROUTER_FCM_TESTS_REPAIR_OK')


if __name__ == '__main__':
    main()
