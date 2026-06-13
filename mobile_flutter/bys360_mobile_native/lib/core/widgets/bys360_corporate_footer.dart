// BYS360_MOBILE_V2_8_70_ANDROID_IMPRINT_FOOTER
import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class BYS360CorporateFooter extends StatelessWidget {
  const BYS360CorporateFooter({super.key, this.compact = false, this.onOpenImprint});

  final bool compact;
  final VoidCallback? onOpenImprint;

  static const String copyrightLine = '© 2026 Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı.';
  static const String rightsLine = 'Her hakkı saklıdır.';

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(top: 8, bottom: 6),
      padding: EdgeInsets.fromLTRB(14, compact ? 10 : 13, 14, compact ? 10 : 13),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: .92),
        borderRadius: BorderRadius.circular(BYS360Radii.lg),
        border: Border.all(color: BYS360Colors.cardBorder),
        boxShadow: BYS360Shadows.card,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Text(
            copyrightLine,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: BYS360Colors.mutedText,
                  fontWeight: FontWeight.w700,
                  height: 1.25,
                ),
          ),
          const SizedBox(height: 2),
          Text(
            rightsLine,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: BYS360Colors.mutedText,
                  fontWeight: FontWeight.w700,
                  height: 1.25,
                ),
          ),
          if (onOpenImprint != null) ...[
            const SizedBox(height: 8),
            TextButton.icon(
              onPressed: onOpenImprint,
              icon: const Icon(Icons.info_outline, size: 18),
              label: const Text('Künye'),
            ),
          ],
        ],
      ),
    );
  }
}
