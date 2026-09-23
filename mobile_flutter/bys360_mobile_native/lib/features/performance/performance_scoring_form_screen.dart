import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/utils/bys360_copy.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';
import 'mobile_scoring_form_path.dart';
import 'performance_mobile_p1_models.dart';

class PerformanceScoringFormScreen extends StatefulWidget {
  const PerformanceScoringFormScreen({
    super.key,
    required this.apiClient,
    required this.assignmentId,
    this.seed,
  });

  final ApiClient apiClient;
  final String assignmentId;
  final MobilePerformanceRecord? seed;

  @override
  State<PerformanceScoringFormScreen> createState() => _PerformanceScoringFormScreenState();
}

class _PerformanceScoringFormScreenState extends State<PerformanceScoringFormScreen> {
  late Future<_ScoringFormData> _future;
  final Map<int, int?> _scores = <int, int?>{};
  final Map<int, TextEditingController> _comments = <int, TextEditingController>{};
  final TextEditingController _generalComment = TextEditingController();
  String? _hydratedAssignmentId;
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  @override
  void dispose() {
    for (final controller in _comments.values) {
      controller.dispose();
    }
    _generalComment.dispose();
    super.dispose();
  }

  Future<_ScoringFormData> _load() async {
    final payload = await widget.apiClient.get(BYS360MobileScoringFormPath.scoreFormPath(widget.assignmentId));
    return _ScoringFormData.fromPayload(payload, seed: widget.seed, fallbackAssignmentId: widget.assignmentId);
  }

  Future<void> _refresh() async {
    setState(() {
      _hydratedAssignmentId = null;
      _future = _load();
    });
    await _future;
  }

  void _hydrate(_ScoringFormData form) {
    if (_hydratedAssignmentId == form.assignmentId) return;
    for (final controller in _comments.values) {
      controller.dispose();
    }
    _comments.clear();
    _scores.clear();
    for (final criterion in form.criteria) {
      _scores[criterion.id] = criterion.score;
      _comments[criterion.id] = TextEditingController(text: criterion.comment);
    }
    _generalComment.text = form.generalComment;
    _hydratedAssignmentId = form.assignmentId;
  }

  Future<void> _submit(_ScoringFormData form, {required bool completed}) async {
    if (_submitting) return;
    final items = form.criteria.map((criterion) {
      return <String, dynamic>{
        'criteria_id': criterion.id,
        'score': _scores[criterion.id],
        'comment': _comments[criterion.id]?.text.trim() ?? '',
      };
    }).where((item) => item['score'] != null).toList();

    if (completed && form.scoreMode) {
      final missing = form.criteria.where((criterion) => _scores[criterion.id] == null).toList();
      if (missing.isNotEmpty) {
        _showMessage('Tamamlamak için tüm değerlendirme kriterlerine puan girilmelidir.');
        return;
      }
    }

    if (!form.scoreMode && _generalComment.text.trim().isEmpty) {
      _showMessage('Bu görev yorum/görüş modunda olduğu için genel görüş zorunludur.');
      return;
    }

    setState(() => _submitting = true);
    try {
      final response = await widget.apiClient.post(BYS360MobileScoringFormPath.scoreFormPath(form.assignmentId), <String, dynamic>{
        'completed': completed,
        'general_comment': _generalComment.text.trim(),
        'items': items,
      });
      final map = response is Map ? Map<String, dynamic>.from(response) : <String, dynamic>{};
      _showMessage((map['message'] ?? (completed ? 'Değerlendirme tamamlandı.' : 'Taslak kaydedildi.')).toString());
      setState(() {
        _hydratedAssignmentId = null;
        _future = _load();
      });
    } catch (error) {
      _showMessage(_cleanError(error));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_cleanError(message))));
  }

  String _cleanError(Object? error) => BYS360Copy.error(error);

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_ScoringFormData>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return const BYSLoadingState(message: 'Puanlama formu yükleniyor');
        if (snapshot.hasError) {
          return BYSPage(
            title: 'Puanlama Formu',
            subtitle: 'Değerlendirme formuna şu anda ulaşılamadı.',
            badge: 'Puanlama',
            onRefresh: _refresh,
            children: [ApiEmptyState(message: 'Puanlama formu şu anda alınamadı. Lütfen tekrar deneyin.', onRetry: () => setState(() => _future = _load()))],
          );
        }

        final form = snapshot.data ?? _ScoringFormData.empty(widget.assignmentId, widget.seed);
        _hydrate(form);

        return BYSPage(
          title: 'Puanlama Formu',
          subtitle: '${form.employeeName} • ${form.periodName}',
          badge: form.managerLevelLabel,
          onRefresh: _refresh,
          children: [
            MetricCard(
              title: form.statusLabel,
              value: form.scoreMode ? '1-5' : 'Görüş',
              subtitle: form.scoreMode ? 'Kriter bazlı puanlama ekranı' : '3. amir yorum/görüş modu',
              icon: form.scoreMode ? Icons.fact_check_outlined : Icons.rate_review_outlined,
              tone: BYS360Colors.corporateRed,
            ),
            BYSInfoPanel(
              icon: Icons.person_outline,
              title: form.employeeName,
              body: 'Sicil: ${form.sicilNo} • ${form.unitName}\nDönem: ${form.dateRange.isEmpty ? form.periodName : form.dateRange}',
              tint: BYS360Colors.info,
            ),
            BYSInfoPanel(
              icon: Icons.shield_outlined,
              title: 'Kurumsal kural',
              body: form.warning,
              tint: BYS360Colors.warning,
            ),
            if (!form.scoreMode) ...[
              const BYSSectionTitle(title: 'Genel görüş', subtitle: 'Bu görev puan değil görüş olarak tamamlanır'),
              _GeneralCommentCard(controller: _generalComment),
            ] else ...[
              const BYSSectionTitle(title: 'Değerlendirme Kriterleri', subtitle: 'Her kriter için 1-5 arası puan girin'),
              if (form.criteria.isEmpty)
                const BYSInfoPanel(
                  icon: Icons.info_outline,
                  title: 'Kriter bulunamadı',
                  body: 'Puanlama için aktif değerlendirme kriteri bulunamadı. BYS360’da kriter tanımlarını kontrol edin.',
                  tint: BYS360Colors.warning,
                )
              else
                ...form.criteria.map((criterion) => _CriterionScoreCard(
                      criterion: criterion,
                      score: _scores[criterion.id],
                      commentController: _comments[criterion.id]!,
                      onScoreChanged: (value) => setState(() => _scores[criterion.id] = value),
                    )),
              const BYSSectionTitle(title: 'Genel değerlendirme', subtitle: '70 altı / 90 üstü sonuçlarda zorunlu olabilir'),
              _GeneralCommentCard(controller: _generalComment),
            ],
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _submitting ? null : () => _submit(form, completed: false),
                    icon: const Icon(Icons.save_outlined),
                    label: const Text('Taslak Kaydet'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: _submitting ? null : () => _submit(form, completed: true),
                    icon: _submitting ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.check_circle_outline),
                    label: const Text('Tamamla'),
                  ),
                ),
              ],
            ),
            const BYSInfoPanel(
              icon: Icons.lock_outline,
              title: 'Yetki kontrollü kayıt',
              body: 'Bu form yalnızca size atanmış değerlendirme görevini kaydeder. Yayınlanmamış karne ve yetkisiz performans verisi mobilde açılmaz.',
            ),
          ],
        );
      },
    );
  }
}

class _CriterionScoreCard extends StatelessWidget {
  const _CriterionScoreCard({required this.criterion, required this.score, required this.commentController, required this.onScoreChanged});

  final _ScoringCriterion criterion;
  final int? score;
  final TextEditingController commentController;
  final ValueChanged<int?> onScoreChanged;

  @override
  Widget build(BuildContext context) {
    return Card(
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
                  decoration: BoxDecoration(color: BYS360Colors.corporateRed.withValues(alpha: .10), borderRadius: BorderRadius.circular(15)),
                  child: const Icon(Icons.rule_folder_outlined, color: BYS360Colors.corporateRed, size: 21),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(criterion.title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900)),
                      if (criterion.description.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(criterion.description, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText, height: 1.28)),
                      ],
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<int>(
              initialValue: score,
              decoration: const InputDecoration(labelText: 'Puan', hintText: '1-5 arası seçin'),
              items: const [1, 2, 3, 4, 5].map((value) => DropdownMenuItem<int>(value: value, child: Text('$value'))).toList(),
              onChanged: onScoreChanged,
            ),
            const SizedBox(height: 10),
            TextFormField(
              controller: commentController,
              minLines: 2,
              maxLines: 4,
              decoration: const InputDecoration(labelText: 'Kriter açıklaması', hintText: 'Gerekli ise kısa açıklama yazın'),
            ),
          ],
        ),
      ),
    );
  }
}

class _GeneralCommentCard extends StatelessWidget {
  const _GeneralCommentCard({required this.controller});

  final TextEditingController controller;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: TextFormField(
          controller: controller,
          minLines: 4,
          maxLines: 7,
          decoration: const InputDecoration(labelText: 'Genel görüş', hintText: 'Genel değerlendirme veya üst görüş yazın'),
        ),
      ),
    );
  }
}

class _ScoringFormData {
  const _ScoringFormData({
    required this.assignmentId,
    required this.employeeName,
    required this.sicilNo,
    required this.unitName,
    required this.periodName,
    required this.dateRange,
    required this.managerLevelLabel,
    required this.statusLabel,
    required this.scoreMode,
    required this.criteria,
    required this.generalComment,
    required this.warning,
  });

  final String assignmentId;
  final String employeeName;
  final String sicilNo;
  final String unitName;
  final String periodName;
  final String dateRange;
  final String managerLevelLabel;
  final String statusLabel;
  final bool scoreMode;
  final List<_ScoringCriterion> criteria;
  final String generalComment;
  final String warning;

  factory _ScoringFormData.fromPayload(dynamic payload, {MobilePerformanceRecord? seed, required String fallbackAssignmentId}) {
    final root = _asMap(payload);
    final form = _asMap(root['form']).isNotEmpty ? _asMap(root['form']) : root;
    final criteria = _asList(form['criteria']).map((item) => _ScoringCriterion.fromMap(_asMap(item))).where((item) => item.id > 0).toList();
    return _ScoringFormData(
      assignmentId: _asString(form['assignment_id'], fallbackAssignmentId),
      employeeName: _asString(form['employee_name'], seed?.title ?? 'Personel'),
      sicilNo: _asString(form['sicil_no'], '-'),
      unitName: _asString(form['unit_name'], seed?.subtitle ?? 'Birim bilgisi'),
      periodName: _asString(form['period_name'], seed?.subtitle ?? 'Performans Dönemi'),
      dateRange: _asString(form['date_range'], seed?.meta ?? ''),
      managerLevelLabel: _asString(form['manager_level_label'], seed?.meta ?? 'Amir'),
      statusLabel: _asString(form['status_label'], seed?.status ?? 'Değerlendirme Bekliyor'),
      scoreMode: form['score_mode'] == false ? false : true,
      criteria: criteria,
      generalComment: _asString(form['general_comment'], ''),
      warning: _asString(form['warning'], '70 altı veya 90 üstü sonuçlarda ayrıntılı genel görüş zorunludur.'),
    );
  }

  factory _ScoringFormData.empty(String assignmentId, MobilePerformanceRecord? seed) {
    return _ScoringFormData(
      assignmentId: assignmentId,
      employeeName: seed?.title ?? 'Personel',
      sicilNo: '-',
      unitName: seed?.subtitle ?? 'Birim bilgisi',
      periodName: seed?.subtitle ?? 'Performans Dönemi',
      dateRange: seed?.meta ?? '',
      managerLevelLabel: seed?.meta ?? 'Amir',
      statusLabel: seed?.status ?? 'Değerlendirme Bekliyor',
      scoreMode: true,
      criteria: const <_ScoringCriterion>[],
      generalComment: '',
      warning: 'Puanlama formu için veri bulunamadı.',
    );
  }
}

class _ScoringCriterion {
  const _ScoringCriterion({required this.id, required this.title, required this.description, required this.score, required this.comment});

  final int id;
  final String title;
  final String description;
  final int? score;
  final String comment;

  factory _ScoringCriterion.fromMap(Map<String, dynamic> map) {
    final scoreValue = map['score'];
    int? score;
    if (scoreValue is num) score = scoreValue.round();
    if (scoreValue is String && scoreValue.trim().isNotEmpty) score = int.tryParse(scoreValue.split('.').first);
    if (score != null && (score < 1 || score > 5)) score = null;
    return _ScoringCriterion(
      id: _asInt(map['criteria_id'] ?? map['id']),
      title: _asString(map['title'] ?? map['name'], 'Değerlendirme Kriteri'),
      description: _asString(map['description'], ''),
      score: score,
      comment: _asString(map['comment'], ''),
    );
  }
}

Map<String, dynamic> _asMap(dynamic value) {
  if (value is Map) return Map<String, dynamic>.from(value);
  return <String, dynamic>{};
}

List<dynamic> _asList(dynamic value) {
  if (value is List) return value;
  return const <dynamic>[];
}

String _asString(dynamic value, [String fallback = '']) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}

int _asInt(dynamic value, [int fallback = 0]) {
  if (value is num) return value.toInt();
  return int.tryParse(value?.toString() ?? '') ?? fallback;
}

// BYS360_MOBILE_V2_8_35_PERFORMANCE_SCORING_FORM

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION

// BYS360_MOBILE_V2_8_68_QUALITY_CLEANUP
