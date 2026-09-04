import '../../core/utils/bys360_status_labels.dart';

class MobilePerformanceRecord {
  const MobilePerformanceRecord({
    required this.id,
    required this.title,
    required this.subtitle,
    required this.status,
    required this.value,
    required this.meta,
    required this.progress,
    required this.raw,
  });

  final String id;
  final String title;
  final String subtitle;
  final String status;
  final String value;
  final String meta;
  final double? progress;
  final Map<String, dynamic> raw;

  factory MobilePerformanceRecord.fromJson(Map<String, dynamic> json, {String fallbackTitle = 'Performans kaydı'}) {
    String pick(List<String> keys, [String fallback = '']) {
      for (final key in keys) {
        final value = json[key];
        if (value != null && value.toString().trim().isNotEmpty) return value.toString().trim();
      }
      return fallback;
    }

    double? progressValue;
    final progressSource = json['progress'] ?? json['completion_rate'] ?? json['completionRate'] ?? json['score_rate'] ?? json['scoreRate'];
    if (progressSource is num) progressValue = progressSource.toDouble();
    if (progressSource is String) progressValue = double.tryParse(progressSource.replaceAll('%', '').replaceAll(',', '.'));
    if (progressValue != null && progressValue > 1) progressValue = progressValue / 100;
    if (progressValue != null) progressValue = progressValue.clamp(0, 1).toDouble();

    return MobilePerformanceRecord(
      id: pick(['id', 'assignment_id', 'assignmentId', 'period_id', 'periodId', 'scorecard_id', 'scorecardId', 'uuid'], ''),
      title: pick(['title', 'name', 'period_name', 'periodName', 'employee_name', 'employeeName', 'display_name', 'displayName', 'label'], fallbackTitle),
      subtitle: pick(['subtitle', 'description', 'summary', 'unit', 'unit_name', 'period_label', 'periodLabel'], 'Yetkiniz dahilindeki performans kaydı'),
      status: bys360GenericStatusLabel(pick(['status_label', 'statusLabel', 'state_label', 'stateLabel', 'status', 'state'], 'Takipte')),
      value: pick(['value', 'score', 'final_score', 'finalScore', 'count', 'task_count', 'taskCount'], ''),
      meta: pick(['meta', 'date_range', 'dateRange', 'period', 'role', 'manager_level', 'managerLevel'], ''),
      progress: progressValue,
      raw: json,
    );
  }
}

List<Map<String, dynamic>> bys360ExtractList(dynamic payload) {
  if (payload is List) {
    return payload.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
  }
  if (payload is Map) {
    for (final key in ['items', 'records', 'data', 'results', 'periods', 'tasks', 'scorecards', 'assignments']) {
      final value = payload[key];
      if (value is List) return value.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
    }
  }
  return const [];
}

Map<String, dynamic> bys360ExtractMap(dynamic payload) {
  if (payload is Map) {
    final map = Map<String, dynamic>.from(payload);
    for (final key in ['item', 'record', 'data', 'detail', 'scorecard', 'task', 'period']) {
      final value = map[key];
      if (value is Map) return Map<String, dynamic>.from(value);
    }
    return map;
  }
  return <String, dynamic>{};
}


// bys360PerformanceStatusLabel moved to core/utils/bys360_status_labels.dart
// as bys360GenericStatusLabel(value, {fallback}) -- same dictionary and
// fallback behaviour, now reusable outside the performance module.

String bys360Text(Map<String, dynamic> data, List<String> keys, [String fallback = '']) {
  for (final key in keys) {
    final value = data[key];
    if (value != null && value.toString().trim().isNotEmpty) return value.toString().trim();
  }
  return fallback;
}

// BYS360_MOBILE_V2_8_27_PERFORMANCE_P1 shared model

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION
