import 'package:flutter/material.dart';

import '../../models/module_data.dart';
import '../config/app_config.dart';
import '../network/api_client.dart';
import '../theme/app_theme.dart';
import 'api_state.dart';
import 'bys360_logo.dart';
import 'bys_page.dart';
import 'metric_card.dart';
import 'mobile_feature_scope.dart';
import 'record_widgets.dart';

class ModuleApiScreen extends StatefulWidget {
  const ModuleApiScreen({
    super.key,
    required this.apiClient,
    required this.path,
    required this.title,
    required this.subtitle,
    required this.badge,
    required this.icon,
    this.features = const <MobileFeatureScope>[],
    this.tone = BYS360Colors.corporateRed,
  });

  final ApiClient apiClient;
  final String path;
  final String title;
  final String subtitle;
  final String badge;
  final IconData icon;
  final List<MobileFeatureScope> features;
  final Color tone;

  @override
  State<ModuleApiScreen> createState() => _ModuleApiScreenState();
}

class _ModuleApiScreenState extends State<ModuleApiScreen> {
  late Future<ModuleData> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<ModuleData> _load() async {
    final payload = await widget.apiClient.get(widget.path);
    if (payload is! Map) throw StateError('Sayfa bilgileri şu anda alınamadı.');
    final data = ModuleData.fromJson(Map<String, dynamic>.from(payload));
    if (!AppConfig.demoFallback && data.source == 'mock') throw StateError('Bu sayfa gerçek veriyle çalışmalıdır.');
    return data;
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ModuleData>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return const BYSLoadingState();
        if (snapshot.hasError) {
          return BYSPage(
            title: widget.title,
            subtitle: 'Sayfa bilgileri şu anda alınamadı.',
            badge: widget.badge,
            onRefresh: _refresh,
            children: [
              ApiEmptyState(message: 'Bağlantı veya yetki bilgisi nedeniyle sayfa yüklenemedi. Lütfen tekrar deneyin.', onRetry: () => setState(() => _future = _load())),
            ],
          );
        }

        final data = snapshot.data ?? const ModuleData(metrics: [], items: []);
        return BYSPage(
          title: widget.title,
          subtitle: widget.subtitle,
          badge: widget.badge,
          onRefresh: _refresh,
          trailing: Container(
            width: 76,
            height: 66,
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
            child: const BYS360Logo(),
          ),
          children: [
            const BYSSectionTitle(title: 'Özet', subtitle: 'Yetkiniz kapsamındaki güncel durum'),
            if (data.metrics.isEmpty)
              BYSInfoPanel(icon: widget.icon, title: 'Özet bulunamadı', body: 'Bu sayfa için görüntülenecek özet bulunamadı.', tint: widget.tone)
            else
              ...data.metrics.map((metric) => MetricCard(
                    title: metric.title,
                    value: metric.value,
                    subtitle: metric.subtitle,
                    icon: _metricIcon(metric.icon, fallback: widget.icon),
                    tone: _metricTone(metric.tone, fallback: widget.tone),
                  )),
            if (data.items.isNotEmpty) ...[
              const BYSSectionTitle(title: 'Kayıtlar', subtitle: 'Görüntüleme yetkiniz olan kayıtlar'),
              ...data.items.map((record) => RecordCard(record: record, icon: _recordIcon(record.icon, fallback: widget.icon), tone: _recordTone(record.tone, fallback: widget.tone))),
            ] else if (widget.features.isNotEmpty) ...[
              const BYSSectionTitle(title: 'İşlem Alanları', subtitle: 'Bu modülde kullanabileceğiniz başlıklar'),
              MobileFeatureScopeCard(features: widget.features, tone: widget.tone),
            ] else ...[
              const BYSSectionTitle(title: 'Kayıtlar', subtitle: 'Görüntüleme yetkiniz olan kayıtlar'),
              const ApiEmptyState(title: 'Kayıt bulunamadı', message: 'Bu modül için yetkiniz kapsamında görüntülenecek kayıt bulunamadı.'),
            ],
          ],
        );
      },
    );
  }

  Color _metricTone(String tone, {required Color fallback}) => _tone(tone, fallback: fallback);
  Color _recordTone(String? tone, {required Color fallback}) => _tone(tone ?? '', fallback: fallback);

  Color _tone(String tone, {required Color fallback}) {
    switch (tone.toLowerCase()) {
      case 'green':
      case 'success':
        return BYS360Colors.success;
      case 'blue':
      case 'info':
        return BYS360Colors.info;
      case 'yellow':
      case 'warning':
      case 'gold':
        return BYS360Colors.warning;
      case 'purple':
        return BYS360Colors.purple;
      case 'red':
      case 'danger':
        return BYS360Colors.corporateRed;
      default:
        return fallback;
    }
  }

  IconData _metricIcon(String icon, {required IconData fallback}) => _icon(icon, fallback: fallback);
  IconData _recordIcon(String? icon, {required IconData fallback}) => _icon(icon ?? '', fallback: fallback);

  IconData _icon(String icon, {required IconData fallback}) {
    switch (icon.toLowerCase()) {
      case 'assignment':
      case 'task':
        return Icons.assignment_outlined;
      case 'calendar':
      case 'period':
        return Icons.calendar_month_outlined;
      case 'approval':
      case 'shield':
        return Icons.verified_user_outlined;
      case 'score':
      case 'chart':
      case 'insights':
        return Icons.trending_up_outlined;
      case 'warning':
        return Icons.warning_amber_rounded;
      case 'lock':
        return Icons.lock_outline;
      case 'rule':
        return Icons.rule_folder_outlined;
      case 'scale':
        return Icons.scale_outlined;
      case 'people':
      case 'person':
        return Icons.people_alt_outlined;
      case 'settings':
        return Icons.settings_outlined;
      case 'survey':
        return Icons.poll_outlined;
      case 'support':
        return Icons.support_agent_outlined;
      default:
        return fallback;
    }
  }
}

// BYS360_MOBILE_V2_8_25_REAL_API_P0 modül ekranları gerçek API sözleşmesi
