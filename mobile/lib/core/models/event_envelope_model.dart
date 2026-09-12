import 'dart:convert';
import 'package:flutter/foundation.dart';

/// Briefing: Represents a synchronized event wrapper used for offline-first distributed syncing.
/// Reason: When devices sync peer-to-peer (e.g., via Bluetooth Mesh) or with the backend, 
/// we need a consistent way to package data (`payload`) with metadata (timestamps, clocks, hashes) 
/// to resolve conflicts and ensure data integrity.
class EventEnvelopeModel {
  // Explanation: Unique identifier for this specific event occurrence
  final String eventId;
  // Explanation: Tenant/Organization ID isolating data
  final String tenantId;
  // Explanation: The type of entity being modified (e.g., 'INCIDENT', 'TASK')
  final String entityType;
  // Explanation: The ID of the specific entity being modified
  final String entityId;
  // Explanation: Action performed (e.g., 'CREATE', 'UPDATE', 'DELETE')
  final String eventType;
  // Explanation: ID of the user or agent who performed the action
  final String actorId;
  // Explanation: ID of the hardware device that generated the event
  final String deviceId;
  // Explanation: Logical clock used for total ordering of events across distributed nodes
  final int lamportClock;
  // Explanation: Vector clock used to detect causal relationships and concurrent modifications
  final Map<String, int> vectorClock;
  // Explanation: The actual data being synced (e.g., the JSON of a Task or Incident)
  final Map<String, dynamic> payload;
  // Explanation: Cryptographic hash verifying the envelope hasn't been tampered with
  final String integrityHash;
  // Explanation: Wall-clock timestamp when the event occurred
  final String occurredAt;

  /// Explanation: Constructor requiring all fields to create a valid sync envelope.
  const EventEnvelopeModel({
    required this.eventId,
    required this.tenantId,
    required this.entityType,
    required this.entityId,
    required this.eventType,
    required this.actorId,
    required this.deviceId,
    required this.lamportClock,
    required this.vectorClock,
    required this.payload,
    required this.integrityHash,
    required this.occurredAt,
  });

  /// Briefing: Parses an [EventEnvelopeModel] from a JSON map.
  /// Reason: Used when receiving sync packets over the network or reading from the outbox table.
  factory EventEnvelopeModel.fromJson(Map<String, dynamic> json) {
    // Explanation: Safely parses the vector clock, which is a map of Device ID to Integer tick count.
    final rawVector = json['vector_clock'] as Map<String, dynamic>? ?? {};
    final parsedVector = rawVector.map((k, v) => MapEntry(k, (v as num).toInt()));

    return EventEnvelopeModel(
      eventId: json['event_id'] as String,
      tenantId: json['tenant_id'] as String,
      entityType: json['entity_type'] as String,
      entityId: json['entity_id'] as String,
      eventType: json['event_type'] as String,
      actorId: json['actor_id'] as String,
      deviceId: json['device_id'] as String,
      lamportClock: (json['lamport_clock'] as num).toInt(),
      vectorClock: parsedVector,
      payload: json['payload'] as Map<String, dynamic>? ?? {},
      integrityHash: json['integrity_hash'] as String,
      occurredAt: json['occurred_at'] as String? ?? DateTime.now().toUtc().toIso8601String(),
    );
  }

  /// Briefing: Converts the envelope back to a JSON Map.
  /// Reason: Required to transmit the event over the wire (HTTP or Bluetooth).
  Map<String, dynamic> toJson() {
    return {
      'event_id': eventId,
      'tenant_id': tenantId,
      'entity_type': entityType,
      'entity_id': entityId,
      'event_type': eventType,
      'actor_id': actorId,
      'device_id': deviceId,
      'lamport_clock': lamportClock,
      'vector_clock': vectorClock,
      'payload': payload,
      'integrity_hash': integrityHash,
      'occurred_at': occurredAt,
    };
  }

  /// Briefing: Helper method to parse a list of envelopes from a JSON string.
  static List<EventEnvelopeModel> parseList(String jsonString) {
    final parsed = (jsonDecode(jsonString) as List<dynamic>).cast<Map<String, dynamic>>();
    return parsed.map<EventEnvelopeModel>((json) => EventEnvelopeModel.fromJson(json)).toList();
  }

  /// Briefing: Parses a list of envelopes in a background thread to prevent UI freezing during large syncs.
  static Future<List<EventEnvelopeModel>> parseListInBackground(String jsonString) {
    return compute(parseList, jsonString);
  }
}
