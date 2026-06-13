import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import 'performance_mobile_p1_widgets.dart';

class PerformanceRiskAnalysisScreen extends StatelessWidget {
  const PerformanceRiskAnalysisScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  Widget build(BuildContext context) {
    return PerformanceP1ListScreen(
      apiClient: apiClient,
      path: '/api/mobile/performance/risk-analysis',
      title: 'Risk Analizi',
      subtitle: 'Düşük performans, geciken değerlendirme, yayın kilidi ve tekrar eden riskler özetlenir.',
      badge: 'Risk',
      icon: Icons.warning_amber_rounded,
      tone: BYS360Colors.danger,
      detailTitle: 'Risk Detayı',
      detailPathPrefix: '/api/mobile/performance/risk-analysis',
      emptyMessage: 'Yetkiniz kapsamında görünen risk kaydı bulunmadı.',
    );
  }
}

// BYS360_MOBILE_V2_8_30_RISK_ANALYSIS

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION
