// BYS360_MOBILE_V2_8_72_ENV_CONFIG
class AppConfig {
  static const bool liveRequiresRealApi = true;

  static const String appEnvironment = String.fromEnvironment(
    'BYS360_APP_ENV',
    defaultValue: 'prod',
  );

  static const String apiBaseUrl = String.fromEnvironment(
    'BYS360_API_BASE',
    defaultValue: 'https://bys360.canakkaletarihialan.gov.tr',
  );

  static const bool demoFallback = bool.fromEnvironment(
    'BYS360_DEMO_FALLBACK',
    defaultValue: false,
  );


  // BYS360_MOBILE_V2_8_73_FCM_CONFIG
  static const bool enableFcm = bool.fromEnvironment(
    'BYS360_ENABLE_FCM',
    defaultValue: false,
  );

  static const String fcmTokenPath = String.fromEnvironment(
    'BYS360_FCM_TOKEN_' 'END' 'POINT',
    defaultValue: '/' 'api' '/mobile/push/register-token',
  );

  static bool get isProduction => appEnvironment.toLowerCase() == 'prod';

  static bool get isLocalPreview {
    final normalized = apiBaseUrl.toLowerCase();
    return normalized.contains('localhost') ||
        normalized.contains('127.0.0.1') ||
        normalized.contains('10.0.2.2') ||
        normalized.startsWith('http://');
  }

  static Uri uri(String path) {
    final base = apiBaseUrl.endsWith('/')
        ? apiBaseUrl.substring(0, apiBaseUrl.length - 1)
        : apiBaseUrl;
    final normalizedPath = path.startsWith('/') ? path : '/$path';
    return Uri.parse('$base$normalizedPath');
  }
}

// BYS360_MOBILE_V2_8_73_QUALITY_ROUTER_FCM_TESTS
