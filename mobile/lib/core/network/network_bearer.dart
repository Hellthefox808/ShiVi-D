import 'dart:async';

/// Supported network bearer types in the ShiVi disaster mesh architecture
enum NetworkBearerType {
  wifiInternet,    // High-speed broadband / Wi-Fi with internet access
  cellular4G5G,    // High-bandwidth LTE / 5G cellular network
  cellular2G3G,    // Low-bandwidth constrained 2G/EDGE or 3G cellular
  satelliteNTN,    // Ultra-low bandwidth satellite non-terrestrial network
  wifiDirectMesh,  // Peer-to-peer Wi-Fi Direct / Local ad-hoc hotspot (no internet required)
  bluetoothMesh,   // Bluetooth Low Energy (BLE) / Bluetooth Classic P2P mesh
  disconnected,    // Completely isolated (pure offline local storage)
}

/// Profile describing bandwidth, packet MTU, and battery cost of a bearer
class NetworkBearerProfile {
  final NetworkBearerType type;
  final int maxPayloadBytes;      // Safe MTU for single unfragmented transmission
  final bool requiresInternet;    // True if cloud connection is needed
  final bool isPeerToPeer;        // True if direct device-to-device radio
  final int batteryCostLevel;     // 1 (Ultra Low BLE) to 5 (Satellite/High-TX Wi-Fi Direct)
  final String humanReadableName;

  const NetworkBearerProfile({
    required this.type,
    required this.maxPayloadBytes,
    required this.requiresInternet,
    required this.isPeerToPeer,
    required this.batteryCostLevel,
    required this.humanReadableName,
  });

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
      case NetworkBearerType.wifiDirectMesh:
        return wifiDirectMesh;
      case NetworkBearerType.bluetoothMesh:
        return bluetoothMesh;
      case NetworkBearerType.disconnected:
        return disconnected;
    }
  }
}

/// Adaptive Bearer Manager with radio-priority decision hierarchy
class NetworkBearerManager {
  NetworkBearerType _activeBearer = NetworkBearerType.disconnected;
  final _bearerStreamController = StreamController<NetworkBearerType>.broadcast();

  NetworkBearerType get activeBearer => _activeBearer;
  Stream<NetworkBearerType> get onBearerChanged => _bearerStreamController.stream;
  NetworkBearerProfile get activeProfile => NetworkBearerProfile.getProfile(_activeBearer);

  /// Selects the most optimal available network bearer according to life-safety priority
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

  /// Updates active bearer state and notifies listeners
  void setActiveBearer(NetworkBearerType bearer) {
    if (_activeBearer != bearer) {
      _activeBearer = bearer;
      _bearerStreamController.add(bearer);
    }
  }

  void dispose() {
    _bearerStreamController.close();
  }
}
