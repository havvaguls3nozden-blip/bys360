// BYS360_MOBILE_V2_8_74_ANDROID_RELEASE_READY_P0_FCM_NOTIFICATION_SERVICE
// FCM is opt-in. The app stays stable when Firebase configuration is not installed yet.
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

import '../config/app_config.dart';
import '../network/api_client.dart';

class BYSNotificationService {
  BYSNotificationService._();

  static final BYSNotificationService instance = BYSNotificationService._();

  bool _initialized = false;
  bool _tokenRegistered = false;
  BYSNotificationStatus _status = BYSNotificationStatus.disabled;
  String? _fcmToken;
  String? _lastForegroundTitle;

  BYSNotificationStatus get status => _status;
  String? get fcmToken => _fcmToken;
  String? get lastForegroundTitle => _lastForegroundTitle;
  bool get tokenRegistered => _tokenRegistered;

  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;

    if (!AppConfig.enableFcm) {
      _status = BYSNotificationStatus.disabled;
      return;
    }

    try {
      await Firebase.initializeApp();
      final messaging = FirebaseMessaging.instance;
      await messaging.requestPermission(alert: true, badge: true, sound: true);
      _fcmToken = await messaging.getToken();
      FirebaseMessaging.onMessage.listen((message) {
        _lastForegroundTitle = message.notification?.title ?? 'BYS360 bildirimi';
      });
      _status = BYSNotificationStatus.ready;
    } catch (_) {
      // Technical Firebase / Gradle / APNs messages are not shown to users.
      _status = BYSNotificationStatus.unavailable;
    }
  }

  Future<void> registerDeviceToken({ApiClient? apiClient}) async {
    if (!AppConfig.enableFcm || _status != BYSNotificationStatus.ready) return;
    final token = _fcmToken;
    if (token == null || token.trim().isEmpty) return;

    try {
      final client = apiClient ?? ApiClient();
      await client.post(AppConfig.fcmTokenPath, <String, dynamic>{
        'token': token,
        'platform': 'android',
        'source': 'flutter_native',
      });
      _tokenRegistered = true;
    } catch (_) {
      // Token registration must never break login or app startup.
      _tokenRegistered = false;
    }
  }

  String get userFacingStatusText {
    switch (_status) {
      case BYSNotificationStatus.ready:
        return 'Bildirimler hazır.';
      case BYSNotificationStatus.unavailable:
        return 'Bildirim altyapısı yapılandırma tamamlanınca etkinleşecektir.';
      case BYSNotificationStatus.disabled:
        return 'Bildirimler şu anda kapalı.';
    }
  }
}

enum BYSNotificationStatus { disabled, ready, unavailable }
