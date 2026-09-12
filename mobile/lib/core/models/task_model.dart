import 'dart:convert';
import 'package:flutter/foundation.dart';

/// Briefing: Represents a specific task assigned to a field agent during an incident.
/// Reason: We need a structured data model to serialize/deserialize task data from the backend
/// or local database. This encapsulates all the relevant fields for a task.
class TaskModel {
  // Explanation: Unique identifier for the task
  final String id;
  // Explanation: The ID of the incident this task is associated with
  final String incidentId;
  // Explanation: Optional ID of the user/agent assigned to this task
  final String? assigneeId;
  // Explanation: Short, descriptive title of the task
  final String title;
  // Explanation: Detailed description or instructions for the task
  final String? description;
  // Explanation: Current status (e.g., PENDING, IN_PROGRESS, COMPLETED)
  final String status;
  // Explanation: Optional code representing a specific route or sector
  final String? routeCode;
  // Explanation: Flag indicating if the route to this task is physically blocked
  final bool isRouteBlocked;
  // Explanation: Timestamp when the task was created
  final String createdAt;
  // Explanation: Optional timestamp of the last update
  final String? updatedAt;

  /// Explanation: Constructor for [TaskModel]. 
  /// Requires essential fields like id, incidentId, title, status, and createdAt.
  const TaskModel({
    required this.id,
    required this.incidentId,
    this.assigneeId,
    required this.title,
    this.description,
    required this.status,
    this.routeCode,
    this.isRouteBlocked = false,
    required this.createdAt,
    this.updatedAt,
  });

  /// Briefing: Factory constructor to create a [TaskModel] from a JSON map.
  /// Reason: Used when parsing API responses or reading from SQLite/SharedPreferences.
  /// Explanation: It maps JSON keys to class properties, providing default values for missing or null fields.
  factory TaskModel.fromJson(Map<String, dynamic> json) {
    return TaskModel(
      id: json['id'] as String,
      incidentId: json['incident_id'] as String,
      assigneeId: json['assignee_id'] as String?,
      title: json['title'] as String,
      description: json['description'] as String?,
      status: json['status'] as String? ?? 'PENDING',
      routeCode: json['route_code'] as String?,
      isRouteBlocked: json['is_route_blocked'] as bool? ?? false,
      createdAt: json['created_at'] as String? ?? DateTime.now().toUtc().toIso8601String(),
      updatedAt: json['updated_at'] as String?,
    );
  }

  /// Briefing: Converts a [TaskModel] instance into a JSON map.
  /// Reason: Required when sending data back to the server or saving it to local storage.
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'incident_id': incidentId,
      'assignee_id': assigneeId,
      'title': title,
      'description': description,
      'status': status,
      'route_code': routeCode,
      'is_route_blocked': isRouteBlocked,
      'created_at': createdAt,
      'updated_at': updatedAt,
    };
  }

  /// Briefing: Parses a raw JSON string into a list of [TaskModel]s.
  /// Explanation: Decodes the string into a List of Maps, then maps each Map into a TaskModel object.
  static List<TaskModel> parseList(String jsonString) {
    final parsed = (jsonDecode(jsonString) as List<dynamic>).cast<Map<String, dynamic>>();
    return parsed.map<TaskModel>((json) => TaskModel.fromJson(json)).toList();
  }

  /// Briefing: Parses a JSON string into a list of [TaskModel]s on a separate background isolate.
  /// Reason: JSON decoding and mapping can be CPU-intensive for large lists, which can cause UI stutter (jank).
  /// Explanation: Uses Flutter's `compute` function to run `parseList` off the main UI thread.
  static Future<List<TaskModel>> parseListInBackground(String jsonString) {
    return compute(parseList, jsonString);
  }
}
