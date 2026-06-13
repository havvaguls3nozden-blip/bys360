// BYS360_MOBILE_V2_8_63A_HISTORY_ARCHIVE_SCREEN
import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';
import '../../core/widgets/record_widgets.dart';
import '../../models/module_data.dart';
import '../../models/mobile_record.dart';

class PerformanceHistoryArchiveScreen extends StatefulWidget {
  const PerformanceHistoryArchiveScreen({super.key, required this.apiClient});
  final ApiClient apiClient;
  @override
  State<PerformanceHistoryArchiveScreen> createState() => _PerformanceHistoryArchiveScreenState();
}

class _PerformanceHistoryArchiveScreenState extends State<PerformanceHistoryArchiveScreen> {
  late Future<ModuleData> _future;
  @override
  void initState() { super.initState(); _future = _load(); }
  Future<ModuleData> _load() async {
    final payload = await widget.apiClient.get('/api/mobile/performance/history-archive');
    if (payload is! Map) throw StateError('Geçmiş karne arşivi şu anda okunamadı.');
    return ModuleData.fromJson(Map<String, dynamic>.from(payload));
  }
  Future<void> _refresh() async { setState(() => _future = _load()); await _future; }
  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ModuleData>(future: _future, builder: (context, snapshot) {
      if (snapshot.connectionState == ConnectionState.waiting) return const BYSLoadingState(message: 'Geçmiş karne arşivi yükleniyor');
      if (snapshot.hasError) {
        return BYSPage(title: 'Geçmiş Karne Arşivi', subtitle: 'Geçmiş performans kayıtlarına şu anda ulaşılamadı.', badge: 'Arşiv', onRefresh: _refresh, trailing: const Icon(Icons.archive_outlined, color: BYS360Colors.purple, size: 52), children: <Widget>[
          ApiEmptyState(message: 'Geçmiş karne arşivi şu anda alınamadı. Lütfen tekrar deneyin.', onRetry: () => setState(() => _future = _load())),
        ]);
      }
      final data = snapshot.data ?? const ModuleData(metrics: <ModuleMetric>[], items: <MobileRecord>[]);
      return BYSPage(title: 'Geçmiş Karne Arşivi', subtitle: 'Yayınlanmış geçmiş performans karneleri ve eski dönem puanları burada izlenir.', badge: 'Arşiv', onRefresh: _refresh, trailing: const Icon(Icons.archive_outlined, color: BYS360Colors.purple, size: 52), children: <Widget>[
        const BYSInfoPanel(icon: Icons.lock_outline, title: 'Yetki kontrollü arşiv', body: 'Personel yalnızca kendi yayınlanmış geçmişini görür. Yönetici ve yetkili kullanıcılar yalnızca yetki kapsamındaki arşiv kayıtlarını görüntüler.', tint: BYS360Colors.purple),
        if (data.metrics.isNotEmpty) ...<Widget>[
          const BYSSectionTitle(title: 'Arşiv özeti', subtitle: 'Yetki kapsamındaki geçmiş kayıtlar'),
          ...data.metrics.map((metric) => MetricCard(title: metric.title, value: metric.value, subtitle: metric.subtitle, icon: _icon(metric.icon), tone: _tone(metric.tone))),
        ],
        const BYSSectionTitle(title: 'Karne arşivi', subtitle: 'Yıl, dönem ve puan bilgileri'),
        if (data.items.isEmpty)
          const BYSInfoPanel(icon: Icons.info_outline, title: 'Arşiv kaydı bulunmadı', body: 'Yayınlanmış geçmiş karne veya eski dönem puanı oluştuğunda bu alanda görünecek.', tint: BYS360Colors.info)
        else
          ...data.items.map((record) => RecordCard(record: record, icon: _icon(record.icon ?? 'archive'), tone: _tone(record.tone ?? 'purple'))),
      ]);
    });
  }
}

Color _tone(String tone) {
  switch (tone.toLowerCase()) {
    case 'green': case 'success': return BYS360Colors.success;
    case 'yellow': case 'warning': return BYS360Colors.warning;
    case 'blue': case 'info': return BYS360Colors.info;
    case 'purple': return BYS360Colors.purple;
    case 'danger': return BYS360Colors.danger;
    default: return BYS360Colors.corporateRed;
  }
}
IconData _icon(String icon) {
  switch (icon.toLowerCase()) {
    case 'archive': return Icons.archive_outlined;
    case 'scorecard': case 'card': return Icons.assignment_turned_in_outlined;
    case 'shield': case 'lock': return Icons.lock_outline;
    case 'report': return Icons.bar_chart_outlined;
    default: return Icons.history_outlined;
  }
}
