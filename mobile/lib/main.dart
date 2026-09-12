import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/field_theme.dart';
import 'features/dashboard/field_dashboard_screen.dart';

/// Briefing: Main entry point for the ShiVi Field Node mobile application.
/// Reason: Every Flutter application requires a `main` function to bootstrap the app.
/// We also use Riverpod for state management, so we wrap the app in a `ProviderScope`.
void main() {
  // Explanation: Ensures that the Flutter binding is initialized before doing any setup.
  // Required when calling native code or platform channels before `runApp`.
  WidgetsFlutterBinding.ensureInitialized();
  
  // Explanation: `runApp` inflates the given widget and attaches it to the screen.
  // `ProviderScope` is required by Riverpod to store the state of the providers.
  runApp(const ProviderScope(child: ShiViFieldApp()));
}

/// Briefing: The root widget of the ShiVi Field application.
/// Reason: It's a Stateful widget because it needs to manage the top-level
/// theme state (`FieldVisualMode`) dynamically.
class ShiViFieldApp extends StatefulWidget {
  const ShiViFieldApp({Key? key}) : super(key: key);

  @override
  State<ShiViFieldApp> createState() => _ShiViFieldAppState();
}

/// Briefing: State class for [ShiViFieldApp].
/// Reason: Holds mutable data (like the current theme mode) and provides
/// a callback to update it from child widgets.
class _ShiViFieldAppState extends State<ShiViFieldApp> {
  // Explanation: Stores the currently selected visual mode for the application.
  // Defaults to `oledStealth` (e.g., a dark theme optimized for OLED screens).
  FieldVisualMode _currentMode = FieldVisualMode.oledStealth;

  /// Explanation: A callback function passed down to children to update the theme.
  /// Reason: When this is called, `setState` triggers a rebuild of the entire `MaterialApp`
  /// with the new theme applied.
  void _handleThemeChange(FieldVisualMode mode) {
    setState(() => _currentMode = mode);
  }

  @override
  Widget build(BuildContext context) {
    // Explanation: `MaterialApp` is the core structure for material design apps.
    // It configures navigation, themes, and locale.
    return MaterialApp(
      title: 'ShiVi Field Node',
      debugShowCheckedModeBanner: false, // Removes the debug banner in the top right corner
      // Dynamically sets the theme based on the current mode using the `FieldTheme` utility
      theme: FieldTheme.getTheme(_currentMode),
      // Sets the initial screen of the application to the FieldDashboardScreen
      home: FieldDashboardScreen(
        currentThemeMode: _currentMode,
        onThemeChanged: _handleThemeChange,
      ),
    );
  }
}
