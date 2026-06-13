// BYS360_MOBILE_V2_8_73_MAIN_NOTIFICATION_BOOTSTRAP
import 'package:flutter/material.dart';

import 'app.dart';
import 'core/diagnostics/bys_mobile_crash_service.dart';
import 'core/notifications/bys_notification_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await BYSMobileCrashService.instance.initialize();
  await BYSNotificationService.instance.initialize();
  runApp(const BYS360MobileApp());
}

// BYS360_MOBILE_V2_8_75_APP_MATURITY_P1_MAIN_CRASH_BOOTSTRAP
