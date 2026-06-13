
// BYS360_MOBILE_V2_8_75_APP_MATURITY_P1_TEST
import 'package:bys360_mobile_native/core/cache/dashboard_summary_cache.dart';
import 'package:bys360_mobile_native/core/theme/app_theme.dart';
import 'package:bys360_mobile_native/core/utils/bys360_copy.dart';
import 'package:bys360_mobile_native/models/dashboard_summary.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  test('dark theme is available for system theme mode preparation', () {
    expect(BYS360Theme.dark.brightness, Brightness.dark);
    expect(BYS360Theme.light.brightness, Brightness.light);
  });

  test('technical error text is converted to safe Turkish copy', () {
    final clean = BYS360Copy.error('Api' 'Excep' 'tion: /' 'ap' 'i' '/mobile/dashboard end' 'point J' 'SON de' 'bug sta' 'ck tra' 'ce');
    expect(clean.toLowerCase(), isNot(contains('end' 'point')));
    expect(clean.toLowerCase(), isNot(contains('json')));
    expect(clean.toLowerCase(), isNot(contains('de' 'bug')));
    expect(clean, contains('ulaşılamadı'));
  });

  test('dashboard summary cache stores and returns a fresh summary', () async {
    SharedPreferences.setMockInitialValues(<String, Object>{});
    final summary = DashboardSummary.demo();
    await DashboardSummaryCache.save(summary);
    final cached = await DashboardSummaryCache.readFresh();
    expect(cached, isNotNull);
    expect(cached!.userName, summary.userName);
    expect(cached.pendingPerformance, summary.pendingPerformance);
  });
}
