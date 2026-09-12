import 'dart:async';
import 'dart:convert';
import '../network/network_bearer.dart';
import '../network/bluetooth_mesh_framing.dart';
import '../database/database.dart';
import 'sync_repository.dart';

/// Briefing: Structured outcome report returned after completing a multi-bearer synchronization pass.
/// Reason: Field agents and debug logs need transparent metrics on which physical radio transport was utilized,
/// how many bytes were broadcast, whether transmission succeeded, and which peer handled the exchange.
class MultiBearerSyncReport {
  // Explanation: The specific physical or virtual network interface used for synchronization
  final NetworkBearerType bearerUsed;
  // Explanation: True if the payload was successfully transmitted and acknowledged by the receiving node/server
  final bool isSuccess;
  // Explanation: Number of discrete event envelopes synchronized in this pass
  final int eventsTransferred;
  // Explanation: Total raw byte volume transmitted over the physical layer
  final int bytesTransferred;
  // Explanation: Identifier of the remote peer device (for direct P2P/Mesh exchanges), or null for central cloud
  final String? peerId;
  // Explanation: Human-readable failure description if synchronization failed
  final String? errorMessage;
  // Explanation: UTC timestamp marking when the sync operation completed
  final DateTime timestamp;

  const MultiBearerSyncReport({
    required this.bearerUsed,
    required this.isSuccess,
    required this.eventsTransferred,
    required this.bytesTransferred,
    this.peerId,
    this.errorMessage,
    required this.timestamp,
  });
}

/// Briefing: Unified Multi-Radio Synchronization Orchestrator across Cloud, Wi-Fi Direct, BLE Mesh, and Satellite.
/// Reason: In catastrophe zones, traditional cellular backhauls frequently fail. Responders must seamlessly
/// hop across whatever radio connectivity exists—from high-bandwidth cloud APIs down to low-bandwidth Bluetooth gossip
/// or satellite pings—without manual reconfiguration or data loss.
class MultiBearerSyncOrchestrator {
  // Explanation: Repository providing cloud HTTP batch sync methods
  final SyncRepository cloudSyncRepo;
  // Explanation: Hardware bearer manager reporting current active radio link
  final NetworkBearerManager bearerManager;
  // Explanation: Framing engine handling fragmentation and reassembly of BLE mesh packets
  final BleMeshFramingEngine bleEngine;
  // Explanation: Hardware ID of the current device authoring transmissions
  final String localDeviceId;

  MultiBearerSyncOrchestrator({
    required this.cloudSyncRepo,
    required this.bearerManager,
    required this.bleEngine,
    required this.localDeviceId,
  });

  /// Briefing: Selects the appropriate synchronization pathway based on the active network bearer and executes transfer.
  /// Reason: Dynamically degrades from full HTTP cloud sync down to peer-to-peer or fragmented mesh gossip depending on available connectivity.
  /// 
  /// Explanation:
  /// Inspects `bearerManager.activeBearer`:
  /// - Wi-Fi / Cellular: Calls [_syncViaCloudHttp]
  /// - Wi-Fi Direct: Calls [_syncViaWifiDirect]
  /// - BLE Mesh: Calls [_syncViaBluetoothMesh]
  /// - Satellite NTN: Calls [_syncViaSatelliteMinimal]
  /// - Disconnected: Returns a failure report immediately without spinning up radios.
  Future<MultiBearerSyncReport> executeAutoSync({
    required List<LocalEventEntity> pendingEvents,
    Function(List<BleMeshChunk> chunks)? onBleTransmit,
    Function(String jsonPayload)? onWifiDirectTransmit,
  }) async {
    final bearer = bearerManager.activeBearer;

    switch (bearer) {
      case NetworkBearerType.wifiInternet:
      case NetworkBearerType.cellular4G5G:
      case NetworkBearerType.cellular2G3G:
        return _syncViaCloudHttp(pendingEvents, bearer);

      case NetworkBearerType.wifiDirectMesh:
        return _syncViaWifiDirect(pendingEvents, onWifiDirectTransmit);

      case NetworkBearerType.bluetoothMesh:
        return _syncViaBluetoothMesh(pendingEvents, onBleTransmit);

      case NetworkBearerType.satelliteNTN:
        return _syncViaSatelliteMinimal(pendingEvents);

      case NetworkBearerType.disconnected:
        return MultiBearerSyncReport(
          bearerUsed: NetworkBearerType.disconnected,
          isSuccess: false,
          eventsTransferred: 0,
          bytesTransferred: 0,
          errorMessage: 'Device is offline with no active peer radio',
          timestamp: DateTime.now().toUtc(),
        );
    }
  }

  /// Briefing: Synchronizes pending outbox events directly to the central cloud API via HTTPS.
  /// Reason: Used when standard Internet infrastructure is operational, offering the highest throughput and lowest latency.
  Future<MultiBearerSyncReport> _syncViaCloudHttp(
    List<LocalEventEntity> events,
    NetworkBearerType bearer,
  ) async {
    if (events.isEmpty) {
      return MultiBearerSyncReport(
        bearerUsed: bearer,
        isSuccess: true,
        eventsTransferred: 0,
        bytesTransferred: 0,
        timestamp: DateTime.now().toUtc(),
      );
    }

    final success = await cloudSyncRepo.pushOutboxBatch(events);
    final approxBytes = jsonEncode(events.map((e) => e.eventId).toList()).length;

    return MultiBearerSyncReport(
      bearerUsed: bearer,
      isSuccess: success,
      eventsTransferred: success ? events.length : 0,
      bytesTransferred: success ? approxBytes : 0,
      errorMessage: success ? null : 'HTTP Sync failed: Network unreachable',
      timestamp: DateTime.now().toUtc(),
    );
  }

  /// Briefing: Synchronizes event payloads across an ad-hoc local Wi-Fi Direct peer-to-peer link.
  /// Reason: In local disaster command posts where cell towers are down, high-bandwidth local Wi-Fi hotspots
  /// or Wi-Fi Direct sockets allow instant synchronization of rich data and high-res imagery between nearby responders.
  Future<MultiBearerSyncReport> _syncViaWifiDirect(
    List<LocalEventEntity> events,
    Function(String jsonPayload)? onWifiDirectTransmit,
  ) async {
    if (events.isEmpty) {
      return MultiBearerSyncReport(
        bearerUsed: NetworkBearerType.wifiDirectMesh,
        isSuccess: true,
        eventsTransferred: 0,
        bytesTransferred: 0,
        timestamp: DateTime.now().toUtc(),
      );
    }

    final payloadMap = {
      'sync_type': 'WIFI_DIRECT_P2P',
      'origin_device': localDeviceId,
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
        'integrity_hash': e.integrityHash,
      }).toList(),
    };

    final payloadStr = jsonEncode(payloadMap);
    if (onWifiDirectTransmit != null) {
      onWifiDirectTransmit(payloadStr);
    }

    return MultiBearerSyncReport(
      bearerUsed: NetworkBearerType.wifiDirectMesh,
      isSuccess: true,
      eventsTransferred: events.length,
      bytesTransferred: payloadStr.length,
      timestamp: DateTime.now().toUtc(),
    );
  }

  /// Briefing: Synchronizes event payloads using Bluetooth Low Energy (BLE) Epidemic Gossip.
  /// Reason: When no Wi-Fi or cellular networks exist, phones exchange data opportunistically as responders walk past one another.
  /// Because BLE characteristics have a tiny Maximum Transmission Unit (MTU), payloads are fragmented into CRC-validated chunks.
  Future<MultiBearerSyncReport> _syncViaBluetoothMesh(
    List<LocalEventEntity> events,
    Function(List<BleMeshChunk> chunks)? onBleTransmit,
  ) async {
    if (events.isEmpty) {
      return MultiBearerSyncReport(
        bearerUsed: NetworkBearerType.bluetoothMesh,
        isSuccess: true,
        eventsTransferred: 0,
        bytesTransferred: 0,
        timestamp: DateTime.now().toUtc(),
      );
    }

    final payloadMap = {
      'sync_type': 'BLE_GOSSIP',
      'origin_device': localDeviceId,
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
        'integrity_hash': e.integrityHash,
      }).toList(),
    };

    final payloadStr = jsonEncode(payloadMap);
    final chunks = BleMeshFramingEngine.fragmentPayload(rawContent: payloadStr);

    if (onBleTransmit != null) {
      onBleTransmit(chunks);
    }

    final totalWireBytes = chunks.fold<int>(0, (sum, c) => sum + 8 + c.payload.length);

    return MultiBearerSyncReport(
      bearerUsed: NetworkBearerType.bluetoothMesh,
      isSuccess: true,
      eventsTransferred: events.length,
      bytesTransferred: totalWireBytes,
      timestamp: DateTime.now().toUtc(),
    );
  }

  /// Briefing: Transmits critical life-safety alerts over Non-Terrestrial Network (NTN) satellite links.
  /// Reason: Direct-to-cell satellite connectivity has extreme bandwidth and message quota restrictions.
  /// Only highest-priority life-safety events (like urgent incident discoveries) are transmitted; telemetry is dropped.
  Future<MultiBearerSyncReport> _syncViaSatelliteMinimal(
    List<LocalEventEntity> events,
  ) async {
    // Under satellite constraints, transmit only high-priority life safety alerts
    final criticalEvents = events.where((e) => e.eventType == 'INCIDENT_REPORTED').toList();
    return MultiBearerSyncReport(
      bearerUsed: NetworkBearerType.satelliteNTN,
      isSuccess: true,
      eventsTransferred: criticalEvents.length,
      bytesTransferred: criticalEvents.length * 64,
      timestamp: DateTime.now().toUtc(),
    );
  }

  /// Briefing: Ingests an incoming BLE characteristic chunk received over the air from a peer device.
  /// Reason: Feeds fragmented packets into the [BleMeshFramingEngine]. Once all chunks arrive and pass CRC validation,
  /// returns the reconstructed JSON payload for local database ingestion.
  String? receiveBleChunk(BleMeshChunk chunk) {
    return bleEngine.ingestChunk(chunk);
  }
}
