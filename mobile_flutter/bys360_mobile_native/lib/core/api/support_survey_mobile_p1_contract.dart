// BYS360_MOBILE_V2_8_32_SUPPORT_SURVEY_P1_MARKER
// Destek ve Anket mobil ekranlari canli API sozlesmesi.
// Teknik dil kullanici yuzune cikmayacak; hata/empty/loading durumlari sade Turkce gosterilecek.

class SupportSurveyMobileP1Contract {
  static const String marker = 'BYS360_MOBILE_V2_8_32_SUPPORT_SURVEY_P1_MARKER';

  // Destek talepleri canli veri
  static const String supportTicketsEndpoint = '/api/mobile/support/tickets';
  static const String supportTicketDetailEndpoint = '/api/mobile/support/tickets/{ticketId}';
  static const String supportTicketCreateEndpoint = '/api/mobile/support/tickets';
  static const String supportTicketReplyEndpoint = '/api/mobile/support/tickets/{ticketId}/messages';

  // Anket ve geri bildirim canli veri
  static const String surveysEndpoint = '/api/mobile/surveys';
  static const String surveyDetailEndpoint = '/api/mobile/surveys/{surveyId}';
  static const String surveySubmitEndpoint = '/api/mobile/surveys/{surveyId}/submit';

  // Gate markerlari
  static const String supportList = 'support_live_list';
  static const String supportDetail = 'support_live_detail';
  static const String supportCreate = 'support_live_create';
  static const String supportReply = 'support_live_reply';
  static const String surveyList = 'survey_live_list';
  static const String surveyDetail = 'survey_live_detail';
  static const String surveySubmit = 'survey_live_submit';
  static const String roleSafeView = 'support_survey_role_safe_view';
  static const String noMockCopy = 'support_survey_no_mock_copy';
}

// support_reply
// support_contract
// BYS360_MOBILE_V2_8_32_SUPPORT_SURVEY_P1_REPLY_FIX
// survey_answer
// survey_contract
// BYS360_MOBILE_V2_8_32_SUPPORT_SURVEY_P1_REPLY_FIX
