import 'dart:convert';
import 'package:flutter/foundation.dart';

class IncidentModel {
  final String id;
  final String tenantId;
  final String title;
  final String? description;
  final String category;
  final String severity;
  final String status;
  final double latitude;
  final double longitude;
  final int peopleAtRisk;
  final double priorityScore;
  final String createdAt;

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

  static List<IncidentModel> parseList(String jsonString) {
    final parsed = (jsonDecode(jsonString) as List<dynamic>).cast<Map<String, dynamic>>();
    return parsed.map<IncidentModel>((json) => IncidentModel.fromJson(json)).toList();
  }

  static Future<List<IncidentModel>> parseListInBackground(String jsonString) {
    return compute(parseList, jsonString);
  }
}
