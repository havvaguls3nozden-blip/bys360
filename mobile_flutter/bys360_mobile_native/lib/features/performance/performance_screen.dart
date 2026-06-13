// BYS360_MOBILE_V2_8_52_PERFORMANCE_WEB_PARITY_MAIN
import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/api_state.dart';
import '../../core/widgets/bys360_logo.dart';
import '../../core/widgets/bys_page.dart';
import '../../core/widgets/metric_card.dart';
import '../../models/module_data.dart';
import 'performance_executive_p1_screen.dart';
import 'performance_feature_list_screen.dart';
import 'performance_history_archive_screen.dart';
import 'performance_manager_tasks_screen.dart';
import 'performance_periods_screen.dart';
import 'performance_process_rules_screen.dart';
import 'performance_period_notes_screen.dart';
import 'performance_note_scorecard_screen.dart';
import 'performance_route_shell.dart';
import 'performance_scorecards_screen.dart';
import 'performance_tasks_screen.dart';

class PerformanceScreen extends StatefulWidget {
  const PerformanceScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<PerformanceScreen> createState() => _PerformanceScreenState();
}

class _PerformanceScreenState extends State<PerformanceScreen> {
  late Future<ModuleData> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<ModuleData> _load() async {
    final payload = await widget.apiClient.get('/api/mobile/performance/full-feature-summary');
    if (payload is! Map) throw StateError('Performans özeti şu anda okunamadı.');
    return ModuleData.fromJson(Map<String, dynamic>.from(payload));
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  void _open(String title, Widget screen) {
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => PerformanceMobileRouteShell(apiClient: widget.apiClient, title: title, child: screen),
    ));
  }

  PerformanceFeatureListScreen _feature({
    required String path,
    required String title,
    required String subtitle,
    required String badge,
    required IconData icon,
    Color tone = BYS360Colors.corporateRed,
    String emptyMessage = 'Bu ekran için gösterilecek kayıt bulunmadı.',
    String? detailPathPrefix,
  }) {
    return PerformanceFeatureListScreen(
      apiClient: widget.apiClient,
      path: path,
      title: title,
      subtitle: subtitle,
      badge: badge,
      icon: icon,
      tone: tone,
      emptyMessage: emptyMessage,
      detailPathPrefix: detailPathPrefix,
    );
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ModuleData>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return const BYSLoadingState(message: 'Performans modülü yükleniyor');
        if (snapshot.hasError) {
          return BYSPage(
            title: 'Performans Yönetimi',
            subtitle: 'Performans özetine şu anda ulaşılamadı.',
            badge: 'Performans',
            onRefresh: _refresh,
            children: [ApiEmptyState(message: 'Performans bilgileri şu anda alınamadı. Lütfen tekrar deneyin.', onRetry: () => setState(() => _future = _load()))],
          );
        }

        final data = snapshot.data ?? const ModuleData(metrics: [], items: []);
        return BYSPage(
          title: 'Performans Yönetimi',
          subtitle: 'Performans süreçleri, görevler, karneler ve onay başlıkları mobilde tek yerden izlenir.',
          badge: 'Performans',
          onRefresh: _refresh,
          trailing: Container(
            width: 76,
            height: 66,
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
            child: const BYS360Logo(),
          ),
          children: [
            const BYSSectionTitle(title: 'Canlı performans özeti', subtitle: 'BYS360 verileriyle güncellenir'),
            if (data.metrics.isEmpty)
              const BYSInfoPanel(icon: Icons.info_outline, title: 'Özet bekleniyor', body: 'Performans özeti için sistemde kayıt oluştuğunda bu alan otomatik güncellenir.')
            else
              ...data.metrics.map((metric) => MetricCard(title: metric.title, value: metric.value, subtitle: metric.subtitle, icon: _icon(metric.icon), tone: _tone(metric.tone))),
            const BYSInfoPanel(
              icon: Icons.dashboard_customize_outlined,
              title: 'Tam kapsamlı mobil performans alanı',
              body: 'Dönem, kapsam, kategori, puanlama, karne, Başkan/Üst Onay, yayın ön onayı, rapor, arşiv, dönem içi not, gelişim önerisi, hatırlatma ve yönetici görünürlüğü tek ekranda toplanmıştır.',
            ),

            const BYSSectionTitle(title: 'Temel değerlendirme akışı', subtitle: 'Dönem, görev, puanlama ve karne'),
            ActionTile(
              title: 'Dönem Yönetimi',
              subtitle: 'Açık, geçmiş, birim/kategori/seçili personel kapsamlı dönemler',
              icon: Icons.timeline_outlined,
              tone: BYS360Colors.info,
              onTap: () => _open('Performans Dönemleri', PerformancePeriodsScreen(apiClient: widget.apiClient)),
            ),
            ActionTile(
              title: 'Değerlendirme Görevlerim',
              subtitle: 'Puan ver, taslak kaydet, tamamla, geri çek veya iade et',
              icon: Icons.assignment_ind_outlined,
              tone: BYS360Colors.corporateRed,
              onTap: () => _open('Değerlendirme Görevlerim', PerformanceTasksScreen(apiClient: widget.apiClient)),
            ),
            ActionTile(
              title: 'Performans Karneleri',
              subtitle: 'Yayınlanmış ve yetki kapsamınızda açılmış karneler',
              icon: Icons.assignment_turned_in_outlined,
              tone: BYS360Colors.success,
              onTap: () => _open('Performans Karneleri', PerformanceScorecardsScreen(apiClient: widget.apiClient)),
            ),

            const BYSSectionTitle(title: 'Kural, kriter ve ayarlar', subtitle: 'Kurumsal performans yönetim başlıkları'),
            ActionTile(
              title: 'Değerlendirme Kriterleri',
              subtitle: 'Aktif kriterler, açıklamalar ve ağırlık bilgileri',
              icon: Icons.rule_folder_outlined,
              tone: BYS360Colors.purple,
              onTap: () => _open('Değerlendirme Kriterleri', _feature(path: '/api/mobile/performance/criteria', title: 'Değerlendirme Kriterleri', subtitle: 'Değerlendirme kriterleri mobilde görüntülenir.', badge: 'Kriterler', icon: Icons.rule_folder_outlined, tone: BYS360Colors.purple)),
            ),
            ActionTile(
              title: 'Ağırlık Ayarları',
              subtitle: '1. amir, 2. amir ve varsa 3. amir ağırlıkları',
              icon: Icons.scale_outlined,
              tone: BYS360Colors.warning,
              onTap: () => _open('Ağırlık Ayarları', _feature(path: '/api/mobile/performance/weights', title: 'Ağırlık Ayarları', subtitle: 'Ağırlık toplamı ve 3. amir etkisi mobilde izlenir.', badge: 'Ağırlık', icon: Icons.scale_outlined, tone: BYS360Colors.warning)),
            ),
            ActionTile(
              title: '3. Amir Yapısı',
              subtitle: 'Yorum modu, puan modu ve sahte görev kontrolü',
              icon: Icons.account_tree_outlined,
              tone: BYS360Colors.info,
              onTap: () => _open('3. Amir Yapısı', _feature(path: '/api/mobile/performance/third-manager', title: '3. Amir Yapısı', subtitle: '3. amir opsiyonelliği ve mod bilgileri gösterilir.', badge: '3. Amir', icon: Icons.account_tree_outlined, tone: BYS360Colors.info)),
            ),
            ActionTile(
              title: 'Performans Kuralları',
              subtitle: 'Kör değerlendirme yok, 70 altı onay ve yayın sınırları',
              icon: Icons.policy_outlined,
              tone: BYS360Colors.corporateRed,
              onTap: () => _open('Performans Kuralları', const PerformanceProcessRulesScreen()),
            ),

            const BYSSectionTitle(title: 'Kapsam ve personel grupları', subtitle: 'Kategori, grup ve özel dönem görünürlüğü'),
            ActionTile(
              title: 'Personel Grup/Kategori',
              subtitle: 'Güvenlik, Temizlik, İdari, Teknik, Deneme Süreli ve Diğer',
              icon: Icons.groups_outlined,
              tone: BYS360Colors.info,
              onTap: () => _open('Personel Grup/Kategori', _feature(path: '/api/mobile/performance/categories', title: 'Personel Grup/Kategori', subtitle: 'Kategori bazlı performans kapsamı ve kişi detaysız özetler.', badge: 'Kategori', icon: Icons.groups_outlined, tone: BYS360Colors.info)),
            ),

            const BYSSectionTitle(title: 'Onay, yayın ve yönetici görünürlüğü', subtitle: 'Başkan/Üst Onay, yayın ön onayı ve ekip takibi'),
            ActionTile(
              title: 'Başkan/Üst Onayları',
              subtitle: '70 altı sonuçlar ve yayın kilidi kayıtları',
              icon: Icons.verified_user_outlined,
              tone: BYS360Colors.warning,
              onTap: () => _open('Başkan/Üst Onayları', _feature(path: '/api/mobile/performance/president-approvals', title: 'Başkan/Üst Onayları', subtitle: 'Düşük performans onayları ve karne inceleme kayıtları.', badge: 'Üst Onay', icon: Icons.verified_user_outlined, tone: BYS360Colors.warning)),
            ),
            ActionTile(
              title: 'Yayın Ön Onayı',
              subtitle: 'Personel ve Destek Hizmetleri Grup Başkanı final kontrolü',
              icon: Icons.approval_outlined,
              tone: BYS360Colors.corporateRed,
              onTap: () => _open('Yayın Ön Onayı', _feature(path: '/api/mobile/performance/publish-preapproval', title: 'Yayın Ön Onayı', subtitle: 'Final yayın öncesi kontrol ve yayın kilidi durumu.', badge: 'Yayın Ön Onayı', icon: Icons.approval_outlined, tone: BYS360Colors.corporateRed)),
            ),
            ActionTile(
              title: 'Yönetici Görünümü',
              subtitle: 'Ekip, dönem, görev ve karne özetleri',
              icon: Icons.dashboard_customize_outlined,
              tone: BYS360Colors.info,
              onTap: () => _open('Performans Yönetici Alanı', PerformanceExecutiveP1Screen(apiClient: widget.apiClient)),
            ),
            ActionTile(
              title: 'Amir Görev Takibi',
              subtitle: 'Bekleyen, geciken ve tamamlanan amir görevleri',
              icon: Icons.manage_accounts_outlined,
              tone: BYS360Colors.warning,
              onTap: () => _open('Amir Görev Takibi', PerformanceManagerTasksScreen(apiClient: widget.apiClient)),
            ),
            ActionTile(
              title: 'Riskli Personel Analizi',
              subtitle: 'Düşük performans, gecikme ve tekrar eden riskler',
              icon: Icons.warning_amber_rounded,
              tone: BYS360Colors.danger,
              onTap: () => _open('Riskli Personel Analizi', _feature(path: '/api/mobile/performance/risk-analysis', title: 'Riskli Personel Analizi', subtitle: 'Yetki kapsamındaki düşük performans ve gecikme göstergeleri.', badge: 'Risk', icon: Icons.warning_amber_rounded, tone: BYS360Colors.danger)),
            ),

            const BYSSectionTitle(title: 'Arşiv, gelişim ve takip', subtitle: 'Geçmiş kayıt, dönem içi not, gelişim önerisi ve hatırlatma'),
            ActionTile(
              title: 'Geçmiş Karne Arşivi',
              subtitle: 'Yayınlanmış geçmiş karneler ve eski dönem puanları',
              icon: Icons.archive_outlined,
              tone: BYS360Colors.purple,
              onTap: () => _open('Geçmiş Karne Arşivi', PerformanceHistoryArchiveScreen(apiClient: widget.apiClient)),
            ),
            ActionTile(
              title: 'Dönem İçi Notlar',
              subtitle: 'Olumlu/olumsuz olay, başarı, gelişim ihtiyacı ve gözlem notları',
              icon: Icons.edit_note_outlined,
              tone: BYS360Colors.info,
              onTap: () => _open('Dönem İçi Notlar', PerformancePeriodNotesScreen(apiClient: widget.apiClient)),
            ),
            ActionTile(
              title: 'Not Karnesi',
              subtitle: 'Karne detayına açılan dönem içi notlar ve gelişim kayıtları',
              icon: Icons.sticky_note_2_outlined,
              tone: BYS360Colors.warning,
              onTap: () => _open('Not Karnesi', PerformanceNoteScorecardScreen(apiClient: widget.apiClient)),
            ),
            ActionTile(
              title: 'Gelişim Önerileri',
              subtitle: 'Düşük performans veya gelişim alanları için rehber notlar',
              icon: Icons.school_outlined,
              tone: BYS360Colors.success,
              onTap: () => _open('Gelişim Önerileri', _feature(path: '/api/mobile/performance/development-suggestions', title: 'Gelişim Önerileri', subtitle: 'Güçlü yön, gelişim alanı ve takip önerisi kayıtları.', badge: 'Gelişim', icon: Icons.school_outlined, tone: BYS360Colors.success)),
            ),
            ActionTile(
              title: 'Raporlar ve Analizler',
              subtitle: 'Birim, kategori, dönem, amir, personel ve risk bazlı raporlar',
              icon: Icons.bar_chart_outlined,
              tone: BYS360Colors.corporateRed,
              onTap: () => _open('Raporlar ve Analizler', _feature(path: '/api/mobile/performance/reports', title: 'Raporlar ve Analizler', subtitle: 'Performans raporlarının mobil özet görünümü.', badge: 'Rapor', icon: Icons.bar_chart_outlined, tone: BYS360Colors.corporateRed)),
            ),
            ActionTile(
              title: 'Hatırlatma ve Aksatan Amir',
              subtitle: 'Bekleyen görev, yaklaşan son tarih ve aksatan amir takibi',
              icon: Icons.notifications_active_outlined,
              tone: BYS360Colors.warning,
              onTap: () => _open('Hatırlatma ve Aksatan Amir', _feature(path: '/api/mobile/performance/reminders', title: 'Hatırlatma ve Aksatan Amir', subtitle: 'Bekleyen görevler, gecikenler ve hatırlatma kayıtları.', badge: 'Hatırlatma', icon: Icons.notifications_active_outlined, tone: BYS360Colors.warning)),
            ),
            const BYSInfoPanel(
              icon: Icons.lock_outline,
              title: 'Güvenli performans görünümü',
              body: 'Mobil performans modülü yetki, görünürlük, yayın, onay ve hassas veri kurallarını aşmaz. Veri yalnızca rol kapsamına göre gösterilir.',
            ),
          ],
        );
      },
    );
  }
}

Color _tone(String tone) {
  switch (tone.toLowerCase()) {
    case 'green':
    case 'success':
      return BYS360Colors.success;
    case 'yellow':
    case 'warning':
      return BYS360Colors.warning;
    case 'blue':
    case 'info':
      return BYS360Colors.info;
    case 'purple':
      return BYS360Colors.purple;
    case 'danger':
    case 'red-danger':
      return BYS360Colors.danger;
    default:
      return BYS360Colors.corporateRed;
  }
}

IconData _icon(String icon) {
  switch (icon.toLowerCase()) {
    case 'timeline':
      return Icons.timeline_outlined;
    case 'assignment':
      return Icons.assignment_ind_outlined;
    case 'scorecard':
      return Icons.assignment_turned_in_outlined;
    case 'verified_user':
      return Icons.verified_user_outlined;
    case 'warning':
      return Icons.warning_amber_rounded;
    case 'rule':
      return Icons.rule_folder_outlined;
    case 'scale':
      return Icons.scale_outlined;
    case 'people':
      return Icons.groups_outlined;
    case 'archive':
      return Icons.archive_outlined;
    case 'note':
      return Icons.edit_note_outlined;
    case 'development':
      return Icons.school_outlined;
    case 'report':
      return Icons.bar_chart_outlined;
    case 'reminder':
      return Icons.notifications_active_outlined;
    case 'approval':
      return Icons.approval_outlined;
    default:
      return Icons.insights_outlined;
  }
}

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION

// BYS360_MOBILE_V2_8_63A_ARCHIVE_NOTE_SCORECARD
