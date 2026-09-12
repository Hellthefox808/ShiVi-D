import 'dart:convert';
import 'package:dio/dio.dart';
import '../database/database.dart';

/// Briefing: ShiVi Mobile Client REST API Service.
/// Reason: Provides structured, authenticated HTTP communication between field devices and the central FastAPI hub.
/// When network connectivity is operational, this service delivers cloud synchronization, evidence ingest,
/// mission tasking, and telemetry reporting.
class ApiService {
  // Explanation: Dio HTTP client configured with aggressive connection and receive timeouts for field conditions
  final Dio dio;
  // Explanation: Target backend host URL
  final String baseUrl;
  // Explanation: Authorization bearer token for API authentication
  final String authToken;

  ApiService({
    Dio? dioClient,
    this.baseUrl = 'http://localhost:8000',
    this.authToken = 'TACTICAL-OFFLINE-TOKEN-DEFAULT',
  }) : dio = dioClient ?? Dio(BaseOptions(
          baseUrl: baseUrl,
          connectTimeout: const Duration(seconds: 5),
          receiveTimeout: const Duration(seconds: 5),
        ));

  /// Briefing: Checks liveness and network path reachability to the backend server.
  /// Reason: Used by connectivity monitors to distinguish between local Wi-Fi connection and actual internet uplink.
  Future<bool> checkHealth() async {
    try {
      final response = await dio.get('/health');
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Briefing: Pushes a batch of outbox event envelopes to `/v1/sync/push`.
  /// Reason: Flushes local event-sourced state changes to the central database in an atomic bulk transaction.
  /// 
  /// Explanation:
  /// Transforms each [LocalEventEntity] into JSON and posts to `/v1/sync/push`.
  /// Returns `true` on HTTP 200 success, or `false` on network failure so items remain in the outbox.
  Future<bool> pushOutboxEvents({
    required String deviceId,
    required List<LocalEventEntity> events,
  }) async {
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
        '/v1/sync/push',
        data: payload,
        options: Options(
          headers: {
            'Authorization': 'Bearer $authToken',
            'Content-Type': 'application/json',
          },
        ),
      );
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Briefing: Fetches live Incident Operations Center (IOC) dashboard metrics and system posture.
  /// Reason: Populates the mobile tactical overview with real-time responder counts, open incidents, and network health.
  Future<Map<String, dynamic>?> fetchDashboardSummary() async {
    try {
      final response = await dio.get('/v1/dashboard/summary');
      if (response.statusCode == 200 && response.data is Map<String, dynamic>) {
        return response.data as Map<String, dynamic>;
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  /// Briefing: Retrieves the list of active tasks assigned to field units.
  /// Reason: Synchronizes task status, priorities, and assigned personnel from the central coordination server.
  Future<List<Map<String, dynamic>>> fetchTasks() async {
    try {
      final response = await dio.get('/v1/tasks');
      if (response.statusCode == 200 && response.data is List) {
        return (response.data as List).cast<Map<String, dynamic>>();
      }
      return [];
    } catch (_) {
      return [];
    }
  }

  /// Briefing: Uploads photographic or sensor verification evidence with cryptographic digest (Phase 7: Verification).
  /// Reason: Validates task completion through immutable GPS-stamped SHA-256 evidence hashes.
  Future<bool> uploadEvidence({
    required String taskId,
    required String sha256Hash,
    required double latitude,
    required double longitude,
    String? note,
  }) async {
    final payload = {
      'task_id': taskId,
      'sha256_hash': sha256Hash,
      'latitude': latitude,
      'longitude': longitude,
      'note': note ?? 'Tactical field completion evidence',
      'captured_at': DateTime.now().toUtc().toIso8601String(),
    };

    try {
      final response = await dio.post(
        '/v1/evidence/upload',
        data: payload,
        options: Options(headers: {'Authorization': 'Bearer $authToken'}),
      );
      return response.statusCode == 200 || response.statusCode == 201;
    } catch (_) {
      return false;
    }
  }

  /// Briefing: Triggers the full 8-phase P0 demo workflow simulation on the backend.
  /// Reason: Allows field testers to simulate an entire disaster response cycle with synthetic multi-node data.
  Future<Map<String, dynamic>?> triggerSimulation() async {
    try {
      final response = await dio.post('/v1/demo/simulate-workflow');
      if (response.statusCode == 200 && response.data is Map<String, dynamic>) {
        return response.data as Map<String, dynamic>;
      }
      return null;
    } catch (_) {
      return null;
    }
  }
}
