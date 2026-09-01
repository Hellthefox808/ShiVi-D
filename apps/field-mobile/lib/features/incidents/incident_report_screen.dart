import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';
import '../../core/theme/field_theme.dart';
import '../../core/models/incident_model.dart';

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

  final List<String> _categories = ['RESCUE', 'MEDICAL', 'HAZARD', 'RELIEF'];
  final List<String> _severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

  @override
  void dispose() {
    _titleController.dispose();
    _descController.dispose();
    super.dispose();
  }

  void _handleSubmit() {
    if (_titleController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please enter a brief incident description / title'),
          backgroundColor: FieldTheme.alertWarning,
        ),
      );
      return;
    }

    setState(() => _isSubmitting = true);

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
      priorityScore: _selectedSeverity == 'CRITICAL' ? 85.0 : 50.0,
      createdAt: DateTime.now().toUtc().toIso8601String(),
    );

    widget.onSubmit(newIncident);

    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('REPORT EMERGENCY'),
        actions: [
          IconButton(
            icon: const Icon(Icons.gps_fixed, color: FieldTheme.cyanAccent),
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('GPS Locked: ${_lat.toStringAsFixed(4)}, ${_lon.toStringAsFixed(4)} (Acc: ±3m)')),
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            // Category Selection (Large Chips for Gloved Operation)
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

            // Severity Selection
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

            // Title Input
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
                      style: IconButton.styleFrom(backgroundColor: const Color(0xFF334155), minimumSize: const Size(48, 48)),
                      onPressed: _peopleAtRisk > 1 ? () => setState(() => _peopleAtRisk--) : null,
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Text('$_peopleAtRisk', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: FieldTheme.cyanAccent)),
                    ),
                    IconButton.filled(
                      icon: const Icon(Icons.add),
                      style: IconButton.styleFrom(backgroundColor: FieldTheme.primaryBlue, minimumSize: const Size(48, 48)),
                      onPressed: () => setState(() => _peopleAtRisk++),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Submit Button
            ElevatedButton.icon(
              icon: _isSubmitting ? const CircularProgressIndicator(color: Colors.white) : const Icon(Icons.send),
              label: Text(_isSubmitting ? 'COMMITTING TO OUTBOX...' : 'BROADCAST EMERGENCY (OFFLINE SAFE)'),
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
