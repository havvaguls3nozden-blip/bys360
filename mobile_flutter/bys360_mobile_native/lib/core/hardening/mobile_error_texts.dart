// BYS360_MOBILE_V2_8_29_ERROR_SCREENS
class MobileErrorTexts {
  const MobileErrorTexts._();

  static const String offlineTitle = 'Bağlantı yok';
  static const String offlineMessage =
      'İnternet bağlantınızı kontrol edin. Bağlantı geldiğinde tekrar deneyebilirsiniz.';

  static const String timeoutTitle = 'İşlem zaman aşımına uğradı';
  static const String timeoutMessage =
      'Sunucudan yanıt alınamadı. Lütfen birkaç saniye sonra tekrar deneyin.';

  static const String authTitle = 'Oturum yenilenemedi';
  static const String authMessage =
      'Güvenliğiniz için tekrar giriş yapmanız gerekiyor.';

  static const String forbiddenTitle = 'Yetkiniz bulunmamaktadır';
  static const String forbiddenMessage =
      'Bu işlem veya ekran için gerekli yetkiniz bulunmamaktadır.';

  static const String genericTitle = 'Bu sayfaya şu anda ulaşılamadı';
  static const String genericMessage =
      'İşlem tamamlanamadı. Lütfen tekrar deneyin.';

  static String fromStatusCode(int? statusCode) {
    if (statusCode == 401) return authMessage;
    if (statusCode == 403) return forbiddenMessage;
    if (statusCode == 408 || statusCode == 504) return timeoutMessage;
    return genericMessage;
  }
}
