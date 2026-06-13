import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';
import '../../core/widgets/record_widgets.dart';
import '../../models/mobile_record.dart';
import 'performance_mobile_p1_models.dart';
import 'performance_scoring_form_screen.dart';

class PerformanceP1ListScreen extends StatefulWidget {
  const PerformanceP1ListScreen({
    super.key,
    required this.apiClient,
    required this.path,
    required this.title,
    required this.subtitle,
    required this.badge,
    required this.icon,
    required this.tone,
    this.detailTitle,
    this.detailPathPrefix,
    this.emptyMessage,
  });

  final ApiClient apiClient;
  final String path;
  final String title;
  final String subtitle;
  final String badge;
  final IconData icon;
  final Color tone;
  final String? detailTitle;
  final String? detailPathPrefix;
  final String? emptyMessage;

  @override
  State<PerformanceP1ListScreen> createState() => _PerformanceP1ListScreenState();
}

class _PerformanceP1ListScreenState extends State<PerformanceP1ListScreen> {
  late Future<List<MobilePerformanceRecord>> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<List<MobilePerformanceRecord>> _load() async {
    final payload = await widget.apiClient.get(widget.path);
    return bys360ExtractList(payload).map((item) => MobilePerformanceRecord.fromJson(item, fallbackTitle: widget.title)).toList();
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  void _openDetail(MobilePerformanceRecord record) {
    final prefix = widget.detailPathPrefix;
    if (prefix == null || prefix.isEmpty || record.id.isEmpty) return;
    if (prefix.endsWith('/performance/tasks')) {
      Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => PerformanceScoringFormScreen(
          apiClient: widget.apiClient,
          assignmentId: record.id,
          seed: record,
        ),
      ));
      return;
    }
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => PerformanceP1DetailScreen(
        apiClient: widget.apiClient,
        path: '$prefix/${record.id}',
        title: widget.detailTitle ?? record.title,
        subtitle: record.subtitle,
        badge: widget.badge,
        icon: widget.icon,
        tone: widget.tone,
        seed: record,
      ),
    ));
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<MobilePerformanceRecord>>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return const BYSLoadingState();
        if (snapshot.hasError) {
          return BYSPage(
            title: widget.title,
            subtitle: 'Bu performans ekranına şu anda ulaşılamadı.',
            badge: widget.badge,
            onRefresh: _refresh,
            children: [ApiEmptyState(message: 'Performans kaydı şu anda alınamadı. Lütfen tekrar deneyin.', onRetry: () => setState(() => _future = _load()))],
          );
        }
        final records = snapshot.data ?? const <MobilePerformanceRecord>[];
        return BYSPage(
          title: widget.title,
          subtitle: widget.subtitle,
          badge: widget.badge,
          onRefresh: _refresh,
          children: [
            _PerformanceP1HeaderCard(title: widget.title, count: records.length, icon: widget.icon, tone: widget.tone),
            if (records.isEmpty)
              BYSInfoPanel(
                icon: Icons.info_outline,
                title: 'Kayıt bulunamadı',
                body: widget.emptyMessage ?? 'Bu alanda görüntülenecek performans kaydı bulunamadı.',
              )
            else
              ...records.map((record) => RecordCard(
                    record: MobileRecord(
                      id: record.id.isNotEmpty ? record.id : record.title,
                      title: record.title,
                      subtitle: record.subtitle,
                      value: record.value,
                      status: record.status,
                      meta: record.meta,
                      progress: record.progress == null ? null : (record.progress! * 100).round().clamp(0, 100),
                    ),
                    icon: widget.icon,
                    tone: widget.tone,
                    onTap: widget.detailPathPrefix == null ? null : () => _openDetail(record),
                  )),
            const BYSInfoPanel(
              icon: Icons.shield_outlined,
              title: 'Yetki kontrollü görünüm',
              body: 'Bu ekran yalnızca BYS360’da yetkiniz olan performans kayıtlarını gösterir. Rol ve görünürlük kuralları mobilde de korunur.',
            ),
          ],
        );
      },
    );
  }
}

class PerformanceP1DetailScreen extends StatefulWidget {
  const PerformanceP1DetailScreen({
    super.key,
    required this.apiClient,
    required this.path,
    required this.title,
    required this.subtitle,
    required this.badge,
    required this.icon,
    required this.tone,
    this.seed,
  });

  final ApiClient apiClient;
  final String path;
  final String title;
  final String subtitle;
  final String badge;
  final IconData icon;
  final Color tone;
  final MobilePerformanceRecord? seed;

  @override
  State<PerformanceP1DetailScreen> createState() => _PerformanceP1DetailScreenState();
}

class _PerformanceP1DetailScreenState extends State<PerformanceP1DetailScreen> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<Map<String, dynamic>> _load() async {
    final payload = await widget.apiClient.get(widget.path);
    final detail = bys360ExtractMap(payload);
    if (detail.isEmpty && widget.seed != null) return widget.seed!.raw;
    return detail;
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return const BYSLoadingState();
        if (snapshot.hasError) {
          return BYSPage(
            title: widget.title,
            subtitle: 'Detay bilgisi şu anda alınamadı.',
            badge: widget.badge,
            onRefresh: _refresh,
            children: [ApiEmptyState(message: 'Performans kaydı şu anda alınamadı. Lütfen tekrar deneyin.', onRetry: () => setState(() => _future = _load()))],
          );
        }
        final data = snapshot.data ?? widget.seed?.raw ?? <String, dynamic>{};
        final title = bys360Text(data, ['title', 'name', 'employee_name', 'employeeName', 'period_name', 'periodName'], widget.title);
        final status = bys360PerformanceStatusLabel(bys360Text(data, ['status_label', 'statusLabel', 'state_label', 'stateLabel', 'status'], widget.seed?.status ?? 'Takipte'));
        final score = bys360Text(data, ['final_score', 'finalScore', 'score', 'value'], widget.seed?.value ?? '');
        final period = bys360Text(data, ['period', 'period_name', 'periodName', 'date_range', 'dateRange'], widget.seed?.meta ?? '');
        final description = bys360Text(data, ['description', 'summary', 'general_comment', 'generalComment', 'note'], widget.subtitle);
        final criteria = bys360ExtractList(data['criteria'] ?? data['items'] ?? data['scores']);
        final history = bys360ExtractList(data['history'] ?? data['timeline'] ?? data['süreç']);

        return BYSPage(
          title: title,
          subtitle: description,
          badge: widget.badge,
          onRefresh: _refresh,
          children: [
            _PerformanceP1HeaderCard(title: status, count: score.isEmpty ? 0 : 1, icon: widget.icon, tone: widget.tone, valueOverride: score.isEmpty ? null : score),
            if (period.isNotEmpty) _InfoLineCard(icon: Icons.date_range_outlined, title: 'Dönem bilgisi', value: period, tone: BYS360Colors.info),
            _InfoLineCard(icon: Icons.verified_outlined, title: 'Süreç durumu', value: status, tone: widget.tone),
            if (criteria.isNotEmpty) ...[
              const BYSSectionTitle(title: 'Değerlendirme detayları', subtitle: 'Kriter ve puan bilgileri'),
              ...criteria.map((item) {
                final map = Map<String, dynamic>.from(item);
                final itemTitle = bys360Text(map, ['title', 'name', 'criterion', 'criterion_name', 'criterionName'], 'Değerlendirme kriteri');
                final itemValue = bys360Text(map, ['score', 'value', 'point', 'rate'], '');
                final itemStatus = bys360Text(map, ['comment', 'description', 'status'], 'Kayıtlı değerlendirme detayı');
                return _InfoLineCard(icon: Icons.rule_folder_outlined, title: itemTitle, value: itemValue.isEmpty ? itemStatus : '$itemValue • $itemStatus', tone: BYS360Colors.corporateRed);
              }),
            ],
            if (history.isNotEmpty) ...[
              const BYSSectionTitle(title: 'Süreç geçmişi', subtitle: 'İşlem ve onay akışı'),
              ...history.map((item) {
                final map = Map<String, dynamic>.from(item);
                return _InfoLineCard(
                  icon: Icons.history_outlined,
                  title: bys360PerformanceStatusLabel(bys360Text(map, ['title', 'action', 'status', 'state'], 'Süreç kaydı')),
                  value: bys360Text(map, ['description', 'note', 'created_at', 'createdAt', 'date'], 'Kayıt bilgisi'),
                  tone: BYS360Colors.info,
                );
              }),
            ],
            const BYSInfoPanel(
              icon: Icons.lock_outline,
              title: 'Hassas veri sınırı',
              body: 'Mobil detay ekranı yalnızca yetkiniz dahilindeki performans bilgisini gösterir. Yayınlanmamış karne ve yetkisiz puan bilgileri açılmamalıdır.',
            ),
          ],
        );
      },
    );
  }
}

class _PerformanceP1HeaderCard extends StatelessWidget {
  const _PerformanceP1HeaderCard({required this.title, required this.count, required this.icon, required this.tone, this.valueOverride});

  final String title;
  final int count;
  final IconData icon;
  final Color tone;
  final String? valueOverride;

  @override
  Widget build(BuildContext context) {
    return MetricCard(
      title: title,
      value: valueOverride ?? '$count',
      subtitle: valueOverride == null ? 'BYS360 verileriyle güncellenen mobil performans görünümü' : 'Yetki kontrollü performans sonucu',
      icon: icon,
      tone: tone,
    );
  }
}

class _InfoLineCard extends StatelessWidget {
  const _InfoLineCard({required this.icon, required this.title, required this.value, required this.tone});

  final IconData icon;
  final String title;
  final String value;
  final Color tone;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(color: tone.withValues(alpha: .10), borderRadius: BorderRadius.circular(14)),
              child: Icon(icon, color: tone, size: 21),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900), maxLines: 2, overflow: TextOverflow.ellipsis),
                  const SizedBox(height: 4),
                  Text(value, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText, height: 1.28)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// BYS360_MOBILE_V2_8_27_PERFORMANCE_P1 shared widgets

// BYS360_MOBILE_V2_8_27_PERFORMANCE_P1_BUILDFIX

// BYS360_MOBILE_V2_8_35_PERFORMANCE_SCORING_NAV

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION
