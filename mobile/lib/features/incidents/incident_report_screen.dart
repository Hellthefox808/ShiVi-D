import 'dart:async';
import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';
import '../../core/theme/field_theme.dart';
import '../../core/models/incident_model.dart';
import '../../core/database/local_database_repository.dart';

class IncidentReportScreen extends StatefulWidget {
  final Function(IncidentModel incident) onSubmit;

  const IncidentReportScreen({Key? key, required this.onSubmit}) : super(key: key);

  @override
  State<IncidentReportScreen> createState() => _IncidentReportScreenState();
}

class _IncidentReportScreenState extends State<IncidentReportScreen> {
  final _titleController = TextEditingController();
  final _descController = TextEditingController();
  String _selectedCategory = 'RESCUE';
  String _selectedSeverity = 'CRITICAL';
  int _peopleAtRisk = 3;
  double _lat = 26.1856;
  double _lon = 91.7483;
  bool _isSubmitting = false;

  // Voice recording simulation
  bool _isRecordingVoice = false;
  int _recordingSeconds = 0;
  Timer? _recordingTimer;

  final List<String> _categories = ['RESCUE', 'MEDICAL', 'HAZARD', 'RELIEF'];
  final List<String> _severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

  @override
  void dispose() {
    _titleController.dispose();
    _descController.dispose();
    _recordingTimer?.cancel();
    super.dispose();
  }

  double get _currentPriorityScore {
    return LocalDatabaseRepository.calculatePriorityScore(
      category: _selectedCategory,
      severity: _selectedSeverity,
      peopleAtRisk: _peopleAtRisk,
    );
  }

  void _applyQuickPreset(String title, String category, String severity, int people) {
    setState(() {
      _titleController.text = title;
      _selectedCategory = category;
      _selectedSeverity = severity;
      _peopleAtRisk = people;
    });
  }

  void _toggleVoiceRecording() {
    if (_isRecordingVoice) {
      _recordingTimer?.cancel();
      setState(() {
        _isRecordingVoice = false;
        if (_descController.text.isEmpty) {
          _descController.text = '[Audio Note attached: ${_recordingSeconds}s distress voice capture]';
        }
      });
    } else {
      setState(() {
        _isRecordingVoice = true;
        _recordingSeconds = 0;
      });
      _recordingTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
        setState(() => _recordingSeconds++);
      });
    }
  }

  void _handleSubmit() {
    if (_titleController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please enter an incident summary or select a quick SOS preset'),
          backgroundColor: FieldTheme.alertWarning,
        ),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    final score = _currentPriorityScore;
    final newIncident = IncidentModel(
      id: const Uuid().v4(),
      tenantId: '00000000-0000-0000-0000-000000000001',
      title: _titleController.text.trim(),
      description: _descController.text.trim().isEmpty ? null : _descController.text.trim(),
      category: _selectedCategory,
      severity: _selectedSeverity,
      status: 'REPORTED',
      latitude: _lat,
      longitude: _lon,
      peopleAtRisk: _peopleAtRisk,
      priorityScore: score,
      createdAt: DateTime.now().toUtc().toIso8601String(),
    );

    widget.onSubmit(newIncident);
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final score = _currentPriorityScore;

    return Scaffold(
      appBar: AppBar(
        title: const Text('CAPTURE EMERGENCY SOS'),
        actions: [
          IconButton(
            icon: const Icon(Icons.gps_fixed, color: FieldTheme.cyanAccent),
            tooltip: 'GPS Locked',
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('GPS Locked: ${_lat.toStringAsFixed(4)}, ${_lon.toStringAsFixed(4)} (Accuracy ±3m)'),
                  backgroundColor: const Color(0xFF1E293B),
                ),
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            // Quick Tactical SOS Presets
            const Text(
              'QUICK TACTICAL PRESETS (ONE-TOUCH)',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Colors.grey),
            ),
            const SizedBox(height: 8),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  ActionChip(
                    avatar: const Icon(Icons.roofing, size: 18, color: Colors.orangeAccent),
                    label: const Text('Rooftop Flooding'),
                    backgroundColor: const Color(0xFF1E293B),
                    onPressed: () => _applyQuickPreset(
                      '3 Civilians Trapped on Rooftop - Rising Water',
                      'RESCUE',
                      'CRITICAL',
                      3,
                    ),
                  ),
                  const SizedBox(width: 8),
                  ActionChip(
                    avatar: const Icon(Icons.medical_services, size: 18, color: Colors.redAccent),
                    label: const Text('Critical Medical'),
                    backgroundColor: const Color(0xFF1E293B),
                    onPressed: () => _applyQuickPreset(
                      'Diabetic Shock & Severe Dehydration - Sector 2',
                      'MEDICAL',
                      'CRITICAL',
                      1,
                    ),
                  ),
                  const SizedBox(width: 8),
                  ActionChip(
                    avatar: const Icon(Icons.warning, size: 18, color: Colors.amberAccent),
                    label: const Text('Bridge Submerged'),
                    backgroundColor: const Color(0xFF1E293B),
                    onPressed: () => _applyQuickPreset(
                      'Sector 4 Bridge Overtopped - Flow Rate Severe',
                      'HAZARD',
                      'HIGH',
                      0,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Live Priority Score Card
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: score >= 70
                    ? const Color(0xFF450A0A)
                    : (score >= 40 ? const Color(0xFF422006) : const Color(0xFF064E3B)),
                borderRadius: BorderRadius.circular(8),
                border: Border.Border.all(
                  color: score >= 70 ? Colors.redAccent : Colors.cyanAccent,
                  width: 1.5,
                ),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.black38,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      score.toStringAsFixed(1),
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Text(
                              'CALCULATED PRIORITY: ',
                              style: TextStyle(fontSize: 11, color: Colors.white70),
                            ),
                            Text(
                              score >= 70 ? 'P0 (CRITICAL)' : (score >= 40 ? 'P1 (URGENT)' : 'P2 (ROUTINE)'),
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: score >= 70 ? Colors.redAccent : Colors.cyanAccent,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'Cat($_selectedCategory) + Sev($_selectedSeverity) + People($_peopleAtRisk)',
                          style: const TextStyle(fontSize: 11, color: Colors.white60),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Emergency Category
            const Text('EMERGENCY CATEGORY', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.grey)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _categories.map((cat) {
                final isSelected = _selectedCategory == cat;
                return ChoiceChip(
                  label: Text(cat, style: TextStyle(fontWeight: FontWeight.bold, color: isSelected ? Colors.white : Colors.grey[400])),
                  selected: isSelected,
                  selectedColor: FieldTheme.primaryBlue,
                  backgroundColor: const Color(0xFF1E293B),
                  onSelected: (selected) {
                    if (selected) setState(() => _selectedCategory = cat);
                  },
                );
              }).toList(),
            ),
            const SizedBox(height: 16),

            // Severity Level
            const Text('SEVERITY LEVEL', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.grey)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _severities.map((sev) {
                final isSelected = _selectedSeverity == sev;
                Color chipColor = FieldTheme.primaryBlue;
                if (sev == 'CRITICAL') chipColor = FieldTheme.alertCritical;
                if (sev == 'HIGH') chipColor = FieldTheme.alertWarning;

                return ChoiceChip(
                  label: Text(sev, style: TextStyle(fontWeight: FontWeight.bold, color: isSelected ? Colors.white : Colors.grey[400])),
                  selected: isSelected,
                  selectedColor: chipColor,
                  backgroundColor: const Color(0xFF1E293B),
                  onSelected: (selected) {
                    if (selected) setState(() => _selectedSeverity = sev);
                  },
                );
              }).toList(),
            ),
            const SizedBox(height: 16),

            // Summary Title Input
            TextField(
              controller: _titleController,
              maxLines: 2,
              style: const TextStyle(fontSize: 16),
              decoration: InputDecoration(
                labelText: 'Incident Summary / Location',
                hintText: 'e.g. Sector 4 Bridge breach, 3 trapped on roof',
                filled: true,
                fillColor: const Color(0xFF1E293B),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
              ),
            ),
            const SizedBox(height: 12),

            // Voice Distress Capture Button
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    icon: Icon(
                      _isRecordingVoice ? Icons.stop_circle : Icons.mic,
                      color: _isRecordingVoice ? Colors.redAccent : Colors.cyanAccent,
                    ),
                    label: Text(
                      _isRecordingVoice ? 'STOP RECORDING (${_recordingSeconds}s)' : 'RECORD VOICE DISTRESS',
                      style: TextStyle(
                        color: _isRecordingVoice ? Colors.redAccent : Colors.cyanAccent,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    style: OutlinedButton.styleFrom(
                      side: BorderSide(color: _isRecordingVoice ? Colors.redAccent : Colors.cyanAccent),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    onPressed: _toggleVoiceRecording,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // People Count Counter
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('PEOPLE AT RISK:', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                Row(
                  children: [
                    IconButton.filled(
                      icon: const Icon(Icons.remove),
                      style: IconButton.styleFrom(
                        backgroundColor: const Color(0xFF334155),
                        minimumSize: const Size(48, 48),
                      ),
                      onPressed: _peopleAtRisk > 0 ? () => setState(() => _peopleAtRisk--) : null,
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Text(
                        '$_peopleAtRisk',
                        style: const TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                          color: FieldTheme.cyanAccent,
                        ),
                      ),
                    ),
                    IconButton.filled(
                      icon: const Icon(Icons.add),
                      style: IconButton.styleFrom(
                        backgroundColor: FieldTheme.primaryBlue,
                        minimumSize: const Size(48, 48),
                      ),
                      onPressed: () => setState(() => _peopleAtRisk++),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Submit Button
            ElevatedButton.icon(
              icon: _isSubmitting
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                    )
                  : const Icon(Icons.send),
              label: Text(
                _isSubmitting
                    ? 'COMMITTING TO LOCAL OUTBOX...'
                    : 'COMMIT & BROADCAST (OFFLINE DURABLE)',
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: _selectedSeverity == 'CRITICAL' ? FieldTheme.alertCritical : FieldTheme.primaryBlue,
                minimumSize: const Size(double.infinity, 56),
              ),
              onPressed: _isSubmitting ? null : _handleSubmit,
            ),
          ],
        ),
      ),
    );
  }
}
