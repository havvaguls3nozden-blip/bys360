// BYS360_MOBILE_V2_8_72_SECURE_TOKEN_STORE
// Erişim ve yenileme tokenları artık Android Keystore / iOS Keychain üzerinden saklanır.
// Kullanıcı adı, rol, sicil ve birim gibi hassas olmayan oturum özetleri SharedPreferences içinde kalabilir.
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

class TokenStore {
  static const _accessTokenKey = 'bys360_access_token';
  static const _refreshTokenKey = 'bys360_refresh_token';
  static const _displayNameKey = 'bys360_display_name';
  static const _roleKey = 'bys360_role';
  static const _sicilNoKey = 'bys360_sicil_no';
  static const _unitKey = 'bys360_unit';

  static const AndroidOptions _androidOptions = AndroidOptions(
    encryptedSharedPreferences: true,
  );

  static const IOSOptions _iosOptions = IOSOptions(
    accessibility: KeychainAccessibility.first_unlock_this_device,
  );

  static const FlutterSecureStorage _secureStorage = FlutterSecureStorage(
    aOptions: _androidOptions,
    iOptions: _iosOptions,
  );

  Future<String?> get accessToken => _readSensitiveToken(_accessTokenKey);

  Future<String?> get refreshToken => _readSensitiveToken(_refreshTokenKey);

  Future<String?> get displayName async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_displayNameKey);
  }

  Future<String?> get role async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_roleKey);
  }

  Future<String?> get sicilNo async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_sicilNoKey);
  }

  Future<String?> get unit async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_unitKey);
  }

  Future<MobileStoredSession> get storedSession async {
    final prefs = await SharedPreferences.getInstance();
    return MobileStoredSession(
      displayName: prefs.getString(_displayNameKey),
      role: prefs.getString(_roleKey),
      sicilNo: prefs.getString(_sicilNoKey),
      unit: prefs.getString(_unitKey),
    );
  }

  Future<void> saveSession({
    required String accessToken,
    String? refreshToken,
    String? displayName,
    String? role,
    String? sicilNo,
    String? unit,
  }) async {
    final prefs = await SharedPreferences.getInstance();

    await _secureStorage.write(key: _accessTokenKey, value: accessToken);
    if (refreshToken != null && refreshToken.trim().isNotEmpty) {
      await _secureStorage.write(key: _refreshTokenKey, value: refreshToken);
    }

    // Eski sürümden kalmış tokenlar varsa açık alandan temizlenir.
    await prefs.remove(_accessTokenKey);
    await prefs.remove(_refreshTokenKey);

    if (displayName != null) {
      await prefs.setString(_displayNameKey, displayName);
    }
    if (role != null) await prefs.setString(_roleKey, role);
    if (sicilNo != null) await prefs.setString(_sicilNoKey, sicilNo);
    if (unit != null) await prefs.setString(_unitKey, unit);
  }

  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await _secureStorage.delete(key: _accessTokenKey);
    await _secureStorage.delete(key: _refreshTokenKey);
    await prefs.remove(_accessTokenKey);
    await prefs.remove(_refreshTokenKey);
    await prefs.remove(_displayNameKey);
    await prefs.remove(_roleKey);
    await prefs.remove(_sicilNoKey);
    await prefs.remove(_unitKey);
  }

  Future<String?> _readSensitiveToken(String key) async {
    final value = await _secureStorage.read(key: key);
    if (value != null && value.trim().isNotEmpty) return value;

    // V2.8.72 geçiş güvenliği: önceki sürüm SharedPreferences'a yazdıysa
    // ilk okumada güvenli depoya taşınır ve açık kayıt silinir.
    final prefs = await SharedPreferences.getInstance();
    final legacyValue = prefs.getString(key);
    if (legacyValue != null && legacyValue.trim().isNotEmpty) {
      await _secureStorage.write(key: key, value: legacyValue);
      await prefs.remove(key);
      return legacyValue;
    }
    return null;
  }
}

class MobileStoredSession {
  const MobileStoredSession(
      {this.displayName, this.role, this.sicilNo, this.unit});

  final String? displayName;
  final String? role;
  final String? sicilNo;
  final String? unit;

  String get safeDisplayName =>
      displayName == null || displayName!.trim().isEmpty
          ? 'BYS360 Kullanıcısı'
          : displayName!.trim();
  String get safeRole =>
      role == null || role!.trim().isEmpty ? 'Mobil Kullanıcı' : role!.trim();
  String get safeUnit =>
      unit == null || unit!.trim().isEmpty ? 'Birim bilgisi yok' : unit!.trim();
  String get safeSicil =>
      sicilNo == null || sicilNo!.trim().isEmpty ? '-' : sicilNo!.trim();
}
