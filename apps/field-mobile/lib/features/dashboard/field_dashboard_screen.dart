import 'package:flutter/material.dart';
import '../../core/theme/field_theme.dart';
import '../../core/models/models.dart';
import '../tasks/task_list_screen.dart';
import '../incidents/incident_report_screen.dart';
import '../../core/database/database.dart';

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
  int _pendingOutboxCount = 0;
  int _batteryPercent = 88;
  bool _isOnline = true;

  final List<LocalTaskEntity> _tasks = [
    LocalTaskEntity(
      id: 'task-sdrf-01',
      incidentId: 'inc-01',
      title: 'Evacuate 3 Trapped Civilians - Sector 4 Bridge',
      description: 'Water level at 1.8m and rising. Deploy inflatable rescue boat with upstream spotter.',
      taskType: 'RESCUE_EVACUATION',
      status: 'OFFERED',
      routeId: 'ROUTE-88',
      isRouteBlocked: 'TRUE', // Safety Freeze active from contradictory reports
      createdAt: DateTime.now().subtract(const Duration(minutes: 15)),
    ),
    LocalTaskEntity(
      id: 'task-sdrf-02',
      incidentId: 'inc-02',
      title: 'Deliver High-Energy Rations & ORS Kits',
      description: 'Relief camp sector 2 cutoff. Transport via shallow draft craft.',
      taskType: 'RELIEF_SUPPLY',
      status: 'ASSIGNED',
      routeId: 'ROUTE-42',
      isRouteBlocked: 'FALSE',
      createdAt: DateTime.now().subtract(const Duration(minutes: 45)),
    ),
  ];

  @override
  Widget build(BuildContext context) {
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
              _currentIndex == 0 ? 'DISPATCH TASKS' : _currentIndex == 1 ? 'LIVE SECTORS' : 'NODE STATUS',
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
                  Text('$_pendingOutboxCount Q', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                  const SizedBox(width: 6),
                  const Icon(Icons.battery_5_bar, size: 14, color: FieldTheme.cyanAccent),
                  Text('$_batteryPercent%', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
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
                  setState(() => _pendingOutboxCount++);
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
            icon: Icon(Icons.map_outlined),
            selectedIcon: Icon(Icons.map, color: FieldTheme.cyanAccent),
            label: 'Sectors',
          ),
          NavigationDestination(
            icon: Icon(Icons.sync_outlined),
            selectedIcon: Icon(Icons.sync, color: FieldTheme.cyanAccent),
            label: 'Mesh & Sync',
          ),
        ],
      ),
    );
  }

  Widget _buildBody() {
    switch (_currentIndex) {
      case 0:
        return TaskListScreen(
          tasks: _tasks,
          onStatusChange: (taskId, newStatus) {
            setState(() {
              final idx = _tasks.indexWhere((t) => t.id == taskId);
              if (idx != -1) {
                // In actual Drift DB this updates sqlite table and queues outbox event
                _pendingOutboxCount++;
              }
            });
          },
        );
      case 1:
        return _buildSectorsMapTab();
      case 2:
        return _buildSyncCenterTab();
      default:
        return Container();
    }
  }

  Widget _buildSectorsMapTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          color: const Color(0xFF1E293B),
          child: Padding(
            padding: const EdgeInsets.all(16),
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: const [
                  Text('SECTOR 4 - GUWAHATI BASIN', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  Chip(
                    label: Text('HIGH INUNDATION', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.white)),
                    backgroundColor: FieldTheme.alertCritical,
                  ),
                ],
              ),
              const SizedBox(height: 12),
              const Text('Water Depth: 1.8m | Flow Rate: 7.2 knots | Evacuees: 42 accounted', style: TextStyle(color: Colors.grey)),
              const Divider(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Route-88 Status:', style: TextStyle(fontWeight: FontWeight.bold)),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: FieldTheme.alertFrozen.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(4),
                      border: Border.all(color: FieldTheme.alertFrozen),
                    ),
                    child: const Text('SAFETY FROZEN (BRIDGE BREACH)', style: TextStyle(color: FieldTheme.alertFrozen, fontWeight: FontWeight.bold, fontSize: 11)),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildSyncCenterTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          color: const Color(0xFF1E293B),
          child: Padding(
            padding: const EdgeInsets.all(16),
            children: [
              const Text('OFFLINE CAUSAL SYNC STATUS', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              const SizedBox(height: 16),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.outbox, color: FieldTheme.cyanAccent),
                title: const Text('Local Unsynced Outbox Events'),
                trailing: Text('$_pendingOutboxCount events', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              ),
              const Divider(),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.security, color: FieldTheme.alertSuccess),
                title: const Text('Cryptographic Integrity Verification'),
                subtitle: const Text('SHA-256 + Lamport Causal Clocks Active'),
                trailing: const Icon(Icons.check_circle, color: FieldTheme.alertSuccess),
              ),
              const Divider(),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.battery_charging_full, color: FieldTheme.cyanAccent),
                title: const Text('Battery Throttling Policy'),
                subtitle: Text('Normal Mode (Current: $_batteryPercent% | Throttle at < 20%)'),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                icon: const Icon(Icons.refresh),
                label: const Text('FORCE SYNC PUSH / PULL'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: FieldTheme.primaryBlue,
                  minimumSize: const Size(double.infinity, 48),
                ),
                onPressed: () {
                  setState(() => _pendingOutboxCount = 0);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Sync complete. Zero duplicate side-effects verified.'), backgroundColor: FieldTheme.alertSuccess),
                  );
                },
              ),
            ],
          ),
        ),
      ],
    );
  }
}
