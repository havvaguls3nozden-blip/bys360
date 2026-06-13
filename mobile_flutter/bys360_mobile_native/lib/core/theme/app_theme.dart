
// BYS360_MOBILE_V2_8_75_APP_MATURITY_P1_THEME
import 'package:flutter/material.dart';

class BYS360Colors {
  static const Color corporateRed = Color(0xFF8B0000);
  static const Color deepRed = Color(0xFF650000);
  static const Color darkerRed = Color(0xFF4F0000);
  static const Color softRed = Color(0xFFF7E9E7);
  static const Color pageBackground = Color(0xFFF7F4F1);
  static const Color pageBackgroundWarm = Color(0xFFFDFBF9);
  static const Color surface = Colors.white;
  static const Color surfaceRaised = Color(0xFFFFFEFC);
  static const Color surfaceSoft = Color(0xFFFBF7F4);
  static const Color cardBorder = Color(0xFFE8DDD8);
  static const Color border = Color(0xFFE8DDD8);
  static const Color mutedText = Color(0xFF6B5F5A);
  static const Color subtleText = Color(0xFF8C7F79);
  static const Color ink = Color(0xFF241A17);
  static const Color primaryText = ink;
  static const Color borderColor = cardBorder;
  static const Color gold = Color(0xFFC8A45D);
  static const Color success = Color(0xFF26734D);
  static const Color warning = Color(0xFF9A6200);
  static const Color info = Color(0xFF315B7C);
  static const Color purple = Color(0xFF6F407A);
  static const Color danger = Color(0xFFB42318);

  // Dark-mode preparation colors. Existing screens keep the corporate line; new screens can read these safely.
  static const Color darkPage = Color(0xFF17100E);
  static const Color darkSurface = Color(0xFF241917);
  static const Color darkSurfaceRaised = Color(0xFF2F211E);
  static const Color darkBorder = Color(0xFF4C3834);
  static const Color darkText = Color(0xFFF7EFEA);
  static const Color darkMutedText = Color(0xFFD8C8BF);
}

class BYS360Radii {
  static const double sm = 12;
  static const double md = 16;
  static const double lg = 20;
  static const double xl = 26;
}

class BYS360Spacing {
  static const double xs = 6;
  static const double sm = 10;
  static const double md = 14;
  static const double lg = 18;
  static const double xl = 24;
}

class BYS360Shadows {
  static List<BoxShadow> get card => [
        BoxShadow(
          color: BYS360Colors.corporateRed.withValues(alpha: .055),
          blurRadius: 18,
          offset: const Offset(0, 10),
        ),
      ];

  static List<BoxShadow> get elevated => [
        BoxShadow(
          color: BYS360Colors.corporateRed.withValues(alpha: .075),
          blurRadius: 28,
          offset: const Offset(0, 16),
        ),
      ];
}

class BYS360Theme {
  static ThemeData get light {
    final scheme = ColorScheme.fromSeed(
      seedColor: BYS360Colors.corporateRed,
      primary: BYS360Colors.corporateRed,
      secondary: BYS360Colors.deepRed,
      surface: BYS360Colors.surface,
    );

    return _baseTheme(
      scheme: scheme,
      scaffoldBackground: BYS360Colors.pageBackground,
      cardColor: Colors.white,
      cardBorder: BYS360Colors.cardBorder,
      textColor: BYS360Colors.ink,
      mutedTextColor: BYS360Colors.mutedText,
      inputFill: Colors.white,
      isDark: false,
    );
  }

  static ThemeData get dark {
    final scheme = ColorScheme.fromSeed(
      seedColor: BYS360Colors.corporateRed,
      brightness: Brightness.dark,
      primary: const Color(0xFFFFB4A8),
      secondary: const Color(0xFFE7BDB3),
      surface: BYS360Colors.darkSurface,
    );

    return _baseTheme(
      scheme: scheme,
      scaffoldBackground: BYS360Colors.darkPage,
      cardColor: BYS360Colors.darkSurface,
      cardBorder: BYS360Colors.darkBorder,
      textColor: BYS360Colors.darkText,
      mutedTextColor: BYS360Colors.darkMutedText,
      inputFill: BYS360Colors.darkSurfaceRaised,
      isDark: true,
    );
  }

  static ThemeData _baseTheme({
    required ColorScheme scheme,
    required Color scaffoldBackground,
    required Color cardColor,
    required Color cardBorder,
    required Color textColor,
    required Color mutedTextColor,
    required Color inputFill,
    required bool isDark,
  }) {
    return ThemeData(
      useMaterial3: true,
      brightness: isDark ? Brightness.dark : Brightness.light,
      colorScheme: scheme,
      scaffoldBackgroundColor: scaffoldBackground,
      fontFamily: 'Roboto',
      textTheme: TextTheme(
        headlineLarge: TextStyle(fontWeight: FontWeight.w900, color: textColor, letterSpacing: -.3, decoration: TextDecoration.none),
        headlineMedium: TextStyle(fontWeight: FontWeight.w900, color: textColor, letterSpacing: -.2, decoration: TextDecoration.none),
        headlineSmall: TextStyle(fontWeight: FontWeight.w900, color: textColor, decoration: TextDecoration.none),
        titleLarge: TextStyle(fontWeight: FontWeight.w900, color: textColor, decoration: TextDecoration.none),
        titleMedium: TextStyle(fontWeight: FontWeight.w800, color: textColor, decoration: TextDecoration.none),
        titleSmall: TextStyle(fontWeight: FontWeight.w800, color: textColor, decoration: TextDecoration.none),
        bodyLarge: TextStyle(height: 1.36, color: textColor, decoration: TextDecoration.none),
        bodyMedium: TextStyle(height: 1.34, color: textColor, decoration: TextDecoration.none),
        bodySmall: TextStyle(height: 1.30, color: mutedTextColor, decoration: TextDecoration.none),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: BYS360Colors.corporateRed,
        foregroundColor: Colors.white,
        centerTitle: false,
        elevation: 0,
        scrolledUnderElevation: 0,
        titleTextStyle: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, decoration: TextDecoration.none),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: cardColor,
        indicatorColor: isDark ? BYS360Colors.darkSurfaceRaised : BYS360Colors.softRed,
        elevation: 0,
        height: 70,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return TextStyle(
            fontWeight: selected ? FontWeight.w900 : FontWeight.w700,
            color: selected ? (isDark ? const Color(0xFFFFD0C8) : BYS360Colors.corporateRed) : mutedTextColor,
            fontSize: 12,
            decoration: TextDecoration.none,
          );
        }),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: inputFill,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
        labelStyle: TextStyle(color: mutedTextColor, fontWeight: FontWeight.w700),
        hintStyle: TextStyle(color: mutedTextColor),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(BYS360Radii.md)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(BYS360Radii.md),
          borderSide: BorderSide(color: cardBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(BYS360Radii.md),
          borderSide: const BorderSide(color: BYS360Colors.corporateRed, width: 1.4),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(BYS360Radii.md),
          borderSide: const BorderSide(color: BYS360Colors.danger, width: 1.2),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: BYS360Colors.corporateRed,
          foregroundColor: Colors.white,
          minimumSize: const Size.fromHeight(50),
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(BYS360Radii.md)),
          textStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 15, decoration: TextDecoration.none),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: isDark ? const Color(0xFFFFD0C8) : BYS360Colors.corporateRed,
          side: BorderSide(color: cardBorder),
          minimumSize: const Size.fromHeight(46),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(BYS360Radii.md)),
          textStyle: const TextStyle(fontWeight: FontWeight.w900, decoration: TextDecoration.none),
        ),
      ),
      cardTheme: CardThemeData(
        color: cardColor,
        elevation: 0,
        margin: const EdgeInsets.symmetric(vertical: 6),
        surfaceTintColor: cardColor,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(BYS360Radii.lg),
          side: BorderSide(color: cardBorder),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: isDark ? BYS360Colors.darkSurfaceRaised : BYS360Colors.ink,
        contentTextStyle: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
    );
  }
}
