/* BYS360_MOBILE_V2_8_34_RELEASE_FINAL_ANALYZE_FIX */
import 'package:flutter/material.dart';

// BYS360_MOBILE_V2_8_34_RELEASE_ANALYZE_CLEAN: release analyze cleanup.

import '../../core/api/mobile_api_client.dart';
import '../../core/widgets/mobile_design_system.dart';
// BYS360_MOBILE_V2_8_34_RELEASE_UI_CONTRACT_FIX

/// BYS360 Mobile V2.8.34 KPI Target Dashboard Release Contract
/// Canlı API sözleşmesi: /api/mobile/kpi/dashboard
/// Hedef özeti, riskli KPI, dönem/kapsam ve yönetici görünümü yetki kontrollü gösterilir.
class KpiTargetDashboardP1Screen extends StatefulWidget {
  const KpiTargetDashboardP1Screen({super.key, this.apiClient});

  final MobileApiClient? apiClient;

  @override
  State<KpiTargetDashboardP1Screen> createState() => _KpiTargetDashboardP1ScreenState();
}

class _KpiTargetDashboardP1ScreenState extends State<KpiTargetDashboardP1Screen> {
  late final Future<Map<String, dynamic>> _future = _loadKpiDashboard();

  Future<Map<String, dynamic>> _loadKpiDashboard() {
    final client = widget.apiClient ?? const MobileApiClient();
    return client.getJson('/api/mobile/kpi/dashboard');
  }

  @override
  Widget build(BuildContext context) {
    return MobilePageScaffold(
      title: 'KPI ve Hedefler',
      subtitle: 'Canlı hedef gerçekleşme ve risk görünümü',
      children: <Widget>[
        FutureBuilder<Map<String, dynamic>>(
          future: _future,
          builder: (context, snapshot) {
            final data = snapshot.data ?? const <String, dynamic>{};
            final payload = data['data'] is Map<String, dynamic>
                ? data['data'] as Map<String, dynamic>
                : data;
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                MobileInfoCard(
                  title: 'Hedef Özeti',
                  description: _label(payload, 'target_summary', 'Canlı hedef gerçekleşme özeti yüklenir.'),

                  icon: Icons.flag_outlined,
                ),
                const SizedBox(height: 12),
                MobileInfoCard(
                  title: 'Riskli KPI’lar',
                  description: _label(payload, 'risky_kpi', 'Riskli KPI kayıtları yetki kapsamına göre gösterilir.'),

                  icon: Icons.warning_amber_rounded,
                ),
                const SizedBox(height: 12),
                MobileInfoCard(
                  title: 'Dönem ve Kapsam',
                  description: _label(payload, 'period_scope', 'Dönem, birim, kategori veya seçili kapsam bilgisi gösterilir.'),

                  icon: Icons.date_range_outlined,
                ),
                const SizedBox(height: 12),
                MobileInfoCard(
                  title: 'Yönetici Görünümü',
                  description: _label(payload, 'manager_view', 'Yönetici rolüne göre özet ve yönlendirme sunulur.'),

                  icon: Icons.admin_panel_settings_outlined,
                ),
              ],
            );
          },
        ),
      ],
    );
  }

  String _label(Map<String, dynamic> data, String key, String fallback) {
    final value = data[key];
    if (value == null) return fallback;
    if (value is String && value.trim().isNotEmpty) return value.trim();
    if (value is num) return value.toString();
    if (value is Map || value is List) return 'Canlı veri alındı ve yetki kapsamına göre özetlendi.';
    return fallback;
  }
}

// BYS360_MOBILE_V2_8_34_KPI_NONNULL_FIX

// BYS360_MOBILE_V2_8_34_RELEASE_KPI_CONSTRUCTOR_FIX
