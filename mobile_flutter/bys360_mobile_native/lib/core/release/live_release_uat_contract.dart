// BYS360_MOBILE_V2_8_34_LIVE_RELEASE_UAT
// Canlı release ve UAT kontrol sözleşmesi.

class LiveReleaseUatContract {
  static const String marker = 'BYS360_MOBILE_V2_8_34_LIVE_RELEASE_UAT';
  static const String liveApiBase = 'https://bys360.canakkaletarihialan.gov.tr';
  static const String releaseBuildCommand = 'flutter build apk --release --dart-define=BYS360_API_BASE=https://bys360.canakkaletarihialan.gov.tr';

  static const List<String> uatAreas = <String>[
    'login_live_api',
    'dashboard_live_data',
    'notifications_live_data',
    'profile_live_data',
    'performance_live_data',
    'personnel_live_data',
    'support_survey_live_data',
    'kpi_target_live_dashboard',
    'role_matrix_visibility',
    'offline_timeout_token_flow',
    'release_apk_build',
  ];
}
