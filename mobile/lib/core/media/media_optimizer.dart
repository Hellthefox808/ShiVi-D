import 'dart:typed_data';
import 'package:crypto/crypto.dart';
import 'package:flutter/foundation.dart';
import '../device/performance_tier.dart';

class MediaOptimizationResult {
  final Uint8List optimizedBytes;
  final String sha256Hash;
  final int byteSize;

  const MediaOptimizationResult({
    required this.optimizedBytes,
    required this.sha256Hash,
    required this.byteSize,
  });
}

class MediaOptimizer {
  /// Offload hash computation to a background isolate to keep UI thread 60fps
  static Future<String> computeSha256InBackground(Uint8List bytes) async {
    return compute(_calculateHash, bytes);
  }

  static String _calculateHash(Uint8List bytes) {
    return sha256.convert(bytes).toString();
  }

  /// Optimizes media based on the detected hardware performance tier
  static Future<MediaOptimizationResult> optimizeForTier({
    required Uint8List rawBytes,
    required PerformanceProfile profile,
  }) async {
    // In production, flutter_image_compress or image package can downsample dimensions.
    // Hash is calculated immediately and deterministically.
    final hash = await computeSha256InBackground(rawBytes);

    return MediaOptimizationResult(
      optimizedBytes: rawBytes,
      sha256Hash: hash,
      byteSize: rawBytes.lengthInBytes,
    );
  }
}
