import 'package:flutter_test/flutter_test.dart';
import 'package:shivi_field_mobile/core/database/local_database_repository.dart';

void main() {
  group('Deterministic Triage Priority Scoring (Research Paper Formula)', () {
    test('Calculates max priority for RESCUE + CRITICAL + >=10 people at risk', () {
      final score = LocalDatabaseRepository.calculatePriorityScore(
        category: 'RESCUE',
        severity: 'CRITICAL',
        peopleAtRisk: 10,
      );

      // Category RESCUE = 15.0, Severity CRITICAL = 30.0, People (10 * 2.5 = 25.0 capped at 25.0)
      // Total = 15 + 30 + 25 = 70.0
      expect(score, equals(70.0));
    });

    test('Caps people at risk contribution at 25.0 for large casualty counts', () {
      final score10 = LocalDatabaseRepository.calculatePriorityScore(
        category: 'RESCUE',
        severity: 'CRITICAL',
        peopleAtRisk: 10,
      );
      final score100 = LocalDatabaseRepository.calculatePriorityScore(
        category: 'RESCUE',
        severity: 'CRITICAL',
        peopleAtRisk: 100,
      );

      expect(score100, equals(score10));
      expect(score100, equals(70.0));
    });

    test('Zero people at risk contributes 0.0 without errors', () {
      final score = LocalDatabaseRepository.calculatePriorityScore(
        category: 'MEDICAL',
        severity: 'HIGH',
        peopleAtRisk: 0,
      );

      // MEDICAL = 12.0, HIGH = 20.0, People = 0.0 -> Total = 32.0
      expect(score, equals(32.0));
    });

    test('Evaluates intermediate hazard and relief scenarios accurately', () {
      // HAZARD = 10.0, MEDIUM = 12.0, 2 people = 5.0 -> Total = 27.0
      final hazardScore = LocalDatabaseRepository.calculatePriorityScore(
        category: 'HAZARD',
        severity: 'MEDIUM',
        peopleAtRisk: 2,
      );
      expect(hazardScore, equals(27.0));

      // RELIEF = 6.0, LOW = 5.0, 4 people = 10.0 -> Total = 21.0
      final reliefScore = LocalDatabaseRepository.calculatePriorityScore(
        category: 'RELIEF',
        severity: 'LOW',
        peopleAtRisk: 4,
      );
      expect(reliefScore, equals(21.0));
    });

    test('Case-insensitivity handles user input variations gracefully', () {
      final scoreUpper = LocalDatabaseRepository.calculatePriorityScore(
        category: 'rescue',
        severity: 'critical',
        peopleAtRisk: 3,
      );
      final scoreLower = LocalDatabaseRepository.calculatePriorityScore(
        category: 'RESCUE',
        severity: 'CRITICAL',
        peopleAtRisk: 3,
      );

      expect(scoreUpper, equals(scoreLower));
      // 15 + 30 + (3 * 2.5 = 7.5) = 52.5
      expect(scoreUpper, equals(52.5));
    });

    test('Gracefully defaults unmapped categories and severities to lowest weights', () {
      final score = LocalDatabaseRepository.calculatePriorityScore(
        category: 'OTHER_MISC',
        severity: 'UNKNOWN',
        peopleAtRisk: 1,
      );

      // Default cat = 5.0, Default sev = 5.0, People (1 * 2.5 = 2.5) -> Total = 12.5
      expect(score, equals(12.5));
    });
  });
}
