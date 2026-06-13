/// BYS360 Mobile V2.8.72 P0 gerçek API sözleşmesi.
/// Bu dosya mobil uygulamada canli_api/veri kopyası yerine BYS360 web sistem
/// uçlarının kullanılacağını sabitler.
class MobileRealApiContract {
  const MobileRealApiContract._();

  static const String marker = 'BYS360_MOBILE_V2_8_25_REAL_API_P0';

  static const String login = '/api/mobile/auth/login';
  static const String refresh = '/api/mobile/auth/refresh';
  static const String me = '/api/mobile/me';
  static const String menu = '/api/mobile/me/menu';
  static const String dashboardSummary = '/api/mobile/dashboard/summary';
  static const String notifications = '/api/mobile/notifications';
  static const String profile = '/api/mobile/me';
  static const String performanceSummary = '/api/mobile/performance/summary';

  static const List<String> p0Endpoints = <String>[
    login,
    refresh,
    me,
    menu,
    dashboardSummary,
    notifications,
    profile,
    performanceSummary,
  ];

  /// Mobil P0 kuralı: canlı build varsayılan olarak demo veriye düşmez.
  /// Demo yalnızca açıkça BYS360_DEMO_FALLBACK=true verilirse çalışır.
  static const bool liveRequiresRealApi = true;
}

// BYS360_MOBILE_V2_8_29_REAL_API_HARDENING_CONTRACT
class MobileRealApiHardeningContract {
  const MobileRealApiHardeningContract._();

  static const String offlineBehavior = 'offline_behavior_ready';
  static const String tokenRefresh = 'token_refresh_ready';
  static const String timeoutManagement = 'timeout_management_ready';
  static const String httpsLiveTest = 'https_live_test_ready';
  static const String notificationTest = 'notification_test_ready';
  static const String apkSizePerformance = 'apk_size_performance_ready';

  static const List<String> p0Checks = <String>[
    offlineBehavior,
    tokenRefresh,
    timeoutManagement,
    httpsLiveTest,
    notificationTest,
    apkSizePerformance,
  ];
}

// BYS360_MOBILE_V2_8_30_PERFORMANCE_EXECUTIVE_P1_CONTRACT
class MobilePerformanceExecutiveP1Contract {
  const MobilePerformanceExecutiveP1Contract._();

  static const String presidentApprovals =
      '/api/mobile/performance/president-approvals';
  static const String riskAnalysis = '/api/mobile/performance/risk-analysis';
  static const String managerView = '/api/mobile/performance/manager-view';

  static const List<String> endpoints = <String>[
    presidentApprovals,
    riskAnalysis,
    managerView,
  ];

  static const bool roleMatrixRequired = true;
  static const bool hideUnauthorizedRecords = true;
  static const bool sensitiveScoreGuard = true;
}

// BYS360 Mobile V2.8.31 Personnel P1 real API contract
const Map<String, String> personnelMobileP1 = <String, String>{
  'list': '/api/mobile/personnel',
  'detail': '/api/mobile/personnel/{id}',
  'organizationSummary': '/api/mobile/personnel/{id}/organization-summary',
  'leaveDelegationSummary':
      '/api/mobile/personnel/{id}/leave-delegation-summary',
};

// BYS360_MOBILE_V2_8_72_REFRESH_CONTRACT
