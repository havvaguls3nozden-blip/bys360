// BYS360_MOBILE_V2_8_29_HARDENING_P0
class MobileHardeningConfig {
  const MobileHardeningConfig._();

  static const String marker = 'BYS360_MOBILE_V2_8_29_HARDENING_P0';

  /// Canlı HTTPS adresi. Geliştirme derlemesi sırasında --dart-define ile değiştirilebilir.
  static const String liveHttpsBase =
      String.fromEnvironment('BYS360_LIVE_API_BASE', defaultValue: 'https://bys360.canakkaletarihialan.gov.tr');

  /// Local/test API base. Mevcut BYS360_API_BASE değerini bozmadan kullanılır.
  static const String apiBase =
      String.fromEnvironment('BYS360_API_BASE', defaultValue: liveHttpsBase);

  static const Duration connectTimeout = Duration(seconds: 12);
  static const Duration receiveTimeout = Duration(seconds: 25);
  static const Duration tokenRefreshSkew = Duration(minutes: 3);

  static const int maxRetryCount = 1;
  static const bool offlineFriendlyErrors = true;
  static const bool roleSafeNotifications = true;
  static const bool apkSizeAwareness = true;
  static const bool performanceOptimizationReady = true;
  static const bool httpsLiveTestReady = true;
}
