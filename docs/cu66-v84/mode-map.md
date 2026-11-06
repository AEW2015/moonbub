# V84 bounded operation-map prototype

The operation map is an independently encoded/parsed piece of research metadata,
not a finished streaming codec. It names **COPY_REF**, **CONST128**, and
**RESIDUAL** for every canonical tile. Native mode selection uses the verified
zero-coefficient COPY condition; hidden tiles use the fixed profile's CONST128
mask. The profile retains 720×480 YUV420 geometry and existing quantized pixels.

An independent bounded parser round-trips all **457 native sources**. There are
**28 positive/malformed checks** and **five exact packet-hex/SHA vectors**. These
exercise the metadata grammar, not an AB38 residual encoder, a content tree,
reference ownership, FPGA timing, or ESP32 forwarding.

## Actual binary grammar

The 20-byte, big-endian header is `>4sBBBBHHHHI`:

| Field | Value/meaning |
|---|---|
| Magic, version | `CM84`, 1; a distinct research profile |
| Method | 0 = packed two-bit map; 1 = group16; 2 = RLE64 |
| Key flag | Exactly 0 or 1 |
| Grouping | Exactly 16 |
| Width, height, tile count | Exactly 720, 480, 8,100 |
| Body length | Maximum 2,025 bytes; exact packet length required |
| CRC32 | Covers the body; corruption check, not authentication |

Tile codes are 0 = COPY_REF, 1 = CONST128, 2 = RESIDUAL; code 3 is forbidden.
The receiver gets the fixed hidden mask from its profile, not this packet.
CONST128 is required exactly on hidden tiles, forbidden on visible tiles, and
COPY_REF is forbidden for keys. The optional expected-key argument binds the
flag to the caller's frame context. This component does not bind frame IDs,
reference generations, capability exchange or content roots; the complete
outer protocol must do that.

Methods are:

- **Flat2:** four modes per byte, most-significant pair first. The 8,100 modes
  occupy exactly 2,025 bytes.
- **Group16:** 508 groups, restarting at each Y/Cb/Cr plane boundary. A uniform
  group uses one byte, tag 0/1/2. Tag 3 introduces packed two-bit modes for the
  known group size. Padding pairs in partial groups must be zero. Other tags
  are rejected.
- **RLE64:** each byte has mode in its low two bits and run-length-minus-one in
  its high six bits. Runs span 1–64 tiles, with exact 8,100-tile coverage.

The encoder chooses the shortest complete body; equal lengths prefer Flat2,
then Group16, then RLE64. The flat fallback guarantees a 2,025-byte body cap
and **2,045-byte packet cap**. The parser never calls the encoder or body
builders. It accepts valid alternative representations rather than requiring
the shortest choice; it enforces operation legality, lengths, tile counts and
zero padding. CRC32 does not authenticate the header or sender.

## Native results

| Representation | Body minimum | Body median | Body maximum | Total body bytes |
|---|---:|---:|---:|---:|
| Flat2 | 2,025 | 2,025 | 2,025 | 925,425 |
| Group16 | 596 | 1,744 | 2,208 | 754,516 |
| RLE64 | 138 | 1,123 | 2,277 | 494,665 |
| Shortest with flat fallback | **138** | **1,123** | **2,025** | **494,413** |

RLE64 is selected for 456 sources, Flat2 for one, and Group16 for none. Total
selected packets including headers are 503,553 bytes; packet minimum/median/
maximum are **158 / 1,143 / 2,045 bytes**. The selected operation-map bodies
use 46.57% fewer bytes than a standalone flat two-bit map on this corpus.

**That is a metadata comparison, not a streaming bitrate improvement.** Adding
these packets to unchanged AB38 adds bytes. Existing adaptive entropy contexts
and DC/AC dependencies still require decoding. A complete explicit-COPY codec
needs actual residual reencoding/context rules and independent pixel/content
validation before any avoided entropy work or total-rate benefit is claimed.

## Limits and next application-specific reduction

The 8,100-entry output is a logical bound. Python list/object allocations are
not an ESP32 RAM budget; an embedded parser needs a packed or streaming form,
finite input/forward buffers, backpressure and error recovery tests.

The fixed hidden mask makes CONST128 positions implicit. A successor format
could therefore encode only visible COPY/RESIDUAL choices with one bit each:
7,806 visible tiles require at most **976 bytes**, and key choices could be
implicit. That successor format is not implemented or included in these
results; it needs an explicitly new method/version and its own parser tests.

## Reproduction

```sh
python3 scripts/cu66-v84/prototype_mode_map.py
```

The command refuses to overwrite existing retained results. Native input
identities are cross-bound to the entropy index, with original V82 chunk/hash
verification. The result binds the executed source, native index/loader and
entropy index; `frames.jsonl`, `tests.json` and `vectors.json` have retained
SHA-256 hashes. No model or entropy source from earlier iterations changed.
