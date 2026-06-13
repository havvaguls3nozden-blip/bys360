import 'dart:async';
import 'dart:io';

import 'mobile_error_texts.dart';
import 'mobile_hardening_config.dart';
import 'mobile_hardening_state.dart';

// BYS360_MOBILE_V2_8_29_HARDENING_SERVICE
class MobileHardeningService {
  const MobileHardeningService();

  MobileHardeningState get state => MobileHardeningState.ready;

  Future<T> withTimeout<T>(Future<T> Function() action) {
    return action().timeout(
      MobileHardeningConfig.receiveTimeout,
      onTimeout: () => throw TimeoutException(MobileErrorTexts.timeoutMessage),
    );
  }

  String safeErrorMessage(Object error, {int? statusCode}) {
    if (error is TimeoutException) {
      return MobileErrorTexts.timeoutMessage;
    }
    if (error is SocketException) {
      return MobileErrorTexts.offlineMessage;
    }
    return MobileErrorTexts.fromStatusCode(statusCode);
  }

  bool get isHttpsLiveReady =>
      MobileHardeningConfig.apiBase.startsWith('https://') ||
      MobileHardeningConfig.apiBase.contains('192.168.') ||
      MobileHardeningConfig.apiBase.contains('127.0.0.1') ||
      MobileHardeningConfig.apiBase.contains('localhost');

  bool get notificationTestReady => MobileHardeningConfig.roleSafeNotifications;

  bool shouldRefreshToken(DateTime? expiresAt) {
    if (expiresAt == null) return false;
    final now = DateTime.now();
    return expiresAt.difference(now) <= MobileHardeningConfig.tokenRefreshSkew;
  }
}
