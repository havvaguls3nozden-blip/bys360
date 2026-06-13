// BYS360_MOBILE_V2_8_57_TOKEN_STORE_IO
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class BYS360TokenStore {
  BYS360TokenStore();

  static const String _key = 'bys360_token';
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  Future<String?> readToken() => _storage.read(key: _key);
  Future<void> writeToken(String token) => _storage.write(key: _key, value: token);
  Future<void> clearToken() => _storage.delete(key: _key);
}
