import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';
import 'performance_scoring_screen.dart';

class PerformanceTasksScreen extends StatefulWidget {
  const PerformanceTasksScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<PerformanceTasksScreen> createState() => _PerformanceTasksScreenState();
}

class _PerformanceTasksScreenState extends State<PerformanceTasksScreen> {
  late Future<_TaskPayload> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<_TaskPayload> _load() async {
    final payload = await widget.apiClient.get('/api/mobile/performance/tasks');
    return _TaskPayload.fromPayload(payload);
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  Future<void> _openTask(_TaskItem task) async {
    if (task.id.isEmpty) return;
    final changed = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => PerformanceScoringScreen(
          apiClient: widget.apiClient,
          assignmentId: task.id,
          taskTitle: task.title,
        ),
      ),
    );
    if (changed == true && mounted) {
      await _refresh();
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_TaskPayload>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const BYSLoadingState(message: 'Puanlama görevleri yükleniyor');
        }
        if (snapshot.hasError) {
          return BYSPage(
            title: 'Değerlendirme Görevlerim',
            subtitle: 'Puanlama ekranı şu anda açılamadı.',
            badge: 'Görevlerim',
            onRefresh: _refresh,
            children: [
              ApiEmptyState(
                title: 'Görevler yüklenemedi',
                message: 'Değerlendirme görevleri şu anda alınamadı. Lütfen tekrar deneyin.',
                onRetry: () => setState(() => _future = _load()),
              ),
            ],
          );
        }

        final payload = snapshot.data ?? _TaskPayload.empty();
        return BYSPage(
          title: 'Değerlendirme Görevlerim',
          subtitle: 'Puan verin, toplu puan uygulayın, taslak kaydedin, tamamlayın, geri çekin veya iade edin.',
          badge: 'Görevlerim',
          onRefresh: _refresh,
          trailing: const Icon(Icons.fact_check_outlined, color: BYS360Colors.corporateRed, size: 48),
          children: [
            const _PremiumScoringIntro(),
            if (payload.metrics.isNotEmpty) ...[
              const BYSSectionTitle(title: 'Görev Özeti', subtitle: 'BYS360 verileriyle güncellenir'),
              ...payload.metrics.take(5).map(
                    (metric) => MetricCard(
                      title: metric.title,
                      value: metric.value,
                      subtitle: metric.subtitle,
                      icon: _metricIcon(metric.icon),
                      tone: _tone(metric.tone),
                    ),
                  ),
            ],
            const BYSSectionTitle(title: 'Puanlanacak Görevler', subtitle: 'Göreve dokunarak puanlama formunu açın'),
            if (payload.tasks.isEmpty)
              const BYSInfoPanel(
                icon: Icons.info_outline,
                title: 'Puanlanacak görev bulunamadı',
                body: 'Bu kullanıcıya atanmış açık değerlendirme görevi oluştuğunda burada görünecek.',
                tint: BYS360Colors.info,
              )
            else
              ...payload.tasks.map((task) => _TaskCard(task: task, onTap: () => _openTask(task))),
            const BYSInfoPanel(
              icon: Icons.verified_user_outlined,
              title: 'Kurumsal kural korunur',
              body: '1-5 puanlama, açıklama zorunlulukları, 70 altı üst onay ve yayın kilidi kuralları mobilde de BYS360 kurallarıyla aynı çalışır.',
            ),
          ],
        );
      },
    );
  }
}

class _PremiumScoringIntro extends StatelessWidget {
  const _PremiumScoringIntro();

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(BYS360Radii.lg),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [BYS360Colors.corporateRed.withValues(alpha: .09), Colors.white],
          ),
        ),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(color: BYS360Colors.corporateRed, borderRadius: BorderRadius.circular(18)),
                  child: const Icon(Icons.stars_outlined, color: Colors.white),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Kolay Puanlama Ekranı', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
                      const SizedBox(height: 3),
                      const Text('Her kriter için tek dokunuşla puan verin veya tüm kriterlere toplu puan uygulayın.'),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            const Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _FeatureChip(label: 'Hepsine 5'),
                _FeatureChip(label: 'Hepsine 4'),
                _FeatureChip(label: 'Hepsine 3'),
                _FeatureChip(label: 'Taslak'),
                _FeatureChip(label: 'Tamamla'),
                _FeatureChip(label: 'Geri Çek / İade'),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _FeatureChip extends StatelessWidget {
  const _FeatureChip({required this.label});
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: BYS360Colors.cardBorder),
      ),
      child: Text(label, style: const TextStyle(color: BYS360Colors.corporateRed, fontWeight: FontWeight.w900, fontSize: 12)),
    );
  }
}

class _TaskCard extends StatelessWidget {
  const _TaskCard({required this.task, required this.onTap});

  final _TaskItem task;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final progress = task.progress.clamp(0, 100);
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(BYS360Radii.lg),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(color: BYS360Colors.softRed, borderRadius: BorderRadius.circular(17)),
                child: const Icon(Icons.rate_review_outlined, color: BYS360Colors.corporateRed),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(task.title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900), maxLines: 2, overflow: TextOverflow.ellipsis),
                    const SizedBox(height: 4),
                    Text(task.subtitle, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText), maxLines: 2, overflow: TextOverflow.ellipsis),
                    if (task.meta.isNotEmpty) ...[
                      const SizedBox(height: 7),
                      Text(task.meta, style: const TextStyle(color: BYS360Colors.subtleText, fontWeight: FontWeight.w700, fontSize: 12)),
                    ],
                    const SizedBox(height: 10),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(999),
                      child: LinearProgressIndicator(value: progress / 100, minHeight: 7, backgroundColor: BYS360Colors.softRed, color: BYS360Colors.corporateRed),
                    ),
                    const SizedBox(height: 9),
                    Wrap(
                      spacing: 8,
                      runSpacing: 6,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        _StatusBadge(text: task.status.isEmpty ? 'Değerlendirme Bekliyor' : task.status),
                        if (task.value.isNotEmpty) _MiniText(text: task.value),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              const Icon(Icons.chevron_right, color: BYS360Colors.mutedText),
            ],
          ),
        ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.text});
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: BYS360Colors.corporateRed.withValues(alpha: .09),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(text, style: const TextStyle(color: BYS360Colors.corporateRed, fontWeight: FontWeight.w900, fontSize: 11)),
    );
  }
}

class _MiniText extends StatelessWidget {
  const _MiniText({required this.text});
  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(text, style: const TextStyle(color: BYS360Colors.mutedText, fontWeight: FontWeight.w800, fontSize: 12));
  }
}

class _TaskPayload {
  const _TaskPayload({required this.metrics, required this.tasks});
  final List<_MetricItem> metrics;
  final List<_TaskItem> tasks;

  factory _TaskPayload.fromPayload(dynamic payload) {
    final map = _asMap(payload);
    return _TaskPayload(
      metrics: _asList(map['metrics']).map(_MetricItem.fromJson).toList(),
      tasks: _asList(map['items']).map(_TaskItem.fromJson).where((item) => item.id.isNotEmpty).toList(),
    );
  }

  factory _TaskPayload.empty() => const _TaskPayload(metrics: [], tasks: []);
}

class _MetricItem {
  const _MetricItem({required this.title, required this.value, required this.subtitle, required this.tone, required this.icon});
  final String title;
  final String value;
  final String subtitle;
  final String tone;
  final String icon;

  factory _MetricItem.fromJson(Map<String, dynamic> json) => _MetricItem(
        title: _text(json, ['title'], 'Özet'),
        value: _text(json, ['value'], '-'),
        subtitle: _text(json, ['subtitle'], ''),
        tone: _text(json, ['tone'], 'red'),
        icon: _text(json, ['icon'], 'assignment'),
      );
}

class _TaskItem {
  const _TaskItem({required this.id, required this.title, required this.subtitle, required this.status, required this.meta, required this.value, required this.progress});
  final String id;
  final String title;
  final String subtitle;
  final String status;
  final String meta;
  final String value;
  final int progress;

  factory _TaskItem.fromJson(Map<String, dynamic> json) => _TaskItem(
        id: _text(json, ['id'], ''),
        title: _text(json, ['title', 'name', 'employee_name'], 'Değerlendirme görevi'),
        subtitle: _text(json, ['subtitle', 'description', 'period_name'], ''),
        status: _performanceTaskStatusLabel(_text(json, ['status_label', 'status', 'state_label', 'state'], '')),
        meta: _text(json, ['meta', 'unit_name'], ''),
        value: _text(json, ['value', 'score'], ''),
        progress: _int(json['progress'], fallback: 40).clamp(0, 100),
      );
}

List<Map<String, dynamic>> _asList(dynamic value) {
  if (value is List) {
    return value.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
  }
  return const <Map<String, dynamic>>[];
}

Map<String, dynamic> _asMap(dynamic value) {
  if (value is Map) return Map<String, dynamic>.from(value);
  return <String, dynamic>{};
}

String _text(Map<String, dynamic> map, List<String> keys, String fallback) {
  for (final key in keys) {
    final value = map[key];
    if (value != null && value.toString().trim().isNotEmpty) return value.toString().trim();
  }
  return fallback;
}

int _int(dynamic value, {required int fallback}) {
  if (value is int) return value;
  if (value is num) return value.toInt();
  return int.tryParse(value?.toString() ?? '') ?? fallback;
}

Color _tone(String value) {
  final key = value.toLowerCase();
  if (key.contains('green') || key.contains('success')) return BYS360Colors.success;
  if (key.contains('yellow') || key.contains('warning')) return BYS360Colors.warning;
  if (key.contains('blue') || key.contains('info')) return BYS360Colors.info;
  if (key.contains('danger')) return BYS360Colors.danger;
  return BYS360Colors.corporateRed;
}

IconData _metricIcon(String value) {
  final key = value.toLowerCase();
  if (key.contains('warning')) return Icons.warning_amber_outlined;
  if (key.contains('check')) return Icons.check_circle_outline;
  if (key.contains('today')) return Icons.today_outlined;
  if (key.contains('timeline')) return Icons.timeline_outlined;
  if (key.contains('people')) return Icons.people_alt_outlined;
  return Icons.assignment_ind_outlined;
}

// BYS360_MOBILE_V2_8_38_NATIVE_SCORING_TASKS_HARD_REPLACE

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION

String _performanceTaskStatusLabel(String value) {
  final raw = value.trim();
  final key = raw.toLowerCase().replaceAll(' ', '_').replaceAll('-', '_');
  const labels = <String, String>{
    'pending': 'Bekliyor',
    'waiting': 'Bekliyor',
    'assigned': 'Atandı',
    'open': 'Açık',
    'draft': 'Taslak',
    'in_progress': 'Devam Ediyor',
    'completed': 'Tamamlandı',
    'done': 'Tamamlandı',
    'tamamlandi': 'Tamamlandı',
    'tamamlandı': 'Tamamlandı',
    'returned': 'İade Edildi',
    'rejected': 'İade Edildi',
    'withdrawn': 'Geri Çekildi',
    'president_pending': 'Başkan Onayı Bekliyor',
    'blocked_president_pending': 'Başkan Onayı Yayın Kilidi',
  };
  if (labels.containsKey(key)) return labels[key]!;
  return raw.isEmpty ? 'Değerlendirme Bekliyor' : raw;
}
