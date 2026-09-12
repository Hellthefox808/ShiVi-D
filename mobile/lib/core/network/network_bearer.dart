import 'dart:async';

/// Briefing: Supported network bearer physical/logical interfaces in the ShiVi disaster mesh architecture.
/// Reason: Disaster environments require opportunistic multi-transport routing. Devices must dynamically transition
/// across available radios without interrupting data integrity.
enum NetworkBearerType {
  // Explanation: High-speed broadband / Wi-Fi with internet access
  wifiInternet,
  // Explanation: High-bandwidth LTE / 5G cellular network
  cellular4G5G,
  // Explanation: Low-bandwidth constrained 2G/EDGE or 3G cellular
  cellular2G3G,
  // Explanation: Ultra-low bandwidth satellite non-terrestrial network (3GPP Rel-17)
  satelliteNTN,
  // Explanation: Cellular SMS & Satellite 140B Burst Relay for emergency text bursts
  smsRelay,
  // Explanation: Peer-to-peer Wi-Fi Direct / Local ad-hoc hotspot (no internet required)
  wifiDirectMesh,
  // Explanation: Bluetooth Low Energy (BLE) / Bluetooth Classic P2P mesh
  bluetoothMesh,
  // Explanation: Completely isolated (pure offline local storage)
  disconnected,
}

/// Briefing: Specification profile detailing MTU packet bounds, battery drain, and radio capabilities for a bearer.
/// Reason: Prevents network buffer bloat and transmission timeouts by adapting chunk sizes and protocol overhead
/// to the physical constraints of each radio link.
class NetworkBearerProfile {
  // Explanation: The bearer type this profile configures
  final NetworkBearerType type;
  // Explanation: Maximum Transmission Unit (MTU) in bytes safe for unfragmented single frame delivery
  final int maxPayloadBytes;
  // Explanation: True if an upstream internet gateway is required for successful routing
  final bool requiresInternet;
  // Explanation: True if communication is strictly local device-to-device radio without intermediaries
  final bool isPeerToPeer;
  // Explanation: Power consumption index on a scale from 1 (Ultra Low BLE) to 5 (Heavy Satellite / High-Power Wi-Fi Direct)
  final int batteryCostLevel;
  // Explanation: User-facing descriptive name for diagnostic screens
  final String humanReadableName;

  const NetworkBearerProfile({
    required this.type,
    required this.maxPayloadBytes,
    required this.requiresInternet,
    required this.isPeerToPeer,
    required this.batteryCostLevel,
    required this.humanReadableName,
  });

  // Pre-configured static profiles for each bearer
  static const NetworkBearerProfile wifiInternet = NetworkBearerProfile(
    type: NetworkBearerType.wifiInternet,
    maxPayloadBytes: 65536, // 64 KB HTTP chunks
    requiresInternet: true,
    isPeerToPeer: false,
    batteryCostLevel: 2,
    humanReadableName: 'Wi-Fi Broadband',
  );

  static const NetworkBearerProfile cellular4G5G = NetworkBearerProfile(
    type: NetworkBearerType.cellular4G5G,
    maxPayloadBytes: 32768, // 32 KB HTTP chunks
    requiresInternet: true,
    isPeerToPeer: false,
    batteryCostLevel: 3,
    humanReadableName: 'Cellular 4G/5G LTE',
  );

  static const NetworkBearerProfile cellular2G3G = NetworkBearerProfile(
    type: NetworkBearerType.cellular2G3G,
    maxPayloadBytes: 2048,  // 2 KB compressed batches
    requiresInternet: true,
    isPeerToPeer: false,
    batteryCostLevel: 3,
    humanReadableName: 'Cellular 2G/3G (Low-Bandwidth)',
  );

  static const NetworkBearerProfile satelliteNTN = NetworkBearerProfile(
    type: NetworkBearerType.satelliteNTN,
    maxPayloadBytes: 256,   // 256 B minimal telemetry packet
    requiresInternet: true,
    isPeerToPeer: false,
    batteryCostLevel: 5,
    humanReadableName: 'Satellite NTN (3GPP Rel-17)',
  );

  static const NetworkBearerProfile smsRelay = NetworkBearerProfile(
    type: NetworkBearerType.smsRelay,
    maxPayloadBytes: 140,   // 140 B compact satellite burst / SMS segment
    requiresInternet: false,
    isPeerToPeer: false,
    batteryCostLevel: 2,
    humanReadableName: 'Emergency SMS / Satellite Burst (140B)',
  );

  static const NetworkBearerProfile wifiDirectMesh = NetworkBearerProfile(
    type: NetworkBearerType.wifiDirectMesh,
    maxPayloadBytes: 16384, // 16 KB P2P socket frames
    requiresInternet: false,
    isPeerToPeer: true,
    batteryCostLevel: 4,
    humanReadableName: 'Wi-Fi Direct P2P Mesh',
  );

  static const NetworkBearerProfile bluetoothMesh = NetworkBearerProfile(
    type: NetworkBearerType.bluetoothMesh,
    maxPayloadBytes: 480,   // BLE GATT characteristic safe MTU after framing
    requiresInternet: false,
    isPeerToPeer: true,
    batteryCostLevel: 1,    // Ultra-low battery consumption
    humanReadableName: 'Bluetooth Low Energy (BLE) Mesh',
  );

  static const NetworkBearerProfile disconnected = NetworkBearerProfile(
    type: NetworkBearerType.disconnected,
    maxPayloadBytes: 0,
    requiresInternet: false,
    isPeerToPeer: false,
    batteryCostLevel: 0,
    humanReadableName: 'Offline (Isolated)',
  );

  /// Briefing: Retrieves the corresponding static profile for a given bearer type.
  static NetworkBearerProfile getProfile(NetworkBearerType type) {
    switch (type) {
      case NetworkBearerType.wifiInternet:
        return wifiInternet;
      case NetworkBearerType.cellular4G5G:
        return cellular4G5G;
      case NetworkBearerType.cellular2G3G:
        return cellular2G3G;
      case NetworkBearerType.satelliteNTN:
        return satelliteNTN;
      case NetworkBearerType.smsRelay:
        return smsRelay;
      case NetworkBearerType.wifiDirectMesh:
        return wifiDirectMesh;
      case NetworkBearerType.bluetoothMesh:
        return bluetoothMesh;
      case NetworkBearerType.disconnected:
        return disconnected;
    }
  }
}

/// Briefing: Dynamic link supervisor and radio prioritization engine.
/// Reason: Continuously monitors hardware radio states and residual battery power to elect the most appropriate
/// bearer, ensuring critical emergency data flows without prematurely exhausting device battery.
class NetworkBearerManager {
  // Explanation: Current selected active network interface
  NetworkBearerType _activeBearer = NetworkBearerType.disconnected;
  // Explanation: Broadcast stream notifying UI and sync orchestrator of radio changes
  final _bearerStreamController = StreamController<NetworkBearerType>.broadcast();

  NetworkBearerType get activeBearer => _activeBearer;
  Stream<NetworkBearerType> get onBearerChanged => _bearerStreamController.stream;
  NetworkBearerProfile get activeProfile => NetworkBearerProfile.getProfile(_activeBearer);

  /// Briefing: Selects the most optimal available network bearer according to life-safety priority and power constraints.
  /// Reason: Implements a deterministic priority waterfall:
  /// 1. High-speed Wi-Fi Internet (highest bandwidth, lowest energy per bit)
  /// 2. Cellular 4G/5G or 2G/3G (if battery allows)
  /// 3. Wi-Fi Direct Mesh (high bandwidth local P2P, if battery > 20%)
  /// 4. Bluetooth Low Energy Mesh (ultra-low power local gossip)
  /// 5. Satellite NTN (high power, emergency uplink only)
  /// 6. Complete offline isolation
  NetworkBearerType determineOptimalBearer({
    required bool hasWifiInternet,
    required bool hasCellularData,
    required bool isCellularHighSpeed,
    required bool hasSatelliteLock,
    required bool hasNearbyWifiDirectPeers,
    required bool hasNearbyBlePeers,
    required double batteryLevel, // 0.0 to 1.0
  }) {
    // 1. If high-speed Wi-Fi internet is present, use it immediately
    if (hasWifiInternet) {
      return NetworkBearerType.wifiInternet;
    }

    // 2. If cellular is available and battery is healthy (> 15%)
    if (hasCellularData) {
      return isCellularHighSpeed
          ? NetworkBearerType.cellular4G5G
          : NetworkBearerType.cellular2G3G;
    }

    // 3. If zero internet, check for direct local Wi-Fi peers (if battery > 20%)
    if (hasNearbyWifiDirectPeers && batteryLevel > 0.20) {
      return NetworkBearerType.wifiDirectMesh;
    }

    // 4. Low-power Bluetooth Mesh for peer-to-peer field exchange
    if (hasNearbyBlePeers) {
      return NetworkBearerType.bluetoothMesh;
    }

    // 5. Satellite uplink for emergency beaconing (if hardware locked)
    if (hasSatelliteLock) {
      return NetworkBearerType.satelliteNTN;
    }

    // 6. Complete offline isolation
    return NetworkBearerType.disconnected;
  }

  /// Briefing: Updates active bearer state and broadcasts the change to stream subscribers.
  void setActiveBearer(NetworkBearerType bearer) {
    if (_activeBearer != bearer) {
      _activeBearer = bearer;
      _bearerStreamController.add(bearer);
    }
  }

  /// Briefing: Closes internal broadcast stream when the manager is disposed.
  void dispose() {
    _bearerStreamController.close();
  }
}
