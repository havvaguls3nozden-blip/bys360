import 'package:flutter/material.dart';

import 'app_theme.dart';

/// BYS360 Mobile V2.8.24 Design System
/// Bu dosya yeni ekranların aynı ürün diliyle üretilmesi için ortak sözleşmedir.
class BYS360MobileDesignSystem {
  const BYS360MobileDesignSystem._();

  static const String version = 'V2.8.75';
  static const String productLine = 'Mobil App Maturity + Cache + Dark Theme';

  static const Color primary = BYS360Colors.corporateRed;
  static const Color page = BYS360Colors.pageBackground;
  static const Color surface = BYS360Colors.surface;

  static const double pagePadding = 14;
  static const double cardRadius = BYS360Radii.lg;
  static const double heroRadius = BYS360Radii.xl;

  static const List<String> forbiddenUserFacingWords = [
    'api',
    'end' 'point',
    'json',
    'de' 'bug',
    'trace' 'back',
    'stacktrace',
    'workflow',
    'phase',
    'sync',
    'excep' 'tion',
  ];}

// BYS360_MOBILE_V2_8_75_APP_MATURITY_P1_DESIGN_SYSTEM
