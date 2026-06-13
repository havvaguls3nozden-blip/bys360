import 'mobile_record.dart';

class ModuleMetric {
  const ModuleMetric({required this.title, required this.value, required this.subtitle, this.tone = 'red', this.icon = 'insights'});

  final String title;
  final String value;
  final String subtitle;
  final String tone;
  final String icon;

  factory ModuleMetric.fromJson(Map<String, dynamic> json) {
    return ModuleMetric(
      title: json['title']?.toString() ?? 'Özet',
      value: json['value']?.toString() ?? '0',
      subtitle: json['subtitle']?.toString() ?? '',
      tone: json['tone']?.toString() ?? 'red',
      icon: json['icon']?.toString() ?? 'insights',
    );
  }
}

class ModuleData {
  const ModuleData({required this.metrics, required this.items, this.source = 'real_api'});

  final List<ModuleMetric> metrics;
  final List<MobileRecord> items;
  final String source;

  factory ModuleData.fromJson(Map<String, dynamic> json) {
    final metricList = json['metrics'] is List ? json['metrics'] as List : const [];
    final itemList = json['items'] is List ? json['items'] as List : const [];
    return ModuleData(
      source: json['source']?.toString() ?? 'real_api',
      metrics: metricList.map((item) => ModuleMetric.fromJson(Map<String, dynamic>.from(item as Map))).toList(),
      items: itemList.map((item) => MobileRecord.fromJson(Map<String, dynamic>.from(item as Map))).toList(),
    );
  }
}
