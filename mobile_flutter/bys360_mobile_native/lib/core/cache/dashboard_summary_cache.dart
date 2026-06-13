
// BYS360_MOBILE_V2_8_75_APP_MATURITY_P1_DASHBOARD_CACHE
import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../../models/dashboard_summary.dart';

class DashboardSummaryCache {
  const DashboardSummaryCache._();

  static const String _dataKey = 'bys360_dashboard_summary_cache_data_v1';
  static const String _timeKey = 'bys360_dashboard_summary_cache_time_v1';
  static const Duration freshFor = Duration(minutes: 5);

  static Future<void> save(DashboardSummary summary) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_dataKey, jsonEncode(_toJson(summary)));
    await prefs.setString(_timeKey, DateTime.now().toIso8601String());
  }

  static Future<DashboardSummary?> readFresh() async {
    final prefs = await SharedPreferences.getInstance();
    final rawTime = prefs.getString(_timeKey);
    final rawData = prefs.getString(_dataKey);
    if (rawTime == null || rawData == null) return null;

    final savedAt = DateTime.tryParse(rawTime);
    if (savedAt == null) return null;
    if (DateTime.now().difference(savedAt) > freshFor) return null;

    try {
      final decoded = jsonDecode(rawData);
      if (decoded is! Map) return null;
      return DashboardSummary.fromJson(Map<String, dynamic>.from(decoded));
    } catch (_) {
      return null;
    }
  }

  static Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_dataKey);
    await prefs.remove(_timeKey);
  }

  static Map<String, dynamic> _toJson(DashboardSummary summary) => <String, dynamic>{
        'user_name': summary.userName,
        'pending_performance': summary.pendingPerformance,
        'unread_notifications': summary.unreadNotifications,
        'open_tickets': summary.openTickets,
        'assigned_surveys': summary.assignedSurveys,
        'kpi_success_rate': summary.kpiSuccessRate,
        'pending_approvals': summary.pendingApprovals,
        'active_personnel': summary.activePersonnel,
        'unread_messages': summary.unreadMessages,
        'ai_alerts': summary.aiAlerts,
        'active_goals': summary.activeGoals,
        'certificates': summary.certificates,
      };
}
