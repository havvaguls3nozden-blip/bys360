import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/bys_mobile_chrome.dart';
import '../assistant/assistant_screen.dart';
import '../dashboard/dashboard_screen.dart';
import '../notifications/notifications_screen.dart';
import 'performance_periods_screen.dart';
import 'performance_scorecards_screen.dart';
import 'performance_tasks_screen.dart';
import 'performance_executive_p1_screen.dart';

class PerformanceMobileRouteShell extends StatelessWidget {
  const PerformanceMobileRouteShell({
    super.key,
    required this.apiClient,
    required this.title,
    required this.child,
  });

  final ApiClient apiClient;
  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: BYS360Colors.pageBackground,
      appBar: BYSMobileAppBar(title: title, onMenu: () => Navigator.of(context).maybePop()),
      body: Material(color: BYS360Colors.pageBackground, child: child),
      bottomNavigationBar: SafeArea(
        child: Container(
          decoration: const BoxDecoration(color: Colors.white, border: Border(top: BorderSide(color: BYS360Colors.cardBorder))),
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _NavMini(icon: Icons.dashboard_outlined, label: 'Ana', onTap: () => _replace(context, 'Ana Sayfa', DashboardScreen(apiClient: apiClient))),
              _NavMini(icon: Icons.timeline_outlined, label: 'Dönem', onTap: () => _replace(context, 'Dönemler', PerformancePeriodsScreen(apiClient: apiClient))),
              _NavMini(icon: Icons.assignment_ind_outlined, label: 'Görev', onTap: () => _replace(context, 'Görevlerim', PerformanceTasksScreen(apiClient: apiClient))),
              _NavMini(icon: Icons.assignment_turned_in_outlined, label: 'Karne', onTap: () => _replace(context, 'Karne', PerformanceScorecardsScreen(apiClient: apiClient))),
              _NavMini(icon: Icons.admin_panel_settings_outlined, label: 'Yönetim', onTap: () => _replace(context, 'Yönetici', PerformanceExecutiveP1Screen(apiClient: apiClient))),
              _NavMini(icon: Icons.chat_bubble_outline, label: 'Asistan', onTap: () => _replace(context, 'BYS360 Asistanı', AssistantScreen(apiClient: apiClient))),
              _NavMini(icon: Icons.notifications_outlined, label: 'Bildirim', onTap: () => _replace(context, 'Bildirimler', NotificationsScreen(apiClient: apiClient))),
            ],
          ),
        ),
      ),
    );
  }

  void _replace(BuildContext context, String nextTitle, Widget nextChild) {
    Navigator.of(context).pushReplacement(MaterialPageRoute(
      builder: (_) => PerformanceMobileRouteShell(apiClient: apiClient, title: nextTitle, child: nextChild),
    ));
  }
}

class _NavMini extends StatelessWidget {
  const _NavMini({required this.icon, required this.label, required this.onTap});

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 4),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: BYS360Colors.corporateRed, size: 20),
            const SizedBox(height: 2),
            Text(label, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: BYS360Colors.ink)),
          ],
        ),
      ),
    );
  }
}

// BYS360_MOBILE_V2_8_27_PERFORMANCE_P1 route shell

// BYS360_MOBILE_V2_8_30_ROUTE_ENTRY

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION
