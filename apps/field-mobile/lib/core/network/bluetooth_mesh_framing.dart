import 'dart:convert';
import 'dart:typed_data';

/// Represents a single BLE characteristic transmission frame
class BleMeshChunk {
  final int packetId;      // 0 - 65535
  final int totalChunks;   // 1 - 255
  final int chunkIndex;    // 0 - (totalChunks - 1)
  final int crc32;         // 32-bit checksum of the FULL unfragmented payload
  final Uint8List payload; // Raw chunk bytes

  const BleMeshChunk({
    required this.packetId,
    required this.totalChunks,
    required this.chunkIndex,
    required this.crc32,
    required this.payload,
  });

  /// Binary wire serialization: [packetId:2B][totalChunks:1B][chunkIndex:1B][crc32:4B][payload:NB]
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

  /// Binary wire deserialization
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

/// Standard IEEE 802.3 CRC-32 implementation for wire framing
class Crc32Calculator {
  static final List<int> _table = _generateTable();

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

  static int compute(List<int> bytes) {
    int crc = 0xFFFFFFFF;
    for (final byte in bytes) {
      final tableIndex = (crc ^ byte) & 0xFF;
      crc = (crc >>> 8) ^ _table[tableIndex];
    }
    return (crc ^ 0xFFFFFFFF) & 0xFFFFFFFF;
  }
}

/// Fragmenter & Assembler for BLE GATT Mesh Transmissions
class BleMeshFramingEngine {
  static int _globalPacketCounter = 1;
  static const int defaultMaxChunkPayload = 450; // Leave 8 bytes for header within 512 MTU

  /// Fragments a large string/payload into BLE chunks
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

  /// Stateful Reassembler for collecting chunks from asynchronous BLE streams
  final Map<int, Map<int, BleMeshChunk>> _pendingPackets = {};

  /// Ingests a chunk; returns the complete decoded string when all chunks arrive and CRC passes
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

  void clearPending() {
    _pendingPackets.clear();
  }
}
