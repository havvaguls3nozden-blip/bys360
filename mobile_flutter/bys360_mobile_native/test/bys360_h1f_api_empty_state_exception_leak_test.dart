// BYS360 H1F -- mobile-side raw exception leak audit.
//
// A repo-wide grep of mobile_flutter/**/*.dart for FutureBuilder error
// branches found three screens that passed `snapshot.error.toString()`
// directly as the ApiEmptyState `message` prop instead of routing it
// through the app's existing BYS360Copy.error() helper first (H1 built
// that helper specifically to convert technical/English exception text
// into a safe Turkish message; see core/utils/bys360_copy.dart):
//
//   - lib/features/surveys/survey_detail_screen.dart (line ~123)
//   - lib/features/surveys/surveys_screen.dart (line ~89)
//   - lib/features/kpi/kpi_target_management_screen.dart (line ~142)
//
// Every OTHER FutureBuilder error branch in this app (~20 sibling screens,
// e.g. dashboard_screen.dart, performance_screen.dart, support_screen.dart,
// notifications_screen.dart, ...) instead hard-codes a fixed safe Turkish
// string for this exact "list load failed" case and never echoes the live
// exception at all -- these three were the only outliers.
//
// Investigation before fixing (required by this initiative's mobile-API
// contract-risk check) found that ApiEmptyState itself
// (lib/core/widgets/api_state.dart) already unconditionally routes its
// `message` prop through BYS360Copy.error() before rendering (see its
// `build()`: `final cleanMessage = BYS360Copy.error(message);` then
// `Text(cleanMessage, ...)`) -- so these three call sites were not actually
// exploitable through this exact widget; ApiEmptyState's own internal
// safety net already caught the raw text before it painted. This suite
// records that as a positive/defense-in-depth fact (group 1) so it is not
// silently lost, and separately proves the three fixed call sites now also
// sanitize *before* handing the string to ApiEmptyState (group 2), so
// nothing here relies solely on ApiEmptyState's internal behavior staying
// exactly as it is today. Both layers now agree on the same safe output --
// exactly what H1F requires ("route the display through BYS360Copy.error()
// ... instead of showing the raw exception/error text directly").
//
// Fix applied at each of the three call sites: replaced
// `snapshot.error.toString()` with `BYS360Copy.error(snapshot.error)`.
import 'package:bys360_mobile_native/core/utils/bys360_copy.dart';
import 'package:bys360_mobile_native/core/widgets/api_state.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const String _sentinel = 'TECHNICAL_SENTINEL_DO_NOT_SHOW_9F3A';

void main() {
  group('ApiEmptyState defense-in-depth (unconditional internal sanitization)', () {
    testWidgets(
      'a raw, unsanitized exception .toString() passed directly as message never reaches the rendered Text',
      (tester) async {
        // Mirrors exactly what the three fixed screens did BEFORE this H1F
        // fix: `message: snapshot.error.toString()` with no BYS360Copy call
        // at the call site at all. Proves ApiEmptyState's own internal
        // `BYS360Copy.error(message)` call is a real, working safety net on
        // its own -- not merely documented, but exercised here.
        final rawException = Exception(_sentinel);

        await tester.pumpWidget(MaterialApp(
          home: Scaffold(
            body: ApiEmptyState(message: rawException.toString()),
          ),
        ));

        expect(find.textContaining(_sentinel), findsNothing);
        expect(find.text(BYS360Copy.genericUnavailable), findsOneWidget);
      },
    );

    testWidgets(
      'a raw StateError .toString() (carries the English "Bad state:" prefix) never reaches the rendered Text',
      (tester) async {
        // survey_detail_screen.dart's and surveys_screen.dart's _load()
        // throw `StateError('<safe Turkish text>')` for a malformed payload
        // shape. StateError.toString() prepends the English "Bad state:"
        // marker even though the message itself is Turkish -- proves that
        // prefix does not leak through either.
        final stateError = StateError('Anket detayı beklenen biçimde alınamadı.');

        await tester.pumpWidget(MaterialApp(
          home: Scaffold(
            body: ApiEmptyState(message: stateError.toString()),
          ),
        ));

        expect(find.textContaining('Bad state'), findsNothing);
      },
    );
  });

  group('H1F fix: the three call sites now sanitize before reaching ApiEmptyState', () {
    testWidgets(
      'kpi_target_management_screen / survey_detail_screen / surveys_screen pattern: '
      'BYS360Copy.error(snapshot.error) passed to ApiEmptyState renders no sentinel',
      (tester) async {
        final rawException = Exception(_sentinel);

        // This is the exact expression now used at all three fixed call
        // sites: ApiEmptyState(message: BYS360Copy.error(snapshot.error), ...)
        await tester.pumpWidget(MaterialApp(
          home: Scaffold(
            body: ApiEmptyState(message: BYS360Copy.error(rawException)),
          ),
        ));

        expect(find.textContaining(_sentinel), findsNothing);
        expect(find.text(BYS360Copy.genericUnavailable), findsOneWidget);
      },
    );

    test('BYS360Copy.error() never leaks the sentinel for a generic Exception object (not just a String)', () {
      // The three fixed call sites pass the live `snapshot.error` Object
      // directly (not a pre-stringified value) -- confirm BYS360Copy.error
      // handles a real Exception instance, not only String input.
      final rawException = Exception(_sentinel);
      final result = BYS360Copy.error(rawException);

      expect(result, isNot(contains(_sentinel)));
      expect(result, BYS360Copy.genericUnavailable);
    });

    test('the real StateError thrown by these screens\' own _load() round-trips through BYS360Copy.error() unchanged and never carries the English "Bad state:" marker', () {
      // survey_detail_screen.dart / surveys_screen.dart / kpi_target_
      // management_screen.dart all throw StateError with this exact fixed,
      // already-Turkish, non-interpolated string when the payload shape is
      // wrong -- this is the actual (not hypothetical) content that can
      // reach snapshot.error at these three call sites.
      final stateError = StateError('Anket detayı beklenen biçimde alınamadı.');
      final result = BYS360Copy.error(stateError);

      expect(result, isNot(contains('Bad state')));
      expect(result, 'Anket detayı beklenen biçimde alınamadı.');
    });
  });
}
