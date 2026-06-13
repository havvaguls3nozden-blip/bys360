import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/bys_page.dart';
import 'performance_manager_view_screen.dart';
import 'performance_president_approvals_screen.dart';
import 'performance_risk_analysis_screen.dart';
import 'performance_route_shell.dart';

class PerformanceExecutiveP1Screen extends StatelessWidget {
  const PerformanceExecutiveP1Screen({super.key, required this.apiClient});

  final ApiClient apiClient;

  void _open(BuildContext context, String title, Widget child) {
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => PerformanceMobileRouteShell(apiClient: apiClient, title: title, child: child),
    ));
  }

  @override
  Widget build(BuildContext context) {
    return BYSPage(
      title: 'Performans Yönetici Alanı',
      subtitle: 'Başkan/Üst Onay, risk analizi ve yönetici görünümü aynı mobil performans omurgasında çalışır.',
      badge: 'Yönetici Alanı',
      children: [
        const BYSSectionTitle(
          title: 'Kritik yönetici ekranları',
          subtitle: 'Veriler BYS360 yetki kurallarıyla sınırlandırılır',
        ),
        _BYS360MobileActionTile(
          title: 'Başkan/Üst Onayları',
          subtitle: '70 altı sonuç, yayın kilidi ve onay bekleyen karneler',
          icon: Icons.verified_user_outlined,
          tone: BYS360Colors.warning,
          onTap: () => _open(context, 'Başkan/Üst Onayları', PerformancePresidentApprovalsScreen(apiClient: apiClient)),
        ),
        _BYS360MobileActionTile(
          title: 'Risk Analizi',
          subtitle: 'Düşük performans, gecikme ve tekrar eden risk göstergeleri',
          icon: Icons.warning_amber_rounded,
          tone: BYS360Colors.danger,
          onTap: () => _open(context, 'Risk Analizi', PerformanceRiskAnalysisScreen(apiClient: apiClient)),
        ),
        _BYS360MobileActionTile(
          title: 'Yönetici Görünümü',
          subtitle: 'Yetki kapsamındaki ekip, görev ve karne özetleri',
          icon: Icons.dashboard_customize_outlined,
          tone: BYS360Colors.info,
          onTap: () => _open(context, 'Yönetici Görünümü', PerformanceManagerViewScreen(apiClient: apiClient)),
        ),
        const BYSInfoPanel(
          icon: Icons.lock_outline,
          title: 'Yetki kontrollü yönetici özeti',
          body: 'Bu alanda kişi detayı, yayınlanmamış karne ve hassas performans görüşleri yalnızca yetkiniz varsa görüntülenir. Yetkisiz kayıt mobilde de gösterilmez.',
        ),
      ],
    );
  }
}

// BYS360_MOBILE_V2_8_30_PERFORMANCE_EXECUTIVE_P1

class _BYS360MobileActionTile extends StatelessWidget {
  const _BYS360MobileActionTile({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.tone,
    required this.onTap,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final Color tone;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: tone.withValues(alpha: .10),
                  borderRadius: BorderRadius.circular(15),
                ),
                child: Icon(icon, color: tone, size: 23),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900)),
                    const SizedBox(height: 4),
                    Text(subtitle, style: const TextStyle(color: BYS360Colors.mutedText, height: 1.32)),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded, color: BYS360Colors.mutedText),
            ],
          ),
        ),
      ),
    );
  }
}

// BYS360_MOBILE_V2_8_31_ACTION_TILE_ADAPTER


class PerformanceExecutiveActionTile extends StatelessWidget {
  const PerformanceExecutiveActionTile({
    super.key,
    required this.title,
    required this.subtitle,
    required this.icon,
    this.onTap,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      child: ListTile(
        leading: Icon(icon, color: const Color(0xFF8B0000)),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
        subtitle: Text(subtitle),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION
