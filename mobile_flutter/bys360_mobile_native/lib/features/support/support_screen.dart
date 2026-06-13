import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/utils/bys360_copy.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';
import '../../core/widgets/record_widgets.dart';
import '../../models/mobile_record.dart';
import '../../models/module_data.dart';
import 'support_ticket_detail_screen.dart';

enum _SupportFilter { all, open, closed }

class SupportScreen extends StatefulWidget {
  const SupportScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<SupportScreen> createState() => _SupportScreenState();
}

class _SupportScreenState extends State<SupportScreen> {
  late Future<ModuleData> _future;
  _SupportFilter _filter = _SupportFilter.all;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<ModuleData> _load() async {
    final payload = await widget.apiClient.get('/api/mobile/support/tickets');
    if (payload is! Map) throw StateError('Destek talepleri şu anda alınamadı.');
    return ModuleData.fromJson(Map<String, dynamic>.from(payload));
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  Future<void> _openDetail(MobileRecord record) async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => SupportTicketDetailScreen(
          apiClient: widget.apiClient,
          ticketId: record.id,
          fallbackTitle: record.title,
        ),
      ),
    );
    if (mounted) setState(() => _future = _load());
  }

  Future<void> _openCreateSheet() async {
    final created = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _CreateSupportTicketSheet(apiClient: widget.apiClient),
    );
    if (created == true && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Destek talebi oluşturuldu.')));
      setState(() => _future = _load());
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ModuleData>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return const BYSLoadingState();
        if (snapshot.hasError) {
          return BYSPage(
            title: 'Destek Taleplerim',
            subtitle: 'Talep oluşturabilir, mevcut taleplerinizi takip edebilirsiniz',
            badge: 'Destek',
            onRefresh: _refresh,
            children: [
              ApiEmptyState(
                title: 'Destek talepleri açılamadı',
                message: 'Destek talepleri şu anda alınamadı. Lütfen bağlantınızı kontrol edip tekrar deneyin.',
                onRetry: () => setState(() => _future = _load()),
              ),
              _CreateTicketAction(onTap: _openCreateSheet),
            ],
          );
        }

        final data = snapshot.data ?? const ModuleData(metrics: [], items: []);
        final items = _filteredItems(data.items);
        return BYSPage(
          title: 'Destek Taleplerim',
          subtitle: 'Talep oluşturabilir, mevcut taleplerinizi takip edebilir ve cevap yazabilirsiniz',
          badge: 'Destek',
          onRefresh: _refresh,
          children: [
            _CreateTicketAction(onTap: _openCreateSheet),
            const BYSSectionTitle(title: 'Destek Özeti', subtitle: 'Size ait destek taleplerinin güncel durumu'),
            if (data.metrics.isEmpty)
              const BYSInfoPanel(
                icon: Icons.support_agent_outlined,
                title: 'Destek özeti bulunamadı',
                body: 'Şu anda görüntülenecek destek özeti bulunmuyor.',
                tint: BYS360Colors.info,
              )
            else
              ...data.metrics.map((metric) => MetricCard(
                    title: metric.title,
                    value: metric.value,
                    subtitle: metric.subtitle,
                    icon: _metricIcon(metric.icon),
                    tone: _tone(metric.tone),
                  )),
            const BYSSectionTitle(title: 'Talep Listesi', subtitle: 'Açık ve sonuçlanan destek taleplerinizi takip edin'),
            _SupportFilterBar(value: _filter, onChanged: (value) => setState(() => _filter = value)),
            if (items.isEmpty)
              ApiEmptyState(
                title: _emptyTitle(),
                message: _emptyMessage(),
                onRetry: () => setState(() => _future = _load()),
              )
            else
              ...items.map((record) => _SupportTicketCard(record: record, onOpen: () => _openDetail(record))),
          ],
        );
      },
    );
  }

  List<MobileRecord> _filteredItems(List<MobileRecord> items) {
    switch (_filter) {
      case _SupportFilter.open:
        return items.where((item) => !_isClosed(item)).toList();
      case _SupportFilter.closed:
        return items.where(_isClosed).toList();
      case _SupportFilter.all:
        return items;
    }
  }

  bool _isClosed(MobileRecord record) {
    final status = (record.status ?? '').toLowerCase().trim();
    return {'kapalı', 'kapali', 'closed', 'çözüldü', 'cozuldu', 'resolved', 'reddedildi', 'rejected'}.contains(status);
  }

  String _emptyTitle() {
    switch (_filter) {
      case _SupportFilter.open:
        return 'Açık destek talebiniz bulunmuyor';
      case _SupportFilter.closed:
        return 'Sonuçlanmış destek talebiniz bulunmuyor';
      case _SupportFilter.all:
        return 'Destek talebiniz bulunmuyor';
    }
  }

  String _emptyMessage() {
    switch (_filter) {
      case _SupportFilter.open:
        return 'Yeni destek talebi oluşturduğunuzda veya açık talebiniz olduğunda burada görünecektir.';
      case _SupportFilter.closed:
        return 'Sonuçlanan destek talepleriniz bu alanda listelenecektir.';
      case _SupportFilter.all:
        return 'Yardım ihtiyacınız olduğunda yeni destek talebi oluşturabilirsiniz.';
    }
  }

  IconData _metricIcon(String value) {
    switch (value.toLowerCase()) {
      case 'done':
      case 'check':
        return Icons.check_circle_outline;
      case 'list':
        return Icons.list_alt_outlined;
      case 'support':
      default:
        return Icons.support_agent_outlined;
    }
  }

  Color _tone(String value) {
    switch (value.toLowerCase()) {
      case 'green':
      case 'success':
        return BYS360Colors.success;
      case 'yellow':
      case 'warning':
        return BYS360Colors.warning;
      case 'red':
      case 'danger':
        return BYS360Colors.corporateRed;
      case 'purple':
        return BYS360Colors.purple;
      case 'blue':
      case 'info':
      default:
        return BYS360Colors.info;
    }
  }
}

class _CreateTicketAction extends StatelessWidget {
  const _CreateTicketAction({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ActionTile(
      title: 'Yeni destek talebi oluştur',
      subtitle: 'Sorununuzu veya talebinizi destek birimine iletin',
      icon: Icons.add_circle_outline,
      tone: BYS360Colors.info,
      onTap: onTap,
    );
  }
}

class _SupportFilterBar extends StatelessWidget {
  const _SupportFilterBar({required this.value, required this.onChanged});

  final _SupportFilter value;
  final ValueChanged<_SupportFilter> onChanged;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Row(
          children: [
            _FilterButton(label: 'Tümü', selected: value == _SupportFilter.all, onTap: () => onChanged(_SupportFilter.all)),
            const SizedBox(width: 8),
            _FilterButton(label: 'Açık', selected: value == _SupportFilter.open, onTap: () => onChanged(_SupportFilter.open)),
            const SizedBox(width: 8),
            _FilterButton(label: 'Sonuçlanan', selected: value == _SupportFilter.closed, onTap: () => onChanged(_SupportFilter.closed)),
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
      child: InkWell(
        borderRadius: BorderRadius.circular(999),
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
          decoration: BoxDecoration(
            color: selected ? BYS360Colors.corporateRed : BYS360Colors.surfaceSoft,
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: selected ? BYS360Colors.corporateRed : BYS360Colors.cardBorder),
          ),
          child: Text(
            label,
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(color: selected ? Colors.white : BYS360Colors.ink, fontWeight: FontWeight.w900, fontSize: 12, decoration: TextDecoration.none),
          ),
        ),
      ),
    );
  }
}

class _SupportTicketCard extends StatelessWidget {
  const _SupportTicketCard({required this.record, required this.onOpen});

  final MobileRecord record;
  final VoidCallback onOpen;

  @override
  Widget build(BuildContext context) {
    final tone = _statusTone(record.status ?? '');
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(BYS360Radii.lg),
        onTap: onOpen,
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
                    child: Icon(Icons.support_agent_outlined, color: tone),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(record.title, maxLines: 2, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
                        if ((record.subtitle ?? '').trim().isNotEmpty) ...[
                          const SizedBox(height: 5),
                          Text(record.subtitle!, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(color: BYS360Colors.mutedText, height: 1.30)),
                        ],
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
                  if ((record.status ?? '').trim().isNotEmpty) StatusPill(text: record.status!, tone: tone),
                  if ((record.value ?? '').trim().isNotEmpty) StatusPill(text: record.value!, tone: BYS360Colors.info),
                  if ((record.meta ?? '').trim().isNotEmpty) StatusPill(text: record.meta!, tone: BYS360Colors.warning),
                ],
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(onPressed: onOpen, icon: const Icon(Icons.visibility_outlined, size: 18), label: const Text('Detayı Aç')),
            ],
          ),
        ),
      ),
    );
  }

  Color _statusTone(String status) {
    final value = status.toLowerCase().trim();
    if ({'kapalı', 'kapali', 'closed', 'çözüldü', 'cozuldu', 'resolved'}.contains(value)) return BYS360Colors.success;
    if ({'beklemede', 'waiting_info', 'planned'}.contains(value)) return BYS360Colors.warning;
    if ({'reddedildi', 'rejected'}.contains(value)) return BYS360Colors.corporateRed;
    return BYS360Colors.info;
  }
}

class _CreateSupportTicketSheet extends StatefulWidget {
  const _CreateSupportTicketSheet({required this.apiClient});

  final ApiClient apiClient;

  @override
  State<_CreateSupportTicketSheet> createState() => _CreateSupportTicketSheetState();
}

class _CreateSupportTicketSheetState extends State<_CreateSupportTicketSheet> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final TextEditingController _titleController = TextEditingController();
  final TextEditingController _descriptionController = TextEditingController();
  String _moduleName = 'Mobil Uygulama';
  String _priority = 'normal';
  bool _saving = false;

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _create() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() => _saving = true);
    try {
      await widget.apiClient.post('/api/mobile/support/tickets', <String, dynamic>{
        'title': _titleController.text.trim(),
        'description': _descriptionController.text.trim(),
        'module_name': _moduleName,
        'priority': _priority,
        'ticket_type': 'mobile_support',
      });
      if (mounted) Navigator.of(context).pop(true);
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(BYS360Copy.error(error))));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.of(context).viewInsets.bottom;
    return AnimatedPadding(
      duration: const Duration(milliseconds: 160),
      curve: Curves.easeOut,
      padding: EdgeInsets.only(bottom: bottom),
      child: Container(
        decoration: const BoxDecoration(color: BYS360Colors.pageBackground, borderRadius: BorderRadius.vertical(top: Radius.circular(28))),
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Center(child: Container(width: 42, height: 5, decoration: BoxDecoration(color: BYS360Colors.cardBorder, borderRadius: BorderRadius.circular(999)))),
                const SizedBox(height: 14),
                Text('Yeni destek talebi', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
                const SizedBox(height: 5),
                const Text('Sorununuzu veya talebinizi kısa ve anlaşılır şekilde yazın.', style: TextStyle(color: BYS360Colors.mutedText, height: 1.25)),
                const SizedBox(height: 14),
                TextFormField(
                  controller: _titleController,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(labelText: 'Başlık', hintText: 'Örn. Mobilde personel listesi açılmıyor'),
                  validator: (value) => (value ?? '').trim().length < 3 ? 'Başlık en az 3 karakter olmalı.' : null,
                ),
                const SizedBox(height: 10),
                TextFormField(
                  controller: _descriptionController,
                  minLines: 4,
                  maxLines: 7,
                  decoration: const InputDecoration(labelText: 'Açıklama', hintText: 'Talebinizi veya yaşadığınız sorunu yazın'),
                  validator: (value) => (value ?? '').trim().length < 5 ? 'Açıklama en az 5 karakter olmalı.' : null,
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  initialValue: _moduleName,
                  decoration: const InputDecoration(labelText: 'İlgili alan'),
                  items: const [
                    DropdownMenuItem(value: 'Mobil Uygulama', child: Text('Mobil Uygulama')),
                    DropdownMenuItem(value: 'Personel Yönetimi', child: Text('Personel Yönetimi')),
                    DropdownMenuItem(value: 'Performans Yönetimi', child: Text('Performans Yönetimi')),
                    DropdownMenuItem(value: 'Destek Talepleri', child: Text('Destek Talepleri')),
                    DropdownMenuItem(value: 'Anketler', child: Text('Anketler')),
                    DropdownMenuItem(value: 'Sistem Ayarları', child: Text('Sistem Ayarları')),
                  ],
                  onChanged: (value) => setState(() => _moduleName = value ?? 'Mobil Uygulama'),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  initialValue: _priority,
                  decoration: const InputDecoration(labelText: 'Öncelik'),
                  items: const [
                    DropdownMenuItem(value: 'low', child: Text('Düşük')),
                    DropdownMenuItem(value: 'normal', child: Text('Normal')),
                    DropdownMenuItem(value: 'high', child: Text('Yüksek')),
                    DropdownMenuItem(value: 'critical', child: Text('Kritik')),
                  ],
                  onChanged: (value) => setState(() => _priority = value ?? 'normal'),
                ),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: _saving ? null : _create,
                  icon: _saving ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.save_outlined),
                  label: Text(_saving ? 'Kaydediliyor' : 'Talebi Oluştur'),
                ),
                const SizedBox(height: 8),
                OutlinedButton.icon(onPressed: _saving ? null : () => Navigator.of(context).pop(false), icon: const Icon(Icons.close), label: const Text('Vazgeç')),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// BYS360_MOBILE_V2_8_65_SUPPORT_COMPLETION
