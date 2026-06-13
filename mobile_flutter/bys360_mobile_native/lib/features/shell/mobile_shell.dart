// BYS360_MOBILE_V2_8_45_ANDROID_HAMBURGER_DRAWER_FIX
// BYS360_MOBILE_V2_8_24_SCAFFOLD_SCOPE_FIX
// BYS360_MOBILE_V2_8_24_BUILD_FIX_OK
import 'package:flutter/material.dart';

import '../../core/auth/token_store.dart';
import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/utils/bys360_copy.dart';
import '../../core/widgets/bys360_logo.dart';
import '../../core/widgets/bys_mobile_chrome.dart';
import '../ai_decision/ai_decision_screen.dart';
import '../assistant/assistant_screen.dart';
import '../communication/communication_screen.dart';
import '../dashboard/dashboard_screen.dart';
import '../kpi/kpi_screen.dart';
import '../modules/modules_screen.dart';
import '../notifications/notifications_screen.dart';
import '../performance/performance_screen.dart';
import '../personnel/personnel_screen.dart';
import '../portal/portal_web_screen.dart';
import '../profile/profile_screen.dart';
import '../reports/reports_screen.dart';
import '../settings/settings_screen.dart';
import '../support/support_screen.dart';
import '../surveys/surveys_screen.dart';

class MobileShell extends StatefulWidget {
  const MobileShell({super.key, required this.onLogout});

  final Future<void> Function() onLogout;

  @override
  State<MobileShell> createState() => _MobileShellState();
}

class _MobileShellState extends State<MobileShell> {
  final ApiClient _apiClient = ApiClient();
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final pages = [
      DashboardScreen(apiClient: _apiClient),
      PerformanceScreen(apiClient: _apiClient),
      ModulesScreen(apiClient: _apiClient),
      AssistantScreen(apiClient: _apiClient),
      NotificationsScreen(apiClient: _apiClient),
    ];

    return Scaffold(
      key: _scaffoldKey,
      drawerEnableOpenDragGesture: true,
      backgroundColor: BYS360Colors.pageBackground,
      appBar: BYSMobileAppBar(
        title: _title,
        onMenu: () {
          final scaffold = _scaffoldKey.currentState;
          if (scaffold == null) return;
          if (!scaffold.isDrawerOpen) {
            scaffold.openDrawer();
          }
        },
        showProfile: _index != 4,
        showNotification: _index == 0,
        onProfile: () => _push(ProfileScreen(apiClient: _apiClient), 'Profil'),
        onNotification: () => setState(() => _index = 4),
      ),
      drawer: _MobileDrawer(
        apiClient: _apiClient,
        onLogout: widget.onLogout,
        onNavigateTab: (index) {
          Navigator.of(context).pop();
          setState(() => _index = index);
        },
        onPush: (screen, title) {
          Navigator.of(context).pop();
          _push(screen, title);
        },
      ),
      body: pages[_index],
      bottomNavigationBar: BYSMobileBottomNav(selectedIndex: _index, onDestinationSelected: (value) => setState(() => _index = value)),
    );
  }

  void _push(Widget screen, String title) {
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => _UnifiedStandalonePage(title: title, apiClient: _apiClient, child: screen),
    ));
  }

  String get _title {
    switch (_index) {
      case 1:
        return 'Performans Yönetimi';
      case 2:
        return 'Modüller';
      case 3:
        return 'BYS360 Asistanı';
      case 4:
        return 'Bildirimler';
      default:
        return 'BYS360';
    }
  }
}

class _UnifiedStandalonePage extends StatelessWidget {
  const _UnifiedStandalonePage({required this.title, required this.apiClient, required this.child});

  final String title;
  final ApiClient apiClient;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      
      backgroundColor: BYS360Colors.pageBackground,
      appBar: BYSMobileAppBar(title: title, onBack: () => Navigator.of(context).maybePop()),
      body: child,
      bottomNavigationBar: BYSMobileBottomNav(
        selectedIndex: _selectedIndex(title),
        onDestinationSelected: (index) => _openBottom(context, index),
      ),
    );
  }

  int _selectedIndex(String title) {
    if (title.contains('Performans')) return 1;
    if (title.contains('Asistan')) return 3;
    if (title.contains('Bildirim')) return 4;
    if (title.contains('Modül')) return 2;
    return 0;
  }

  void _openBottom(BuildContext context, int index) {
    if (index == _selectedIndex(title)) return;
    final Widget screen;
    final String nextTitle;
    switch (index) {
      case 1:
        screen = PerformanceScreen(apiClient: apiClient);
        nextTitle = 'Performans Yönetimi';
        break;
      case 2:
        screen = ModulesScreen(apiClient: apiClient);
        nextTitle = 'Modüller';
        break;
      case 3:
        screen = AssistantScreen(apiClient: apiClient);
        nextTitle = 'BYS360 Asistanı';
        break;
      case 4:
        screen = NotificationsScreen(apiClient: apiClient);
        nextTitle = 'Bildirimler';
        break;
      default:
        screen = DashboardScreen(apiClient: apiClient);
        nextTitle = 'BYS360';
    }
    Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => _UnifiedStandalonePage(title: nextTitle, apiClient: apiClient, child: screen)));
  }
}

class _MobileDrawer extends StatelessWidget {
  const _MobileDrawer({required this.apiClient, required this.onLogout, required this.onNavigateTab, required this.onPush});

  final ApiClient apiClient;
  final Future<void> Function() onLogout;
  final ValueChanged<int> onNavigateTab;
  final void Function(Widget screen, String title) onPush;

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: SafeArea(
        child: Column(
          children: [
            _DrawerHeaderCard(onProfileTap: () => onPush(ProfileScreen(apiClient: apiClient), 'Profil')),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(vertical: 8),
                children: [
                  _DrawerTile(icon: Icons.home_outlined, title: 'Ana Sayfa', subtitle: 'Genel durum ve hızlı işlemler', onTap: () => onNavigateTab(0)),
                  _DrawerTile(icon: Icons.bar_chart_outlined, title: 'Performans Yönetimi', subtitle: 'Görev, dönem, karne ve onaylar', onTap: () => onNavigateTab(1)),
                  _DrawerTile(icon: Icons.apps_outlined, title: 'Modüller', subtitle: 'BYS360 modül kısayolları', onTap: () => onNavigateTab(2)),
                  _DrawerTile(icon: Icons.public_outlined, title: 'Kurumsal Portal', subtitle: 'Duyuru, paylaşım ve kurum içi portal', onTap: () => onPush(const PortalWebScreen(), 'Kurumsal Portal')),
                  _DrawerTile(icon: Icons.rate_review_outlined, title: 'Geri Bildirim', subtitle: 'Hata, eksik, öneri, teşekkür ve tebrik', onTap: () => onPush(const PortalWebScreen(moduleTitle: 'Geri Bildirim', moduleSubtitle: 'Ekran hatası, eksik, öneri, teşekkür ve tebriklerinizi iletin.', modulePath: '/feedback/gonder'), 'Geri Bildirim')),
                  _DrawerTile(icon: Icons.chat_bubble_outline, title: 'BYS360 Asistanı', subtitle: 'Kurumsal yönlendirme ve destek', onTap: () => onNavigateTab(3)),
                  _DrawerTile(icon: Icons.notifications_none_outlined, title: 'Bildirimler', subtitle: 'Bekleyen bildirimler', onTap: () => onNavigateTab(4)),
                  const Divider(height: 22),
                  _DrawerTile(icon: Icons.people_outline, title: 'Personel Yönetimi', subtitle: 'Personel ve organizasyon özetleri', onTap: () => onPush(PersonnelScreen(apiClient: apiClient), 'Personel Yönetimi')),
                  _DrawerTile(icon: Icons.support_agent_outlined, title: 'Destek Talepleri', subtitle: 'Talepler ve yanıtlar', onTap: () => onPush(SupportScreen(apiClient: apiClient), 'Destek Talepleri')),
                  _DrawerTile(icon: Icons.poll_outlined, title: 'Anketler', subtitle: 'Anketler ve cevaplama', onTap: () => onPush(SurveysScreen(apiClient: apiClient), 'Anketler')),
                  _DrawerTile(icon: Icons.campaign_outlined, title: 'İletişim', subtitle: 'Duyuru ve iletişim alanı', onTap: () => onPush(CommunicationScreen(apiClient: apiClient), 'İletişim')),
                  _DrawerTile(icon: Icons.track_changes_outlined, title: 'KPI / Hedef', subtitle: 'Hedef ve gösterge özetleri', onTap: () => onPush(KpiScreen(apiClient: apiClient), 'KPI ve Hedef')),
                  _DrawerTile(icon: Icons.analytics_outlined, title: 'Raporlar', subtitle: 'Rapor ve analiz alanı', onTap: () => onPush(ReportsScreen(apiClient: apiClient), 'Raporlar')),
                  _DrawerTile(icon: Icons.psychology_alt_outlined, title: 'AI Karar Destek', subtitle: 'Yetki kontrollü analiz özetleri', onTap: () => onPush(AiDecisionScreen(apiClient: apiClient), 'AI Karar Destek')),
                  _DrawerTile(icon: Icons.settings_outlined, title: 'Sistem Ayarları', subtitle: 'Yetki ve görünürlük kontrolleri', onTap: () => onPush(SettingsScreen(apiClient: apiClient), 'Sistem Ayarları')),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(12),
              child: OutlinedButton.icon(
                onPressed: onLogout,
                icon: const Icon(Icons.logout),
                label: const Text('Güvenli Çıkış'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DrawerHeaderCard extends StatelessWidget {
  const _DrawerHeaderCard({required this.onProfileTap});

  final VoidCallback onProfileTap;

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<MobileStoredSession>(
      future: TokenStore().storedSession,
      builder: (context, snapshot) {
        final session = snapshot.data ?? const MobileStoredSession();
        final userLabel = session.displayName?.trim().isNotEmpty == true
            ? session.displayName!.trim()
            : 'BYS360 Kullanıcısı';
        return Container(
          width: double.infinity,
          padding: const EdgeInsets.fromLTRB(18, 18, 18, 18),
          decoration: const BoxDecoration(
            gradient: LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight, colors: [BYS360Colors.corporateRed, BYS360Colors.deepRed]),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(
                height: 98,
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(24)),
                child: const BYS360Logo(),
              ),
              const SizedBox(height: 12),
              Text(BYS360Copy.title(userLabel), textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 15)),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: onProfileTap,
                icon: const Icon(Icons.account_circle_outlined, size: 18),
                label: const Text('Profil'),
                style: OutlinedButton.styleFrom(foregroundColor: Colors.white, side: const BorderSide(color: Colors.white38), minimumSize: const Size.fromHeight(38)),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _DrawerTile extends StatelessWidget {
  const _DrawerTile({required this.icon, required this.title, required this.subtitle, required this.onTap});

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Container(
        width: 38,
        height: 38,
        decoration: BoxDecoration(color: BYS360Colors.softRed, borderRadius: BorderRadius.circular(14)),
        child: Icon(icon, color: BYS360Colors.corporateRed, size: 21),
      ),
      title: Text(BYS360Copy.title(title), style: const TextStyle(fontWeight: FontWeight.w900)),
      subtitle: Text(BYS360Copy.subtitle(subtitle), maxLines: 1, overflow: TextOverflow.ellipsis),
      onTap: onTap,
    );
  }
}

// BYS360_MOBILE_V2_8_25_REAL_API_P0 mobil menü/yetki görünürlüğü sistem sözleşmesine hazırlanmıştır

// BYS360_MOBILE_V2_8_26_DASHBOARD_P1 scaffold scope safety

// KPI_TARGET_DASHBOARD_P1_ROUTE_ENTRY



