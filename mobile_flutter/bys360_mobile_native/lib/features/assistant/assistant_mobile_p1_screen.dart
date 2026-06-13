
// BYS360_MOBILE_V2_8_28_ASSISTANT_P1_MARKER
import 'package:flutter/material.dart';

import '../../core/assistant/assistant_mobile_contract.dart';

class AssistantMobileP1Screen extends StatefulWidget {
  const AssistantMobileP1Screen({super.key});

  @override
  State<AssistantMobileP1Screen> createState() => _AssistantMobileP1ScreenState();
}

class _AssistantMobileP1ScreenState extends State<AssistantMobileP1Screen> {
  final TextEditingController _controller = TextEditingController();
  AssistantMobileIntent _intent = AssistantMobileContract.resolveIntent('');
  AssistantScreenContext _context = AssistantMobileContract.detectScreen('/dashboard', 'Ana Sayfa');

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _ask() {
    setState(() {
      _intent = AssistantMobileContract.resolveIntent(_controller.text);
    });
  }

  @override
  Widget build(BuildContext context) {
    _context = AssistantMobileContract.detectScreen(ModalRoute.of(context)?.settings.name ?? '/dashboard', 'BYS360 Mobil');
    return Scaffold(
      appBar: AppBar(
        title: const Text('BYS360 Asistanı'),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _HeaderCard(contextInfo: _context),
            const SizedBox(height: 12),
            _SafeSummaryCard(),
            const SizedBox(height: 12),
            TextField(
              controller: _controller,
              minLines: 1,
              maxLines: 3,
              decoration: InputDecoration(
                labelText: 'Ne yapmak istiyorsunuz?',
                hintText: 'Örn. performans dönemini açacağım',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.send_rounded),
                  onPressed: _ask,
                ),
              ),
              onSubmitted: (_) => _ask(),
            ),
            const SizedBox(height: 12),
            _IntentCard(intent: _intent),
          ],
        ),
      ),
    );
  }
}

class _HeaderCard extends StatelessWidget {
  const _HeaderCard({required this.contextInfo});

  final AssistantScreenContext contextInfo;

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Ekranı tanıdım', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Text('Bulunduğunuz alan: ${contextInfo.screenTitle}'),
            Text('Modül: ${contextInfo.moduleName}'),
            Text('Tanıma güveni: ${contextInfo.confidence}'),
          ],
        ),
      ),
    );
  }
}

class _SafeSummaryCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    const items = [
      AssistantSafeSummary(title: 'Bekleyen işler', value: 'Yetkiye göre', description: 'Kişisel ve rol kapsamındaki görev özeti'),
      AssistantSafeSummary(title: 'Bildirimler', value: 'Güvenli özet', description: 'Okunmamış bildirim sayısı ve yönlendirme'),
      AssistantSafeSummary(title: 'Performans', value: 'Kısıtlı görünüm', description: 'Puan veya hassas görüş gösterilmez'),
    ];
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Yetki kontrollü özet', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            ...items.map((item) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.verified_user_outlined, size: 18),
                  const SizedBox(width: 8),
                  Expanded(child: Text('${item.title}: ${item.value} — ${item.description}')),
                ],
              ),
            )),
          ],
        ),
      ),
    );
  }
}

class _IntentCard extends StatelessWidget {
  const _IntentCard({required this.intent});

  final AssistantMobileIntent intent;

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(intent.title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Text('Modül: ${intent.module}'),
            Text('Doğru menü: ${intent.routeHint}'),
            Text('Kim yapabilir: ${intent.requiredRoleText}'),
            const SizedBox(height: 12),
            const Text('Adım adım:', style: TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 6),
            ...intent.steps.asMap().entries.map((entry) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 3),
              child: Text('${entry.key + 1}. ${entry.value}'),
            )),
            const SizedBox(height: 12),
            Text('Dikkat: ${intent.safeNote}'),
          ],
        ),
      ),
    );
  }
}

// BYS360_MOBILE_V2_8_28_ASSISTANT_P1_SCREEN_DETECT_FIX_MARKER
