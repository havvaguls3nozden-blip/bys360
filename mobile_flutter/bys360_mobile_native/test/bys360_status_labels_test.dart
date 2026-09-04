// BYS360 H1D/H1E -- bys360GenericStatusLabel() coverage.
//
// Root cause fixed in H1D: two independent, duplicated status-label
// dictionaries existed for essentially the same concept
// (features/performance/performance_tasks_screen.dart's now-removed
// _performanceTaskStatusLabel and this file's original
// bys360PerformanceStatusLabel). The screen-local copy was missing several
// keys the canonical one already had (hr_precheck, scorecard_pending,
// approved_by_president, ...), so a backend status code using one of those
// missing keys fell through to a raw, untranslated return. The screen-local
// function now delegates to the canonical one instead of keeping a second
// copy that can silently fall behind. Separately, the canonical function's
// own fallback for a genuinely unmapped *single-word* code (no
// underscore/dash) used to return the raw lowercase value verbatim; it now
// title-cases that case too.
//
// H1E moved the canonical function out of the performance module to
// core/utils/bys360_status_labels.dart as bys360GenericStatusLabel(), so
// every module (KPI, support, surveys, personnel, the shared
// RecordCard/StatusPill pipeline) can reuse the same dictionary instead of
// each leaving its own raw-status leak. It gained a configurable
// `fallback` parameter (the performance module still wants 'Takipte' for
// an empty value; other callers want a more generic default) and a guard
// against mangling already-composed multi-word free text (see the "does
// not corrupt free text" group below).
import 'package:bys360_mobile_native/core/utils/bys360_status_labels.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('bys360GenericStatusLabel known codes', () {
    test('maps a core status code to its Turkish label', () {
      expect(bys360GenericStatusLabel('pending'), 'Bekliyor');
      expect(bys360GenericStatusLabel('completed'), 'Tamamlandı');
    });

    test('maps the extended codes the screen-local copy used to be missing', () {
      // These keys existed only in the canonical dictionary, not in the
      // old features/performance/performance_tasks_screen.dart copy --
      // proving the consolidation actually closes the gap, not just moves
      // code around.
      expect(bys360GenericStatusLabel('hr_precheck'), 'İK/Admin Ön Kontrolünde');
      expect(bys360GenericStatusLabel('scorecard_pending'), 'Karne Yayın Bekliyor');
      expect(bys360GenericStatusLabel('approved_by_president'), 'Başkan Tarafından Onaylandı');
      expect(bys360GenericStatusLabel('published'), 'Yayınlandı');
    });

    test('is case- and separator-insensitive', () {
      expect(bys360GenericStatusLabel('PENDING'), 'Bekliyor');
      expect(bys360GenericStatusLabel('in-progress'), 'Devam Ediyor');
      expect(bys360GenericStatusLabel('in progress'), 'Devam Ediyor');
    });
  });

  group('bys360GenericStatusLabel fallback for unmapped codes', () {
    test('empty value returns the caller-supplied fallback', () {
      expect(bys360GenericStatusLabel('', fallback: 'Takipte'), 'Takipte');
      expect(bys360GenericStatusLabel('   ', fallback: 'Takipte'), 'Takipte');
    });

    test('empty value returns the generic default fallback when none is supplied', () {
      expect(bys360GenericStatusLabel(''), 'Bilinmiyor');
      expect(bys360GenericStatusLabel(null), 'Bilinmiyor');
    });

    test('an unmapped multi-word CODE (underscore-separated) is title-cased, not shown raw', () {
      expect(bys360GenericStatusLabel('some_future_status'), 'Some Future Status');
    });

    test('an unmapped SINGLE-WORD code is title-cased too (the H1D fix)', () {
      // Before the H1D fix this returned 'cancelled' verbatim (raw,
      // lowercase, untranslated) because the split/title-case branch only
      // ran for values containing an underscore or dash.
      expect(bys360GenericStatusLabel('cancelled'), 'Cancelled');
      expect(bys360GenericStatusLabel('archived'), 'Archived');
    });
  });

  group('bys360GenericStatusLabel does not corrupt already-composed free text', () {
    // Reusing this function for generic screens (module names, notes,
    // already-Turkish labels a backend or a sibling helper already
    // produced) risks flattening deliberate capitalization if the
    // underscore/dash title-caser ran on a full phrase -- e.g. it would
    // otherwise turn "İnsan Kaynakları" into "İnsan kaynakları". A value
    // containing a space (and not itself a known dictionary key) is
    // assumed to already be composed text and is returned unchanged.
    test('a multi-word phrase with its own capitalization passes through unchanged', () {
      expect(bys360GenericStatusLabel('İnsan Kaynakları'), 'İnsan Kaynakları');
      expect(bys360GenericStatusLabel('Kurum içi'), 'Kurum içi');
      expect(bys360GenericStatusLabel('Tekrar cevaplanabilir'), 'Tekrar cevaplanabilir');
    });

    test('a multi-word value that still matches the dictionary is translated normally', () {
      expect(bys360GenericStatusLabel('in progress'), 'Devam Ediyor');
    });
  });
}
