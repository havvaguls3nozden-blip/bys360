// BYS360_MOBILE_V2_8_73_QUALITY_TEST
import 'package:bys360_mobile_native/core/config/app_config.dart';
import 'package:bys360_mobile_native/core/navigation/bys360_route_names.dart';
import 'package:bys360_mobile_native/core/notifications/bys_notification_service.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('BYS360 mobile v2.8.73 route names are centralized', () {
    expect(BYS360RoutePaths.root, '/');
    expect(BYS360RouteNames.performance, 'performance');
    expect(BYS360RoutePaths.profile, '/profile');
  });

  test('FCM is opt-in and disabled by default for safe builds', () {
    expect(AppConfig.enableFcm, isFalse);
    expect(BYSNotificationService.instance.status, BYSNotificationStatus.disabled);
    expect(BYSNotificationService.instance.userFacingStatusText, contains('kapalı'));
  });
}
