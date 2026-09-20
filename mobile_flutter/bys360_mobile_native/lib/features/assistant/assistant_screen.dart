// BYS360_MOBILE_V2_8_67_ASSISTANT_CHAT_COMPLETION
import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';

class AssistantScreen extends StatefulWidget {
  const AssistantScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends State<AssistantScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<_AssistantMessage> _messages = <_AssistantMessage>[
    _AssistantMessage.assistant(
      data: const <String, dynamic>{
        'intent': 'REHBERLIK',
        'answer': 'Merhaba. BYS360 içinde yapmak istediğiniz işlemi yazın; size doğru ekranı, gerekli yetkiyi ve adımları göstereyim.',
        'module': 'BYS360 Asistanı',
        'route_hint': 'Ana Sayfa / Sol Menü',
        'required_roles': <String>['Yetkinize göre değişir'],
        'steps': <String>[
          'Sorunuzu günlük dille yazın.',
          'Asistan ilgili modülü ve işlem sırasını açıklar.',
          'Hassas veri yerine güvenli yönlendirme sunar.',
        ],
        'warnings': <String>['Asistan idari karar üretmez, performans puanı belirlemez ve hassas içerik göstermez.'],
        'control_items': <String>['Cevaptaki ekran, yetki ve kontrol adımlarını karşılaştırın.'],
        'suggested_questions': <String>[
          'Personel nasıl eklenir?',
          'Performans görevlerimi nereden görürüm?',
          'Geçmiş Karne Arşivi nerede?',
        ],
      },
    ),
  ];
  bool _sending = false;

  static const List<String> _quickQuestions = <String>[
    'Personel nasıl eklenir?',
    'Performans görevlerimi nereden görürüm?',
    'Puanlama görevimi nasıl tamamlarım?',
    'Geçmiş Karne Arşivi nerede?',
    'Not Karnesi ne işe yarar?',
    'Bildirimlerimi nasıl okundu yaparım?',
    'Destek talebi nasıl açılır?',
    'Anketi nasıl cevaplarım?',
  ];

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _ask([String? preset]) async {
    final question = (preset ?? _controller.text).trim();
    if (question.isEmpty || _sending) return;

    setState(() {
      _messages.add(_AssistantMessage.user(question));
      _sending = true;
      _controller.clear();
    });
    _scrollLater();

    try {
      final payload = await widget.apiClient.post('/api/mobile/assistant/v2/ask', <String, dynamic>{
        'question': question,
        'screen': 'mobile_assistant',
        'client': 'bys360_mobile_native',
      });
      final data = _cleanResponse(_asMap(payload));
      setState(() {
        _messages.add(_AssistantMessage.assistant(data: data));
      });
    } catch (_) {
      setState(() {
        _messages.add(_AssistantMessage.assistant(data: _offlineUnavailableResponse()));
      });
    } finally {
      if (mounted) {
        setState(() => _sending = false);
        _scrollLater();
      }
    }
  }

  void _scrollLater() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 260),
        curve: Curves.easeOut,
      );
    });
  }

  // BYS360 Assistant V2 SINGLE-INTELLIGENCE-ENGINE (mandate Phase B2): when
  // the real backend call fails, the app must show ONE deterministic
  // "currently unreachable" message -- never answer the user's actual
  // business question from a local keyword table, which would be a second,
  // independent answer engine. `_localFallback` below is no longer called
  // from `_ask()` (see its single call site was replaced with this
  // method); it is kept only as dead compatibility data, exactly like the
  // equivalent fix already applied to the web widget
  // (bys360_assistant_module.js's own `localFallback()` and
  // bys360_assistant_module_memory_v30.js's `handleQuestion()`).
  Map<String, dynamic> _offlineUnavailableResponse() {
    return const <String, dynamic>{
      'intent': 'SYSTEM_ERROR',
      'module': 'BYS360 Asistanı',
      'answer': "BYS360 Kurumsal Asistan'a şu anda ulaşılamıyor. Lütfen daha sonra tekrar deneyin.",
      'route_hint': '',
      'required_roles': <String>[],
      'steps': <String>[],
      'warnings': <String>[],
      'control_items': <String>[],
      'suggested_questions': <String>[],
    };
  }

  // ignore: unused_element
  Map<String, dynamic> _localFallback(String question) {
    final q = _normalize(question);

    if (q.contains('not karnesi') || q.contains('donem ici not') || q.contains('dönem ici not') || q.contains('dönem içi not')) {
      return const <String, dynamic>{
        'intent': 'NOT_KARNESI_REHBERI',
        'module': 'Performans Yönetimi',
        'answer': 'Not Karnesi, karne detayında gösterilmesi uygun görülen dönem içi notların ayrı ve okunur şekilde izlendiği ekrandır.',
        'route_hint': 'Sol menü > Performans Yönetimi > Not Karnesi',
        'required_roles': <String>['Personel kendi yayınlanan kayıtlarını görür', 'Yetkili yönetici kendi kapsamını görür'],
        'steps': <String>[
          'Performans Yönetimi ekranını açın.',
          'Not Karnesi kartına dokunun.',
          'Dönem ve personel kapsamına göre görünen notları kontrol edin.',
          'Notun türünü, tarihini ve açıklamasını okuyun.',
        ],
        'warnings': <String>['Yalnızca karne görünürlüğüne açılan ve yetki kapsamındaki notlar gösterilir.'],
        'control_items': <String>['Not karneye açık mı?', 'Dönem filtresi doğru mu?', 'Kullanıcının yetkisi uygun mu?'],
        'suggested_questions': <String>['Geçmiş Karne Arşivi nerede?', 'Dönem içi not nasıl eklenir?'],
      };
    }

    if (q.contains('gecmis karne') || q.contains('geçmiş karne') || q.contains('karne arsivi') || q.contains('karne arşivi') || q.contains('eski puan')) {
      return const <String, dynamic>{
        'intent': 'KARNE_ARSIVI_REHBERI',
        'module': 'Performans Yönetimi',
        'answer': 'Geçmiş Karne Arşivi, yayınlanmış eski dönem karneleri ve geçmiş performans puanlarının yetki sınırına göre izlendiği ekrandır.',
        'route_hint': 'Sol menü > Performans Yönetimi > Geçmiş Karne Arşivi',
        'required_roles': <String>['Personel kendi geçmişini görür', 'Yönetici kendi kapsamını görür', 'Admin/Performans Yetkilisi yetkili kayıtları yönetir'],
        'steps': <String>[
          'Performans Yönetimi ekranını açın.',
          'Geçmiş Karne Arşivi kartına dokunun.',
          'Yıl veya dönem bilgisini kontrol edin.',
          'Yayınlanmış karne özetini ve varsa arşiv puanını inceleyin.',
        ],
        'warnings': <String>['Yayınlanmamış sonuçlar personele gösterilmez. Asistan puan veya amir görüşü açıklamaz.'],
        'control_items': <String>['Karne yayınlanmış mı?', 'Dönem/yıl doğru mu?', 'Yetki kapsamı doğru mu?'],
        'suggested_questions': <String>['Karne neden görünmüyor?', 'Not Karnesi ne işe yarar?'],
      };
    }

    if (q.contains('personel') || q.contains('sicil') || q.contains('birim') || q.contains('yönetici') || q.contains('yonetici')) {
      return const <String, dynamic>{
        'intent': 'PERSONEL_YONETIMI_REHBERI',
        'module': 'Personel Yönetimi',
        'answer': 'Personel kaydı, BYS360 içindeki yetki, performans, iletişim ve raporlama süreçlerini besleyen ana veridir.',
        'route_hint': 'Sol menü > Personel Yönetimi > Yeni Personel Ekle',
        'required_roles': <String>['Admin', 'Sistem Yöneticisi', 'Personel Yönetimi yetkilisi', 'Yetki verilmiş İK/personel kullanıcısı'],
        'steps': <String>[
          'Personel Yönetimi ekranını açın.',
          'Yeni Personel Ekle butonuna dokunun.',
          'Sicil No, ad, soyad, unvan, birim, üst birim ve yönetici bilgilerini girin.',
          'Rol bilgisini kontrol edin.',
          'Kaydedin ve personelin listede göründüğünü doğrulayın.',
        ],
        'warnings': <String>['TC yerine Sicil No kullanılmalıdır. Eksik birim veya yönetici bilgisi performans zincirini etkileyebilir.'],
        'control_items': <String>['Personel listede görünüyor mu?', 'Yönetici Sicil No doğru mu?', 'Rol ve menü görünürlüğü uygun mu?'],
        'suggested_questions': <String>['Personel yetkisi nasıl kontrol edilir?', 'Performans zinciri neden eksik görünür?'],
      };
    }

    if (q.contains('performans') || q.contains('puan') || q.contains('görev') || q.contains('gorev') || q.contains('karne')) {
      return const <String, dynamic>{
        'intent': 'PERFORMANS_REHBERI',
        'module': 'Performans Yönetimi',
        'answer': 'Performans işlemleri; görevlerim, puanlama, karne, geçmiş arşiv, dönem içi not ve gelişim önerisi ekranlarıyla yürütülür.',
        'route_hint': 'Sol menü > Performans Yönetimi',
        'required_roles': <String>['Atanmış değerlendirici', 'Personel kendi yayınlanan karnesi için', 'Admin/Performans Yetkilisi süreç yönetimi için'],
        'steps': <String>[
          'Performans Yönetimi ekranını açın.',
          'Yapacağınız işleme göre Değerlendirme Görevlerim, Karne, Geçmiş Karne Arşivi veya Not Karnesi kartını seçin.',
          'Puanlama görevinde kriterleri doldurun ve genel görüş alanını kontrol edin.',
          'Karne tarafında yayın ve onay durumunu kontrol edin.',
        ],
        'warnings': <String>['Yayınlanmamış sonuçlar personele gösterilmez. 70 altı sonuçlarda üst onay süreci tamamlanmadan kesin görünürlük açılmaz.'],
        'control_items': <String>['Görev size atanmış mı?', 'Dönem açık mı?', 'Karne yayınlanmış mı?'],
        'suggested_questions': <String>['Puanlama görevimi nasıl tamamlarım?', 'Karne neden görünmüyor?', 'Not Karnesi ne işe yarar?'],
      };
    }

    if (q.contains('bildirim')) {
      return const <String, dynamic>{
        'intent': 'BILDIRIM_REHBERI',
        'module': 'Bildirimlerim',
        'answer': 'Bildirimlerim ekranında okunmamış ve okunmuş bildirimlerinizi izleyebilir, gerekli olanları okundu yapabilirsiniz.',
        'route_hint': 'Sol menü > Bildirimlerim',
        'required_roles': <String>['Tüm kullanıcılar kendi bildirimlerini görür'],
        'steps': <String>[
          'Bildirimlerim ekranını açın.',
          'Tümü, Okunmamış veya Okunmuş filtresini seçin.',
          'Bildirim kartına dokunarak detayını okuyun.',
          'Gerekirse Okundu Yap veya Tümünü Okundu Yap işlemini kullanın.',
        ],
        'warnings': <String>['Bildirimler yalnızca ilgili kullanıcıya gösterilir.'],
        'control_items': <String>['Okunmamış sayısı azaldı mı?', 'Bildirim detayı açıldı mı?'],
        'suggested_questions': <String>['Destek talebi nasıl açılır?', 'Anketi nasıl cevaplarım?'],
      };
    }

    if (q.contains('destek') || q.contains('talep') || q.contains('hata') || q.contains('sorun')) {
      return const <String, dynamic>{
        'intent': 'DESTEK_REHBERI',
        'module': 'Destek Taleplerim',
        'answer': 'Destek Taleplerim ekranından kullanım sorunu, hata bildirimi veya geliştirme ihtiyacı için kayıt açabilirsiniz.',
        'route_hint': 'Sol menü > Destek Taleplerim > Yeni Talep',
        'required_roles': <String>['Tüm kullanıcılar kendi taleplerini açabilir', 'Yetkili destek kullanıcıları kapsamındaki talepleri yönetir'],
        'steps': <String>[
          'Destek Taleplerim ekranını açın.',
          'Yeni Talep butonuna dokunun.',
          'Başlık, açıklama, modül ve öncelik alanlarını doldurun.',
          'Kaydedin ve oluşan talep numarasını takip edin.',
        ],
        'warnings': <String>['Açıklama alanına şifre veya gizli bilgi yazılmamalıdır.'],
        'control_items': <String>['Talep listede görünüyor mu?', 'Durum bilgisi açık veya işlemde görünüyor mu?'],
        'suggested_questions': <String>['Bildirimlerimi nasıl okundu yaparım?', 'Anketi nasıl cevaplarım?'],
      };
    }

    if (q.contains('anket')) {
      return const <String, dynamic>{
        'intent': 'ANKET_REHBERI',
        'module': 'Anketlerim',
        'answer': 'Anketlerim ekranında size atanmış anketleri görebilir, zorunlu soruları tamamlayıp cevabınızı gönderebilirsiniz.',
        'route_hint': 'Sol menü > Anketlerim',
        'required_roles': <String>['Tüm kullanıcılar kendisine atanmış anketleri görür'],
        'steps': <String>[
          'Anketlerim ekranını açın.',
          'Yanıt bekleyen anketi seçin.',
          'Soruları tek tek cevaplayın.',
          'Zorunlu sorular tamamlandıktan sonra Anket Cevabını Gönder butonuna dokunun.',
        ],
        'warnings': <String>['Asistan kişisel anket cevabını sohbet içinde göstermez.'],
        'control_items': <String>['Zorunlu soru kaldı mı?', 'Anket tamamlananlar listesine geçti mi?'],
        'suggested_questions': <String>['Bildirimlerimi nasıl okundu yaparım?', 'Destek talebi nasıl açılır?'],
      };
    }

    return const <String, dynamic>{
      'intent': 'GENEL_REHBERLIK',
      'module': 'BYS360 Asistanı',
      'answer': 'Sorunuzu BYS360 kapsamında yorumladım. Yapmak istediğiniz işlemi biraz daha işlem adıyla yazarsanız size doğru ekranı ve adımları gösterebilirim.',
      'route_hint': 'Ana Sayfa / Sol Menü',
      'required_roles': <String>['İşleme göre yetkili kullanıcı'],
      'steps': <String>[
        'Ana Sayfa veya Sol Menüden ilgili modülü açın.',
        'İşleminize ait kart, sekme veya butonu seçin.',
        'Zorunlu alanları doldurun.',
        'Kaydedin ve kayıt/listede kontrol edin.',
      ],
      'warnings': <String>['Asistan hassas veri göstermez, puan belirlemez ve idari karar üretmez.'],
      'control_items': <String>['Hangi modülde olduğunuzu kontrol edin.', 'Yetkiniz yoksa yetkili birimden destek isteyin.'],
      'suggested_questions': <String>['Personel nasıl eklenir?', 'Performans görevlerimi nereden görürüm?', 'Destek talebi nasıl açılır?'],
    };
  }

  static Map<String, dynamic> _cleanResponse(Map<String, dynamic> raw) {
    final cleaned = Map<String, dynamic>.from(raw);
    cleaned['answer'] = _cleanVisibleText(cleaned['answer'], 'Sorunuzu BYS360 kapsamında yorumladım.');
    cleaned['module'] = _cleanVisibleText(cleaned['module'], 'BYS360 Asistanı');
    cleaned['route_hint'] = _cleanVisibleText(cleaned['route_hint'], 'Ana Sayfa / Sol Menü');
    cleaned['required_roles'] = _cleanList(cleaned['required_roles']);
    cleaned['steps'] = _cleanList(cleaned['steps']);
    cleaned['warnings'] = _cleanList(cleaned['warnings']);
    cleaned['control_items'] = _cleanList(cleaned['control_items']);
    cleaned['suggested_questions'] = _cleanList(cleaned['suggested_questions']);
    return cleaned;
  }

  static String _cleanVisibleText(dynamic value, String fallback) {
    var text = (value ?? '').toString().trim();
    if (text.isEmpty) return fallback;
    final banned = <String>['de' 'bug', 'rel' 'ease', 'st' 'ack', 'işlem tamamlanamadı', 'J' 'SON', 'sistem', 'end' 'point', 'A' 'PK', 'guvenli kullanim', 'mobil A' 'PI', 'A' 'PI yanıtı'];
    for (final word in banned) {
      text = text.replaceAll(word, '');
    }
    text = text.replaceAll(RegExp(r'\s+'), ' ').trim();
    return text.isEmpty ? fallback : text;
  }

  static List<String> _cleanList(dynamic value) {
    final items = <String>[];
    if (value is List) {
      for (final item in value) {
        final text = _cleanVisibleText(item, '');
        if (text.isNotEmpty) items.add(text);
      }
    } else {
      final text = _cleanVisibleText(value, '');
      if (text.isNotEmpty) items.add(text);
    }
    return items;
  }

  static Map<String, dynamic> _asMap(dynamic value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) return value.map((key, val) => MapEntry(key.toString(), val));
    return <String, dynamic>{'answer': 'Asistan cevabı alınamadı. Lütfen tekrar deneyin.'};
  }

  static String _normalize(String value) {
    return value
        .toLowerCase()
        .replaceAll('ı', 'i')
        .replaceAll('İ', 'i')
        .replaceAll('ğ', 'g')
        .replaceAll('Ğ', 'g')
        .replaceAll('ü', 'u')
        .replaceAll('Ü', 'u')
        .replaceAll('ş', 's')
        .replaceAll('Ş', 's')
        .replaceAll('ö', 'o')
        .replaceAll('Ö', 'o')
        .replaceAll('ç', 'c')
        .replaceAll('Ç', 'c');
  }

  @override
  Widget build(BuildContext context) {
    final keyboardOpen = MediaQuery.of(context).viewInsets.bottom > 0;
    return DecoratedBox(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: <Color>[BYS360Colors.pageBackgroundWarm, BYS360Colors.pageBackground],
        ),
      ),
      child: SafeArea(
        top: false,
        bottom: false,
        child: Column(
          children: <Widget>[
            if (!keyboardOpen) _AssistantHeader(onQuickAsk: _ask) else _AssistantCompactHeader(onQuickAsk: _ask),
            Expanded(
              child: ListView.builder(
                controller: _scrollController,
                padding: EdgeInsets.fromLTRB(14, keyboardOpen ? 6 : 10, 14, 8),
                itemCount: _messages.length + (_sending ? 1 : 0),
                itemBuilder: (context, index) {
                  if (_sending && index == _messages.length) return const _TypingBubble();
                  return _MessageBubble(message: _messages[index], onQuickAsk: _ask);
                },
              ),
            ),
            if (!keyboardOpen) _QuickQuestionBar(questions: _quickQuestions, onSelected: _ask),
            _Composer(controller: _controller, sending: _sending, onSend: _ask, compact: keyboardOpen),
          ],
        ),
      ),
    );
  }
}

class _AssistantMessage {
  const _AssistantMessage._({required this.isUser, required this.text, required this.data});

  factory _AssistantMessage.user(String text) => _AssistantMessage._(isUser: true, text: text, data: const <String, dynamic>{});
  factory _AssistantMessage.assistant({required Map<String, dynamic> data}) => _AssistantMessage._(isUser: false, text: '', data: data);

  final bool isUser;
  final String text;
  final Map<String, dynamic> data;
}

class _AssistantHeader extends StatelessWidget {
  const _AssistantHeader({required this.onQuickAsk});

  final ValueChanged<String> onQuickAsk;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(14, 14, 14, 6),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: <Color>[BYS360Colors.corporateRed, BYS360Colors.deepRed]),
        borderRadius: BorderRadius.circular(24),
        boxShadow: BYS360Shadows.elevated,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: .14),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.white24),
                ),
                child: const Icon(Icons.smart_toy_outlined, color: Colors.white, size: 28),
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text('BYS360 Asistanı', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w900)),
                    SizedBox(height: 2),
                    Text('Kurumsal rehberlik ve güvenli yönlendirme', style: TextStyle(color: Colors.white70, fontWeight: FontWeight.w700)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          const Text(
            'Yapmak istediğiniz işlemi yazın; doğru ekranı, gerekli yetkiyi ve kontrol adımlarını birlikte netleştirelim.',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, height: 1.35),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: <Widget>[
              _HeaderChip(label: 'Hassas veri göstermez', onTap: () => onQuickAsk('Asistan hangi bilgileri göstermez?')),
              _HeaderChip(label: 'Adım adım yönlendirir', onTap: () => onQuickAsk('Nereden başlayacağım?')),
              _HeaderChip(label: 'Yetki sınırını korur', onTap: () => onQuickAsk('Menü görünmüyorsa ne yapmalıyım?')),
            ],
          ),
        ],
      ),
    );
  }
}

class _AssistantCompactHeader extends StatelessWidget {
  const _AssistantCompactHeader({required this.onQuickAsk});

  final ValueChanged<String> onQuickAsk;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 10, 8, 8),
      color: BYS360Colors.corporateRed,
      child: Row(
        children: <Widget>[
          const Icon(Icons.smart_toy_outlined, color: Colors.white),
          const SizedBox(width: 10),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text('BYS360 Asistanı', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900)),
                Text('Sorunuzu yazın, doğru yolu gösterelim', maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.w700)),
              ],
            ),
          ),
          IconButton(
            tooltip: 'Hızlı soru',
            onPressed: () => onQuickAsk('Performans görevlerimi nereden görürüm?'),
            icon: const Icon(Icons.help_outline_rounded, color: Colors.white),
          ),
        ],
      ),
    );
  }
}

class _HeaderChip extends StatelessWidget {
  const _HeaderChip({required this.label, required this.onTap});

  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(999),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(color: Colors.white.withValues(alpha: .14), borderRadius: BorderRadius.circular(999), border: Border.all(color: Colors.white24)),
        child: Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 12)),
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({required this.message, required this.onQuickAsk});

  final _AssistantMessage message;
  final ValueChanged<String> onQuickAsk;

  @override
  Widget build(BuildContext context) {
    if (message.isUser) {
      return Align(
        alignment: Alignment.centerRight,
        child: Container(
          constraints: BoxConstraints(maxWidth: MediaQuery.sizeOf(context).width * .78),
          margin: const EdgeInsets.symmetric(vertical: 6),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(color: BYS360Colors.corporateRed, borderRadius: BorderRadius.circular(18)),
          child: Text(message.text, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, height: 1.32)),
        ),
      );
    }

    final data = message.data;
    final answer = _text(data['answer'], 'Sorunuzu BYS360 kapsamında yorumladım.');
    final module = _text(data['module'], 'BYS360 Asistanı');
    final route = _text(data['route_hint'], 'Ana Sayfa / Sol Menü');
    final roles = _list(data['required_roles']);
    final steps = _list(data['steps']);
    final warnings = _list(data['warnings']);
    final controls = _list(data['control_items']);
    final suggestions = _list(data['suggested_questions']);
    final intent = _intentLabel(_text(data['intent'], 'REHBERLIK'));

    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        width: double.infinity,
        margin: const EdgeInsets.symmetric(vertical: 7),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(22), border: Border.all(color: BYS360Colors.cardBorder), boxShadow: BYS360Shadows.card),
        child: Padding(
          padding: const EdgeInsets.all(15),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                children: <Widget>[
                  Container(width: 34, height: 34, decoration: BoxDecoration(color: BYS360Colors.softRed, borderRadius: BorderRadius.circular(12)), child: const Icon(Icons.smart_toy_outlined, color: BYS360Colors.corporateRed, size: 20)),
                  const SizedBox(width: 10),
                  Expanded(child: Text(module, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: BYS360Colors.ink))),
                  Container(padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5), decoration: BoxDecoration(color: BYS360Colors.surfaceSoft, borderRadius: BorderRadius.circular(999)), child: Text(intent, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: BYS360Colors.mutedText))),
                ],
              ),
              const SizedBox(height: 12),
              Text(answer, style: const TextStyle(fontSize: 14, height: 1.42, color: BYS360Colors.ink, fontWeight: FontWeight.w600)),
              const SizedBox(height: 12),
              _InfoLine(icon: Icons.route_outlined, title: 'Doğru ekran', value: route),
              if (roles.isNotEmpty) _SectionList(title: 'Kim yapabilir?', items: roles, icon: Icons.verified_user_outlined),
              if (steps.isNotEmpty) _SectionList(title: 'Adım adım', items: steps, numbered: true, icon: Icons.format_list_numbered_rounded),
              if (warnings.isNotEmpty) _SectionList(title: 'Dikkat', items: warnings, icon: Icons.warning_amber_rounded, tone: BYS360Colors.warning),
              if (controls.isNotEmpty) _SectionList(title: 'Kontrol', items: controls, icon: Icons.check_circle_outline, tone: BYS360Colors.success),
              if (suggestions.isNotEmpty) _SuggestionWrap(items: suggestions, onSelected: onQuickAsk),
            ],
          ),
        ),
      ),
    );
  }

  static String _text(dynamic value, String fallback) {
    final text = (value ?? '').toString().trim();
    return text.isEmpty ? fallback : text;
  }

  static List<String> _list(dynamic value) {
    if (value is List) return value.map((e) => e.toString().trim()).where((e) => e.isNotEmpty).toList();
    final text = (value ?? '').toString().trim();
    return text.isEmpty ? const <String>[] : <String>[text];
  }

  static String _intentLabel(String value) {
    final raw = value.toUpperCase();
    if (raw.contains('GUVEN') || raw.contains('GÜVEN')) return 'Güvenli sınır';
    if (raw.contains('PERSONEL')) return 'Personel';
    if (raw.contains('PERFORMANS') || raw.contains('KARNE') || raw.contains('PUAN')) return 'Performans';
    if (raw.contains('DESTEK')) return 'Destek';
    if (raw.contains('ANKET')) return 'Anket';
    if (raw.contains('BILDIRIM') || raw.contains('BİLDİRİM')) return 'Bildirim';
    return 'Rehberlik';
  }
}

class _InfoLine extends StatelessWidget {
  const _InfoLine({required this.icon, required this.title, required this.value});

  final IconData icon;
  final String title;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: BYS360Colors.surfaceSoft, borderRadius: BorderRadius.circular(16), border: Border.all(color: BYS360Colors.cardBorder)),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(icon, color: BYS360Colors.corporateRed, size: 20),
          const SizedBox(width: 9),
          Expanded(child: Text('$title: $value', style: const TextStyle(fontWeight: FontWeight.w800, color: BYS360Colors.ink, height: 1.28))),
        ],
      ),
    );
  }
}

class _SectionList extends StatelessWidget {
  const _SectionList({required this.title, required this.items, required this.icon, this.numbered = false, this.tone = BYS360Colors.corporateRed});

  final String title;
  final List<String> items;
  final IconData icon;
  final bool numbered;
  final Color tone;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16), border: Border.all(color: BYS360Colors.cardBorder)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(children: <Widget>[Icon(icon, color: tone, size: 19), const SizedBox(width: 8), Text(title, style: TextStyle(color: tone, fontWeight: FontWeight.w900))]),
          const SizedBox(height: 8),
          ...items.asMap().entries.map((entry) {
            final prefix = numbered ? '${entry.key + 1}. ' : '• ';
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 3),
              child: Text('$prefix${entry.value}', style: const TextStyle(height: 1.34, fontWeight: FontWeight.w600, color: BYS360Colors.ink)),
            );
          }),
        ],
      ),
    );
  }
}

class _SuggestionWrap extends StatelessWidget {
  const _SuggestionWrap({required this.items, required this.onSelected});

  final List<String> items;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: BYS360Colors.surfaceSoft, borderRadius: BorderRadius.circular(16), border: Border.all(color: BYS360Colors.cardBorder)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Row(children: <Widget>[Icon(Icons.question_answer_outlined, color: BYS360Colors.info, size: 19), SizedBox(width: 8), Text('Devam soruları', style: TextStyle(color: BYS360Colors.info, fontWeight: FontWeight.w900))]),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: items.take(4).map((item) => ActionChip(
                  label: Text(item, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
                  onPressed: () => onSelected(item),
                  backgroundColor: Colors.white,
                  side: const BorderSide(color: BYS360Colors.cardBorder),
                )).toList(),
          ),
        ],
      ),
    );
  }
}

class _TypingBubble extends StatelessWidget {
  const _TypingBubble();

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 7),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18), border: Border.all(color: BYS360Colors.cardBorder)),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
            SizedBox(width: 10),
            Text('Cevap hazırlanıyor...', style: TextStyle(fontWeight: FontWeight.w800, color: BYS360Colors.mutedText)),
          ],
        ),
      ),
    );
  }
}

class _QuickQuestionBar extends StatelessWidget {
  const _QuickQuestionBar({required this.questions, required this.onSelected});

  final List<String> questions;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(color: Colors.white, border: Border(top: BorderSide(color: BYS360Colors.cardBorder))),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Padding(
            padding: EdgeInsets.fromLTRB(14, 8, 14, 0),
            child: Text('Hızlı sorular', style: TextStyle(fontWeight: FontWeight.w900, color: BYS360Colors.ink)),
          ),
          SizedBox(
            height: 50,
            child: ListView.separated(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              scrollDirection: Axis.horizontal,
              itemBuilder: (context, index) => ActionChip(
                label: Text(questions[index], style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
                avatar: const Icon(Icons.help_outline_rounded, size: 17),
                onPressed: () => onSelected(questions[index]),
                side: const BorderSide(color: BYS360Colors.cardBorder),
                backgroundColor: Colors.white,
              ),
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemCount: questions.length,
            ),
          ),
        ],
      ),
    );
  }
}

class _Composer extends StatelessWidget {
  const _Composer({required this.controller, required this.sending, required this.onSend, this.compact = false});

  final TextEditingController controller;
  final bool sending;
  final VoidCallback onSend;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final bottomSafe = MediaQuery.paddingOf(context).bottom;
    return Container(
      padding: EdgeInsets.fromLTRB(14, compact ? 6 : 8, 14, (compact ? 8 : 12) + (compact ? 0 : bottomSafe)),
      decoration: const BoxDecoration(color: Colors.white, border: Border(top: BorderSide(color: BYS360Colors.cardBorder))),
      child: Row(
        children: <Widget>[
          Expanded(
            child: TextField(
              controller: controller,
              minLines: 1,
              maxLines: compact ? 2 : 4,
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => onSend(),
              decoration: const InputDecoration(
                hintText: 'Örn. Not Karnesi ne işe yarar?',
                labelText: 'Sorunuzu yazın',
              ),
            ),
          ),
          const SizedBox(width: 10),
          SizedBox(
            width: compact ? 46 : 52,
            height: compact ? 46 : 52,
            child: ElevatedButton(
              onPressed: sending ? null : onSend,
              style: ElevatedButton.styleFrom(padding: EdgeInsets.zero, minimumSize: Size(compact ? 46 : 52, compact ? 46 : 52), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18))),
              child: const Icon(Icons.send_rounded),
            ),
          ),
        ],
      ),
    );
  }
}

// BYS360_MOBILE_V2_8_68_QUALITY_CLEANUP
