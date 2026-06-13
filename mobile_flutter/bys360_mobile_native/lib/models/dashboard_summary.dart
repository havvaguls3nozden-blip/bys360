class DashboardSummary {
  DashboardSummary({
    required this.userName,
    required this.pendingPerformance,
    required this.unreadNotifications,
    required this.openTickets,
    required this.assignedSurveys,
    required this.kpiSuccessRate,
    required this.pendingApprovals,
    required this.activePersonnel,
    required this.unreadMessages,
    required this.aiAlerts,
    required this.activeGoals,
    required this.certificates,
  });

  final String userName;
  final int pendingPerformance;
  final int unreadNotifications;
  final int openTickets;
  final int assignedSurveys;
  final int kpiSuccessRate;
  final int pendingApprovals;
  final int activePersonnel;
  final int unreadMessages;
  final int aiAlerts;
  final int activeGoals;
  final int certificates;

  factory DashboardSummary.fromJson(Map<String, dynamic> json) {
    return DashboardSummary(
      userName: json['user_name']?.toString() ?? 'BYS360 Kullanıcısı',
      pendingPerformance: _asInt(json['pending_performance']),
      unreadNotifications: _asInt(json['unread_notifications']),
      openTickets: _asInt(json['open_tickets']),
      assignedSurveys: _asInt(json['assigned_surveys']),
      kpiSuccessRate: _asInt(json['kpi_success_rate']),
      pendingApprovals: _asInt(json['pending_approvals']),
      activePersonnel: _asInt(json['active_personnel']),
      unreadMessages: _asInt(json['unread_messages']),
      aiAlerts: _asInt(json['ai_alerts']),
      activeGoals: _asInt(json['active_goals']),
      certificates: _asInt(json['certificates']),
    );
  }

  factory DashboardSummary.demo() {
    return DashboardSummary(
      userName: 'BYS360 Kullanıcısı',
      pendingPerformance: 3,
      unreadNotifications: 5,
      openTickets: 1,
      assignedSurveys: 2,
      kpiSuccessRate: 82,
      pendingApprovals: 1,
      activePersonnel: 126,
      unreadMessages: 4,
      aiAlerts: 2,
      activeGoals: 9,
      certificates: 14,
    );
  }

  static int _asInt(dynamic value) {
    if (value is int) return value;
    if (value is num) return value.toInt();
    return int.tryParse(value?.toString() ?? '') ?? 0;
  }
}
