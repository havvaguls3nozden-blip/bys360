import 'package:flutter/material.dart';

class ReportsScreen extends StatelessWidget {
  const ReportsScreen({
    super.key,
    required this.apiClient,
  });

  final dynamic apiClient;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Raporlar ve Analizler'),
        centerTitle: false,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _HeaderCard(theme: theme),
          const SizedBox(height: 16),
          _ReportTile(
            icon: Icons.insights_outlined,
            title: 'Yönetici Özeti',
            subtitle: 'Performans, iletişim, anket ve personel göstergelerini tek bakışta izleyin.',
            color: const Color(0xFF1D4ED8),
          ),
          _ReportTile(
            icon: Icons.assignment_turned_in_outlined,
            title: 'Performans Raporları',
            subtitle: 'Dönem, görev, puanlama, düşük skor ve onay süreçleri için özet alan.',
            color: const Color(0xFF0F766E),
          ),
          _ReportTile(
            icon: Icons.groups_2_outlined,
            title: 'Personel ve Birim Görünümü',
            subtitle: 'Personel dağılımı, birim bazlı durum ve görev yoğunluğu raporları.',
            color: const Color(0xFF7C3AED),
          ),
          _ReportTile(
            icon: Icons.campaign_outlined,
            title: 'Portal ve İletişim',
            subtitle: 'Duyuru, iç haber, mesaj, bildirim ve katılım hareketleri.',
            color: const Color(0xFFEA580C),
          ),
          _ReportTile(
            icon: Icons.poll_outlined,
            title: 'Anket ve Geri Bildirim',
            subtitle: 'Anket katılımı, destek talepleri ve geri bildirim özetleri.',
            color: const Color(0xFF15803D),
          ),
          _ReportTile(
            icon: Icons.smart_toy_outlined,
            title: 'AI Karar Destek',
            subtitle: 'Risk, öneri, karar desteği ve aksiyon takip özetleri.',
            color: const Color(0xFFBE123C),
          ),
          const SizedBox(height: 16),
          _InfoBox(theme: theme),
        ],
      ),
    );
  }
}

class _HeaderCard extends StatelessWidget {
  const _HeaderCard({required this.theme});

  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(22),
        gradient: const LinearGradient(
          colors: [
            Color(0xFF0F172A),
            Color(0xFF1D4ED8),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: const [
          BoxShadow(
            blurRadius: 20,
            offset: Offset(0, 10),
            color: Color(0x22000000),
          ),
        ],
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.analytics_outlined, color: Colors.white, size: 34),
          SizedBox(height: 14),
          Text(
            'BYS360 Rapor Merkezi',
            style: TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.w800,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Kurumun performans, portal, iletişim, anket ve karar destek verilerini mobilde sade ve yönetilebilir şekilde sunar.',
            style: TextStyle(
              color: Color(0xFFE0E7FF),
              height: 1.35,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }
}

class _ReportTile extends StatelessWidget {
  const _ReportTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(18),
        side: BorderSide(color: color.withOpacity(0.16)),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        leading: Container(
          width: 46,
          height: 46,
          decoration: BoxDecoration(
            color: color.withOpacity(0.12),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Icon(icon, color: color),
        ),
        title: Text(
          title,
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 5),
          child: Text(
            subtitle,
            style: const TextStyle(height: 1.3),
          ),
        ),
      ),
    );
  }
}

class _InfoBox extends StatelessWidget {
  const _InfoBox({required this.theme});

  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest.withOpacity(0.55),
        borderRadius: BorderRadius.circular(16),
      ),
      child: const Text(
        'Canlı veri bağlantıları aşamalı olarak performans, portal ve anket API uçlarına bağlanacaktır. Bu ekran mobil APK derlemesini tamamlamak ve rapor merkezini kurumsal bir temel yapıya oturtmak için eklenmiştir.',
        style: TextStyle(height: 1.35),
      ),
    );
  }
}
