# CS85 V1 research wire format

CS85 V1 is the host-side research packet format assembled by `scripts/cu66-v85/run_wire.py` and parsed by `experiments/python-gamebub-v85/receiver.cpp`. All multi-byte integers use big-endian byte order. The fixed header is 256 bytes; the Python `PREFIX` struct occupies 52 bytes, followed by six 32-byte digests and twelve reserved zero bytes.

## Header: 256 bytes

| Offset | Size | Field |
| ---: | ---: | --- |
| 0 | 4 | ASCII magic `CS85` |
| 4 | 1 | Version, `1` |
| 5 | 1 | Flags: `0` is delta, `1` is key; larger values are rejected |
| 6 | 1 | Tile group size, `16` |
| 7 | 1 | Reserved, zero |
| 8 | 4 | Frame ID |
| 12 | 4 | Reference frame ID |
| 16 | 8 | Generation |
| 24 | 2 | Width, `720` |
| 26 | 2 | Height, `480` |
| 28 | 2 | Block size, `16` or `32` |
| 30 | 2 | Reserved, zero |
| 32 | 4 | AB38 coefficient-block chunk cap: `16`, `64`, `256`, or `65536` |
| 36 | 4 | Mode-map byte length |
| 40 | 4 | Quantizer-map byte length, `338` |
| 44 | 4 | HUD byte length |
| 48 | 4 | Encoded three-plane data byte length |
| 52 | 32 | Previous frame content root; all zero for a key frame |
| 84 | 32 | Expected current content root |
| 116 | 32 | Expected C2 frame seal |
| 148 | 32 | Expected semantic HUD SHA-256 |
| 180 | 32 | Profile context digest |
| 212 | 32 | Hidden-mask digest |
| 244 | 12 | Reserved, all zero |

The six digests are, in order, previous root, current root, seal, semantic HUD SHA-256, profile context, and hidden-mask digest. The `PREFIX` struct corresponds exactly to offsets 0–51.

## Body

The body follows the header in this order:

1. The mode-map packet, exactly the declared mode-map length (20–996 bytes).
2. The fixed 338-byte packed quantizer map.
3. Three plane streams in Y, U, V order. Each starts with a big-endian `u32` chunk count. Each chunk then has a big-endian `u32` coefficient-block count, a big-endian `u32` AB38 payload length, and that many AB38 bytes. Counts and lengths are validated against the declared cap and decoder bounds.
4. The original HUD payload, exactly the declared HUD length (110–49152 bytes).
5. A four-byte big-endian CRC-32 over every preceding packet byte, including header and body.

The total packet length must equal 256 plus all declared body component lengths plus four CRC bytes. The host research receiver bounds a packet at 2 MiB. This parser bound is distinct from the older 49,152-byte compatibility budget; neither number is a claim about hardware receive RAM.

## Identity, binding, and state update

The profile is explicitly identified as CS85 version 1. The C2 commitment binds the profile context, frame ID, reference ID, key/delta marker, generation, previous root, semantic HUD digest, and reconstructed content root. These SHA-256 digests and the outer CRC detect mismatches and accidental corruption; they are unkeyed and do not authenticate a sender.

A key frame uses reference ID `0xffffffff` and an all-zero previous root. A delta frame must reference the currently accepted frame ID and its root. After an accepted frame exists, a new frame must have a greater frame ID and generation. Replaying the same packet is idempotent when its whole-packet SHA-256 matches the accepted packet. A packet with a changed digest and stale identity or generation is rejected. The receiver publishes the candidate frame and generation only after map, chunk, decode, HUD, content-root, and seal checks succeed; rejected packets leave the accepted state unchanged.

This is a Python packet builder plus host C++ research parser. It does not establish FPGA or ESP32 implementation behavior, hardware memory capacity, timing, sustained frame rate, or scanout behavior. A smoke run is not evidence for a complete 457-frame native parity campaign.
