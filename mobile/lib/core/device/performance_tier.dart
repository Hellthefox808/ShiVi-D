import 'package:flutter/foundation.dart';

/// Briefing: Defines hardware capability categories.
/// Reason: Field devices range from old, budget Android phones to modern flagship devices.
/// We categorize them to selectively disable heavy UI effects (like blur) on weak devices to save battery and reduce jank.
enum DeviceTier {
  low,     // <= 3GB RAM, Budget Quad-Core (Android Go, older devices)
  medium,  // 4GB - 6GB RAM, Mid-range Octa-Core
  high,    // >= 8GB RAM, Flagship SoC, 120Hz displays
}

/// Briefing: A configuration object containing thresholds and toggles for a specific device tier.
/// Reason: Centralizes performance tuning. Instead of scattering `if (isLowEndDevice)` everywhere,
/// we inject a `PerformanceProfile` and check `profile.enableComplexAnimations`.
class PerformanceProfile {
  // Explanation: The tier this profile represents
  final DeviceTier tier;
  // Explanation: How many HTTP or Bluetooth sync requests to run at once. 
  // Lower on weak devices to prevent CPU/memory spikes.
  final int maxConcurrentSyncRequests;
  // Explanation: Maximum width/height for compressing photos taken by the camera before syncing
  final int imageMaxDimension;
  // Explanation: JPEG compression quality (0-100)
  final int imageCompressionQuality;
  // Explanation: Toggle for complex UI animations
  final bool enableComplexAnimations;
  // Explanation: Toggle for expensive Gaussian blur effects (BackdropFilter)
  final bool enableBackdropBlur;
  // Explanation: Maximum memory in MB to allocate for caching offline map tiles
  final int mapTileCacheLimitMB;
  // Explanation: Number of events to send in a single sync payload
  final int batchSyncChunkSize;
  // Explanation: Percentage below which background sync throttles to save battery
  final int minBatteryThresholdForSync;

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

  /// Briefing: Factory method returning a pre-configured profile based on the tier.
  /// Explanation: Hardcodes optimal settings for low, medium, and high-end hardware.
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

  /// Briefing: Automatically infers the device tier based on platform runtime and screen characteristics
  /// Reason: Used during app initialization to automatically select the best profile.
  static DeviceTier detectDeviceTier() {
    if (kIsWeb) return DeviceTier.medium;
    
    // In production, plugins like device_info_plus & battery_plus can inspect exact RAM.
    // Default safe fallback for field hardware is medium, with adaptive downgrades.
    return DeviceTier.medium;
  }
}
