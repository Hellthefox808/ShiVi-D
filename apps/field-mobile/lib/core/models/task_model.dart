import 'dart:convert';
import 'package:flutter/foundation.dart';

class TaskModel {
  final String id;
  final String incidentId;
  final String? assigneeId;
  final String title;
  final String? description;
  final String status;
  final String? routeCode;
  final bool isRouteBlocked;
  final String createdAt;
  final String? updatedAt;

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

  static List<TaskModel> parseList(String jsonString) {
    final parsed = (jsonDecode(jsonString) as List<dynamic>).cast<Map<String, dynamic>>();
    return parsed.map<TaskModel>((json) => TaskModel.fromJson(json)).toList();
  }

  static Future<List<TaskModel>> parseListInBackground(String jsonString) {
    return compute(parseList, jsonString);
  }
}
