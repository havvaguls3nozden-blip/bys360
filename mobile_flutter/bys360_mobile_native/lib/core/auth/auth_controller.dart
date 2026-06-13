import '../api/mobile_real_api_contract.dart';
import '../config/app_config.dart';
import '../network/api_client.dart';
import '../network/api_exception.dart';
import '../notifications/bys_notification_service.dart';
import 'token_store.dart';

class AuthController {
  AuthController({ApiClient? apiClient, TokenStore? tokenStore})
      : _apiClient = apiClient ?? ApiClient(),
        _tokenStore = tokenStore ?? TokenStore();

  final ApiClient _apiClient;
  final TokenStore _tokenStore;

  Future<void> login(String username, String password) async {
    if (username.trim().isEmpty || password.trim().isEmpty) {
      throw const ApiException('Kullanıcı adı ve şifre zorunludur.');
    }

    final payload = await _apiClient.post(MobileRealApiContract.login, {
      'username': username.trim(),
      'password': password,
    });

    if (payload is! Map<String, dynamic>) {
      throw const ApiException('Giriş yanıtı beklenen formatta değil.');
    }

    final token = (payload['access_token'] ?? payload['token'] ?? payload['accessToken'])?.toString();
    if (token == null || token.isEmpty) {
      throw const ApiException('Mobil oturum anahtarı alınamadı. Lütfen tekrar deneyin.');
    }

    final user = payload['user'] ?? payload['profile'] ?? payload['current_user'];
    await _tokenStore.saveSession(
      accessToken: token,
      refreshToken: payload['refresh_token']?.toString(),
      displayName: user is Map ? (user['full_name'] ?? user['display_name'] ?? user['name'])?.toString() : null,
      role: user is Map ? (user['role'] ?? user['role_name'] ?? user['primary_role'])?.toString() : null,
      sicilNo: user is Map ? (user['sicil_no'] ?? user['registration_no'] ?? user['employee_no'])?.toString() : null,
      unit: user is Map ? (user['unit'] ?? user['unit_name'] ?? user['organization_unit'])?.toString() : null,
    );
    await BYSNotificationService.instance.registerDeviceToken(apiClient: _apiClient);
  }

  Future<void> demoLogin() async {
    if (!AppConfig.demoFallback) {
      throw const ApiException('Demo ön izleme kapalı.');
    }
    await _tokenStore.saveSession(
      accessToken: 'demo-mobile-token',
      displayName: 'BYS360 Kullanıcısı',
      role: 'Mobil Ön İzleme',
      sicilNo: 'demo',
      unit: 'Ön İzleme',
    );
  }

  Future<void> logout() => _tokenStore.clear();
}

// BYS360_MOBILE_V2_8_25_REAL_API_P0 auth gerçek API login sözleşmesi

// BYS360_MOBILE_V2_8_74_ANDROID_RELEASE_READY_P0_AUTH
