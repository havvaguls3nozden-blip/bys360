// BYS360 H1 -- BYS360Copy.error() must never leak an untranslated raw
// exception message that clean()'s existing known-pattern checks do not
// recognize (root cause: P0 humanization audit, reconfirmed against real
// mobile call sites in api_client.dart / api_state.dart before this fix).
import 'package:bys360_mobile_native/core/utils/bys360_copy.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('BYS360Copy.error unknown-exception fallback', () {
    test('unmapped English exception text falls back to safe Turkish message', () {
      // Does not match any of clean()'s specific handlers (not 401/403,
      // not timeout, not socket/network, not looksTechnical) -- before the
      // fix this was returned to the user almost verbatim.
      final result = BYS360Copy.error('Unexpected character at offset 12');
      expect(result, BYS360Copy.genericUnavailable);
    });

    test('unmapped FormatException-style text falls back to safe Turkish message', () {
      final result = BYS360Copy.error('FormatException: Invalid radix-10 number');
      expect(result, BYS360Copy.genericUnavailable);
    });

    test('known socket exception still routes to the existing connection message', () {
      // Positive regression: previously-working known-pattern paths in
      // clean() must be completely unaffected by this change.
      final result = BYS360Copy.error('SocketException: Failed host lookup');
      expect(result, BYS360Copy.genericConnection);
    });

    test('known 403 exception still routes to the existing unauthorized message', () {
      final result = BYS360Copy.error('ApiException: 403 Forbidden');
      expect(result, BYS360Copy.genericUnauthorized);
    });

    test('a real Turkish exception message passes through unchanged', () {
      // Positive regression: a legitimate already-Turkish message (typical
      // of this app's own custom exceptions) must never be swallowed.
      final result = BYS360Copy.error('Kayıt bulunamadı, lütfen tekrar deneyin.');
      expect(result, 'Kayıt bulunamadı, lütfen tekrar deneyin.');
    });

    test('empty/null input still returns the existing generic empty message', () {
      expect(BYS360Copy.error(null), BYS360Copy.genericEmpty);
      expect(BYS360Copy.error(''), BYS360Copy.genericEmpty);
    });
  });

  group('BYS360Copy.title / subtitle / clean remain untouched by the error() fix', () {
    // Critical regression guard: title()/subtitle()/clean() are used
    // throughout the app for ordinary short UI labels (metric_card.dart,
    // bys_page.dart, bys_mobile_chrome.dart), many of which legitimately
    // contain no Turkish diacritic character (e.g. "Personel", "Toplam",
    // "42"). The error()-only fallback must never reach these call paths.
    test('a plain ASCII Turkish label with no diacritics passes through title()', () {
      expect(BYS360Copy.title('Personel'), 'Personel');
    });

    test('a plain ASCII numeric-looking value passes through clean()', () {
      expect(BYS360Copy.clean('42'), '42');
    });

    test('a short ASCII label containing "error" as a substring still passes through clean() (not error())', () {
      // clean() itself is intentionally unchanged -- only the error() alias
      // gained the extra safety net. Any caller using clean()/title()/
      // subtitle() directly keeps the exact pre-existing behavior.
      expect(BYS360Copy.clean('Terror Yonetimi'), 'Terror Yonetimi');
    });
  });
}
