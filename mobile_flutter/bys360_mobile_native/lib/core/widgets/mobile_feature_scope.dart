import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import '../utils/bys360_copy.dart';
import 'record_widgets.dart';

/// BYS360 mobil modül işlem başlığı veri modeli.
/// Kullanıcı ekranında teknik paket / kod dili göstermez; sade kurumsal açıklama üretir.
class MobileFeatureScope {
  const MobileFeatureScope({
    required this.title,
    required this.description,
    this.status = '',
    this.phase = '',
    this.icon = Icons.check_circle_outline,
  });

  final String title;
  final String description;
  final String status;
  final String phase;
  final IconData icon;
}

class MobileFeatureScopeCard extends StatelessWidget {
  const MobileFeatureScopeCard({
    super.key,
    required this.features,
    this.tone = BYS360Colors.corporateRed,
  });

  final List<MobileFeatureScope> features;
  final Color tone;

  @override
  Widget build(BuildContext context) {
    if (features.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ...features.map(
          (feature) => ModuleIntroCard(
            icon: feature.icon,
            title: feature.title,
            body: _cleanDescription(feature),
            tone: tone,
          ),
        ),
      ],
    );
  }

  String _cleanDescription(MobileFeatureScope feature) {
    final text = BYS360Copy.subtitle(feature.description);
    if (text.trim().isNotEmpty) return text;
    return 'Bu başlık mobil uygulama içinde aynı kurumsal tasarım diliyle gösterilir.';
  }
}
