import 'dart:convert';
import 'package:crypto/crypto.dart';

/// Briefing: ShiVi Local-First Embedded SQLite Drift Table Definitions
/// Reason: The app must function in completely disconnected environments (e.g., natural disasters).
/// By maintaining a local database, users can continue to read and write data without an internet connection.
/// 
/// Invariant: Mutations commit atomically across 3 tables:
/// 1. Materialized View (for zero-latency local UI reads)
/// 2. Immutable Event Log (for causal history)
/// 3. Local Outbox (for background causal sync push)

/// Briefing: Represents an Incident record as stored in the local device database.
/// Reason: Caches incident data locally so first responders can view emergency details offline.
class LocalIncidentEntity {
  // Explanation: Unique UUID for the incident
  final String id;
  // Explanation: A human-readable local reference code for quick radio communication
  final String localReference;
  // Explanation: Type of emergency (e.g., MEDICAL, FIRE)
  final String category;
  // Explanation: Short descriptive title
  final String title;
  // Explanation: Full description of the situation
  final String description;
  // Explanation: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
  final String severity;
  // Explanation: Lifecycle state of the incident
  final String status;
  // Explanation: Estimated count of vulnerable people
  final int peopleAtRisk;
  // Explanation: Computed triage priority score
  final double priorityScore;
  // Explanation: Map coordinates for the incident
  final double latitude;
  final double longitude;
  // Explanation: When the incident was initially logged
  final DateTime createdAt;
  // Explanation: Flag indicating if this record has been successfully synced with the cloud
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

/// Briefing: Represents a Task assigned to a responder in the local database.
/// Reason: Allows responders to see their mission objectives and update their progress while offline.
class LocalTaskEntity {
  // Explanation: Unique identifier for the task
  final String id;
  // Explanation: The parent incident this task belongs to
  final String incidentId;
  // Explanation: Task objective
  final String title;
  // Explanation: Task instructions
  final String description;
  // Explanation: Categorization of the task type
  final String taskType;
  // Explanation: Current progress status
  final String status;
  // Explanation: Optional ID mapping to a specific geographical route
  final String? routeId;
  // Explanation: Boolean (stored as string) indicating if the route is blocked
  final String isRouteBlocked;
  // Explanation: Creation timestamp
  final DateTime createdAt;
  // Explanation: Sync status flag
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

/// Briefing: An immutable record of an action taken on the device.
/// Reason: Instead of just overwriting rows, we store a log of "events" (e.g., "TASK_COMPLETED").
/// This enables Conflict-Free Replicated Data Types (CRDTs) and causal syncing when network is restored.
class LocalEventEntity {
  // Explanation: Unique identifier for the event
  final String eventId;
  // Explanation: Tenant isolation ID
  final String tenantId;
  // Explanation: The type of entity modified ('INCIDENT', 'TASK')
  final String entityType;
  // Explanation: The specific entity's ID
  final String entityId;
  // Explanation: The specific action (e.g., 'INCIDENT_REPORTED')
  final String eventType;
  // Explanation: The JSON payload of what actually changed
  final Map<String, dynamic> changes;
  // Explanation: Who made the change
  final String actorId;
  // Explanation: Which device made the change
  final String deviceId;
  // Explanation: Logical counter for this device to maintain strict ordering
  final int deviceSequence;
  // Explanation: Wall-clock time of the event
  final DateTime occurredAt;
  // Explanation: Vector clock map tracking causality dependencies across the mesh network
  final Map<String, int> versionVector;
  // Explanation: List of references to binary evidence (e.g., photo SHA hashes)
  final List<String> evidenceIds;
  // Explanation: Cryptographic hash to prevent tampering with the event history
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

  /// Briefing: Computes a SHA-256 hash for a given JSON payload.
  /// Reason: Used to generate the `integrityHash` to prove that the event data was not altered.
  static String computeHash(Map<String, dynamic> payload) {
    final raw = jsonEncode(payload);
    return sha256.convert(utf8.encode(raw)).toString();
  }
}

/// Briefing: A queue item representing an event that needs to be transmitted.
/// Reason: Acts as a buffer/queue. If an event fails to upload, it stays in the outbox
/// to be retried later, guaranteeing at-least-once delivery.
class LocalOutboxEntity {
  // Explanation: Unique ID for the queue item
  final String id;
  // Explanation: The ID of the `LocalEventEntity` that needs syncing
  final String eventId;
  // Explanation: Current transmission status (PENDING, IN_FLIGHT, SENT, FAILED)
  final String status; 
  // Explanation: Number of times we've tried to send this
  final int retryCount;
  // Explanation: When it was queued
  final DateTime createdAt;

  LocalOutboxEntity({
    required this.id,
    required this.eventId,
    this.status = 'PENDING',
    this.retryCount = 0,
    required this.createdAt,
  });
}
