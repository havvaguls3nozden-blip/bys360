// BYS360_MOBILE_V2_8_52_PERFORMANCE_WEB_PARITY_GENERIC_LIST
import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';
import '../../core/widgets/record_widgets.dart';
import '../../models/module_data.dart';

class PerformanceFeatureListScreen extends StatefulWidget {
  const PerformanceFeatureListScreen({
    super.key,
    required this.apiClient,
    required this.path,
    required this.title,
    required this.subtitle,
    required this.badge,
    required this.icon,
    this.tone = BYS360Colors.corporateRed,
    this.emptyMessage = 'Bu ekran için gösterilecek kayıt bulunmadı.',
    this.detailPathPrefix,
  });

  final ApiClient apiClient;
  final String path;
  final String title;
  final String subtitle;
  final String badge;
  final IconData icon;
  final Color tone;
  final String emptyMessage;
  final String? detailPathPrefix;

  @override
  State<PerformanceFeatureListScreen> createState() => _PerformanceFeatureListScreenState();
}

class _PerformanceFeatureListScreenState extends State<PerformanceFeatureListScreen> {
  late Future<ModuleData> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<ModuleData> _load() async {
    final payload = await widget.apiClient.get(widget.path);
    if (payload is! Map) throw StateError('Bu performans ekranı şu anda okunamadı.');
    return ModuleData.fromJson(Map<String, dynamic>.from(payload));
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  void _openDetail(String id) {
    final prefix = widget.detailPathPrefix;
    if (prefix == null || prefix.trim().isEmpty || id.trim().isEmpty) return;
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => PerformanceFeatureDetailScreen(
        apiClient: widget.apiClient,
        path: '$prefix/$id',
        title: '${widget.title} Detayı',
        badge: widget.badge,
        icon: widget.icon,
        tone: widget.tone,
      ),
    ));
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ModuleData>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const BYSLoadingState(message: 'Performans verileri yükleniyor');
        }
        if (snapshot.hasError) {
          return BYSPage(
            title: widget.title,
            subtitle: 'Bu performans alanına şu anda ulaşılamadı.',
            badge: widget.badge,
            onRefresh: _refresh,
            trailing: Icon(widget.icon, color: widget.tone, size: 48),
            children: [
              ApiEmptyState(
                title: 'Ekran yüklenemedi',
                message: 'Bu performans ekranına şu anda ulaşılamadı. Lütfen tekrar deneyin.',
                onRetry: () => setState(() => _future = _load()),
              ),
            ],
          );
        }

        final data = snapshot.data ?? const ModuleData(metrics: [], items: []);
        return BYSPage(
          title: widget.title,
          subtitle: widget.subtitle,
          badge: widget.badge,
          onRefresh: _refresh,
          trailing: Icon(widget.icon, color: widget.tone, size: 48),
          children: [
            if (data.metrics.isNotEmpty) ...[
              const BYSSectionTitle(title: 'Özet', subtitle: 'Yetki kapsamınıza göre BYS360 verisi'),
              ...data.metrics.map((metric) => MetricCard(
                    title: metric.title,
                    value: metric.value,
                    subtitle: metric.subtitle,
                    icon: _icon(metric.icon),
                    tone: _tone(metric.tone),
                  )),
            ],
            const BYSSectionTitle(title: 'Kayıtlar', subtitle: 'BYS360 performans verileriyle eşleşir'),
            if (data.items.isEmpty)
              BYSInfoPanel(
                icon: Icons.info_outline,
                title: 'Kayıt bulunmadı',
                body: widget.emptyMessage,
                tint: BYS360Colors.info,
              )
            else
              ...data.items.map((record) => RecordCard(
                    record: record,
                    icon: _icon(record.icon ?? ''),
                    tone: _tone(record.tone ?? '') == BYS360Colors.corporateRed ? widget.tone : _tone(record.tone ?? ''),
                    onTap: widget.detailPathPrefix == null ? null : () => _openDetail(record.id),
                  )),
            const BYSInfoPanel(
              icon: Icons.shield_outlined,
              title: 'Yetki ve görünürlük sınırı',
              body: 'Bu ekran BYS360 yetki ve veri görünürlüğü kurallarıyla çalışır. Yetkisiz performans puanı, karne veya hassas görüş gösterilmez.',
            ),
          ],
        );
      },
    );
  }
}

class PerformanceFeatureDetailScreen extends StatefulWidget {
  const PerformanceFeatureDetailScreen({
    super.key,
    required this.apiClient,
    required this.path,
    required this.title,
    required this.badge,
    required this.icon,
    required this.tone,
  });

  final ApiClient apiClient;
  final String path;
  final String title;
  final String badge;
  final IconData icon;
  final Color tone;

  @override
  State<PerformanceFeatureDetailScreen> createState() => _PerformanceFeatureDetailScreenState();
}

class _PerformanceFeatureDetailScreenState extends State<PerformanceFeatureDetailScreen> {
  late Future<ModuleData> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<ModuleData> _load() async {
    final payload = await widget.apiClient.get(widget.path);
    if (payload is! Map) throw StateError('Detay bilgisi şu anda okunamadı.');
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
        if (snapshot.connectionState == ConnectionState.waiting) return const BYSLoadingState(message: 'Detay yükleniyor');
        if (snapshot.hasError) {
          return BYSPage(
            title: widget.title,
            subtitle: 'Detay bilgisine şu anda ulaşılamadı.',
            badge: widget.badge,
            onRefresh: _refresh,
            trailing: Icon(widget.icon, color: widget.tone, size: 48),
            children: [ApiEmptyState(message: 'Bu performans ekranına şu anda ulaşılamadı. Lütfen tekrar deneyin.', onRetry: () => setState(() => _future = _load()))],
          );
        }
        final data = snapshot.data ?? const ModuleData(metrics: [], items: []);
        return BYSPage(
          title: widget.title,
          subtitle: 'Seçili kaydın yetki kapsamındaki detay bilgisi.',
          badge: widget.badge,
          onRefresh: _refresh,
          trailing: Icon(widget.icon, color: widget.tone, size: 48),
          children: [
            if (data.metrics.isNotEmpty) ...data.metrics.map((metric) => MetricCard(title: metric.title, value: metric.value, subtitle: metric.subtitle, icon: _icon(metric.icon), tone: _tone(metric.tone))),
            if (data.items.isEmpty)
              const BYSInfoPanel(icon: Icons.info_outline, title: 'Detay bulunmadı', body: 'Bu kayıt için gösterilecek ek detay bulunmadı.', tint: BYS360Colors.info)
            else
              ...data.items.map((record) => RecordCard(record: record, icon: _icon(record.icon ?? ''), tone: _tone(record.tone ?? '') == BYS360Colors.corporateRed ? widget.tone : _tone(record.tone ?? ''))),
          ],
        );
      },
    );
  }
}

Color _tone(String tone) {
  switch (tone.toLowerCase()) {
    case 'green':
    case 'success':
      return BYS360Colors.success;
    case 'yellow':
    case 'warning':
      return BYS360Colors.warning;
    case 'blue':
    case 'info':
      return BYS360Colors.info;
    case 'purple':
      return BYS360Colors.purple;
    case 'danger':
    case 'red-danger':
      return BYS360Colors.danger;
    default:
      return BYS360Colors.corporateRed;
  }
}

IconData _icon(String icon) {
  switch (icon.toLowerCase()) {
    case 'timeline':
    case 'period':
      return Icons.timeline_outlined;
    case 'assignment':
    case 'task':
      return Icons.assignment_ind_outlined;
    case 'scorecard':
    case 'card':
      return Icons.assignment_turned_in_outlined;
    case 'verified_user':
    case 'approval':
      return Icons.verified_user_outlined;
    case 'warning':
    case 'risk':
      return Icons.warning_amber_rounded;
    case 'rule':
    case 'criteria':
      return Icons.rule_folder_outlined;
    case 'scale':
    case 'weight':
      return Icons.scale_outlined;
    case 'people':
    case 'category':
      return Icons.groups_outlined;
    case 'archive':
      return Icons.archive_outlined;
    case 'note':
    case 'edit_note':
      return Icons.edit_note_outlined;
    case 'development':
    case 'school':
      return Icons.school_outlined;
    case 'report':
      return Icons.bar_chart_outlined;
    case 'reminder':
    case 'schedule':
      return Icons.notifications_active_outlined;
    case 'dashboard':
      return Icons.dashboard_customize_outlined;
    case 'shield':
      return Icons.shield_outlined;
    case 'lock':
      return Icons.lock_outline;
    default:
      return Icons.insights_outlined;
  }
}

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION
