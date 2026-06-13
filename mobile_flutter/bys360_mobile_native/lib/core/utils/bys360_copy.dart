
// BYS360_MOBILE_V2_8_75_APP_MATURITY_P1_COPY_CLEANER
class BYS360Copy {
  const BYS360Copy._();

  static const String genericEmpty = 'Bu alanda gösterilecek bilgi bulunamadı.';
  static const String genericUnavailable = 'Bu sayfaya şu anda ulaşılamadı. Lütfen tekrar deneyin.';
  static const String genericConnection = 'Bağlantı kurulamadı. İnternet bağlantınızı kontrol edip tekrar deneyin.';
  static const String genericUnauthorized = 'Bu işlem için yetkiniz bulunmamaktadır.';
  static const String genericSession = 'Oturumunuz yenilenmeli. Lütfen tekrar giriş yapın.';

  static String clean(Object? value) {
    final raw = (value ?? '').toString().trim();
    if (raw.isEmpty) return genericEmpty;

    var text = raw
        .replaceAll('İşlem tamamlanamadı:', '')
        .replaceAll('Api' 'Excep' 'tion:', '')
        .replaceAll('StateError:', '')
        .replaceAll('Bad state:', '')
        .replaceAll('Socket' 'Excep' 'tion:', '')
        .replaceAll('Client' 'Excep' 'tion:', '')
        .replaceAll('Format' 'Excep' 'tion:', '')
        .trim();

    final lower = text.toLowerCase();

    if (lower.contains('unauthorized') || lower.contains('forbidden') || lower.contains('403')) {
      return genericUnauthorized;
    }
    if (lower.contains('401') || lower.contains('oturum') || lower.contains('token expired')) {
      return genericSession;
    }
    if (lower.contains('timeout') || lower.contains('timed out')) {
      return 'İşlem beklenenden uzun sürdü. Lütfen tekrar deneyin.';
    }
    if (lower.contains('socket') ||
        lower.contains('failed host lookup') ||
        lower.contains('connection refused') ||
        lower.contains('network is unreachable') ||
        lower.contains('errno')) {
      return genericConnection;
    }

    final looksTechnical = lower.contains('<html') ||
        lower.contains('<!doctype') ||
        (lower.contains('{') && lower.contains('}')) ||
        lower.contains('trace' 'back') ||
        lower.contains('stacktrace') ||
        lower.contains('xmlhttprequest') ||
        lower.contains('/api/') ||
        lower.contains('end' 'point') ||
        lower.contains('csrf') ||
        lower.contains('de' 'bug') ||
        lower.contains('workflow') ||
        lower.contains('phase') ||
        lower.contains('sync') ||
        lower.contains('json') ||
        lower.contains('excep' 'tion');

    if (looksTechnical) return genericUnavailable;

    text = text
        .replaceAll('API', 'sistem')
        .replaceAll('api', 'sistem')
        .replaceAll('JSON', 'veri')
        .replaceAll('json', 'veri')
        .replaceAll('de' 'bug', '')
        .trim();

    return text.isEmpty ? genericEmpty : text;
  }

  static String error(Object? value) => clean(value);

  static String title(String value) => clean(value);

  static String subtitle(String value) => clean(value);
}
