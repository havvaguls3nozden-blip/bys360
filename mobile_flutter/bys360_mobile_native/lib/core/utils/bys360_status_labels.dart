// BYS360_MOBILE_H1E_GENERIC_STATUS_LABEL
// Shared closed-vocabulary status/type label dictionary. Moved here from
// features/performance/performance_mobile_p1_models.dart's
// bys360PerformanceStatusLabel() so every module (not just performance) can
// reuse the same safe, tested mapping instead of leaving raw backend status
// codes (e.g. "in_progress", "hr_precheck") on screen untranslated.
const Map<String, String> _bys360StatusLabels = <String, String>{
  'pending': 'Bekliyor',
  'waiting': 'Bekliyor',
  'assigned': 'Atandı',
  'open': 'Açık',
  'draft': 'Taslak',
  'in_progress': 'Devam Ediyor',
  'ongoing': 'Devam Ediyor',
  'devam': 'Devam Ediyor',
  'devam_ediyor': 'Devam Ediyor',
  'completed': 'Tamamlandı',
  'done': 'Tamamlandı',
  'tamamlandi': 'Tamamlandı',
  'tamamlandı': 'Tamamlandı',
  'returned': 'İade Edildi',
  'rejected': 'İade Edildi',
  'withdrawn': 'Geri Çekildi',
  'president_pending': 'Başkan Onayı Bekliyor',
  'blocked_president_pending': 'Başkan Onayı Yayın Kilidi',
  'hr_precheck': 'İK/Admin Ön Kontrolünde',
  'first_low_warning': 'Düşük Performans Uyarısı Oluşturuldu',
  'second_low_repeat': 'Tekrarlayan Düşük Performans Süreci',
  'approved_by_president': 'Başkan Tarafından Onaylandı',
  'rejected_by_president': 'Başkan Tarafından İade Edildi',
  'scorecard_pending': 'Karne Yayın Bekliyor',
  'published': 'Yayınlandı',
  'locked': 'Yayın Kilidi',
  'closed': 'Kapalı',
  'resolved': 'Çözüldü',
  'waiting_info': 'Bilgi Bekleniyor',
  'planned': 'Planlandı',
};

/// Safe, closed-vocabulary status/type label lookup shared across the whole
/// app. Never echoes a raw, untranslated machine value: an unmapped code is
/// at least title-cased, and a genuinely empty value returns [fallback]
/// (never null, never blank).
///
/// A value that already contains a space is assumed to be free text a
/// caller composed itself (a module name, a count label, an already
/// human-written phrase) rather than a raw machine slug, and is returned
/// unchanged -- title-casing it via the underscore/dash splitter below
/// would otherwise flatten intentional internal capitalization (e.g.
/// "İnsan Kaynakları" -> "İnsan kaynakları").
String bys360GenericStatusLabel(String? value, {String fallback = 'Bilinmiyor'}) {
  final raw = (value ?? '').trim();
  if (raw.isEmpty) return fallback;

  final key = raw.toLowerCase().replaceAll(' ', '_').replaceAll('-', '_');
  if (_bys360StatusLabels.containsKey(key)) return _bys360StatusLabels[key]!;

  if (raw.contains(' ')) return raw;

  return raw.split(RegExp(r'[_\-]+')).where((part) => part.isNotEmpty).map((part) {
    if (part.length == 1) return part.toUpperCase();
    return part[0].toUpperCase() + part.substring(1).toLowerCase();
  }).join(' ');
}

/// Turkish label for a boolean "is active" flag, accepting the raw value
/// straight from JSON -- a real bool, or a stringified "true"/"false"/
/// "1"/"0". Returns null if [value] isn't recognizable as a boolean at
/// all, so callers can fall through to another field instead of showing
/// the raw literal (e.g. the English word "true") to the user.
String? bys360ActiveFlagLabel(dynamic value) {
  if (value is bool) return value ? 'Aktif' : 'Pasif';
  if (value == null) return null;
  final normalized = value.toString().trim().toLowerCase();
  if (normalized == 'true' || normalized == '1') return 'Aktif';
  if (normalized == 'false' || normalized == '0') return 'Pasif';
  return null;
}
