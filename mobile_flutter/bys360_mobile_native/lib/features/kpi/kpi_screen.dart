// BYS360_MOBILE_V2_8_53_KPI_SCREEN_ROUTE
import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import 'kpi_target_management_screen.dart';

class KpiScreen extends StatelessWidget {
  const KpiScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  Widget build(BuildContext context) {
    return KpiTargetManagementScreen(apiClient: apiClient);
  }
}
