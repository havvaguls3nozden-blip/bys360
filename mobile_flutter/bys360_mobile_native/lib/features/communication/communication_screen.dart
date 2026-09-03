// BYS360_MOBILE_V2_8_48_COMMUNICATION_MESSAGES_V2_NATIVE
// Mobil iletişim ve mesajlaşma ekranı: konuşma listesi, mesaj detayı, mesaj gönderme ve yeni konuşma başlatma.

import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/utils/bys360_copy.dart';

class CommunicationScreen extends StatefulWidget {
  const CommunicationScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<CommunicationScreen> createState() => _CommunicationScreenState();
}

class _CommunicationScreenState extends State<CommunicationScreen> {
  static const String _threadsPath = '/api/mobile/communication/v2/threads';
  static const Color _red = BYS360Colors.corporateRed;
  static const Color _bg = BYS360Colors.pageBackground;

  final TextEditingController _searchController = TextEditingController();
  List<Map<String, dynamic>> _threads = <Map<String, dynamic>>[];
  bool _loading = true;
  String? _error;
  String _sourceLabel = 'Canlı BYS360 mesajlaşma verisi';

  @override
  void initState() {
    super.initState();
    _loadThreads();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadThreads() async {
    if (!mounted) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final payload = await widget.apiClient.get(_threadsPath);
      final data = _asMap(payload);
      final rows = _parseList(data, const <String>['threads', 'items', 'rows', 'results']);
      if (!mounted) return;
      setState(() {
        _threads = rows;
        _sourceLabel = _text(data['source_label'] ?? data['source'] ?? 'Canlı BYS360 mesajlaşma verisi');
        _loading = false;
      });
    } catch (error) {
      try {
        final fallbackPayload = await widget.apiClient.get('/api/mobile/communication/threads');
        final data = _asMap(fallbackPayload);
        final rows = _parseList(data, const <String>['threads', 'items', 'rows', 'results']);
        if (!mounted) return;
        setState(() {
          _threads = rows;
          _sourceLabel = 'BYS360 iletişim listesi';
          _loading = false;
          _error = null;
        });
      } catch (_) {
        if (!mounted) return;
        setState(() {
          _loading = false;
          _error = _friendlyError(error);
        });
      }
    }
  }

  List<Map<String, dynamic>> get _visibleThreads {
    final q = _searchController.text.trim().toLowerCase();
    if (q.isEmpty) return _threads;
    return _threads.where((row) {
      final haystack = '${_title(row)} ${_subtitle(row)} ${_lastBody(row)} ${_text(row['participants_label'])}'.toLowerCase();
      return haystack.contains(q);
    }).toList(growable: false);
  }

  @override
  Widget build(BuildContext context) {
    final rows = _visibleThreads;
    return Scaffold(
      backgroundColor: _bg,
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: _red,
        foregroundColor: Colors.white,
        onPressed: _openNewThreadSheet,
        icon: const Icon(Icons.edit_outlined),
        label: const Text('Yeni Mesaj'),
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadThreads,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
            children: <Widget>[
              _heroCard(),
              const SizedBox(height: 12),
              _searchBox(),
              const SizedBox(height: 12),
              if (_loading)
                const Padding(
                  padding: EdgeInsets.all(32),
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (_error != null)
                _stateCard('Mesajlaşma yüklenemedi', _error!, Icons.error_outline, actionText: 'Tekrar Dene', onAction: _loadThreads)
              else if (rows.isEmpty)
                _stateCard('Konuşma bulunamadı', 'Yetkiniz kapsamında görüntülenecek konuşma bulunamadı. Yeni mesaj butonuyla konuşma başlatabilirsiniz.', Icons.forum_outlined)
              else ...<Widget>[
                _sectionTitle('Konuşmalar', '${rows.length} konuşma görüntüleniyor'),
                ...rows.map(_threadCard),
              ],
              const SizedBox(height: 6),
              Text(_sourceLabel, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: Colors.black45)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _heroCard() {
    final unread = _threads.fold<int>(0, (sum, row) => sum + _int(row['unread_count']));
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: <Color>[BYS360Colors.corporateRed, BYS360Colors.deepRed]),
        borderRadius: BorderRadius.circular(24),
        boxShadow: const <BoxShadow>[BoxShadow(color: Color(0x22000000), blurRadius: 18, offset: Offset(0, 10))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Container(
                width: 54,
                height: 54,
                decoration: BoxDecoration(color: Colors.white.withValues(alpha: .14), borderRadius: BorderRadius.circular(18)),
                child: const Icon(Icons.forum_outlined, color: Colors.white, size: 30),
              ),
              const SizedBox(width: 14),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text('İletişim ve Mesajlaşma', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w900)),
                    SizedBox(height: 4),
                    Text('Kurum içi konuşmaları görüntüleyin, yanıtlayın ve yeni mesaj başlatın. B48', style: TextStyle(color: Colors.white70, height: 1.25)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: <Widget>[
              _heroPill('${_threads.length} konuşma'),
              _heroPill('$unread okunmamış'),
              _heroPill('Mesaj gönderme aktif'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _heroPill(String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 6),
      decoration: BoxDecoration(color: Colors.white.withValues(alpha: .15), borderRadius: BorderRadius.circular(999)),
      child: Text(label, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w800)),
    );
  }

  Widget _searchBox() {
    return TextField(
      controller: _searchController,
      decoration: InputDecoration(
        labelText: 'Konuşma ara',
        hintText: 'Konu, kişi veya mesaj içeriği',
        prefixIcon: const Icon(Icons.search),
        suffixIcon: _searchController.text.isEmpty
            ? IconButton(onPressed: _loadThreads, icon: const Icon(Icons.refresh), tooltip: 'Yenile')
            : IconButton(
                onPressed: () {
                  _searchController.clear();
                  setState(() {});
                },
                icon: const Icon(Icons.close),
                tooltip: 'Temizle',
              ),
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(18)),
      ),
      onChanged: (_) => setState(() {}),
    );
  }

  Widget _sectionTitle(String title, String subtitle) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(2, 10, 2, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: BYS360Colors.ink)),
          const SizedBox(height: 3),
          Text(subtitle, style: const TextStyle(color: BYS360Colors.mutedText)),
        ],
      ),
    );
  }

  Widget _threadCard(Map<String, dynamic> row) {
    final unread = _int(row['unread_count']);
    final lastBody = _lastBody(row);
    final participants = _text(row['participants_label']);
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22), side: const BorderSide(color: BYS360Colors.cardBorder)),
      child: InkWell(
        borderRadius: BorderRadius.circular(22),
        onTap: () => _openThread(row),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Stack(
                clipBehavior: Clip.none,
                children: <Widget>[
                  Container(
                    width: 50,
                    height: 50,
                    decoration: BoxDecoration(color: _red.withValues(alpha: .08), borderRadius: BorderRadius.circular(18)),
                    child: const Icon(Icons.chat_bubble_outline, color: _red),
                  ),
                  if (unread > 0)
                    Positioned(
                      right: -4,
                      top: -4,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                        decoration: BoxDecoration(color: BYS360Colors.danger, borderRadius: BorderRadius.circular(999)),
                        child: Text('$unread', style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w900)),
                      ),
                    ),
                ],
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        Expanded(child: Text(_title(row), maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 15))),
                        if (_text(row['last_message_at_label']).isNotEmpty)
                          Text(_text(row['last_message_at_label']), style: const TextStyle(fontSize: 11, color: Colors.black45, fontWeight: FontWeight.w700)),
                      ],
                    ),
                    const SizedBox(height: 5),
                    Text(participants.isEmpty ? _subtitle(row) : participants, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: BYS360Colors.mutedText, fontWeight: FontWeight.w700)),
                    const SizedBox(height: 6),
                    Text(lastBody.isEmpty ? 'Henüz mesaj yok.' : lastBody, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(height: 1.25)),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: <Widget>[
                        _pill(_text(row['thread_type_label']).isEmpty ? 'Konuşma' : _text(row['thread_type_label'])),
                        if (unread > 0) _pill('Okunmamış'),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 6),
              const Icon(Icons.chevron_right, color: Colors.black38),
            ],
          ),
        ),
      ),
    );
  }

  Widget _pill(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(color: _red.withValues(alpha: .07), borderRadius: BorderRadius.circular(999)),
      child: Text(text, style: const TextStyle(color: _red, fontSize: 11, fontWeight: FontWeight.w800)),
    );
  }

  Widget _stateCard(String title, String message, IconData icon, {String? actionText, VoidCallback? onAction}) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22), side: const BorderSide(color: BYS360Colors.cardBorder)),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Icon(icon, color: _red, size: 30),
            const SizedBox(height: 10),
            Text(title, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
            const SizedBox(height: 6),
            Text(message, style: const TextStyle(height: 1.35)),
            if (actionText != null && onAction != null) ...<Widget>[
              const SizedBox(height: 12),
              FilledButton.icon(onPressed: onAction, icon: const Icon(Icons.refresh), label: Text(actionText)),
            ],
          ],
        ),
      ),
    );
  }

  void _openThread(Map<String, dynamic> row) async {
    final id = _text(row['id'] ?? row['thread_id']);
    if (id.isEmpty) return;
    await Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => _ThreadDetailPage(apiClient: widget.apiClient, threadId: id, title: _title(row)),
    ));
    _loadThreads();
  }

  Future<void> _openNewThreadSheet() async {
    final created = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(28))),
      builder: (context) => _NewThreadSheet(apiClient: widget.apiClient),
    );
    if (created == true) _loadThreads();
  }
}

class _ThreadDetailPage extends StatefulWidget {
  const _ThreadDetailPage({required this.apiClient, required this.threadId, required this.title});

  final ApiClient apiClient;
  final String threadId;
  final String title;

  @override
  State<_ThreadDetailPage> createState() => _ThreadDetailPageState();
}

class _ThreadDetailPageState extends State<_ThreadDetailPage> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  Map<String, dynamic> _thread = <String, dynamic>{};
  List<Map<String, dynamic>> _messages = <Map<String, dynamic>>[];
  List<Map<String, dynamic>> _participants = <Map<String, dynamic>>[];
  bool _loading = true;
  bool _sending = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadDetail();
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _loadDetail() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final payload = await widget.apiClient.get('/api/mobile/communication/v2/threads/${widget.threadId}');
      final data = _asMap(payload);
      if (!mounted) return;
      setState(() {
        _thread = _asMap(data['thread']);
        _messages = _parseList(data, const <String>['messages', 'items', 'rows']);
        _participants = _parseList(data, const <String>['participants', 'users']);
        _loading = false;
      });
      _scrollToBottom();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = _friendlyError(error);
      });
    }
  }

  Future<void> _send() async {
    final body = _messageController.text.trim();
    if (body.isEmpty || _sending) return;
    setState(() => _sending = true);
    try {
      final payload = await widget.apiClient.post('/api/mobile/communication/v2/threads/${widget.threadId}/send', <String, dynamic>{'body': body});
      final data = _asMap(payload);
      final detail = _asMap(data['detail']);
      if (!mounted) return;
      _messageController.clear();
      setState(() {
        _sending = false;
        _thread = _asMap(detail['thread']).isNotEmpty ? _asMap(detail['thread']) : _thread;
        _messages = _parseList(detail.isNotEmpty ? detail : data, const <String>['messages', 'items', 'rows']);
        if (_messages.isEmpty) _loadDetail();
      });
      _scrollToBottom();
    } catch (error) {
      if (!mounted) return;
      setState(() => _sending = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(error))));
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(_scrollController.position.maxScrollExtent, duration: const Duration(milliseconds: 260), curve: Curves.easeOut);
    });
  }

  @override
  Widget build(BuildContext context) {
    final title = _text(_thread['subject']).isNotEmpty ? _text(_thread['subject']) : widget.title;
    return Scaffold(
      backgroundColor: BYS360Colors.pageBackground,
      appBar: AppBar(
        title: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),
        actions: <Widget>[IconButton(onPressed: _loadDetail, icon: const Icon(Icons.refresh), tooltip: 'Yenile')],
      ),
      body: SafeArea(
        child: Column(
          children: <Widget>[
            _participantsBar(),
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : _error != null
                      ? Center(child: Padding(padding: const EdgeInsets.all(18), child: Text(_error!, textAlign: TextAlign.center)))
                      : RefreshIndicator(
                          onRefresh: _loadDetail,
                          child: ListView.builder(
                            controller: _scrollController,
                            padding: const EdgeInsets.fromLTRB(14, 14, 14, 20),
                            itemCount: _messages.isEmpty ? 1 : _messages.length,
                            itemBuilder: (context, index) {
                              if (_messages.isEmpty) return _emptyMessages();
                              return _messageBubble(_messages[index]);
                            },
                          ),
                        ),
            ),
            _composer(),
          ],
        ),
      ),
    );
  }

  Widget _participantsBar() {
    final label = _participants.map((p) => _text(p['display_name'] ?? p['name'])).where((e) => e.isNotEmpty).take(4).join(', ');
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      color: Colors.white,
      child: Row(
        children: <Widget>[
          const Icon(Icons.groups_outlined, color: BYS360Colors.corporateRed, size: 20),
          const SizedBox(width: 8),
          Expanded(child: Text(label.isEmpty ? 'Katılımcı bilgisi' : label, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800))),
        ],
      ),
    );
  }

  Widget _emptyMessages() {
    return Container(
      margin: const EdgeInsets.only(top: 80),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(22), border: Border.all(color: BYS360Colors.cardBorder)),
      child: const Column(
        children: <Widget>[
          Icon(Icons.chat_bubble_outline, color: BYS360Colors.corporateRed, size: 34),
          SizedBox(height: 10),
          Text('Henüz mesaj yok', style: TextStyle(fontWeight: FontWeight.w900)),
          SizedBox(height: 5),
          Text('İlk mesajı yazarak konuşmayı başlatabilirsiniz.', textAlign: TextAlign.center),
        ],
      ),
    );
  }

  Widget _messageBubble(Map<String, dynamic> row) {
    final mine = _bool(row['is_mine'] ?? row['mine']);
    final sender = _text(row['sender_name']);
    final time = _text(row['sent_at_label']);
    final body = _text(row['body']);
    return Align(
      alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * .78),
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.fromLTRB(13, 10, 13, 8),
        decoration: BoxDecoration(
          color: mine ? BYS360Colors.corporateRed : Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(18),
            topRight: const Radius.circular(18),
            bottomLeft: Radius.circular(mine ? 18 : 4),
            bottomRight: Radius.circular(mine ? 4 : 18),
          ),
          border: mine ? null : Border.all(color: BYS360Colors.cardBorder),
          boxShadow: const <BoxShadow>[BoxShadow(color: Color(0x0F000000), blurRadius: 10, offset: Offset(0, 4))],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            if (!mine && sender.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(sender, style: const TextStyle(color: BYS360Colors.corporateRed, fontWeight: FontWeight.w900, fontSize: 12)),
              ),
            Text(body.isEmpty ? 'Mesaj içeriği bulunamadı.' : body, style: TextStyle(color: mine ? Colors.white : BYS360Colors.ink, height: 1.32)),
            const SizedBox(height: 5),
            Align(
              alignment: Alignment.centerRight,
              child: Text(time, style: TextStyle(color: mine ? Colors.white70 : Colors.black45, fontSize: 10, fontWeight: FontWeight.w700)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _composer() {
    return Container(
      padding: EdgeInsets.fromLTRB(12, 10, 12, 10 + MediaQuery.of(context).viewInsets.bottom),
      decoration: const BoxDecoration(color: Colors.white, boxShadow: <BoxShadow>[BoxShadow(color: Color(0x14000000), blurRadius: 16, offset: Offset(0, -4))]),
      child: Row(
        children: <Widget>[
          Expanded(
            child: TextField(
              controller: _messageController,
              minLines: 1,
              maxLines: 5,
              decoration: InputDecoration(
                hintText: 'Mesajınızı yazın',
                filled: true,
                fillColor: BYS360Colors.pageBackground,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(20), borderSide: BorderSide.none),
              ),
            ),
          ),
          const SizedBox(width: 8),
          FilledButton(
            onPressed: _sending ? null : _send,
            style: FilledButton.styleFrom(backgroundColor: BYS360Colors.corporateRed, foregroundColor: Colors.white, shape: const CircleBorder(), padding: const EdgeInsets.all(14)),
            child: _sending ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.send),
          ),
        ],
      ),
    );
  }
}

class _NewThreadSheet extends StatefulWidget {
  const _NewThreadSheet({required this.apiClient});

  final ApiClient apiClient;

  @override
  State<_NewThreadSheet> createState() => _NewThreadSheetState();
}

class _NewThreadSheetState extends State<_NewThreadSheet> {
  final TextEditingController _searchController = TextEditingController();
  final TextEditingController _subjectController = TextEditingController();
  final TextEditingController _bodyController = TextEditingController();
  List<Map<String, dynamic>> _users = <Map<String, dynamic>>[];
  Map<String, dynamic>? _selectedUser;
  bool _searching = false;
  bool _creating = false;
  String? _error;

  // B48: Yeni mesaj ekranı açılır açılmaz alıcı/personel listesini yükler.
  // Sadece arama ikonuna basmaya bağlı kalmaz; birincil bağlantı başarısız olursa yedek personel kaynağına düşer.
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _searchUsers());
  }

  Future<dynamic> _loadRecipientsPayload(String query) async {
    final encoded = Uri.encodeQueryComponent(query);
    try {
      return await widget.apiClient.get('/api/mobile/communication/v2/users?limit=10000&q=$encoded');
    } catch (_) {
      return await widget.apiClient.get('/api/mobile/personnel/all?limit=10000&q=$encoded');
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    _subjectController.dispose();
    _bodyController.dispose();
    super.dispose();
  }

  Future<void> _searchUsers() async {
    final q = _searchController.text.trim();
    setState(() {
      _searching = true;
      _error = null;
    });
    try {
      final payload = await _loadRecipientsPayload(q);
      final data = _asMap(payload);
      if (!mounted) return;
      setState(() {
        _users = _parseList(data, const <String>['users', 'items', 'rows', 'personnel', 'results']);
        _searching = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _searching = false;
        _error = _friendlyError(error);
      });
    }
  }

  Future<void> _create() async {
    if (_selectedUser == null || _creating) return;
    final recipientId = _text(_selectedUser!['id'] ?? _selectedUser!['user_id']);
    if (recipientId.isEmpty) return;
    final body = _bodyController.text.trim();
    if (body.isEmpty) {
      setState(() => _error = 'Konuşma başlatmak için ilk mesajı yazmanız gerekir.');
      return;
    }
    setState(() {
      _creating = true;
      _error = null;
    });
    try {
      await widget.apiClient.post('/api/mobile/communication/v2/create-thread', <String, dynamic>{
        'participant_user_ids': <String>[recipientId],
        'subject': _subjectController.text.trim(),
        'body': body,
      });
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _creating = false;
        _error = _friendlyError(error);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(18, 18, 18, 18 + MediaQuery.of(context).viewInsets.bottom),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                const Expanded(child: Text('Yeni Mesaj', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900))),
                IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.close)),
              ],
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _searchController,
              decoration: InputDecoration(
                labelText: 'Alıcı ara',
                hintText: 'Ad, soyad veya sicil no',
                prefixIcon: const Icon(Icons.person_search_outlined),
                suffixIcon: IconButton(onPressed: _searchUsers, icon: const Icon(Icons.search)),
              ),
              onSubmitted: (_) => _searchUsers(),
            ),
            const SizedBox(height: 10),
            if (_searching) const LinearProgressIndicator(),
            if (_users.isNotEmpty)
              SizedBox(
                height: 180,
                child: ListView.builder(
                  itemCount: _users.length,
                  itemBuilder: (context, index) {
                    final user = _users[index];
                    final selected = _text(user['id'] ?? user['user_id']) == _text(_selectedUser?['id'] ?? _selectedUser?['user_id']);
                    return ListTile(
                      selected: selected,
                      leading: CircleAvatar(backgroundColor: BYS360Colors.softRed, child: Text(_initial(_text(user['display_name'] ?? user['name'])))),
                      title: Text(_text(user['display_name'] ?? user['name']), style: const TextStyle(fontWeight: FontWeight.w800)),
                      subtitle: Text(_text(user['subtitle'] ?? user['unit_name'] ?? user['registry_no'])),
                      onTap: () => setState(() => _selectedUser = user),
                    );
                  },
                ),
              ),
            if (!_searching && _users.isEmpty)
              Container(
                width: double.infinity,
                margin: const EdgeInsets.only(top: 8),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: BYS360Colors.softRed, borderRadius: BorderRadius.circular(16)),
                child: const Text('Alıcı listesi otomatik yüklenir. Görünmüyorsa Yenile/Ara ikonuna basın veya ad-soyad yazarak arayın.', style: TextStyle(fontWeight: FontWeight.w700)),
              ),
            if (_selectedUser != null)
              Container(
                width: double.infinity,
                margin: const EdgeInsets.only(top: 8),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: BYS360Colors.corporateRed.withValues(alpha: .08), borderRadius: BorderRadius.circular(16)),
                child: Text('Seçilen alıcı: ${_text(_selectedUser!['display_name'] ?? _selectedUser!['name'] ?? _selectedUser!['full_name'])}', style: const TextStyle(fontWeight: FontWeight.w900, color: BYS360Colors.corporateRed)),
              ),
            const SizedBox(height: 10),
            TextField(controller: _subjectController, decoration: const InputDecoration(labelText: 'Konu (isteğe bağlı)', prefixIcon: Icon(Icons.subject))),
            const SizedBox(height: 10),
            TextField(controller: _bodyController, minLines: 3, maxLines: 6, decoration: const InputDecoration(labelText: 'İlk mesaj', prefixIcon: Icon(Icons.message_outlined))),
            if (_error != null) ...<Widget>[
              const SizedBox(height: 10),
              Text(_error!, style: const TextStyle(color: BYS360Colors.danger, fontWeight: FontWeight.w800)),
            ],
            const SizedBox(height: 14),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _creating ? null : _create,
                icon: _creating ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.send_outlined),
                label: Text(_creating ? 'Gönderiliyor' : 'Konuşmayı Başlat'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

Map<String, dynamic> _asMap(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  if (value != null) {
    try {
      final dynamic data = value.data;
      if (data is Map<String, dynamic>) return data;
      if (data is Map) return Map<String, dynamic>.from(data);
    } catch (_) {
      return <String, dynamic>{};
    }
  }
  return <String, dynamic>{};
}

List<Map<String, dynamic>> _parseList(Map<String, dynamic> payload, List<String> keys) {
  final dynamic data = payload['data'];
  final candidates = <dynamic>[
    for (final key in keys) payload[key],
    if (data is Map) for (final key in keys) data[key],
    if (data is List) data,
  ];
  for (final candidate in candidates) {
    if (candidate is List) {
      return candidate.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList(growable: false);
    }
  }
  return <Map<String, dynamic>>[];
}

String _text(dynamic value) {
  if (value == null) return '';
  final text = value.toString().trim();
  if (text.toLowerCase() == 'null') return '';
  return text;
}

int _int(dynamic value) {
  if (value is int) return value;
  if (value is num) return value.toInt();
  return int.tryParse(_text(value)) ?? 0;
}

bool _bool(dynamic value) {
  if (value is bool) return value;
  final text = _text(value).toLowerCase();
  return text == 'true' || text == '1' || text == 'evet' || text == 'yes';
}

String _title(Map<String, dynamic> row) {
  final candidates = <dynamic>[row['subject'], row['title'], row['thread_title'], row['name']];
  for (final value in candidates) {
    final text = _text(value);
    if (text.isNotEmpty) return text;
  }
  return 'Kurum içi konuşma';
}

String _subtitle(Map<String, dynamic> row) => _text(row['subtitle'] ?? row['meta'] ?? row['thread_type_label']);
String _lastBody(Map<String, dynamic> row) => _text(row['last_message_body'] ?? row['body'] ?? row['preview']);
String _initial(String text) => text.trim().isEmpty ? '?' : text.trim().substring(0, 1).toUpperCase();

String _friendlyError(Object error) => BYS360Copy.error(error);

// BYS360_MOBILE_V2_8_68_QUALITY_CLEANUP
