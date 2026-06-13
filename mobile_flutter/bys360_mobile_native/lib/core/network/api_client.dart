// BYS360_MOBILE_V2_8_72_REFRESH_TOKEN_CLIENT
// 401 yanıtında, refresh token varsa oturumu sessiz yeniler; yoksa kullanıcı güvenli şekilde giriş ekranına alınır.
import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../api/mobile_real_api_contract.dart';
import '../auth/session_state.dart';
import '../auth/token_store.dart';
import '../config/app_config.dart';
import '../utils/bys360_copy.dart';
import 'api_exception.dart';

class ApiClient {
  ApiClient({TokenStore? tokenStore, http.Client? httpClient})
      : _tokenStore = tokenStore ?? TokenStore(),
        _httpClient = httpClient ?? http.Client();

  final TokenStore _tokenStore;
  final http.Client _httpClient;

  static const String _bys360MobileCsrfFriendlyMessage =
      'Güvenlik doğrulaması yenilendi. Lütfen tekrar giriş yapın.';

  Future<Map<String, String>> _headers({bool includeAuth = true}) async {
    final token = includeAuth ? await _tokenStore.accessToken : null;
    return {
      'Accept': 'application/json',
      'Content-Type': 'application/json; charset=utf-8',
      'X-Requested-With': 'XMLHttpRequest',
      if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
    };
  }

  Future<dynamic> get(String path) async {
    return _send('GET', path);
  }

  Future<dynamic> post(String path, Map<String, dynamic> body) async {
    return _send('POST', path, body: body);
  }

  Future<dynamic> _send(
    String method,
    String path, {
    Map<String, dynamic>? body,
    bool allowRefresh = true,
  }) async {
    try {
      final uri = AppConfig.uri(path);
      final headers = await _headers();
      final response = method == 'POST'
          ? await _httpClient
              .post(uri,
                  headers: headers,
                  body: jsonEncode(body ?? <String, dynamic>{}))
              .timeout(const Duration(seconds: 22))
          : await _httpClient
              .get(uri, headers: headers)
              .timeout(const Duration(seconds: 22));
      return _decode(
        response,
        path: path,
        allowRefresh: allowRefresh,
        retryAfterRefresh: () =>
            _send(method, path, body: body, allowRefresh: false),
      );
    } on ApiException {
      rethrow;
    } catch (error) {
      throw ApiException(_connectionMessage(error));
    }
  }

  Future<dynamic> _decode(
    http.Response response, {
    required String path,
    required bool allowRefresh,
    required Future<dynamic> Function() retryAfterRefresh,
  }) async {
    final text = utf8.decode(response.bodyBytes);
    final trimmed = text.trimLeft();
    dynamic payload;

    final lowerText = trimmed.toLowerCase();
    final csrfRefreshRequired = lowerText.contains('csrf token is missing') ||
        (lowerText.contains('csrf') && lowerText.contains('token'));
    final looksLikeHtml = trimmed.startsWith('<!DOCTYPE') ||
        trimmed.startsWith('<html') ||
        trimmed.contains('<title>');
    if (csrfRefreshRequired) {
      await _tokenStore.clear();
      SessionState.notifyExpired();
      throw const ApiException(_bys360MobileCsrfFriendlyMessage, statusCode: 400);
    }
    if (trimmed.isNotEmpty && !looksLikeHtml) {
      try {
        payload = jsonDecode(text);
      } catch (_) {
        payload = {'message': text};
      }
    }

    if (response.statusCode == 401) {
      final canRefresh = allowRefresh &&
          path != MobileRealApiContract.login &&
          path != MobileRealApiContract.refresh;
      if (canRefresh && await _refreshAccessToken()) {
        return retryAfterRefresh();
      }

      await _tokenStore.clear();
      SessionState.notifyExpired();
      final message = payload is Map && payload['message'] != null
          ? BYS360Copy.clean(payload['message'])
          : 'Oturumunuz yenilenmeli. Lütfen tekrar giriş yapın.';
      throw ApiException(message, statusCode: response.statusCode);
    }

    if (response.statusCode == 403) {
      throw const ApiException('Bu işlem için yetkiniz bulunmamaktadır.',
          statusCode: 403);
    }

    if (response.statusCode < 200 || response.statusCode >= 300) {
      String message;
      if (payload is Map && payload['message'] != null) {
        message = BYS360Copy.clean(payload['message']);
      } else if (looksLikeHtml) {
        message = 'Bu sayfaya şu anda ulaşılamadı. Lütfen tekrar deneyin.';
      } else {
        message = 'İşlem tamamlanamadı. Lütfen tekrar deneyin.';
      }
      throw ApiException(message, statusCode: response.statusCode);
    }

    return payload ?? <String, dynamic>{};
  }

  Future<bool> _refreshAccessToken() async {
    final refreshToken = await _tokenStore.refreshToken;
    if (refreshToken == null || refreshToken.trim().isEmpty) return false;

    try {
      final response = await _httpClient
          .post(
            AppConfig.uri(MobileRealApiContract.refresh),
            headers: await _headers(includeAuth: false),
            body: jsonEncode({'refresh_token': refreshToken}),
          )
          .timeout(const Duration(seconds: 15));

      if (response.statusCode < 200 || response.statusCode >= 300) return false;
      final payload = jsonDecode(utf8.decode(response.bodyBytes));
      if (payload is! Map<String, dynamic>) return false;

      final accessToken = (payload['access_token'] ??
              payload['token'] ??
              payload['accessToken'])
          ?.toString();
      if (accessToken == null || accessToken.trim().isEmpty) return false;

      await _tokenStore.saveSession(
        accessToken: accessToken,
        refreshToken: (payload['refresh_token'] ??
                payload['refreshToken'] ??
                refreshToken)
            .toString(),
      );
      return true;
    } catch (_) {
      return false;
    }
  }

  String _connectionMessage(Object error) {
    if (error is TimeoutException) {
      return 'İşlem beklenenden uzun sürdü. Lütfen tekrar deneyin.';
    }
    final text = error.toString().toLowerCase();
    if (text.contains('socket') ||
        text.contains('connection') ||
        text.contains('host') ||
        text.contains('network')) {
      return 'BYS360 sunucusuna şu anda ulaşılamadı. Telefonunuzun internete bağlı olduğundan ve BYS360 adresinin erişilebilir olduğundan emin olun.';
    }
    return BYS360Copy.error(error);
  }
}
