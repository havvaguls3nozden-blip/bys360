// ignore_for_file: avoid_web_libraries_in_flutter, deprecated_member_use
// BYS360_MOBILE_V2_8_57_TOKEN_STORE_WEB
import 'dart:html' as html;

class BYS360TokenStore {
  BYS360TokenStore();

  static const String _key = 'bys360_token';

  Future<String?> readToken() async => html.window.localStorage[_key];
  Future<void> writeToken(String token) async {
    html.window.localStorage[_key] = token;
  }
  Future<void> clearToken() async {
    html.window.localStorage.remove(_key);
  }
}
