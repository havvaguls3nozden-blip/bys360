// BYS360_MOBILE_V2_8_66_SURVEY_COMPLETION
import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys360_logo.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';
import '../../core/widgets/record_widgets.dart';
import '../../models/mobile_record.dart';
import '../../models/module_data.dart';
import 'survey_detail_screen.dart';

class SurveysScreen extends StatefulWidget {
  const SurveysScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<SurveysScreen> createState() => _SurveysScreenState();
}

class _SurveysScreenState extends State<SurveysScreen> {
  late Future<ModuleData> _future;
  _SurveyFilter _filter = _SurveyFilter.all;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<ModuleData> _load() async {
    final payload = await widget.apiClient.get('/api/mobile/surveys');
    if (payload is! Map) {
      throw StateError('Anket bilgileri beklenen biçimde alınamadı.');
    }
    return ModuleData.fromJson(Map<String, dynamic>.from(payload));
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  Future<void> _openDetail(MobileRecord record) async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => SurveyDetailScreen(
          apiClient: widget.apiClient,
          surveyId: record.id,
          fallbackTitle: record.title,
        ),
      ),
    );
    if (mounted) {
      setState(() => _future = _load());
    }
  }

  List<MobileRecord> _filteredItems(List<MobileRecord> items) {
    if (_filter == _SurveyFilter.all) return items;
    return items.where((item) {
      final status = (item.status ?? '').toLowerCase();
      final progress = item.progress ?? 0;
      final completed = status.contains('cevaplandı') || status.contains('tamamlandı') || progress >= 100;
      if (_filter == _SurveyFilter.waiting) return !completed;
      return completed;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ModuleData>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return BYSPage(
            title: 'Anketlerim',
            subtitle: 'Anket bilgileri şu anda alınamadı.',
            badge: 'Anket',
            onRefresh: _refresh,
            children: [
              ApiEmptyState(
                message: snapshot.error.toString(),
                onRetry: () => setState(() => _future = _load()),
              ),
            ],
          );
        }

        final data = snapshot.data ?? const ModuleData(metrics: [], items: []);
        final items = _filteredItems(data.items);
        return BYSPage(
          title: 'Anketlerim',
          subtitle: 'Size atanan anketleri görüntüleyin ve cevaplarınızı güvenli şekilde gönderin.',
          badge: 'Anket',
          onRefresh: _refresh,
          trailing: Container(
            width: 76,
            height: 66,
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
            child: const BYS360Logo(),
          ),
          children: [
            const ModuleIntroCard(
              icon: Icons.poll_outlined,
              title: 'Anket cevaplama',
              body: 'Yanıt bekleyen anketleri açın, zorunlu soruları tamamlayın ve cevabınızı kaydedin.',
              tone: BYS360Colors.warning,
            ),
            const BYSSectionTitle(title: 'Anket özetim', subtitle: 'Yanıt bekleyen ve tamamlanan anketler'),
            if (data.metrics.isEmpty)
              const BYSInfoPanel(
                icon: Icons.info_outline,
                title: 'Özet bulunamadı',
                body: 'Yetkiniz kapsamında gösterilecek anket özeti bulunmuyor.',
                tint: BYS360Colors.warning,
              )
            else
              ...data.metrics.map((metric) => MetricCard(
                    title: metric.title,
                    value: metric.value,
                    subtitle: metric.subtitle,
                    icon: _icon(metric.icon),
                    tone: BYS360Colors.warning,
                  )),
            BYSSectionTitle(
              title: 'Anket listesi',
              subtitle: 'Filtre seçerek yanıt bekleyen veya tamamlanan anketleri görebilirsiniz',
              action: IconButton(
                tooltip: 'Yenile',
                onPressed: () => setState(() => _future = _load()),
                icon: const Icon(Icons.refresh_outlined, color: BYS360Colors.corporateRed),
              ),
            ),
            _SurveyFilterBar(
              selected: _filter,
              onChanged: (next) => setState(() => _filter = next),
            ),
            if (items.isEmpty)
              BYSInfoPanel(
                icon: Icons.inbox_outlined,
                title: _emptyTitle,
                body: _emptyBody,
                tint: BYS360Colors.warning,
              )
            else
              ...items.map((record) => _SurveyListCard(
                    record: record,
                    onTap: () => _openDetail(record),
                  )),
          ],
        );
      },
    );
  }

  String get _emptyTitle {
    switch (_filter) {
      case _SurveyFilter.waiting:
        return 'Yanıt bekleyen anket yok';
      case _SurveyFilter.completed:
        return 'Tamamlanan anket yok';
      case _SurveyFilter.all:
        return 'Anket bulunamadı';
    }
  }

  String get _emptyBody {
    switch (_filter) {
      case _SurveyFilter.waiting:
        return 'Şu anda cevaplamanız gereken anket bulunmuyor.';
      case _SurveyFilter.completed:
        return 'Tamamlanan anketiniz bulunmuyor.';
      case _SurveyFilter.all:
        return 'Yetkiniz kapsamında görüntülenecek anket bulunmuyor.';
    }
  }

  IconData _icon(String value) {
    switch (value.toLowerCase()) {
      case 'verified_user':
        return Icons.verified_user_outlined;
      case 'feedback':
        return Icons.feedback_outlined;
      case 'groups':
        return Icons.groups_outlined;
      case 'poll':
      default:
        return Icons.poll_outlined;
    }
  }
}

enum _SurveyFilter { all, waiting, completed }

class _SurveyFilterBar extends StatelessWidget {
  const _SurveyFilterBar({required this.selected, required this.onChanged});

  final _SurveyFilter selected;
  final ValueChanged<_SurveyFilter> onChanged;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Row(
          children: [
            _FilterButton(label: 'Tümü', selected: selected == _SurveyFilter.all, onTap: () => onChanged(_SurveyFilter.all)),
            _FilterButton(label: 'Yanıt bekleyen', selected: selected == _SurveyFilter.waiting, onTap: () => onChanged(_SurveyFilter.waiting)),
            _FilterButton(label: 'Tamamlanan', selected: selected == _SurveyFilter.completed, onTap: () => onChanged(_SurveyFilter.completed)),
          ],
        ),
      ),
    );
  }
}

class _FilterButton extends StatelessWidget {
  const _FilterButton({required this.label, required this.selected, required this.onTap});

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 3),
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: onTap,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 160),
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
            decoration: BoxDecoration(
              color: selected ? BYS360Colors.corporateRed : BYS360Colors.surfaceSoft,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: selected ? BYS360Colors.corporateRed : BYS360Colors.cardBorder),
            ),
            child: Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: selected ? Colors.white : BYS360Colors.ink,
                fontWeight: FontWeight.w900,
                fontSize: 12,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _SurveyListCard extends StatelessWidget {
  const _SurveyListCard({required this.record, required this.onTap});

  final MobileRecord record;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final status = record.status ?? '-';
    final isDone = status.toLowerCase().contains('cevaplandı') || (record.progress ?? 0) >= 100;
    final tone = isDone ? BYS360Colors.success : BYS360Colors.warning;
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(BYS360Radii.lg),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 42,
                    height: 42,
                    decoration: BoxDecoration(color: tone.withValues(alpha: .10), borderRadius: BorderRadius.circular(15)),
                    child: Icon(isDone ? Icons.verified_outlined : Icons.poll_outlined, color: tone, size: 22),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(record.title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
                        if ((record.subtitle ?? '').trim().isNotEmpty) ...[
                          const SizedBox(height: 4),
                          Text(record.subtitle!, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(color: BYS360Colors.mutedText, height: 1.28)),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: [
                  StatusPill(text: status, tone: tone),
                  if ((record.meta ?? '').trim().isNotEmpty) StatusPill(text: record.meta!, tone: BYS360Colors.info),
                  StatusPill(text: isDone ? 'Görüntüle' : 'Cevapla', tone: BYS360Colors.corporateRed),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
