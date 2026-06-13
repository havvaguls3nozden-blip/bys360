import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import 'performance_mobile_p1_widgets.dart';

class PerformancePresidentApprovalsScreen extends StatelessWidget {
  const PerformancePresidentApprovalsScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  Widget build(BuildContext context) {
    return PerformanceP1ListScreen(
      apiClient: apiClient,
      path: '/api/mobile/performance/president-approvals',
      title: 'Başkan/Üst Onayları',
      subtitle: '70 altı sonuçlar, yayın kilidi ve üst onay bekleyen kayıtlar yetki sınırıyla gösterilir.',
      badge: 'Üst Onay',
      icon: Icons.verified_user_outlined,
      tone: BYS360Colors.warning,
      detailTitle: 'Başkan Onayı Karne İncelemesi',
      detailPathPrefix: '/api/mobile/performance/president-approvals',
      emptyMessage: 'Başkan/Üst Onay bekleyen düşük performans kaydı bulunmadı veya bu alan için yetkiniz yok.',
    );
  }
}

// BYS360_MOBILE_V2_8_30_PRESIDENT_APPROVALS

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION
