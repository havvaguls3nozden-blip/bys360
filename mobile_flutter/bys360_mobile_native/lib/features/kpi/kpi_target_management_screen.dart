// BYS360_MOBILE_V2_8_53_KPI_TARGET_MANAGEMENT_NATIVE
import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/utils/bys360_copy.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';
import '../../core/widgets/record_widgets.dart';
import '../../models/module_data.dart';
import '../../models/mobile_record.dart';

class KpiTargetManagementScreen extends StatefulWidget {
  const KpiTargetManagementScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<KpiTargetManagementScreen> createState() => _KpiTargetManagementScreenState();
}

class _KpiTargetManagementScreenState extends State<KpiTargetManagementScreen> {
  late Future<ModuleData> _future;
  final TextEditingController _targetNameController = TextEditingController();
  final TextEditingController _descriptionController = TextEditingController();
  final TextEditingController _categoryController = TextEditingController();
  final TextEditingController _targetValueController = TextEditingController();
  final TextEditingController _currentValueController = TextEditingController();
  String _targetType = 'personnel';
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _future = _loadTargets();
  }

  @override
  void dispose() {
    _targetNameController.dispose();
    _descriptionController.dispose();
    _categoryController.dispose();
    _targetValueController.dispose();
    _currentValueController.dispose();
    super.dispose();
  }

  Future<ModuleData> _loadTargets() async {
    final payload = await widget.apiClient.get('/api/mobile/kpi/target-management');
    if (payload is! Map) throw StateError('KPI/Hedef verisi şu anda okunamadı.');
    return ModuleData.fromJson(Map<String, dynamic>.from(payload));
  }

  Future<void> _refresh() async {
    setState(() => _future = _loadTargets());
    await _future;
  }

  Future<void> _createTarget() async {
    final name = _targetNameController.text.trim();
    if (name.isEmpty) {
      _showMessage('Hedef adı boş bırakılamaz.');
      return;
    }
    setState(() => _saving = true);
    try {
      await widget.apiClient.post('/api/mobile/kpi/target-management', <String, dynamic>{
        'target_name': name,
        'description': _descriptionController.text.trim(),
        'category': _categoryController.text.trim(),
        'target_type': _targetType,
        'target_value': _targetValueController.text.trim(),
        'current_value': _currentValueController.text.trim(),
      });
      _targetNameController.clear();
      _descriptionController.clear();
      _categoryController.clear();
      _targetValueController.clear();
      _currentValueController.clear();
      _targetType = 'personnel';
      _showMessage('KPI hedef kartı oluşturuldu.');
      await _refresh();
    } catch (error) {
      _showMessage(BYS360Copy.error(error));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _openProgressDialog(MobileRecord record) async {
    final controller = TextEditingController(text: _cleanNumber(record.value));
    final result = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(record.title),
        content: TextField(
          controller: controller,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(
            labelText: 'Gerçekleşen değer',
            hintText: 'Örn. 82',
          ),
        ),
        actions: <Widget>[
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Vazgeç')),
          FilledButton(onPressed: () => Navigator.pop(context, controller.text.trim()), child: const Text('Güncelle')),
        ],
      ),
    );
    controller.dispose();
    if (result == null || result.trim().isEmpty) return;
    try {
      await widget.apiClient.post('/api/mobile/kpi/target-management/${record.id}/progress', <String, dynamic>{'current_value': result.trim()});
      _showMessage('KPI gerçekleşme değeri güncellendi.');
      await _refresh();
    } catch (error) {
      _showMessage(BYS360Copy.error(error));
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
          return const BYSLoadingState(message: 'KPI hedefleri yükleniyor');
        }
        if (snapshot.hasError) {
          return BYSPage(
            title: 'KPI / Hedef Yönetimi',
            subtitle: 'SP-1 hedef verisine şu anda ulaşılamadı.',
            badge: 'KPI Hedef V2.8.53',
            onRefresh: _refresh,
            children: <Widget>[
              ApiEmptyState(message: snapshot.error.toString(), onRetry: () => setState(() => _future = _loadTargets())),
            ],
          );
        }
        final data = snapshot.data ?? const ModuleData(metrics: <ModuleMetric>[], items: <MobileRecord>[]);
        return BYSPage(
          title: 'KPI / Hedef Yönetimi',
          subtitle: 'Hedef kartı oluşturma, gerçekleşme güncelleme, risk ve başarı oranı takibi mobilde de yapılır.',
          badge: 'KPI Hedef V2.8.53',
          onRefresh: _refresh,
          trailing: const Icon(Icons.flag_outlined, color: BYS360Colors.success, size: 52),
          children: <Widget>[
            const BYSInfoPanel(
              icon: Icons.insights_outlined,
              title: 'SP-1 hedef motoru',
              body: 'KPI/Hedef Yönetimi performans puanını kendiliğinden değiştirmez; hedef gerçekleşme ve yönetici görünürlüğü için veri üretir.',
              tint: BYS360Colors.success,
            ),
            if (data.metrics.isNotEmpty) ...<Widget>[
              const BYSSectionTitle(title: 'KPI özeti', subtitle: 'Canlı hedef gerçekleşme ve risk görünümü'),
              ...data.metrics.map((metric) => MetricCard(
                    title: metric.title,
                    value: metric.value,
                    subtitle: metric.subtitle,
                    icon: _icon(metric.icon),
                    tone: _tone(metric.tone),
                  )),
            ],
            const BYSSectionTitle(title: 'Yeni hedef kartı', subtitle: 'Kurumsal, birim veya personel hedefi oluşturun'),
            _TargetFormCard(
              targetNameController: _targetNameController,
              descriptionController: _descriptionController,
              categoryController: _categoryController,
              targetValueController: _targetValueController,
              currentValueController: _currentValueController,
              targetType: _targetType,
              saving: _saving,
              onTargetTypeChanged: (value) => setState(() => _targetType = value ?? 'personnel'),
              onSave: _createTarget,
            ),
            const BYSSectionTitle(title: 'Hedef kartları', subtitle: 'Gerçekleşme değeri ve risk durumu'),
            if (data.items.isEmpty)
              const BYSInfoPanel(
                icon: Icons.info_outline,
                title: 'Hedef kaydı bulunmadı',
                body: 'Yeni hedef kartı oluşturduğunuzda burada listelenecek.',
                tint: BYS360Colors.info,
              )
            else
              ...data.items.map((record) => _TargetRecordCard(record: record, onUpdateProgress: () => _openProgressDialog(record))),
          ],
        );
      },
    );
  }
}

class _TargetFormCard extends StatelessWidget {
  const _TargetFormCard({
    required this.targetNameController,
    required this.descriptionController,
    required this.categoryController,
    required this.targetValueController,
    required this.currentValueController,
    required this.targetType,
    required this.saving,
    required this.onTargetTypeChanged,
    required this.onSave,
  });

  final TextEditingController targetNameController;
  final TextEditingController descriptionController;
  final TextEditingController categoryController;
  final TextEditingController targetValueController;
  final TextEditingController currentValueController;
  final String targetType;
  final bool saving;
  final ValueChanged<String?> onTargetTypeChanged;
  final VoidCallback onSave;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            TextField(
              controller: targetNameController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'Hedef adı', hintText: 'Örn. Birim iş tamamlama oranı'),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: descriptionController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'Açıklama (isteğe bağlı)'),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: categoryController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'Kategori', hintText: 'KPI / Operasyon / Stratejik'),
            ),
            const SizedBox(height: 10),
            DropdownButtonFormField<String>(
              initialValue: targetType,
              decoration: const InputDecoration(labelText: 'Hedef tipi'),
              items: const <DropdownMenuItem<String>>[
                DropdownMenuItem<String>(value: 'institution', child: Text('Kurumsal')),
                DropdownMenuItem<String>(value: 'unit', child: Text('Birim')),
                DropdownMenuItem<String>(value: 'personnel', child: Text('Personel')),
              ],
              onChanged: onTargetTypeChanged,
            ),
            const SizedBox(height: 10),
            Row(
              children: <Widget>[
                Expanded(
                  child: TextField(
                    controller: targetValueController,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(labelText: 'Hedef değer'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: TextField(
                    controller: currentValueController,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(labelText: 'Gerçekleşen'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: saving ? null : onSave,
              icon: saving ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.add_task_outlined),
              label: Text(saving ? 'Oluşturuluyor' : 'Hedef Kartı Oluştur'),
            ),
          ],
        ),
      ),
    );
  }
}

class _TargetRecordCard extends StatelessWidget {
  const _TargetRecordCard({required this.record, required this.onUpdateProgress});

  final MobileRecord record;
  final VoidCallback onUpdateProgress;

  @override
  Widget build(BuildContext context) {
    final tone = _tone(record.tone ?? 'success');
    final progress = record.progress?.clamp(0, 100) ?? 0;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(color: tone.withValues(alpha: .10), borderRadius: BorderRadius.circular(15)),
                  child: Icon(_icon(record.icon ?? 'flag'), color: tone, size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(record.title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900), maxLines: 2, overflow: TextOverflow.ellipsis),
                      if ((record.subtitle ?? '').trim().isNotEmpty) ...<Widget>[
                        const SizedBox(height: 3),
                        Text(record.subtitle!, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText), maxLines: 2, overflow: TextOverflow.ellipsis),
                      ],
                    ],
                  ),
                ),
                Text('%$progress', style: Theme.of(context).textTheme.titleMedium?.copyWith(color: tone, fontWeight: FontWeight.w900)),
              ],
            ),
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(999),
              child: LinearProgressIndicator(value: progress / 100, minHeight: 8, backgroundColor: tone.withValues(alpha: .12), color: tone),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: <Widget>[
                if ((record.status ?? '').trim().isNotEmpty) StatusPill(text: record.status!, tone: tone),
                if ((record.meta ?? '').trim().isNotEmpty) StatusPill(text: record.meta!, tone: BYS360Colors.info),
                if ((record.value ?? '').trim().isNotEmpty) StatusPill(text: record.value!, tone: BYS360Colors.success),
              ],
            ),
            const SizedBox(height: 10),
            Align(
              alignment: Alignment.centerRight,
              child: OutlinedButton.icon(
                onPressed: onUpdateProgress,
                icon: const Icon(Icons.trending_up),
                label: const Text('Gerçekleşme Güncelle'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

String _cleanNumber(String? value) {
  final raw = (value ?? '').replaceAll('%', '').replaceAll('/100', '').trim();
  return raw;
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
    case 'flag':
      return Icons.flag_outlined;
    case 'target':
      return Icons.track_changes_outlined;
    case 'warning':
      return Icons.warning_amber_rounded;
    case 'trending_up':
      return Icons.trending_up;
    case 'dashboard':
      return Icons.dashboard_customize_outlined;
    case 'api':
      return Icons.hub_outlined;
    case 'shield':
      return Icons.shield_outlined;
    default:
      return Icons.flag_outlined;
  }
}

// BYS360_MOBILE_V2_8_68_QUALITY_CLEANUP
