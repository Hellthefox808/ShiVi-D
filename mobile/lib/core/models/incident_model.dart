import 'dart:convert';
import 'package:flutter/foundation.dart';

/// Briefing: Represents an emergency incident reported in the system.
/// Reason: Serves as the core data transfer object for incident tracking. It contains 
/// all geographical and metadata information required to display incidents on maps and dashboards.
class IncidentModel {
  // Explanation: Unique identifier for the incident
  final String id;
  // Explanation: The organization or tenant ID this incident belongs to
  final String tenantId;
  // Explanation: A short title describing the incident (e.g., "Fire at Main St")
  final String title;
  // Explanation: Additional context or details about the incident
  final String? description;
  // Explanation: Type of incident (e.g., MEDICAL, FIRE, GENERAL)
  final String category;
  // Explanation: How severe the incident is (e.g., LOW, MEDIUM, CRITICAL)
  final String severity;
  // Explanation: Current lifecycle status of the incident (e.g., REPORTED, RESOLVED)
  final String status;
  // Explanation: Geographical latitude coordinate
  final double latitude;
  // Explanation: Geographical longitude coordinate
  final double longitude;
  // Explanation: Estimated number of people at risk
  final int peopleAtRisk;
  // Explanation: Calculated score determining triage priority
  final double priorityScore;
  // Explanation: Timestamp when the incident was created
  final String createdAt;

  /// Explanation: Constructor requiring all fields to be initialized.
  const IncidentModel({
    required this.id,
    required this.tenantId,
    required this.title,
    this.description,
    required this.category,
    required this.severity,
    required this.status,
    required this.latitude,
    required this.longitude,
    required this.peopleAtRisk,
    required this.priorityScore,
    required this.createdAt,
  });

  /// Briefing: Factory to parse [IncidentModel] from JSON.
  /// Reason: Standardizes how the app ingests raw JSON from the REST API or WebSockets.
  /// Explanation: Safely casts JSON types (e.g., `num` to `double`) and provides safe default values.
  factory IncidentModel.fromJson(Map<String, dynamic> json) {
    return IncidentModel(
      id: json['id'] as String,
      tenantId: json['tenant_id'] as String? ?? '00000000-0000-0000-0000-000000000001',
      title: json['title'] as String,
      description: json['description'] as String?,
      category: json['category'] as String? ?? 'GENERAL',
      severity: json['severity'] as String? ?? 'MEDIUM',
      status: json['status'] as String? ?? 'REPORTED',
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      peopleAtRisk: (json['people_at_risk'] as num?)?.toInt() ?? 1,
      priorityScore: (json['priority_score'] as num?)?.toDouble() ?? 50.0,
      createdAt: json['created_at'] as String? ?? DateTime.now().toUtc().toIso8601String(),
    );
  }

  /// Briefing: Serializes the [IncidentModel] to a JSON Map.
  /// Reason: Used for caching locally in SQLite or making POST requests to the backend.
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'tenant_id': tenantId,
      'title': title,
      'description': description,
      'category': category,
      'severity': severity,
      'status': status,
      'latitude': latitude,
      'longitude': longitude,
      'people_at_risk': peopleAtRisk,
      'priority_score': priorityScore,
      'created_at': createdAt,
    };
  }

  /// Briefing: Helper method to parse a JSON string list.
  /// Explanation: Decodes JSON string into a `List<Map>` then maps to `IncidentModel` instances.
  static List<IncidentModel> parseList(String jsonString) {
    final parsed = (jsonDecode(jsonString) as List<dynamic>).cast<Map<String, dynamic>>();
    return parsed.map<IncidentModel>((json) => IncidentModel.fromJson(json)).toList();
  }

  /// Briefing: Helper to parse JSON lists in a background isolate.
  /// Reason: Parsing large lists of incidents on the main thread causes UI freezes.
  /// Explanation: Passes `parseList` to Flutter's `compute` to run it in parallel.
  static Future<List<IncidentModel>> parseListInBackground(String jsonString) {
    return compute(parseList, jsonString);
  }
}
