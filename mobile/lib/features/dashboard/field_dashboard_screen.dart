import 'package:flutter/material.dart';
import '../../core/theme/field_theme.dart';
import '../../core/models/models.dart';
import '../tasks/task_list_screen.dart';
import '../incidents/incident_report_screen.dart';
import '../map/tactical_map_screen.dart';
import '../mesh/mesh_radar_screen.dart';
import '../audit/audit_inspector_screen.dart';
import '../../core/database/database.dart';
import '../../core/database/local_database_repository.dart';
import '../../core/network/api_service.dart';

class FieldDashboardScreen extends StatefulWidget {
  final Function(FieldVisualMode mode) onThemeChanged;
  final FieldVisualMode currentThemeMode;

  const FieldDashboardScreen({
    Key? key,
    required this.onThemeChanged,
    required this.currentThemeMode,
  }) : super(key: key);

  @override
  State<FieldDashboardScreen> createState() => _FieldDashboardScreenState();
}

class _FieldDashboardScreenState extends State<FieldDashboardScreen> {
  int _currentIndex = 0;
  final int _batteryPercent = 88;
  bool _isOnline = true;
  bool _isSyncing = false;

  late final LocalDatabaseRepository _repository;
  late final ApiService _apiService;

  @override
  void initState() {
    super.initState();
    _repository = LocalDatabaseRepository(deviceId: 'NODE-SDRF-01');
    _apiService = ApiService();
  }

  void _handleSyncOutbox() async {
    setState(() => _isSyncing = true);

    final flushed = await _repository.flushOutbox(_apiService);
    final isBackendAlive = await _apiService.checkHealth();

    setState(() {
      _isSyncing = false;
      _isOnline = isBackendAlive;
    });

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            flushed > 0
                ? 'Pushed $flushed outbox mutations to central command. Zero duplicate side-effects.'
                : (_repository.pendingOutboxCount == 0
                    ? 'All outbox records up-to-date. Zero pending mutations.'
                    : 'Offline: ${_repository.pendingOutboxCount} mutations retained durably in local SQLite outbox.'),
          ),
          backgroundColor: flushed > 0 || _repository.pendingOutboxCount == 0
              ? FieldTheme.alertSuccess
              : FieldTheme.alertWarning,
        ),
      );
    }
  }

  void _handleSimulationTrigger() async {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Triggering P0 8-Phase Disaster Workflow Simulation...'),
        backgroundColor: Colors.blueAccent,
      ),
    );

    final res = await _apiService.triggerSimulation();
    if (res != null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Simulation Succeeded: ${res["summary"]}'),
          backgroundColor: FieldTheme.alertSuccess,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final pendingCount = _repository.pendingOutboxCount;

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: FieldTheme.primaryBlue.withOpacity(0.3),
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: FieldTheme.primaryBlue),
              ),
              child: const Text('SHIVI NODE', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.0)),
            ),
            const SizedBox(width: 8),
            Text(
              _currentIndex == 0
                  ? 'DISPATCH TASKS'
                  : _currentIndex == 1
                      ? 'TACTICAL RADAR'
                      : _currentIndex == 2
                          ? 'MESH & SYNC'
                          : 'AUDIT LEDGER',
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
            ),
          ],
        ),
        actions: [
          // Battery & Sync Pill
          Center(
            child: Container(
              margin: const EdgeInsets.only(right: 8),
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFF1E293B),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    _isOnline ? Icons.cloud_done : Icons.cloud_off,
                    size: 14,
                    color: _isOnline ? FieldTheme.alertSuccess : FieldTheme.alertWarning,
                  ),
                  const SizedBox(width: 4),
                  Text('$pendingCount Q', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                  const SizedBox(width: 6),
                  const Icon(Icons.battery_5_bar, size: 14, color: FieldTheme.cyanAccent),
                  Text('$_batteryPercent%', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
          ),

          IconButton(
            icon: const Icon(Icons.play_circle_outline, color: FieldTheme.cyanAccent),
            tooltip: 'Trigger P0 Disaster Simulation',
            onPressed: _handleSimulationTrigger,
          ),

          // Theme Switcher Menu
          PopupMenuButton<FieldVisualMode>(
            icon: const Icon(Icons.brightness_medium),
            tooltip: 'Visual Profile',
            onSelected: widget.onThemeChanged,
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: FieldVisualMode.oledStealth,
                child: Text('OLED Battery Saver (True Black)'),
              ),
              const PopupMenuItem(
                value: FieldVisualMode.directSunlight,
                child: Text('Direct Sunlight (High Contrast)'),
              ),
              const PopupMenuItem(
                value: FieldVisualMode.nightVision,
                child: Text('Night Vision (Tactical Red)'),
              ),
            ],
          ),
        ],
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: FieldTheme.alertCritical,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.add_alert),
        label: const Text('REPORT EMERGENCY', style: TextStyle(fontWeight: FontWeight.bold)),
        onPressed: () {
          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => IncidentReportScreen(
                onSubmit: (newIncident) {
                  setState(() {
                    _repository.recordIncident(
                      title: newIncident.title,
                      description: newIncident.description ?? '',
                      category: newIncident.category,
                      severity: newIncident.severity,
                      peopleAtRisk: newIncident.peopleAtRisk,
                      latitude: newIncident.latitude,
                      longitude: newIncident.longitude,
                    );
                  });
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Incident "${newIncident.title}" committed to local outbox.'),
                      backgroundColor: FieldTheme.alertSuccess,
                    ),
                  );
                },
              ),
            ),
          );
        },
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (idx) => setState(() => _currentIndex = idx),
        backgroundColor: const Color(0xFF0F172A),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.assignment_outlined),
            selectedIcon: Icon(Icons.assignment, color: FieldTheme.cyanAccent),
            label: 'Tasks',
          ),
          NavigationDestination(
            icon: Icon(Icons.radar_outlined),
            selectedIcon: Icon(Icons.radar, color: FieldTheme.cyanAccent),
            label: 'Radar',
          ),
          NavigationDestination(
            icon: Icon(Icons.hub_outlined),
            selectedIcon: Icon(Icons.hub, color: FieldTheme.cyanAccent),
            label: 'Mesh P2P',
          ),
          NavigationDestination(
            icon: Icon(Icons.security_outlined),
            selectedIcon: Icon(Icons.security, color: FieldTheme.cyanAccent),
            label: 'Audit Log',
          ),
        ],
      ),
    );
  }

  Widget _buildBody() {
    switch (_currentIndex) {
      case 0:
        return TaskListScreen(
          tasks: _repository.tasks,
          onStatusChange: (taskId, newStatus) {
            setState(() {
              _repository.updateTaskStatus(taskId, newStatus);
            });
          },
          onCompleteWithEvidence: (taskId, sha256Proof, lat, lon, note) {
            setState(() {
              _repository.completeTaskWithEvidence(
                taskId: taskId,
                sha256Hash: sha256Proof,
                latitude: lat,
                longitude: lon,
                notes: note,
              );
            });
          },
        );
      case 1:
        return TacticalMapScreen(
          incidents: _repository.incidents,
        );
      case 2:
        return MeshRadarScreen(
          repository: _repository,
          apiService: _apiService,
          onStateChanged: () => setState(() {}),
        );
      case 3:
        return AuditInspectorScreen(
          repository: _repository,
        );
      default:
        return Container();
    }
  }

}

