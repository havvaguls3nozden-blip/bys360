// BYS360_MOBILE_V2_8_53_IN_PERIOD_NOTES_NATIVE
import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';
import '../../core/widgets/record_widgets.dart';
import '../../models/module_data.dart';
import '../../models/mobile_record.dart';

class PerformancePeriodNotesScreen extends StatefulWidget {
  const PerformancePeriodNotesScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<PerformancePeriodNotesScreen> createState() => _PerformancePeriodNotesScreenState();
}

class _PerformancePeriodNotesScreenState extends State<PerformancePeriodNotesScreen> {
  late Future<ModuleData> _future;
  final TextEditingController _titleController = TextEditingController();
  final TextEditingController _noteController = TextEditingController();
  String _noteType = 'genel_gozlem';
  bool _remindDuringScoring = true;
  bool _includeInScorecard = false;
  bool _saving = false;
  bool _optionsLoading = true;
  List<Map<String, dynamic>> _periods = const <Map<String, dynamic>>[];
  List<Map<String, dynamic>> _users = const <Map<String, dynamic>>[];
  int? _selectedPeriodId;
  int? _selectedEmployeeId;

  static const List<Map<String, String>> _noteTypes = <Map<String, String>>[
    {'value': 'olumlu_olay', 'label': 'Olumlu Olay'},
    {'value': 'olumsuz_olay', 'label': 'Olumsuz Olay'},
    {'value': 'basari', 'label': 'Başarı'},
    {'value': 'gelisim_ihtiyaci', 'label': 'Gelişim İhtiyacı'},
    {'value': 'genel_gozlem', 'label': 'Genel Gözlem'},
  ];

  @override
  void initState() {
    super.initState();
    _future = _loadNotes();
    _loadOptions();
  }

  @override
  void dispose() {
    _titleController.dispose();
    _noteController.dispose();
    super.dispose();
  }

  Future<ModuleData> _loadNotes() async {
    final payload = await widget.apiClient.get('/api/mobile/performance/in-period-notes/v2');
    if (payload is! Map) throw StateError('Dönem içi notlar şu anda okunamadı.');
    return ModuleData.fromJson(Map<String, dynamic>.from(payload));
  }

  Future<void> _loadOptions() async {
    try {
      final payload = await widget.apiClient.get('/api/mobile/performance/in-period-note-options');
      final map = payload is Map ? Map<String, dynamic>.from(payload) : <String, dynamic>{};
      final periods = _mapList(map['periods']);
      final users = _mapList(map['users']);
      if (!mounted) return;
      setState(() {
        _periods = periods;
        _users = users;
        _selectedPeriodId = periods.isNotEmpty ? _asInt(periods.first['id']) : null;
        _selectedEmployeeId = users.isNotEmpty ? _asInt(users.first['id']) : null;
        _optionsLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _optionsLoading = false);
    }
  }

  Future<void> _refresh() async {
    setState(() => _future = _loadNotes());
    await Future.wait(<Future<void>>[_future.then((_) {}), _loadOptions()]);
  }

  Future<void> _saveNote() async {
    final note = _noteController.text.trim();
    if (note.isEmpty) {
      _showMessage('Not metni boş bırakılamaz.');
      return;
    }
    setState(() => _saving = true);
    try {
      await widget.apiClient.post('/api/mobile/performance/in-period-notes/v2', <String, dynamic>{
        'period_id': _selectedPeriodId,
        'employee_id': _selectedEmployeeId,
        'note_type': _noteType,
        'title': _titleController.text.trim(),
        'note': note,
        'remind_during_scoring': _remindDuringScoring,
        'include_in_scorecard': _includeInScorecard,
      });
      _titleController.clear();
      _noteController.clear();
      _includeInScorecard = false;
      _remindDuringScoring = true;
      _noteType = 'genel_gozlem';
      _showMessage('Dönem içi not kaydedildi.');
      await _refresh();
    } catch (error) {
      _showMessage('Dönem içi not şu anda kaydedilemedi. Lütfen tekrar deneyin.');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ModuleData>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const BYSLoadingState(message: 'Dönem içi notlar yükleniyor');
        }
        if (snapshot.hasError) {
          return BYSPage(
            title: 'Dönem İçi Notlar',
            subtitle: 'Ara gözlem ve gelişim notlarına şu anda ulaşılamadı.',
            badge: 'Dönem İçi Not',
            onRefresh: _refresh,
            children: <Widget>[
              ApiEmptyState(message: 'Dönem içi notlar şu anda alınamadı. Lütfen tekrar deneyin.', onRetry: () => setState(() => _future = _loadNotes())),
            ],
          );
        }

        final data = snapshot.data ?? const ModuleData(metrics: <ModuleMetric>[], items: <MobileRecord>[]);
        return BYSPage(
          title: 'Dönem İçi Notlar',
          subtitle: 'Olumlu/olumsuz olay, başarı, gelişim ihtiyacı ve genel gözlem notları mobilde de kaydedilir.',
          badge: 'Dönem İçi Not',
          onRefresh: _refresh,
          trailing: const Icon(Icons.edit_note_outlined, color: BYS360Colors.info, size: 52),
          children: <Widget>[
            const BYSInfoPanel(
              icon: Icons.shield_outlined,
              title: 'Puanı otomatik değiştirmez',
              body: 'Dönem içi notlar değerlendirme sırasında hatırlatma ve kurumsal hafıza sağlar; hiçbir personelin performans puanını otomatik üretmez.',
              tint: BYS360Colors.info,
            ),
            if (data.metrics.isNotEmpty) ...<Widget>[
              const BYSSectionTitle(title: 'Özet', subtitle: 'Yetki kapsamınızdaki dönem içi not verisi'),
              ...data.metrics.map((metric) => MetricCard(
                    title: metric.title,
                    value: metric.value,
                    subtitle: metric.subtitle,
                    icon: _icon(metric.icon),
                    tone: _tone(metric.tone),
                  )),
            ],
            const BYSSectionTitle(title: 'Yeni not ekle', subtitle: 'Yetki kapsamınızda personel ve dönem seçerek kayıt oluşturun'),
            _NoteFormCard(
              periods: _periods,
              users: _users,
              optionsLoading: _optionsLoading,
              selectedPeriodId: _selectedPeriodId,
              selectedEmployeeId: _selectedEmployeeId,
              noteType: _noteType,
              noteTypes: _noteTypes,
              titleController: _titleController,
              noteController: _noteController,
              remindDuringScoring: _remindDuringScoring,
              includeInScorecard: _includeInScorecard,
              saving: _saving,
              onPeriodChanged: (value) => setState(() => _selectedPeriodId = value),
              onEmployeeChanged: (value) => setState(() => _selectedEmployeeId = value),
              onNoteTypeChanged: (value) => setState(() => _noteType = value ?? 'genel_gozlem'),
              onRemindChanged: (value) => setState(() => _remindDuringScoring = value),
              onScorecardChanged: (value) => setState(() => _includeInScorecard = value),
              onSave: _saveNote,
            ),
            const BYSSectionTitle(title: 'Kayıtlı notlar', subtitle: 'Yetkiniz dahilindeki ara not ve gözlem kayıtları'),
            if (data.items.isEmpty)
              const BYSInfoPanel(
                icon: Icons.info_outline,
                title: 'Kayıt bulunmadı',
                body: 'Dönem içi not oluşturulduğunda bu alanda listelenecek.',
                tint: BYS360Colors.info,
              )
            else
              ...data.items.map((record) => RecordCard(
                    record: record,
                    icon: _icon(record.icon ?? 'note'),
                    tone: _tone(record.tone ?? 'info'),
                  )),
          ],
        );
      },
    );
  }
}

class _NoteFormCard extends StatelessWidget {
  const _NoteFormCard({
    required this.periods,
    required this.users,
    required this.optionsLoading,
    required this.selectedPeriodId,
    required this.selectedEmployeeId,
    required this.noteType,
    required this.noteTypes,
    required this.titleController,
    required this.noteController,
    required this.remindDuringScoring,
    required this.includeInScorecard,
    required this.saving,
    required this.onPeriodChanged,
    required this.onEmployeeChanged,
    required this.onNoteTypeChanged,
    required this.onRemindChanged,
    required this.onScorecardChanged,
    required this.onSave,
  });

  final List<Map<String, dynamic>> periods;
  final List<Map<String, dynamic>> users;
  final bool optionsLoading;
  final int? selectedPeriodId;
  final int? selectedEmployeeId;
  final String noteType;
  final List<Map<String, String>> noteTypes;
  final TextEditingController titleController;
  final TextEditingController noteController;
  final bool remindDuringScoring;
  final bool includeInScorecard;
  final bool saving;
  final ValueChanged<int?> onPeriodChanged;
  final ValueChanged<int?> onEmployeeChanged;
  final ValueChanged<String?> onNoteTypeChanged;
  final ValueChanged<bool> onRemindChanged;
  final ValueChanged<bool> onScorecardChanged;
  final VoidCallback onSave;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            if (optionsLoading)
              const Padding(
                padding: EdgeInsets.only(bottom: 12),
                child: LinearProgressIndicator(minHeight: 3),
              ),
            DropdownButtonFormField<int>(
              initialValue: _safeDropdownValue(periods, selectedPeriodId),
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Performans dönemi'),
              items: periods.map((row) {
                final id = _asInt(row['id']) ?? 0;
                return DropdownMenuItem<int>(value: id, child: Text(_label(row, 'title', 'Dönem')));
              }).toList(),
              onChanged: periods.isEmpty ? null : onPeriodChanged,
            ),
            const SizedBox(height: 10),
            DropdownButtonFormField<int>(
              initialValue: _safeDropdownValue(users, selectedEmployeeId),
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Personel'),
              items: users.map((row) {
                final id = _asInt(row['id']) ?? 0;
                return DropdownMenuItem<int>(value: id, child: Text(_label(row, 'name', 'Personel')));
              }).toList(),
              onChanged: users.isEmpty ? null : onEmployeeChanged,
            ),
            const SizedBox(height: 10),
            DropdownButtonFormField<String>(
              initialValue: noteType,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Not türü'),
              items: noteTypes.map((row) => DropdownMenuItem<String>(value: row['value'], child: Text(row['label'] ?? 'Not'))).toList(),
              onChanged: onNoteTypeChanged,
            ),
            const SizedBox(height: 10),
            TextField(
              controller: titleController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'Başlık (isteğe bağlı)', hintText: 'Örn. Tamamlanan önemli görev'),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: noteController,
              minLines: 4,
              maxLines: 7,
              decoration: const InputDecoration(labelText: 'Not metni', alignLabelWithHint: true, hintText: 'Gözlem, başarı, gelişim ihtiyacı veya ara geri bildirim yazın'),
            ),
            const SizedBox(height: 8),
            SwitchListTile.adaptive(
              value: remindDuringScoring,
              contentPadding: EdgeInsets.zero,
              title: const Text('Puanlama sırasında hatırlatılsın'),
              subtitle: const Text('Amire değerlendirme formunda destek bilgi olarak gösterilir.'),
              onChanged: onRemindChanged,
            ),
            SwitchListTile.adaptive(
              value: includeInScorecard,
              contentPadding: EdgeInsets.zero,
              title: const Text('Karne detayında gösterilsin'),
              subtitle: const Text('İşaretlenmezse yalnızca süreç hafızasında kalır.'),
              onChanged: onScorecardChanged,
            ),
            const SizedBox(height: 10),
            FilledButton.icon(
              onPressed: saving ? null : onSave,
              icon: saving ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.save_outlined),
              label: Text(saving ? 'Kaydediliyor' : 'Notu Kaydet'),
            ),
          ],
        ),
      ),
    );
  }
}

List<Map<String, dynamic>> _mapList(dynamic value) {
  if (value is! List) return const <Map<String, dynamic>>[];
  return value.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
}

int? _asInt(dynamic value) {
  if (value is int) return value;
  if (value is num) return value.toInt();
  return int.tryParse(value?.toString() ?? '');
}

int? _safeDropdownValue(List<Map<String, dynamic>> rows, int? selected) {
  if (selected == null) return null;
  for (final row in rows) {
    if (_asInt(row['id']) == selected) return selected;
  }
  return null;
}

String _label(Map<String, dynamic> row, String key, String fallback) {
  return (row[key] ?? row['title'] ?? row['name'] ?? fallback).toString();
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
      return BYS360Colors.danger;
    default:
      return BYS360Colors.corporateRed;
  }
}

IconData _icon(String icon) {
  switch (icon.toLowerCase()) {
    case 'note':
    case 'edit_note':
      return Icons.edit_note_outlined;
    case 'success':
      return Icons.emoji_events_outlined;
    case 'warning':
      return Icons.warning_amber_rounded;
    case 'development':
      return Icons.school_outlined;
    case 'person':
      return Icons.person_outline;
    case 'timeline':
      return Icons.timeline_outlined;
    default:
      return Icons.edit_note_outlined;
  }
}

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION

// BYS360_MOBILE_V2_8_68_QUALITY_CLEANUP
