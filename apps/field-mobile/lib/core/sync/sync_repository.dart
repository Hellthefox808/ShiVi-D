import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:crypto/crypto.dart';
import '../database/database.dart';

/// ShiVi Causal Delta Synchronization Repository for Flutter Field Nodes
class SyncRepository {
  final Dio dio;
  final String baseUrl;
  final String tenantId;
  final String deviceId;
  final String authToken;

  int _localSequence = 0;
  final Map<String, int> _versionVector = {};

  SyncRepository({
    required this.dio,
    required this.baseUrl,
    required this.tenantId,
    required this.deviceId,
    required this.authToken,
  }) {
    _versionVector[deviceId] = 0;
  }

  /// Push pending outbox events to central API
  Future<bool> pushOutboxBatch(List<LocalEventEntity> events) async {
    if (events.isEmpty) return true;

    final payload = {
      'device_id': deviceId,
      'events': events.map((e) => {
        'event_id': e.eventId,
        'tenant_id': e.tenantId,
        'entity_type': e.entityType,
        'entity_id': e.entityId,
        'event_type': e.eventType,
        'changes': e.changes,
        'actor_id': e.actorId,
        'device_id': e.deviceId,
        'device_sequence': e.deviceSequence,
        'occurred_at': e.occurredAt.toIso8601String(),
        'version_vector': e.versionVector,
        'evidence_ids': e.evidenceIds,
        'schema_version': 1,
        'integrity_hash': e.integrityHash,
      }).toList(),
    };

    try {
      final response = await dio.post(
        '$baseUrl/v1/sync/push',
        data: payload,
        options: Options(
          headers: {
            'Authorization': 'Bearer $authToken',
            'Content-Type': 'application/json',
          },
        ),
      );

      return response.statusCode == 200;
    } catch (e) {
      // Offline network failure - gracefully retain in local outbox
      return false;
    }
  }

  /// Creates a local event envelope with SHA-256 integrity hash
  LocalEventEntity createLocalEvent({
    required String entityType,
    required String entityId,
    required String eventType,
    required Map<String, dynamic> changes,
    required String actorId,
    List<String> evidenceIds = const [],
  }) {
    _localSequence += 1;
    _versionVector[deviceId] = _localSequence;

    final occurredAt = DateTime.now().toUtc();
    final eventId = 'EVT-${DateTime.now().millisecondsSinceEpoch}-$deviceId-$_localSequence';

    final rawForHash = '$eventId:$tenantId:$entityId:$eventType:${occurredAt.toIso8601String()}';
    final integrityHash = sha256.convert(utf8.encode(rawForHash)).toString();

    return LocalEventEntity(
      eventId: eventId,
      tenantId: tenantId,
      entityType: entityType,
      entityId: entityId,
      eventType: eventType,
      changes: changes,
      actorId: actorId,
      deviceId: deviceId,
      deviceSequence: _localSequence,
      occurredAt: occurredAt,
      versionVector: Map.from(_versionVector),
      evidenceIds: evidenceIds,
      integrityHash: integrityHash,
    );
  }
}
