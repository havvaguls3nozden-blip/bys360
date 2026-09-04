import 'package:flutter/material.dart';

import '../../models/mobile_record.dart';
import '../theme/app_theme.dart';
import '../utils/bys360_copy.dart';
import '../utils/bys360_status_labels.dart';

class StatusPill extends StatelessWidget {
  const StatusPill({super.key, required this.text, this.tone = BYS360Colors.corporateRed});

  final String text;
  final Color tone;

  @override
  Widget build(BuildContext context) {
    final label = bys360GenericStatusLabel(BYS360Copy.clean(text));
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: tone.withValues(alpha: .10),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: tone.withValues(alpha: .10)),
      ),
      child: Text(label, style: TextStyle(color: tone, fontWeight: FontWeight.w900, fontSize: 11)),
    );
  }
}

class RecordCard extends StatelessWidget {
  const RecordCard({super.key, required this.record, required this.icon, this.tone = BYS360Colors.corporateRed, this.onTap});

  final MobileRecord record;
  final IconData icon;
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
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
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
                        Text(BYS360Copy.title(record.title), style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900), maxLines: 2, overflow: TextOverflow.ellipsis),
                        if (record.subtitle != null && record.subtitle!.trim().isNotEmpty) ...[
                          const SizedBox(height: 3),
                          Text(BYS360Copy.subtitle(record.subtitle!), style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText), maxLines: 2, overflow: TextOverflow.ellipsis),
                        ],
                      ],
                    ),
                  ),
                  if (record.value != null && record.value!.trim().isNotEmpty)
                    Text(BYS360Copy.clean(record.value!), style: Theme.of(context).textTheme.titleMedium?.copyWith(color: tone, fontWeight: FontWeight.w900)),
                ],
              ),
              if (record.status != null || record.meta != null) ...[
                const SizedBox(height: 10),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    if (record.status != null) StatusPill(text: record.status!, tone: tone),
                    if (record.meta != null) StatusPill(text: record.meta!, tone: BYS360Colors.info),
                  ],
                ),
              ],
              if (record.progress != null) ...[
                const SizedBox(height: 10),
                ClipRRect(
                  borderRadius: BorderRadius.circular(999),
                  child: LinearProgressIndicator(
                    value: record.progress!.clamp(0, 100) / 100,
                    minHeight: 6,
                    backgroundColor: tone.withValues(alpha: .12),
                    color: tone,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class ModuleIntroCard extends StatelessWidget {
  const ModuleIntroCard({super.key, required this.icon, required this.title, required this.body, this.tone = BYS360Colors.corporateRed});

  final IconData icon;
  final String title;
  final String body;
  final Color tone;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
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
                  Text(BYS360Copy.title(title), style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900), maxLines: 2, overflow: TextOverflow.ellipsis),
                  const SizedBox(height: 3),
                  Text(BYS360Copy.subtitle(body), style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText, height: 1.25), maxLines: 3, overflow: TextOverflow.ellipsis),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
