import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import 'performance_mobile_p1_widgets.dart';

class PerformanceScorecardsScreen extends StatelessWidget {
  const PerformanceScorecardsScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  Widget build(BuildContext context) {
    return PerformanceP1ListScreen(
      apiClient: apiClient,
      path: '/api/mobile/performance/scorecards',
      title: 'Performans Karnelerim',
      subtitle: 'Yayınlanmış ve yetki kapsamınızda açılmış performans karnelerini görüntüleyin.',
      badge: 'Karne',
      icon: Icons.assignment_turned_in_outlined,
      tone: BYS360Colors.success,
      detailTitle: 'Karne Detayı',
      detailPathPrefix: '/api/mobile/performance/scorecards',
      emptyMessage: 'Yayınlanmış veya yetkiniz dahilinde görüntülenecek karne bulunamadı.',
    );
  }
}

// BYS360_MOBILE_V2_8_27_PERFORMANCE_P1 scorecards

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION
