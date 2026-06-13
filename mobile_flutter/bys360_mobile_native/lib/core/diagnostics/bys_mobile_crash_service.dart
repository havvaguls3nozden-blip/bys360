
// BYS360_MOBILE_V2_8_75_APP_MATURITY_P1_CRASH_SERVICE
import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../utils/bys360_copy.dart';

class BYSMobileCrashService {
  BYSMobileCrashService._();

  static final BYSMobileCrashService instance = BYSMobileCrashService._();

  static const String _messageKey = 'bys360_mobile_last_safe_error_message';
  static const String _timeKey = 'bys360_mobile_last_safe_error_time';

  bool _initialized = false;

  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;

    final previousFlutterHandler = FlutterError.onError;
    FlutterError.onError = (FlutterErrorDetails details) {
      previousFlutterHandler?.call(details);
      FlutterError.presentError(details);
      unawaited(_store(details.exceptionAsString(), details.stack));
    };

    PlatformDispatcher.instance.onError = (Object error, StackTrace stack) {
      unawaited(_store(error.toString(), stack));
      return true;
    };
  }

  Future<void> _store(String message, StackTrace? stack) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_messageKey, BYS360Copy.error(message));
      await prefs.setString(_timeKey, DateTime.now().toIso8601String());
    } catch (_) {
      // Crash logging must never create a second crash.
    }
  }

  Future<String?> readLastSafeMessage() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_messageKey);
  }

  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_messageKey);
    await prefs.remove(_timeKey);
  }
}
