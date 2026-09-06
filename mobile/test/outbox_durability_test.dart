import 'package:flutter_test/flutter_test.dart';
import 'package:shivi_field_mobile/core/database/local_database_repository.dart';
import 'package:shivi_field_mobile/core/network/api_service.dart';
import 'package:shivi_field_mobile/core/database/database.dart';

class FakeSuccessApiService extends ApiService {
  int pushCallCount = 0;
  List<LocalEventEntity> pushedEvents = [];

  @override
  Future<bool> pushOutboxEvents({
    required String deviceId,
    required List<LocalEventEntity> events,
  }) async {
    pushCallCount++;
    pushedEvents.addAll(events);
    return true;
  }
}

class FakeFailureApiService extends ApiService {
  @override
  Future<bool> pushOutboxEvents({
    required String deviceId,
    required List<LocalEventEntity> events,
  }) async {
    return false;
  }
}

void main() {
  group('LocalDatabaseRepository Outbox Durability & Lifecycle Tests', () {
    late LocalDatabaseRepository repo;

    setUp(() {
      repo = LocalDatabaseRepository(
        deviceId: 'NODE-TEST-01',
        actorId: 'SDRF-COMMANDER-01',
      );
    });

    test('Initializes with seeded tasks and default safety freeze status', () {
      expect(repo.tasks.length, equals(2));
      final blockedTask = repo.tasks.firstWhere((t) => t.isRouteBlocked == 'TRUE');
      expect(blockedTask.routeId, equals('ROUTE-88'));
      expect(blockedTask.status, equals('OFFERED'));
      expect(repo.pendingOutboxCount, equals(0));
    });

    test('Recording an incident atomically commits entity, event, and pending outbox item', () {
      final incident = repo.recordIncident(
        title: 'Flash Flood Near Community Hall',
        description: 'Water breached low bund wall, 6 elderly people trapped.',
        category: 'RESCUE',
        severity: 'CRITICAL',
        peopleAtRisk: 6,
        latitude: 26.1856,
        longitude: 91.7483,
      );

      // 1. Materialized Entity Verification
      expect(incident.id, isNotEmpty);
      expect(incident.localReference.startsWith('OFFLINE-REF-'), isTrue);
      expect(incident.status, equals('REPORTED'));
      expect(repo.incidents.length, equals(1));
      expect(repo.incidents.first.id, equals(incident.id));

      // 2. Event Log & Vector Clock Verification (Invariant 2)
      expect(repo.eventLog.length, equals(1));
      final loggedEvent = repo.eventLog.first;
      expect(loggedEvent.eventType, equals('INCIDENT_REPORTED'));
      expect(loggedEvent.deviceId, equals('NODE-TEST-01'));
      expect(loggedEvent.deviceSequence, equals(1));
      expect(loggedEvent.versionVector['NODE-TEST-01'], equals(1));
      expect(loggedEvent.integrityHash.length, equals(64)); // SHA-256 hex length

      // 3. Outbox Queue Verification (Invariant 1)
      expect(repo.outbox.length, equals(1));
      final outboxItem = repo.outbox.first;
      expect(outboxItem.eventId, equals(loggedEvent.eventId));
      expect(outboxItem.status, equals('PENDING'));
      expect(repo.pendingOutboxCount, equals(1));
    });

    test('Multiple incidents monotonically increment sequence numbers and vector clocks', () {
      repo.recordIncident(
        title: 'Incident 1',
        description: 'First event',
        category: 'RELIEF',
        severity: 'LOW',
        peopleAtRisk: 0,
        latitude: 26.18,
        longitude: 91.74,
      );

      repo.recordIncident(
        title: 'Incident 2',
        description: 'Second event',
        category: 'MEDICAL',
        severity: 'HIGH',
        peopleAtRisk: 3,
        latitude: 26.19,
        longitude: 91.75,
      );

      expect(repo.pendingOutboxCount, equals(2));
      expect(repo.eventLog[1].deviceSequence, equals(1));
      expect(repo.eventLog[0].deviceSequence, equals(2));
      expect(repo.eventLog[0].versionVector['NODE-TEST-01'], equals(2));
    });

    test('Phase 7 task completion registers cryptographic evidence and enqueues completion event', () {
      const sha256Proof = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855';
      final success = repo.completeTaskWithEvidence(
        taskId: 'task-sdrf-01',
        sha256Hash: sha256Proof,
        latitude: 26.1856,
        longitude: 91.7483,
        notes: '3 civilians safely extracted via Zodiac boat.',
      );

      expect(success, isTrue);

      // Verify task status
      final task = repo.tasks.firstWhere((t) => t.id == 'task-sdrf-01');
      expect(task.status, equals('COMPLETED'));

      // Verify event log contains evidence hash
      final completionEvent = repo.eventLog.firstWhere((e) => e.eventType == 'TASK_COMPLETED');
      expect(completionEvent.entityId, equals('task-sdrf-01'));
      expect(completionEvent.evidenceIds, contains(sha256Proof));
      expect(completionEvent.changes['sha256_proof'], equals(sha256Proof));

      // Verify pending outbox item enqueued
      expect(repo.pendingOutboxCount, equals(1));
    });

    test('Flush outbox pushes all pending records and marks them SENT on success', () async {
      repo.recordIncident(
        title: 'Evac Alert',
        description: 'Bridge collapsed',
        category: 'RESCUE',
        severity: 'CRITICAL',
        peopleAtRisk: 5,
        latitude: 26.18,
        longitude: 91.74,
      );

      expect(repo.pendingOutboxCount, equals(1));

      final fakeApi = FakeSuccessApiService();
      final flushedCount = await repo.flushOutbox(fakeApi);

      expect(flushedCount, equals(1));
      expect(fakeApi.pushCallCount, equals(1));
      expect(fakeApi.pushedEvents.length, equals(1));
      expect(repo.pendingOutboxCount, equals(0));
      expect(repo.outbox.first.status, equals('SENT'));
    });

    test('Outbox records remain PENDING when network transmission fails (Zero Data Loss)', () async {
      repo.recordIncident(
        title: 'Evac Alert',
        description: 'Bridge collapsed',
        category: 'RESCUE',
        severity: 'CRITICAL',
        peopleAtRisk: 5,
        latitude: 26.18,
        longitude: 91.74,
      );

      expect(repo.pendingOutboxCount, equals(1));

      final failingApi = FakeFailureApiService();
      final flushedCount = await repo.flushOutbox(failingApi);

      expect(flushedCount, equals(0));
      expect(repo.pendingOutboxCount, equals(1));
      expect(repo.outbox.first.status, equals('PENDING'));
    });
  });
}
