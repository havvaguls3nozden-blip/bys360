import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import '../utils/bys360_copy.dart';

class MetricCard extends StatelessWidget {
  const MetricCard({
    super.key,
    required this.title,
    required this.value,
    required this.subtitle,
    this.icon,
    this.tone = BYS360Colors.corporateRed,
    this.onTap,
  });

  final String title;
  final String value;
  final String subtitle;
  final IconData? icon;
  final Color tone;
  final VoidCallback? onTap;

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
                width: 44,
                height: 44,
                decoration: BoxDecoration(color: tone.withValues(alpha: .10), borderRadius: BorderRadius.circular(16)),
                child: Icon(icon ?? Icons.insights, color: tone, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(BYS360Copy.title(title), style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900), maxLines: 1, overflow: TextOverflow.ellipsis),
                    const SizedBox(height: 3),
                    Text(BYS360Copy.subtitle(subtitle), style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText), maxLines: 2, overflow: TextOverflow.ellipsis),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Text(BYS360Copy.clean(value), style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900, color: tone)),
            ],
          ),
        ),
      ),
    );
  }
}

class CompactMetricCard extends StatelessWidget {
  const CompactMetricCard({super.key, required this.label, required this.value, required this.icon, this.tone = BYS360Colors.corporateRed, this.onTap});

  final String label;
  final String value;
  final IconData icon;
  final Color tone;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(BYS360Radii.lg),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(13),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(BYS360Radii.lg),
          border: Border.all(color: BYS360Colors.cardBorder),
          boxShadow: BYS360Shadows.card,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 34,
                  height: 34,
                  decoration: BoxDecoration(color: tone.withValues(alpha: .10), borderRadius: BorderRadius.circular(13)),
                  child: Icon(icon, color: tone, size: 18),
                ),
                const Spacer(),
                Text(BYS360Copy.clean(value), style: Theme.of(context).textTheme.titleMedium?.copyWith(color: tone, fontWeight: FontWeight.w900)),
              ],
            ),
            const SizedBox(height: 9),
            Text(BYS360Copy.title(label), style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText, fontWeight: FontWeight.w800), maxLines: 2, overflow: TextOverflow.ellipsis),
          ],
        ),
      ),
    );
  }
}

class ActionTile extends StatelessWidget {
  const ActionTile({super.key, required this.title, required this.subtitle, required this.icon, this.onTap, this.tone = BYS360Colors.corporateRed});

  final String title;
  final String subtitle;
  final IconData icon;
  final VoidCallback? onTap;
  final Color tone;

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
                width: 42,
                height: 42,
                decoration: BoxDecoration(color: tone.withValues(alpha: .10), borderRadius: BorderRadius.circular(15)),
                child: Icon(icon, color: tone, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(BYS360Copy.title(title), style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900), maxLines: 1, overflow: TextOverflow.ellipsis),
                    const SizedBox(height: 3),
                    Text(BYS360Copy.subtitle(subtitle), style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText), maxLines: 2, overflow: TextOverflow.ellipsis),
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

class ProgressCard extends StatelessWidget {
  const ProgressCard({super.key, required this.title, required this.subtitle, required this.progress, this.tone = BYS360Colors.corporateRed});

  final String title;
  final String subtitle;
  final int progress;
  final Color tone;

  @override
  Widget build(BuildContext context) {
    final clamped = progress.clamp(0, 100);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(child: Text(BYS360Copy.title(title), style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900), maxLines: 1, overflow: TextOverflow.ellipsis)),
                Text('%$clamped', style: Theme.of(context).textTheme.titleMedium?.copyWith(color: tone, fontWeight: FontWeight.w900)),
              ],
            ),
            const SizedBox(height: 4),
            Text(BYS360Copy.subtitle(subtitle), style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText), maxLines: 2, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(999),
              child: LinearProgressIndicator(value: clamped / 100, minHeight: 7, backgroundColor: tone.withValues(alpha: .12), color: tone),
            ),
          ],
        ),
      ),
    );
  }
}
