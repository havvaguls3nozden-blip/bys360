import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';
import '../ai_decision/ai_decision_screen.dart';
import '../assistant/assistant_screen.dart';
import '../communication/communication_screen.dart';
import '../kpi/kpi_screen.dart';
import '../notifications/notifications_screen.dart';
import '../performance/performance_screen.dart';
import '../personnel/personnel_screen.dart';
import '../portal/portal_web_screen.dart';
import '../profile/profile_screen.dart';
import '../reports/reports_screen.dart';
import '../settings/settings_screen.dart';
import '../support/support_screen.dart';
import '../surveys/surveys_screen.dart';

class ModulesScreen extends StatelessWidget {
  const ModulesScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  void _open(BuildContext context, _ModuleLink module) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => _ModuleRouteScaffold(title: module.title, child: module.screen),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final modules = [
      _ModuleLink('Personel', 'Sicil ve organizasyon', Icons.people_outline, BYS360Colors.corporateRed, PersonnelScreen(apiClient: apiClient)),
      _ModuleLink('Performans', 'Dönem, karne ve onay', Icons.assessment_outlined, BYS360Colors.corporateRed, PerformanceScreen(apiClient: apiClient)),
      const _ModuleLink('Kurumsal Portal', 'Duyurular, paylaşımlar ve kurum içi akış', Icons.public_outlined, BYS360Colors.corporateRed, PortalWebScreen()),
      const _ModuleLink('Geri Bildirim', 'Hata, eksik, öneri, teşekkür ve tebrik', Icons.rate_review_outlined, BYS360Colors.info, PortalWebScreen(moduleTitle: 'Geri Bildirim', moduleSubtitle: 'Ekran hatası, eksik, öneri, teşekkür ve tebriklerinizi iletin.', modulePath: '/feedback/gonder')),
      _ModuleLink('KPI / Hedef', 'Hedef ve gerçekleşme', Icons.flag_outlined, BYS360Colors.success, KpiScreen(apiClient: apiClient)),
      _ModuleLink('AI Karar Destek', 'Özet ve dikkat notu', Icons.psychology_alt_outlined, BYS360Colors.purple, AiDecisionScreen(apiClient: apiClient)),
      _ModuleLink('BYS360 Asistanı', 'Rehberlik ve yönlendirme', Icons.chat_bubble_outline, BYS360Colors.corporateRed, AssistantScreen(apiClient: apiClient)),
      _ModuleLink('İletişim', 'Mesaj ve duyurular', Icons.forum_outlined, BYS360Colors.info, CommunicationScreen(apiClient: apiClient)),
      _ModuleLink('Bildirimler', 'Görev ve süreç uyarıları', Icons.notifications_outlined, BYS360Colors.warning, NotificationsScreen(apiClient: apiClient)),
      _ModuleLink('Destek', 'Yardım ve talepler', Icons.support_agent, BYS360Colors.info, SupportScreen(apiClient: apiClient)),
      _ModuleLink('Anketler', 'Nabız ve geri bildirim', Icons.poll_outlined, BYS360Colors.warning, SurveysScreen(apiClient: apiClient)),
      _ModuleLink('Ayarlar', 'Rol, menü ve güvenlik', Icons.tune_outlined, BYS360Colors.corporateRed, SettingsScreen(apiClient: apiClient)),
      _ModuleLink('Raporlar', 'Analiz ve çıktılar', Icons.insert_chart_outlined, BYS360Colors.success, ReportsScreen(apiClient: apiClient)),
      _ModuleLink('Hesabım', 'Profil ve oturum', Icons.account_circle_outlined, BYS360Colors.corporateRed, ProfileScreen(apiClient: apiClient)),
    ];

    return BYSPage(
      title: 'Modüller',
      subtitle: 'Portal, geri bildirim ve aktif BYS360 modülleri tek kurumsal mobil dilde toplanır.',
      badge: 'Modül merkezi',
      children: [
        GridView.count(
          crossAxisCount: 2,
          childAspectRatio: 1.20,
          crossAxisSpacing: 9,
          mainAxisSpacing: 9,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          children: modules.map((module) => _ModuleTile(module: module, onTap: () => _open(context, module))).toList(),
        ),
        const BYSSectionTitle(title: 'Mobil kullanım ilkesi', subtitle: 'Her modül aynı tasarım ve aynı güvenlik sınırıyla çalışır'),
        const ActionTile(
          title: 'Ortak arayüz standardı',
          subtitle: 'Sayfa başlığı, kartlar, formlar, hata ve boş durum ekranları tüm modüllerde aynı yapıdadır.',
          icon: Icons.design_services_outlined,
          tone: BYS360Colors.info,
        ),
        const ActionTile(
          title: 'Güvenli işlem akışı',
          subtitle: 'Her ekranda önce yetki kapsamındaki bilgiler gösterilir; işlem formları modül modül tamamlanır.',
          icon: Icons.verified_user_outlined,
          tone: BYS360Colors.corporateRed,
        ),
      ],
    );
  }
}

class _ModuleRouteScaffold extends StatelessWidget {
  const _ModuleRouteScaffold({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: BYS360Colors.pageBackground,
      appBar: AppBar(title: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis)),
      body: Material(color: BYS360Colors.pageBackground, child: child),
    );
  }
}

class _ModuleLink {
  const _ModuleLink(this.title, this.subtitle, this.icon, this.tone, this.screen);
  final String title;
  final String subtitle;
  final IconData icon;
  final Color tone;
  final Widget screen;
}

class _ModuleTile extends StatelessWidget {
  const _ModuleTile({required this.module, required this.onTap});
  final _ModuleLink module;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      child: InkWell(
        borderRadius: BorderRadius.circular(BYS360Radii.lg),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(color: module.tone.withValues(alpha: .10), borderRadius: BorderRadius.circular(13)),
                    child: Icon(module.icon, color: module.tone, size: 20),
                  ),
                  const Spacer(),
                  const Icon(Icons.chevron_right, color: BYS360Colors.mutedText, size: 19),
                ],
              ),
              const SizedBox(height: 10),
              Text(module.title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900), maxLines: 1, overflow: TextOverflow.ellipsis),
              const SizedBox(height: 4),
              Text(module.subtitle, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText, height: 1.20), maxLines: 2, overflow: TextOverflow.ellipsis),
            ],
          ),
        ),
      ),
    );
  }
}
