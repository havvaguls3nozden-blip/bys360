import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/module_api_screen.dart';
import '../../core/widgets/mobile_feature_scope.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  Widget build(BuildContext context) {
    return ModuleApiScreen(
      apiClient: apiClient,
      path: '/api/mobile/settings/summary',
      title: 'Ayarlar ve Yetkilendirme',
      subtitle: 'Rol, menü görünürlüğü, modül ayarları, güvenlik ve audit izleri.',
      badge: 'Ayarlar',
      icon: Icons.tune_outlined,

      features: const [
        MobileFeatureScope(title: 'Rol ve menü görünürlüğü', description: 'Rol matrisi, kişi bazlı menü ve birim profil özetleri mobilde kontrollü gösterilecek.', icon: Icons.admin_panel_settings_outlined),
        MobileFeatureScope(title: 'Modül ayarları', description: 'Performans, iletişim, AI, bildirim ve güvenlik ayarları yetkili rollere özetlenecek.', icon: Icons.tune_outlined),
        MobileFeatureScope(title: 'Audit ve güvenlik', description: 'Kritik ayar değişiklikleri, CAPTCHA/oturum güvenliği ve audit izleri mobil sıraya alındı.', status: 'Sıradaki iş paketi', phase: 'V2.8.18', icon: Icons.security_outlined),
      ],
      tone: BYS360Colors.corporateRed,
    );
  }
}
