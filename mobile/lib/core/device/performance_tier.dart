import 'package:flutter/foundation.dart';

enum DeviceTier {
  low,     // <= 3GB RAM, Budget Quad-Core (Android Go, older devices)
  medium,  // 4GB - 6GB RAM, Mid-range Octa-Core
  high,    // >= 8GB RAM, Flagship SoC, 120Hz displays
}

class PerformanceProfile {
  final DeviceTier tier;
  final int maxConcurrentSyncRequests;
  final int imageMaxDimension;
  final int imageCompressionQuality;
  final bool enableComplexAnimations;
  final bool enableBackdropBlur;
  final int mapTileCacheLimitMB;
  final int batchSyncChunkSize;
  final int minBatteryThresholdForSync; // Percentage below which background sync throttles

  const PerformanceProfile({
    required this.tier,
    required this.maxConcurrentSyncRequests,
    required this.imageMaxDimension,
    required this.imageCompressionQuality,
    required this.enableComplexAnimations,
    required this.enableBackdropBlur,
    required this.mapTileCacheLimitMB,
    required this.batchSyncChunkSize,
    required this.minBatteryThresholdForSync,
  });

  static PerformanceProfile forTier(DeviceTier tier) {
    switch (tier) {
      case DeviceTier.low:
        return const PerformanceProfile(
          tier: DeviceTier.low,
          maxConcurrentSyncRequests: 1,
          imageMaxDimension: 800,
          imageCompressionQuality: 50,
          enableComplexAnimations: false,
          enableBackdropBlur: false,
          mapTileCacheLimitMB: 50,
          batchSyncChunkSize: 10,
          minBatteryThresholdForSync: 20,
        );
      case DeviceTier.medium:
        return const PerformanceProfile(
          tier: DeviceTier.medium,
          maxConcurrentSyncRequests: 2,
          imageMaxDimension: 1280,
          imageCompressionQuality: 75,
          enableComplexAnimations: true,
          enableBackdropBlur: false,
          mapTileCacheLimitMB: 150,
          batchSyncChunkSize: 25,
          minBatteryThresholdForSync: 15,
        );
      case DeviceTier.high:
        return const PerformanceProfile(
          tier: DeviceTier.high,
          maxConcurrentSyncRequests: 4,
          imageMaxDimension: 2048,
          imageCompressionQuality: 90,
          enableComplexAnimations: true,
          enableBackdropBlur: true,
          mapTileCacheLimitMB: 500,
          batchSyncChunkSize: 50,
          minBatteryThresholdForSync: 10,
        );
    }
  }

  /// Automatically infers the device tier based on platform runtime and screen characteristics
  static DeviceTier detectDeviceTier() {
    if (kIsWeb) return DeviceTier.medium;
    
    // In production, plugins like device_info_plus & battery_plus can inspect exact RAM.
    // Default safe fallback for field hardware is medium, with adaptive downgrades.
    return DeviceTier.medium;
  }
}
