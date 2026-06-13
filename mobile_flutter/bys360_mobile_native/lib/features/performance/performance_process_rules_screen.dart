// BYS360_MOBILE_V2_8_52_PERFORMANCE_RULES_NATIVE
import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import '../../core/widgets/bys_page.dart';

class PerformanceProcessRulesScreen extends StatelessWidget {
  const PerformanceProcessRulesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const BYSPage(
      title: 'Performans Kuralları',
      subtitle: 'Mobil uygulama performans modülündeki ana iş kurallarını aynı şekilde uygular.',
      badge: 'Performans',
      trailing: Icon(Icons.policy_outlined, color: BYS360Colors.corporateRed, size: 48),
      children: [
        BYSSectionTitle(title: 'Sabit kurallar', subtitle: 'BYS360 ve mobil aynı kurumsal mantıkta çalışır'),
        _RuleCard(
          icon: Icons.visibility_outlined,
          title: 'Kör değerlendirme yoktur',
          body: 'Sonraki amir, önceki amirin puanını ve kanaatini görebilir. 1. amir, 2. amirin verdiği puanı mobilde de görür.',
        ),
        _RuleCard(
          icon: Icons.fact_check_outlined,
          title: 'Puanlama 1–5 ölçeğiyle yapılır',
          body: 'Kriter bazlı puanlar 100’lük sisteme dönüştürülür. Hepsine 5, 4, 3, 2 veya 1 verme kolaylığı mobilde korunur.',
        ),
        _RuleCard(
          icon: Icons.comment_outlined,
          title: '1 ve 5 puanda kriter yorumu zorunlu değildir',
          body: 'Mobilde kriter açıklaması isteğe bağlıdır. 70 altı veya 90 üstü sonuçlarda genel görüş kuralı ayrıca korunur.',
        ),
        _RuleCard(
          icon: Icons.verified_user_outlined,
          title: '70 altı sonuç doğrudan yayınlanmaz',
          body: 'Düşük performans sonucu Başkan/Üst Onay ve süreç zinciri tamamlanmadan personele kesin sonuç olarak açılmaz.',
        ),
        _RuleCard(
          icon: Icons.approval_outlined,
          title: 'Yayın ön onayı korunur',
          body: 'Gerekli onaylar tamamlandıktan sonra Personel ve Destek Hizmetleri Grup Başkanı yayın ön onayı ve final yayın akışı izlenir.',
        ),
        _RuleCard(
          icon: Icons.account_tree_outlined,
          title: '3. amir opsiyoneldir',
          body: '3. amir olmayan personelde boş görev veya sahte bekleme oluşmaz. Yorum modu ve puan modu sistem ayarına bağlıdır.',
        ),
        _RuleCard(
          icon: Icons.lock_outline,
          title: 'Yetki ve karne görünürlüğü ayrıdır',
          body: 'Personel yalnızca yayınlanan kendi karnesini görür. Yönetici, koordinatör, grup başkanı ve Başkan görünürlüğü rol matrisiyle sınırlıdır.',
        ),
      ],
    );
  }
}

class _RuleCard extends StatelessWidget {
  const _RuleCard({required this.icon, required this.title, required this.body});

  final IconData icon;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(color: BYS360Colors.softRed, borderRadius: BorderRadius.circular(15)),
              child: Icon(icon, color: BYS360Colors.corporateRed),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900)),
                  const SizedBox(height: 4),
                  Text(body, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText, height: 1.32)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION
