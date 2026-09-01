import 'dart:convert';
import 'package:flutter/foundation.dart';

class EventEnvelopeModel {
  final String eventId;
  final String tenantId;
  final String entityType;
  final String entityId;
  final String eventType;
  final String actorId;
  final String deviceId;
  final int lamportClock;
  final Map<String, int> vectorClock;
  final Map<String, dynamic> payload;
  final String integrityHash;
  final String occurredAt;

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

  factory EventEnvelopeModel.fromJson(Map<String, dynamic> json) {
    // Parse vector clock safely
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

  static List<EventEnvelopeModel> parseList(String jsonString) {
    final parsed = (jsonDecode(jsonString) as List<dynamic>).cast<Map<String, dynamic>>();
    return parsed.map<EventEnvelopeModel>((json) => EventEnvelopeModel.fromJson(json)).toList();
  }

  static Future<List<EventEnvelopeModel>> parseListInBackground(String jsonString) {
    return compute(parseList, jsonString);
  }
}
