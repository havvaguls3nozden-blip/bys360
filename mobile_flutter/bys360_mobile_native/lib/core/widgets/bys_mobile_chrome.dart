import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import '../utils/bys360_copy.dart';
import 'bys360_logo.dart';

// BYS360 MOBILE V2.8.24 DESIGN SYSTEM CHROME
class BYSMobileAppBar extends StatelessWidget implements PreferredSizeWidget {
  const BYSMobileAppBar({
    super.key,
    required this.title,
    this.onMenu,
    this.onBack,
    this.showProfile = false,
    this.onProfile,
    this.showNotification = false,
    this.onNotification,
  });

  final String title;
  final VoidCallback? onMenu;
  final VoidCallback? onBack;
  final bool showProfile;
  final VoidCallback? onProfile;
  final bool showNotification;
  final VoidCallback? onNotification;

  @override
  Size get preferredSize => const Size.fromHeight(72);

  @override
  Widget build(BuildContext context) {
    final safeTop = MediaQuery.paddingOf(context).top;
    return Container(
      height: preferredSize.height + safeTop,
      padding: EdgeInsets.only(top: safeTop),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
          colors: [BYS360Colors.deepRed, BYS360Colors.corporateRed],
        ),
        boxShadow: [BoxShadow(color: Color(0x22000000), blurRadius: 18, offset: Offset(0, 8))],
      ),
      child: SafeArea(
        top: false,
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Row(
            children: [
              _ChromeIconButton(icon: onBack == null ? Icons.menu : Icons.arrow_back, tooltip: onBack == null ? 'Menü' : 'Geri', onPressed: onBack ?? onMenu),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  BYS360Copy.title(title),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    height: 1,
                    fontWeight: FontWeight.w900,
                    decoration: TextDecoration.none,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              if (showNotification)
                _ChromeIconButton(icon: Icons.notifications_none_rounded, tooltip: 'Bildirimler', onPressed: onNotification)
              else if (showProfile)
                _ChromeIconButton(icon: Icons.account_circle_outlined, tooltip: 'Profil', onPressed: onProfile)
              else
                Container(
                  width: 54,
                  height: 42,
                  padding: const EdgeInsets.all(5),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(13)),
                  child: const BYS360AppIcon(borderRadius: 8),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ChromeIconButton extends StatelessWidget {
  const _ChromeIconButton({required this.icon, required this.tooltip, this.onPressed});

  final IconData icon;
  final String tooltip;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 44,
      height: 44,
      child: IconButton(
        tooltip: tooltip,
        onPressed: onPressed,
        icon: Icon(icon, color: Colors.white, size: 28),
      ),
    );
  }
}

class BYSMobileBottomNav extends StatelessWidget {
  const BYSMobileBottomNav({super.key, required this.selectedIndex, required this.onDestinationSelected});

  final int selectedIndex;
  final ValueChanged<int> onDestinationSelected;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        color: Colors.white,
        boxShadow: [BoxShadow(color: Color(0x14000000), blurRadius: 18, offset: Offset(0, -8))],
      ),
      child: NavigationBar(
        selectedIndex: selectedIndex,
        onDestinationSelected: onDestinationSelected,
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Ana Sayfa'),
          NavigationDestination(icon: Icon(Icons.bar_chart_outlined), selectedIcon: Icon(Icons.bar_chart), label: 'Performans'),
          NavigationDestination(icon: Icon(Icons.apps_outlined), selectedIcon: Icon(Icons.apps), label: 'Modüller'),
          NavigationDestination(icon: Icon(Icons.chat_bubble_outline), selectedIcon: Icon(Icons.chat_bubble), label: 'Asistan'),
          NavigationDestination(icon: Icon(Icons.notifications_none_outlined), selectedIcon: Icon(Icons.notifications), label: 'Bildirim'),
        ],
      ),
    );
  }
}

class BYSUnifiedBackground extends StatelessWidget {
  const BYSUnifiedBackground({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [BYS360Colors.pageBackgroundWarm, BYS360Colors.pageBackground],
        ),
      ),
      child: child,
    );
  }
}
