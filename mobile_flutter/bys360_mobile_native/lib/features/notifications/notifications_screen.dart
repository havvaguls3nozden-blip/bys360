import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/utils/bys360_copy.dart';
import '../../core/utils/bys360_status_labels.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';
import '../../models/mobile_record.dart';
import '../../models/module_data.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

enum _NotificationFilter { all, unread, read }

class _NotificationsScreenState extends State<NotificationsScreen> {
  late Future<ModuleData> _future;
  _NotificationFilter _filter = _NotificationFilter.all;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<ModuleData> _load() async {
    final payload = await widget.apiClient.get('/api/mobile/notifications');
    if (payload is! Map) throw StateError('Bildirimler şu anda alınamadı.');
    return ModuleData.fromJson(Map<String, dynamic>.from(payload));
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  Future<void> _markAsRead(MobileRecord record) async {
    if (_busy || record.id.trim().isEmpty || _isRead(record)) return;
    setState(() => _busy = true);
    try {
      await widget.apiClient.post('/api/mobile/notifications/${record.id}/read', <String, dynamic>{});
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Bildirim okundu olarak işaretlendi.')));
      await _refresh();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Bildirim durumu güncellenemedi. Lütfen tekrar deneyin.')));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _markAllAsRead() async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      await widget.apiClient.post('/api/mobile/notifications/read-all', <String, dynamic>{});
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Okunmamış bildirimler okundu olarak işaretlendi.')));
      await _refresh();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Bildirimler güncellenemedi. Lütfen tekrar deneyin.')));
    } finally {
      if (mounted) setState(() => _busy = false);
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
            title: 'Bildirimlerim',
            subtitle: 'Size ulaşan süreç, görev ve sistem bilgilendirmeleri',
            badge: 'Bildirim',
            onRefresh: _refresh,
            children: [
              ApiEmptyState(
                title: 'Bildirimler açılamadı',
                message: 'Bildirimler şu anda alınamadı. Lütfen tekrar deneyin.',
                onRetry: () => setState(() => _future = _load()),
              ),
            ],
          );
        }

        final data = snapshot.data ?? const ModuleData(metrics: [], items: []);
        final items = _filteredItems(data.items);
        final unreadCount = data.items.where((item) => !_isRead(item)).length;
        return BYSPage(
          title: 'Bildirimlerim',
          subtitle: 'Size ulaşan süreç, görev ve sistem bilgilendirmeleri',
          badge: 'Bildirim',
          onRefresh: _refresh,
          children: [
            const BYSSectionTitle(title: 'Özet', subtitle: 'Yetkiniz kapsamındaki güncel bildirim durumu'),
            if (data.metrics.isEmpty)
              const BYSInfoPanel(
                icon: Icons.notifications_none_outlined,
                title: 'Bildirim özeti bulunamadı',
                body: 'Şu anda görüntülenecek bildirim özeti bulunmuyor.',
                tint: BYS360Colors.warning,
              )
            else
              ...data.metrics.map((metric) => MetricCard(
                    title: metric.title,
                    value: metric.value,
                    subtitle: metric.subtitle,
                    icon: _metricIcon(metric.icon),
                    tone: _tone(metric.tone),
                  )),
            BYSSectionTitle(
              title: 'Bildirim Listesi',
              subtitle: 'Okunmuş ve okunmamış bildirimlerinizi takip edin',
              action: unreadCount > 0
                  ? TextButton.icon(
                      onPressed: _busy ? null : _markAllAsRead,
                      icon: const Icon(Icons.done_all_outlined, size: 18),
                      label: const Text('Tümünü Okundu Yap'),
                    )
                  : null,
            ),
            _FilterBar(value: _filter, onChanged: (value) => setState(() => _filter = value)),
            if (items.isEmpty)
              ApiEmptyState(
                title: _emptyTitle(),
                message: _emptyMessage(),
                onRetry: () => setState(() => _future = _load()),
              )
            else
              ...items.map((record) => _NotificationCard(
                    record: record,
                    isRead: _isRead(record),
                    isBusy: _busy,
                    onOpen: () => _showDetail(record),
                    onMarkRead: () => _markAsRead(record),
                  )),
          ],
        );
      },
    );
  }

  List<MobileRecord> _filteredItems(List<MobileRecord> items) {
    switch (_filter) {
      case _NotificationFilter.unread:
        return items.where((item) => !_isRead(item)).toList();
      case _NotificationFilter.read:
        return items.where(_isRead).toList();
      case _NotificationFilter.all:
        return items;
    }
  }

  bool _isRead(MobileRecord record) {
    final status = (record.status ?? '').toLowerCase().trim();
    return status == 'okundu' || status == 'read';
  }

  String _emptyTitle() {
    switch (_filter) {
      case _NotificationFilter.unread:
        return 'Okunmamış bildiriminiz bulunmuyor';
      case _NotificationFilter.read:
        return 'Okunmuş bildiriminiz bulunmuyor';
      case _NotificationFilter.all:
        return 'Bildirim bulunmuyor';
    }
  }

  String _emptyMessage() {
    switch (_filter) {
      case _NotificationFilter.unread:
        return 'Yeni bir bildirim geldiğinde bu alanda görünecektir.';
      case _NotificationFilter.read:
        return 'Okuduğunuz bildirimler bu alanda listelenecektir.';
      case _NotificationFilter.all:
        return 'Size ait bildirim kaydı oluştuğunda burada görüntülenir.';
    }
  }

  Future<void> _showDetail(MobileRecord record) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => _NotificationDetailSheet(record: record, isRead: _isRead(record), onMarkRead: () async {
        Navigator.of(context).pop();
        await _markAsRead(record);
      }),
    );
  }

  IconData _metricIcon(String icon) {
    switch (icon.toLowerCase()) {
      case 'list':
        return Icons.list_alt_outlined;
      case 'done':
      case 'check':
        return Icons.done_all_outlined;
      case 'notifications':
      default:
        return Icons.notifications_outlined;
    }
  }

  Color _tone(String tone) {
    switch (tone.toLowerCase()) {
      case 'green':
      case 'success':
        return BYS360Colors.success;
      case 'red':
      case 'danger':
        return BYS360Colors.corporateRed;
      case 'blue':
      case 'info':
        return BYS360Colors.info;
      case 'purple':
        return BYS360Colors.purple;
      case 'yellow':
      case 'warning':
      default:
        return BYS360Colors.warning;
    }
  }
}

class _FilterBar extends StatelessWidget {
  const _FilterBar({required this.value, required this.onChanged});

  final _NotificationFilter value;
  final ValueChanged<_NotificationFilter> onChanged;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Row(
          children: [
            _FilterChipButton(label: 'Tümü', selected: value == _NotificationFilter.all, onTap: () => onChanged(_NotificationFilter.all)),
            const SizedBox(width: 8),
            _FilterChipButton(label: 'Okunmamış', selected: value == _NotificationFilter.unread, onTap: () => onChanged(_NotificationFilter.unread)),
            const SizedBox(width: 8),
            _FilterChipButton(label: 'Okunmuş', selected: value == _NotificationFilter.read, onTap: () => onChanged(_NotificationFilter.read)),
          ],
        ),
      ),
    );
  }
}

class _FilterChipButton extends StatelessWidget {
  const _FilterChipButton({required this.label, required this.selected, required this.onTap});

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
            style: TextStyle(
              color: selected ? Colors.white : BYS360Colors.ink,
              fontWeight: FontWeight.w900,
              fontSize: 12,
              decoration: TextDecoration.none,
            ),
          ),
        ),
      ),
    );
  }
}

class _NotificationCard extends StatelessWidget {
  const _NotificationCard({required this.record, required this.isRead, required this.isBusy, required this.onOpen, required this.onMarkRead});

  final MobileRecord record;
  final bool isRead;
  final bool isBusy;
  final VoidCallback onOpen;
  final VoidCallback onMarkRead;

  @override
  Widget build(BuildContext context) {
    final tone = isRead ? BYS360Colors.info : BYS360Colors.warning;
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
                    child: Icon(isRead ? Icons.mark_email_read_outlined : Icons.notifications_active_outlined, color: tone),
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
                  const SizedBox(width: 8),
                  _StatusBadge(text: isRead ? 'Okundu' : 'Okunmadı', tone: tone),
                ],
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  if ((record.meta ?? '').trim().isNotEmpty) _MiniMeta(icon: Icons.schedule_outlined, text: record.meta!),
                  if ((record.value ?? '').trim().isNotEmpty) _MiniMeta(icon: Icons.label_outline, text: record.value!),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: onOpen,
                      icon: const Icon(Icons.visibility_outlined, size: 18),
                      label: const Text('Detay'),
                    ),
                  ),
                  if (!isRead) ...[
                    const SizedBox(width: 10),
                    Expanded(
                      child: FilledButton.icon(
                        onPressed: isBusy ? null : onMarkRead,
                        icon: const Icon(Icons.done_outlined, size: 18),
                        label: const Text('Okundu Yap'),
                      ),
                    ),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _NotificationDetailSheet extends StatelessWidget {
  const _NotificationDetailSheet({required this.record, required this.isRead, required this.onMarkRead});

  final MobileRecord record;
  final bool isRead;
  final Future<void> Function() onMarkRead;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Container(
        margin: const EdgeInsets.all(12),
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(BYS360Radii.xl), boxShadow: BYS360Shadows.elevated),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(child: Text('Bildirim Detayı', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900))),
                IconButton(onPressed: () => Navigator.of(context).pop(), icon: const Icon(Icons.close)),
              ],
            ),
            const SizedBox(height: 10),
            Text(record.title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
            if ((record.subtitle ?? '').trim().isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(record.subtitle!, style: const TextStyle(color: BYS360Colors.mutedText, height: 1.36)),
            ],
            const SizedBox(height: 14),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _StatusBadge(text: isRead ? 'Okundu' : 'Okunmadı', tone: isRead ? BYS360Colors.info : BYS360Colors.warning),
                if ((record.meta ?? '').trim().isNotEmpty) _MiniMeta(icon: Icons.schedule_outlined, text: record.meta!),
                if ((record.value ?? '').trim().isNotEmpty) _MiniMeta(icon: Icons.label_outline, text: record.value!),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(child: OutlinedButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Kapat'))),
                if (!isRead) ...[
                  const SizedBox(width: 10),
                  Expanded(child: FilledButton.icon(onPressed: onMarkRead, icon: const Icon(Icons.done_outlined), label: const Text('Okundu Yap'))),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.text, required this.tone});

  final String text;
  final Color tone;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(color: tone.withValues(alpha: .10), borderRadius: BorderRadius.circular(999), border: Border.all(color: tone.withValues(alpha: .20))),
      child: Text(text, style: TextStyle(color: tone, fontWeight: FontWeight.w900, fontSize: 11, decoration: TextDecoration.none)),
    );
  }
}

class _MiniMeta extends StatelessWidget {
  const _MiniMeta({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    final label = bys360GenericStatusLabel(BYS360Copy.clean(text));
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
      decoration: BoxDecoration(color: BYS360Colors.surfaceSoft, borderRadius: BorderRadius.circular(999), border: Border.all(color: BYS360Colors.cardBorder)),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: BYS360Colors.mutedText),
          const SizedBox(width: 5),
          Text(label, style: const TextStyle(color: BYS360Colors.mutedText, fontWeight: FontWeight.w800, fontSize: 11, decoration: TextDecoration.none)),
        ],
      ),
    );
  }
}

// BYS360_MOBILE_V2_8_64_NOTIFICATIONS_COMPLETION

// BYS360_MOBILE_V2_8_74_ANDROID_RELEASE_READY_P0_NOTIFICATION_COPY
