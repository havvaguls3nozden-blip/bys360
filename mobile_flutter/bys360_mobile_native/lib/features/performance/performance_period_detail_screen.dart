import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';
import '../../core/widgets/record_widgets.dart';
import '../../models/module_data.dart';

class PerformancePeriodDetailScreen extends StatefulWidget {
  const PerformancePeriodDetailScreen({super.key, required this.apiClient, required this.periodId, required this.title});

  final ApiClient apiClient;
  final String periodId;
  final String title;

  @override
  State<PerformancePeriodDetailScreen> createState() => _PerformancePeriodDetailScreenState();
}

class _PerformancePeriodDetailScreenState extends State<PerformancePeriodDetailScreen> {
  late Future<ModuleData> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<ModuleData> _load() async {
    final payload = await widget.apiClient.get('/api/mobile/performance/periods/${widget.periodId}');
    if (payload is! Map) throw StateError('Dönem detayı şu anda okunamadı.');
    return ModuleData.fromJson(Map<String, dynamic>.from(payload));
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ModuleData>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator());
        if (snapshot.hasError) {
          return BYSPage(
            title: 'Dönem Detayı',
            subtitle: 'Dönem detayına şu anda ulaşılamadı.',
            badge: 'Dönem',
            onRefresh: _refresh,
            children: [ApiEmptyState(message: 'Bu sayfaya şu anda ulaşılamadı. Lütfen tekrar deneyin.', onRetry: () => setState(() => _future = _load()))],
          );
        }

        final data = snapshot.data ?? const ModuleData(metrics: [], items: []);
        return BYSPage(
          title: widget.title,
          subtitle: 'Döneme ait görev, karne ve takip özetleri yetki sınırınıza göre gösterilir.',
          badge: 'Dönem Detayı',
          onRefresh: _refresh,
          children: [
            const ModuleIntroCard(
              icon: Icons.event_note_outlined,
              title: 'Dönem işlem özeti',
              body: 'Görev, tamamlanma, düşük performans ve karne durumu bu ekranda birlikte izlenir.',
            ),
            const BYSInfoPanel(
              icon: Icons.lock_outline,
              title: 'Görünürlük sınırı',
              body: 'Bu ekranda yalnızca yetkiniz kapsamındaki dönem, görev ve karne kayıtları gösterilir.',
            ),
            const BYSSectionTitle(title: 'Dönem göstergeleri', subtitle: 'Görev ve karne özeti'),
            if (data.metrics.isEmpty)
              const BYSInfoPanel(icon: Icons.info_outline, title: 'Özet bulunamadı', body: 'Bu dönem için gösterilecek özet bulunamadı.')
            else
              ...data.metrics.map((metric) => MetricCard(
                    title: metric.title,
                    value: metric.value,
                    subtitle: metric.subtitle,
                    icon: _icon(metric.icon),
                    tone: _tone(metric.tone),
                  )),
            const BYSSectionTitle(title: 'Dönem kayıtları', subtitle: 'Görev, dönem bilgisi ve karne özetleri'),
            if (data.items.isEmpty)
              const BYSInfoPanel(icon: Icons.inbox_outlined, title: 'Kayıt bulunamadı', body: 'Bu dönem için yetkiniz kapsamında kayıt bulunamadı.')
            else
              ...data.items.map((record) => RecordCard(record: record, icon: Icons.assignment_outlined)),
          ],
        );
      },
    );
  }

  Color _tone(String value) {
    switch (value.toLowerCase()) {
      case 'green':
      case 'success':
        return BYS360Colors.success;
      case 'yellow':
      case 'warning':
        return BYS360Colors.warning;
      case 'blue':
      case 'info':
        return BYS360Colors.info;
      default:
        return BYS360Colors.corporateRed;
    }
  }

  IconData _icon(String value) {
    switch (value.toLowerCase()) {
      case 'assignment':
        return Icons.assignment_outlined;
      case 'check':
        return Icons.check_circle_outline;
      case 'warning':
        return Icons.warning_amber_outlined;
      case 'verified_user':
        return Icons.verified_user_outlined;
      case 'trending_up':
        return Icons.trending_up;
      case 'timeline':
        return Icons.timeline_outlined;
      default:
        return Icons.insights_outlined;
    }
  }
}

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION
