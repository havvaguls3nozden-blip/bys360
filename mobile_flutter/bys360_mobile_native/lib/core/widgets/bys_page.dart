import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import '../utils/bys360_copy.dart';
import 'bys360_logo.dart';
import 'bys_mobile_chrome.dart';

class BYSPage extends StatelessWidget {
  const BYSPage({
    super.key,
    required this.title,
    required this.subtitle,
    required this.children,
    this.trailing,
    this.onRefresh,
    this.badge,
  });

  final String title;
  final String subtitle;
  final String? badge;
  final List<Widget> children;
  final Widget? trailing;
  final Future<void> Function()? onRefresh;

  @override
  Widget build(BuildContext context) {
    final content = BYSUnifiedBackground(
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(14, 14, 14, 96),
        children: [
          _BYSPageHero(title: title, subtitle: subtitle, badge: badge, trailing: trailing),
          const SizedBox(height: 12),
          ...children,
        ],
      ),
    );

    if (onRefresh == null) return content;
    return RefreshIndicator(onRefresh: onRefresh!, child: content);
  }
}

class _BYSPageHero extends StatelessWidget {
  const _BYSPageHero({required this.title, required this.subtitle, this.badge, this.trailing});

  final String title;
  final String subtitle;
  final String? badge;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(BYS360Radii.xl),
        border: Border.all(color: BYS360Colors.cardBorder),
        boxShadow: BYS360Shadows.elevated,
      ),
      clipBehavior: Clip.antiAlias,
      child: Stack(
        children: [
          Positioned(
            right: -12,
            top: -18,
            child: Opacity(
              opacity: .040,
              child: Transform.rotate(angle: -.06, child: const BYS360AppIcon(size: 118, borderRadius: 26)),
            ),
          ),
          Positioned(left: 0, top: 0, bottom: 0, child: Container(width: 6, color: BYS360Colors.corporateRed)),
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 18, 14, 18),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (badge != null && badge!.trim().isNotEmpty) ...[
                        _HeroBadge(text: badge!),
                        const SizedBox(height: 10),
                      ],
                      Text(
                        BYS360Copy.title(title),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                              color: BYS360Colors.ink,
                              fontWeight: FontWeight.w900,
                              height: 1.05,
                              decoration: TextDecoration.none,
                            ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        BYS360Copy.subtitle(subtitle),
                        maxLines: 3,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: BYS360Colors.mutedText, height: 1.28),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 10),
                SizedBox(
                  width: 70,
                  height: 62,
                  child: FittedBox(
                    fit: BoxFit.contain,
                    child: trailing ?? const BYS360AppIcon(size: 74, borderRadius: 18),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _HeroBadge extends StatelessWidget {
  const _HeroBadge({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: BYS360Colors.softRed,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: BYS360Colors.corporateRed.withValues(alpha: .12)),
      ),
      child: Text(
        BYS360Copy.clean(text),
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(color: BYS360Colors.corporateRed, fontWeight: FontWeight.w900, fontSize: 11, decoration: TextDecoration.none),
      ),
    );
  }
}

class BYSSectionTitle extends StatelessWidget {
  const BYSSectionTitle({super.key, required this.title, this.subtitle, this.action});

  final String title;
  final String? subtitle;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(2, 16, 2, 6),
      child: Row(
        children: [
          Container(width: 5, height: subtitle == null ? 24 : 38, decoration: BoxDecoration(color: BYS360Colors.corporateRed, borderRadius: BorderRadius.circular(99))),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(BYS360Copy.title(title), style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
                if (subtitle != null) ...[
                  const SizedBox(height: 2),
                  Text(BYS360Copy.subtitle(subtitle!), style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: BYS360Colors.mutedText)),
                ],
              ],
            ),
          ),
          if (action != null) action!,
        ],
      ),
    );
  }
}

class BYSInfoPanel extends StatelessWidget {
  const BYSInfoPanel({super.key, required this.icon, required this.title, required this.body, this.tint = BYS360Colors.corporateRed});

  final IconData icon;
  final String title;
  final String body;
  final Color tint;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(color: tint.withValues(alpha: .10), borderRadius: BorderRadius.circular(15)),
              child: Icon(icon, color: tint, size: 22),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(BYS360Copy.title(title), style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900)),
                  const SizedBox(height: 4),
                  Text(BYS360Copy.subtitle(body), style: const TextStyle(color: BYS360Colors.mutedText, height: 1.32)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
