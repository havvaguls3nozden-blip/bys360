// BYS360 H1D -- bys360PerformanceStatusLabel() coverage.
//
// Root cause fixed here: two independent, duplicated status-label
// dictionaries existed for essentially the same concept
// (features/performance/performance_tasks_screen.dart's now-removed
// _performanceTaskStatusLabel and this file's bys360PerformanceStatusLabel).
// The screen-local copy was missing several keys the canonical one already
// had (hr_precheck, scorecard_pending, approved_by_president, ...), so a
// backend status code using one of those missing keys fell through to a
// raw, untranslated return. The screen-local function now delegates to this
// canonical one instead of keeping a second copy that can silently fall
// behind. Separately, this canonical function's own fallback for a
// genuinely unmapped *single-word* code (no underscore/dash) used to return
// the raw lowercase value verbatim; it now title-cases that case too.
import 'package:bys360_mobile_native/features/performance/performance_mobile_p1_models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('bys360PerformanceStatusLabel known codes', () {
    test('maps a core status code to its Turkish label', () {
      expect(bys360PerformanceStatusLabel('pending'), 'Bekliyor');
      expect(bys360PerformanceStatusLabel('completed'), 'Tamamlandı');
    });

    test('maps the extended codes the screen-local copy used to be missing', () {
      // These keys existed only in bys360PerformanceStatusLabel, not in the
      // old features/performance/performance_tasks_screen.dart copy --
      // proving the consolidation actually closes the gap, not just moves
      // code around.
      expect(bys360PerformanceStatusLabel('hr_precheck'), 'İK/Admin Ön Kontrolünde');
      expect(bys360PerformanceStatusLabel('scorecard_pending'), 'Karne Yayın Bekliyor');
      expect(bys360PerformanceStatusLabel('approved_by_president'), 'Başkan Tarafından Onaylandı');
      expect(bys360PerformanceStatusLabel('published'), 'Yayınlandı');
    });

    test('is case- and separator-insensitive', () {
      expect(bys360PerformanceStatusLabel('PENDING'), 'Bekliyor');
      expect(bys360PerformanceStatusLabel('in-progress'), 'Devam Ediyor');
      expect(bys360PerformanceStatusLabel('in progress'), 'Devam Ediyor');
    });
  });

  group('bys360PerformanceStatusLabel fallback for unmapped codes', () {
    test('empty value returns the safe generic label', () {
      expect(bys360PerformanceStatusLabel(''), 'Takipte');
      expect(bys360PerformanceStatusLabel('   '), 'Takipte');
    });

    test('an unmapped multi-word code is title-cased, not shown raw', () {
      expect(bys360PerformanceStatusLabel('some_future_status'), 'Some Future Status');
    });

    test('an unmapped SINGLE-WORD code is title-cased too (the fixed gap)', () {
      // Before the fix this returned 'cancelled' verbatim (raw, lowercase,
      // untranslated) because the split/title-case branch only ran for
      // values containing an underscore or dash.
      expect(bys360PerformanceStatusLabel('cancelled'), 'Cancelled');
      expect(bys360PerformanceStatusLabel('archived'), 'Archived');
    });
  });
}
