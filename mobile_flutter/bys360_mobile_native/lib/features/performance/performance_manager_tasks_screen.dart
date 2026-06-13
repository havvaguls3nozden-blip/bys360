
import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';
import '../../core/widgets/record_widgets.dart';
import '../../models/module_data.dart';

class PerformanceManagerTasksScreen extends StatefulWidget {
  const PerformanceManagerTasksScreen({super.key, required this.apiClient});
  final ApiClient apiClient;
  @override
  State<PerformanceManagerTasksScreen> createState() => _PerformanceManagerTasksScreenState();
}

class _PerformanceManagerTasksScreenState extends State<PerformanceManagerTasksScreen> {
  late Future<ModuleData> _future;
  @override
  void initState() { super.initState(); _future = _load(); }
  Future<ModuleData> _load() async { final payload = await widget.apiClient.get('/api/mobile/performance/manager-tasks'); if (payload is! Map) throw StateError('Amir görev listesi şu anda okunamadı.'); return ModuleData.fromJson(Map<String, dynamic>.from(payload)); }
  Future<void> _refresh() async { setState(() => _future = _load()); await _future; }
  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ModuleData>(future: _future, builder: (context, snapshot) {
      if (snapshot.connectionState == ConnectionState.waiting) return const BYSLoadingState(message: 'Amir görevleri yükleniyor');
      if (snapshot.hasError) return BYSPage(title: 'Amir Görev Takibi', subtitle: 'Amir görev listesine şu anda ulaşılamadı.', badge: 'Görev Takibi', onRefresh: _refresh, children: [ApiEmptyState(message: 'Amir görevleri şu anda alınamadı. Lütfen tekrar deneyin.', onRetry: () => setState(() => _future = _load()))]);
      final data = snapshot.data ?? const ModuleData(metrics: [], items: []);
      return BYSPage(title: 'Amir Görev Takibi', subtitle: 'Bekleyen ve geciken değerlendirme görevlerini takip edin.', badge: 'Görev Takibi', onRefresh: _refresh, children: [
        const BYSSectionTitle(title: 'Genel durum', subtitle: 'Yetkiniz kapsamındaki amir görev özeti'),
        if (data.metrics.isEmpty) const BYSInfoPanel(icon: Icons.info_outline, title: 'Özet bulunamadı', body: 'Amir görev takibi için özet bilgi bulunamadı.') else ...data.metrics.map((metric) => MetricCard(title: metric.title, value: metric.value, subtitle: metric.subtitle, icon: _icon(metric.icon), tone: _tone(metric.tone))),
        const BYSSectionTitle(title: 'Amirler', subtitle: 'Geciken ve bekleyen görev durumları'),
        if (data.items.isEmpty) const BYSInfoPanel(icon: Icons.lock_outline, title: 'Kayıt bulunamadı', body: 'Bu ekran için gösterilecek amir görev kaydı bulunmuyor veya yetkiniz sınırlı.', tint: BYS360Colors.info) else ...data.items.map((record) => RecordCard(record: record, icon: Icons.manage_accounts_outlined, tone: _recordTone(record.status))),
      ]);
    });
  }
  // ignore: unused_element
  String _cleanError(Object? error) { final text = error?.toString() ?? ''; if (text.contains('403')) return 'Bu işlem için yetkiniz bulunmamaktadır.'; return 'Bu sayfaya şu anda ulaşılamadı. Lütfen tekrar deneyin.'; }
  Color _recordTone(String? status) { final key = (status ?? '').toLowerCase(); if (key.contains('kritik')) return BYS360Colors.warning; if (key.contains('dikkat')) return BYS360Colors.purple; if (key.contains('normal')) return BYS360Colors.success; return BYS360Colors.corporateRed; }
  Color _tone(String tone) { switch (tone.toLowerCase()) { case 'green': case 'success': return BYS360Colors.success; case 'yellow': case 'warning': return BYS360Colors.warning; case 'blue': case 'info': return BYS360Colors.info; case 'purple': return BYS360Colors.purple; default: return BYS360Colors.corporateRed; } }
  IconData _icon(String icon) { switch (icon.toLowerCase()) { case 'people': return Icons.groups_outlined; case 'warning': return Icons.warning_amber_outlined; case 'assignment': return Icons.assignment_ind_outlined; case 'schedule': return Icons.schedule_outlined; case 'lock': return Icons.lock_outline; default: return Icons.manage_accounts_outlined; } }
}

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION

// BYS360_MOBILE_V2_8_68_QUALITY_CLEANUP
