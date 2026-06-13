# BYS360 A10C Hard UI Teknik Dil Düzeltme Planı

Tarih: 2026-06-12T19:04:20

## Özet

- Hard UI file count: 20
- Hard UI hit total: 57
- A10C OK: False

## Düzeltme Planı

```json
[
  {
    "path": "app/templates/feedback_go_live_center.html",
    "hard_count": 1,
    "suggestions": [
      {
        "line": 223,
        "term": "endpoint",
        "sample": "{% for item in endpoint_checks %}",
        "suggested_message": "Servis bağlantısı"
      }
    ]
  },
  {
    "path": "app/templates/home.html",
    "hard_count": 2,
    "suggestions": [
      {
        "line": 130,
        "term": "endpoint",
        "sample": "<a href=\"{{ safe_url_for(item.endpoint, fallback='#') }}\" class=\"home-faz1-quick-card tone-{{ item.tone }}\">",
        "suggested_message": "Servis bağlantısı"
      },
      {
        "line": 175,
        "term": "endpoint",
        "sample": "<a href=\"{{ safe_url_for(card.endpoint, fallback='#') }}\" class=\"home-faz1-op-card\">",
        "suggested_message": "Servis bağlantısı"
      }
    ]
  },
  {
    "path": "app/templates/hr_attendance.html",
    "hard_count": 3,
    "suggestions": [
      {
        "line": 308,
        "term": "exception",
        "sample": "<select name=\"exception_type\" required data-role=\"attendance-type\">",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 424,
        "term": "exception",
        "sample": "<option value=\"{{ row.id }}\">{{ row.user.full_name if row.user else '-' }} · {{ row.record_date }} · {{ row.exception_type }}</option>",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 492,
        "term": "exception",
        "sample": "<td>{{ attendance_type_label(row.exception_type) }}</td>",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      }
    ]
  },
  {
    "path": "app/static/js/bys360_live_full_overlay_v2_13_0.js",
    "hard_count": 6,
    "suggestions": [
      {
        "line": 105,
        "term": "workflow",
        "sample": "[/\\bworkflow state\\b/gi, \"Süreç durumu\"],",
        "suggested_message": "Teknik ifade yerine sade ve kurumsal Türkçe mesaj kullanılmalıdır."
      },
      {
        "line": 109,
        "term": "endpoint",
        "sample": "[/\\bendpoint\\b/gi, \"bağlantı\"],",
        "suggested_message": "Servis bağlantısı"
      },
      {
        "line": 104,
        "term": "unauthorized_scope",
        "sample": "[/\\bunauthorized_scope\\b/gi, \"Bu işlem için yetkiniz bulunmamaktadır\"],",
        "suggested_message": "Bu işlem için yetkiniz bulunmamaktadır."
      },
      {
        "line": 111,
        "term": "traceback",
        "sample": "[/\\btraceback\\b/gi, \"hata ayrıntısı\"],",
        "suggested_message": "İşlem sırasında teknik bir hata oluştu. Lütfen sistem yöneticisine bildiriniz."
      },
      {
        "line": 110,
        "term": "exception",
        "sample": "[/\\bexception\\b/gi, \"işlem hatası\"],",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 113,
        "term": "api error",
        "sample": "[/\\bAPI error\\b/gi, \"Veriler şu anda alınamadı\"]",
        "suggested_message": "Servise şu anda ulaşılamadı. Lütfen tekrar deneyiniz."
      }
    ]
  },
  {
    "path": "app/templates/ai_decision/_faz9_reminder_panel.html",
    "hard_count": 2,
    "suggestions": [
      {
        "line": 2,
        "term": "faz",
        "sample": "<section class=\"ai-faz9-reminder-panel\" data-ai-reminder-endpoint=\"/ai/decision-support/performance/reminders/summary\">",
        "suggested_message": "Teknik ifade yerine sade ve kurumsal Türkçe mesaj kullanılmalıdır."
      },
      {
        "line": 2,
        "term": "endpoint",
        "sample": "<section class=\"ai-faz9-reminder-panel\" data-ai-reminder-endpoint=\"/ai/decision-support/performance/reminders/summary\">",
        "suggested_message": "Servis bağlantısı"
      }
    ]
  },
  {
    "path": "app/templates/performance/feedback_corporate_cleanup_phase6.html",
    "hard_count": 1,
    "suggestions": [
      {
        "line": 62,
        "term": "endpoint",
        "sample": "<a class=\"bys-live-btn {% if loop.first %}primary{% else %}soft{% endif %}\" href=\"{{ safe_url_for(link.endpoint) }}\"><i class=\"{{ link.icon }}\"></i> {{ link.label }}</a>",
        "suggested_message": "Servis bağlantısı"
      }
    ]
  },
  {
    "path": "app/templates/performance/feedback_pipeline.html",
    "hard_count": 3,
    "suggestions": [
      {
        "line": 585,
        "term": "endpoint",
        "sample": "{% if step.endpoint_ok %}",
        "suggested_message": "Servis bağlantısı"
      },
      {
        "line": 631,
        "term": "endpoint",
        "sample": "{% if step.endpoint_ok %}",
        "suggested_message": "Servis bağlantısı"
      },
      {
        "line": 633,
        "term": "endpoint",
        "sample": "href=\"{{ safe_url_for(step.endpoint) }}\"",
        "suggested_message": "Servis bağlantısı"
      }
    ]
  },
  {
    "path": "app/templates/portal/people.html",
    "hard_count": 1,
    "suggestions": [
      {
        "line": 88,
        "term": "endpoint",
        "sample": "<!-- BYS360_PORTAL_PROFILE_ME_LINK_V2_10_3: portal_my_profile endpoint bağlantısı portal_my_profile olarak düzeltildi. -->",
        "suggested_message": "Servis bağlantısı"
      }
    ]
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/api/mobile_real_api_contract.dart",
    "hard_count": 2,
    "suggestions": [
      {
        "line": 18,
        "term": "endpoint",
        "sample": "static const List<String> p0Endpoints = <String>[",
        "suggested_message": "Servis bağlantısı"
      },
      {
        "line": 64,
        "term": "endpoint",
        "sample": "static const List<String> endpoints = <String>[",
        "suggested_message": "Servis bağlantısı"
      }
    ]
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/api/support_survey_mobile_p1_contract.dart",
    "hard_count": 7,
    "suggestions": [
      {
        "line": 9,
        "term": "endpoint",
        "sample": "static const String supportTicketsEndpoint = '/api/mobile/support/tickets';",
        "suggested_message": "Servis bağlantısı"
      },
      {
        "line": 10,
        "term": "endpoint",
        "sample": "static const String supportTicketDetailEndpoint = '/api/mobile/support/tickets/{ticketId}';",
        "suggested_message": "Servis bağlantısı"
      },
      {
        "line": 11,
        "term": "endpoint",
        "sample": "static const String supportTicketCreateEndpoint = '/api/mobile/support/tickets';",
        "suggested_message": "Servis bağlantısı"
      },
      {
        "line": 12,
        "term": "endpoint",
        "sample": "static const String supportTicketReplyEndpoint = '/api/mobile/support/tickets/{ticketId}/messages';",
        "suggested_message": "Servis bağlantısı"
      },
      {
        "line": 15,
        "term": "endpoint",
        "sample": "static const String surveysEndpoint = '/api/mobile/surveys';",
        "suggested_message": "Servis bağlantısı"
      },
      {
        "line": 16,
        "term": "endpoint",
        "sample": "static const String surveyDetailEndpoint = '/api/mobile/surveys/{surveyId}';",
        "suggested_message": "Servis bağlantısı"
      },
      {
        "line": 17,
        "term": "endpoint",
        "sample": "static const String surveySubmitEndpoint = '/api/mobile/surveys/{surveyId}/submit';",
        "suggested_message": "Servis bağlantısı"
      }
    ]
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/auth/auth_controller.dart",
    "hard_count": 5,
    "suggestions": [
      {
        "line": 4,
        "term": "exception",
        "sample": "import '../network/api_exception.dart';",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 18,
        "term": "exception",
        "sample": "throw const ApiException('Kullanıcı adı ve şifre zorunludur.');",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 27,
        "term": "exception",
        "sample": "throw const ApiException('Giriş yanıtı beklenen formatta değil.');",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 32,
        "term": "exception",
        "sample": "throw const ApiException('Mobil oturum anahtarı alınamadı. Lütfen tekrar deneyin.');",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 49,
        "term": "exception",
        "sample": "throw const ApiException('Demo ön izleme kapalı.');",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      }
    ]
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/diagnostics/bys_mobile_crash_service.dart",
    "hard_count": 4,
    "suggestions": [
      {
        "line": 37,
        "term": "sync",
        "sample": "Future<void> _store(String message, StackTrace? stack) async {",
        "suggested_message": "Teknik ifade yerine sade ve kurumsal Türkçe mesaj kullanılmalıdır."
      },
      {
        "line": 31,
        "term": "stacktrace",
        "sample": "PlatformDispatcher.instance.onError = (Object error, StackTrace stack) {",
        "suggested_message": "İşlem sırasında teknik bir hata oluştu. Lütfen sistem yöneticisine bildiriniz."
      },
      {
        "line": 37,
        "term": "stacktrace",
        "sample": "Future<void> _store(String message, StackTrace? stack) async {",
        "suggested_message": "İşlem sırasında teknik bir hata oluştu. Lütfen sistem yöneticisine bildiriniz."
      },
      {
        "line": 28,
        "term": "exception",
        "sample": "unawaited(_store(details.exceptionAsString(), details.stack));",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      }
    ]
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/hardening/mobile_hardening_service.dart",
    "hard_count": 3,
    "suggestions": [
      {
        "line": 17,
        "term": "exception",
        "sample": "onTimeout: () => throw TimeoutException(MobileErrorTexts.timeoutMessage),",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 22,
        "term": "exception",
        "sample": "if (error is TimeoutException) {",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 25,
        "term": "exception",
        "sample": "if (error is SocketException) {",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      }
    ]
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/network/api_client.dart",
    "hard_count": 8,
    "suggestions": [
      {
        "line": 13,
        "term": "exception",
        "sample": "import 'api_exception.dart';",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 69,
        "term": "exception",
        "sample": "} on ApiException {",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 72,
        "term": "exception",
        "sample": "throw ApiException(_connectionMessage(error));",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 95,
        "term": "exception",
        "sample": "throw const ApiException(_bys360MobileCsrfFriendlyMessage, statusCode: 400);",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 118,
        "term": "exception",
        "sample": "throw ApiException(message, statusCode: response.statusCode);",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 122,
        "term": "exception",
        "sample": "throw const ApiException('Bu işlem için yetkiniz bulunmamaktadır.',",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 135,
        "term": "exception",
        "sample": "throw ApiException(message, statusCode: response.statusCode);",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 178,
        "term": "exception",
        "sample": "if (error is TimeoutException) {",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      }
    ]
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/network/api_exception.dart",
    "hard_count": 2,
    "suggestions": [
      {
        "line": 1,
        "term": "exception",
        "sample": "class ApiException implements Exception {",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 2,
        "term": "exception",
        "sample": "const ApiException(this.message, {this.statusCode});",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      }
    ]
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/theme/mobile_design_system.dart",
    "hard_count": 1,
    "suggestions": [
      {
        "line": 27,
        "term": "stacktrace",
        "sample": "'stacktrace',",
        "suggested_message": "İşlem sırasında teknik bir hata oluştu. Lütfen sistem yöneticisine bildiriniz."
      }
    ]
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
    "hard_count": 1,
    "suggestions": [
      {
        "line": 49,
        "term": "stacktrace",
        "sample": "lower.contains('stacktrace') ||",
        "suggested_message": "İşlem sırasında teknik bir hata oluştu. Lütfen sistem yöneticisine bildiriniz."
      }
    ]
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/widgets/bys360_logo.dart",
    "hard_count": 2,
    "suggestions": [
      {
        "line": 31,
        "term": "stacktrace",
        "sample": "errorBuilder: (context, error, stackTrace) => _LogoFallback(width: width, height: height),",
        "suggested_message": "İşlem sırasında teknik bir hata oluştu. Lütfen sistem yöneticisine bildiriniz."
      },
      {
        "line": 70,
        "term": "stacktrace",
        "sample": "errorBuilder: (context, error, stackTrace) => Container(",
        "suggested_message": "İşlem sırasında teknik bir hata oluştu. Lütfen sistem yöneticisine bildiriniz."
      }
    ]
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/features/auth/login_screen.dart",
    "hard_count": 2,
    "suggestions": [
      {
        "line": 5,
        "term": "exception",
        "sample": "import '../../core/network/api_exception.dart';",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      },
      {
        "line": 44,
        "term": "exception",
        "sample": "setState(() => _error = error is ApiException ? BYS360Copy.error(error.message) : BYS360Copy.error(error));",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      }
    ]
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/features/performance/performance_scoring_form_screen.dart",
    "hard_count": 1,
    "suggestions": [
      {
        "line": 130,
        "term": "exception",
        "sample": "return text.replaceFirst('İşlem tamamlanamadı: ', '').replaceFirst('ApiException: ', '').trim().isEmpty ? 'İşlem tamamlanamadı. Lütfen tekrar deneyin.' : text.replaceFirst('İşlem tamamlanamadı: ', '').replaceFirst('ApiException: ', '').trim",
        "suggested_message": "Beklenmeyen bir hata oluştu."
      }
    ]
  }
]
```

## Not

Bu aşama dosya değiştirmez. A10D aşamasında yedek alınarak güvenli dönüşüm uygulanacaktır.