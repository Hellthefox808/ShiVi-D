import 'dart:convert';
import 'dart:typed_data';

/// Briefing: Represents an atomic BLE characteristic transmission frame with compact binary header.
/// Reason: Standard Bluetooth Low Energy characteristics have tight MTU limits (typically ~512 bytes on Android/iOS).
/// To reliably broadcast multi-kilobyte disaster event envelopes, payloads must be sliced into small frames
/// stamped with packet identification, chunk indexing, and overall payload checksums.
class BleMeshChunk {
  // Explanation: 16-bit identifier grouping chunks belonging to the same root transmission
  final int packetId;      // 0 - 65535
  // Explanation: Total count of chunks comprising the complete payload (max 255 chunks)
  final int totalChunks;   // 1 - 255
  // Explanation: Zero-based sequence position of this specific chunk
  final int chunkIndex;    // 0 - (totalChunks - 1)
  // Explanation: 32-bit CRC checksum computed over the UNFRAGMENTED root payload for integrity verification
  final int crc32;
  // Explanation: The raw binary payload slice carried by this characteristic frame
  final Uint8List payload;

  const BleMeshChunk({
    required this.packetId,
    required this.totalChunks,
    required this.chunkIndex,
    required this.crc32,
    required this.payload,
  });

  /// Briefing: Serializes the frame into an 8-byte binary header followed by chunk payload.
  /// Reason: Binary packing avoids JSON/hex string bloating over radio frequencies.
  /// Layout: [packetId: 2B big-endian][totalChunks: 1B][chunkIndex: 1B][crc32: 4B big-endian][payload: NB]
  Uint8List toBytes() {
    final byteData = ByteData(8 + payload.length);
    byteData.setUint16(0, packetId, Endian.big);
    byteData.setUint8(2, totalChunks);
    byteData.setUint8(3, chunkIndex);
    byteData.setUint32(4, crc32, Endian.big);
    
    final result = byteData.buffer.asUint8List();
    result.setRange(8, 8 + payload.length, payload);
    return result;
  }

  /// Briefing: Deserializes a raw binary characteristic byte buffer into a structured [BleMeshChunk].
  /// Reason: Parses incoming radio packets received by the peripheral manager.
  static BleMeshChunk fromBytes(Uint8List bytes) {
    if (bytes.length < 8) {
      throw FormatException('BLE Mesh chunk corrupted: Length ${bytes.length} < 8 bytes header');
    }
    final byteData = ByteData.sublistView(bytes);
    final packetId = byteData.getUint16(0, Endian.big);
    final totalChunks = byteData.getUint8(2);
    final chunkIndex = byteData.getUint8(3);
    final crc32 = byteData.getUint32(4, Endian.big);
    final payload = bytes.sublist(8);

    return BleMeshChunk(
      packetId: packetId,
      totalChunks: totalChunks,
      chunkIndex: chunkIndex,
      crc32: crc32,
      payload: payload,
    );
  }
}

/// Briefing: Standard IEEE 802.3 CRC-32 lookup table implementation for wire framing.
/// Reason: Radio transmissions over BLE are susceptible to atmospheric interference and bit flips.
/// A 32-bit cyclical redundancy check guarantees that reassembled payloads match the sender's origin exactly.
class Crc32Calculator {
  static final List<int> _table = _generateTable();

  /// Briefing: Pre-computes the 256-entry lookup table for fast 32-bit polynomial division.
  static List<int> _generateTable() {
    final table = List<int>.filled(256, 0);
    for (int i = 0; i < 256; i++) {
      int crc = i;
      for (int j = 0; j < 8; j++) {
        if ((crc & 1) != 0) {
          crc = (crc >>> 1) ^ 0xEDB88320;
        } else {
          crc = crc >>> 1;
        }
      }
      table[i] = crc;
    }
    return table;
  }

  /// Briefing: Computes the CRC-32 checksum for an arbitrary byte array.
  static int compute(List<int> bytes) {
    int crc = 0xFFFFFFFF;
    for (final byte in bytes) {
      final tableIndex = (crc ^ byte) & 0xFF;
      crc = (crc >>> 8) ^ _table[tableIndex];
    }
    return (crc ^ 0xFFFFFFFF) & 0xFFFFFFFF;
  }
}

/// Briefing: Slicing and Reassembly Engine for asynchronous BLE GATT Mesh Transmissions.
/// Reason: Responders walk in and out of BLE range dynamically. Chunks may arrive out of order
/// or over multiple GATT read/write cycles. This engine tracks incomplete packets and emits
/// complete UTF-8 strings once all slices are assembled and checksums validate.
class BleMeshFramingEngine {
  static int _globalPacketCounter = 1;
  // Explanation: Default MTU chunk slice. 450 bytes payload + 8 bytes header = 458 bytes, safely within 512 MTU.
  static const int defaultMaxChunkPayload = 450;

  /// Briefing: Fragments an arbitrary text payload into a sequence of MTU-safe [BleMeshChunk]s.
  /// Reason: Prepares disaster event envelopes for broadcast across BLE characteristics.
  static List<BleMeshChunk> fragmentPayload({
    required String rawContent,
    int maxChunkSize = defaultMaxChunkPayload,
  }) {
    final rawBytes = Uint8List.fromList(utf8.encode(rawContent));
    final crc32 = Crc32Calculator.compute(rawBytes);
    final packetId = _globalPacketCounter++ % 65535;

    final totalChunks = (rawBytes.length / maxChunkSize).ceil();
    if (totalChunks > 255) {
      throw ArgumentError('Payload too large for BLE mesh framing (> 255 chunks)');
    }

    final chunks = <BleMeshChunk>[];
    for (int i = 0; i < totalChunks; i++) {
      final start = i * maxChunkSize;
      final end = (start + maxChunkSize > rawBytes.length) ? rawBytes.length : start + maxChunkSize;
      final chunkBytes = rawBytes.sublist(start, end);

      chunks.add(BleMeshChunk(
        packetId: packetId,
        totalChunks: totalChunks == 0 ? 1 : totalChunks,
        chunkIndex: i,
        crc32: crc32,
        payload: chunkBytes,
      ));
    }

    if (chunks.isEmpty) {
      chunks.add(BleMeshChunk(
        packetId: packetId,
        totalChunks: 1,
        chunkIndex: 0,
        crc32: crc32,
        payload: Uint8List(0),
      ));
    }

    return chunks;
  }

  // Explanation: Buffer cache mapping [packetId -> [chunkIndex -> chunk]]
  final Map<int, Map<int, BleMeshChunk>> _pendingPackets = {};

  /// Briefing: Ingests an incoming chunk; returns the complete decoded string when all chunks arrive and CRC passes.
  /// Reason: Handles asynchronous, out-of-order BLE frame arrivals. Discards corrupted packets on CRC mismatch.
  String? ingestChunk(BleMeshChunk chunk) {
    _pendingPackets.putIfAbsent(chunk.packetId, () => {});
    _pendingPackets[chunk.packetId]![chunk.chunkIndex] = chunk;

    final receivedChunks = _pendingPackets[chunk.packetId]!;
    if (receivedChunks.length == chunk.totalChunks) {
      // All chunks present! Assemble in index order
      final byteBuilder = BytesBuilder();
      for (int i = 0; i < chunk.totalChunks; i++) {
        final c = receivedChunks[i];
        if (c == null) return null; // Missing slice
        byteBuilder.add(c.payload);
      }

      final fullBytes = byteBuilder.toBytes();
      final calculatedCrc = Crc32Calculator.compute(fullBytes);

      // Verify CRC-32 Checksum
      if (calculatedCrc != chunk.crc32) {
        _pendingPackets.remove(chunk.packetId);
        throw StateError('BLE Mesh CRC-32 mismatch on packet ${chunk.packetId}: corrupted transmission');
      }

      // Cleanup pending cache
      _pendingPackets.remove(chunk.packetId);
      return utf8.decode(fullBytes);
    }

    return null; // Awaiting remaining chunks
  }

  /// Briefing: Purges all pending packet buffers to release memory.
  void clearPending() {
    _pendingPackets.clear();
  }
}
