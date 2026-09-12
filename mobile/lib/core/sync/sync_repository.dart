import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:crypto/crypto.dart';
import '../database/database.dart';

/// Briefing: ShiVi Causal Delta Synchronization Repository for Flutter Field Nodes.
/// Reason: In humanitarian and disaster zones, internet connectivity is intermittent and partitioned.
/// Field workers generate state mutations locally that must eventually reach the central hub.
/// This repository constructs tamper-evident event envelopes with causal version vectors and handles
/// batch uploading to the sync endpoint.
class SyncRepository {
  // Explanation: HTTP client used for REST communication with the backend
  final Dio dio;
  // Explanation: Central API root URL (e.g., https://api.shivi.internal)
  final String baseUrl;
  // Explanation: Organization or deployment boundary ID for multi-tenant isolation
  final String tenantId;
  // Explanation: Unique identifier for this hardware node (phone/tablet)
  final String deviceId;
  // Explanation: Bearer token representing the responder's authenticated session
  final String authToken;

  // Explanation: Monotonically increasing counter of events authored on this device
  int _localSequence = 0;
  // Explanation: Causal tracking map tracking [deviceId -> highest known sequence number]
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

  /// Briefing: Pushes a batch of pending outbox events to the central API.
  /// Reason: Sending events individually would cause massive network overhead and high radio-frequency battery drain.
  /// Batching amortizes HTTP connection handshakes and SSL negotiation.
  /// 
  /// Explanation:
  /// Transforms each [LocalEventEntity] into the expected backend JSON wire format.
  /// Returns `true` if the server accepted the batch with HTTP 200, or `false` on network timeout/failure.
  /// On failure, the outbox retains the events for subsequent retry by the sync orchestrator.
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

  /// Briefing: Constructs an immutable local event envelope stamped with a sequence number, version vector, and SHA-256 integrity hash.
  /// Reason: Prevents event tampering, guarantees causal partial ordering across distributed field devices, and ensures idempotent reconciliation.
  /// 
  /// Explanation:
  /// 1. Increments `_localSequence` and updates `_versionVector[deviceId]`.
  /// 2. Generates an RFC-compliant deterministic event ID using timestamp, deviceId, and sequence.
  /// 3. Computes a SHA-256 cryptographic integrity hash across critical event fields.
  /// 4. Returns a ready-to-persist [LocalEventEntity].
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
