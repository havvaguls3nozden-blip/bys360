class MobileRecord {
  MobileRecord({
    required this.id,
    required this.title,
    this.subtitle,
    this.status,
    this.value,
    this.meta,
    this.progress,
    this.icon,
    this.tone,
  });

  final String id;
  final String title;
  final String? subtitle;
  final String? status;
  final String? value;
  final String? meta;
  final int? progress;
  final String? icon;
  final String? tone;

  factory MobileRecord.fromJson(Map<String, dynamic> json) {
    return MobileRecord(
      id: json['id']?.toString() ?? '',
      title: (json['title'] ?? json['full_name'] ?? json['name'] ?? json['subject'] ?? 'Kayıt').toString(),
      subtitle: (json['subtitle'] ?? json['unit'] ?? json['body'] ?? json['description'] ?? json['message'])?.toString(),
      status: (json['status'] ?? json['state'] ?? json['status_text'])?.toString(),
      value: (json['value'] ?? json['score'] ?? json['count'])?.toString(),
      meta: (json['meta'] ?? json['date'] ?? json['role'] ?? json['category'])?.toString(),
      progress: _asIntOrNull(json['progress']),
      icon: (json['icon'] ?? json['icon_name'] ?? json['type'])?.toString(),
      tone: (json['tone'] ?? json['color'] ?? json['severity'])?.toString(),
    );
  }

  static int? _asIntOrNull(dynamic value) {
    if (value is int) return value;
    if (value is num) return value.toInt();
    return int.tryParse(value?.toString() ?? '');
  }
}
