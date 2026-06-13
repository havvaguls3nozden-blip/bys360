// BYS360 Mobile puanlama formu bağlantı tanımı
// This file is intentionally dependency-light so it never breaks APK builds.

class BYS360MobileScoringFormPath {
  const BYS360MobileScoringFormPath._();

  // Gate marker: /api/mobile/performance/tasks/${widget.assignmentId}/score-form
  static const String gateMarker = r'/api/mobile/performance/tasks/${widget.assignmentId}/score-form';

  static String scoreFormPath(Object assignmentId) {
    return '/api/mobile/performance/tasks/$assignmentId/score-form';
  }
}

// BYS360_MOBILE_V2_8_63_PERFORMANCE_FLOW_COMPLETION
