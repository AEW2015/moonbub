# V96 accepted-reference inventory

Run `python3 scripts/cu66-v96/inventory.py --timeout 900` from the repository.
The runner creates an immutable attempt with failure receipts and a finite wall
watchdog. `index.json` selects the last successful report. It consumes the frozen
V82 loader, validates every source shard digest and pins input/source hashes.
Every frame is independently parsed and materialized for all three profiles.
Canonical SHA-256 is calculated after undoing tile order into raster planes.

`model.py` exposes `encode(frame, accepted, profile, dst_bank, src_bank, index)`,
`parse(stream)`, `materialize(stream, accepted)`, `dictionaries(tiles, slots)`,
`physical_byte(logical_byte)`, `address(plane, tile, bank)` and `raster_digest`.
The exact stream grammar is self-described in each header. It is an explicitly
new research stream and has no runtime/deployed-wire compatibility claim.

The eight-byte magic is `V96RS01\0`, followed by little-endian uint32 JSON byte
length and descriptor count (8100), then UTF-8 JSON and tile-order descriptors.
Each descriptor is `<BBHHBBIIII`, exactly 24 bytes: operation, plane, destination
tile-local position, source tile-local position, destination bank, source bank,
destination plane-relative physical byte, destination global physical byte,
source plane-relative physical byte, source global physical byte. Source-free
records use source position 65535, bank 255, and both addresses 0xffffffff.
Only FALLBACK has a following literal 64-byte payload. All framing, JSON,
descriptors, and payload bytes are charged. Actual compressed gzip sizes are
archive sizes and establish no compression ratio against deployed residuals.

Operation values are FALLBACK=0, COPY_REF=1, CONST128=2 and CROSSCOPY=3. Every
operation materializes all 64 destination bytes. A copy reads 64 accepted-source
bytes and writes 64 destination bytes; it creates no alias. Hidden CONST128
always writes 64 bytes in this model. NonCOPY exact same-position equality is
counted separately and is never silently promoted to COPY_REF. Cross proposals
exclude hidden/COPY tiles, require a different local position in the same plane,
use only the previous accepted frame, and are disabled on keys.

The three profiles are control, cross64 and cross256. Each plane has its own
bounded dictionary of 64 or 256 distinct exact byte strings, with source local
positions. Rebuild scans all accepted tiles in ascending order, evicting FIFO
when a new distinct byte string arrives; duplicate hits do not refresh order.
The first position is kept until eviction. The dictionary is rebuilt only after
successful exact output validation. Candidate encode/abort cannot mutate it.
Initial keys have no dictionary/reference. The runner reports scan/query budgets,
occupancy, exact-byte comparison upper bounds and selected source positions.
Python byte-string hash lookups are host implementation details with no cycle or
hardware-search claim. A linear comparator implementation's explicit worst case
is `slots * 64` compared bytes per query. Logical contents alone require
`3 * slots * (64 + 2 + 1)` bytes for tile bytes, local position and valid bit stored
as a byte (12,864 / 51,456 bytes); host object overhead and hardware lookup logic
are additional. Unbounded opportunity dictionaries are diagnostics and cannot
select proposed copies.

The frozen bridge maps Y/U/V plane bases 0/345600/432000 to contiguous 64-byte
tiles in each plane, leaves HUD bytes 518400..560639 linear, and maps global
word address as `(bank << 22) | (physical_byte >> 1)`. The global byte stride is
therefore 8 MiB per bank. Banks 0..2 retain their apertures and offsets; there is
no address compaction. `test_model.py` checks every canonical byte against an
independent raster-to-tile address calculation, plus initial keys, COPY and cross
sources, abort/replay immutability, malformed streams and source ownership.

Archive `records-NNN.bin.gz` shards are bounded to 24 MiB uncompressed. Each
record is uint32 JSON byte length plus frame JSON, followed by three uint32
stream byte length plus stream pairs in control/cross64/cross256 order. The
frame JSON contains each exact stream SHA, operation/search counts, and traffic
counters. `frames.jsonl.gz` repeats these compact inventory rows. `results.json`
pins raw/gzip shard hashes and all artifacts.

The named materialization fence is canonical candidate tiles drained before
publication. Its counters include copy source reads and every canonical tile
write, excluding input acquisition, entropy/residual reconstruction, hashing,
HUD and scanout. A separately labeled retained reconstruction accounting charges
64 accepted prediction bytes for each visible tile of every delta. CROSSCOPY
replaces a same-position predictor read with its source read in that account;
it implies no memory-volume saving. Avoided residual tiles are a work proxy,
with no estimated residual packet bytes or latency saving. Display constant
generation, grouped service, abort/held-display root/seal checks and continuous
scanout service require their separate V96 harnesses. No raw-capture,
full-path timing, refresh/arbitration, hardware or compression claim is made.
