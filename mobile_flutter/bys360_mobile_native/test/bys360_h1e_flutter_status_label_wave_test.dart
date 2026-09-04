// BYS360 H1E (Flutter/mobile wave) -- raw status/enum display closure.
//
// A repo-wide sweep (mirroring the Python-side H1E-A..F waves already
// landed) found the same underlying defect repeated across the Flutter
// app in several independent shapes:
//
//   - core/widgets/record_widgets.dart's StatusPill (used directly or via
//     RecordCard on 15+ screens: performance, KPI, support, surveys,
//     profile/settings/ai-decision) ran raw status/meta text through
//     BYS360Copy.clean() only -- an *error-message* sanitizer, not a
//     status dictionary -- so a raw backend code like "in_progress" or
//     "hr_precheck" was shown verbatim to the user.
//   - features/support/support_models.dart and
//     features/surveys/survey_detail_screen.dart's SurveyHeader both had
//     the classic `json['x_label'] ?? json['x'] ?? '-'` self-fallback
//     shape: if the backend omitted the pre-built label, the raw
//     machine-value fell through untranslated.
//     SupportStatusHistoryItem's oldStatus/newStatus had no mapping
//     attempt at all.
//   - features/personnel/personnel_mobile_p1_screen.dart's `_status()`
//     picked status_label/status/aktiflik/is_active/active with a single
//     generic priority chain; if only a boolean is_active/active was
//     present, `.toString()` on a genuine Dart bool rendered the literal
//     English word "true"/"false" in the "Durum" detail row.
//
// The fix is a single shared, safe dictionary (bys360GenericStatusLabel,
// moved from the performance-only bys360PerformanceStatusLabel to
// core/utils/bys360_status_labels.dart so every module can reuse it) plus
// a dedicated bys360ActiveFlagLabel() for the boolean case, wired into
// StatusPill (fixing the whole RecordCard/StatusPill surface in one
// place) and into the two model-level self-fallbacks directly (so the
// value is safe regardless of which widget ends up displaying it, e.g.
// BysPage's `badge:` parameter, which does NOT go through StatusPill).
import 'package:bys360_mobile_native/core/theme/app_theme.dart';
import 'package:bys360_mobile_native/core/utils/bys360_status_labels.dart';
import 'package:bys360_mobile_native/core/widgets/record_widgets.dart';
import 'package:bys360_mobile_native/features/support/support_models.dart';
import 'package:bys360_mobile_native/features/surveys/survey_detail_screen.dart';
import 'package:bys360_mobile_native/models/mobile_record.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('bys360ActiveFlagLabel', () {
    test('maps real Dart booleans', () {
      expect(bys360ActiveFlagLabel(true), 'Aktif');
      expect(bys360ActiveFlagLabel(false), 'Pasif');
    });

    test('maps stringified booleans (defensive JSON parsing)', () {
      expect(bys360ActiveFlagLabel('true'), 'Aktif');
      expect(bys360ActiveFlagLabel('false'), 'Pasif');
      expect(bys360ActiveFlagLabel('1'), 'Aktif');
      expect(bys360ActiveFlagLabel('0'), 'Pasif');
    });

    test('returns null (not a raw echo) for null or an unrecognizable value', () {
      expect(bys360ActiveFlagLabel(null), isNull);
      expect(bys360ActiveFlagLabel('unknown'), isNull);
      expect(bys360ActiveFlagLabel(42), isNull);
    });
  });

  group('SupportTicketInfo.fromJson status/priority labels', () {
    Map<String, dynamic> ticketJson({String? status, String? priority, String? statusLabel, String? priorityLabel}) => <String, dynamic>{
          'id': '1',
          if (status != null) 'status': status,
          if (statusLabel != null) 'status_label': statusLabel,
          if (priority != null) 'priority': priority,
          if (priorityLabel != null) 'priority_label': priorityLabel,
        };

    test('uses the backend-supplied label verbatim when present', () {
      final ticket = SupportTicketInfo.fromJson(ticketJson(status: 'open', statusLabel: 'Açık Talep'));
      expect(ticket.statusLabel, 'Açık Talep');
    });

    test('falls back to the safe dictionary for a KNOWN raw status/priority when no label is supplied', () {
      final ticket = SupportTicketInfo.fromJson(ticketJson(status: 'in_progress', priority: 'open'));
      expect(ticket.statusLabel, 'Devam Ediyor');
      expect(ticket.priorityLabel, 'Açık');
    });

    test('an UNMAPPED raw status/priority never leaks raw -- it is at least title-cased', () {
      final ticket = SupportTicketInfo.fromJson(ticketJson(status: 'future_ticket_status_v9', priority: 'future_priority_v9'));
      expect(ticket.statusLabel, isNot('future_ticket_status_v9'));
      expect(ticket.statusLabel, 'Future Ticket Status V9');
      expect(ticket.priorityLabel, 'Future Priority V9');
    });

    test('no status/priority at all falls back to "-", not an empty or null string', () {
      final ticket = SupportTicketInfo.fromJson(ticketJson());
      expect(ticket.statusLabel, '-');
      expect(ticket.priorityLabel, '-');
    });

    test('the raw status/priority fields themselves stay exactly as the backend sent them', () {
      final ticket = SupportTicketInfo.fromJson(ticketJson(status: 'in_progress', priority: 'open'));
      expect(ticket.status, 'in_progress');
      expect(ticket.priority, 'open');
    });
  });

  group('SupportStatusHistoryItem.fromJson old/new status labels', () {
    test('known codes are translated', () {
      final item = SupportStatusHistoryItem.fromJson(<String, dynamic>{'old_status': 'pending', 'new_status': 'completed'});
      expect(item.oldStatus, 'Bekliyor');
      expect(item.newStatus, 'Tamamlandı');
    });

    test('an unmapped code is title-cased, never shown raw', () {
      final item = SupportStatusHistoryItem.fromJson(<String, dynamic>{'old_status': 'some_future_code', 'new_status': 'another_future_code'});
      expect(item.oldStatus, 'Some Future Code');
      expect(item.newStatus, 'Another Future Code');
    });

    test('missing old_status/new_status keep their original safe defaults', () {
      final item = SupportStatusHistoryItem.fromJson(<String, dynamic>{});
      expect(item.oldStatus, 'İlk kayıt');
      expect(item.newStatus, '-');
    });
  });

  group('SurveyHeader.fromJson status label', () {
    test('uses the backend-supplied label verbatim when present', () {
      final header = SurveyHeader.fromJson(<String, dynamic>{'id': '1', 'status_label': 'Yayında'});
      expect(header.statusLabel, 'Yayında');
    });

    test('an unmapped raw status never leaks raw when no label is supplied', () {
      final header = SurveyHeader.fromJson(<String, dynamic>{'id': '1', 'status': 'future_survey_status_v9'});
      expect(header.statusLabel, isNot('future_survey_status_v9'));
      expect(header.statusLabel, 'Future Survey Status V9');
    });

    test('no status at all falls back to "-"', () {
      final header = SurveyHeader.fromJson(<String, dynamic>{'id': '1'});
      expect(header.statusLabel, '-');
    });
  });

  group('StatusPill widget', () {
    Future<void> pump(WidgetTester tester, Widget child) async {
      await tester.pumpWidget(MaterialApp(home: Scaffold(body: child)));
    }

    testWidgets('translates a raw machine status code instead of showing it verbatim', (tester) async {
      await pump(tester, const StatusPill(text: 'in_progress'));
      expect(find.text('Devam Ediyor'), findsOneWidget);
      expect(find.text('in_progress'), findsNothing);
    });

    testWidgets('title-cases a genuinely unmapped raw code rather than leaking it raw', (tester) async {
      await pump(tester, const StatusPill(text: 'future_status_v9'));
      expect(find.text('Future Status V9'), findsOneWidget);
      expect(find.text('future_status_v9'), findsNothing);
    });

    testWidgets('does not mangle an already-composed multi-word Turkish phrase', (tester) async {
      await pump(tester, const StatusPill(text: 'İnsan Kaynakları'));
      expect(find.text('İnsan Kaynakları'), findsOneWidget);
    });
  });

  group('RecordCard (the shared widget behind 15+ screens)', () {
    testWidgets('shows the translated status, not the raw MobileRecord.status value', (tester) async {
      final record = MobileRecord(id: '1', title: 'Test kaydı', status: 'hr_precheck');
      await tester.pumpWidget(MaterialApp(
        home: Scaffold(
          body: RecordCard(record: record, icon: Icons.info_outline, tone: BYS360Colors.corporateRed, onTap: null),
        ),
      ));
      expect(find.text('İK/Admin Ön Kontrolünde'), findsOneWidget);
      expect(find.text('hr_precheck'), findsNothing);
    });
  });
}
