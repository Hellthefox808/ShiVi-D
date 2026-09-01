import 'package:flutter/material.dart';

enum FieldVisualMode {
  oledStealth, // True black #000000 for maximum battery preservation on OLED
  directSunlight, // Ultra high-contrast pure white/black for outdoor glare
  nightVision, // Deep red tactical mode to prevent dark-adaptation loss
}

class FieldTheme {
  // Brand & Life-Safety Color Tokens
  static const Color alertCritical = Color(0xFFEF4444); // Red
  static const Color alertWarning = Color(0xFFF59E0B);  // Amber
  static const Color alertSuccess = Color(0xFF10B981);  // Green
  static const Color alertFrozen = Color(0xFF8B5CF6);   // Purple (Conflict Safety Freeze)
  static const Color cyanAccent = Color(0xFF06B6D4);    // Cyan Telemetry
  static const Color primaryBlue = Color(0xFF2563EB);   // Command Blue

  // Touch Target Sizing (Gloved Operation Standard)
  static const double minTouchTarget = 48.0;
  static const double largeTouchTarget = 56.0;

  static ThemeData getTheme(FieldVisualMode mode) {
    switch (mode) {
      case FieldVisualMode.oledStealth:
        return _buildOledTheme();
      case FieldVisualMode.directSunlight:
        return _buildSunlightTheme();
      case FieldVisualMode.nightVision:
        return _buildNightVisionTheme();
    }
  }

  static ThemeData _buildOledTheme() {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: const Color(0xFF000000), // True black saves battery
      cardColor: const Color(0xFF121826),
      primaryColor: primaryBlue,
      colorScheme: const ColorScheme.dark(
        primary: primaryBlue,
        secondary: cyanAccent,
        surface: Color(0xFF121826),
        background: Color(0xFF000000),
        error: alertCritical,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Color(0xFF000000),
        elevation: 0,
        titleTextStyle: TextStyle(
          color: Colors.white,
          fontSize: 18,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.5,
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          minimumSize: const Size(double.infinity, largeTouchTarget),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }

  static ThemeData _buildSunlightTheme() {
    return ThemeData(
      brightness: Brightness.light,
      scaffoldBackgroundColor: const Color(0xFFFFFFFF),
      cardColor: const Color(0xFFF1F5F9),
      primaryColor: const Color(0xFF0F172A),
      colorScheme: const ColorScheme.light(
        primary: Color(0xFF0F172A),
        secondary: Color(0xFF0284C7),
        surface: Color(0xFFF8FAFC),
        background: Color(0xFFFFFFFF),
        error: Color(0xFFDC2626),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Color(0xFF0F172A),
        elevation: 2,
        iconTheme: IconThemeData(color: Colors.white),
        titleTextStyle: TextStyle(
          color: Colors.white,
          fontSize: 18,
          fontWeight: FontWeight.w900,
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF0F172A),
          foregroundColor: Colors.white,
          minimumSize: const Size(double.infinity, largeTouchTarget),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900),
        ),
      ),
    );
  }

  static ThemeData _buildNightVisionTheme() {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: const Color(0xFF0A0000),
      cardColor: const Color(0xFF220000),
      primaryColor: const Color(0xFFFF1744),
      colorScheme: const ColorScheme.dark(
        primary: Color(0xFFFF1744),
        secondary: Color(0xFFFF5252),
        surface: Color(0xFF220000),
        background: Color(0xFF0A0000),
        error: Color(0xFFFF1744),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Color(0xFF150000),
        elevation: 0,
        titleTextStyle: TextStyle(color: Color(0xFFFF1744), fontSize: 18, fontWeight: FontWeight.bold),
      ),
    );
  }
}
