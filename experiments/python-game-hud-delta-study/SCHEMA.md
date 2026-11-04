# gamebub-hud-delta-v21-1

`results.json` binds six synthetic complete HD21 packet controls and exact current
and optional reference RGB565 rasters. Arrays have the declared shape and portable
little-endian uint16 words. Each blob uses a safe relative content-addressed zlib
object path, exact raw length/hash, and stored hash. No source footage is required.

`source_sha256` pins this component's six source/documentation files. `summary`
counts component controls, exact reconstructed words and complete packet bytes;
these counts are not source-clock frames, native service or physical FPS.

`verify.py` checks all pins/objects, replays an independently written scalar decoder,
compares the NumPy implementation, deterministically re-encodes every fixture and
rejects six CRC corruptions. Unit tests additionally cover random input and semantic
negative cases. Receiver cache/ACK/generation semantics are a separate component.
