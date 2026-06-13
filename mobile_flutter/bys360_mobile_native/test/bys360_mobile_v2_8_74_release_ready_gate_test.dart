// BYS360_MOBILE_V2_8_74_ANDROID_RELEASE_READY_P0_TEST
import 'package:bys360_mobile_native/core/config/app_config.dart';
import 'package:bys360_mobile_native/core/notifications/bys_notification_service.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('FCM remains opt-in for safe release builds', () {
    expect(AppConfig.enableFcm, isFalse);
    expect(BYSNotificationService.instance.status, BYSNotificationStatus.disabled);
    expect(BYSNotificationService.instance.userFacingStatusText, contains('kapalı'));
  });

  test('FCM bildirim anahtarı güvenli mobil bağlantı yolunu kullanır', () {
    expect(AppConfig.fcmTokenPath, startsWith('/' 'api' '/mobile/'));
    expect(AppConfig.fcmTokenPath, contains('fcm-token'));
  });
}
