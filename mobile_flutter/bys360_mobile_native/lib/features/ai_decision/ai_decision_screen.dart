import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/module_api_screen.dart';
import '../../core/widgets/mobile_feature_scope.dart';

class AiDecisionScreen extends StatelessWidget {
  const AiDecisionScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  Widget build(BuildContext context) {
    return ModuleApiScreen(
      apiClient: apiClient,
      path: '/api/mobile/ai/insights',
      title: 'AI Karar Destek',
      subtitle: 'Kontrollü özet, dikkat notu ve karar destek kayıtları.',
      badge: 'AI Karar Destek',
      icon: Icons.psychology_alt_outlined,

      features: const [
        MobileFeatureScope(title: 'Kontrollü özetler', description: 'AI karar vermez; yalnızca yetki kontrollü dikkat notu, özet ve analiz başlığı sunar.', icon: Icons.psychology_alt_outlined),
        MobileFeatureScope(title: 'Risk farkındalığı', description: 'Düşük performans, yoğun destek talebi, düşük katılım ve KPI riski mobil özetlere bağlanacak.', icon: Icons.warning_amber_outlined),
        MobileFeatureScope(title: 'AI log ve sınır bilgisi', description: 'AI istekleri, kullanım sınırı ve hassas veri maskeleme uyarıları mobilde görünür olacak.', status: 'Sıradaki iş paketi', phase: 'V2.8.18', icon: Icons.shield_outlined),
      ],
      tone: BYS360Colors.purple,
    );
  }
}
