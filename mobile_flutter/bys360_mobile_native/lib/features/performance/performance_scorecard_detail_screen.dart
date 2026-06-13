import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import 'performance_mobile_p1_widgets.dart';

class PerformanceScorecardDetailScreen extends StatelessWidget {
  const PerformanceScorecardDetailScreen({super.key, required this.apiClient, required this.scorecardId});

  final ApiClient apiClient;
  final String scorecardId;

  @override
  Widget build(BuildContext context) {
    return PerformanceP1DetailScreen(
      apiClient: apiClient,
      path: '/api/mobile/performance/scorecards/$scorecardId',
      title: 'Karne Detayı',
      subtitle: 'Yayınlanmış karne, kriterler ve süreç geçmişi',
      badge: 'Karne',
      icon: Icons.assignment_turned_in_outlined,
      tone: BYS360Colors.success,
    );
  }
}

// BYS360_MOBILE_V2_8_27_PERFORMANCE_P1 scorecard detail

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION
