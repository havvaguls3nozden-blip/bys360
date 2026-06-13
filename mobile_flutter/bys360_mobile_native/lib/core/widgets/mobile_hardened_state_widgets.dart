import 'package:flutter/material.dart';

import '../hardening/mobile_error_texts.dart';

// BYS360_MOBILE_V2_8_29_ERROR_SCREENS
class MobileHardenedErrorState extends StatelessWidget {
  const MobileHardenedErrorState({
    super.key,
    this.title = MobileErrorTexts.genericTitle,
    this.message = MobileErrorTexts.genericMessage,
    this.onRetry,
  });

  final String title;
  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Card(
          elevation: 0,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.info_outline, size: 42),
                const SizedBox(height: 12),
                Text(title, style: Theme.of(context).textTheme.titleMedium, textAlign: TextAlign.center),
                const SizedBox(height: 8),
                Text(message, textAlign: TextAlign.center),
                if (onRetry != null) ...[
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: onRetry,
                    child: const Text('Tekrar dene'),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class MobileOfflineState extends StatelessWidget {
  const MobileOfflineState({super.key, this.onRetry});

  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return MobileHardenedErrorState(
      title: MobileErrorTexts.offlineTitle,
      message: MobileErrorTexts.offlineMessage,
      onRetry: onRetry,
    );
  }
}

class MobileTimeoutState extends StatelessWidget {
  const MobileTimeoutState({super.key, this.onRetry});

  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return MobileHardenedErrorState(
      title: MobileErrorTexts.timeoutTitle,
      message: MobileErrorTexts.timeoutMessage,
      onRetry: onRetry,
    );
  }
}
