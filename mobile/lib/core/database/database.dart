import 'dart:convert';
import 'package:crypto/crypto.dart';

/// ShiVi Local-First Embedded SQLite Drift Table Definitions
///
/// Invariant: Mutations commit atomically across 3 tables:
/// 1. Materialized View (for zero-latency local UI reads)
/// 2. Immutable Event Log (for causal history)
/// 3. Local Outbox (for background causal sync push)

class LocalIncidentEntity {
  final String id;
  final String localReference;
  final String category;
  final String title;
  final String description;
  final String severity;
  final String status;
  final int peopleAtRisk;
  final double priorityScore;
  final double latitude;
  final double longitude;
  final DateTime createdAt;
  final bool isSynced;

  LocalIncidentEntity({
    required this.id,
    required this.localReference,
    required this.category,
    required this.title,
    required this.description,
    required this.severity,
    required this.status,
    required this.peopleAtRisk,
    required this.priorityScore,
    required this.latitude,
    required this.longitude,
    required this.createdAt,
    this.isSynced = false,
  });
}

class LocalTaskEntity {
  final String id;
  final String incidentId;
  final String title;
  final String description;
  final String taskType;
  final String status;
  final String? routeId;
  final String isRouteBlocked;
  final DateTime createdAt;
  final bool isSynced;

  LocalTaskEntity({
    required this.id,
    required this.incidentId,
    required this.title,
    required this.description,
    required this.taskType,
    required this.status,
    this.routeId,
    this.isRouteBlocked = 'FALSE',
    required this.createdAt,
    this.isSynced = false,
  });
}

class LocalEventEntity {
  final String eventId;
  final String tenantId;
  final String entityType;
  final String entityId;
  final String eventType;
  final Map<String, dynamic> changes;
  final String actorId;
  final String deviceId;
  final int deviceSequence;
  final DateTime occurredAt;
  final Map<String, int> versionVector;
  final List<String> evidenceIds;
  final String integrityHash;

  LocalEventEntity({
    required this.eventId,
    required this.tenantId,
    required this.entityType,
    required this.entityId,
    required this.eventType,
    required this.changes,
    required this.actorId,
    required this.deviceId,
    required this.deviceSequence,
    required this.occurredAt,
    required this.versionVector,
    this.evidenceIds = const [],
    required this.integrityHash,
  });

  static String computeHash(Map<String, dynamic> payload) {
    final raw = jsonEncode(payload);
    return sha256.convert(utf8.encode(raw)).toString();
  }
}

class LocalOutboxEntity {
  final String id;
  final String eventId;
  final String status; // PENDING, IN_FLIGHT, SENT, FAILED
  final int retryCount;
  final DateTime createdAt;

  LocalOutboxEntity({
    required this.id,
    required this.eventId,
    this.status = 'PENDING',
    this.retryCount = 0,
    required this.createdAt,
  });
}
