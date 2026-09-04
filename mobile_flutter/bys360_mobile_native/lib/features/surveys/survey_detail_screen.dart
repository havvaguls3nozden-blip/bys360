// BYS360_MOBILE_V2_8_66_SURVEY_COMPLETION
import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/utils/bys360_copy.dart';
import '../../core/utils/bys360_status_labels.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/record_widgets.dart';

class SurveyDetailScreen extends StatefulWidget {
  const SurveyDetailScreen({super.key, required this.apiClient, required this.surveyId, required this.fallbackTitle});

  final ApiClient apiClient;
  final String surveyId;
  final String fallbackTitle;

  @override
  State<SurveyDetailScreen> createState() => _SurveyDetailScreenState();
}

class _SurveyDetailScreenState extends State<SurveyDetailScreen> {
  late Future<SurveyDetail> _future;
  final Map<String, dynamic> _answers = <String, dynamic>{};
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<SurveyDetail> _load() async {
    final payload = await widget.apiClient.get('/api/mobile/surveys/${widget.surveyId}');
    if (payload is! Map) {
      throw StateError('Anket detayı beklenen biçimde alınamadı.');
    }
    final detail = SurveyDetail.fromJson(Map<String, dynamic>.from(payload));
    _answers.clear();
    return detail;
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  Future<void> _submit(SurveyDetail detail) async {
    final validationMessage = _firstValidationError(detail);
    if (validationMessage != null) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(validationMessage)));
      return;
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Anket cevabı gönderilsin mi?'),
        content: const Text('Cevabınız kaydedildikten sonra anket kuralına göre tekrar düzenleme yapılamayabilir.'),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: const Text('Vazgeç')),
          FilledButton(onPressed: () => Navigator.of(context).pop(true), child: const Text('Gönder')),
        ],
      ),
    );
    if (confirmed != true) return;

    setState(() => _submitting = true);
    try {
      await widget.apiClient.post('/api/mobile/surveys/${detail.survey.id}/submit', {'answers': _answers});
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Anket cevabınız kaydedildi.')));
      setState(() => _future = _load());
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(BYS360Copy.error(error))));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  String? _firstValidationError(SurveyDetail detail) {
    for (final question in detail.questions) {
      if (!question.isRequired) continue;
      final value = _answers[question.id];
      if (question.type == 'multiple_choice') {
        if (value is! List || value.isEmpty) return 'Lütfen zorunlu soruyu cevaplayın: ${question.text}';
      } else if (value == null || value.toString().trim().isEmpty) {
        return 'Lütfen zorunlu soruyu cevaplayın: ${question.text}';
      }
    }
    return null;
  }

  int _answeredCount(SurveyDetail detail) {
    var count = 0;
    for (final question in detail.questions) {
      final value = _answers[question.id];
      if (value is List && value.isNotEmpty) {
        count++;
      } else if (value != null && value.toString().trim().isNotEmpty) {
        count++;
      }
    }
    return count;
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<SurveyDetail>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(body: Center(child: CircularProgressIndicator()));
        }
        if (snapshot.hasError) {
          return BYSPage(
            title: widget.fallbackTitle,
            subtitle: 'Anket detayı alınamadı.',
            badge: 'Anket',
            onRefresh: _refresh,
            children: [ApiEmptyState(message: snapshot.error.toString(), onRetry: () => setState(() => _future = _load()))],
          );
        }

        final detail = snapshot.data!;
        final answeredCount = _answeredCount(detail);
        return BYSPage(
          title: detail.survey.title,
          subtitle: detail.survey.description.isEmpty ? 'Anket cevaplama formu' : detail.survey.description,
          badge: detail.survey.statusLabel,
          onRefresh: _refresh,
          children: [
            _SurveySummaryCard(detail: detail, answeredCount: answeredCount),
            if (detail.completed && !detail.survey.allowMultipleSubmissions)
              const BYSInfoPanel(
                icon: Icons.verified_outlined,
                title: 'Anket tamamlandı',
                body: 'Bu anket için cevabınız kaydedilmiş. Tekrar cevaplamaya izin verilmediği için form kapalıdır.',
                tint: BYS360Colors.success,
              ),
            if (!detail.canSubmit)
              const BYSInfoPanel(
                icon: Icons.lock_outline,
                title: 'Cevap gönderilemez',
                body: 'Anket yayında olmayabilir, daha önce cevaplanmış olabilir veya yetki kapsamı dışında kalabilir.',
                tint: BYS360Colors.warning,
              ),
            const BYSSectionTitle(title: 'Sorular', subtitle: 'Zorunlu alanlar doldurulmadan gönderim yapılmaz'),
            if (detail.questions.isEmpty)
              const BYSInfoPanel(icon: Icons.info_outline, title: 'Soru bulunamadı', body: 'Bu ankette cevaplanacak soru bulunmuyor.', tint: BYS360Colors.warning)
            else
              ...detail.questions.map((question) => _QuestionCard(
                    question: question,
                    enabled: detail.canSubmit && !_submitting,
                    value: _answers[question.id],
                    onChanged: (value) => setState(() => _answers[question.id] = value),
                  )),
            if (detail.canSubmit) ...[
              const SizedBox(height: 6),
              ElevatedButton.icon(
                onPressed: _submitting ? null : () => _submit(detail),
                icon: _submitting
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.send_outlined),
                label: Text(_submitting ? 'Gönderiliyor...' : 'Anket Cevabını Gönder'),
              ),
              const SizedBox(height: 8),
              const BYSInfoPanel(
                icon: Icons.privacy_tip_outlined,
                title: 'Gizlilik ve güvenli gönderim',
                body: 'Cevaplarınız yalnızca anketin yetki ve gizlilik kurallarına göre işlenir.',
                tint: BYS360Colors.info,
              ),
            ],
          ],
        );
      },
    );
  }
}

class _SurveySummaryCard extends StatelessWidget {
  const _SurveySummaryCard({required this.detail, required this.answeredCount});

  final SurveyDetail detail;
  final int answeredCount;

  @override
  Widget build(BuildContext context) {
    final survey = detail.survey;
    final total = survey.questionCount > 0 ? survey.questionCount : detail.questions.length;
    final progress = total == 0 ? 0.0 : (answeredCount / total).clamp(0.0, 1.0);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(color: BYS360Colors.warning.withValues(alpha: .10), borderRadius: BorderRadius.circular(15)),
                  child: const Icon(Icons.poll_outlined, color: BYS360Colors.warning),
                ),
                const SizedBox(width: 12),
                Expanded(child: Text(survey.title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900))),
              ],
            ),
            if (survey.description.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(survey.description, style: const TextStyle(color: BYS360Colors.mutedText, height: 1.3)),
            ],
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(999),
              child: LinearProgressIndicator(
                minHeight: 8,
                value: detail.canSubmit ? progress : (detail.completed ? 1.0 : 0.0),
                backgroundColor: BYS360Colors.cardBorder,
                valueColor: AlwaysStoppedAnimation<Color>(detail.completed ? BYS360Colors.success : BYS360Colors.warning),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              detail.canSubmit ? '$answeredCount / $total soru cevaplandı' : (detail.completed ? 'Cevabınız kaydedildi' : 'Form şu anda kapalı'),
              style: const TextStyle(color: BYS360Colors.mutedText, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                StatusPill(text: survey.statusLabel, tone: BYS360Colors.warning),
                StatusPill(text: survey.isAnonymous ? 'Anonim' : 'Kurum içi', tone: BYS360Colors.info),
                StatusPill(text: '$total soru', tone: BYS360Colors.corporateRed),
                if (survey.allowMultipleSubmissions) const StatusPill(text: 'Tekrar cevaplanabilir', tone: BYS360Colors.success),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _QuestionCard extends StatelessWidget {
  const _QuestionCard({required this.question, required this.enabled, required this.value, required this.onChanged});

  final SurveyQuestionItem question;
  final bool enabled;
  final dynamic value;
  final ValueChanged<dynamic> onChanged;

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
                Expanded(
                  child: Text(
                    question.text,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900),
                  ),
                ),
                if (question.isRequired) const StatusPill(text: 'Zorunlu', tone: BYS360Colors.corporateRed),
              ],
            ),
            const SizedBox(height: 5),
            Text(question.typeLabel, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText)),
            const SizedBox(height: 12),
            _buildInput(context),
          ],
        ),
      ),
    );
  }

  Widget _buildInput(BuildContext context) {
    switch (question.type) {
      case 'single_choice':
      case 'yes_no':
        final options = question.options.isEmpty && question.type == 'yes_no'
            ? const [SurveyOptionItem(id: 'yes', text: 'Evet'), SurveyOptionItem(id: 'no', text: 'Hayır')]
            : question.options;
        if (options.isEmpty) {
          return const BYSInfoPanel(icon: Icons.info_outline, title: 'Seçenek bulunamadı', body: 'Bu soru için seçenek tanımlanmamış.', tint: BYS360Colors.warning);
        }
        return Column(
          children: options.map((option) {
            final selected = value?.toString() == option.id;
            return ListTile(
              contentPadding: EdgeInsets.zero,
              enabled: enabled,
              leading: Icon(
                selected ? Icons.radio_button_checked : Icons.radio_button_unchecked,
                color: selected ? BYS360Colors.corporateRed : BYS360Colors.mutedText,
              ),
              title: Text(option.text),
              onTap: enabled ? () => onChanged(option.id) : null,
            );
          }).toList(),
        );
      case 'multiple_choice':
        final selected = value is List ? value!.map((item) => item.toString()).toSet() : <String>{};
        if (question.options.isEmpty) {
          return const BYSInfoPanel(icon: Icons.info_outline, title: 'Seçenek bulunamadı', body: 'Bu soru için seçenek tanımlanmamış.', tint: BYS360Colors.warning);
        }
        return Column(
          children: question.options.map((option) {
            final checked = selected.contains(option.id);
            return CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              value: checked,
              onChanged: enabled
                  ? (next) {
                      final copy = <String>{...selected};
                      if (next == true) {
                        copy.add(option.id);
                      } else {
                        copy.remove(option.id);
                      }
                      onChanged(copy.toList());
                    }
                  : null,
              title: Text(option.text),
            );
          }).toList(),
        );
      case 'rating_5':
      case 'rating_10':
        final maxValue = question.maxValue ?? (question.type == 'rating_10' ? 10 : 5);
        final selectedValue = int.tryParse(value?.toString() ?? '');
        return Wrap(
          spacing: 7,
          runSpacing: 7,
          children: List.generate(maxValue, (index) {
            final score = index + 1;
            return ChoiceChip(
              selected: selectedValue == score,
              label: Text(score.toString()),
              onSelected: enabled ? (_) => onChanged(score.toString()) : null,
              selectedColor: BYS360Colors.warning.withValues(alpha: .20),
              labelStyle: TextStyle(fontWeight: FontWeight.w900, color: selectedValue == score ? BYS360Colors.warning : BYS360Colors.ink),
            );
          }),
        );
      case 'text':
      default:
        return TextFormField(
          enabled: enabled,
          initialValue: value?.toString() ?? '',
          minLines: 2,
          maxLines: 5,
          decoration: const InputDecoration(hintText: 'Cevabınızı yazın'),
          onChanged: onChanged,
        );
    }
  }
}

class SurveyDetail {
  const SurveyDetail({required this.survey, required this.questions, required this.canSubmit, required this.completed});

  final SurveyHeader survey;
  final List<SurveyQuestionItem> questions;
  final bool canSubmit;
  final bool completed;

  factory SurveyDetail.fromJson(Map<String, dynamic> json) {
    final surveyJson = json['survey'] is Map ? Map<String, dynamic>.from(json['survey'] as Map) : <String, dynamic>{};
    final questionList = json['questions'] is List ? json['questions'] as List : const [];
    return SurveyDetail(
      survey: SurveyHeader.fromJson(surveyJson),
      questions: questionList.map((item) => SurveyQuestionItem.fromJson(Map<String, dynamic>.from(item as Map))).toList(),
      canSubmit: json['can_submit'] == true,
      completed: json['completed'] == true,
    );
  }
}

class SurveyHeader {
  const SurveyHeader({
    required this.id,
    required this.title,
    required this.description,
    required this.statusLabel,
    required this.isAnonymous,
    required this.allowMultipleSubmissions,
    required this.questionCount,
  });

  final String id;
  final String title;
  final String description;
  final String statusLabel;
  final bool isAnonymous;
  final bool allowMultipleSubmissions;
  final int questionCount;

  factory SurveyHeader.fromJson(Map<String, dynamic> json) {
    return SurveyHeader(
      id: json['id']?.toString() ?? '',
      title: json['title']?.toString() ?? 'Anket',
      description: json['description']?.toString() ?? '',
      statusLabel: json['status_label']?.toString() ?? bys360GenericStatusLabel(json['status']?.toString(), fallback: '-'),
      isAnonymous: json['is_anonymous'] == true,
      allowMultipleSubmissions: json['allow_multiple_submissions'] == true,
      questionCount: int.tryParse(json['question_count']?.toString() ?? '') ?? 0,
    );
  }
}

class SurveyQuestionItem {
  const SurveyQuestionItem({required this.id, required this.text, required this.type, required this.typeLabel, required this.isRequired, required this.options, this.maxValue});

  final String id;
  final String text;
  final String type;
  final String typeLabel;
  final bool isRequired;
  final List<SurveyOptionItem> options;
  final int? maxValue;

  factory SurveyQuestionItem.fromJson(Map<String, dynamic> json) {
    final optionList = json['options'] is List ? json['options'] as List : const [];
    return SurveyQuestionItem(
      id: json['id']?.toString() ?? '',
      text: json['text']?.toString() ?? 'Anket sorusu',
      type: json['type']?.toString() ?? 'text',
      typeLabel: json['type_label']?.toString() ?? 'Soru',
      isRequired: json['is_required'] != false,
      maxValue: int.tryParse(json['max_value']?.toString() ?? ''),
      options: optionList.map((item) => SurveyOptionItem.fromJson(Map<String, dynamic>.from(item as Map))).toList(),
    );
  }
}

class SurveyOptionItem {
  const SurveyOptionItem({required this.id, required this.text});

  final String id;
  final String text;

  factory SurveyOptionItem.fromJson(Map<String, dynamic> json) {
    return SurveyOptionItem(id: json['id']?.toString() ?? '', text: json['text']?.toString() ?? 'Seçenek');
  }
}
