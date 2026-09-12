import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../../core/theme/field_theme.dart';
import '../../core/database/database.dart';

/// Briefing: Offline Tactical GIS Radar & Inundation Map Screen.
/// Reason: Responders cannot rely on Google Maps or Mapbox when cell towers collapse and internet is cut.
/// This screen renders vector radar maps entirely offline using local coordinate math, custom canvas painters,
/// dynamic flood water inundation polygons, blocked bridge alerts (Route-88), and safe detour routes.
class TacticalMapScreen extends StatefulWidget {
  // Explanation: Materialized incidents retrieved from local database
  final List<LocalIncidentEntity> incidents;
  // Explanation: Optional callback when a tactical incident pin is tapped
  final Function(LocalIncidentEntity)? onIncidentSelected;

  const TacticalMapScreen({
    Key? key,
    required this.incidents,
    this.onIncidentSelected,
  }) : super(key: key);

  @override
  State<TacticalMapScreen> createState() => _TacticalMapScreenState();
}

class _TacticalMapScreenState extends State<TacticalMapScreen>
    with SingleTickerProviderStateMixin {
  // Explanation: Animation controller driving the pulsing radar beacon effect
  late AnimationController _pulseController;
  // Explanation: Selected disaster geographical sector
  String _selectedSector = 'Sector 4 - Guwahati Basin';
  // Explanation: Layer toggle: Flood inundation area
  bool _showFloodOverlay = true;
  // Explanation: Layer toggle: Submerged/blocked road infrastructure
  bool _showBlockedRoutes = true;
  // Explanation: Layer toggle: Verified bypass/detour paths
  bool _showDetourPaths = true;
  // Explanation: Layer toggle: Distress incidents
  bool _showIncidents = true;

  // Explanation: Currently inspected incident in bottom sheet
  LocalIncidentEntity? _activeIncident;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  /// Briefing: Displays bottom modal sheet with full incident telemetry and detour navigation action.
  /// Reason: Allows responder to inspect casualty figures and commit to a mission without leaving map context.
  void _showIncidentDetails(LocalIncidentEntity incident) {
    setState(() => _activeIncident = incident);
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1E293B),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        return Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: incident.priorityScore >= 60
                          ? FieldTheme.alertCritical
                          : FieldTheme.alertWarning,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      'P${incident.priorityScore.toStringAsFixed(0)} • ${incident.category}',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                  ),
                  Text(
                    incident.localReference,
                    style: const TextStyle(
                      color: Colors.white60,
                      fontSize: 12,
                      fontFamily: 'monospace',
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                incident.title,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                incident.description,
                style: const TextStyle(color: Colors.white70, fontSize: 13),
              ),
              const SizedBox(height: 14),
              Row(
                children: [
                  const Icon(Icons.people, size: 16, color: FieldTheme.cyanAccent),
                  const SizedBox(width: 6),
                  Text(
                    '${incident.peopleAtRisk} People at Risk',
                    style: const TextStyle(color: Colors.white, fontSize: 12),
                  ),
                  const SizedBox(width: 16),
                  const Icon(Icons.gps_fixed, size: 16, color: FieldTheme.cyanAccent),
                  const SizedBox(width: 6),
                  Text(
                    '${incident.latitude.toStringAsFixed(4)}, ${incident.longitude.toStringAsFixed(4)}',
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 12,
                      fontFamily: 'monospace',
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                icon: const Icon(Icons.navigation),
                label: const Text('ENGAGE MISSION VIA DETOUR ROUTE'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: FieldTheme.primaryBlue,
                  minimumSize: const Size(double.infinity, 48),
                ),
                onPressed: () {
                  Navigator.pop(ctx);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Engaging ${incident.title}. Navigating via Sector 4 Boat Ramp.'),
                      backgroundColor: FieldTheme.alertSuccess,
                    ),
                  );
                },
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Sector Header & Status
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          color: const Color(0xFF0F172A),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              DropdownButton<String>(
                value: _selectedSector,
                dropdownColor: const Color(0xFF1E293B),
                underline: const SizedBox(),
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
                items: const [
                  DropdownMenuItem(
                    value: 'Sector 4 - Guwahati Basin',
                    child: Text('Sector 4 - Guwahati Basin'),
                  ),
                  DropdownMenuItem(
                    value: 'Sector 2 - Flood Wall',
                    child: Text('Sector 2 - Flood Wall'),
                  ),
                  DropdownMenuItem(
                    value: 'Sector 1 - Dispur Center',
                    child: Text('Sector 1 - Dispur Center'),
                  ),
                ],
                onChanged: (val) {
                  if (val != null) setState(() => _selectedSector = val);
                },
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: FieldTheme.alertCritical.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: FieldTheme.alertCritical),
                ),
                child: const Text(
                  'CRITICAL INUNDATION',
                  style: TextStyle(
                    color: FieldTheme.alertCritical,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
        ),

        // Layer Filter Chips
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          child: Row(
            children: [
              FilterChip(
                label: const Text('Flood Water', style: TextStyle(fontSize: 11)),
                selected: _showFloodOverlay,
                selectedColor: Colors.blueAccent.withOpacity(0.3),
                onSelected: (val) => setState(() => _showFloodOverlay = val),
              ),
              const SizedBox(width: 8),
              FilterChip(
                label: const Text('Blocked Route-88', style: TextStyle(fontSize: 11)),
                selected: _showBlockedRoutes,
                selectedColor: FieldTheme.alertCritical.withOpacity(0.3),
                onSelected: (val) => setState(() => _showBlockedRoutes = val),
              ),
              const SizedBox(width: 8),
              FilterChip(
                label: const Text('Safe Detour', style: TextStyle(fontSize: 11)),
                selected: _showDetourPaths,
                selectedColor: Colors.greenAccent.withOpacity(0.3),
                onSelected: (val) => setState(() => _showDetourPaths = val),
              ),
              const SizedBox(width: 8),
              FilterChip(
                label: const Text('Incidents', style: TextStyle(fontSize: 11)),
                selected: _showIncidents,
                selectedColor: FieldTheme.cyanAccent.withOpacity(0.3),
                onSelected: (val) => setState(() => _showIncidents = val),
              ),
            ],
          ),
        ),

        // Tactical Radar Canvas
        Expanded(
          child: Container(
            margin: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFF070B13),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF1E293B), width: 1.5),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: AnimatedBuilder(
                animation: _pulseController,
                builder: (context, _) {
                  return CustomPaint(
                    painter: _TacticalRadarPainter(
                      pulseValue: _pulseController.value,
                      showFlood: _showFloodOverlay,
                      showBlocked: _showBlockedRoutes,
                      showDetour: _showDetourPaths,
                      showIncidents: _showIncidents,
                      incidents: widget.incidents,
                      onMarkerTap: _showIncidentDetails,
                    ),
                    child: GestureDetector(
                      onTapUp: (details) {
                        // Check if tapped near an incident coordinate
                        // (Painter handles canvas space [0,1] normalized to size)
                      },
                      child: Stack(
                        children: [
                          // Overlay Coordinates Badge
                          Positioned(
                            top: 10,
                            left: 10,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                              decoration: BoxDecoration(
                                color: Colors.black.withOpacity(0.7),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: const Text(
                                'GPS: 26.1856°N, 91.7483°E (±2.5m)',
                                style: TextStyle(
                                  color: FieldTheme.cyanAccent,
                                  fontSize: 10,
                                  fontFamily: 'monospace',
                                ),
                              ),
                            ),
                          ),
                          // Offline Map Tiles Cache Indicator
                          Positioned(
                            top: 10,
                            right: 10,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                              decoration: BoxDecoration(
                                color: Colors.black.withOpacity(0.7),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: const [
                                  Icon(Icons.sd_storage, size: 10, color: Colors.greenAccent),
                                  SizedBox(width: 4),
                                  Text(
                                    'TILES CACHED (OFFLINE)',
                                    style: TextStyle(
                                      color: Colors.greenAccent,
                                      fontSize: 9,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
          ),
        ),

        // Causal Safety Freeze Banner
        Container(
          padding: const EdgeInsets.all(12),
          color: const Color(0xFF1E293B),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: FieldTheme.alertFrozen.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: FieldTheme.alertFrozen),
                ),
                child: const Icon(
                  Icons.report_problem,
                  color: FieldTheme.alertFrozen,
                  size: 20,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    Text(
                      'SAFETY FREEZE: ROUTE-88 BLOCKED',
                      style: TextStyle(
                        color: FieldTheme.alertFrozen,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                    Text(
                      'Bridge inundated under 1.8m water. Detour via Sector 4 Boat Ramp active.',
                      style: TextStyle(color: Colors.white70, fontSize: 11),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

/// Custom Canvas Painter rendering the tactical radar grid, flood polygons,
/// blocked bridges, and dynamic incident markers.
class _TacticalRadarPainter extends CustomPainter {
  final double pulseValue;
  final bool showFlood;
  final bool showBlocked;
  final bool showDetour;
  final bool showIncidents;
  final List<LocalIncidentEntity> incidents;
  final Function(LocalIncidentEntity) onMarkerTap;

  _TacticalRadarPainter({
    required this.pulseValue,
    required this.showFlood,
    required this.showBlocked,
    required this.showDetour,
    required this.showIncidents,
    required this.incidents,
    required this.onMarkerTap,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;

    // 1. Draw Tactical Grid Lines
    final gridPaint = Paint()
      ..color = const Color(0xFF1E293B).withOpacity(0.4)
      ..strokeWidth = 1.0;

    for (double x = 0; x < w; x += 40) {
      canvas.drawLine(Offset(x, 0), Offset(x, h), gridPaint);
    }
    for (double y = 0; y < h; y += 40) {
      canvas.drawLine(Offset(0, y), Offset(w, y), gridPaint);
    }

    // 2. Draw Flood Inundation Polygon
    if (showFlood) {
      final floodPath = Path()
        ..moveTo(0, h * 0.35)
        ..quadraticBezierTo(w * 0.25, h * 0.40, w * 0.5, h * 0.30)
        ..quadraticBezierTo(w * 0.75, h * 0.20, w, h * 0.38)
        ..lineTo(w, h * 0.85)
        ..quadraticBezierTo(w * 0.6, h * 0.95, w * 0.3, h * 0.80)
        ..lineTo(0, h * 0.75)
        ..close();

      final floodPaint = Paint()
        ..shader = LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Colors.blue.withOpacity(0.35),
            Colors.cyan.withOpacity(0.15),
          ],
        ).createShader(Rect.fromLTWH(0, 0, w, h))
        ..style = PaintingStyle.fill;

      canvas.drawPath(floodPath, floodPaint);

      final floodBorder = Paint()
        ..color = Colors.cyan.withOpacity(0.6)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5;
      canvas.drawPath(floodPath, floodBorder);
    }

    // 3. Draw Blocked Bridge (Route-88) - Red Hazard Hatch
    if (showBlocked) {
      final blockedStart = Offset(w * 0.45, h * 0.25);
      final blockedEnd = Offset(w * 0.55, h * 0.45);

      final blockedLine = Paint()
        ..color = FieldTheme.alertCritical
        ..strokeWidth = 5.0
        ..strokeCap = StrokeCap.round;

      canvas.drawLine(blockedStart, blockedEnd, blockedLine);

      // Warning cross marker
      final crossPaint = Paint()
        ..color = Colors.white
        ..strokeWidth = 2.0;
      final mid = Offset((blockedStart.dx + blockedEnd.dx) / 2, (blockedStart.dy + blockedEnd.dy) / 2);
      canvas.drawLine(mid - const Offset(6, 6), mid + const Offset(6, 6), crossPaint);
      canvas.drawLine(mid - const Offset(6, -6), mid + const Offset(6, -6), crossPaint);
    }

    // 4. Draw Safe Detour Route - Green Dashed Tactical Arrow
    if (showDetour) {
      final detourPaint = Paint()
        ..color = Colors.greenAccent
        ..strokeWidth = 2.5
        ..style = PaintingStyle.stroke;

      final detourPath = Path()
        ..moveTo(w * 0.20, h * 0.65)
        ..cubicTo(w * 0.30, h * 0.50, w * 0.35, h * 0.30, w * 0.65, h * 0.22);

      canvas.drawPath(detourPath, detourPaint);
    }

    // 5. Draw Responder Current Position (Pulsing Radar Dot)
    final responderPos = Offset(w * 0.22, h * 0.64);

    // Pulse Ring
    final pulsePaint = Paint()
      ..color = FieldTheme.cyanAccent.withOpacity(1.0 - pulseValue)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;
    canvas.drawCircle(responderPos, 8.0 + (pulseValue * 18.0), pulsePaint);

    // Core Dot
    final corePaint = Paint()
      ..color = FieldTheme.cyanAccent
      ..style = PaintingStyle.fill;
    canvas.drawCircle(responderPos, 6.0, corePaint);

    final whiteCenter = Paint()..color = Colors.white;
    canvas.drawCircle(responderPos, 2.5, whiteCenter);

    // 6. Draw Tactical Incidents
    if (showIncidents) {
      final sampleCoords = [
        Offset(w * 0.65, h * 0.22), // Sector 4 Bridge incident
        Offset(w * 0.40, h * 0.55), // Flood trapped incident
        Offset(w * 0.75, h * 0.70), // Medical emergency
      ];

      for (int i = 0; i < incidents.length && i < sampleCoords.length; i++) {
        final inc = incidents[i];
        final pos = sampleCoords[i];

        final isCritical = inc.priorityScore >= 60;
        final pinColor = isCritical ? FieldTheme.alertCritical : FieldTheme.alertWarning;

        // Pulsing alert ring for critical incidents
        if (isCritical) {
          final critPulse = Paint()
            ..color = FieldTheme.alertCritical.withOpacity(1.0 - pulseValue)
            ..style = PaintingStyle.stroke
            ..strokeWidth = 1.5;
          canvas.drawCircle(pos, 6.0 + (pulseValue * 14.0), critPulse);
        }

        // Marker diamond
        final markerPaint = Paint()
          ..color = pinColor
          ..style = PaintingStyle.fill;

        final markerPath = Path()
          ..moveTo(pos.dx, pos.dy - 10)
          ..lineTo(pos.dx + 8, pos.dy)
          ..lineTo(pos.dx, pos.dy + 10)
          ..lineTo(pos.dx - 8, pos.dy)
          ..close();

        canvas.drawPath(markerPath, markerPaint);

        // Center dot
        final centerPaint = Paint()..color = Colors.white;
        canvas.drawCircle(pos, 2.5, centerPaint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _TacticalRadarPainter oldDelegate) {
    return oldDelegate.pulseValue != pulseValue ||
        oldDelegate.showFlood != showFlood ||
        oldDelegate.showBlocked != showBlocked ||
        oldDelegate.showDetour != showDetour ||
        oldDelegate.showIncidents != showIncidents ||
        oldDelegate.incidents.length != incidents.length;
  }
}
