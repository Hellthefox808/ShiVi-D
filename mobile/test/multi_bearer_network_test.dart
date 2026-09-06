import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:shivi_field_mobile/core/network/network_bearer.dart';
import 'package:shivi_field_mobile/core/network/bluetooth_mesh_framing.dart';

void main() {
  group('Multi-Bearer Network Manager Tests', () {
    late NetworkBearerManager manager;

    setUp(() {
      manager = NetworkBearerManager();
    });

    tearDown(() {
      manager.dispose();
    });

    test('Prioritizes Wi-Fi Internet when available', () {
      final bearer = manager.determineOptimalBearer(
        hasWifiInternet: true,
        hasCellularData: true,
        isCellularHighSpeed: true,
        hasSatelliteLock: true,
        hasNearbyWifiDirectPeers: true,
        hasNearbyBlePeers: true,
        batteryLevel: 0.85,
      );

      expect(bearer, NetworkBearerType.wifiInternet);
      expect(NetworkBearerProfile.getProfile(bearer).requiresInternet, isTrue);
    });

    test('Selects 4G/5G Cellular when Wi-Fi is lost', () {
      final bearer = manager.determineOptimalBearer(
        hasWifiInternet: false,
        hasCellularData: true,
        isCellularHighSpeed: true,
        hasSatelliteLock: false,
        hasNearbyWifiDirectPeers: true,
        hasNearbyBlePeers: true,
        batteryLevel: 0.50,
      );

      expect(bearer, NetworkBearerType.cellular4G5G);
    });

    test('Falls back to Wi-Fi Direct Mesh when internet is completely down but battery > 20%', () {
      final bearer = manager.determineOptimalBearer(
        hasWifiInternet: false,
        hasCellularData: false,
        isCellularHighSpeed: false,
        hasSatelliteLock: false,
        hasNearbyWifiDirectPeers: true,
        hasNearbyBlePeers: true,
        batteryLevel: 0.40,
      );

      expect(bearer, NetworkBearerType.wifiDirectMesh);
      expect(NetworkBearerProfile.getProfile(bearer).isPeerToPeer, isTrue);
    });

    test('Selects Ultra-Low-Power BLE Mesh when battery is low (< 20%) or only BLE peers present', () {
      final bearer = manager.determineOptimalBearer(
        hasWifiInternet: false,
        hasCellularData: false,
        isCellularHighSpeed: false,
        hasSatelliteLock: false,
        hasNearbyWifiDirectPeers: true,
        hasNearbyBlePeers: true,
        batteryLevel: 0.12, // Low battery forces BLE mesh
      );

      expect(bearer, NetworkBearerType.bluetoothMesh);
      expect(NetworkBearerProfile.getProfile(bearer).batteryCostLevel, 1);
    });

    test('Reports Disconnected when no radios or peers are reachable', () {
      final bearer = manager.determineOptimalBearer(
        hasWifiInternet: false,
        hasCellularData: false,
        isCellularHighSpeed: false,
        hasSatelliteLock: false,
        hasNearbyWifiDirectPeers: false,
        hasNearbyBlePeers: false,
        batteryLevel: 0.50,
      );

      expect(bearer, NetworkBearerType.disconnected);
    });
  });

  group('Bluetooth Low Energy (BLE) Mesh Framing & CRC-32 Tests', () {
    test('Calculates consistent IEEE 802.3 CRC-32 checksums', () {
      final data = utf8.encode('ShiVi Emergency Disaster Mesh Protocol');
      final crc = Crc32Calculator.compute(data);
      expect(crc, isNonZero);
      expect(Crc32Calculator.compute(data), equals(crc));
    });

    test('Fragments and reassembles payload over BLE chunks with 100% integrity', () {
      final engine = BleMeshFramingEngine();
      final largePayload = jsonEncode({
        'incident_id': 'INC-CYCLONE-GUWAHATI-99',
        'category': 'RESCUE',
        'severity': 'CRITICAL',
        'people_at_risk': 14,
        'description': 'Bridge collapsed over Brahmaputra tributary. 14 people stranded on rooftop.',
        'coordinates': [91.7362, 26.1856],
        'notes': List.generate(20, (i) => 'Field observation report sequence note $i'),
      });

      // Split into small 100-byte chunks to test multi-frame fragmentation
      final chunks = BleMeshFramingEngine.fragmentPayload(
        rawContent: largePayload,
        maxChunkSize: 100,
      );

      expect(chunks.length, greaterThan(3));

      // Reassemble chunks
      String? result;
      for (final chunk in chunks) {
        // Serialize to wire bytes and deserialize back
        final wireBytes = chunk.toBytes();
        final parsedChunk = BleMeshChunk.fromBytes(wireBytes);
        result = engine.ingestChunk(parsedChunk);
      }

      expect(result, isNotNull);
      expect(result, equals(largePayload));

      final decodedMap = jsonDecode(result!) as Map<String, dynamic>;
      expect(decodedMap['incident_id'], 'INC-CYCLONE-GUWAHATI-99');
      expect(decodedMap['people_at_risk'], 14);
    });

    test('Rejects corrupted chunks with CRC-32 mismatch', () {
      final engine = BleMeshFramingEngine();
      const payload = 'Emergency SOS Alert Payload';
      final chunks = BleMeshFramingEngine.fragmentPayload(rawContent: payload, maxChunkSize: 50);

      // Corrupt byte in payload
      final chunk0 = chunks[0];
      final corruptedPayload = Uint8List.fromList(chunk0.payload);
      corruptedPayload[0] ^= 0xFF; // Flip bits

      final corruptedChunk = BleMeshChunk(
        packetId: chunk0.packetId,
        totalChunks: chunk0.totalChunks,
        chunkIndex: chunk0.chunkIndex,
        crc32: chunk0.crc32, // Original CRC
        payload: corruptedPayload,
      );

      expect(() => engine.ingestChunk(corruptedChunk), throwsA(isA<StateError>()));
    });
  });
}
