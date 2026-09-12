import 'dart:typed_data';
import 'package:crypto/crypto.dart';
import 'package:flutter/foundation.dart';
import '../device/performance_tier.dart';

/// Briefing: Container for optimized media payload and metadata.
/// Reason: When media is taken, we need both the byte data for upload and its SHA-256 hash for deduplication
/// and content-addressable storage on the backend.
class MediaOptimizationResult {
  // Explanation: The compressed or raw bytes of the media
  final Uint8List optimizedBytes;
  // Explanation: Cryptographic hash of the bytes, used for deduplication in the event log
  final String sha256Hash;
  // Explanation: The size of the payload in bytes
  final int byteSize;

  const MediaOptimizationResult({
    required this.optimizedBytes,
    required this.sha256Hash,
    required this.byteSize,
  });
}

/// Briefing: Utility class for processing media files (images, audio) before they enter the sync queue.
/// Reason: Raw images from a modern smartphone camera can be 10MB+. Syncing this over a poor connection
/// will block the outbox. This optimizer downsamples media based on the device's [PerformanceProfile].
class MediaOptimizer {
  /// Briefing: Computes a cryptographic hash of the given bytes.
  /// Explanation: Offloads hash computation to a background isolate (using `compute`) to keep the UI thread running at 60fps,
  /// as hashing megabytes of data on the main thread would cause frame drops.
  static Future<String> computeSha256InBackground(Uint8List bytes) async {
    return compute(_calculateHash, bytes);
  }

  static String _calculateHash(Uint8List bytes) {
    return sha256.convert(bytes).toString();
  }

  /// Briefing: Optimizes media payload size and dimensions based on the detected hardware performance tier.
  /// Explanation: In a real implementation, this would use the provided [PerformanceProfile] to limit
  /// max dimensions and apply JPEG compression. Currently, it just computes the hash in the background.
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

