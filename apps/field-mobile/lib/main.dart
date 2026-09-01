import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/field_theme.dart';
import 'features/dashboard/field_dashboard_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ProviderScope(child: ShiViFieldApp()));
}

class ShiViFieldApp extends StatefulWidget {
  const ShiViFieldApp({Key? key}) : super(key: key);

  @override
  State<ShiViFieldApp> createState() => _ShiViFieldAppState();
}

class _ShiViFieldAppState extends State<ShiViFieldApp> {
  FieldVisualMode _currentMode = FieldVisualMode.oledStealth;

  void _handleThemeChange(FieldVisualMode mode) {
    setState(() => _currentMode = mode);
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ShiVi Field Node',
      debugShowCheckedModeBanner: false,
      theme: FieldTheme.getTheme(_currentMode),
      home: FieldDashboardScreen(
        currentThemeMode: _currentMode,
        onThemeChanged: _handleThemeChange,
      ),
    );
  }
}
