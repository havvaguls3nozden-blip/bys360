import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import '../utils/bys360_copy.dart';

class ApiEmptyState extends StatelessWidget {
  const ApiEmptyState({super.key, required this.message, this.onRetry, this.title});

  final String message;
  final String? title;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final cleanMessage = BYS360Copy.error(message);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(color: BYS360Colors.softRed, borderRadius: BorderRadius.circular(15)),
                  child: const Icon(Icons.info_outline, color: BYS360Colors.corporateRed),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title ?? 'Bu sayfa şu anda açılamadı', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
                      const SizedBox(height: 4),
                      Text(cleanMessage, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: BYS360Colors.mutedText)),
                    ],
                  ),
                ),
              ],
            ),
            if (onRetry != null) ...[
              const SizedBox(height: 14),
              OutlinedButton.icon(onPressed: onRetry, icon: const Icon(Icons.refresh), label: const Text('Tekrar Dene')),
            ],
          ],
        ),
      ),
    );
  }
}

class BYSLoadingState extends StatelessWidget {
  const BYSLoadingState({super.key, this.message = 'Veriler yükleniyor'});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.4)),
              const SizedBox(width: 12),
              Text(message, style: const TextStyle(color: BYS360Colors.mutedText, fontWeight: FontWeight.w800)),
            ],
          ),
        ),
      ),
    );
  }
}
