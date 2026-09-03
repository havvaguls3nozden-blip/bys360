// BYS360_MOBILE_V2_8_44_SCORE_1_5_COMMENT_OPTIONAL: 1 ve 5 puanda kriter açıklaması mobilde isteğe bağlıdır | 70 altı 90 üstü genel görüş korunur
// BYS360_MOBILE_V2_8_39_NATIVE_FAST_SCORE_MARKERS: Hepsine 5 | Hepsine 4 | Hepsine 3 | Hepsine 2 | Hepsine 1 | Geri Çek | İade Et
import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/utils/bys360_copy.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';

class PerformanceScoringScreen extends StatefulWidget {
  const PerformanceScoringScreen({super.key, required this.apiClient, required this.assignmentId, required this.taskTitle});

  final ApiClient apiClient;
  final String assignmentId;
  final String taskTitle;

  @override
  State<PerformanceScoringScreen> createState() => _PerformanceScoringScreenState();
}

class _PerformanceScoringScreenState extends State<PerformanceScoringScreen> {
  final TextEditingController _generalComment = TextEditingController();
  late Future<_ScoreForm> _future;
  _ScoreForm? _form;
  bool _saving = false;
  bool _actionRunning = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  @override
  void dispose() {
    _generalComment.dispose();
    _form?.dispose();
    super.dispose();
  }

  Future<_ScoreForm> _load() async {
    final payload = await widget.apiClient.get('/api/mobile/performance/tasks/${widget.assignmentId}/score-form');
    final form = _ScoreForm.fromPayload(payload);
    _form?.dispose();
    _form = form;
    _generalComment.text = form.generalComment;
    return form;
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  void _applyBulk(_ScoreForm form, int score) {
    setState(() {
      for (final item in form.criteria) {
        item.score = score;
      }
    });
  }

  String? _validate(_ScoreForm form, {required bool completed}) {
    final general = _generalComment.text.trim();
    if (!form.scoreMode) {
      return general.isEmpty ? 'Bu görev yalnızca görüş modundadır. Genel görüş yazmanız gerekir.' : null;
    }
    if (completed) {
      for (final item in form.criteria) {
        if (item.score == null) return 'Tamamlamak için tüm kriterlere 1 ile 5 arasında puan verin.';
      }
    }
    if (!completed && general.isEmpty && form.criteria.every((item) => item.score == null && item.comment.text.trim().isEmpty)) {
      return 'Taslak kaydetmek için en az bir puan, açıklama veya genel görüş girin.';
    }
    return null;
  }

  Future<void> _submit(_ScoreForm form, {required bool completed}) async {
    final error = _validate(form, completed: completed);
    if (error != null) {
      _message(error);
      return;
    }
    setState(() => _saving = true);
    try {
      final body = <String, dynamic>{
        'completed': completed,
        'general_comment': _generalComment.text.trim(),
        'items': form.scoreMode
            ? form.criteria
                .where((item) => item.score != null || item.comment.text.trim().isNotEmpty)
                .map((item) => {
                      'criteria_id': item.criteriaId,
                      'score': item.score,
                      'comment': item.comment.text.trim(),
                    })
                .toList()
            : <Map<String, dynamic>>[],
      };
      final result = await widget.apiClient.post('/api/mobile/performance/tasks/${widget.assignmentId}/score-form', body);
      final map = _asMap(result);
      _message(_text(map, ['message'], completed ? 'Değerlendirme tamamlandı.' : 'Taslak kaydedildi.'));
      await _refresh();
      if (completed && mounted) Navigator.of(context).pop(true);
    } catch (error) {
      _message(BYS360Copy.error(error));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _runAction(_ScoreForm form, String action) async {
    final isReturn = action == 'return';
    final note = await _askActionNote(isReturn ? 'İade Açıklaması' : 'Geri Çekme Açıklaması');
    if (note == null) return;
    setState(() => _actionRunning = true);
    try {
      final result = await widget.apiClient.post('/api/mobile/performance/tasks/${widget.assignmentId}/score-action', {'action': action, 'note': note});
      final map = _asMap(result);
      _message(_text(map, ['message'], isReturn ? 'Değerlendirme iade edildi.' : 'Değerlendirme geri çekildi.'));
      if (mounted) Navigator.of(context).pop(true);
    } catch (error) {
      _message(BYS360Copy.error(error));
    } finally {
      if (mounted) setState(() => _actionRunning = false);
    }
  }

  Future<String?> _askActionNote(String title) async {
    final controller = TextEditingController();
    final result = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          maxLines: 4,
          decoration: const InputDecoration(labelText: 'Açıklama', hintText: 'İşlem gerekçesini yazın'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(null), child: const Text('Vazgeç')),
          FilledButton(onPressed: () => Navigator.of(context).pop(controller.text.trim()), child: const Text('Onayla')),
        ],
      ),
    );
    controller.dispose();
    return result;
  }

  void _message(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Puanlama Formu')),
      body: FutureBuilder<_ScoreForm>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const BYSLoadingState(message: 'Puanlama formu yükleniyor');
          }
          if (snapshot.hasError) {
            return BYSPage(
              title: 'Puanlama Formu',
              subtitle: 'Bu değerlendirme formuna şu anda ulaşılamadı.',
              badge: 'Puanlama',
              onRefresh: _refresh,
              children: [
                ApiEmptyState(
                  title: 'Form yüklenemedi',
                  message: 'Puanlama formu şu anda alınamadı. Lütfen tekrar deneyin.',
                  onRetry: () => setState(() => _future = _load()),
                ),
              ],
            );
          }
          final form = snapshot.data ?? _ScoreForm.empty(widget.assignmentId);
          final filled = form.scoreMode ? form.criteria.where((item) => item.score != null).length : (_generalComment.text.trim().isEmpty ? 0 : 1);
          final total = form.scoreMode ? form.criteria.length : 1;
          final progress = total == 0 ? 0 : ((filled / total) * 100).round().clamp(0, 100);

          return BYSPage(
            title: form.employeeName.isEmpty ? widget.taskTitle : form.employeeName,
            subtitle: '${form.periodName} • ${form.managerLevelLabel}',
            badge: 'Puanlama',
            onRefresh: _refresh,
            trailing: _ScoreCircle(score: form.averageScore),
            children: [
              ProgressCard(title: 'Puanlama İlerlemesi', subtitle: '$filled / $total alan dolduruldu', progress: progress),
              _PersonSummary(form: form),
              if (form.warning.isNotEmpty) BYSInfoPanel(icon: Icons.info_outline, title: 'Süreç Uyarısı', body: form.warning, tint: BYS360Colors.warning),
              if (form.scoreMode) ...[
                _BulkScorePanel(onBulk: (score) => _applyBulk(form, score), scores: form.bulkScores),
                const BYSSectionTitle(title: 'Değerlendirme Kriterleri', subtitle: 'Her kriter için 1 ile 5 arasında puan seçin'),
                ...form.criteria.map((item) => _CriterionCard(item: item, onChanged: () => setState(() {}))),
              ] else
                const BYSInfoPanel(
                  icon: Icons.edit_note_outlined,
                  title: 'Yalnızca görüş modu',
                  body: 'Bu görevde puan alanı kapalıdır. Genel görüş alanını doldurarak kaydedebilirsiniz.',
                  tint: BYS360Colors.info,
                ),
              const BYSSectionTitle(title: 'Genel Görüş', subtitle: 'Değerlendirmeye ilişkin kurumsal kanaatinizi yazın'),
              TextField(
                controller: _generalComment,
                minLines: 4,
                maxLines: 7,
                textInputAction: TextInputAction.newline,
                onChanged: (_) => setState(() {}),
                decoration: const InputDecoration(
                  labelText: 'Genel görüş',
                  hintText: 'Personelin dönem içindeki genel performansına ilişkin görüşünüzü yazın',
                ),
              ),
              const SizedBox(height: 12),
              _ActionButtons(
                form: form,
                saving: _saving,
                actionRunning: _actionRunning,
                onSaveDraft: () => _submit(form, completed: false),
                onComplete: () => _submit(form, completed: true),
                onWithdraw: form.canWithdraw ? () => _runAction(form, 'withdraw') : null,
                onReturn: form.canReturn ? () => _runAction(form, 'return') : null,
              ),
              const BYSInfoPanel(
                icon: Icons.lock_outline,
                title: 'Yayın ve onay sınırı',
                body: 'Mobilde yapılan puanlama BYS360 kurallarına bağlıdır. 70 altı sonuçlar gerekli üst onay tamamlanmadan personele açılmaz.',
              ),
            ],
          );
        },
      ),
    );
  }
}

class _PersonSummary extends StatelessWidget {
  const _PersonSummary({required this.form});
  final _ScoreForm form;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(15),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 46,
                  height: 46,
                  decoration: BoxDecoration(color: BYS360Colors.softRed, borderRadius: BorderRadius.circular(17)),
                  child: const Icon(Icons.person_outline, color: BYS360Colors.corporateRed),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(form.employeeName, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
                      const SizedBox(height: 3),
                      Text('${form.unitName} • Sicil ${form.sicilNo}', style: const TextStyle(color: BYS360Colors.mutedText, fontWeight: FontWeight.w700)),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _SmallInfo(label: 'Dönem', value: form.periodName),
                _SmallInfo(label: 'Tarih', value: form.dateRange),
                _SmallInfo(label: 'Durum', value: form.statusLabel),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _SmallInfo extends StatelessWidget {
  const _SmallInfo({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(color: BYS360Colors.surfaceSoft, borderRadius: BorderRadius.circular(13), border: Border.all(color: BYS360Colors.cardBorder)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label, style: const TextStyle(color: BYS360Colors.subtleText, fontSize: 11, fontWeight: FontWeight.w800)),
          const SizedBox(height: 2),
          Text(value.isEmpty ? '-' : value, style: const TextStyle(color: BYS360Colors.ink, fontSize: 12, fontWeight: FontWeight.w900)),
        ],
      ),
    );
  }
}

class _BulkScorePanel extends StatelessWidget {
  const _BulkScorePanel({required this.onBulk, required this.scores});
  final ValueChanged<int> onBulk;
  final List<int> scores;

  @override
  Widget build(BuildContext context) {
    final usableScores = scores.isEmpty ? const [5, 4, 3, 2, 1] : scores;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(15),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Hızlı Puanlama', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 5),
            const Text('Tek dokunuşla tüm kriterlere aynı puanı uygulayın. Sonra istediğiniz kriteri ayrıca değiştirebilirsiniz.', style: TextStyle(color: BYS360Colors.mutedText)),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: usableScores.map((score) => FilledButton.tonalIcon(onPressed: () => onBulk(score), icon: const Icon(Icons.auto_awesome, size: 18), label: Text('Hepsine $score'))).toList(),
            ),
          ],
        ),
      ),
    );
  }
}

class _CriterionCard extends StatelessWidget {
  const _CriterionCard({required this.item, required this.onChanged});
  final _CriterionItem item;
  final VoidCallback onChanged;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(15),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(child: Text(item.title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900))),
                if (item.weight > 0) _WeightBadge(weight: item.weight),
              ],
            ),
            if (item.description.isNotEmpty) ...[
              const SizedBox(height: 5),
              Text(item.description, style: const TextStyle(color: BYS360Colors.mutedText, height: 1.3)),
            ],
            const SizedBox(height: 13),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [1, 2, 3, 4, 5]
                  .map((score) => ChoiceChip(
                        label: Text('$score'),
                        selected: item.score == score,
                        onSelected: (_) {
                          item.score = score;
                          onChanged();
                        },
                        selectedColor: BYS360Colors.corporateRed,
                        labelStyle: TextStyle(color: item.score == score ? Colors.white : BYS360Colors.ink, fontWeight: FontWeight.w900),
                        backgroundColor: Colors.white,
                        side: const BorderSide(color: BYS360Colors.cardBorder),
                      ))
                  .toList(),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: item.comment,
              minLines: 2,
              maxLines: 4,
              onChanged: (_) => onChanged(),
              decoration: const InputDecoration(
                labelText: 'Kriter açıklaması (isteğe bağlı)',
                hintText: 'Gerekliyse bu kritere ilişkin kısa açıklama yazın',
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _WeightBadge extends StatelessWidget {
  const _WeightBadge({required this.weight});
  final double weight;

  @override
  Widget build(BuildContext context) {
    final value = weight == weight.roundToDouble() ? weight.toInt().toString() : weight.toStringAsFixed(1);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(color: BYS360Colors.softRed, borderRadius: BorderRadius.circular(999)),
      child: Text('%$value', style: const TextStyle(color: BYS360Colors.corporateRed, fontWeight: FontWeight.w900, fontSize: 12)),
    );
  }
}

class _ActionButtons extends StatelessWidget {
  const _ActionButtons({required this.form, required this.saving, required this.actionRunning, required this.onSaveDraft, required this.onComplete, this.onWithdraw, this.onReturn});

  final _ScoreForm form;
  final bool saving;
  final bool actionRunning;
  final VoidCallback onSaveDraft;
  final VoidCallback onComplete;
  final VoidCallback? onWithdraw;
  final VoidCallback? onReturn;

  @override
  Widget build(BuildContext context) {
    final busy = saving || actionRunning;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        OutlinedButton.icon(onPressed: busy ? null : onSaveDraft, icon: const Icon(Icons.save_outlined), label: Text(form.saveLabel.isEmpty ? 'Taslak Kaydet' : form.saveLabel)),
        const SizedBox(height: 8),
        ElevatedButton.icon(
          onPressed: busy ? null : onComplete,
          icon: saving ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.check_circle_outline),
          label: Text(form.submitLabel.isEmpty ? 'Tamamla' : form.submitLabel),
        ),
        if (onWithdraw != null || onReturn != null) ...[
          const SizedBox(height: 10),
          Row(
            children: [
              if (onWithdraw != null) Expanded(child: OutlinedButton.icon(onPressed: busy ? null : onWithdraw, icon: const Icon(Icons.undo_outlined), label: const Text('Geri Çek'))),
              if (onWithdraw != null && onReturn != null) const SizedBox(width: 10),
              if (onReturn != null) Expanded(child: OutlinedButton.icon(onPressed: busy ? null : onReturn, icon: const Icon(Icons.reply_all_outlined), label: const Text('İade Et'))),
            ],
          ),
        ],
      ],
    );
  }
}

class _ScoreCircle extends StatelessWidget {
  const _ScoreCircle({required this.score});
  final double score;

  @override
  Widget build(BuildContext context) {
    final text = score <= 0 ? '-' : score.toStringAsFixed(1);
    return Container(
      width: 72,
      height: 72,
      decoration: BoxDecoration(color: BYS360Colors.softRed, shape: BoxShape.circle, border: Border.all(color: BYS360Colors.corporateRed.withValues(alpha: .16))),
      child: Center(child: Text(text, style: const TextStyle(color: BYS360Colors.corporateRed, fontWeight: FontWeight.w900, fontSize: 18))),
    );
  }
}

class _ScoreForm {
  _ScoreForm({
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
    required this.submitLabel,
    required this.saveLabel,
    required this.canWithdraw,
    required this.canReturn,
    required this.bulkScores,
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
  final List<_CriterionItem> criteria;
  final String generalComment;
  final String warning;
  final String submitLabel;
  final String saveLabel;
  final bool canWithdraw;
  final bool canReturn;
  final List<int> bulkScores;

  double get averageScore {
    final scores = criteria.map((item) => item.score).whereType<int>().toList();
    if (scores.isEmpty) return 0;
    return scores.reduce((a, b) => a + b) / scores.length;
  }

  factory _ScoreForm.fromPayload(dynamic payload) {
    final map = _asMap(payload);
    final rawForm = map['form'];
    final form = _asMap(rawForm is Map && rawForm.isNotEmpty ? rawForm : map);
    final actions = _asMap(form['actions']);
    final bulk = form['bulk_scores'] ?? actions['bulk_scores'];
    return _ScoreForm(
      assignmentId: _text(form, ['assignment_id'], ''),
      employeeName: _text(form, ['employee_name'], 'Personel'),
      sicilNo: _text(form, ['sicil_no'], '-'),
      unitName: _text(form, ['unit_name'], '-'),
      periodName: _text(form, ['period_name'], 'Performans Dönemi'),
      dateRange: _text(form, ['date_range'], ''),
      managerLevelLabel: _text(form, ['manager_level_label'], 'Amir'),
      statusLabel: _text(form, ['status_label'], 'Değerlendirme Bekliyor'),
      scoreMode: _bool(form['score_mode'], fallback: true),
      criteria: _asList(form['criteria']).map(_CriterionItem.fromJson).toList(),
      generalComment: _text(form, ['general_comment'], ''),
      warning: _text(form, ['warning'], ''),
      submitLabel: _text(form, ['submit_label'], 'Tamamla'),
      saveLabel: _text(form, ['save_label'], 'Taslak Kaydet'),
      canWithdraw: _bool(actions['can_withdraw'], fallback: false),
      canReturn: _bool(actions['can_return'], fallback: false),
      bulkScores: _intList(bulk),
    );
  }

  factory _ScoreForm.empty(String assignmentId) => _ScoreForm(
        assignmentId: assignmentId,
        employeeName: 'Personel',
        sicilNo: '-',
        unitName: '-',
        periodName: 'Performans Dönemi',
        dateRange: '',
        managerLevelLabel: 'Amir',
        statusLabel: 'Değerlendirme Bekliyor',
        scoreMode: true,
        criteria: const [],
        generalComment: '',
        warning: '',
        submitLabel: 'Tamamla',
        saveLabel: 'Taslak Kaydet',
        canWithdraw: false,
        canReturn: false,
        bulkScores: const [5, 4, 3, 2, 1],
      );

  void dispose() {
    for (final item in criteria) {
      item.dispose();
    }
  }
}

class _CriterionItem {
  _CriterionItem({required this.criteriaId, required this.title, required this.description, required this.weight, required this.score, required String comment}) : comment = TextEditingController(text: comment);

  final int criteriaId;
  final String title;
  final String description;
  final double weight;
  int? score;
  final TextEditingController comment;

  factory _CriterionItem.fromJson(Map<String, dynamic> json) => _CriterionItem(
        criteriaId: _int(json['criteria_id'] ?? json['id'], fallback: 0),
        title: _text(json, ['title', 'name'], 'Değerlendirme Kriteri'),
        description: _text(json, ['description'], ''),
        weight: _double(json['weight']),
        score: _nullableInt(json['score']),
        comment: _text(json, ['comment'], ''),
      );

  void dispose() => comment.dispose();
}


List<Map<String, dynamic>> _asList(dynamic value) {
  if (value is List) return value.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
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

bool _bool(dynamic value, {required bool fallback}) {
  if (value is bool) return value;
  final text = value?.toString().toLowerCase().trim();
  if (text == 'true' || text == '1' || text == 'evet') return true;
  if (text == 'false' || text == '0' || text == 'hayır' || text == 'hayir') return false;
  return fallback;
}

int _int(dynamic value, {required int fallback}) {
  if (value is int) return value;
  if (value is num) return value.toInt();
  return int.tryParse(value?.toString() ?? '') ?? fallback;
}

int? _nullableInt(dynamic value) {
  if (value == null || value.toString().trim().isEmpty) return null;
  if (value is int) return value;
  if (value is num) return value.round();
  final parsed = double.tryParse(value.toString().replaceAll(',', '.'));
  return parsed?.round();
}

double _double(dynamic value) {
  if (value is double) return value;
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString().replaceAll(',', '.') ?? '') ?? 0;
}

List<int> _intList(dynamic value) {
  if (value is List) {
    final items = value.map((item) => _int(item, fallback: 0)).where((item) => item > 0).toList();
    if (items.isNotEmpty) return items;
  }
  return const [5, 4, 3, 2, 1];
}

// BYS360_MOBILE_V2_8_38_NATIVE_PREMIUM_SCORING_SCREEN

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION
