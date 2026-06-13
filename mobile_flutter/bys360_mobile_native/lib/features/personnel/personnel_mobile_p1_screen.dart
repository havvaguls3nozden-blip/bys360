// BYS360_MOBILE_V2_8_62_PERSONNEL_ADD
// Android personel listesi ve yetki kontrollü personel ekleme ekranı.
// Kullanıcı ekranında geliştirici dili gösterilmez.

import 'package:flutter/material.dart';

import '../../core/api/mobile_api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/utils/bys360_copy.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';

class PersonnelMobileP1Screen extends StatefulWidget {
  const PersonnelMobileP1Screen({super.key, this.apiClient});

  final dynamic apiClient;

  @override
  State<PersonnelMobileP1Screen> createState() => _PersonnelMobileP1ScreenState();
}

class _PersonnelMobileP1ScreenState extends State<PersonnelMobileP1Screen> {
  static const int _limit = 10000;

  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<Map<String, dynamic>> _rows = <Map<String, dynamic>>[];
  final Set<String> _seenKeys = <String>{};

  int _page = 1;
  int _offset = 0;
  int? _totalCount;
  bool _loading = false;
  bool _loadingMore = false;
  bool _hasMore = false;
  bool _canCreatePersonnel = false;
  String? _error;
  String? _emptyMessage;
  String? _scopeLabel;

  dynamic get _client => widget.apiClient ?? const MobileApiClient();

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
    _load(reset: true);
  }

  @override
  void dispose() {
    _scrollController.removeListener(_onScroll);
    _scrollController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (!_hasMore || _loading || _loadingMore) return;
    if (!_scrollController.hasClients) return;
    final position = _scrollController.position;
    if (position.pixels >= position.maxScrollExtent - 360) {
      _load(reset: false);
    }
  }

  Future<void> _refresh() => _load(reset: true);

  Future<void> _load({required bool reset}) async {
    if (_loading || _loadingMore) return;

    if (reset) {
      setState(() {
        _loading = true;
        _loadingMore = false;
        _error = null;
        _emptyMessage = null;
        _rows.clear();
        _seenKeys.clear();
        _page = 1;
        _offset = 0;
        _totalCount = null;
        _hasMore = false;
        _canCreatePersonnel = false;
      });
    } else {
      setState(() {
        _loadingMore = true;
        _error = null;
      });
    }

    try {
      final query = _searchController.text.trim();
      final attempts = _buildPathAttempts(query);
      List<Map<String, dynamic>> parsed = <Map<String, dynamic>>[];
      Map<String, dynamic>? lastPayload;
      bool? payloadHasMore;

      for (final path in attempts) {
        final payload = await _getJson(path);
        lastPayload = payload;
        parsed = _parsePersonnelRows(payload);
        final total = _parseTotal(payload);
        if (parsed.isNotEmpty || total != null) {
          _totalCount = total ?? _totalCount;
          _scopeLabel = _value(payload, const ['scope', 'scope_label', 'visibility_scope']);
          _canCreatePersonnel = _parseCanCreatePersonnel(payload);
          payloadHasMore = _parseHasMore(payload);
          break;
        }
      }

      int added = 0;
      for (final row in parsed) {
        final key = _stablePersonKey(row);
        if (_seenKeys.add(key)) {
          _rows.add(row);
          added += 1;
        }
      }

      _page += 1;
      _offset = _rows.length;
      _hasMore = payloadHasMore ?? false;
      if (parsed.length >= _limit && added > 0 && (_totalCount == null || _rows.length < _totalCount!)) {
        _hasMore = true;
      }
      if (_totalCount != null && _rows.length >= _totalCount!) {
        _hasMore = false;
      }
      if (parsed.length < _limit) {
        _hasMore = false;
      }
      if (added == 0 && !reset) {
        _hasMore = false;
      }

      if (!mounted) return;
      setState(() {
        _loading = false;
        _loadingMore = false;
        _error = null;
        _emptyMessage = _rows.isEmpty ? _friendlyEmptyMessage(lastPayload) : null;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _loadingMore = false;
        _error = BYS360Copy.error(error);
        _emptyMessage = null;
      });
    }
  }

  List<String> _buildPathAttempts(String query) {
    final q = Uri.encodeQueryComponent(query);
    final search = query.isEmpty ? '' : '&q=$q&search=$q&query=$q';
    final offset = _offset;
    final page = _page;
    return <String>[
      '/api/mobile/personnel/all?limit=$_limit&offset=$offset&page=$page$search',
      '/api/mobile/personnel/list?limit=$_limit&offset=$offset&page=$page$search',
      '/api/mobile/personnel/list?length=$_limit&start=$offset$search',
      '/api/mobile/personnel?limit=$_limit&offset=$offset&page=$page$search',
      '/api/personnel/mobile?limit=$_limit&offset=$offset&page=$page$search',
      '/api/personnel?limit=$_limit&offset=$offset&page=$page$search',
      '/personnel/api/list?limit=$_limit&offset=$offset&page=$page$search',
    ];
  }

  Future<Map<String, dynamic>> _getJson(String path) async {
    final dynamic client = _client;
    try {
      final dynamic result = await client.getJson(path);
      return _asMap(result);
    } catch (_) {
      final dynamic result = await client.get(path);
      return _asMap(result);
    }
  }

  Future<Map<String, dynamic>> _postJson(String path, Map<String, dynamic> body) async {
    final dynamic client = _client;
    final dynamic result = await client.post(path, body);
    return _asMap(result);
  }

  Map<String, dynamic> _asMap(dynamic result) {
    if (result is Map<String, dynamic>) return result;
    if (result is Map) return Map<String, dynamic>.from(result);
    if (result != null) {
      try {
        final dynamic data = result.data;
        if (data is Map<String, dynamic>) return data;
        if (data is Map) return Map<String, dynamic>.from(data);
      } catch (_) {
        return <String, dynamic>{};
      }
    }
    return <String, dynamic>{};
  }

  List<Map<String, dynamic>> _parsePersonnelRows(dynamic payload) {
    final dynamic data = payload is Map ? payload['data'] : null;
    final candidates = <dynamic>[
      payload is Map ? payload['personnel'] : null,
      payload is Map ? payload['rows'] : null,
      payload is Map ? payload['items'] : null,
      payload is Map ? payload['results'] : null,
      payload is Map ? payload['persons'] : null,
      payload is Map ? payload['users'] : null,
      data is Map ? data['personnel'] : null,
      data is Map ? data['rows'] : null,
      data is Map ? data['items'] : null,
      data is Map ? data['results'] : null,
      data is Map ? data['persons'] : null,
      data is Map ? data['users'] : null,
      data is List ? data : null,
      payload is List ? payload : null,
    ];
    for (final candidate in candidates) {
      if (candidate is List) {
        return candidate.whereType<Map>().map((row) => Map<String, dynamic>.from(row)).toList(growable: false);
      }
    }
    return <Map<String, dynamic>>[];
  }

  int? _parseTotal(Map<String, dynamic>? payload) {
    if (payload == null) return null;
    final dynamic data = payload['data'];
    for (final source in <dynamic>[payload, if (data is Map) data]) {
      if (source is Map) {
        for (final key in const <String>['total', 'total_count', 'recordsTotal', 'count', 'filtered_count']) {
          final value = source[key];
          if (value is int) return value;
          if (value is num) return value.toInt();
          if (value is String) return int.tryParse(value);
        }
      }
    }
    return null;
  }

  bool? _parseHasMore(Map<String, dynamic>? payload) {
    if (payload == null) return null;
    final dynamic data = payload['data'];
    for (final source in <dynamic>[payload, if (data is Map) data]) {
      if (source is Map) {
        final value = source['has_more'] ?? source['hasMore'];
        if (value is bool) return value;
        if (value is String) return value.toLowerCase() == 'true';
      }
    }
    return null;
  }

  bool _parseCanCreatePersonnel(Map<String, dynamic>? payload) {
    if (payload == null) return false;
    final dynamic data = payload['data'];
    for (final source in <dynamic>[payload, if (data is Map) data]) {
      if (source is Map) {
        final value = source['can_create_personnel'] ?? source['canCreatePersonnel'] ?? source['can_create'];
        if (value is bool) return value;
        if (value is String) return value.toLowerCase() == 'true';
      }
    }
    return false;
  }

  String _friendlyEmptyMessage(Map<String, dynamic>? payload) {
    if (payload == null || payload.isEmpty) {
      return 'Yetkiniz kapsamında görüntülenecek personel kaydı bulunamadı veya sayfa bilgisi alınamadı.';
    }
    return 'Personel kayıtları şu anda görüntülenemedi. Lütfen yenileyin veya yetki kapsamınızı kontrol edin.';
  }

  String _value(Map<String, dynamic> row, List<String> keys) {
    for (final key in keys) {
      final value = row[key];
      if (value == null) continue;
      final text = value.toString().trim();
      if (text.isNotEmpty && text.toLowerCase() != 'null') return BYS360Copy.clean(text);
    }
    return '';
  }

  String _displayName(Map<String, dynamic> row) {
    final full = _value(row, const ['full_name', 'fullName', 'name_surname', 'ad_soyad', 'display_name', 'name', 'title']);
    if (full.isNotEmpty) return full;
    final first = _value(row, const ['first_name', 'firstName', 'ad']);
    final last = _value(row, const ['last_name', 'lastName', 'soyad', 'surname']);
    final combined = ('$first $last').trim();
    return combined.isEmpty ? 'İsimsiz personel' : combined;
  }

  String _registry(Map<String, dynamic> row) => _value(row, const ['registry_no', 'sicil_no', 'sicilNo', 'sicil', 'employee_no', 'personnel_no']);
  String _unit(Map<String, dynamic> row) => _value(row, const ['unit_name', 'organization_unit', 'organization_unit_name', 'org_unit_name', 'birim', 'unit', 'department']);
  String _upperUnit(Map<String, dynamic> row) => _value(row, const ['upper_unit_name', 'parent_unit_name', 'ust_birim', 'upper_unit']);
  String _title(Map<String, dynamic> row) => _value(row, const ['title_name', 'unvan', 'title', 'position_title', 'job_title']);
  String _duty(Map<String, dynamic> row) => _value(row, const ['duty_name', 'gorev', 'duty', 'role_name', 'position']);
  String _manager(Map<String, dynamic> row) => _value(row, const ['manager_name', 'yonetici', 'supervisor_name', 'first_manager_name', 'amir', 'amir_adi']);
  String _category(Map<String, dynamic> row) => _value(row, const ['personnel_category', 'category', 'kategori']);
  String _status(Map<String, dynamic> row) => _value(row, const ['status_label', 'status', 'aktiflik', 'is_active', 'active']);

  String _stablePersonKey(Map<String, dynamic> row) {
    final key = _value(row, const ['id', 'user_id', 'personnel_id', 'employee_id', 'registry_no', 'sicil_no', 'sicil']);
    if (key.isNotEmpty) return key;
    return '${_displayName(row)}-${_unit(row)}-${_title(row)}'.toLowerCase();
  }

  List<Map<String, dynamic>> get _visibleRows {
    final q = _searchController.text.trim().toLowerCase();
    if (q.isEmpty) return _rows;
    return _rows.where((row) {
      final text = '${_displayName(row)} ${_registry(row)} ${_unit(row)} ${_upperUnit(row)} ${_title(row)} ${_duty(row)} ${_manager(row)} ${_category(row)}'.toLowerCase();
      return text.contains(q);
    }).toList(growable: false);
  }

  Future<Map<String, dynamic>> _createPersonnel(Map<String, dynamic> payload) {
    return _postJson('/api/mobile/personnel/create', payload);
  }

  Future<void> _openAddPersonnelSheet() async {
    final created = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(26))),
      builder: (context) => _PersonnelAddSheet(onSubmit: _createPersonnel),
    );
    if (created == true) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Personel kaydı oluşturuldu')));
      await _refresh();
    }
  }

  @override
  Widget build(BuildContext context) {
    final rows = _visibleRows;
    final loadedText = _totalCount == null ? '${_rows.length}' : '${_rows.length} / $_totalCount';

    if (_loading && _rows.isEmpty) {
      return const BYSLoadingState(message: 'Personel kayıtları yükleniyor');
    }

    return BYSPage(
      title: 'Personel Yönetimi',
      subtitle: 'Yetkiniz kapsamındaki personel, birim, unvan ve yönetici bilgileri.',
      badge: _scopeLabel?.isNotEmpty == true ? _scopeLabel : 'Personel',
      onRefresh: _refresh,
      children: <Widget>[
        const BYSSectionTitle(title: 'Personel özeti', subtitle: 'Web uygulamasıyla aynı yetki sınırında mobil görünüm'),
        MetricCard(
          title: 'Yüklenen kayıt',
          value: loadedText,
          subtitle: _hasMore ? 'Liste kaydırıldıkça devamı alınır' : 'Yetki kapsamındaki kayıtlar',
          icon: Icons.people_alt_outlined,
          tone: BYS360Colors.corporateRed,
        ),
        if (_canCreatePersonnel) _addPersonnelCard(),
        _searchBox(),
        if (_error != null) ...[
          ApiEmptyState(message: _error!, onRetry: () => _load(reset: true)),
        ] else if (rows.isEmpty) ...[
          ApiEmptyState(title: 'Personel kaydı bulunamadı', message: _emptyMessage ?? 'Arama veya yetki kapsamınızda personel kaydı bulunamadı.', onRetry: () => _load(reset: true)),
        ] else ...[
          const BYSSectionTitle(title: 'Personel listesi', subtitle: 'Detay için kayda dokunun'),
          ...rows.map(_personCard),
        ],
        if (_hasMore)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: OutlinedButton.icon(
              onPressed: _loadingMore ? null : () => _load(reset: false),
              icon: _loadingMore
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.expand_more),
              label: Text(_loadingMore ? 'Yükleniyor' : 'Kalan personeli yükle'),
            ),
          ),
        if (!_loading && !_hasMore && _rows.isNotEmpty)
          const BYSInfoPanel(
            icon: Icons.check_circle_outline,
            title: 'Liste tamamlandı',
            body: 'Yetki kapsamınızda görüntülenebilen personel kayıtları yüklendi.',
            tint: BYS360Colors.success,
          ),
      ],
    );
  }

  Widget _addPersonnelCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(color: BYS360Colors.softRed, borderRadius: BorderRadius.circular(15)),
              child: const Icon(Icons.person_add_alt_1_outlined, color: BYS360Colors.corporateRed),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text('Personel Ekle', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
                  const SizedBox(height: 4),
                  const Text('Yeni personel kaydı oluşturmak için zorunlu kimlik, birim ve yönetici bilgilerini girin.', style: TextStyle(color: BYS360Colors.mutedText, height: 1.35)),
                  const SizedBox(height: 12),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: ElevatedButton.icon(
                      onPressed: _openAddPersonnelSheet,
                      icon: const Icon(Icons.add),
                      label: const Text('Yeni Personel Ekle'),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _searchBox() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: TextField(
          controller: _searchController,
          decoration: InputDecoration(
            labelText: 'Personel ara',
            hintText: 'Ad soyad, sicil no, birim veya unvan',
            prefixIcon: const Icon(Icons.search),
            suffixIcon: IconButton(
              tooltip: 'Ara',
              onPressed: _refresh,
              icon: const Icon(Icons.send),
            ),
          ),
          onChanged: (_) => setState(() {}),
          onSubmitted: (_) => _refresh(),
        ),
      ),
    );
  }

  Widget _personCard(Map<String, dynamic> row) {
    final name = _displayName(row);
    final registry = _registry(row);
    final unit = _unit(row);
    final title = _title(row);
    final duty = _duty(row);
    final category = _category(row);
    final initial = name.trim().isEmpty ? '?' : name.trim().substring(0, 1).toUpperCase();
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        borderRadius: BorderRadius.circular(BYS360Radii.lg),
        onTap: () => _showDetail(row),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              CircleAvatar(backgroundColor: BYS360Colors.softRed, foregroundColor: BYS360Colors.corporateRed, child: Text(initial)),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(name, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 15)),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: <Widget>[
                        if (registry.isNotEmpty) _pill('Sicil: $registry'),
                        if (unit.isNotEmpty) _pill(unit),
                        if (title.isNotEmpty) _pill(title),
                        if (duty.isNotEmpty) _pill(duty),
                        if (category.isNotEmpty) _pill(category),
                      ],
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: BYS360Colors.mutedText),
            ],
          ),
        ),
      ),
    );
  }

  Widget _pill(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(color: BYS360Colors.softRed, borderRadius: BorderRadius.circular(999)),
      child: Text(BYS360Copy.clean(text), style: const TextStyle(color: BYS360Colors.corporateRed, fontSize: 11, fontWeight: FontWeight.w800)),
    );
  }

  void _showDetail(Map<String, dynamic> row) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(26))),
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(_displayName(row), style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
                  const SizedBox(height: 14),
                  _detailRow('Sicil No', _registry(row)),
                  _detailRow('Birim', _unit(row)),
                  _detailRow('Üst Birim', _upperUnit(row)),
                  _detailRow('Unvan', _title(row)),
                  _detailRow('Görev', _duty(row)),
                  _detailRow('Kategori', _category(row)),
                  _detailRow('Yönetici', _manager(row)),
                  _detailRow('Durum', _status(row)),
                  const SizedBox(height: 16),
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton(onPressed: () => Navigator.pop(context), child: const Text('Kapat')),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _detailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          SizedBox(width: 96, child: Text(label, style: const TextStyle(fontWeight: FontWeight.w900))),
          Expanded(child: Text(value.isEmpty ? 'Belirtilmemiş' : BYS360Copy.clean(value))),
        ],
      ),
    );
  }
}

class _PersonnelAddSheet extends StatefulWidget {
  const _PersonnelAddSheet({required this.onSubmit});

  final Future<Map<String, dynamic>> Function(Map<String, dynamic> payload) onSubmit;

  @override
  State<_PersonnelAddSheet> createState() => _PersonnelAddSheetState();
}

class _PersonnelAddSheetState extends State<_PersonnelAddSheet> {
  final _formKey = GlobalKey<FormState>();
  final _sicilController = TextEditingController();
  final _adController = TextEditingController();
  final _soyadController = TextEditingController();
  final _emailController = TextEditingController();
  final _unvanController = TextEditingController();
  final _birimController = TextEditingController();
  final _ustBirimController = TextEditingController();
  final _yoneticiController = TextEditingController();
  final _gorevController = TextEditingController();

  String _role = 'personel';
  String _category = 'Diğer';
  bool _isActive = true;
  bool _submitting = false;
  String? _error;

  static const List<MapEntry<String, String>> _roleOptions = <MapEntry<String, String>>[
    MapEntry<String, String>('personel', 'Personel'),
    MapEntry<String, String>('personel_yonetimi', 'Personel Yönetimi Yetkilisi'),
    MapEntry<String, String>('ik', 'İK Yetkilisi'),
    MapEntry<String, String>('performans_yetkilisi', 'Performans Yetkilisi'),
    MapEntry<String, String>('koordinator', 'Koordinatör'),
    MapEntry<String, String>('grup_baskani', 'Grup Başkanı'),
    MapEntry<String, String>('admin', 'Admin'),
  ];

  static const List<String> _categoryOptions = <String>[
    'Güvenlik',
    'Temizlik',
    'İdari Personel',
    'Teknik Personel',
    'Deneme Süreli Personel',
    'Diğer',
  ];

  @override
  void dispose() {
    _sicilController.dispose();
    _adController.dispose();
    _soyadController.dispose();
    _emailController.dispose();
    _unvanController.dispose();
    _birimController.dispose();
    _ustBirimController.dispose();
    _yoneticiController.dispose();
    _gorevController.dispose();
    super.dispose();
  }

  String? _required(String? value) {
    if ((value ?? '').trim().isEmpty) return 'Bu alan zorunludur';
    return null;
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final payload = <String, dynamic>{
        'sicil_no': _sicilController.text.trim(),
        'ad': _adController.text.trim(),
        'soyad': _soyadController.text.trim(),
        'email': _emailController.text.trim(),
        'unvan': _unvanController.text.trim(),
        'birim': _birimController.text.trim(),
        'ust_birim': _ustBirimController.text.trim(),
        'yonetici_sicil': _yoneticiController.text.trim(),
        'gorev': _gorevController.text.trim(),
        'role': _role,
        'personnel_category': _category,
        'is_active': _isActive,
      };
      await widget.onSubmit(payload);
      if (!mounted) return;
      Navigator.pop(context, true);
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _submitting = false;
        _error = BYS360Copy.error(error);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;
    return Padding(
      padding: EdgeInsets.only(bottom: bottomInset),
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 18, 20, 22),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(color: BYS360Colors.softRed, borderRadius: BorderRadius.circular(16)),
                    child: const Icon(Icons.person_add_alt_1_outlined, color: BYS360Colors.corporateRed),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text('Yeni Personel Ekle', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
                        const SizedBox(height: 4),
                        const Text('Zorunlu alanları doldurarak personel kaydını oluşturun.', style: TextStyle(color: BYS360Colors.mutedText, height: 1.35)),
                      ],
                    ),
                  ),
                  IconButton(onPressed: _submitting ? null : () => Navigator.pop(context, false), icon: const Icon(Icons.close)),
                ],
              ),
              const SizedBox(height: 16),
              const BYSInfoPanel(
                icon: Icons.lock_reset_outlined,
                title: 'Başlangıç bilgisi',
                body: 'Başlangıç şifresi sistem tarafından otomatik atanır. Kullanıcı ilk girişte güvenli şekilde değiştirme adımlarına yönlendirilir.',
              ),
              const SizedBox(height: 12),
              _field(_sicilController, 'Sicil No', Icons.badge_outlined, validator: _required, keyboardType: TextInputType.number),
              _field(_adController, 'Ad', Icons.person_outline, validator: _required),
              _field(_soyadController, 'Soyad', Icons.person_outline, validator: _required),
              _field(_emailController, 'E-posta', Icons.mail_outline, keyboardType: TextInputType.emailAddress, helperText: 'Boş bırakılırsa sistem sicil numarasına göre kurumsal kayıt oluşturur'),
              _field(_unvanController, 'Unvan', Icons.workspace_premium_outlined, validator: _required),
              _field(_birimController, 'Birim', Icons.account_tree_outlined, validator: _required),
              _field(_ustBirimController, 'Üst Birim', Icons.apartment_outlined, validator: _required),
              _field(_yoneticiController, 'Yönetici Sicil No', Icons.supervisor_account_outlined, validator: _required, keyboardType: TextInputType.number),
              _field(_gorevController, 'Görev', Icons.assignment_ind_outlined),
              DropdownButtonFormField<String>(
                initialValue: _role,
                decoration: const InputDecoration(labelText: 'Rol / Yetki Grubu', prefixIcon: Icon(Icons.verified_user_outlined)),
                items: _roleOptions.map((entry) => DropdownMenuItem<String>(value: entry.key, child: Text(entry.value))).toList(),
                onChanged: _submitting ? null : (value) => setState(() => _role = value ?? 'personel'),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _category,
                decoration: const InputDecoration(labelText: 'Personel Kategorisi', prefixIcon: Icon(Icons.category_outlined)),
                items: _categoryOptions.map((value) => DropdownMenuItem<String>(value: value, child: Text(value))).toList(),
                onChanged: _submitting ? null : (value) => setState(() => _category = value ?? 'Diğer'),
              ),
              const SizedBox(height: 8),
              SwitchListTile.adaptive(
                contentPadding: EdgeInsets.zero,
                value: _isActive,
                onChanged: _submitting ? null : (value) => setState(() => _isActive = value),
                title: const Text('Aktif personel kaydı'),
                subtitle: const Text('Pasif kayıtlar süreçlere dahil edilmez.'),
              ),
              if (_error != null) ...<Widget>[
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: BYS360Colors.softRed, borderRadius: BorderRadius.circular(16)),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      const Icon(Icons.info_outline, color: BYS360Colors.corporateRed),
                      const SizedBox(width: 8),
                      Expanded(child: Text(_error!, style: const TextStyle(color: BYS360Colors.corporateRed, fontWeight: FontWeight.w800))),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 14),
              Row(
                children: <Widget>[
                  Expanded(child: OutlinedButton(onPressed: _submitting ? null : () => Navigator.pop(context, false), child: const Text('Vazgeç'))),
                  const SizedBox(width: 10),
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: _submitting ? null : _submit,
                      icon: _submitting ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.save_outlined),
                      label: Text(_submitting ? 'Kaydediliyor' : 'Kaydet'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _field(
    TextEditingController controller,
    String label,
    IconData icon, {
    String? Function(String?)? validator,
    TextInputType? keyboardType,
    String? helperText,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: controller,
        validator: validator,
        keyboardType: keyboardType,
        textInputAction: TextInputAction.next,
        enabled: !_submitting,
        decoration: InputDecoration(labelText: label, prefixIcon: Icon(icon), helperText: helperText),
      ),
    );
  }
}

// BYS360_MOBILE_V2_8_62_PERSONNEL_ADD_END
