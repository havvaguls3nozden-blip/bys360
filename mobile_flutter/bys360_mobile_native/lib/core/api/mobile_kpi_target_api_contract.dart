// BYS360_MOBILE_V2_8_33_KPI_TARGET_API_CONTRACT
// bağlantılar:
// GET /api/mobile/kpi/dashboard
// GET /api/mobile/kpi/targets
// GET /api/mobile/kpi/risk-summary
// GET /api/mobile/kpi/periods
// role safe: user can only see authorized KPI/target scope.
class MobileKpiTargetApiContract {
  static const dashboard = '/api/mobile/kpi/dashboard';
  static const targets = '/api/mobile/kpi/targets';
  static const riskSummary = '/api/mobile/kpi/risk-summary';
  static const periods = '/api/mobile/kpi/periods';
}
