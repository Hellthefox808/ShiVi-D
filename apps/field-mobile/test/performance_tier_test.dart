import 'package:flutter_test/flutter_test.dart';
import 'package:field_mobile/core/device/performance_tier.dart';

void main() {
  group('Device Performance Profile Tiering', () {
    test('low tier enforces strict RAM and concurrency limits', () {
      final lowProfile = PerformanceProfile.forTier(DeviceTier.low);
      expect(lowProfile.tier, equals(DeviceTier.low));
      expect(lowProfile.maxConcurrentSyncRequests, equals(1));
      expect(lowProfile.imageMaxDimension, equals(800));
      expect(lowProfile.imageCompressionQuality, equals(50));
      expect(lowProfile.enableComplexAnimations, isFalse);
      expect(lowProfile.enableBackdropBlur, isFalse);
      expect(lowProfile.mapTileCacheLimitMB, equals(50));
      expect(lowProfile.batchSyncChunkSize, equals(10));
      expect(lowProfile.minBatteryThresholdForSync, equals(20));
    });

    test('high tier unlocks 60/120fps animations and high resolution caching', () {
      final highProfile = PerformanceProfile.forTier(DeviceTier.high);
      expect(highProfile.tier, equals(DeviceTier.high));
      expect(highProfile.maxConcurrentSyncRequests, equals(4));
      expect(highProfile.imageMaxDimension, equals(2048));
      expect(highProfile.imageCompressionQuality, equals(90));
      expect(highProfile.enableComplexAnimations, isTrue);
      expect(highProfile.enableBackdropBlur, isTrue);
      expect(highProfile.mapTileCacheLimitMB, equals(500));
      expect(highProfile.batchSyncChunkSize, equals(50));
    });
  });
}
