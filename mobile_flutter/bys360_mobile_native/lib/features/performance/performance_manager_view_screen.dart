import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import 'performance_mobile_p1_widgets.dart';

class PerformanceManagerViewScreen extends StatelessWidget {
  const PerformanceManagerViewScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  Widget build(BuildContext context) {
    return PerformanceP1ListScreen(
      apiClient: apiClient,
      path: '/api/mobile/performance/manager-view',
      title: 'Yönetici Görünümü',
      subtitle: 'Kendi yetki kapsamınızdaki ekip, dönem, görev ve karne özetleri gösterilir.',
      badge: 'Yönetici',
      icon: Icons.dashboard_customize_outlined,
      tone: BYS360Colors.info,
      detailTitle: 'Yönetici Performans Detayı',
      detailPathPrefix: '/api/mobile/performance/manager-view',
      emptyMessage: 'Yönetici görünümü için yetki kapsamınızda kayıt bulunmadı.',
    );
  }
}

// BYS360_MOBILE_V2_8_30_MANAGER_VIEW

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION
