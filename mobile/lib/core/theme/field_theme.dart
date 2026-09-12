import 'package:flutter/material.dart';

/// Briefing: Operating display modes designed for extreme field conditions.
/// Reason: Responders encounter harsh physical environments: blinding outdoor sun, pitch-black night missions,
/// and low-battery emergencies where screen backlight power must be conserved.
enum FieldVisualMode {
  // Explanation: True black #000000 background shuts off OLED subpixels completely to preserve battery over 48+ hour deployments.
  oledStealth,
  // Explanation: Maximum contrast light theme (pure white background, deep ink text) engineered to defeat glare in direct sunlight.
  directSunlight,
  // Explanation: Deep monochromatic red spectrum preventing dark-adaptation loss and rod-cell fatigue during night searches.
  nightVision,
}

/// Briefing: Field Ergonomics and Life-Safety Theme System for ShiVi Mobile.
/// Reason: Emergency UIs must be legible under stress, operational with thick hazmat/firefighting gloves,
/// and instantly communicative of hazard states through deterministic color coding.
class FieldTheme {
  // Explanation: Critical life-safety emergency alert (immediate evacuation, active hazard)
  static const Color alertCritical = Color(0xFFEF4444); // Red
  // Explanation: Warning condition requiring operator attention or caution
  static const Color alertWarning = Color(0xFFF59E0B);  // Amber
  // Explanation: Nominal state, successful synchronization, or resolved task
  static const Color alertSuccess = Color(0xFF10B981);  // Green
  // Explanation: Causal Safety Freeze active (concurrent conflict awaiting supervisor adjudication)
  static const Color alertFrozen = Color(0xFF8B5CF6);   // Purple (Conflict Safety Freeze)
  // Explanation: Telemetry and sensor data indicator
  static const Color cyanAccent = Color(0xFF06B6D4);    // Cyan Telemetry
  // Explanation: Primary incident command authority accent
  static const Color primaryBlue = Color(0xFF2563EB);   // Command Blue

  // Touch Target Sizing (Gloved Operation Standard)
  // Explanation: Minimum tap target size in dp for gloved operation (ISO/OSHA safety standards)
  static const double minTouchTarget = 48.0;
  // Explanation: Expanded tap target size for rapid-action buttons under high-stress field scenarios
  static const double largeTouchTarget = 56.0;

  /// Briefing: Resolves and builds a full Flutter [ThemeData] tailored to the selected [FieldVisualMode].
  /// Reason: Dynamically switches the UI palette at runtime when ambient sensors or user switches modes.
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

  /// Briefing: Assembles the OLED stealth theme with 0-nit true black backgrounds.
  /// Reason: Preserves maximum mAh battery life on AMOLED/OLED displays during protracted rescue operations.
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

  /// Briefing: Assembles high-contrast light theme for direct midday sunlight.
  /// Reason: Mitigates screen reflection and glare when responders operate outdoors without shade.
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

  /// Briefing: Assembles tactical red-spectrum theme for night operations.
  /// Reason: Preserves visual rhodopsin and scotopic vision, allowing personnel to look from screen to dark terrain without blindness.
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
