// BYS360_MOBILE_V2_8_34_RELEASE_GETJSON_FIX
// BYS360_MOBILE_API_BASE_CONSISTENCY_V2_17_64
import 'dart:convert';
import 'dart:io';

class MobileApiResponse {
  const MobileApiResponse({
    required this.statusCode,
    required this.data,
    this.errorMessage,
  });

  final int statusCode;
  final Map<String, dynamic> data;
  final String? errorMessage;

  bool get isSuccess => statusCode >= 200 && statusCode < 300;
}

class MobileApiClient {
  const MobileApiClient({
    this.baseUrl = const String.fromEnvironment(
      'BYS360_API_BASE',
      defaultValue: 'https://bys360.canakkaletarihialan.gov.tr',
    ),
    this.timeout = const Duration(seconds: 20),
  });

  final String baseUrl;
  final Duration timeout;

  Uri _buildUri(String path) {
    final normalizedBase = baseUrl.endsWith('/')
        ? baseUrl.substring(0, baseUrl.length - 1)
        : baseUrl;
    final normalizedPath = path.startsWith('/') ? path : '/$path';
    return Uri.parse('$normalizedBase$normalizedPath');
  }

  Future<MobileApiResponse> get(
    String path, {
    Map<String, String>? headers,
  }) async {
    final client = HttpClient();
    client.connectionTimeout = timeout;

    try {
      final request = await client.getUrl(_buildUri(path)).timeout(timeout);
      headers?.forEach(request.headers.set);
      request.headers.set(HttpHeaders.acceptHeader, 'application/json');

      final response = await request.close().timeout(timeout);
      final body = await response.transform(utf8.decoder).join();

      Map<String, dynamic> parsed;
      if (body.trim().isEmpty) {
        parsed = <String, dynamic>{};
      } else {
        final decoded = jsonDecode(body);
        parsed = decoded is Map<String, dynamic>
            ? decoded
            : <String, dynamic>{'items': decoded};
      }

      return MobileApiResponse(
        statusCode: response.statusCode,
        data: parsed,
        errorMessage: response.statusCode >= 400 ? body : null,
      );
    } catch (error) {
      return MobileApiResponse(
        statusCode: 0,
        data: <String, dynamic>{},
        errorMessage: error.toString(),
      );
    } finally {
      client.close(force: true);
    }
  }



  Future<MobileApiResponse> post(
    String path,
    Map<String, dynamic> body, {
    Map<String, String>? headers,
  }) async {
    final client = HttpClient();
    client.connectionTimeout = timeout;

    try {
      final request = await client.postUrl(_buildUri(path)).timeout(timeout);
      headers?.forEach(request.headers.set);
      request.headers.set(HttpHeaders.acceptHeader, 'application/json');
      request.headers.set(HttpHeaders.contentTypeHeader, 'application/json; charset=utf-8');
      request.write(jsonEncode(body));

      final response = await request.close().timeout(timeout);
      final responseBody = await response.transform(utf8.decoder).join();

      Map<String, dynamic> parsed;
      if (responseBody.trim().isEmpty) {
        parsed = <String, dynamic>{};
      } else {
        final decoded = jsonDecode(responseBody);
        parsed = decoded is Map<String, dynamic>
            ? decoded
            : <String, dynamic>{'items': decoded};
      }

      return MobileApiResponse(
        statusCode: response.statusCode,
        data: parsed,
        errorMessage: response.statusCode >= 400 ? responseBody : null,
      );
    } catch (error) {
      return MobileApiResponse(
        statusCode: 0,
        data: <String, dynamic>{},
        errorMessage: error.toString(),
      );
    } finally {
      client.close(force: true);
    }
  }

  Future<Map<String, dynamic>> postJson(
    String path,
    Map<String, dynamic> body, {
    Map<String, String>? headers,
  }) async {
    final response = await post(path, body, headers: headers);
    return response.data;
  }

  Future<Map<String, dynamic>> getJson(
    String path, {
    Map<String, String>? headers,
  }) async {
    final response = await get(path, headers: headers);
    return response.data;
  }
}

// BYS360_MOBILE_V2_8_62_POST_SUPPORT
