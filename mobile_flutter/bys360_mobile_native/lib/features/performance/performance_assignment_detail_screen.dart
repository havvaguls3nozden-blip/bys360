import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import 'performance_mobile_p1_widgets.dart';

class PerformanceAssignmentDetailScreen extends StatelessWidget {
  const PerformanceAssignmentDetailScreen({super.key, required this.apiClient, required this.assignmentId});

  final ApiClient apiClient;
  final String assignmentId;

  @override
  Widget build(BuildContext context) {
    return PerformanceP1DetailScreen(
      apiClient: apiClient,
      path: '/api/mobile/performance/tasks/$assignmentId',
      title: 'Değerlendirme Detayı',
      subtitle: 'Görev, kriter, puanlama ve süreç bilgileri',
      badge: 'Değerlendirme',
      icon: Icons.fact_check_outlined,
      tone: BYS360Colors.corporateRed,
    );
  }
}

// BYS360_MOBILE_V2_8_27_PERFORMANCE_P1 assignment detail

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION
