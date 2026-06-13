// BYS360_MOBILE_V2_8_63A_NOTE_SCORECARD_SCREEN
import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';
import '../../core/widgets/record_widgets.dart';
import '../../models/module_data.dart';
import '../../models/mobile_record.dart';

class PerformanceNoteScorecardScreen extends StatefulWidget {
  const PerformanceNoteScorecardScreen({super.key, required this.apiClient});
  final ApiClient apiClient;
  @override
  State<PerformanceNoteScorecardScreen> createState() => _PerformanceNoteScorecardScreenState();
}

class _PerformanceNoteScorecardScreenState extends State<PerformanceNoteScorecardScreen> {
  late Future<ModuleData> _future;
  @override
  void initState() { super.initState(); _future = _load(); }
  Future<ModuleData> _load() async {
    final payload = await widget.apiClient.get('/api/mobile/performance/note-scorecard');
    if (payload is! Map) throw StateError('Not karnesi şu anda okunamadı.');
    return ModuleData.fromJson(Map<String, dynamic>.from(payload));
  }
  Future<void> _refresh() async { setState(() => _future = _load()); await _future; }
  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ModuleData>(future: _future, builder: (context, snapshot) {
      if (snapshot.connectionState == ConnectionState.waiting) return const BYSLoadingState(message: 'Not karnesi yükleniyor');
      if (snapshot.hasError) {
        return BYSPage(title: 'Not Karnesi', subtitle: 'Karne detayına açılan notlara şu anda ulaşılamadı.', badge: 'Not Karnesi', onRefresh: _refresh, trailing: const Icon(Icons.sticky_note_2_outlined, color: BYS360Colors.warning, size: 52), children: <Widget>[
          ApiEmptyState(message: 'Not karnesi şu anda alınamadı. Lütfen tekrar deneyin.', onRetry: () => setState(() => _future = _load())),
        ]);
      }
      final data = snapshot.data ?? const ModuleData(metrics: <ModuleMetric>[], items: <MobileRecord>[]);
      return BYSPage(title: 'Not Karnesi', subtitle: 'Karne detayında gösterilmek üzere işaretlenen dönem içi notlar burada izlenir.', badge: 'Not Karnesi', onRefresh: _refresh, trailing: const Icon(Icons.sticky_note_2_outlined, color: BYS360Colors.warning, size: 52), children: <Widget>[
        const BYSInfoPanel(icon: Icons.info_outline, title: 'Puan değildir', body: 'Not karnesi performans puanını otomatik değiştirmez. Yalnızca karneye açılması uygun görülen ara gözlem ve gelişim notlarını gösterir.', tint: BYS360Colors.warning),
        if (data.metrics.isNotEmpty) ...<Widget>[
          const BYSSectionTitle(title: 'Not karnesi özeti', subtitle: 'Karneye açılan notlar'),
          ...data.metrics.map((metric) => MetricCard(title: metric.title, value: metric.value, subtitle: metric.subtitle, icon: _icon(metric.icon), tone: _tone(metric.tone))),
        ],
        const BYSSectionTitle(title: 'Karneye açılan notlar', subtitle: 'Yalnızca yetki kapsamındaki kayıtlar'),
        if (data.items.isEmpty)
          const BYSInfoPanel(icon: Icons.info_outline, title: 'Not karnesi kaydı bulunmadı', body: 'Dönem içi not eklerken “Karne detayında gösterilsin” işaretlenen kayıtlar burada görünecek.', tint: BYS360Colors.info)
        else
          ...data.items.map((record) => RecordCard(record: record, icon: _icon(record.icon ?? 'scorecard'), tone: _tone(record.tone ?? 'warning'))),
      ]);
    });
  }
}

Color _tone(String tone) {
  switch (tone.toLowerCase()) {
    case 'green': case 'success': return BYS360Colors.success;
    case 'blue': case 'info': return BYS360Colors.info;
    case 'purple': return BYS360Colors.purple;
    case 'danger': return BYS360Colors.danger;
    case 'yellow': case 'warning': default: return BYS360Colors.warning;
  }
}
IconData _icon(String icon) {
  switch (icon.toLowerCase()) {
    case 'note': return Icons.edit_note_outlined;
    case 'scorecard': case 'card': return Icons.sticky_note_2_outlined;
    case 'shield': case 'lock': return Icons.lock_outline;
    case 'warning': return Icons.warning_amber_rounded;
    default: return Icons.sticky_note_2_outlined;
  }
}
