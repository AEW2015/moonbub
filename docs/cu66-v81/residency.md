# V81 three-bank resident-tile store-elision prototype

This application-specific Python prototype preserves three ordinary canonical
banks. It can omit an unchanged decoded tile's physical store only when the
candidate bank already has a valid certificate for that tile's bytes. It uses
no aliases, allocation, reference counts, or tile-location indirection. The
candidate still contains the entire decoded canonical image at every accepted
commit. This is a native-oracle/model experiment; it changes no RTL, encoding,
producer, system bench, or system-run script, and implements no FPGA write gate.

The round-robin native replay passes all 457 frozen sources: 20 full-write keys
and 437 deltas, in four independent histories from one walkthrough family.
It certifies **1,685,219 tile-store elisions**, or **6,740,876 hypothetical BL8
canonical writes avoided**. This is less than the earlier previous-reference
equality upper bound: 659,906 unchanged delta tiles still require stores
because the selected candidate bank lacks a valid residency bit.

| Round-robin count, all 457 sources | Full-store baseline | Resident-store what-if |
|---|---:|---:|
| Canonical BL8 writes | 14,806,800 | 8,065,924 |
| Canonical plus HUD BL8 writes | 16,013,280 | 9,272,404 |
| Canonical reference BL8 reads | 14,158,800 | 14,158,800 |
| HUD readback BL8 reads | 1,206,480 | 1,206,480 |
| Sum of these read/write commands | 31,378,560 | 24,637,684 |

Each 64-byte tile corresponds to four 128-bit BL8 writes in this arithmetic.
HUD writes remain 2,640 per source. Metadata accesses and display scanout traffic
are unpriced; these are hypothetical counts, not observed physical traffic or
latency savings. Native logical decoding, full canonical SHA, packet
authentication, HUD digest, and display digest checks remain in the experiment.

| Cohort | Delta sources | Median resident-elided tiles/delta | Total resident-elided tiles |
|---:|---:|---:|---:|
| 0 | 114 | 3,467.5 | 370,201 |
| 1 | 114 | 2,957.5 | 395,106 |
| 2 | 114 | 6,922 | 704,806 |
| 3 | 95 | 2,467 | 215,106 |

Of the elisions, 116,718 are fixed-128 hidden tiles and 1,568,501 are visible
tiles. Keys always write all 8,100 tiles, even if bytes match an older frame.
With round-robin selection, the first two deltas after each key have no
certified candidate residency: **40 delta sources retain all canonical writes**.
Startup, key recovery, reset and generations that lack residency certificates
can therefore retain full traffic. Aggregate canonical-write reduction of
45.5% does not eliminate the existing
[conditional 11.91342 ms frozen-service floor](next-bottleneck.md) on
remaining full-traffic deltas at the assumed 100 MHz. This experiment proves
neither 30 fps, strict maximum latency below 10 ms, nor physical FPGA timing.
Strict maximum latency would still require changes to the service path or
transaction beyond this residency scheme.

## State and transaction rules

For each tile, the accepted map holds three bits: bit `b` certifies that
physical bank `b` contains that tile's bytes from the current accepted
reference. The candidate builds a second shadow map while decoding. A future
implementation would require 8,100 × 3 × 2 = 48,600 logical map bits, or
**6,075 packed bytes**, plus control state and map access costs. Python object
sizes are unrelated to this number. Target fit and metadata throughput are
unproven.

1. Candidate selection excludes the accepted reference, the displayed front,
   and every undrained scanout lease. No tile can be written in those banks.
2. For a delta tile, the decoded bytes must first compare equal to the leased
   accepted reference. If the old accepted-map candidate bit is also set, the
   existing physical candidate bytes may be certified and their store omitted.
   The shadow map retains the old residency bits.
3. An unchanged tile missing that bit is physically written. Its shadow mask
   retains still-valid accepted bits and adds the candidate. A changed tile
   must be written; its shadow mask contains only the candidate bit.
4. Before the first physical write to any tile, its candidate bit is cleared
   in the **old accepted map**. This is per-tile invalidation, including key
   writes. An abort discards the shadow map but never restores those old bits;
   a retry must not claim residency for bytes that an abandoned store altered.
5. Only authenticated accepted commit publishes the shadow map and reference
   bank together. The entire physical candidate image must equal the decoded
   canonical image, and every published bit must name matching physical bytes.
   Every key's new accepted mask contains only its candidate bank.
6. A replay with the exact last accepted frame and packet identity returns
   the same acknowledgment without decoding, storing or publishing again.
   Mismatched replay identity is rejected. This is model behavior for the
   surrounding transaction layer, not a change to the frozen native decoder
   or its monotonic receive API.
7. Decode reset invalidates certificates and requires a new full-write key.
   The model retains front/drain leases across reset until actual release.

An aborted transaction may leave physically correct tiles without certificates;
rewriting them on retry is deliberately conservative. No rollback reconstructs
certificates from the abandoned shadow map or an old snapshot.

## Oracle and verification boundaries

The separate [collector](../../fpga/experiments/cu66-v81/residency/collect_tiles.cpp)
includes the existing native decoder read-only. On every fixture it verifies
the content-addressed packet SHA, complete canonical SHA, HUD SHA and display
SHA against the frozen index; normal decoder authentication still runs. It
compares all 64 decoded bytes per tile with the prior accepted frame and
exports exact equality masks plus complete per-tile SHA-256 fingerprints.
All 457 masks match the earlier tile-reuse collector's retained log exactly;
none of its old source or result files is edited.

The [Python model](../../fpga/experiments/cu66-v81/residency/model.py) checks
physical tile fingerprints on **every claimed native elision**, all residency
bits after commit/abort, and the entire candidate image at commit. Its
independent synthetic cases instead use complete 64-byte tile values. Hashes
are an experimental oracle, not a substitute for an implemented hardware
gate or a new integrity guarantee. Actual RTL must derive unchanged
authenticity by comparing decoded pixels against the leased reference and
bind certificates to accepted state. A host-supplied skip flag would be
insufficient. Physical corruption detection exercised here exists in the
oracle/model only.

Nineteen independent synthetic cases run before native data is read. They
cover three-bank warmup, deliberate non-round-robin choices, changed writes,
partial abort/retry, late authentication failure, aborted keys, invalidations
surviving rollback, reset/key recovery, front/reference/drain leases, lost ACK
idempotency, forged unchanged flags, forged residency bits, and physical tile
corruption rejected at the elision certificate gate.

Two complete positive native schedules pass: round-robin and a different
legal bank schedule (1,715,594 tile elisions for the latter, not an optimized
allocator claim). A separate native fault replay accepts all 457 sources
again while injecting 16 partial and 15 late-authentication aborts before
retries and replaying a lost ACK for every accepted source. The partial
aborts clear 4,811 existing old-reference certificate bits without restoring
them on rollback. These fault-path counts
include abandoned stores and are verification evidence, not savings
estimates. Actual packet corruption, asynchronous hardware races, synthesis,
cycle timing, metadata ports and scanout integration remain outside this
prototype.

## Reproduction and retained evidence

From the repository root, run:

```sh
python3 scripts/cu66-v81/prototype_residency.py
```

This runs the exact-byte synthetic cases first, builds the native collector
in a unique directory using one CPU at low priority, recollects the frozen
corpus, and runs all positive and fault replays. `--synthetic-only` runs just
the abstract checks. To repeat model checks against the retained oracle:

```sh
python3 scripts/cu66-v81/prototype_residency.py --replay-oracle \
  fpga/experiments/cu66-v81/residency/attempt-20261106T044132300905Z-c00ca26f
```

The [collection report](../../fpga/experiments/cu66-v81/residency/attempt-20261106T044132300905Z-c00ca26f/results.json)
retains exact compiler/run commands, source snapshot and hashes, compiler and
execution logs, binary SHA, all native digests/masks, and one compressed
fingerprint stream per cohort. Each compressed artifact is under 21 MiB.
The temporary raw files were deleted after recording raw SHA-256, byte count,
record count, ordering and compressed artifact SHA; gzip decompression
recovers each exact raw stream. Frozen inputs plus pinned collector source
allow independent regeneration.

The [final replay report](../../fpga/experiments/cu66-v81/residency/attempt-20261106T044250131135Z-6caa860d/results.json)
pins the final model/script snapshot, points to that collection attempt,
retains per-source results for both schedules, and links the
[native fault results](../../fpga/experiments/cu66-v81/residency/attempt-20261106T044250131135Z-6caa860d/native-fault-cases.json).
The initial pre-execution Python syntax error and its correction are recorded
in [development-attempts.json](../../fpga/experiments/cu66-v81/residency/development-attempts.json).
It changed no native or RTL state. Subsequent collection and complete replay
attempts passed. No old study result is overwritten.
