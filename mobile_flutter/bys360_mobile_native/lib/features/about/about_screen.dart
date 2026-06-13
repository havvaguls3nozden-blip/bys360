// BYS360_MOBILE_V2_8_70_ANDROID_IMPRINT_FOOTER
import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/bys360_corporate_footer.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  static const String routeTitle = 'Künye';

  @override
  Widget build(BuildContext context) {
    return const BYSPage(
      title: 'Künye',
      subtitle: 'BYS360 mobil uygulamasına ilişkin kurumsal bilgi ve kullanım sınırları.',
      badge: 'Kurumsal Bilgi',
      children: [
        _AboutInfoCard(),
        _AboutPrinciplesCard(),
        BYS360CorporateFooter(),
      ],
    );
  }
}

class _AboutInfoCard extends StatelessWidget {
  const _AboutInfoCard();

  @override
  Widget build(BuildContext context) {
    return const Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _AboutRow(label: 'Uygulama', value: 'BYS360 Mobil'),
            _AboutRow(label: 'Kurum', value: 'Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı'),
            _AboutRow(label: 'Yıl', value: '2026'),
            _AboutRow(label: 'Kapsam', value: 'Kurum içi yönetim süreçleri, personel, performans, bildirim, destek, anket ve rehberlik ekranları'),
            _AboutRow(label: 'Hak Bilgisi', value: '© 2026 Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı. Her hakkı saklıdır.'),
          ],
        ),
      ),
    );
  }
}

class _AboutPrinciplesCard extends StatelessWidget {
  const _AboutPrinciplesCard();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(BYS360Radii.xl),
        border: Border.all(color: BYS360Colors.cardBorder),
        boxShadow: BYS360Shadows.card,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: BYS360Colors.softRed,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(Icons.verified_user_outlined, color: BYS360Colors.corporateRed),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Kurumsal kullanım ilkesi',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            'BYS360 Mobil, kullanıcıya yalnızca yetkisi dahilindeki kurumsal süreçleri gösterir. Hassas veri, performans puanı, amir görüşü ve kişisel içerikler ilgili yetki ve yayın kuralları dışında gösterilmez.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: BYS360Colors.mutedText, height: 1.35),
          ),
        ],
      ),
    );
  }
}

class _AboutRow extends StatelessWidget {
  const _AboutRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: BYS360Colors.corporateRed,
                  fontWeight: FontWeight.w900,
                ),
          ),
          const SizedBox(height: 3),
          Text(
            value,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: BYS360Colors.ink,
                  height: 1.30,
                  fontWeight: FontWeight.w600,
                ),
          ),
        ],
      ),
    );
  }
}
