import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import 'performance_mobile_p1_widgets.dart';

class PerformancePeriodsScreen extends StatelessWidget {
  const PerformancePeriodsScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  Widget build(BuildContext context) {
    return PerformanceP1ListScreen(
      apiClient: apiClient,
      path: '/api/mobile/performance/periods',
      title: 'Performans Dönemleri',
      subtitle: 'Açık, geçmiş ve kapsam bazlı performans dönemlerini web verisiyle görüntüleyin.',
      badge: 'Dönemler',
      icon: Icons.timeline_outlined,
      tone: BYS360Colors.info,
      detailTitle: 'Dönem Detayı',
      detailPathPrefix: '/api/mobile/performance/periods',
      emptyMessage: 'Yetkiniz dahilinde görüntülenecek performans dönemi bulunamadı.',
    );
  }
}

// BYS360_MOBILE_V2_8_27_PERFORMANCE_P1 periods

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION
