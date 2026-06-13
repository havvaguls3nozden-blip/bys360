import 'package:flutter/material.dart';

import '../../core/api/mobile_real_api_contract.dart';
import '../../core/cache/dashboard_summary_cache.dart';
import '../../core/config/app_config.dart';
import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/bys360_logo.dart';
import '../../core/widgets/bys360_corporate_footer.dart';
import '../../core/widgets/bys_mobile_chrome.dart';
import '../../core/widgets/metric_card.dart';
import '../../models/dashboard_summary.dart';
import '../ai_decision/ai_decision_screen.dart';
import '../about/about_screen.dart';
import '../assistant/assistant_screen.dart';
import '../communication/communication_screen.dart';
import '../kpi/kpi_screen.dart';
import '../notifications/notifications_screen.dart';
import '../performance/performance_screen.dart';
import '../personnel/personnel_screen.dart';
import '../profile/profile_screen.dart';
import '../portal/portal_web_screen.dart';
import '../support/support_screen.dart';
import '../surveys/surveys_screen.dart';
import 'tarihi_alan_weather_card.dart';
import 'mobile_home_action_center.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<DashboardSummary> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<DashboardSummary> _load() async {
    try {
      final payload = await widget.apiClient.get(MobileRealApiContract.dashboardSummary);
      final summary = DashboardSummary.fromJson(Map<String, dynamic>.from(payload as Map));
      await DashboardSummaryCache.save(summary);
      return summary;
    } catch (_) {
      final cached = await DashboardSummaryCache.readFresh();
      if (cached != null) return cached;
      if (AppConfig.demoFallback) return DashboardSummary.demo();
      rethrow;
    }
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  void _open(String title, Widget screen) {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => _DashboardRouteScaffold(title: title, child: screen)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<DashboardSummary>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const BYSLoadingState();
        }
        if (snapshot.hasError) {
          return BYSPage(
            title: 'Ana Sayfa',
            subtitle: 'Mobil özet bilgileri şu anda alınamadı.',
            badge: 'Bağlantı kontrolü',
            onRefresh: _refresh,
            children: [
              ApiEmptyState(
                message: 'Ana sayfa bilgileri şu anda alınamadı. İnternet bağlantınızı kontrol edip tekrar deneyin.',
                onRetry: () => setState(() => _future = _load()),
              ),
            ],
          );
        }

        final summary = snapshot.data!;
        return BYSPage(
          title: 'Merhaba, ${summary.userName}',
          subtitle: 'Bekleyen işleriniz, bildirimleriniz ve hızlı işlemleriniz tek mobil panelde toplandı.',
          badge: 'BYS360 Mobile',
          trailing: Container(
            width: 86,
            height: 76,
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: Colors.white.withValues(alpha: .86)),
            ),
            child: const BYS360Logo(),
          ),
          onRefresh: _refresh,
          children: [
            _HeroStatusCard(summary: summary),
            const TarihiAlanWeatherCard(),
            const BYSSectionTitle(
              title: 'Bugünkü özet',
              subtitle: 'Öncelikli süreçlere hızlı bakış',
            ),
            _DashboardP1Grid(summary: summary, apiClient: widget.apiClient, onOpen: _open),
            B61HomeActionCenter(summary: summary, apiClient: widget.apiClient, onOpen: _open),
            const BYSSectionTitle(
              title: 'Bekleyen işler',
              subtitle: 'Tamamlanması gereken ana süreçler',
            ),
            _ProcessCard(
              title: 'Bekleyen işler',
              value: '${summary.pendingPerformance + summary.openTickets + summary.assignedSurveys}',
              subtitle: 'Performans, destek ve anket süreçleriniz',
              icon: Icons.pending_actions_outlined,
              tone: BYS360Colors.corporateRed,
              onTap: () => _open('Performans Yönetimi', PerformanceScreen(apiClient: widget.apiClient)),
            ),
            _ProcessCard(
              title: 'Performans görevlerim',
              value: '${summary.pendingPerformance}',
              subtitle: 'Size atanmış değerlendirme ve takip görevleri',
              icon: Icons.fact_check_outlined,
              tone: BYS360Colors.warning,
              onTap: () => _open('Performans Yönetimi', PerformanceScreen(apiClient: widget.apiClient)),
            ),
            _ProcessCard(
              title: 'Destek talepleri',
              value: '${summary.openTickets}',
              subtitle: 'Açık veya işlem bekleyen destek kayıtları',
              icon: Icons.support_agent,
              tone: BYS360Colors.info,
              onTap: () => _open('Destek Talepleri', SupportScreen(apiClient: widget.apiClient)),
            ),
            const BYSSectionTitle(
              title: 'Son işlemler',
              subtitle: 'Mobilde son durum özeti',
            ),
            _RecentActionTile(
              title: 'Bildirimler kontrol edildi',
              subtitle: '${summary.unreadNotifications} okunmamış bildirim görünüyor',
              icon: Icons.notifications_active_outlined,
              tone: BYS360Colors.warning,
              onTap: () => _open('Bildirimler', NotificationsScreen(apiClient: widget.apiClient)),
            ),
            _RecentActionTile(
              title: 'Performans özeti güncellendi',
              subtitle: '${summary.pendingPerformance} görev ve ${summary.pendingApprovals} onay kaydı takipte',
              icon: Icons.assessment_outlined,
              tone: BYS360Colors.corporateRed,
              onTap: () => _open('Performans Yönetimi', PerformanceScreen(apiClient: widget.apiClient)),
            ),
            _RecentActionTile(
              title: 'KPI ve hedef görünümü hazır',
              subtitle: 'Hedef gerçekleşme oranı %${summary.kpiSuccessRate}',
              icon: Icons.trending_up,
              tone: BYS360Colors.success,
              onTap: () => _open('KPI / Hedef Yönetimi', KpiScreen(apiClient: widget.apiClient)),
            ),
            const BYSSectionTitle(
              title: 'Hızlı işlemler',
              subtitle: 'Sık kullanılan mobil geçişler',
            ),
            _QuickActionWrap(
              actions: [
                _QuickAction('Portal', Icons.public_outlined, () => _open('Kurumsal Portal', const PortalWebScreen(initialPath: '/portal', title: 'Kurumsal Portal'))),
                _QuickAction('Geri Bildirim', Icons.rate_review_outlined, () => _open('Geri Bildirim', const PortalWebScreen(initialPath: '/feedback/gonder', title: 'Geri Bildirim'))),
                _QuickAction('Bildirimler', Icons.notifications_outlined, () => _open('Bildirimler', NotificationsScreen(apiClient: widget.apiClient))),
                _QuickAction('Profilim', Icons.person_outline, () => _open('Profilim', ProfileScreen(apiClient: widget.apiClient))),
                _QuickAction('Künye', Icons.info_outline, () => _open('Künye', const AboutScreen())),
                _QuickAction('Destek', Icons.support_agent, () => _open('Destek Talepleri', SupportScreen(apiClient: widget.apiClient))),
                _QuickAction('Anketler', Icons.poll_outlined, () => _open('Anketler ve Geri Bildirim', SurveysScreen(apiClient: widget.apiClient))),
                _QuickAction('Asistan', Icons.chat_bubble_outline, () => _open('BYS360 Asistanı', AssistantScreen(apiClient: widget.apiClient))),
                _QuickAction('Personel', Icons.people_outline, () => _open('Personel Yönetimi', PersonnelScreen(apiClient: widget.apiClient))),
              ],
            ),
            const BYSSectionTitle(
              title: 'Karar destek ve iletişim',
              subtitle: 'Kurumsal görünürlük alanları',
            ),
            ActionTile(
              title: 'AI Karar Destek',
              subtitle: 'Özet, risk ve dikkat notları',
              icon: Icons.psychology_alt_outlined,
              tone: BYS360Colors.purple,
              onTap: () => _open('AI Karar Destek', AiDecisionScreen(apiClient: widget.apiClient)),
            ),
            ActionTile(
              title: 'İletişim ve Duyurular',
              subtitle: 'Mesaj, duyuru ve kurumsal akış',
              icon: Icons.forum_outlined,
              tone: BYS360Colors.info,
              onTap: () => _open('İletişim ve Duyurular', CommunicationScreen(apiClient: widget.apiClient)),
            ),
            ActionTile(
              title: 'BYS360 Asistanı',
              subtitle: 'Doğru ekran ve işlem adımı rehberi',
              icon: Icons.chat_bubble_outline,
              tone: BYS360Colors.corporateRed,
              onTap: () => _open('BYS360 Asistanı', AssistantScreen(apiClient: widget.apiClient)),
            ),
            const BYSInfoPanel(
              icon: Icons.shield_outlined,
              title: 'Yetki kontrollü mobil görünüm',
              body: 'Mobil dashboard yalnızca yetkiniz dahilindeki özetleri gösterir. Rol matrisi ve menü görünürlüğü web ile aynı güvenlik çizgisinde çalışır.',
            ),
            const BYS360CorporateFooter(),
          ],
        );
      },
    );
  }
}

class _DashboardRouteScaffold extends StatelessWidget {
  const _DashboardRouteScaffold({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: BYS360Colors.pageBackground,
      appBar: BYSMobileAppBar(title: title, onBack: () => Navigator.of(context).maybePop()),
      body: Material(color: BYS360Colors.pageBackground, child: child),
    );
  }
}

class _HeroStatusCard extends StatelessWidget {
  const _HeroStatusCard({required this.summary});

  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final totalWork = summary.pendingPerformance + summary.openTickets + summary.assignedSurveys;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: BYS360Colors.corporateRed,
        borderRadius: BorderRadius.circular(BYS360Radii.xl),
        boxShadow: BYS360Shadows.elevated,
      ),
      child: Row(
        children: [
          Container(
            width: 54,
            height: 54,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: .14),
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: Colors.white.withValues(alpha: .24)),
            ),
            child: const Icon(Icons.dashboard_customize_outlined, color: Colors.white, size: 28),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  totalWork == 0 ? 'Bekleyen ana iş görünmüyor' : '$totalWork bekleyen işiniz var',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(color: Colors.white, fontWeight: FontWeight.w900),
                ),
                const SizedBox(height: 4),
                Text(
                  'Bildirim, destek ve performans süreçleri web verisiyle güncellenir.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.white.withValues(alpha: .84)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _DashboardP1Grid extends StatelessWidget {
  const _DashboardP1Grid({required this.summary, required this.apiClient, required this.onOpen});

  final DashboardSummary summary;
  final ApiClient apiClient;
  final void Function(String title, Widget screen) onOpen;

  @override
  Widget build(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      childAspectRatio: 1.34,
      crossAxisSpacing: 10,
      mainAxisSpacing: 10,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      children: [
        CompactMetricCard(
          label: 'Bekleyen işler',
          value: '${summary.pendingPerformance + summary.openTickets + summary.assignedSurveys}',
          icon: Icons.pending_actions_outlined,
          onTap: () => onOpen('Performans Yönetimi', PerformanceScreen(apiClient: apiClient)),
        ),
        CompactMetricCard(
          label: 'Performans',
          value: '${summary.pendingPerformance}',
          icon: Icons.fact_check_outlined,
          tone: BYS360Colors.warning,
          onTap: () => onOpen('Performans Yönetimi', PerformanceScreen(apiClient: apiClient)),
        ),
        CompactMetricCard(
          label: 'Bildirimler',
          value: '${summary.unreadNotifications}',
          icon: Icons.notifications_outlined,
          tone: BYS360Colors.warning,
          onTap: () => onOpen('Bildirimler', NotificationsScreen(apiClient: apiClient)),
        ),
        CompactMetricCard(
          label: 'Destek',
          value: '${summary.openTickets}',
          icon: Icons.support_agent,
          tone: BYS360Colors.info,
          onTap: () => onOpen('Destek Talepleri', SupportScreen(apiClient: apiClient)),
        ),
        CompactMetricCard(
          label: 'Son işlemler',
          value: '${summary.unreadMessages + summary.aiAlerts}',
          icon: Icons.history_outlined,
          tone: BYS360Colors.purple,
          onTap: () => onOpen('İletişim ve Duyurular', CommunicationScreen(apiClient: apiClient)),
        ),
        CompactMetricCard(
          label: 'Hızlı işlem',
          value: '6',
          icon: Icons.bolt_outlined,
          tone: BYS360Colors.success,
          onTap: () => onOpen('BYS360 Asistanı', AssistantScreen(apiClient: apiClient)),
        ),
      ],
    );
  }
}

class _ProcessCard extends StatelessWidget {
  const _ProcessCard({
    required this.title,
    required this.value,
    required this.subtitle,
    required this.icon,
    required this.tone,
    required this.onTap,
  });

  final String title;
  final String value;
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
                width: 48,
                height: 48,
                decoration: BoxDecoration(color: tone.withValues(alpha: .10), borderRadius: BorderRadius.circular(16)),
                child: Icon(icon, color: tone, size: 24),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900), maxLines: 1, overflow: TextOverflow.ellipsis),
                    const SizedBox(height: 4),
                    Text(subtitle, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText), maxLines: 2, overflow: TextOverflow.ellipsis),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Text(value, style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: tone, fontWeight: FontWeight.w900)),
              const SizedBox(width: 4),
              const Icon(Icons.chevron_right, color: BYS360Colors.mutedText),
            ],
          ),
        ),
      ),
    );
  }
}

class _RecentActionTile extends StatelessWidget {
  const _RecentActionTile({required this.title, required this.subtitle, required this.icon, required this.tone, required this.onTap});

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
          padding: const EdgeInsets.all(13),
          child: Row(
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
                    Text(title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900), maxLines: 1, overflow: TextOverflow.ellipsis),
                    const SizedBox(height: 3),
                    Text(subtitle, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText), maxLines: 2, overflow: TextOverflow.ellipsis),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: BYS360Colors.mutedText, size: 20),
            ],
          ),
        ),
      ),
    );
  }
}

class _QuickAction {
  const _QuickAction(this.label, this.icon, this.onTap);

  final String label;
  final IconData icon;
  final VoidCallback onTap;
}

class _QuickActionWrap extends StatelessWidget {
  const _QuickActionWrap({required this.actions});

  final List<_QuickAction> actions;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: actions.map((action) {
        return SizedBox(
          width: (MediaQuery.of(context).size.width - 48) / 2,
          child: InkWell(
            borderRadius: BorderRadius.circular(BYS360Radii.lg),
            onTap: action.onTap,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(BYS360Radii.lg),
                border: Border.all(color: BYS360Colors.cardBorder),
                boxShadow: BYS360Shadows.card,
              ),
              child: Row(
                children: [
                  Container(
                    width: 34,
                    height: 34,
                    decoration: BoxDecoration(color: BYS360Colors.softRed, borderRadius: BorderRadius.circular(12)),
                    child: Icon(action.icon, color: BYS360Colors.corporateRed, size: 19),
                  ),
                  const SizedBox(width: 9),
                  Expanded(
                    child: Text(action.label, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900), maxLines: 1, overflow: TextOverflow.ellipsis),
                  ),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}

// BYS360_MOBILE_V2_8_26_DASHBOARD_P1 Mobil dashboard uygulama hissi dönüşümü

// BYS360_MOBILE_V2_8_28_ASSISTANT_P1_MARKER dashboard assistant quick action compatible

// BYS360_MOBILE_V2_8_61_DASHBOARD_HOME_SESSION_COMPLETION
// B61A_MARKER_DASHBOARD_HOME_SESSION_SAFE_GATE

// BYS360_MOBILE_V2_8_61B_HOME_UI_TEXT_CLEAN

// BYS360_MOBILE_V2_8_61C_HOME_UI_TEXT_FINAL

// BYS360_MOBILE_V2_8_70_ANDROID_IMPRINT_FOOTER

// BYS360_MOBILE_V2_8_75_APP_MATURITY_P1_DASHBOARD_CACHE_HOOK
