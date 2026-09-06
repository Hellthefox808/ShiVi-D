import 'dart:convert';
import 'package:dio/dio.dart';
import '../database/database.dart';

/// ShiVi Mobile Client API Service
/// Handles bidirectional HTTP communication with the FastAPI backend.
class ApiService {
  final Dio dio;
  final String baseUrl;
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

  /// Checks liveness connectivity to the backend
  Future<bool> checkHealth() async {
    try {
      final response = await dio.get('/health');
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Pushes a batch of outbox event envelopes to /v1/sync/push
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

  /// Fetches IOC Dashboard Summary metrics
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

  /// Fetches active tasks for the responder
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

  /// Uploads photographic evidence with SHA-256 digest (Phase 7)
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

  /// Triggers the full 8-phase P0 demo workflow simulation
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
