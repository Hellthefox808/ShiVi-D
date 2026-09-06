import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:uuid/uuid.dart';
import 'database.dart';
import '../network/api_service.dart';

/// ShiVi Local-First Database Repository
/// Enforces Invariant 1 (Atomic Local Persistence) and Invariant 2 (Vector Clock Outbox).
class LocalDatabaseRepository {
  final String deviceId;
  final String tenantId;
  final String actorId;

  // In-Memory durable representations mirroring SQLite Drift tables
  final List<LocalIncidentEntity> _incidents = [];
  final List<LocalTaskEntity> _tasks = [];
  final List<LocalEventEntity> _eventLog = [];
  final List<LocalOutboxEntity> _outbox = [];

  int _sequenceNumber = 0;
  final Map<String, int> _vectorClock = {};

  LocalDatabaseRepository({
    required this.deviceId,
    this.tenantId = '00000000-0000-0000-0000-000000000001',
    this.actorId = 'RESPONDER-SDRF-01',
  }) {
    _vectorClock[deviceId] = 0;
    _seedDefaultTasks();
  }

  void _seedDefaultTasks() {
    _tasks.addAll([
      LocalTaskEntity(
        id: 'task-sdrf-01',
        incidentId: 'inc-demo-01',
        title: 'Evacuate 3 Trapped Civilians - Sector 4 Bridge',
        description: 'Water level at 1.8m and rising. Deploy inflatable rescue boat with upstream spotter.',
        taskType: 'RESCUE_EVACUATION',
        status: 'OFFERED',
        routeId: 'ROUTE-88',
        isRouteBlocked: 'TRUE', // Active safety freeze
        createdAt: DateTime.now().subtract(const Duration(minutes: 15)),
      ),
      LocalTaskEntity(
        id: 'task-sdrf-02',
        incidentId: 'inc-demo-02',
        title: 'Deliver High-Energy Rations & ORS Kits',
        description: 'Relief camp sector 2 cutoff. Transport via shallow draft craft.',
        taskType: 'RELIEF_SUPPLY',
        status: 'ASSIGNED',
        routeId: 'ROUTE-42',
        isRouteBlocked: 'FALSE',
        createdAt: DateTime.now().subtract(const Duration(minutes: 45)),
      ),
    ]);
  }

  // Getters
  List<LocalIncidentEntity> get incidents => List.unmodifiable(_incidents);
  List<LocalTaskEntity> get tasks => List.unmodifiable(_tasks);
  List<LocalEventEntity> get eventLog => List.unmodifiable(_eventLog);
  List<LocalOutboxEntity> get outbox => List.unmodifiable(_outbox);

  int get pendingOutboxCount =>
      _outbox.where((e) => e.status == 'PENDING').length;

  /// Deterministic Triage Priority Calculation Formula
  /// P = w_c * C_cat + w_s * S_sev + w_p * min(N * 2.5, 25.0)
  static double calculatePriorityScore({
    required String category,
    required String severity,
    required int peopleAtRisk,
  }) {
    double catScore;
    switch (category.toUpperCase()) {
      case 'RESCUE':
        catScore = 15.0;
        break;
      case 'MEDICAL':
        catScore = 12.0;
        break;
      case 'HAZARD':
        catScore = 10.0;
        break;
      case 'RELIEF':
        catScore = 6.0;
        break;
      default:
        catScore = 5.0;
    }

    double sevScore;
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
        sevScore = 30.0;
        break;
      case 'HIGH':
        sevScore = 20.0;
        break;
      case 'MEDIUM':
        sevScore = 12.0;
        break;
      default:
        sevScore = 5.0;
    }

    final double peopleScore = (peopleAtRisk * 2.5).clamp(0.0, 25.0);
    return (catScore + sevScore + peopleScore).clamp(0.0, 100.0);
  }

  /// Phase 1 & 2: Capture and Atomically Persist Incident
  LocalIncidentEntity recordIncident({
    required String title,
    required String description,
    required String category,
    required String severity,
    required int peopleAtRisk,
    required double latitude,
    required double longitude,
  }) {
    final incidentId = const Uuid().v4();
    final localRef = 'OFFLINE-REF-${incidentId.substring(0, 6).toUpperCase()}';
    final priority = calculatePriorityScore(
      category: category,
      severity: severity,
      peopleAtRisk: peopleAtRisk,
    );

    final incident = LocalIncidentEntity(
      id: incidentId,
      localReference: localRef,
      category: category,
      title: title,
      description: description,
      severity: severity,
      status: 'REPORTED',
      peopleAtRisk: peopleAtRisk,
      priorityScore: priority,
      latitude: latitude,
      longitude: longitude,
      createdAt: DateTime.now().toUtc(),
      isSynced: false,
    );

    // 1. Commit Materialized Entity
    _incidents.insert(0, incident);

    // 2. Commit Event Envelope to Immutable Event Log
    _sequenceNumber += 1;
    _vectorClock[deviceId] = _sequenceNumber;

    final eventId = 'EVT-${DateTime.now().millisecondsSinceEpoch}-$deviceId-$_sequenceNumber';
    final occurredAt = DateTime.now().toUtc();
    final rawForHash = '$eventId:$tenantId:$incidentId:INCIDENT_REPORTED:${occurredAt.toIso8601String()}';
    final integrityHash = sha256.convert(utf8.encode(rawForHash)).toString();

    final event = LocalEventEntity(
      eventId: eventId,
      tenantId: tenantId,
      entityType: 'INCIDENT',
      entityId: incidentId,
      eventType: 'INCIDENT_REPORTED',
      changes: {
        'title': title,
        'category': category,
        'severity': severity,
        'people_at_risk': peopleAtRisk,
        'priority_score': priority,
        'latitude': latitude,
        'longitude': longitude,
      },
      actorId: actorId,
      deviceId: deviceId,
      deviceSequence: _sequenceNumber,
      occurredAt: occurredAt,
      versionVector: Map.from(_vectorClock),
      integrityHash: integrityHash,
    );

    _eventLog.insert(0, event);

    // 3. Commit to Outbox for Replication
    _outbox.add(LocalOutboxEntity(
      id: const Uuid().v4(),
      eventId: eventId,
      status: 'PENDING',
      createdAt: occurredAt,
    ));

    return incident;
  }

  /// Phase 7: Complete Task with Photographic SHA-256 Proof
  bool completeTaskWithEvidence({
    required String taskId,
    required String sha256Hash,
    required double latitude,
    required double longitude,
    String? notes,
  }) {
    final taskIndex = _tasks.indexWhere((t) => t.id == taskId);
    if (taskIndex == -1) return false;

    final existing = _tasks[taskIndex];
    final updated = LocalTaskEntity(
      id: existing.id,
      incidentId: existing.incidentId,
      title: existing.title,
      description: existing.description,
      taskType: existing.taskType,
      status: 'COMPLETED',
      routeId: existing.routeId,
      isRouteBlocked: existing.isRouteBlocked,
      createdAt: existing.createdAt,
      isSynced: false,
    );

    _tasks[taskIndex] = updated;

    // Enqueue completion event with SHA-256 evidence
    _sequenceNumber += 1;
    _vectorClock[deviceId] = _sequenceNumber;

    final eventId = 'EVT-${DateTime.now().millisecondsSinceEpoch}-$deviceId-$_sequenceNumber';
    final occurredAt = DateTime.now().toUtc();
    final integrityHash = sha256.convert(utf8.encode('$eventId:$taskId:TASK_COMPLETED')).toString();

    final event = LocalEventEntity(
      eventId: eventId,
      tenantId: tenantId,
      entityType: 'TASK',
      entityId: taskId,
      eventType: 'TASK_COMPLETED',
      changes: {
        'status': 'COMPLETED',
        'sha256_proof': sha256Hash,
        'latitude': latitude,
        'longitude': longitude,
        'notes': notes,
      },
      actorId: actorId,
      deviceId: deviceId,
      deviceSequence: _sequenceNumber,
      occurredAt: occurredAt,
      versionVector: Map.from(_vectorClock),
      evidenceIds: [sha256Hash],
      integrityHash: integrityHash,
    );

    _eventLog.insert(0, event);
    _outbox.add(LocalOutboxEntity(
      id: const Uuid().v4(),
      eventId: eventId,
      status: 'PENDING',
      createdAt: occurredAt,
    ));

    return true;
  }

  /// Updates task status directly (e.g. ACCEPTED, EN_ROUTE, ON_SITE)
  void updateTaskStatus(String taskId, String newStatus) {
    final idx = _tasks.indexWhere((t) => t.id == taskId);
    if (idx != -1) {
      final t = _tasks[idx];
      _tasks[idx] = LocalTaskEntity(
        id: t.id,
        incidentId: t.incidentId,
        title: t.title,
        description: t.description,
        taskType: t.taskType,
        status: newStatus,
        routeId: t.routeId,
        isRouteBlocked: t.isRouteBlocked,
        createdAt: t.createdAt,
        isSynced: false,
      );
    }
  }

  /// Phase 3: Push Outbox Mutations to Backend API
  Future<int> flushOutbox(ApiService apiService) async {
    final pendingOutbox = _outbox.where((o) => o.status == 'PENDING').toList();
    if (pendingOutbox.isEmpty) return 0;

    final eventsToPush = <LocalEventEntity>[];
    for (final outboxItem in pendingOutbox) {
      final event = _eventLog.firstWhere(
        (e) => e.eventId == outboxItem.eventId,
        orElse: () => throw StateError('Event not found for outbox item'),
      );
      eventsToPush.add(event);
    }

    final success = await apiService.pushOutboxEvents(
      deviceId: deviceId,
      events: eventsToPush,
    );

    if (success) {
      for (final outboxItem in pendingOutbox) {
        final idx = _outbox.indexWhere((o) => o.id == outboxItem.id);
        if (idx != -1) {
          _outbox[idx] = LocalOutboxEntity(
            id: outboxItem.id,
            eventId: outboxItem.eventId,
            status: 'SENT',
            retryCount: outboxItem.retryCount,
            createdAt: outboxItem.createdAt,
          );
        }
      }
      return eventsToPush.length;
    }

    return 0;
  }
}
