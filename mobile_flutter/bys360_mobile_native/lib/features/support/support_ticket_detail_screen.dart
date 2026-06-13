import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/utils/bys360_copy.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/record_widgets.dart';
import 'support_models.dart';

class SupportTicketDetailScreen extends StatefulWidget {
  const SupportTicketDetailScreen({
    super.key,
    required this.apiClient,
    required this.ticketId,
    required this.fallbackTitle,
  });

  final ApiClient apiClient;
  final String ticketId;
  final String fallbackTitle;

  @override
  State<SupportTicketDetailScreen> createState() => _SupportTicketDetailScreenState();
}

class _SupportTicketDetailScreenState extends State<SupportTicketDetailScreen> {
  late Future<SupportTicketDetail> _future;
  final TextEditingController _replyController = TextEditingController();
  bool _saving = false;
  bool _internalNote = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  @override
  void dispose() {
    _replyController.dispose();
    super.dispose();
  }

  Future<SupportTicketDetail> _load() async {
    final payload = await widget.apiClient.get('/api/mobile/support/tickets/${widget.ticketId}');
    if (payload is! Map) throw StateError('Destek talebi detayı şu anda alınamadı.');
    return SupportTicketDetail.fromJson(Map<String, dynamic>.from(payload));
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  Future<void> _sendReply(SupportTicketDetail detail) async {
    final message = _replyController.text.trim();
    if (message.length < 3) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Cevap alanı boş bırakılamaz.')));
      return;
    }
    setState(() => _saving = true);
    try {
      await widget.apiClient.post('/api/mobile/support/tickets/${widget.ticketId}/reply', <String, dynamic>{
        'message': message,
        'is_internal': detail.canManage && _internalNote,
      });
      _replyController.clear();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Cevabınız destek talebine eklendi.')));
      await _refresh();
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(BYS360Copy.error(error))));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: FutureBuilder<SupportTicketDetail>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) return const BYSLoadingState();
          if (snapshot.hasError) {
            return BYSPage(
              title: 'Talep Detayı',
              subtitle: 'Destek talebi bilgisi şu anda alınamadı',
              badge: 'Destek',
              onRefresh: _refresh,
              children: [
                ApiEmptyState(
                  title: 'Talep detayı açılamadı',
                  message: 'Destek talebi detayı şu anda alınamadı. Lütfen tekrar deneyin.',
                  onRetry: () => setState(() => _future = _load()),
                ),
              ],
            );
          }

          final detail = snapshot.data!;
          final ticket = detail.ticket;
          return BYSPage(
            title: ticket.title,
            subtitle: '${ticket.ticketNo} · ${ticket.moduleName}',
            badge: ticket.statusLabel,
            onRefresh: _refresh,
            children: [
              _TicketSummaryCard(detail: detail),
              _TicketDescriptionCard(ticket: ticket),
              _ReplyCard(
                detail: detail,
                controller: _replyController,
                saving: _saving,
                internalNote: _internalNote,
                onInternalChanged: (value) => setState(() => _internalNote = value),
                onSend: () => _sendReply(detail),
              ),
              _MessagesCard(messages: detail.messages),
              _StatusHistoryCard(items: detail.statusHistory),
              _AttachmentsCard(items: detail.attachments),
            ],
          );
        },
      ),
    );
  }
}

class _TicketSummaryCard extends StatelessWidget {
  const _TicketSummaryCard({required this.detail});

  final SupportTicketDetail detail;

  @override
  Widget build(BuildContext context) {
    final ticket = detail.ticket;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(color: BYS360Colors.info.withValues(alpha: .10), borderRadius: BorderRadius.circular(15)),
                  child: const Icon(Icons.support_agent_outlined, color: BYS360Colors.info),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(ticket.title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
                      const SizedBox(height: 7),
                      Wrap(
                        spacing: 6,
                        runSpacing: 6,
                        children: [
                          StatusPill(text: ticket.statusLabel, tone: _statusTone(ticket.status)),
                          StatusPill(text: ticket.priorityLabel, tone: _priorityTone(ticket.priority)),
                          StatusPill(text: ticket.moduleName, tone: BYS360Colors.info),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            _InfoGrid(rows: [
              ('Talep No', ticket.ticketNo),
              ('Talep Sahibi', ticket.requesterName),
              ('Sicil No', ticket.sicilNo),
              ('Birim', ticket.unitName),
              ('Atanan Kişi', ticket.assignedTo),
              ('Süre', ticket.elapsedLabel),
              ('Oluşturulma', ticket.createdAt),
              ('Son Güncelleme', ticket.updatedAt),
            ]),
          ],
        ),
      ),
    );
  }

  Color _statusTone(String status) {
    final value = status.toLowerCase().trim();
    if ({'resolved', 'closed', 'çözüldü', 'cozuldu', 'kapalı', 'kapali'}.contains(value)) return BYS360Colors.success;
    if ({'waiting_info', 'planned', 'beklemede'}.contains(value)) return BYS360Colors.warning;
    if ({'rejected', 'reddedildi'}.contains(value)) return BYS360Colors.corporateRed;
    return BYS360Colors.info;
  }

  Color _priorityTone(String priority) {
    final value = priority.toLowerCase().trim();
    if ({'critical', 'high', 'kritik', 'yüksek', 'yuksek'}.contains(value)) return BYS360Colors.corporateRed;
    if ({'low', 'düşük', 'dusuk'}.contains(value)) return BYS360Colors.success;
    return BYS360Colors.info;
  }
}

class _TicketDescriptionCard extends StatelessWidget {
  const _TicketDescriptionCard({required this.ticket});

  final SupportTicketInfo ticket;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Talep Açıklaması', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            Text(ticket.description.isEmpty ? 'Açıklama girilmemiş.' : ticket.description, style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.35)),
            if (ticket.subStatusText != '-' || ticket.resolutionText != '-') ...[
              const SizedBox(height: 12),
              _InfoGrid(rows: [('Alt Durum', ticket.subStatusText), ('Çözüm Özeti', ticket.resolutionText)]),
            ],
          ],
        ),
      ),
    );
  }
}

class _ReplyCard extends StatelessWidget {
  const _ReplyCard({
    required this.detail,
    required this.controller,
    required this.saving,
    required this.internalNote,
    required this.onInternalChanged,
    required this.onSend,
  });

  final SupportTicketDetail detail;
  final TextEditingController controller;
  final bool saving;
  final bool internalNote;
  final ValueChanged<bool> onInternalChanged;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) {
    final disabled = !detail.canReply || detail.ticket.isClosed;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Cevap Yaz', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            if (disabled)
              const BYSInfoPanel(
                icon: Icons.lock_outline,
                title: 'Cevap alanı kapalı',
                body: 'Bu talep kapanmış olabilir veya cevap yazma yetkiniz bulunmayabilir.',
                tint: BYS360Colors.warning,
              )
            else ...[
              TextField(
                controller: controller,
                minLines: 3,
                maxLines: 6,
                textInputAction: TextInputAction.newline,
                decoration: const InputDecoration(labelText: 'Mesajınız', hintText: 'Talebinizle ilgili cevabınızı yazın', alignLabelWithHint: true),
              ),
              if (detail.canManage) ...[
                const SizedBox(height: 6),
                SwitchListTile.adaptive(
                  value: internalNote,
                  contentPadding: EdgeInsets.zero,
                  onChanged: onInternalChanged,
                  title: const Text('İç not olarak kaydet', style: TextStyle(fontWeight: FontWeight.w800)),
                  subtitle: const Text('Sadece yetkili destek kullanıcıları görür.'),
                ),
              ],
              const SizedBox(height: 10),
              ElevatedButton.icon(
                onPressed: saving ? null : onSend,
                icon: saving ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.send_outlined),
                label: Text(saving ? 'Kaydediliyor' : 'Cevabı Gönder'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _MessagesCard extends StatelessWidget {
  const _MessagesCard({required this.messages});

  final List<SupportTicketMessageItem> messages;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Yorumlar ve İşlem Notları', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 10),
            if (messages.isEmpty)
              const Text('Henüz not eklenmemiş.', style: TextStyle(color: BYS360Colors.mutedText))
            else
              ...messages.map((item) => _TimelineTile(
                    icon: item.isInternal ? Icons.lock_outline : Icons.chat_bubble_outline,
                    title: item.isInternal ? '${item.author} · İç not' : item.author,
                    date: item.createdAt,
                    body: item.message,
                    tone: item.isInternal ? BYS360Colors.warning : BYS360Colors.info,
                  )),
          ],
        ),
      ),
    );
  }
}

class _StatusHistoryCard extends StatelessWidget {
  const _StatusHistoryCard({required this.items});

  final List<SupportStatusHistoryItem> items;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Süreç Geçmişi', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 10),
            if (items.isEmpty)
              const Text('Süreç geçmişi bulunmuyor.', style: TextStyle(color: BYS360Colors.mutedText))
            else
              ...items.map((item) => _TimelineTile(
                    icon: Icons.history_outlined,
                    title: '${item.oldStatus} → ${item.newStatus}',
                    date: item.createdAt,
                    body: item.note.isEmpty ? item.changedBy : '${item.changedBy}\n${item.note}',
                    tone: BYS360Colors.info,
                  )),
          ],
        ),
      ),
    );
  }
}

class _AttachmentsCard extends StatelessWidget {
  const _AttachmentsCard({required this.items});

  final List<SupportAttachmentItem> items;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Ek Dosyalar', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 10),
            if (items.isEmpty)
              const Text('Bu talebe eklenmiş dosya bulunmuyor.', style: TextStyle(color: BYS360Colors.mutedText))
            else
              ...items.map((item) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.attach_file_outlined, color: BYS360Colors.info),
                    title: Text(item.filename, style: const TextStyle(fontWeight: FontWeight.w800)),
                    subtitle: Text('${item.sizeLabel} · ${item.mimeType}'),
                  )),
          ],
        ),
      ),
    );
  }
}

class _TimelineTile extends StatelessWidget {
  const _TimelineTile({required this.icon, required this.title, required this.date, required this.body, required this.tone});

  final IconData icon;
  final String title;
  final String date;
  final String body;
  final Color tone;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(width: 34, height: 34, decoration: BoxDecoration(color: tone.withValues(alpha: .10), borderRadius: BorderRadius.circular(12)), child: Icon(icon, color: tone, size: 18)),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),
                const SizedBox(height: 2),
                Text(date, style: const TextStyle(color: BYS360Colors.mutedText, fontSize: 12)),
                if (body.trim().isNotEmpty) ...[
                  const SizedBox(height: 5),
                  Text(body, style: const TextStyle(height: 1.32)),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _InfoGrid extends StatelessWidget {
  const _InfoGrid({required this.rows});

  final List<(String, String)> rows;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: rows.where((row) => row.$2.trim().isNotEmpty).map((row) {
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 5),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(width: 116, child: Text(row.$1, style: const TextStyle(color: BYS360Colors.mutedText, fontWeight: FontWeight.w800))),
              const SizedBox(width: 8),
              Expanded(child: Text(row.$2, style: const TextStyle(fontWeight: FontWeight.w800))),
            ],
          ),
        );
      }).toList(),
    );
  }
}

// BYS360_MOBILE_V2_8_65_SUPPORT_COMPLETION
