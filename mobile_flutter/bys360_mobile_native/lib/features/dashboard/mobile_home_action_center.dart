import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/bys_page.dart';
import '../../models/dashboard_summary.dart';
import '../notifications/notifications_screen.dart';
import '../performance/performance_screen.dart';
import '../support/support_screen.dart';
import '../surveys/surveys_screen.dart';
import '../portal/portal_web_screen.dart';

class B61HomeActionCenter extends StatelessWidget {
  const B61HomeActionCenter({
    super.key,
    required this.summary,
    required this.apiClient,
    required this.onOpen,
  });

  final DashboardSummary summary;
  final ApiClient apiClient;
  final void Function(String title, Widget screen) onOpen;

  int get _totalWork => summary.pendingPerformance + summary.openTickets + summary.assignedSurveys;

  @override
  Widget build(BuildContext context) {
    final priority = _priorityAction();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const BYSSectionTitle(
          title: 'Kurumsal erişimler',
          subtitle: 'Portal ve geri bildirim alanları web uygulamasıyla aynı içerikte açılır.',
        ),
        _WideActionCard(
          title: 'Kurumsal Portal',
          subtitle: 'Duyurular, paylaşımlar, personel portalı ve kurum içi akış',
          icon: Icons.public_outlined,
          tone: BYS360Colors.corporateRed,
          onTap: () => onOpen('Kurumsal Portal', const PortalWebScreen()),
        ),
        _WideActionCard(
          title: 'Geri Bildirim',
          subtitle: 'Ekran hatası, eksik, öneri, teşekkür ve tebrik gönderimi',
          icon: Icons.rate_review_outlined,
          tone: BYS360Colors.info,
          onTap: () => onOpen('Geri Bildirim', const PortalWebScreen(moduleTitle: 'Geri Bildirim', moduleSubtitle: 'Ekran hatası, eksik, öneri, teşekkür ve tebriklerinizi iletin.', modulePath: '/feedback/gonder')),
        ),
        const SizedBox(height: 8),

        // B61B_MARKER_VISIBLE_HOME_ACTION_TITLE
        const BYSSectionTitle(
          title: 'Bugünkü işlemlerim',
          subtitle: 'Size ait görev, bildirim, destek ve anket durumları burada özetlenir.',
        ),
        _PriorityCard(priority: priority),
        const SizedBox(height: 10),
        GridView.count(
          crossAxisCount: 2,
          childAspectRatio: 1.04,
          crossAxisSpacing: 10,
          mainAxisSpacing: 10,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          children: [
            _ActionMetricCard(
              title: 'Performans',
              value: summary.pendingPerformance,
              caption: 'Değerlendirme ve görevler',
              icon: Icons.fact_check_outlined,
              tone: BYS360Colors.warning,
              onTap: () => onOpen('Performans Yönetimi', PerformanceScreen(apiClient: apiClient)),
            ),
            _ActionMetricCard(
              title: 'Bildirimler',
              value: summary.unreadNotifications,
              caption: 'Okunmamış bildirimler',
              icon: Icons.notifications_active_outlined,
              tone: BYS360Colors.corporateRed,
              onTap: () => onOpen('Bildirimler', NotificationsScreen(apiClient: apiClient)),
            ),
            _ActionMetricCard(
              title: 'Destek',
              value: summary.openTickets,
              caption: 'Açık destek talepleri',
              icon: Icons.support_agent,
              tone: BYS360Colors.info,
              onTap: () => onOpen('Destek Talepleri', SupportScreen(apiClient: apiClient)),
            ),
            _ActionMetricCard(
              title: 'Anketler',
              value: summary.assignedSurveys,
              caption: 'Yanıt bekleyen anketler',
              icon: Icons.poll_outlined,
              tone: BYS360Colors.success,
              onTap: () => onOpen('Anketler ve Geri Bildirim', SurveysScreen(apiClient: apiClient)),
            ),
          ],
        ),
        const SizedBox(height: 10),
        _ProcessSummaryPanel(totalWork: _totalWork),
      ],
    );
  }

  _PriorityAction _priorityAction() {
    if (summary.pendingPerformance > 0) {
      return _PriorityAction(
        title: 'Önce performans görevlerinizi kontrol edin',
        subtitle: '${summary.pendingPerformance} performans görevi takip bekliyor.',
        icon: Icons.fact_check_outlined,
        tone: BYS360Colors.warning,
        onTap: () => onOpen('Performans Yönetimi', PerformanceScreen(apiClient: apiClient)),
      );
    }
    if (summary.assignedSurveys > 0) {
      return _PriorityAction(
        title: 'Yanıt bekleyen anketleriniz var',
        subtitle: '${summary.assignedSurveys} anket veya geri bildirim kaydı görünüyor.',
        icon: Icons.poll_outlined,
        tone: BYS360Colors.success,
        onTap: () => onOpen('Anketler ve Geri Bildirim', SurveysScreen(apiClient: apiClient)),
      );
    }
    if (summary.openTickets > 0) {
      return _PriorityAction(
        title: 'Açık destek taleplerinizi inceleyin',
        subtitle: '${summary.openTickets} destek talebi açık veya işlem bekliyor.',
        icon: Icons.support_agent,
        tone: BYS360Colors.info,
        onTap: () => onOpen('Destek Talepleri', SupportScreen(apiClient: apiClient)),
      );
    }
    if (summary.unreadNotifications > 0) {
      return _PriorityAction(
        title: 'Okunmamış bildirimleriniz var',
        subtitle: '${summary.unreadNotifications} bildirim kontrol bekliyor.',
        icon: Icons.notifications_active_outlined,
        tone: BYS360Colors.corporateRed,
        onTap: () => onOpen('Bildirimler', NotificationsScreen(apiClient: apiClient)),
      );
    }
    return const _PriorityAction(
      title: 'Bugün için ana süreçler güncel görünüyor',
      subtitle: 'Yeni görev oluşursa bu alanda öncelikli olarak gösterilecek.',
      icon: Icons.verified_outlined,
      tone: BYS360Colors.success,
      onTap: null,
    );
  }
}

class _PriorityAction {
  const _PriorityAction({
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
  final VoidCallback? onTap;
}

class _PriorityCard extends StatelessWidget {
  const _PriorityCard({required this.priority});

  final _PriorityAction priority;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(BYS360Radii.lg),
        onTap: priority.onTap,
        child: Padding(
          padding: const EdgeInsets.all(15),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: priority.tone.withValues(alpha: .10),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(priority.icon, color: priority.tone, size: 24),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      priority.title,
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      priority.subtitle,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText, height: 1.30),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              if (priority.onTap != null) const Icon(Icons.chevron_right, color: BYS360Colors.mutedText),
            ],
          ),
        ),
      ),
    );
  }
}

class _ActionMetricCard extends StatelessWidget {
  const _ActionMetricCard({
    required this.title,
    required this.value,
    required this.caption,
    required this.icon,
    required this.tone,
    required this.onTap,
  });

  final String title;
  final int value;
  final String caption;
  final IconData icon;
  final Color tone;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(BYS360Radii.lg),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(13),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(color: tone.withValues(alpha: .10), borderRadius: BorderRadius.circular(13)),
                    child: Icon(icon, color: tone, size: 20),
                  ),
                  const Spacer(),
                  Icon(value > 0 ? Icons.priority_high_rounded : Icons.check_rounded, color: value > 0 ? tone : BYS360Colors.success, size: 20),
                ],
              ),
              const Spacer(),
              Text('$value', style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: tone, fontWeight: FontWeight.w900)),
              const SizedBox(height: 3),
              Text(title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900), maxLines: 1, overflow: TextOverflow.ellipsis),
              const SizedBox(height: 2),
              Text(caption, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText), maxLines: 2, overflow: TextOverflow.ellipsis),
            ],
          ),
        ),
      ),
    );
  }
}

class _ProcessSummaryPanel extends StatelessWidget {
  const _ProcessSummaryPanel({required this.totalWork});

  final int totalWork;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(BYS360Radii.xl),
        border: Border.all(color: BYS360Colors.cardBorder),
        boxShadow: BYS360Shadows.card,
      ),
      child: Column(
        children: [
          const _StatusLine(
            icon: Icons.shield_outlined,
            title: 'Güvenli kullanım',
            subtitle: 'Oturumunuz korunur; süre dolarsa yeniden giriş yapmanız istenir.',
            tone: BYS360Colors.corporateRed,
          ),
          const SizedBox(height: 12),
          _StatusLine(
            icon: totalWork == 0 ? Icons.task_alt_outlined : Icons.pending_actions_outlined,
            title: totalWork == 0 ? 'Ana süreçlerde bekleyen iş görünmüyor' : '$totalWork ana süreç takip bekliyor',
            subtitle: 'Performans, destek ve anket kayıtları ana sayfada birlikte izlenir.',
            tone: totalWork == 0 ? BYS360Colors.success : BYS360Colors.info,
          ),
        ],
      ),
    );
  }
}

class _StatusLine extends StatelessWidget {
  const _StatusLine({required this.icon, required this.title, required this.subtitle, required this.tone});

  final IconData icon;
  final String title;
  final String subtitle;
  final Color tone;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(color: tone.withValues(alpha: .10), borderRadius: BorderRadius.circular(14)),
          child: Icon(icon, color: tone, size: 21),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900)),
              const SizedBox(height: 3),
              Text(subtitle, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText, height: 1.30)),
            ],
          ),
        ),
      ],
    );
  }
}

// BYS360_MOBILE_V2_8_61B_HOME_UI_TEXT_CLEAN
// B61B_MARKER_HOME_UI_NO_RELEASE_WORDING
// BYS360_MOBILE_V2_8_61C_HOME_UI_TEXT_FINAL
// B61C_MARKER_HOME_USER_TEXT_ONLY

// BYS360_MOBILE_V2_8_70_ANDROID_IMPRINT_FOOTER



class _WideActionCard extends StatelessWidget {
  const _WideActionCard({required this.title, required this.subtitle, required this.icon, required this.tone, required this.onTap});

  final String title;
  final String subtitle;
  final IconData icon;
  final Color tone;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(BYS360Radii.lg),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(color: tone.withValues(alpha: .10), borderRadius: BorderRadius.circular(16)),
                child: Icon(icon, color: tone, size: 23),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900), maxLines: 1, overflow: TextOverflow.ellipsis),
                    const SizedBox(height: 4),
                    Text(subtitle, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText, height: 1.28), maxLines: 2, overflow: TextOverflow.ellipsis),
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
}
