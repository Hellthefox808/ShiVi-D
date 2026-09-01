import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:field_mobile/core/models/models.dart';

void main() {
  group('IncidentModel JSON Serialization', () {
    test('serializes and deserializes IncidentModel correctly', () {
      final incident = IncidentModel(
        id: 'inc-001',
        tenantId: '00000000-0000-0000-0000-000000000001',
        title: 'Sector 4 Embankment Breach',
        description: 'Water level rising near primary school',
        category: 'RESCUE',
        severity: 'CRITICAL',
        status: 'REPORTED',
        latitude: 26.1856,
        longitude: 91.7483,
        peopleAtRisk: 5,
        priorityScore: 88.5,
        createdAt: '2026-09-01T12:00:00Z',
      );

      final jsonMap = incident.toJson();
      expect(jsonMap['id'], equals('inc-001'));
      expect(jsonMap['people_at_risk'], equals(5));

      final jsonStr = jsonEncode(jsonMap);
      final decodedMap = jsonDecode(jsonStr) as Map<String, dynamic>;
      final fromJsonIncident = IncidentModel.fromJson(decodedMap);

      expect(fromJsonIncident.id, equals(incident.id));
      expect(fromJsonIncident.title, equals(incident.title));
      expect(fromJsonIncident.priorityScore, equals(incident.priorityScore));
    });

    test('parses list of incidents synchronously', () {
      final rawJsonList = jsonEncode([
        {
          'id': 'inc-001',
          'tenant_id': '00000000-0000-0000-0000-000000000001',
          'title': 'Test 1',
          'category': 'RESCUE',
          'severity': 'HIGH',
          'status': 'REPORTED',
          'latitude': 26.18,
          'longitude': 91.74,
          'people_at_risk': 2,
          'priority_score': 65.0,
          'created_at': '2026-09-01T12:00:00Z',
        },
        {
          'id': 'inc-002',
          'tenant_id': '00000000-0000-0000-0000-000000000001',
          'title': 'Test 2',
          'category': 'MEDICAL',
          'severity': 'CRITICAL',
          'status': 'TRIAGED',
          'latitude': 26.19,
          'longitude': 91.75,
          'people_at_risk': 1,
          'priority_score': 90.0,
          'created_at': '2026-09-01T12:05:00Z',
        }
      ]);

      final list = IncidentModel.parseList(rawJsonList);
      expect(list.length, equals(2));
      expect(list[0].id, equals('inc-001'));
      expect(list[1].category, equals('MEDICAL'));
    });
  });

  group('EventEnvelopeModel Serialization', () {
    test('serializes vector clocks and nested payload', () {
      final event = EventEnvelopeModel(
        eventId: 'EVT-001',
        tenantId: '00000000-0000-0000-0000-000000000001',
        entityType: 'INCIDENT',
        entityId: 'inc-001',
        eventType: 'INCIDENT_REPORTED',
        actorId: 'usr-001',
        deviceId: 'dev-001',
        lamportClock: 4,
        vectorClock: {'dev-001': 4, 'dev-002': 2},
        payload: {'status': 'REPORTED', 'location': 'Sector 4'},
        integrityHash: 'a' * 64,
        occurredAt: '2026-09-01T12:00:00Z',
      );

      final jsonMap = event.toJson();
      final roundTrip = EventEnvelopeModel.fromJson(jsonMap);

      expect(roundTrip.eventId, equals('EVT-001'));
      expect(roundTrip.vectorClock['dev-001'], equals(4));
      expect(roundTrip.vectorClock['dev-002'], equals(2));
      expect(roundTrip.payload['status'], equals('REPORTED'));
    });
  });
}
